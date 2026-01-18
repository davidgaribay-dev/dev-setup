"""OpenTofu/Terraform infrastructure management."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from harness.core.logger import log
from harness.core.runner import CommandRunner

if TYPE_CHECKING:
    pass


class OpenTofuManager:
    """Manages OpenTofu operations for infrastructure provisioning."""

    def __init__(
        self,
        provision_dir: Path,
        inventory_file: Path,
        verbose: bool = False,
    ):
        """Initialize the OpenTofu manager.

        Args:
            provision_dir: Directory containing Terraform/OpenTofu files.
            inventory_file: Path where Ansible inventory will be written.
            verbose: Enable verbose logging (TF_LOG=INFO).
        """
        self.provision_dir = provision_dir
        self.inventory_file = inventory_file
        self.verbose = verbose

        env = {"TF_LOG": "INFO"} if verbose else {}
        self.runner = CommandRunner(cwd=provision_dir, env=env)

    def init(self, upgrade: bool = True) -> None:
        """Initialize OpenTofu.

        Args:
            upgrade: Whether to upgrade providers.
        """
        log.info("Initializing OpenTofu...")
        cmd = ["tofu", "init"]
        if upgrade:
            cmd.append("-upgrade")
        self.runner.run(cmd)

    def plan(self, variables: dict[str, Any] | None = None) -> None:
        """Create an execution plan.

        Args:
            variables: Variables to pass to OpenTofu.
        """
        log.info("Planning infrastructure...")
        cmd = ["tofu", "plan"]
        cmd.extend(self._build_var_args(variables))
        cmd.extend(["-out=tfplan"])
        self.runner.run(cmd)

    def apply(
        self,
        variables: dict[str, Any] | None = None,
        parallelism: int = 1,
    ) -> None:
        """Apply the planned changes.

        Args:
            variables: Variables to pass to OpenTofu.
            parallelism: Number of parallel operations (default 1 for Proxmox).
        """
        log.info(f"Applying infrastructure changes (parallelism={parallelism})...")
        cmd = ["tofu", "apply", f"-parallelism={parallelism}"]
        cmd.extend(self._build_var_args(variables))
        cmd.append("tfplan")
        self.runner.run(cmd)

        log.success("Infrastructure apply completed")
        self._cleanup_plan_file()

    def destroy(
        self,
        variables: dict[str, Any] | None = None,
        parallelism: int = 1,
    ) -> None:
        """Destroy infrastructure.

        Args:
            variables: Variables to pass to OpenTofu.
            parallelism: Number of parallel operations.
        """
        log.warn("Destroying infrastructure...")
        cmd = ["tofu", "destroy", "-auto-approve", f"-parallelism={parallelism}"]
        cmd.extend(self._build_var_args(variables))
        self.runner.run(cmd)
        log.success("Infrastructure destroyed")

    def refresh(self, variables: dict[str, Any] | None = None) -> None:
        """Refresh state to get updated values.

        Args:
            variables: Variables to pass to OpenTofu.
        """
        log.info("Refreshing state...")
        cmd = ["tofu", "refresh"]
        cmd.extend(self._build_var_args(variables))
        self.runner.run(cmd)

    def get_output(self, name: str) -> str:
        """Get a specific output value.

        Args:
            name: Output name.

        Returns:
            Output value as string.
        """
        result = self.runner.run(
            ["tofu", "output", "-raw", name],
            capture_output=True,
        )
        return result.stdout.strip()

    def get_outputs(self) -> dict[str, Any]:
        """Get all outputs as a dictionary.

        Returns:
            Dictionary of all outputs.
        """
        result = self.runner.run(
            ["tofu", "output", "-json"],
            capture_output=True,
        )
        return json.loads(result.stdout)

    def get_inventory(self) -> dict[str, Any]:
        """Get Ansible inventory from OpenTofu output.

        Returns:
            Ansible inventory dictionary.
        """
        inventory_json = self.get_output("ansible_inventory")
        return json.loads(inventory_json)

    def export_inventory(self) -> None:
        """Export inventory to JSON file for Ansible."""
        log.info("Exporting Ansible inventory...")

        self.inventory_file.parent.mkdir(parents=True, exist_ok=True)
        inventory = self.get_inventory()

        with open(self.inventory_file, "w") as f:
            json.dump(inventory, f, indent=2)

        log.success(f"Inventory written to {self.inventory_file}")

    def _build_var_args(self, variables: dict[str, Any] | None) -> list[str]:
        """Build -var arguments from a dictionary.

        Args:
            variables: Variables dictionary.

        Returns:
            List of -var=key=value arguments.
        """
        if not variables:
            return []

        args = []
        for key, value in variables.items():
            if isinstance(value, (dict, list)):
                json_value = json.dumps(value)
                args.append(f"-var={key}={json_value}")
            else:
                args.append(f"-var={key}={value}")
        return args

    def _cleanup_plan_file(self) -> None:
        """Remove the plan file after apply."""
        plan_file = self.provision_dir / "tfplan"
        if plan_file.exists():
            plan_file.unlink()
