from typer.testing import CliRunner

from lab_gpu.cli import app


def test_cli_server_api_command():
    runner = CliRunner()
    result = runner.invoke(app, ["server", "start", "--role", "master"])
    assert result.exit_code == 0
