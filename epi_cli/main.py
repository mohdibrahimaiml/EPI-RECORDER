"""
EPI CLI Main - Entry point for the EPI command-line interface.

Provides the main CLI application with frictionless first-run experience.
"""

import typer
from rich.console import Console

from epi_cli.keys import generate_default_keypair_if_missing

# Create Typer app
app = typer.Typer(
    name="epi",
    help="""EPI - Evidence Packaged Infrastructure for AI workflows

Commands:
  run    <script.py>        Record, auto-verify and open viewer. (Zero-config)
  record --out <file.epi> -- <cmd...>
                           Advanced: record any command, exact output file.
  verify <file.epi>         Verify a recording's integrity.
  view   <file.epi|name>    Open recording in browser (name resolves ./epi-recordings/).
  ls                        List local recordings (./epi-recordings/).
  keys                      Manage keys (list/generate/export) - advanced.
  help                      Show this quickstart.

Quickstart (first 30s):
  1) Install: pip install epi-recorder
  2) Record (simplest): epi run my_script.py
     -> Saved: ./epi-recordings/my_script_20251121_231501.epi
     -> Verified: OK
     -> Viewer: opened in browser
  3) See recordings: epi ls
  4) Open a recording: epi view my_script_20251121_231501

Tips:
  - Want explicit name? Use the advanced command: epi record --out experiment.epi -- python my_script.py
  - For scripts using the API, use @record decorator or with record(): no filenames needed.
""",
    add_completion=False,
    no_args_is_help=True,
    rich_markup_mode="rich"
)

console = Console()


@app.callback()
def main_callback():
    """
    Main callback - runs before any command.
    
    Implements frictionless first run by auto-generating default key pair.
    """
    # Auto-generate default keypair if missing (frictionless first run)
    generate_default_keypair_if_missing(console_output=True)


@app.command()
def version():
    """Show EPI version information."""
    from epi_core import __version__
    console.print(f"[bold]EPI[/bold] version [cyan]{__version__}[/cyan]")
    console.print("[dim]The PDF for AI workflows[/dim]")


@app.command(name="help")
def show_help():
    """Show extended quickstart help."""
    help_text = """[bold cyan]EPI Recorder - Quickstart Guide[/bold cyan]

[bold]Usage:[/bold] epi <command> [options]

[bold]Commands:[/bold]
  [cyan]run[/cyan]    <script.py>        Record, auto-verify and open viewer. (Zero-config)
  [cyan]record[/cyan] --out <file.epi> -- <cmd...>
                           Advanced: record any command, exact output file.
  [cyan]verify[/cyan] <file.epi>         Verify a recording's integrity.
  [cyan]view[/cyan]   <file.epi|name>    Open recording in browser (name resolves ./epi-recordings/).
  [cyan]ls[/cyan]                        List local recordings (./epi-recordings/).
  [cyan]keys[/cyan]                      Manage keys (list/generate/export) - advanced.
  [cyan]help[/cyan]                      Show this quickstart.

[bold]Quickstart (first 30s):[/bold]
  1) Install: pip install epi-recorder
  2) Record (simplest): [green]epi run my_script.py[/green]
     -> Saved: ./epi-recordings/my_script_20251121_231501.epi
     -> Verified: OK
     -> Viewer: opened in browser
  3) See recordings: [green]epi ls[/green]
  4) Open a recording: [green]epi view my_script_20251121_231501[/green]

[bold]Tips:[/bold]
  - Want explicit name? Use the advanced command: epi record --out experiment.epi -- python my_script.py
  - For scripts using the API, use @record decorator or with record(): no filenames needed.
"""
    console.print(help_text)


# Import and register subcommands
# These will be added as they're implemented

# NEW: run command (zero-config) - direct import
from epi_cli.run import run as run_command
app.command(name="run", help="Record, auto-verify and open viewer. (Zero-config)")(run_command)

# Phase 1: verify command
from epi_cli.verify import verify_app
app.add_typer(verify_app, name="verify", help="Verify .epi file integrity and authenticity")

# Phase 2: record command (legacy/advanced)
from epi_cli.record import app as record_app
app.add_typer(record_app, name="record", help="Advanced: record any command, exact output file.")

# Phase 3: view command
from epi_cli.view import app as view_app
app.add_typer(view_app, name="view", help="Open recording in browser (name resolves ./epi-recordings/)")

# NEW: ls command
from epi_cli.ls import ls as ls_command
app.command(name="ls", help="List local recordings (./epi-recordings/)")(ls_command)

# Phase 1: keys command (for manual key management)
@app.command()
def keys(
    action: str = typer.Argument(..., help="Action: generate, list, or export"),
    name: str = typer.Option("default", "--name", "-n", help="Key pair name"),
    overwrite: bool = typer.Option(False, "--overwrite", help="Overwrite existing keys")
):
    """Manage Ed25519 key pairs for signing."""
    from epi_cli.keys import KeyManager, print_keys_table
    
    key_manager = KeyManager()
    
    if action == "generate":
        try:
            private_path, public_path = key_manager.generate_keypair(name, overwrite=overwrite)
            console.print(f"\n[bold green][OK] Generated key pair:[/bold green] {name}")
            console.print(f"  [cyan]Private:[/cyan] {private_path}")
            console.print(f"  [cyan]Public:[/cyan]  {public_path}\n")
        except FileExistsError as e:
            console.print(f"[red][FAIL] Error:[/red] {e}")
            raise typer.Exit(1)
    
    elif action == "list":
        keys_list = key_manager.list_keys()
        print_keys_table(keys_list)
    
    elif action == "export":
        try:
            public_key_b64 = key_manager.export_public_key(name)
            console.print(f"\n[bold]Public key for '{name}':[/bold]")
            console.print(f"[cyan]{public_key_b64}[/cyan]\n")
        except FileNotFoundError as e:
            console.print(f"[red][FAIL] Error:[/red] {e}")
            raise typer.Exit(1)
    
    else:
        console.print(f"[red][FAIL] Unknown action:[/red] {action}")
        console.print("[dim]Valid actions: generate, list, export[/dim]")
        raise typer.Exit(1)


# Entry point for CLI
def cli_main():
    """CLI entry point (called by `epi` command)."""
    app()


if __name__ == "__main__":
    cli_main()
