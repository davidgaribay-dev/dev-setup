"""Claude development VMs deployment orchestrator."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING

from harness.core.logger import log
from harness.deployers.base import BaseDeployer

if TYPE_CHECKING:
    from harness.infra import OpenTofuManager


class ClaudeVMsDeployer(BaseDeployer):
    """Handles Claude development VMs deployment."""

    def __init__(
        self,
        config,
        verbose: bool = False,
        count: int | None = None,
        prefix: str | None = None,
        start_id: int | None = None,
        neo4j_ip: str | None = None,
    ):
        """Initialize the Claude VMs deployer.

        Args:
            config: Application configuration.
            verbose: Enable verbose output.
            count: Number of VMs to create.
            prefix: VM name prefix.
            start_id: Starting VM ID.
            neo4j_ip: Override Neo4j IP address.
        """
        super().__init__(config, verbose)

        # VM configuration
        self.count = count or config.claude_vms.default_count
        self.prefix = prefix or config.claude_vms.prefix
        self.start_id = start_id or config.claude_vms.start_id

        # Neo4j IP (priority: parameter > env var > config)
        self._neo4j_ip_override = neo4j_ip

        # Validate inputs
        if self.count < 1 or self.count > 50:
            raise ValueError(f"VM count must be between 1 and 50, got {self.count}")
        if len(self.prefix) < 1 or len(self.prefix) > 20:
            raise ValueError(f"VM prefix must be 1-20 characters, got '{self.prefix}'")
        if self.start_id < 100 or self.start_id > 999999999:
            raise ValueError(f"Start ID must be between 100 and 999999999, got {self.start_id}")

    @property
    def component_name(self) -> str:
        return "Claude Development VMs"

    @property
    def provision_dir(self) -> Path:
        return self.config.claude_vms_dir / "provision"

    @property
    def config_dir(self) -> Path:
        return self.config.claude_vms_dir / "configuration"

    @property
    def inventory_file(self) -> Path:
        return self.config_dir / "inventory" / "hosts.json"

    @property
    def neo4j_ip(self) -> str:
        """Get the Neo4j IP address."""
        if self._neo4j_ip_override:
            return self._neo4j_ip_override
        return os.environ.get("NEO4J_IP", self.config.neo4j.ip)

    @property
    def vms_config(self) -> dict[str, dict[str, int]]:
        """Generate VM configuration for OpenTofu."""
        return self.config.claude_vms.generate_vms(
            count=self.count,
            prefix=self.prefix,
            start_id=self.start_id,
        )

    def _log_configuration(self, **kwargs) -> None:
        """Log deployment configuration."""
        log.info("Configuration:")
        log.bullet(f"VM Count: {self.count}")
        log.bullet(f"VM Prefix: {self.prefix}")
        log.bullet(f"Start ID: {self.start_id}")
        log.bullet(f"Neo4j IP: {self.neo4j_ip}")
        log.info("VMs to create:")
        for vm_name, vm_config in self.vms_config.items():
            log.bullet(f"{vm_name} (ID: {vm_config['vm_id']})")

    @property
    def _tofu_variables(self) -> dict:
        """Get variables to pass to OpenTofu."""
        return {
            "vms": self.vms_config,
            "cloud_init_user": self.config.ssh.cloud_init_user,
        }

    def _provision(self, **kwargs) -> None:
        """Provision the Claude VMs."""
        tofu = self.get_tofu_manager()
        tofu.init()
        tofu.plan(variables=self._tofu_variables)
        tofu.apply(variables=self._tofu_variables)
        tofu.export_inventory()

    def _wait_for_vms(self, skip_provision: bool = False, **kwargs) -> None:
        """Wait for VMs to acquire IPs and become SSH accessible.

        Args:
            skip_provision: Whether provisioning was skipped.
            **kwargs: Additional arguments.
        """
        import time

        if skip_provision:
            # Just wait for SSH if skipping provision
            ssh_waiter = self.get_ssh_waiter()
            successful, failed = ssh_waiter.wait_for_inventory(self.inventory_file)
            if failed:
                raise RuntimeError(f"{len(failed)} VM(s) failed to become accessible: {failed}")
            log.success(f"All {len(successful)} VM(s) are accessible")
            return

        tofu = self.get_tofu_manager()
        max_wait = 120  # seconds
        poll_interval = 10
        elapsed = 0

        log.info("Waiting for VMs to acquire IP addresses...")

        while elapsed < max_wait:
            tofu.refresh(variables=self._tofu_variables)
            tofu.export_inventory()

            if self._all_vms_have_ips():
                log.success("All VMs have acquired IP addresses")
                break

            time.sleep(poll_interval)
            elapsed += poll_interval
            log.info(f"Still waiting for IPs... ({elapsed}s elapsed)")
        else:
            raise RuntimeError(f"VMs did not acquire IPs within {max_wait} seconds")

        # Now wait for SSH
        ssh_waiter = self.get_ssh_waiter()
        successful, failed = ssh_waiter.wait_for_inventory(self.inventory_file)
        if failed:
            raise RuntimeError(f"{len(failed)} VM(s) failed to become accessible: {failed}")
        log.success(f"All {len(successful)} VM(s) are accessible")

    def _all_vms_have_ips(self) -> bool:
        """Check if all VMs in inventory have IP addresses."""
        if not self.inventory_file.exists():
            return False
        with open(self.inventory_file) as f:
            inventory = json.load(f)
        hosts = inventory.get("all", {}).get("hosts", {})
        if not hosts:
            return False
        return all(info.get("ansible_host") is not None for info in hosts.values())

    def _configure(self, skip_hardening: bool = False, **kwargs) -> None:
        """Configure VMs using Ansible.

        Args:
            skip_hardening: Skip hardening roles.
            **kwargs: Additional arguments.
        """
        ansible = self.get_ansible_manager()
        ansible.install_requirements()

        # Build extra vars
        extra_vars = {
            "neo4j_ip": self.neo4j_ip,
            "cloud_init_user": self.config.ssh.cloud_init_user,
        }

        # Add GitHub token if set
        gh_token = os.environ.get("ANSIBLE_GH_TOKEN")
        if gh_token:
            log.info("Passing GitHub token to playbook")
            extra_vars["gh_token"] = gh_token

        # Add Neo4j password if set
        neo4j_password = os.environ.get("NEO4J_PASSWORD")
        if neo4j_password:
            extra_vars["neo4j_password"] = neo4j_password

        skip_tags = ["hardening"] if skip_hardening else None
        if skip_hardening:
            log.warn("Skipping hardening roles")

        ansible.run_playbook(extra_vars=extra_vars, skip_tags=skip_tags)

    def _destroy(self, tofu: OpenTofuManager, **kwargs) -> None:
        """Destroy the Claude VMs."""
        tofu.destroy(variables=self._tofu_variables)
        log.success("All Claude VMs destroyed")

    def _plan(self, **kwargs) -> None:
        """Show the infrastructure plan without applying."""
        tofu = self.get_tofu_manager()
        tofu.init()
        tofu.plan(variables=self._tofu_variables)

    def _log_summary(self, **kwargs) -> None:
        """Log VM IP addresses and connection info."""
        self._show_vm_ips()
        log.info(f"Neo4j MCP configured to connect to: bolt://{self.neo4j_ip}:7687")

    def _show_vm_ips(self) -> None:
        """Display VM IP addresses from inventory."""
        if not self.inventory_file.exists():
            return

        with open(self.inventory_file) as f:
            inventory = json.load(f)

        hosts = inventory.get("all", {}).get("hosts", {})
        if hosts:
            log.info("VM IP Addresses:")
            for name, info in hosts.items():
                ip = info.get("ansible_host", "N/A")
                log.bullet(f"{name}: {ip}")

    def deploy(
        self,
        skip_provision: bool = False,
        skip_configure: bool = False,
        skip_hardening: bool = False,
        **kwargs,
    ):
        """Deploy Claude VMs.

        Args:
            skip_provision: Skip OpenTofu provisioning.
            skip_configure: Skip Ansible configuration.
            skip_hardening: Skip hardening roles.
            **kwargs: Additional arguments.

        Returns:
            DeploymentResult indicating success/failure.
        """
        return super().deploy(
            skip_provision=skip_provision,
            skip_configure=skip_configure,
            skip_hardening=skip_hardening,
            **kwargs,
        )
