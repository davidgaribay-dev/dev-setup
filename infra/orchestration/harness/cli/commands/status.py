"""Infrastructure status command."""

from __future__ import annotations

import json
from typing import Any

import typer

from harness.core.context import AppContext
from harness.core.logger import print_json


def status(ctx: typer.Context) -> None:
    """Show the current infrastructure status.

    Displays information about deployed Neo4j and Claude VMs
    based on the current Terraform state and inventory files.

    \b
    Examples:
        # Show status in human-readable format
        $ harness status

        # Show status as JSON (for scripting)
        $ harness --json status
    """
    app_ctx: AppContext = ctx.obj
    log = app_ctx.logger
    config = app_ctx.config

    status_data: dict[str, Any] = {
        "neo4j": {"deployed": False, "hosts": {}},
        "claude_vms": {"deployed": False, "hosts": {}},
    }

    if not app_ctx.json_output:
        log.header("Infrastructure Status")

    # Check Neo4j
    neo4j_inventory = config.get_inventory_file("neo4j")
    if not app_ctx.json_output:
        log.info("Neo4j:")

    if neo4j_inventory.exists():
        with open(neo4j_inventory) as f:
            inventory = json.load(f)
        hosts = inventory.get("all", {}).get("hosts", {})
        if hosts:
            status_data["neo4j"]["deployed"] = True
            for name, info in hosts.items():
                ip = info.get("ansible_host", "N/A")
                status_data["neo4j"]["hosts"][name] = ip
                if not app_ctx.json_output:
                    log.bullet(f"{name}: {ip}")
        else:
            if not app_ctx.json_output:
                log.bullet("No hosts in inventory")
    else:
        if not app_ctx.json_output:
            log.bullet("Not deployed (no inventory file)")

    # Check Claude VMs
    vms_inventory = config.get_inventory_file("claude-vms")
    if not app_ctx.json_output:
        log.info("Claude VMs:")

    if vms_inventory.exists():
        with open(vms_inventory) as f:
            inventory = json.load(f)
        hosts = inventory.get("all", {}).get("hosts", {})
        if hosts:
            status_data["claude_vms"]["deployed"] = True
            for name, info in hosts.items():
                ip = info.get("ansible_host", "N/A")
                status_data["claude_vms"]["hosts"][name] = ip
                if not app_ctx.json_output:
                    log.bullet(f"{name}: {ip}")
        else:
            if not app_ctx.json_output:
                log.bullet("No hosts in inventory")
    else:
        if not app_ctx.json_output:
            log.bullet("Not deployed (no inventory file)")

    # Output JSON if requested
    if app_ctx.json_output:
        print_json(status_data)
