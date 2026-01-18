"""Main CLI application using Typer."""

from __future__ import annotations

from typing import Annotated, Optional

import typer

from harness import __version__
from harness.cli.commands import all_cmd, neo4j, plane, status, vms
from harness.core.context import AppContext
from harness.core.exitcodes import ExitCode

# Create main app with common settings
app = typer.Typer(
    name="harness",
    help="Claude Code Harness - Infrastructure orchestration for Claude development environments.",
    no_args_is_help=True,
    rich_markup_mode="rich",
    context_settings={"help_option_names": ["-h", "--help"]},
)


def version_callback(value: bool) -> None:
    """Display version and exit."""
    if value:
        typer.echo(f"harness {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    ctx: typer.Context,
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version",
            "-V",
            help="Show version and exit.",
            callback=version_callback,
            is_eager=True,
        ),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Enable verbose output (debug logging, TF_LOG=INFO).",
        ),
    ] = False,
    json_output: Annotated[
        bool,
        typer.Option(
            "--json",
            "-j",
            help="Output results as JSON (for scripting).",
        ),
    ] = False,
) -> None:
    """Claude Code Harness - Infrastructure orchestration CLI.

    Manages Neo4j database servers and Claude development VMs
    on Proxmox using OpenTofu and Ansible.

    \b
    Quick Start:
        $ harness all -c 2       # Deploy Neo4j + 2 Claude VMs
        $ harness status         # Check what's deployed
        $ harness vms --destroy  # Tear down Claude VMs only

    \b
    For more information on a command:
        $ harness <command> --help
    """
    # Create and store application context
    try:
        ctx.ensure_object(dict)
        ctx.obj = AppContext.create(
            verbose=verbose,
            json_output=json_output,
        )
    except FileNotFoundError as e:
        typer.secho(f"Configuration error: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=ExitCode.CONFIG)


# Register commands directly (preserves docstrings for help text)
app.command("neo4j")(neo4j)
app.command("plane")(plane)
app.command("vms")(vms)
app.command("all")(all_cmd)
app.command("status")(status)


if __name__ == "__main__":
    app()
