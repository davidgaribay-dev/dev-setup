"""Base deployer class with common functionality."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from harness.core.logger import log
from harness.core.runner import CommandError, check_dependencies
from harness.infra import AnsibleManager, OpenTofuManager, SSHWaiter

if TYPE_CHECKING:
    from harness.core.config import Config


@dataclass
class DeploymentResult:
    """Result of a deployment operation."""

    success: bool
    message: str
    details: dict | None = None


class BaseDeployer(ABC):
    """Base class for component deployers."""

    # Dependencies required for this deployer
    REQUIRED_DEPENDENCIES: list[str] = ["tofu", "ansible-playbook", "ansible-galaxy", "ssh"]

    def __init__(self, config: Config, verbose: bool = False):
        """Initialize the deployer.

        Args:
            config: Application configuration.
            verbose: Enable verbose output.
        """
        self.config = config
        self.verbose = verbose
        self._validate_dependencies()

    def _validate_dependencies(self) -> None:
        """Check that required dependencies are installed."""
        check_dependencies(self.REQUIRED_DEPENDENCIES)

    @property
    @abstractmethod
    def component_name(self) -> str:
        """Name of the component being deployed."""

    @property
    @abstractmethod
    def provision_dir(self):
        """Directory containing Terraform/OpenTofu files."""

    @property
    @abstractmethod
    def config_dir(self):
        """Directory containing Ansible configuration."""

    @property
    @abstractmethod
    def inventory_file(self):
        """Path to the Ansible inventory file."""

    def get_tofu_manager(self) -> OpenTofuManager:
        """Get an OpenTofu manager instance."""
        return OpenTofuManager(
            provision_dir=self.provision_dir,
            inventory_file=self.inventory_file,
            verbose=self.verbose,
        )

    def get_ansible_manager(self) -> AnsibleManager:
        """Get an Ansible manager instance."""
        return AnsibleManager(config_dir=self.config_dir)

    def get_ssh_waiter(self) -> SSHWaiter:
        """Get an SSH waiter instance."""
        return SSHWaiter(
            user=self.config.ssh.user,
            timeout=self.config.ssh.timeout,
            retry_interval=self.config.ssh.retry_interval,
        )

    def deploy(
        self,
        skip_provision: bool = False,
        skip_configure: bool = False,
        **kwargs,
    ) -> DeploymentResult:
        """Run the full deployment.

        Args:
            skip_provision: Skip OpenTofu provisioning.
            skip_configure: Skip Ansible configuration.
            **kwargs: Additional arguments for subclass implementations.

        Returns:
            DeploymentResult indicating success/failure.
        """
        log.header(f"Deploying {self.component_name}")
        self._log_configuration(**kwargs)

        try:
            # Phase 1: Provision
            if not skip_provision:
                log.header("Phase 1: Provisioning")
                self._provision(**kwargs)
            else:
                log.warn("Skipping provisioning phase")
                self._ensure_inventory(**kwargs)

            # Phase 2: Wait for VMs
            if not skip_configure:
                log.header("Phase 2: Waiting for VMs")
                self._wait_for_vms(**kwargs)

            # Phase 3: Configure
            if not skip_configure:
                log.header("Phase 3: Configuration")
                self._configure(**kwargs)
            else:
                log.warn("Skipping configuration phase")

            log.header("Deployment Complete")
            self._log_summary(**kwargs)

            return DeploymentResult(
                success=True,
                message=f"{self.component_name} deployed successfully",
            )

        except CommandError as e:
            log.error(f"Deployment failed: {e}")
            return DeploymentResult(
                success=False,
                message=str(e),
            )
        except Exception as e:
            log.error(f"Unexpected error: {e}")
            return DeploymentResult(
                success=False,
                message=str(e),
            )

    def plan(self, **kwargs) -> DeploymentResult:
        """Show the deployment plan without applying changes.

        Args:
            **kwargs: Additional arguments for subclass implementations.

        Returns:
            DeploymentResult indicating success/failure.
        """
        log.header(f"Planning {self.component_name}")
        self._log_configuration(**kwargs)

        try:
            self._plan(**kwargs)

            return DeploymentResult(
                success=True,
                message=f"{self.component_name} plan completed",
            )

        except CommandError as e:
            log.error(f"Plan failed: {e}")
            return DeploymentResult(
                success=False,
                message=str(e),
            )

    def destroy(self, **kwargs) -> DeploymentResult:
        """Destroy the deployed infrastructure.

        Args:
            **kwargs: Additional arguments for subclass implementations.

        Returns:
            DeploymentResult indicating success/failure.
        """
        log.header(f"Destroying {self.component_name}")

        try:
            tofu = self.get_tofu_manager()
            tofu.init()
            self._destroy(tofu, **kwargs)

            return DeploymentResult(
                success=True,
                message=f"{self.component_name} destroyed successfully",
            )

        except CommandError as e:
            log.error(f"Destroy failed: {e}")
            return DeploymentResult(
                success=False,
                message=str(e),
            )

    @abstractmethod
    def _provision(self, **kwargs) -> None:
        """Run the provisioning phase."""

    @abstractmethod
    def _configure(self, **kwargs) -> None:
        """Run the configuration phase."""

    @abstractmethod
    def _destroy(self, tofu: OpenTofuManager, **kwargs) -> None:
        """Run the destroy operation."""

    def _plan(self, **kwargs) -> None:
        """Run the plan operation. Override in subclasses if needed."""
        tofu = self.get_tofu_manager()
        tofu.init()
        # Subclasses should override to pass their variables
        tofu.plan()

    def _ensure_inventory(self, **kwargs) -> None:
        """Ensure inventory exists when skipping provision."""
        if not self.inventory_file.exists():
            log.info("Attempting to export inventory from existing state...")
            tofu = self.get_tofu_manager()
            tofu.export_inventory()

    def _wait_for_vms(self, boot_delay: int = 30, **kwargs) -> None:
        """Wait for VMs to become accessible.

        Args:
            boot_delay: Seconds to wait for VMs to boot.
            **kwargs: Additional arguments (unused).
        """
        log.info(f"Waiting {boot_delay} seconds for VM(s) to boot...")
        time.sleep(boot_delay)

        ssh_waiter = self.get_ssh_waiter()
        successful, failed = ssh_waiter.wait_for_inventory(self.inventory_file)

        if failed:
            raise RuntimeError(f"{len(failed)} VM(s) failed to become accessible: {failed}")

        log.success(f"All {len(successful)} VM(s) are accessible")

    def _log_configuration(self, **kwargs) -> None:
        """Log the deployment configuration. Override in subclasses."""
        pass

    def _log_summary(self, **kwargs) -> None:
        """Log the deployment summary. Override in subclasses."""
        pass
