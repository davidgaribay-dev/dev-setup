#!/usr/bin/env python3
"""
deploy.py - Provision and configure Claude development VMs

Usage:
    ./deploy.py [OPTIONS]

Options:
    -c, --count NUM       Number of VMs to create (default: 1)
    -p, --prefix NAME     VM name prefix (default: claude-dev)
    -s, --start-id NUM    Starting VM ID (default: 200)
    --skip-provision      Skip OpenTofu provisioning (run Ansible only)
    --skip-configure      Skip Ansible configuration (provision only)
    --skip-hardening      Skip hardening roles (run setup only)
    --destroy             Destroy all VMs
    -h, --help            Show this help message

Examples:
    ./deploy.py -c 3                    # Create 3 VMs: claude-dev-1, claude-dev-2, claude-dev-3
    ./deploy.py -c 2 -p myvm            # Create 2 VMs: myvm-1, myvm-2
    ./deploy.py --skip-provision        # Only run Ansible on existing VMs
    ./deploy.py --destroy               # Destroy all managed VMs
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path


# ANSI color codes
class Colors:
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    NC = "\033[0m"  # No Color


class Logger:
    """Colored logging output matching the original bash script."""

    @staticmethod
    def info(msg: str) -> None:
        print(f"{Colors.BLUE}[INFO]{Colors.NC} {msg}")

    @staticmethod
    def success(msg: str) -> None:
        print(f"{Colors.GREEN}[SUCCESS]{Colors.NC} {msg}")

    @staticmethod
    def warn(msg: str) -> None:
        print(f"{Colors.YELLOW}[WARN]{Colors.NC} {msg}")

    @staticmethod
    def error(msg: str) -> None:
        print(f"{Colors.RED}[ERROR]{Colors.NC} {msg}", file=sys.stderr)


log = Logger()


def die(msg: str) -> None:
    """Log error and exit."""
    log.error(msg)
    sys.exit(1)


@dataclass
class Config:
    """Global configuration paths and settings."""

    script_dir: Path = field(default_factory=lambda: Path(__file__).parent.resolve())

    @property
    def provision_dir(self) -> Path:
        return self.script_dir / "provision"

    @property
    def config_dir(self) -> Path:
        return self.script_dir / "configuration"

    @property
    def inventory_file(self) -> Path:
        return self.config_dir / "inventory" / "hosts.json"

    # SSH settings
    ssh_user: str = "dmg"
    ssh_timeout: int = 300
    ssh_retry_interval: int = 10


def check_dependencies() -> None:
    """Verify required tools are installed."""
    deps = ["tofu", "ansible-playbook", "ansible-galaxy", "ssh"]
    missing = [dep for dep in deps if shutil.which(dep) is None]

    if missing:
        die(f"Missing dependencies: {', '.join(missing)}")


def generate_vms_var(count: int, prefix: str, start_id: int) -> dict:
    """Generate VM configuration dictionary for OpenTofu."""
    return {f"{prefix}-{i}": {"vm_id": start_id + i - 1} for i in range(1, count + 1)}


def run_command(
    cmd: list[str],
    cwd: Path | None = None,
    check: bool = True,
    capture_output: bool = False,
    env: dict | None = None,
) -> subprocess.CompletedProcess:
    """Run a command with proper error handling."""
    import os
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    try:
        return subprocess.run(
            cmd,
            cwd=cwd,
            check=check,
            capture_output=capture_output,
            text=True,
            env=run_env,
        )
    except subprocess.CalledProcessError as e:
        if capture_output:
            log.error(f"Command failed: {' '.join(cmd)}")
            if e.stdout:
                print(e.stdout)
            if e.stderr:
                print(e.stderr, file=sys.stderr)
        raise


class OpenTofu:
    """Manages OpenTofu/Terraform operations."""

    def __init__(self, config: Config, verbose: bool = False):
        self.config = config
        self.provision_dir = config.provision_dir
        self.verbose = verbose
        self.tf_env = {"TF_LOG": "INFO"} if verbose else {}

    def init(self) -> None:
        """Initialize OpenTofu."""
        log.info("Initializing OpenTofu...")
        run_command(["tofu", "init", "-upgrade"], cwd=self.provision_dir)

    def plan(self, vms_var: dict) -> None:
        """Create execution plan."""
        log.info("Planning infrastructure...")
        vms_json = json.dumps(vms_var)
        run_command(
            ["tofu", "plan", f"-var=vms={vms_json}", "-out=tfplan"],
            cwd=self.provision_dir,
        )

    def apply(self, vms_var: dict) -> None:
        """Apply the planned changes."""
        log.info("Applying infrastructure changes (parallelism=1 for Proxmox stability)...")
        log.info("This may take several minutes - cloning VM disks is slow...")
        for vm_name, vm_config in vms_var.items():
            log.info(f"  Will create: {vm_name} (VM ID: {vm_config['vm_id']})")
        vms_json = json.dumps(vms_var)
        run_command(
            ["tofu", "apply", "-parallelism=1", f"-var=vms={vms_json}", "tfplan"],
            cwd=self.provision_dir,
            env=self.tf_env,
        )
        log.success("Infrastructure apply completed")
        # Clean up plan file
        plan_file = self.provision_dir / "tfplan"
        if plan_file.exists():
            plan_file.unlink()

    def destroy(self, vms_var: dict) -> None:
        """Destroy all VMs."""
        log.warn("Destroying all VMs...")
        vms_json = json.dumps(vms_var)
        run_command(
            ["tofu", "destroy", f"-var=vms={vms_json}", "-auto-approve", "-parallelism=1"],
            cwd=self.provision_dir,
        )

    def refresh(self, vms_var: dict) -> None:
        """Refresh state to get updated IPs."""
        vms_json = json.dumps(vms_var)
        run_command(
            ["tofu", "refresh", f"-var=vms={vms_json}"],
            cwd=self.provision_dir,
        )

    def get_inventory(self) -> dict:
        """Get Ansible inventory from OpenTofu output."""
        result = run_command(
            ["tofu", "output", "-raw", "ansible_inventory"],
            cwd=self.provision_dir,
            capture_output=True,
        )
        return json.loads(result.stdout)

    def export_inventory(self) -> None:
        """Export inventory to JSON file for Ansible."""
        log.info("Exporting Ansible inventory...")

        # Ensure inventory directory exists
        self.config.inventory_file.parent.mkdir(parents=True, exist_ok=True)

        inventory = self.get_inventory()
        with open(self.config.inventory_file, "w") as f:
            json.dump(inventory, f, indent=2)

        log.success(f"Inventory written to {self.config.inventory_file}")


class SSHWaiter:
    """Handles SSH connectivity waiting."""

    def __init__(self, config: Config):
        self.config = config

    def wait_for_host(self, host: str) -> bool:
        """Wait for SSH to become available on a host."""
        log.info(f"Waiting for SSH on {host}...")
        elapsed = 0

        while elapsed < self.config.ssh_timeout:
            result = subprocess.run(
                [
                    "ssh",
                    "-o", "BatchMode=yes",
                    "-o", "ConnectTimeout=5",
                    "-o", "StrictHostKeyChecking=no",
                    "-o", "UserKnownHostsFile=/dev/null",
                    f"{self.config.ssh_user}@{host}",
                    "exit",
                ],
                capture_output=True,
            )

            if result.returncode == 0:
                log.success(f"SSH available on {host}")
                return True

            time.sleep(self.config.ssh_retry_interval)
            elapsed += self.config.ssh_retry_interval

        log.error(f"Timeout waiting for SSH on {host}")
        return False

    def wait_for_all(self) -> None:
        """Wait for all VMs in inventory to be accessible."""
        log.info("Waiting for all VMs to be accessible via SSH...")

        if not self.config.inventory_file.exists():
            die(f"Inventory file not found: {self.config.inventory_file}")

        with open(self.config.inventory_file) as f:
            inventory = json.load(f)

        hosts = inventory.get("all", {}).get("hosts", {})
        if not hosts:
            die("No hosts found in inventory or IPs not yet assigned")

        failed = 0
        for name, info in hosts.items():
            host = info.get("ansible_host")
            if host and host != "null":
                if not self.wait_for_host(host):
                    failed += 1

        if failed > 0:
            die(f"{failed} VM(s) failed to become accessible")

        log.success("All VMs are accessible")


class Ansible:
    """Manages Ansible operations."""

    def __init__(self, config: Config):
        self.config = config
        self.config_dir = config.config_dir

    def install_collections(self) -> None:
        """Install Ansible collections and roles."""
        log.info("Installing Ansible collections...")
        run_command(
            ["ansible-galaxy", "collection", "install", "-r", "requirements.yml", "--force"],
            cwd=self.config_dir,
        )
        log.info("Installing Ansible roles...")
        run_command(
            ["ansible-galaxy", "role", "install", "-r", "requirements.yml", "--force"],
            cwd=self.config_dir,
        )

    def run_playbook(self, skip_hardening: bool = False) -> None:
        """Run the Ansible playbook."""
        cmd = ["ansible-playbook", "playbook.yml", "-v"]

        if skip_hardening:
            log.warn("Skipping hardening roles")
            cmd.extend(["--skip-tags", "hardening"])

        log.info("Running Ansible playbook...")
        run_command(cmd, cwd=self.config_dir)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Provision and configure Claude development VMs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -c 3                    Create 3 VMs: claude-dev-1, claude-dev-2, claude-dev-3
  %(prog)s -c 2 -p myvm            Create 2 VMs: myvm-1, myvm-2
  %(prog)s --skip-provision        Only run Ansible on existing VMs
  %(prog)s --destroy               Destroy all managed VMs
""",
    )

    parser.add_argument(
        "-c", "--count",
        type=int,
        default=1,
        metavar="NUM",
        help="Number of VMs to create (default: 1)",
    )
    parser.add_argument(
        "-p", "--prefix",
        type=str,
        default="claude-dev",
        metavar="NAME",
        help="VM name prefix (default: claude-dev)",
    )
    parser.add_argument(
        "-s", "--start-id",
        type=int,
        default=200,
        metavar="NUM",
        help="Starting VM ID (default: 200)",
    )
    parser.add_argument(
        "--skip-provision",
        action="store_true",
        help="Skip OpenTofu provisioning (run Ansible only)",
    )
    parser.add_argument(
        "--skip-configure",
        action="store_true",
        help="Skip Ansible configuration (provision only)",
    )
    parser.add_argument(
        "--skip-hardening",
        action="store_true",
        help="Skip hardening roles (run setup only)",
    )
    parser.add_argument(
        "--destroy",
        action="store_true",
        help="Destroy all VMs",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose OpenTofu logging (TF_LOG=INFO)",
    )

    args = parser.parse_args()

    # Validate
    if args.count < 1:
        parser.error("VM count must be a positive integer")

    return args


