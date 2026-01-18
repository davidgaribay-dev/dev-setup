"""Pytest fixtures for harness tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest


@pytest.fixture
def sample_config() -> dict[str, Any]:
    """Sample configuration matching config.yaml structure."""
    return {
        "neo4j": {
            "ip": "10.0.70.50",
            "bolt_port": 7687,
            "http_port": 7474,
            "username": "neo4j",
            "vm_id": 150,
            "vm_name": "neo4j-db",
        },
        "claude_vms": {
            "start_id": 200,
            "default_count": 1,
            "prefix": "claude-dev",
        },
        "network": {
            "subnet": "10.0.70.0/24",
            "gateway": "10.0.70.1",
            "bridge": "vmbr1",
        },
        "proxmox": {
            "node": "pve1",
            "template_id": 100,
            "datastore_id": "local-lvm",
        },
        "ssh": {
            "user": "dmg",
            "timeout": 300,
            "retry_interval": 10,
        },
    }


@pytest.fixture
def config_file(tmp_path: Path, sample_config: dict[str, Any]) -> Path:
    """Create a temporary config.yaml file."""
    import yaml

    config_path = tmp_path / "config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(sample_config, f)
    return config_path


@pytest.fixture
def sample_inventory() -> dict[str, Any]:
    """Sample Ansible inventory structure."""
    return {
        "all": {
            "hosts": {
                "claude-dev-1": {
                    "ansible_host": "10.0.70.101",
                    "ansible_user": "dmg",
                },
                "claude-dev-2": {
                    "ansible_host": "10.0.70.102",
                    "ansible_user": "dmg",
                },
            }
        }
    }


@pytest.fixture
def inventory_file(tmp_path: Path, sample_inventory: dict[str, Any]) -> Path:
    """Create a temporary inventory file."""
    inventory_dir = tmp_path / "inventory"
    inventory_dir.mkdir()
    inventory_path = inventory_dir / "hosts.json"
    with open(inventory_path, "w") as f:
        json.dump(sample_inventory, f)
    return inventory_path
