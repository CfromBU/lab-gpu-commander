# Repository Guidelines

## Project Structure & Module Organization
- `lab_gpu/`: core Python package (CLI, master/agent, scheduler, policy, TUI).
- `tests/`: pytest suite for scheduling, OOM handling, and process logic.
- `examples/`: runnable GPU workload demos (e.g., `examples/gpu_oom.py`).
- `vscode/`: VS Code extension source, build output, and packaging config.
- `docs/`: add new design notes or contributor docs here if needed.

## Build, Test, and Development Commands
- `python -m pip install .`: install the CLI and package locally.
- `python -m pip install ".[test]"`: install test dependencies.
- `pytest -q`: run the test suite (quiet by default).
- `lab-gpu server start --role master`: start the in-memory demo scheduler.
- `lab-gpu submit --mem 10G --priority normal "python train.py"`: submit a job.
- `cd vscode && npm install && npm run compile`: build the VS Code extension.
- `cd vscode && npx vsce package`: produce a `.vsix` package.

## Coding Style & Naming Conventions
- Python: 4-space indentation, `snake_case` for functions/variables, `PascalCase` for classes.
- Prefer small, focused modules under `lab_gpu/` with explicit imports.
- Keep CLI commands in `lab_gpu/cli.py`, TUI logic in `lab_gpu/tui.py`.
- No unified formatter/linter is enforced; keep changes consistent with existing style.

## Testing Guidelines
- Framework: `pytest` (see `tests/test_scheduler.py`).
- Add or update tests for scheduling policy changes, OOM parsing, and preemption logic.
- Test files use `test_*.py` naming; keep fixtures close to the test file.
- Run `pytest -q` before opening a PR.

## Commit & Pull Request Guidelines
- Commit messages: use `type: summary` or `scope: summary` (e.g., `fix: handle oom retry`).
- PRs should include: a short description, steps to test, and linked issues if applicable.
- Include screenshots or GIFs for TUI or VS Code extension changes.

## Configuration & Security Notes
- Python 3.10+ required (see `pyproject.toml`).
- Optional dependencies: `.[server]` for FastAPI, `pyyaml` for policy files.
- Default agent logs may write to `/nas/logs/{task_id}.log`; document any path changes.
