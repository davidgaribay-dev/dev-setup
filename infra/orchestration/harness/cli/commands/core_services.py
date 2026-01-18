"""Core Services deployment command."""

from __future__ import annotations

from typing import Annotated

import typer

from harness.core.context import AppContext
from harness.core.exitcodes import ExitCode
from harness.core.runner import MissingDependencyError
from harness.deployers import CoreServicesDeployer


def core_services(
    ctx: typer.Context,
    destroy: Annotated[
        bool,
        typer.Option(
            "--destroy",
            "-d",
            help="Destroy the Core Services VM instead of deploying.",
        ),
    ] = False,
    skip_provision: Annotated[
        bool,
        typer.Option(
            "--skip-provision",
            help="Skip OpenTofu provisioning (run Ansible only).",
        ),
    ] = False,
    skip_configure: Annotated[
        bool,
        typer.Option(
            "--skip-configure",
            help="Skip Ansible configuration (provision only).",
        ),
    ] = False,
) -> None:
    """Deploy or destroy Core Services (Plane + Rewind).

    Core Services includes:
    - Plane: Self-hosted project management platform
    - Rewind: Conversation history viewer for Claude Code

    After deployment, you'll need to complete initial setup for Plane
    and generate an API key for MCP integration with Claude VMs.

    \b
    Environment Variables:
        PLANE_SECRET_KEY          Secret key (generate with: openssl rand -hex 32)
        PLANE_LIVE_SECRET_KEY     Live server key (generate with: openssl rand -hex 16)
        PLANE_POSTGRES_PASSWORD   PostgreSQL password
        PLANE_RABBITMQ_PASSWORD   RabbitMQ password
        NEO4J_IP                  Neo4j server IP (default: 10.0.70.60)
        NEO4J_PASSWORD            Neo4j password for Rewind

    \b
    Examples:
        # Deploy Core Services with default settings
        $ harness core-services

        # Destroy the Core Services VM
        $ harness core-services --destroy

        # Only run Ansible configuration (skip provisioning)
        $ harness core-services --skip-provision

        # Only provision infrastructure (skip Ansible)
        $ harness core-services --skip-configure
    """
    app_ctx: AppContext = ctx.obj
    log = app_ctx.logger

    try:
        deployer = CoreServicesDeployer(app_ctx.config, verbose=app_ctx.verbose)

        if destroy:
            result = deployer.destroy()
        else:
            result = deployer.deploy(
                skip_provision=skip_provision,
                skip_configure=skip_configure,
            )

        if app_ctx.json_output:
            log.set_result({
                "success": result.success,
                "message": result.message,
                "component": "core-services",
                "action": "destroy" if destroy else "deploy",
            })
            log.flush_json()

        if not result.success:
            log.error(result.message)
            raise typer.Exit(code=ExitCode.FAILURE)

    except MissingDependencyError as e:
        log.error(f"Missing dependencies: {', '.join(e.dependencies)}")
        raise typer.Exit(code=ExitCode.CONFIG)
