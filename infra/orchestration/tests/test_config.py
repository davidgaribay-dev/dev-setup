"""Tests for configuration loading and validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from harness.core.config import (
    ClaudeVMsConfig,
    Config,
    Neo4jConfig,
    NetworkConfig,
    ProxmoxConfig,
    SSHConfig,
    load_config,
)


class TestLoadConfig:
    """Tests for load_config function."""

    def test_load_config_success(self, config_file: Path) -> None:
        """Test loading a valid config file."""
        config = load_config(config_file)

        assert config["neo4j"]["ip"] == "10.0.70.50"
        assert config["claude_vms"]["prefix"] == "claude-dev"
        assert config["ssh"]["user"] == "dmg"

    def test_load_config_file_not_found(self, tmp_path: Path) -> None:
        """Test error when config file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            load_config(tmp_path / "nonexistent.yaml")


class TestNeo4jConfig:
    """Tests for Neo4jConfig dataclass."""

    def test_bolt_uri(self, sample_config: dict[str, Any]) -> None:
        """Test bolt_uri property."""
        config = Neo4jConfig(**sample_config["neo4j"])

        assert config.bolt_uri == "bolt://10.0.70.50:7687"

    def test_http_uri(self, sample_config: dict[str, Any]) -> None:
        """Test http_uri property."""
        config = Neo4jConfig(**sample_config["neo4j"])

        assert config.http_uri == "http://10.0.70.50:7474"


class TestClaudeVMsConfig:
    """Tests for ClaudeVMsConfig dataclass."""

    def test_generate_vms_default(self, sample_config: dict[str, Any]) -> None:
        """Test VM generation with default values."""
        config = ClaudeVMsConfig(**sample_config["claude_vms"])
        vms = config.generate_vms()

        assert len(vms) == 1
        assert "claude-dev-1" in vms
        assert vms["claude-dev-1"]["vm_id"] == 200

    def test_generate_vms_custom_count(self, sample_config: dict[str, Any]) -> None:
        """Test VM generation with custom count."""
        config = ClaudeVMsConfig(**sample_config["claude_vms"])
        vms = config.generate_vms(count=3)

        assert len(vms) == 3
        assert "claude-dev-1" in vms
        assert "claude-dev-2" in vms
        assert "claude-dev-3" in vms
        assert vms["claude-dev-1"]["vm_id"] == 200
        assert vms["claude-dev-2"]["vm_id"] == 201
        assert vms["claude-dev-3"]["vm_id"] == 202

    def test_generate_vms_custom_prefix(self, sample_config: dict[str, Any]) -> None:
        """Test VM generation with custom prefix."""
        config = ClaudeVMsConfig(**sample_config["claude_vms"])
        vms = config.generate_vms(count=2, prefix="myvm")

        assert "myvm-1" in vms
        assert "myvm-2" in vms

    def test_generate_vms_custom_start_id(self, sample_config: dict[str, Any]) -> None:
        """Test VM generation with custom start ID."""
        config = ClaudeVMsConfig(**sample_config["claude_vms"])
        vms = config.generate_vms(count=2, start_id=500)

        assert vms["claude-dev-1"]["vm_id"] == 500
        assert vms["claude-dev-2"]["vm_id"] == 501


class TestConfig:
    """Tests for main Config class."""

    def test_from_yaml(self, config_file: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test creating Config from YAML file."""
        config = Config.from_yaml(config_file)

        assert isinstance(config.neo4j, Neo4jConfig)
        assert isinstance(config.claude_vms, ClaudeVMsConfig)
        assert isinstance(config.network, NetworkConfig)
        assert isinstance(config.proxmox, ProxmoxConfig)
        assert isinstance(config.ssh, SSHConfig)

    def test_neo4j_properties(self, config_file: Path) -> None:
        """Test Neo4j config properties."""
        config = Config.from_yaml(config_file)

        assert config.neo4j.ip == "10.0.70.50"
        assert config.neo4j.bolt_port == 7687
        assert config.neo4j.vm_id == 150

    def test_ssh_properties(self, config_file: Path) -> None:
        """Test SSH config properties."""
        config = Config.from_yaml(config_file)

        assert config.ssh.user == "dmg"
        assert config.ssh.timeout == 300
        assert config.ssh.retry_interval == 10
