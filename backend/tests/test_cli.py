"""Tests for Typer CLI."""

from unittest.mock import patch

import pytest
from cli import app
from typer.testing import CliRunner


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


class TestCLI:
    def test_cli_help(self, runner: CliRunner) -> None:
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "UPCP CLI" in result.output

    def test_project_list(self, runner: CliRunner) -> None:
        with patch("cli.ProjectService") as mock_service:
            mock_service.return_value.list_projects.return_value = ([], 0)
            result = runner.invoke(app, ["project", "list"])
            assert result.exit_code == 0
            assert "Projects (0 total):" in result.output

    def test_project_get_help(self, runner: CliRunner) -> None:
        result = runner.invoke(app, ["project", "get", "--help"])
        assert result.exit_code == 0
        assert "Get project by ID" in result.output

    def test_task_list_help(self, runner: CliRunner) -> None:
        result = runner.invoke(app, ["task", "list", "--help"])
        assert result.exit_code == 0
        assert "List tasks for a feature" in result.output

    def test_task_get_help(self, runner: CliRunner) -> None:
        result = runner.invoke(app, ["task", "get", "--help"])
        assert result.exit_code == 0
        assert "Get task by ID" in result.output

    def test_status(self, runner: CliRunner) -> None:
        result = runner.invoke(app, ["status"])
        assert result.exit_code == 0
        assert "UPCP Status" in result.output
