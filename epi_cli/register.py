"""
epi-register - Standalone CLI entry point for registering .epi artifacts
on the SCITT transparency ledger and embedding cryptographic receipts.

Usage:
    epi-register file.epi
    epi-register file.epi --local
    epi-register file.epi --service URL

This is a first-class citizen in the EPI toolchain, equivalent to:
    epi scitt register file.epi
"""

from __future__ import annotations

import typer

from epi_cli.scitt import scitt_register

app = typer.Typer(
    name="epi-register",
    help=(
        "Register an .epi artifact on the SCITT transparency ledger "
        "and embed a cryptographic receipt."
    ),
    add_completion=False,
    no_args_is_help=True,
    invoke_without_command=True,
)

app.command(
    name=None,
    help="Register an .epi artifact on the transparency ledger and embed receipt.",
)(scitt_register)


def cli_main() -> None:
    """Entry point for the epi-register standalone CLI."""
    app()


if __name__ == "__main__":
    cli_main()
