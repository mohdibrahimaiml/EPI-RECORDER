"""
api_demo.py - Safe public demo of EPI public API surface.

This file intentionally omits signing, packaging internals, and
advanced OpenAI patching. It demonstrates the public API and produces
a minimal .epi-like directory for inspection.

Run: python demo/api_demo.py
"""
import json
import os
import time
from contextlib import contextmanager
from pathlib import Path
from uuid import uuid4

@contextmanager
def record_demo(output_dir="demo_output", workflow_name="demo-workflow"):
    start = time.time()
    session_id = str(uuid4())
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    steps_path = out / "steps.jsonl"
    env_path = out / "environment.json"
    # session.start
    with steps_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"kind":"session.start","content":{"workflow_name":workflow_name,"session_id":session_id}}) + "\n")
    try:
        yield {"log_step": lambda k,d: _log_step(steps_path, k, d)}
    finally:
        duration = time.time() - start
        with steps_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"kind":"session.end","content":{"duration":duration,"success":True}}) + "\n")
        env = {
            "platform": os.name,
            "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}",
            "demo": True
        }
        env_path.write_text(json.dumps(env, indent=2))

def _log_step(path: Path, kind: str, content: dict):
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"kind": kind, "content": content}) + "\n")

# Example usage
if __name__ == "__main__":
    from pathlib import Path
    outdir = Path("demo_output_basic")
    if outdir.exists():
        # safe cleanup in demo
        for p in outdir.iterdir():
            p.unlink()
        outdir.rmdir()
    with record_demo(str(outdir), workflow_name="Basic Demo") as epi:
        epi["log_step"]("data.loaded", {"samples": 10})
        # Simulate an LLM request/response capture (demo only)
        epi["log_step"]("llm.request", {"model":"gpt-demo","messages":[{"role":"user","content":"Hello"}]})
        epi["log_step"]("llm.response", {"choices":[{"text":"Hi demo"}], "tokens":5})
        # Add artifact example
        artifact = outdir / "output.csv"
        artifact.write_text("id,value\n1,42\n")
        epi["log_step"]("artifact.captured", {"path": str(artifact), "size": artifact.stat().st_size})
    print("Demo complete. Inspect folder:", outdir)
