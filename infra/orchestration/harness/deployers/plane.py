"""Plane deployment orchestrator."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from harness.core.logger import log
from harness.deployers.base import BaseDeployer

if TYPE_CHECKING:
    from harness.infra import OpenTofuManager


class PlaneDeployer(BaseDeployer):
    """Handles Plane project management server deployment."""

    @property
    def component_name(self) -> str:
        return "Plane Project Management Server"

    @property
    def provision_dir(self) -> Path:
        return self.config.plane_dir / "provision"

    @property
    def config_dir(self) -> Path:
        return self.config.plane_dir / "configuration"

    @property
    def inventory_file(self) -> Path:
        return self.config_dir / "inventory" / "hosts.json"

    def _log_configuration(self, **kwargs) -> None:
        """Log Plane deployment configuration."""
        log.info("Configuration:")
        log.bullet(f"VM ID: {self.config.plane.vm_id}")
        log.bullet(f"VM Name: {self.config.plane.vm_name}")
        log.bullet(f"IP Address: {self.config.plane.ip}")
        log.bullet(f"HTTP Port: {self.config.plane.http_port}")
        log.bullet(f"HTTPS Port: {self.config.plane.https_port}")

    def _provision(self, **kwargs) -> None:
        """Provision the Plane VM."""
        tofu = self.get_tofu_manager()
        tofu.init()
        tofu.plan()
        tofu.apply()
        tofu.export_inventory()

    def _configure(self, **kwargs) -> None:
        """Configure Plane using Ansible."""
        ansible = self.get_ansible_manager()
        ansible.install_requirements()
        ansible.run_playbook()

    def _destroy(self, tofu: OpenTofuManager, **kwargs) -> None:
        """Destroy the Plane VM."""
        tofu.destroy()
        log.success("Plane VM destroyed")

    def _log_summary(self, **kwargs) -> None:
        """Log Plane connection information."""
        log.success("Plane is available at:")
        log.bullet(f"HTTP: {self.config.plane.http_uri}")
        log.bullet(f"HTTPS: {self.config.plane.https_uri}")
        log.info("")
        log.info("Next steps:")
        log.bullet("1. Visit the HTTPS URL in your browser")
        log.bullet("2. Complete the initial setup and create an admin account")
        log.bullet("3. Generate an API key for MCP integration")
