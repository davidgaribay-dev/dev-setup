"""SSH connectivity management."""

from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

from harness.core.logger import log


class SSHWaiter:
    """Handles waiting for SSH connectivity on hosts."""

    def __init__(
        self,
        user: str,
        timeout: int = 300,
        retry_interval: int = 10,
    ):
        """Initialize the SSH waiter.

        Args:
            user: SSH username.
            timeout: Maximum time to wait for SSH in seconds.
            retry_interval: Time between SSH connection attempts.
        """
        self.user = user
        self.timeout = timeout
        self.retry_interval = retry_interval

    def wait_for_host(self, host: str) -> bool:
        """Wait for SSH to become available on a host.

        Args:
            host: IP address or hostname.

        Returns:
            True if SSH becomes available, False on timeout.
        """
        log.info(f"Waiting for SSH on {host}...")
        elapsed = 0

        while elapsed < self.timeout:
            if self._try_connect(host):
                log.success(f"SSH available on {host}")
                return True

            time.sleep(self.retry_interval)
            elapsed += self.retry_interval

        log.error(f"Timeout waiting for SSH on {host}")
        return False

    def wait_for_hosts(self, hosts: list[str]) -> tuple[list[str], list[str]]:
        """Wait for SSH on multiple hosts.

        Args:
            hosts: List of IP addresses or hostnames.

        Returns:
            Tuple of (successful_hosts, failed_hosts).
        """
        log.info(f"Waiting for SSH on {len(hosts)} host(s)...")

        successful = []
        failed = []

        for host in hosts:
            if self.wait_for_host(host):
                successful.append(host)
            else:
                failed.append(host)

        return successful, failed

    def wait_for_inventory(self, inventory_file: Path) -> tuple[list[str], list[str]]:
        """Wait for all hosts in an Ansible inventory file.

        Args:
            inventory_file: Path to Ansible inventory JSON file.

        Returns:
            Tuple of (successful_hosts, failed_hosts).

        Raises:
            FileNotFoundError: If inventory file doesn't exist.
            ValueError: If no hosts found in inventory.
        """
        if not inventory_file.exists():
            raise FileNotFoundError(f"Inventory file not found: {inventory_file}")

        with open(inventory_file) as f:
            inventory = json.load(f)

        hosts_data = inventory.get("all", {}).get("hosts", {})
        if not hosts_data:
            raise ValueError("No hosts found in inventory")

        hosts = []
        for name, info in hosts_data.items():
            host = info.get("ansible_host")
            if host and host not in ("null", "None", ""):
                hosts.append(host)

        if not hosts:
            raise ValueError("No valid host IPs found in inventory")

        return self.wait_for_hosts(hosts)

    def _try_connect(self, host: str) -> bool:
        """Attempt a single SSH connection.

        Args:
            host: IP address or hostname.

        Returns:
            True if connection succeeded.
        """
        result = subprocess.run(
            [
                "ssh",
                "-o",
                "BatchMode=yes",
                "-o",
                "ConnectTimeout=5",
                "-o",
                "StrictHostKeyChecking=no",
                "-o",
                "UserKnownHostsFile=/dev/null",
                f"{self.user}@{host}",
                "exit",
            ],
            capture_output=True,
        )
        return result.returncode == 0
