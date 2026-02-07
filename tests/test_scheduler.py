from lab_gpu.agent import Agent, ProcessSample
from lab_gpu.master import Master
from lab_gpu.models import GPU, Node, Priority, Task, TaskStatus
from lab_gpu.scheduler import Scheduler, TaskProfile


def test_scheduler_backfilling():
    scheduler = Scheduler()
    big = Task(task_id=1, user="a", cmd="train", min_vram_gb=80, priority=Priority.HIGH)
    small = Task(task_id=2, user="b", cmd="eval", min_vram_gb=8, priority=Priority.NORMAL, time_limit_s=600)
    scheduler.submit(big)
    scheduler.submit(small)

    node_a = Node(name="A", gpus=[GPU(gpu_id=0, total_vram_gb=24, used_vram_gb=0)])
    node_b = Node(name="B", gpus=[GPU(gpu_id=0, total_vram_gb=80, used_vram_gb=80)])

    assignments = scheduler.schedule([node_a, node_b])
    assert assignments == [(2, "A", 0)]
    assert scheduler.state.tasks[1].status == TaskStatus.PENDING
    assert scheduler.state.tasks[2].status == TaskStatus.RUNNING


def test_oom_recovery():
    master = Master()
    task = Task(task_id=1, user="me", cmd="python mock_oom.py", min_vram_gb=10, priority=Priority.NORMAL)
    master.submit(task)

    agent = Agent(on_oom=master.on_oom)
    stderr_lines = ["RuntimeError: CUDA out of memory. Tried to allocate 1.0 GiB"]
    oom = agent.handle_process_exit(task_id=1, exit_code=1, stderr_lines=stderr_lines, current_used_gb=10)

    assert oom is not None
    updated = master.scheduler.state.tasks[1]
    assert updated.status == TaskStatus.PENDING
    assert updated.min_vram_gb == 12.0
    assert updated.retry_count == 1


def test_fair_share():
    scheduler = Scheduler()
    for i in range(5):
        running = Task(task_id=i + 1, user="user_a", cmd="run", min_vram_gb=4, priority=Priority.NORMAL)
        scheduler.submit(running)
        scheduler.update_task_status(running.task_id, TaskStatus.RUNNING)

    pending_a = Task(task_id=100, user="user_a", cmd="wait", min_vram_gb=4, priority=Priority.NORMAL)
    pending_b = Task(task_id=101, user="user_b", cmd="wait", min_vram_gb=4, priority=Priority.NORMAL)
    scheduler.submit(pending_a)
    scheduler.submit(pending_b)

    node = Node(name="N", gpus=[GPU(gpu_id=0, total_vram_gb=16, used_vram_gb=0)])
    assignments = scheduler.schedule([node])

    assert assignments[0][0] == 101


def test_zombie_process_detection():
    agent = Agent()
    samples = [
        ProcessSample(pid=123, used_vram_gb=20, util_pct=0.0, io_read_kb=0, io_write_kb=0, duration_s=600),
        ProcessSample(pid=124, used_vram_gb=2, util_pct=50.0, io_read_kb=10, io_write_kb=0, duration_s=100),
    ]
    zombies = agent.detect_zombies(samples)
    assert zombies == [123]


def test_profile_recommended_vram_used_when_missing():
    scheduler = Scheduler()
    scheduler.profiles["user:train"] = TaskProfile(peak_vram_gb=20, success_count=1)
    task = Task(
        task_id=1,
        user="user",
        cmd="train",
        min_vram_gb=0,
        priority=Priority.NORMAL,
        profile_key="user:train",
    )
    scheduler.submit(task)

    node_a = Node(name="A", gpus=[GPU(gpu_id=0, total_vram_gb=16, used_vram_gb=0)])
    node_b = Node(name="B", gpus=[GPU(gpu_id=0, total_vram_gb=24, used_vram_gb=0)])

    assignments = scheduler.schedule([node_a, node_b])
    assert assignments == [(1, "B", 0)]
    assert scheduler.state.tasks[1].min_vram_gb >= 20
