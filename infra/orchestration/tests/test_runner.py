"""Tests for command runner utilities."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from harness.core.runner import (
    CommandError,
    CommandRunner,
    MissingDependencyError,
    check_dependencies,
    run_command,
)


class TestCheckDependencies:
    """Tests for check_dependencies function."""

    def test_all_dependencies_present(self) -> None:
        """Test when all dependencies are available."""
        # These should exist on most systems
        check_dependencies(["python3", "ls"])

    def test_missing_dependency_raises_error(self) -> None:
        """Test that missing dependency raises MissingDependencyError."""
        with pytest.raises(MissingDependencyError) as exc_info:
            check_dependencies(["nonexistent_command_xyz123"])

        assert "nonexistent_command_xyz123" in exc_info.value.dependencies

    def test_multiple_missing_dependencies(self) -> None:
        """Test that all missing deps are reported."""
        with pytest.raises(MissingDependencyError) as exc_info:
            check_dependencies(["fake_cmd_1", "python3", "fake_cmd_2"])

        assert "fake_cmd_1" in exc_info.value.dependencies
        assert "fake_cmd_2" in exc_info.value.dependencies
        assert "python3" not in exc_info.value.dependencies

    def test_empty_dependencies_list(self) -> None:
        """Test with empty list (should succeed)."""
        check_dependencies([])  # Should not raise


class TestMissingDependencyError:
    """Tests for MissingDependencyError exception."""

    def test_error_message(self) -> None:
        """Test error message format."""
        error = MissingDependencyError(["cmd1", "cmd2"])

        assert "cmd1" in str(error)
        assert "cmd2" in str(error)
        assert error.dependencies == ["cmd1", "cmd2"]


class TestRunCommand:
    """Tests for run_command function."""

    def test_successful_command(self) -> None:
        """Test running a successful command."""
        result = run_command(["echo", "hello"], capture_output=True)

        assert result.returncode == 0
        assert "hello" in result.stdout

    def test_command_with_cwd(self, tmp_path: Path) -> None:
        """Test running command in specific directory."""
        result = run_command(["pwd"], cwd=tmp_path, capture_output=True)

        assert str(tmp_path) in result.stdout

    def test_failed_command_raises_error(self) -> None:
        """Test that failed command raises CommandError."""
        with pytest.raises(CommandError) as exc_info:
            run_command(["false"], capture_output=True)

        assert exc_info.value.returncode != 0

    def test_failed_command_with_check_false(self) -> None:
        """Test that check=False doesn't raise."""
        result = run_command(["false"], check=False)

        assert result.returncode != 0

    def test_command_with_env(self) -> None:
        """Test passing environment variables."""
        result = run_command(
            ["sh", "-c", "echo $TEST_VAR"],
            env={"TEST_VAR": "test_value"},
            capture_output=True,
        )

        assert "test_value" in result.stdout

    def test_quiet_mode_suppresses_logging(self) -> None:
        """Test that quiet=True suppresses error logging."""
        # This should not print error messages
        with pytest.raises(CommandError):
            run_command(["false"], capture_output=True, quiet=True)


class TestCommandError:
    """Tests for CommandError exception."""

    def test_error_attributes(self) -> None:
        """Test CommandError has correct attributes."""
        error = CommandError(
            command="test command",
            returncode=1,
            stdout="output",
            stderr="error output",
        )

        assert error.command == "test command"
        assert error.returncode == 1
        assert error.stdout == "output"
        assert error.stderr == "error output"

    def test_error_message(self) -> None:
        """Test error message format."""
        error = CommandError(command="failing cmd", returncode=42)

        assert "42" in str(error)
        assert "failing cmd" in str(error)


class TestCommandRunner:
    """Tests for CommandRunner class."""

    def test_run_with_default_cwd(self, tmp_path: Path) -> None:
        """Test runner uses default cwd."""
        runner = CommandRunner(cwd=tmp_path)
        result = runner.run(["pwd"], capture_output=True)

        assert str(tmp_path) in result.stdout

    def test_run_with_base_env(self) -> None:
        """Test runner uses base environment."""
        runner = CommandRunner(env={"BASE_VAR": "base_value"})
        result = runner.run(
            ["sh", "-c", "echo $BASE_VAR"],
            capture_output=True,
        )

        assert "base_value" in result.stdout

    def test_run_merges_env(self) -> None:
        """Test that per-call env is merged with base env."""
        runner = CommandRunner(env={"BASE": "base"})
        result = runner.run(
            ["sh", "-c", "echo $BASE $EXTRA"],
            env={"EXTRA": "extra"},
            capture_output=True,
        )

        assert "base" in result.stdout
        assert "extra" in result.stdout

    def test_run_or_none_success(self) -> None:
        """Test run_or_none returns result on success."""
        runner = CommandRunner()
        result = runner.run_or_none(["echo", "test"])

        assert result is not None
        assert result.returncode == 0

    def test_run_or_none_failure(self) -> None:
        """Test run_or_none returns None on failure."""
        runner = CommandRunner()
        result = runner.run_or_none(["false"])

        assert result is None

    def test_override_cwd(self, tmp_path: Path) -> None:
        """Test that cwd can be overridden per-call."""
        other_dir = tmp_path / "other"
        other_dir.mkdir()

        runner = CommandRunner(cwd=tmp_path)
        result = runner.run(["pwd"], cwd=other_dir, capture_output=True)

        assert str(other_dir) in result.stdout
