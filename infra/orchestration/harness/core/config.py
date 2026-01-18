"""Configuration management for Claude Code Harness."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


def get_project_root() -> Path:
    """Get the project root directory (claude-code-harness)."""
    return Path(__file__).parent.parent.parent.parent.resolve()


def get_orchestration_dir() -> Path:
    """Get the orchestration directory."""
    return Path(__file__).parent.parent.parent.resolve()


def load_config(config_path: Path | None = None) -> dict[str, Any]:
    """Load configuration from YAML file.

    Args:
        config_path: Path to config file. Defaults to orchestration/config.yaml.

    Returns:
        Configuration dictionary.

    Raises:
        FileNotFoundError: If config file doesn't exist.
    """
    if config_path is None:
        config_path = get_orchestration_dir() / "config.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path) as f:
        return yaml.safe_load(f)


@dataclass
class Neo4jConfig:
    """Neo4j-specific configuration."""

    ip: str
    bolt_port: int
    http_port: int
    username: str
    vm_id: int
    vm_name: str

    @property
    def bolt_uri(self) -> str:
        """Get the Bolt connection URI."""
        return f"bolt://{self.ip}:{self.bolt_port}"

    @property
    def http_uri(self) -> str:
        """Get the HTTP browser URI."""
        return f"http://{self.ip}:{self.http_port}"

    @property
    def password(self) -> str:
        """Get password from environment variable."""
        password = os.environ.get("NEO4J_PASSWORD")
        if not password:
            raise ValueError("NEO4J_PASSWORD environment variable is required")
        return password

    @property
    def admin_password(self) -> str:
        """Get admin password from environment variable."""
        password = os.environ.get("NEO4J_ADMIN_PASSWORD")
        if not password:
            raise ValueError("NEO4J_ADMIN_PASSWORD environment variable is required")
        return password


@dataclass
class PlaneConfig:
    """Plane-specific configuration."""

    ip: str
    http_port: int
    https_port: int
    vm_id: int
    vm_name: str

    @property
    def http_uri(self) -> str:
        """Get the HTTP URI."""
        return f"http://{self.ip}"

    @property
    def https_uri(self) -> str:
        """Get the HTTPS URI."""
        return f"https://{self.ip}"


@dataclass
class ClaudeVMsConfig:
    """Claude VMs configuration."""

    start_id: int
    default_count: int
    prefix: str

    def generate_vms(
        self,
        count: int | None = None,
        prefix: str | None = None,
        start_id: int | None = None,
    ) -> dict[str, dict[str, int]]:
        """Generate VM configuration dictionary for OpenTofu.

        Args:
            count: Number of VMs. Defaults to default_count.
            prefix: VM name prefix. Defaults to configured prefix.
            start_id: Starting VM ID. Defaults to configured start_id.

        Returns:
            Dictionary mapping VM names to their configurations.
        """
        count = count or self.default_count
        prefix = prefix or self.prefix
        start_id = start_id or self.start_id

        return {
            f"{prefix}-{i}": {"vm_id": start_id + i - 1} for i in range(1, count + 1)
        }


@dataclass
class NetworkConfig:
    """Network configuration."""

    subnet: str
    gateway: str
    bridge: str


@dataclass
class ProxmoxConfig:
    """Proxmox configuration."""

    node: str
    template_id: int
    datastore_id: str


@dataclass
class SSHConfig:
    """SSH configuration."""

    user: str
    timeout: int
    retry_interval: int
    cloud_init_user: str = "dmg"


@dataclass
class Config:
    """Main configuration container."""

    neo4j: Neo4jConfig
    plane: PlaneConfig
    claude_vms: ClaudeVMsConfig
    network: NetworkConfig
    proxmox: ProxmoxConfig
    ssh: SSHConfig
    _raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_yaml(cls, config_path: Path | None = None) -> Config:
        """Load configuration from YAML file.

        Args:
            config_path: Path to config file.

        Returns:
            Config instance.
        """
        raw = load_config(config_path)

        return cls(
            neo4j=Neo4jConfig(**raw["neo4j"]),
            plane=PlaneConfig(**raw["plane"]),
            claude_vms=ClaudeVMsConfig(**raw["claude_vms"]),
            network=NetworkConfig(**raw["network"]),
            proxmox=ProxmoxConfig(**raw["proxmox"]),
            ssh=SSHConfig(**raw["ssh"]),
            _raw=raw,
        )

    @property
    def project_root(self) -> Path:
        """Get project root directory."""
        return get_project_root()

    @property
    def orchestration_dir(self) -> Path:
        """Get orchestration directory."""
        return get_orchestration_dir()

    @property
    def neo4j_dir(self) -> Path:
        """Get Neo4j component directory."""
        return self.project_root / "neo4j"

    @property
    def plane_dir(self) -> Path:
        """Get Plane component directory."""
        return self.project_root / "plane"

    @property
    def claude_vms_dir(self) -> Path:
        """Get Claude VMs component directory."""
        return self.project_root / "claude-vms"

    def get_provision_dir(self, component: str) -> Path:
        """Get provision directory for a component.

        Args:
            component: Component name ('neo4j' or 'claude-vms').

        Returns:
            Path to the provision directory.
        """
        base = self.neo4j_dir if component == "neo4j" else self.claude_vms_dir
        return base / "provision"

    def get_config_dir(self, component: str) -> Path:
        """Get configuration directory for a component.

        Args:
            component: Component name ('neo4j' or 'claude-vms').

        Returns:
            Path to the configuration directory.
        """
        base = self.neo4j_dir if component == "neo4j" else self.claude_vms_dir
        return base / "configuration"

    def get_inventory_file(self, component: str) -> Path:
        """Get inventory file path for a component.

        Args:
            component: Component name ('neo4j' or 'claude-vms').

        Returns:
            Path to the inventory JSON file.
        """
        return self.get_config_dir(component) / "inventory" / "hosts.json"
