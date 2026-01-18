"""Combined deployment command for all infrastructure."""

from __future__ import annotations

from typing import Annotated, Optional

import typer

from harness.core.context import AppContext
from harness.core.exitcodes import ExitCode
from harness.core.runner import MissingDependencyError
from harness.deployers import ClaudeVMsDeployer, CoreServicesDeployer, Neo4jDeployer


def all_cmd(
    ctx: typer.Context,
    count: Annotated[
        Optional[int],
        typer.Option(
            "--count",
            "-c",
            help="Number of Claude VMs to create.",
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
    destroy: Annotated[
        bool,
        typer.Option(
            "--destroy",
            "-d",
            help="Destroy everything instead of deploying.",
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
            help="Skip OS hardening roles (Claude VMs only).",
        ),
    ] = False,
) -> None:
    """Deploy or destroy the complete infrastructure.

    This command manages Neo4j, Core Services (Plane + Rewind), and Claude VMs together.

    \b
    Deploy order:  Neo4j → Core Services → Claude VMs
    Destroy order: Claude VMs → Core Services → Neo4j

    \b
    Environment Variables:
        NEO4J_ADMIN_PASSWORD  Initial admin password for Neo4j
        NEO4J_PASSWORD        Password for Neo4j MCP connection
        PLANE_*               Core Services (Plane) secrets
        ANSIBLE_GH_TOKEN      GitHub token for gh CLI authentication

    \b
    Examples:
        # Deploy everything with 1 Claude VM
        $ harness all

        # Deploy Neo4j + Core Services + 3 Claude VMs
        $ harness all -c 3

        # Destroy all infrastructure
        $ harness all --destroy

        # Deploy without OS hardening
        $ harness all --skip-hardening
    """
    app_ctx: AppContext = ctx.obj
    log = app_ctx.logger
    config = app_ctx.config

    try:
        if destroy:
            _destroy_all(app_ctx, count, prefix, start_id)
        else:
            _deploy_all(
                app_ctx,
                count,
                prefix,
                start_id,
                skip_provision,
                skip_configure,
                skip_hardening,
            )

        if app_ctx.json_output:
            log.set_result({
                "success": True,
                "action": "destroy" if destroy else "deploy",
                "components": ["neo4j", "core-services", "claude-vms"],
            })
            log.flush_json()

    except MissingDependencyError as e:
        log.error(f"Missing dependencies: {', '.join(e.dependencies)}")
        raise typer.Exit(code=ExitCode.CONFIG)


def _destroy_all(
    app_ctx: AppContext,
    count: int | None,
    prefix: str | None,
    start_id: int | None,
) -> None:
    """Destroy all infrastructure (Claude VMs → Core Services → Neo4j)."""
    log = app_ctx.logger
    config = app_ctx.config

    # Destroy Claude VMs first
    log.header("Destroying Claude VMs")
    vms_deployer = ClaudeVMsDeployer(
        config,
        verbose=app_ctx.verbose,
        count=count,
        prefix=prefix,
        start_id=start_id,
    )
    vms_result = vms_deployer.destroy()
    if not vms_result.success:
        log.warn(f"Claude VMs destruction may have failed: {vms_result.message}")

    # Then destroy Core Services
    log.header("Destroying Core Services")
    core_services_deployer = CoreServicesDeployer(config, verbose=app_ctx.verbose)
    core_services_result = core_services_deployer.destroy()
    if not core_services_result.success:
        log.warn(f"Core Services destruction may have failed: {core_services_result.message}")

    # Finally destroy Neo4j
    log.header("Destroying Neo4j")
    neo4j_deployer = Neo4jDeployer(config, verbose=app_ctx.verbose)
    neo4j_result = neo4j_deployer.destroy()
    if not neo4j_result.success:
        log.warn(f"Neo4j destruction may have failed: {neo4j_result.message}")

    log.success("All components destroyed")


def _deploy_all(
    app_ctx: AppContext,
    count: int | None,
    prefix: str | None,
    start_id: int | None,
    skip_provision: bool,
    skip_configure: bool,
    skip_hardening: bool,
) -> None:
    """Deploy all infrastructure (Neo4j → Core Services → Claude VMs)."""
    log = app_ctx.logger
    config = app_ctx.config

    # Deploy Neo4j first
    neo4j_deployer = Neo4jDeployer(config, verbose=app_ctx.verbose)
    neo4j_result = neo4j_deployer.deploy(
        skip_provision=skip_provision,
        skip_configure=skip_configure,
    )
    if not neo4j_result.success:
        log.error(f"Neo4j deployment failed: {neo4j_result.message}")
        raise typer.Exit(code=ExitCode.FAILURE)

    # Then deploy Core Services (Plane + Rewind)
    core_services_deployer = CoreServicesDeployer(config, verbose=app_ctx.verbose)
    core_services_result = core_services_deployer.deploy(
        skip_provision=skip_provision,
        skip_configure=skip_configure,
    )
    if not core_services_result.success:
        log.error(f"Core Services deployment failed: {core_services_result.message}")
        raise typer.Exit(code=ExitCode.FAILURE)

    # Finally deploy Claude VMs
    vms_deployer = ClaudeVMsDeployer(
        config,
        verbose=app_ctx.verbose,
        count=count,
        prefix=prefix,
        start_id=start_id,
    )
    vms_result = vms_deployer.deploy(
        skip_provision=skip_provision,
        skip_configure=skip_configure,
        skip_hardening=skip_hardening,
    )
    if not vms_result.success:
        log.error(f"Claude VMs deployment failed: {vms_result.message}")
        raise typer.Exit(code=ExitCode.FAILURE)

    # Summary
    log.header("Deployment Summary")
    log.info(f"Neo4j: {config.neo4j.bolt_uri}")
    log.info(f"Neo4j Browser: {config.neo4j.http_uri}")
    log.info(f"Core Services (Plane): {config.core_services.https_uri}")
    log.info(f"Rewind API: {config.core_services.rewind_api_uri}")
    log.info(f"Rewind UI: {config.core_services.rewind_web_uri}")
    log.success("All components deployed successfully")
