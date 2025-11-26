"""
EPI CLI Run - Zero-config recording command.

Usage:
  epi run script.py

This command:
- Auto-generates output filename in ./epi-recordings/
- Records the script execution
- Verifies the recording
- Opens the viewer automatically
"""

import os
import shlex
import sys
import tempfile
import time
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.panel import Panel

from epi_core.container import EPIContainer
from epi_core.schemas import ManifestModel
from epi_core.trust import verify_signature, get_signer_name, create_verification_report
from epi_cli.keys import KeyManager
from epi_recorder.environment import save_environment_snapshot

console = Console()

app = typer.Typer(name="run", help="Zero-config recording: epi run my_script.py")

DEFAULT_DIR = Path("epi-recordings")


def _gen_auto_name(script_path: Path) -> Path:
    """
    Generate automatic output filename in ./epi-recordings/ directory.
    
    Args:
        script_path: Path to the script being recorded
        
    Returns:
        Path to the .epi file
    """
    base = script_path.stem if script_path.name != "-" else "recording"
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    DEFAULT_DIR.mkdir(parents=True, exist_ok=True)
    return DEFAULT_DIR / f"{base}_{timestamp}.epi"


def _ensure_python_command(cmd: List[str]) -> List[str]:
    """
    Ensure the command is run with Python if it looks like a Python script.
    """
    if not cmd:
        return cmd
    first = cmd[0]
    if first.lower().endswith('.py'):
        return [sys.executable] + cmd
    return cmd


def _build_env_for_child(steps_dir: Path, enable_redaction: bool) -> dict:
    """
    Build environment variables for child process to enable recording via sitecustomize.
    """
    env = os.environ.copy()

    # Indicate recording mode and where to write steps
    env["EPI_RECORD"] = "1"
    env["EPI_STEPS_DIR"] = str(steps_dir)
    env["EPI_REDACT"] = "1" if enable_redaction else "0"

    # Create a temporary bootstrap dir with sitecustomize.py
    bootstrap_dir = Path(tempfile.mkdtemp(prefix="epi_bootstrap_"))
    sitecustomize = bootstrap_dir / "sitecustomize.py"
    sitecustomize.write_text(
        "from epi_recorder.bootstrap import initialize_recording\n",
        encoding="utf-8",
    )

    # Prepend bootstrap dir and project root to PYTHONPATH
    project_root = Path(__file__).resolve().parent.parent
    existing = env.get("PYTHONPATH", "")
    sep = os.pathsep
    env["PYTHONPATH"] = f"{bootstrap_dir}{sep}{project_root}{(sep + existing) if existing else ''}"

    return env


def _verify_recording(epi_file: Path) -> tuple[bool, str]:
    """
    Verify the recording and return status.
    
    Returns:
        (success, message) tuple
    """
    try:
        manifest = EPIContainer.read_manifest(epi_file)
        integrity_ok, mismatches = EPIContainer.verify_integrity(epi_file)
        
        if not integrity_ok:
            return False, f"Integrity check failed ({len(mismatches)} mismatches)"
        
        # Check signature
        if manifest.signature:
            signer_name = get_signer_name(manifest.signature)
            key_manager = KeyManager()
            
            try:
                public_key = key_manager.load_public_key(signer_name or "default")
                signature_valid, msg = verify_signature(manifest, public_key)
                
                if signature_valid:
                    return True, "OK (signed & verified)"
                else:
                    return False, f"Signature invalid: {msg}"
            except FileNotFoundError:
                return True, "OK (unsigned - no public key)"
        else:
            return True, "OK (unsigned)"
            
    except Exception as e:
        return False, f"Verification failed: {e}"


def _open_viewer(epi_file: Path) -> bool:
    """
    Open the viewer for the recording.
    
    Returns:
        True if opened successfully
    """
    try:
        import webbrowser
        
        # Extract viewer to temp location
        temp_dir = Path(tempfile.mkdtemp(prefix="epi_view_"))
        viewer_path = temp_dir / "viewer.html"
        
        with zipfile.ZipFile(epi_file, "r") as zf:
            if "viewer.html" in zf.namelist():
                zf.extract("viewer.html", temp_dir)
                file_url = viewer_path.as_uri()
                return webbrowser.open(file_url)
        
        return False
    except Exception:
        return False


