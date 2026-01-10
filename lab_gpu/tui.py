from __future__ import annotations

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import DataTable, Footer, Header, Input, Static

from .master import Master


class LabTui(App):
    CSS = """
    Screen { layout: vertical; }
    #summary { height: 3; padding: 1; }
    #table { height: 1fr; }
    #command { height: 3; padding: 1; }
    """
    BINDINGS = [
        ("k", "kill", "Kill task"),
        ("r", "retry", "Retry task"),
        ("t", "top", "Move to top"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self, master: Master) -> None:
        super().__init__()
        self.master = master
        self.summary = Static(id="summary")
        self.table = DataTable(id="table")
        self.command = Input(placeholder="command: list | top <id>", id="command")
        self.list_mode = False

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical():
            yield self.summary
            yield self.table
            yield self.command
        yield Footer()

    def on_mount(self) -> None:
        self.table.add_columns("ID", "User", "Status", "Mem", "Node", "Cmd")
        self.refresh_view()
        self.set_interval(2.0, self.refresh_view)

    def refresh_view(self) -> None:
        data = self.master.summary()
        if self.list_mode:
            self.summary.update("List mode")
        else:
            self.summary.update(
                f"Tasks: {data['tasks']} | Pending: {data['pending']} | Running: {data['running']} | OOMs: {data['ooms']}"
            )
        self.table.clear()
        for task in self.master.scheduler.state.tasks.values():
            self.table.add_row(
                str(task.task_id),
                task.user,
                task.status.value,
                f"{task.min_vram_gb}G",
                task.assigned_node or "-",
                task.cmd[:40],
            )

    def _selected_task_id(self) -> int | None:
        if self.table.row_count == 0:
            return None
        row_key = self.table.cursor_row
        if row_key is None:
            return None
        row = self.table.get_row_at(row_key)
        if not row:
            return None
        return int(row[0])

    def action_kill(self) -> None:
        task_id = self._selected_task_id()
        if task_id is None:
            return
        self.master.kill_task(task_id)
        self.refresh_view()

    def action_retry(self) -> None:
        task_id = self._selected_task_id()
        if task_id is None:
            return
        self.master.retry_task(task_id)
        self.refresh_view()

    def action_top(self) -> None:
        task_id = self._selected_task_id()
        if task_id is None:
            return
        self.master.move_task_to_front(task_id)
        self.refresh_view()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        if not text:
            return
        if text == "list":
            self.list_mode = not self.list_mode
            self.refresh_view()
        elif text.startswith("top "):
            try:
                task_id = int(text.split()[1])
                self.master.move_task_to_front(task_id)
            except ValueError:
                pass
            self.refresh_view()
        self.command.value = ""
