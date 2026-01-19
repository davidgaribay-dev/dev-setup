"""Core Services (Plane + Rewind) deployment orchestrator."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from harness.core.logger import log
from harness.deployers.base import BaseDeployer

if TYPE_CHECKING:
    from harness.infra import OpenTofuManager


class CoreServicesDeployer(BaseDeployer):
    """Handles Core Services (Plane + Rewind) deployment."""

    @property
    def component_name(self) -> str:
        return "Core Services (Plane + Rewind)"

    @property
    def provision_dir(self) -> Path:
        return self.config.core_services_dir / "provision"

    @property
    def config_dir(self) -> Path:
        return self.config.core_services_dir / "configuration"

    @property
    def inventory_file(self) -> Path:
        return self.config_dir / "inventory" / "hosts.json"

    def _log_configuration(self, **kwargs) -> None:
        """Log Core Services deployment configuration."""
        log.info("Configuration:")
        log.bullet(f"VM ID: {self.config.core_services.vm_id}")
        log.bullet(f"VM Name: {self.config.core_services.vm_name}")
        log.bullet(f"IP Address: {self.config.core_services.ip}")
        log.bullet(f"Plane HTTPS Port: {self.config.core_services.https_port}")
        log.bullet(f"Rewind API Port: {self.config.core_services.rewind_api_port}")
        log.bullet(f"Rewind Web Port: {self.config.core_services.rewind_web_port}")
        log.bullet(f"Neo4j IP: {self.config.neo4j.ip}")

    def _provision(self, **kwargs) -> None:
        """Provision the Core Services VM."""
        tofu = self.get_tofu_manager()
        tofu.init()
        tofu.plan()
        tofu.apply()
        tofu.export_inventory()

    def _configure(self, **kwargs) -> None:
        """Configure Core Services using Ansible."""
        ansible = self.get_ansible_manager()
        ansible.install_requirements()
        # Pass Neo4j IP from central config to ensure consistency
        extra_vars = {
            "neo4j_ip": self.config.neo4j.ip,
        }
        ansible.run_playbook(extra_vars=extra_vars)

    def _destroy(self, tofu: OpenTofuManager, **kwargs) -> None:
        """Destroy the Core Services VM."""
        tofu.destroy()
        log.success("Core Services VM destroyed")

    def _log_summary(self, **kwargs) -> None:
        """Log Core Services connection information."""
        log.success("Core Services are available at:")
        log.bullet(f"Plane: {self.config.core_services.https_uri}")
        log.bullet(f"Rewind API: {self.config.core_services.rewind_api_uri}")
        log.bullet(f"Rewind Web: {self.config.core_services.rewind_web_uri}")
        log.info("")
        log.info("Next steps:")
        log.bullet("1. Visit Plane HTTPS URL in your browser")
        log.bullet("2. Complete the initial setup and create an admin account")
        log.bullet("3. Generate an API key for MCP integration")
        log.bullet("4. Visit Rewind Web URL to view conversation history")
