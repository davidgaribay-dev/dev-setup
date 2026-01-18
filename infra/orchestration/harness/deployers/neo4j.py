"""Neo4j deployment orchestrator."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from harness.core.logger import log
from harness.deployers.base import BaseDeployer

if TYPE_CHECKING:
    from harness.infra import OpenTofuManager


class Neo4jDeployer(BaseDeployer):
    """Handles Neo4j database server deployment."""

    @property
    def component_name(self) -> str:
        return "Neo4j Database Server"

    @property
    def provision_dir(self) -> Path:
        return self.config.neo4j_dir / "provision"

    @property
    def config_dir(self) -> Path:
        return self.config.neo4j_dir / "configuration"

    @property
    def inventory_file(self) -> Path:
        return self.config_dir / "inventory" / "hosts.json"

    def _log_configuration(self, **kwargs) -> None:
        """Log Neo4j deployment configuration."""
        log.info("Configuration:")
        log.bullet(f"VM ID: {self.config.neo4j.vm_id}")
        log.bullet(f"VM Name: {self.config.neo4j.vm_name}")
        log.bullet(f"IP Address: {self.config.neo4j.ip}")
        log.bullet(f"Bolt Port: {self.config.neo4j.bolt_port}")
        log.bullet(f"HTTP Port: {self.config.neo4j.http_port}")

    def _provision(self, **kwargs) -> None:
        """Provision the Neo4j VM."""
        tofu = self.get_tofu_manager()
        tofu.init()
        tofu.plan()
        tofu.apply()
        tofu.export_inventory()

    def _configure(self, **kwargs) -> None:
        """Configure Neo4j using Ansible."""
        ansible = self.get_ansible_manager()
        ansible.install_requirements()
        ansible.run_playbook()

    def _destroy(self, tofu: OpenTofuManager, **kwargs) -> None:
        """Destroy the Neo4j VM."""
        tofu.destroy()
        log.success("Neo4j VM destroyed")

    def _log_summary(self, **kwargs) -> None:
        """Log Neo4j connection information."""
        log.success("Neo4j is available at:")
        log.bullet(f"Bolt: {self.config.neo4j.bolt_uri}")
        log.bullet(f"HTTP: {self.config.neo4j.http_uri}")
        log.bullet(f"Username: {self.config.neo4j.username}")