@app.command()
def run(
    script: Path = typer.Argument(..., help="Python script to record"),
    no_verify: bool = typer.Option(False, "--no-verify", help="Skip verification"),
    no_open: bool = typer.Option(False, "--no-open", help="Don't open viewer automatically"),
    # New metadata options
    goal: Optional[str] = typer.Option(None, "--goal", help="Goal or objective of this workflow"),
    notes: Optional[str] = typer.Option(None, "--notes", help="Additional notes about this workflow"),
    metric: Optional[List[str]] = typer.Option(None, "--metric", help="Key=value metrics (can be used multiple times)"),
    approved_by: Optional[str] = typer.Option(None, "--approved-by", help="Person who approved this workflow"),
    tag: Optional[List[str]] = typer.Option(None, "--tag", help="Tags for categorizing this workflow (can be used multiple times)"),
):
    """
    Zero-config recording: record + verify + view.
    
    Example:
        epi run my_script.py
        epi run script.py --goal "improve accuracy" --notes "test run" --metric accuracy=0.92 --metric latency=210 --approved-by "bob" --tag test --tag v1
    """
    # Validate script exists
    if not script.exists():
        console.print(f"[red][FAIL] Error:[/red] Script not found: {script}")
        raise typer.Exit(1)
    
    # Parse metrics if provided
    metrics_dict = None
    if metric:
        metrics_dict = {}
        for m in metric:
            if "=" in m:
                key, value = m.split("=", 1)
                # Try to convert to float if possible, otherwise keep as string
                try:
                    metrics_dict[key] = float(value)
                except ValueError:
                    metrics_dict[key] = value
            else:
                console.print(f"[yellow]Warning:[/yellow] Invalid metric format: {m} (expected key=value)")
    
    # Auto-generate output filename
    out = _gen_auto_name(script)
    
    # Normalize command
    cmd = _ensure_python_command([str(script)])
    
    # Prepare workspace
    temp_workspace = Path(tempfile.mkdtemp(prefix="epi_record_"))
    steps_dir = temp_workspace
    env_json = temp_workspace / "env.json"
    
    # Capture environment snapshot
    save_environment_snapshot(env_json, include_all_env_vars=False, redact_env_vars=True)
    
    # Build child environment and run
    child_env = _build_env_for_child(steps_dir, enable_redaction=True)
    
    # Create stdout/stderr logs
    stdout_log = temp_workspace / "stdout.log"
    stderr_log = temp_workspace / "stderr.log"
    
    console.print(f"[dim]Recording:[/dim] {script.name}")
    
    import subprocess
    
    start = time.time()
    with open(stdout_log, "wb") as out_f, open(stderr_log, "wb") as err_f:
        proc = subprocess.Popen(cmd, env=child_env, stdout=out_f, stderr=err_f)
        rc = proc.wait()
    duration = round(time.time() - start, 3)
    
    # Build manifest with metadata
    manifest = ManifestModel(
        cli_command=" ".join(shlex.quote(c) for c in cmd),
        goal=goal,
        notes=notes,
        metrics=metrics_dict,
        approved_by=approved_by,
        tags=tag
    )
    
    # Package into .epi
    EPIContainer.pack(temp_workspace, manifest, out)
    
    # Auto-sign
    signed = False
    try:
        km = KeyManager()
        priv = km.load_private_key("default")
        
        # Read manifest from ZIP
        import json as _json
        with zipfile.ZipFile(out, "r") as zf:
            raw = zf.read("manifest.json").decode("utf-8")
            data = _json.loads(raw)
        
        # Sign manifest
        from epi_core.schemas import ManifestModel as _MM
        from epi_core.trust import sign_manifest as _sign
        m = _MM(**data)
        sm = _sign(m, priv, "default")
        signed_json = sm.model_dump_json(indent=2)
        
        # Replace manifest in ZIP
        temp_zip = out.with_suffix(".epi.tmp")
        with zipfile.ZipFile(out, "r") as zf_in:
            with zipfile.ZipFile(temp_zip, "w", zipfile.ZIP_DEFLATED) as zf_out:
                for item in zf_in.namelist():
                    if item != "manifest.json":
                        zf_out.writestr(item, zf_in.read(item))
                zf_out.writestr("manifest.json", signed_json)
        
        temp_zip.replace(out)
        signed = True
    except Exception:
        pass  # Non-fatal
    
    # Verify
    verified = False
    verify_msg = "Skipped"
    if not no_verify:
        verified, verify_msg = _verify_recording(out)
    
    # Open viewer
    viewer_opened = False
    if not no_open and rc == 0 and verified:
        viewer_opened = _open_viewer(out)
    
    # Print results
    size_mb = out.stat().st_size / (1024 * 1024)
    
    lines = []
    lines.append(f"[bold]Saved:[/bold] {out}")
    lines.append(f"[bold]Size:[/bold] {size_mb:.2f} MB")
    lines.append(f"[bold]Duration:[/bold] {duration}s")
    
    if not no_verify:
        if verified:
            lines.append(f"[bold]Verified:[/bold] [green]{verify_msg}[/green]")
        else:
            lines.append(f"[bold]Verified:[/bold] [red]{verify_msg}[/red]")
    
    if viewer_opened:
        lines.append(f"[bold]Viewer:[/bold] [green]Opened in browser[/green]")
    elif not no_open:
        lines.append(f"[bold]Viewer:[/bold] [yellow]Could not open automatically[/yellow]")
        lines.append(f"[dim]Open with:[/dim] epi view {out.name}")
    
    title = "[OK] Recording complete" if rc == 0 else "[WARN] Recording finished with errors"
    panel = Panel(
        "\n".join(lines),
        title=title,
        border_style="green" if rc == 0 else "yellow",
    )
    console.print(panel)
    
    # Exit with appropriate code
    if rc != 0:
        raise typer.Exit(rc)
    if not verified and not no_verify:
        raise typer.Exit(1)
    raise typer.Exit(0)