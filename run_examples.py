#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lab-GPU 示例任务提交脚本 (Python 版本)
使用 examples 目录中的示例程序，无需预设 tasks.json
"""

import subprocess
import sys
import time
import json
from typing import List, Dict

class LabGPUManager:
    """Lab-GPU 任务管理器"""
    
    def __init__(self, host="127.0.0.1"):
        self.host = host
        self.task_ids = []
    
    def run_command(self, cmd: List[str], capture=False):
        """执行命令"""
        try:
            if capture:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                return result.stdout.strip()
            else:
                subprocess.run(cmd, check=True)
                return None
        except subprocess.CalledProcessError as e:
            print(f"❌ 命令执行失败: {' '.join(cmd)}")
            print(f"   错误: {e}")
            sys.exit(1)
    
    def start_server(self):
        """启动 Master 服务"""
        print("⚙️  启动 Master 服务...")
        self.run_command(["lab-gpu", "server", "start", "--role", "master", "--host", self.host])
        print("✅ Master 服务已启动")
    
    def add_node(self, name: str, gpus: int, vram: int, gpu_type: str = None):
        """添加 GPU 节点"""
        cmd = ["lab-gpu", "server", "add-node", "--name", name, "--gpus", str(gpus), "--vram", str(vram)]
        if gpu_type:
            cmd.extend(["--gpu-type", gpu_type])
        self.run_command(cmd)
        print(f"✅ 已添加节点: {name} ({gpus}x GPU, {vram}GB)")
    
    def submit_task(self, cmd: str, mem: str, priority: str = "normal", description: str = None):
        """提交任务"""
        submit_cmd = ["lab-gpu", "submit", "--mem", mem, "--priority", priority, cmd]
        output = self.run_command(submit_cmd, capture=True)
        
        # 提取任务 ID
        if "task" in output.lower():
            task_id = output.split()[-1]
            self.task_ids.append(task_id)
            desc = f" ({description})" if description else ""
            print(f"✅ 已提交任务 ID: {task_id}{desc}")
            return task_id
        return None
    
    def tick(self):
        """执行调度"""
        print("\n⚙️  执行调度...")
        self.run_command(["lab-gpu", "server", "tick"])
        print("✅ 调度完成")
    
    def status(self, json_output=False):
        """查看状态"""
        if json_output:
            output = self.run_command(["lab-gpu", "status", "--json"], capture=True)
            return json.loads(output)
        else:
            self.run_command(["lab-gpu", "status"])
    
    def launch_tui(self):
        """启动 TUI 界面"""
        print("\n🎨 启动 TUI 可视化界面...")
        print("\n💡 TUI 快捷键：")
        print("   k - 杀死任务")
        print("   r - 重试任务")
        print("   t - 提升到队首")
        print("   q - 退出")
        print("━" * 60)
        time.sleep(2)
        subprocess.run(["lab-gpu", "tui"])


def main():
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║     Lab-GPU 示例任务运行脚本 (Python 版)                     ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    
    manager = LabGPUManager()
    
    # 1. 启动服务
    print("━" * 60)
    print("📋 步骤 1: 启动服务")
    print("━" * 60)
    manager.start_server()
    print()
    
    # 2. 添加节点
    print("━" * 60)
    print("📋 步骤 2: 添加 GPU 节点")
    print("━" * 60)
    manager.add_node("node-1", gpus=2, vram=24, gpu_type="RTX 3090")
    manager.add_node("node-2", gpus=2, vram=48, gpu_type="A100")
    print()
    
    # 3. 查看初始状态
    print("━" * 60)
    print("📋 步骤 3: 初始状态")
    print("━" * 60)
    manager.status()
    print()
    
    # 4. 提交示例任务
    print("━" * 60)
    print("📋 步骤 4: 提交示例任务")
    print("━" * 60)
    print()
    
    # 定义任务列表
    tasks = [
        {
            "cmd": "python examples/gpu_alloc.py --mock --gb 2 --sleep 20",
            "mem": "2G",
            "priority": "high",
            "desc": "GPU 显存分配 2GB"
        },
        {
            "cmd": "python examples/gpu_burst.py --mock --gb 1 --cycles 3",
            "mem": "1G",
            "priority": "normal",
            "desc": "GPU Burst 周期性申请"
        },
        {
            "cmd": "python examples/gpu_sleep.py --mock --gb 4 --sleep 60",
            "mem": "4G",
            "priority": "low",
            "desc": "GPU 长时间占用 4GB"
        },
        {
            "cmd": "python examples/gpu_oom.py --mock-oom",
            "mem": "2G",
            "priority": "normal",
            "desc": "OOM 测试（自愈功能）"
        },
        {
            "cmd": "python examples/gpu_alloc.py --mock --gb 0.5 --sleep 5",
            "mem": "0.5G",
            "priority": "normal",
            "desc": "小任务（回填测试）"
        },
        {
            "cmd": "echo 'Lab-GPU Test' && sleep 3",
            "mem": "1G",
            "priority": "high",
            "desc": "简单测试任务"
        },
    ]
    
    print("🚀 提交任务:")
    for i, task in enumerate(tasks, 1):
        print(f"\n   [{i}] {task['desc']}")
        manager.submit_task(
            cmd=task["cmd"],
            mem=task["mem"],
            priority=task["priority"],
            description=f"{task['priority']}, {task['mem']}"
        )
    
    print()
    
    # 5. 执行调度
    print("━" * 60)
    print("📋 步骤 5: 执行调度")
    print("━" * 60)
    manager.tick()
    print()
    
    # 6. 查看任务状态
    print("━" * 60)
    print("📋 步骤 6: 任务状态")
    print("━" * 60)
    manager.status()
    print()
    
    # 7. 详细状态
    print("━" * 60)
    print("📋 步骤 7: 详细状态 (JSON)")
    print("━" * 60)
    status = manager.status(json_output=True)
    import json
    print(json.dumps(status, indent=2))
    print()
    
    # 8. 总结
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║     脚本执行完成！                                            ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    print("💡 接下来你可以：")
    print()
    print("   1️⃣  启动 TUI 可视化界面（按回车启动）")
    print("      lab-gpu tui")
    print()
    print("   2️⃣  查看特定任务的日志")
    if manager.task_ids:
        print(f"      lab-gpu logs {manager.task_ids[0]}")
        print(f"      lab-gpu logs {manager.task_ids[0]} -f  # 实时跟踪")
    print()
    print("   3️⃣  查看任务状态")
    print("      lab-gpu status")
    print()
    print("━" * 60)
    print(f"📝 已提交 {len(manager.task_ids)} 个任务")
    print("━" * 60)
    print()
    
    # 询问是否启动 TUI
    try:
        response = input("是否启动 TUI 界面？(y/n，默认 y): ").strip().lower()
        if response in ['', 'y', 'yes']:
            manager.launch_tui()
    except KeyboardInterrupt:
        print("\n\n👋 再见！")
        sys.exit(0)


if __name__ == "__main__":
    main()
