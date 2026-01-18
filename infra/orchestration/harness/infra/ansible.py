"""Ansible configuration management."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from harness.core.logger import log
from harness.core.runner import CommandRunner

if TYPE_CHECKING:
    pass


class AnsibleManager:
    """Manages Ansible operations for configuration management."""

    def __init__(self, config_dir: Path):
        """Initialize the Ansible manager.

        Args:
            config_dir: Directory containing Ansible files (playbook.yml, etc).
        """
        self.config_dir = config_dir
        self.runner = CommandRunner(cwd=config_dir)

    def install_requirements(self, force: bool = True) -> None:
        """Install Ansible collections and roles from requirements.yml.

        Args:
            force: Force reinstall even if already present.
        """
        requirements_file = self.config_dir / "requirements.yml"
        if not requirements_file.exists():
            log.warn("No requirements.yml found, skipping dependency installation")
            return

        log.info("Installing Ansible collections...")
        cmd = ["ansible-galaxy", "collection", "install", "-r", "requirements.yml"]
        if force:
            cmd.append("--force")
        self.runner.run(cmd)

        log.info("Installing Ansible roles...")
        cmd = ["ansible-galaxy", "role", "install", "-r", "requirements.yml"]
        if force:
            cmd.append("--force")
        self.runner.run(cmd)

    def run_playbook(
        self,
        playbook: str = "playbook.yml",
        extra_vars: dict[str, str] | None = None,
        skip_tags: list[str] | None = None,
        tags: list[str] | None = None,
        verbosity: int = 1,
        timeout: int = 3600,
    ) -> None:
        """Run an Ansible playbook.

        Args:
            playbook: Name of the playbook file.
            extra_vars: Extra variables to pass with -e.
            skip_tags: Tags to skip.
            tags: Tags to run (only these tags will be executed).
            verbosity: Verbosity level (number of -v flags).
            timeout: Maximum seconds to wait for playbook completion (default 1 hour).
        """
        log.info(f"Running Ansible playbook: {playbook}")

        cmd = ["ansible-playbook", playbook]

        # Add verbosity
        if verbosity > 0:
            cmd.append("-" + "v" * verbosity)

        # Add extra variables
        if extra_vars:
            for key, value in extra_vars.items():
                cmd.extend(["-e", f"{key}={value}"])

        # Add skip-tags
        if skip_tags:
            cmd.extend(["--skip-tags", ",".join(skip_tags)])

        # Add tags
        if tags:
            cmd.extend(["--tags", ",".join(tags)])

        self.runner.run(cmd, timeout=timeout)
        log.success("Playbook completed successfully")

    def check_syntax(self, playbook: str = "playbook.yml") -> bool:
        """Check playbook syntax.

        Args:
            playbook: Name of the playbook file.

        Returns:
            True if syntax is valid.
        """
        log.info(f"Checking syntax: {playbook}")
        result = self.runner.run_or_none(
            ["ansible-playbook", "--syntax-check", playbook],
        )
        return result is not None
