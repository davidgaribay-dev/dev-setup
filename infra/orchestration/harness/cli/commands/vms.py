"""Claude VMs deployment command."""

from __future__ import annotations

from typing import Annotated, Optional

import typer

from harness.core.context import AppContext
from harness.core.exitcodes import ExitCode
from harness.core.runner import MissingDependencyError
from harness.deployers import ClaudeVMsDeployer


def vms(
    ctx: typer.Context,
    count: Annotated[
        Optional[int],
        typer.Option(
            "--count",
            "-c",
            help="Number of VMs to create.",
        ),
    ] = None,
    prefix: Annotated[
        Optional[str],
        typer.Option(
            "--prefix",
            "-p",
            help="VM name prefix.",
        ),
    ] = None,
    start_id: Annotated[
        Optional[int],
        typer.Option(
            "--start-id",
            "-s",
            help="Starting VM ID.",
        ),
    ] = None,
    neo4j_ip: Annotated[
        Optional[str],
        typer.Option(
            "--neo4j-ip",
            help="Override Neo4j server IP address.",
        ),
    ] = None,
    destroy: Annotated[
        bool,
        typer.Option(
            "--destroy",
            "-d",
            help="Destroy VMs instead of deploying.",
        ),
    ] = False,
    skip_provision: Annotated[
        bool,
        typer.Option(
            "--skip-provision",
            help="Skip OpenTofu provisioning.",
        ),
    ] = False,
    skip_configure: Annotated[
        bool,
        typer.Option(
            "--skip-configure",
            help="Skip Ansible configuration.",
        ),
    ] = False,
    skip_hardening: Annotated[
        bool,
        typer.Option(
            "--skip-hardening",
            help="Skip OS hardening roles.",
        ),
    ] = False,
    plan_only: Annotated[
        bool,
        typer.Option(
            "--plan-only",
            help="Show Terraform plan without applying changes.",
        ),
    ] = False,
) -> None:
    """Deploy or destroy Claude development VMs.

    Claude VMs are ephemeral development environments configured with
    Claude Code CLI and connected to the Neo4j database server via MCP.

    \b
    Environment Variables:
        NEO4J_PASSWORD    Password for Neo4j MCP connection
        NEO4J_IP          Override Neo4j IP (alternative to --neo4j-ip)
        ANSIBLE_GH_TOKEN  GitHub token for gh CLI authentication

    \b
    Examples:
        # Create 3 VMs with default settings
        $ harness vms -c 3

        # Create 2 VMs with custom prefix
        $ harness vms -c 2 -p myproject

        # Only run Ansible on existing VMs
        $ harness vms --skip-provision

        # Destroy all managed VMs
        $ harness vms --destroy

        # Deploy without OS hardening (faster, less secure)
        $ harness vms --skip-hardening
    """
    app_ctx: AppContext = ctx.obj
    log = app_ctx.logger

    try:
        deployer = ClaudeVMsDeployer(
            app_ctx.config,
            verbose=app_ctx.verbose,
            count=count,
            prefix=prefix,
            start_id=start_id,
            neo4j_ip=neo4j_ip,
        )

        if destroy:
            result = deployer.destroy()
        elif plan_only:
            result = deployer.plan()
        else:
            result = deployer.deploy(
                skip_provision=skip_provision,
                skip_configure=skip_configure,
                skip_hardening=skip_hardening,
            )

        action = "destroy" if destroy else ("plan" if plan_only else "deploy")
        if app_ctx.json_output:
            log.set_result({
                "success": result.success,
                "message": result.message,
                "component": "claude-vms",
                "action": action,
                "count": count or app_ctx.config.claude_vms.default_count,
            })
            log.flush_json()

        if not result.success:
            log.error(result.message)
            raise typer.Exit(code=ExitCode.FAILURE)

    except MissingDependencyError as e:
        log.error(f"Missing dependencies: {', '.join(e.dependencies)}")
        raise typer.Exit(code=ExitCode.CONFIG)
