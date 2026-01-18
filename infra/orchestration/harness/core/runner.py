"""Command execution utilities."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from harness.core.logger import log

if TYPE_CHECKING:
    from collections.abc import Sequence


class CommandError(Exception):
    """Raised when a command fails."""

    def __init__(
        self,
        command: str,
        returncode: int,
        stdout: str | None = None,
        stderr: str | None = None,
    ):
        self.command = command
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr
        super().__init__(f"Command failed with exit code {returncode}: {command}")


class MissingDependencyError(Exception):
    """Raised when required dependencies are missing."""

    def __init__(self, dependencies: list[str]):
        self.dependencies = dependencies
        super().__init__(f"Missing required dependencies: {', '.join(dependencies)}")


def check_dependencies(dependencies: Sequence[str]) -> None:
    """Verify required tools are installed.

    Args:
        dependencies: List of command names to check.

    Raises:
        MissingDependencyError: If any dependencies are missing.
    """
    missing = [dep for dep in dependencies if shutil.which(dep) is None]
    if missing:
        raise MissingDependencyError(missing)


def run_command(
    cmd: Sequence[str],
    cwd: Path | None = None,
    check: bool = True,
    capture_output: bool = False,
    env: dict[str, str] | None = None,
    quiet: bool = False,
    timeout: int | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run a command with proper error handling.

    Args:
        cmd: Command and arguments as a sequence.
        cwd: Working directory for the command.
        check: Whether to raise on non-zero exit code.
        capture_output: Whether to capture stdout/stderr.
        env: Additional environment variables (merged with current env).
        quiet: If True, suppress error logging on failure.
        timeout: Maximum seconds to wait for command completion.

    Returns:
        CompletedProcess instance with command results.

    Raises:
        CommandError: If check=True and command fails.
        subprocess.TimeoutExpired: If command exceeds timeout.
    """
    run_env = os.environ.copy()
    if env:
        run_env.update(env)

    try:
        result = subprocess.run(
            list(cmd),
            cwd=cwd,
            check=check,
            capture_output=capture_output,
            text=True,
            env=run_env,
            timeout=timeout,
        )
        return result
    except subprocess.CalledProcessError as e:
        if not quiet:
            log.error(f"Command failed: {' '.join(cmd)}")
            if e.stdout:
                print(e.stdout)
            if e.stderr:
                print(e.stderr, file=sys.stderr)
        raise CommandError(
            command=" ".join(cmd),
            returncode=e.returncode,
            stdout=e.stdout if capture_output else None,
            stderr=e.stderr if capture_output else None,
        ) from e


class CommandRunner:
    """Executes commands with consistent environment and error handling."""

    def __init__(
        self,
        cwd: Path | None = None,
        env: dict[str, str] | None = None,
        verbose: bool = False,
    ):
        """Initialize the command runner.

        Args:
            cwd: Default working directory for commands.
            env: Additional environment variables for all commands.
            verbose: Whether to enable verbose output.
        """
        self.cwd = cwd
        self.base_env = env or {}
        self.verbose = verbose

    def run(
        self,
        cmd: Sequence[str],
        cwd: Path | None = None,
        check: bool = True,
        capture_output: bool = False,
        env: dict[str, str] | None = None,
        quiet: bool = False,
        timeout: int | None = None,
    ) -> subprocess.CompletedProcess[str]:
        """Run a command.

        Args:
            cmd: Command and arguments.
            cwd: Working directory (overrides default).
            check: Whether to raise on non-zero exit.
            capture_output: Whether to capture output.
            env: Additional environment variables (merged with base_env).
            quiet: Suppress error logging.
            timeout: Maximum seconds to wait for command completion.

        Returns:
            CompletedProcess with results.
        """
        merged_env = {**self.base_env, **(env or {})}
        return run_command(
            cmd,
            cwd=cwd or self.cwd,
            check=check,
            capture_output=capture_output,
            env=merged_env if merged_env else None,
            quiet=quiet,
            timeout=timeout,
        )

    def run_or_none(
        self,
        cmd: Sequence[str],
        cwd: Path | None = None,
        capture_output: bool = True,
    ) -> subprocess.CompletedProcess[str] | None:
        """Run a command, returning None on failure instead of raising.

        Args:
            cmd: Command and arguments.
            cwd: Working directory.
            capture_output: Whether to capture output.

        Returns:
            CompletedProcess on success, None on failure.
        """
        try:
            return self.run(cmd, cwd=cwd, capture_output=capture_output, quiet=True)
        except CommandError:
            return None
