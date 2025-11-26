
import os
import json
import time
import shutil
import zipfile
import requests
from pathlib import Path
from datetime import datetime
from epi_recorder.api import record

def simulate_user_workflow():
    print("\n[SIMULATION] Starting End-to-End User Workflow Simulation...")
    
    output_file = Path("simulation_output.epi").absolute()
    if output_file.exists():
        output_file.unlink()
        
    # 1. Start Recording
    print("1. Starting recording session...")
    with record(
        output_path=output_file,
        workflow_name="User Simulation",
        tags=["simulation", "test"],
        auto_sign=False,  # Skip signing for test speed/simplicity
        goal="Verify end-to-end functionality",
        notes="Automated simulation run"
    ) as session:
        
        # 2. Log Manual Steps
        print("2. Logging manual steps...")
        session.log_step("user.action", {"action": "click", "target": "submit_button"})
        session.log_step("system.state", {"status": "processing", "load": 0.5})
        
        # 3. Simulate HTTP Request (should be patched)
        print("3. Making HTTP request (testing patching)...")
        try:
            # Use httpbin for a real request
            requests.get("https://httpbin.org/get", headers={"User-Agent": "EpiSimulation"})
        except Exception as e:
            print(f"   Warning: HTTP request failed (network issue?): {e}")
            
        # 4. Log Artifact
        print("4. Creating and logging artifact...")
        artifact_path = Path("sim_artifact.txt")
        artifact_path.write_text("This is a simulated artifact content.")
        session.log_artifact(artifact_path)
        
        # 5. Simulate some "thinking" time
        time.sleep(0.5)
        
    print("5. Recording session ended.")
    
    # 6. Verify Output
    print("\n[VERIFICATION] Verifying output file...")
    
    if not output_file.exists():
        raise FileNotFoundError(f"Output file {output_file} was not created!")
        
    print(f"   Output file exists: {output_file} ({output_file.stat().st_size} bytes)")
    
    with zipfile.ZipFile(output_file, 'r') as zf:
        file_list = zf.namelist()
        print(f"   Files in archive: {file_list}")
        
        # Check Manifest
        if "manifest.json" not in file_list:
            raise ValueError("manifest.json missing from archive!")
            
        manifest_data = json.loads(zf.read("manifest.json"))
        print(f"   Manifest Goal: {manifest_data.get('goal')}")
        if manifest_data.get("goal") != "Verify end-to-end functionality":
            raise ValueError("Manifest goal mismatch!")
            
        # Check Steps
        if "steps.jsonl" not in file_list:
            raise ValueError("steps.jsonl missing from archive!")
            
        steps_content = zf.read("steps.jsonl").decode("utf-8")
        steps = [json.loads(line) for line in steps_content.splitlines()]
        print(f"   Recorded {len(steps)} steps.")
        
        # Verify specific steps
        kinds = [s["kind"] for s in steps]
        if "user.action" not in kinds:
            raise ValueError("Manual step 'user.action' not found!")
        if "http.request" not in kinds:
            print("   WARNING: 'http.request' not found! (Did patching fail or network error?)")
        else:
            print("   'http.request' found (Patching verified).")
            
        if "artifact.captured" not in kinds:
            raise ValueError("Artifact step not found!")
            
        # Check Artifact File
        if "artifacts/sim_artifact.txt" not in file_list:
            raise ValueError("Artifact file missing from archive!")
            
        artifact_content = zf.read("artifacts/sim_artifact.txt").decode("utf-8")
        if artifact_content != "This is a simulated artifact content.":
            raise ValueError("Artifact content mismatch!")
            
    print("\n[SUCCESS] End-to-End Simulation Passed!")
    
    # Cleanup
    if output_file.exists():
        output_file.unlink()
    if Path("sim_artifact.txt").exists():
        Path("sim_artifact.txt").unlink()

if __name__ == "__main__":
    try:
        simulate_user_workflow()
    except Exception as e:
        print(f"\n[FAILURE] Simulation Failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