def show_vm_ips(config: Config) -> None:
    """Display VM IP addresses from inventory."""
    if not config.inventory_file.exists():
        return

    with open(config.inventory_file) as f:
        inventory = json.load(f)

    hosts = inventory.get("all", {}).get("hosts", {})
    if hosts:
        log.info("VM IP Addresses:")
        for name, info in hosts.items():
            ip = info.get("ansible_host", "N/A")
            print(f"  {name}: {ip}")


def main() -> None:
    args = parse_args()
    check_dependencies()

    config = Config()
    tofu = OpenTofu(config, verbose=args.verbose)
    ansible = Ansible(config)
    ssh_waiter = SSHWaiter(config)

    vms_var = generate_vms_var(args.count, args.prefix, args.start_id)

    log.info("Configuration:")
    log.info(f"  VM Count: {args.count}")
    log.info(f"  VM Prefix: {args.prefix}")
    log.info(f"  Start ID: {args.start_id}")
    log.info(f"  VMs: {json.dumps(vms_var)}")

    # Handle destroy
    if args.destroy:
        tofu.init()
        tofu.destroy(vms_var)
        log.success("All VMs destroyed")
        return

    # Phase 1: Provision
    if not args.skip_provision:
        log.info("=== Phase 1: Provisioning ===")
        tofu.init()
        tofu.plan(vms_var)
        tofu.apply(vms_var)
        tofu.export_inventory()
    else:
        log.warn("Skipping provisioning phase")
        if not config.inventory_file.exists():
            # Try to export from existing state
            log.info("Attempting to export inventory from existing state...")
            try:
                tofu.export_inventory()
            except subprocess.CalledProcessError:
                die("No inventory file and cannot export from state")

    # Phase 2: Wait for VMs
    if not args.skip_configure:
        log.info("=== Phase 2: Waiting for VMs ===")
        # Give VMs a moment to boot and get IPs
        log.info("Waiting 30 seconds for VMs to boot and acquire IPs...")
        time.sleep(30)

        # Re-export inventory to get IPs (they may not be available immediately after apply)
        if not args.skip_provision:
            log.info("Re-exporting inventory to capture assigned IPs...")
            tofu.refresh(vms_var)
            tofu.export_inventory()

        ssh_waiter.wait_for_all()

    # Phase 3: Configure
    if not args.skip_configure:
        log.info("=== Phase 3: Configuration ===")
        ansible.install_collections()
        ansible.run_playbook(skip_hardening=args.skip_hardening)
    else:
        log.warn("Skipping configuration phase")

    log.success("=== Deployment Complete ===")
    show_vm_ips(config)


if __name__ == "__main__":
    main()
