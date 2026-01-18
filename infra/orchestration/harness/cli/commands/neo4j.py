"""Neo4j deployment command."""

from __future__ import annotations

from typing import Annotated

import typer

from harness.core.context import AppContext
from harness.core.exitcodes import ExitCode
from harness.core.runner import MissingDependencyError
from harness.deployers import Neo4jDeployer


def neo4j(
    ctx: typer.Context,
    destroy: Annotated[
        bool,
        typer.Option(
            "--destroy",
            "-d",
            help="Destroy the Neo4j VM instead of deploying.",
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
    """Deploy or destroy the Neo4j database server.

    The Neo4j server is persistent infrastructure that remains running
    while Claude VMs can be created and destroyed freely.

    \b
    Environment Variables:
        NEO4J_ADMIN_PASSWORD  Initial admin password for Neo4j

    \b
    Examples:
        # Deploy Neo4j with default settings
        $ harness neo4j

        # Destroy the Neo4j VM
        $ harness neo4j --destroy

        # Only run Ansible configuration (skip provisioning)
        $ harness neo4j --skip-provision

        # Only provision infrastructure (skip Ansible)
        $ harness neo4j --skip-configure
    """
    app_ctx: AppContext = ctx.obj
    log = app_ctx.logger

    try:
        deployer = Neo4jDeployer(app_ctx.config, verbose=app_ctx.verbose)

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
                "component": "neo4j",
                "action": "destroy" if destroy else "deploy",
            })
            log.flush_json()

        if not result.success:
            log.error(result.message)
            raise typer.Exit(code=ExitCode.FAILURE)

    except MissingDependencyError as e:
        log.error(f"Missing dependencies: {', '.join(e.dependencies)}")
        raise typer.Exit(code=ExitCode.CONFIG)
