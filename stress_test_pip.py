import subprocess
import concurrent.futures
import time
import os
import shutil
import tempfile

PACKAGE_NAME = "epi-recorder"
MAX_WORKERS = 20  # Increased workers for more massive load
TOTAL_INSTALLS = 200 # Significant increase in total installs

def install_epi(install_id):
    temp_dir = tempfile.mkdtemp(prefix=f"epi_stress_{install_id}_")
    try:
        print(f"[{install_id}] Starting installation in {temp_dir}...")
        start_time = time.time()
        
        # Run pip install with flags to force network activity and isolate
        result = subprocess.run(
            [
                "pip", "install", PACKAGE_NAME,
                "--force-reinstall",
                "--no-cache-dir",
                "--target", temp_dir,
                "--no-user",
                "--quiet"
            ],
            capture_output=True,
            text=True
        )
        
        duration = time.time() - start_time
        
        if result.returncode == 0:
            print(f"[{install_id}] SUCCESS: Installed in {duration:.2f}s")
            return True, duration
        else:
            print(f"[{install_id}] FAILED: {result.stderr}")
            return False, duration
            
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

def main():
    print(f"Starting stress test for '{PACKAGE_NAME}'...")
    print(f"Total Installs: {TOTAL_INSTALLS}, Max Workers: {MAX_WORKERS}")
    
    start_total = time.time()
    results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_id = {executor.submit(install_epi, i): i for i in range(TOTAL_INSTALLS)}
        for future in concurrent.futures.as_completed(future_to_id):
            install_id = future_to_id[future]
            try:
                success, duration = future.result()
                results.append((success, duration))
            except Exception as exc:
                print(f"[{install_id}] generated an exception: {exc}")
                results.append((False, 0))

    end_total = time.time()
    
    successes = [r for r in results if r[0]]
    failures = [r for r in results if not r[0]]
    avg_duration = sum(r[1] for r in successes) / len(successes) if successes else 0
    
    print("\n" + "="*40)
    print("STRESS TEST RESULTS")
    print("="*40)
    print(f"Total Time: {end_total - start_total:.2f}s")
    print(f"Successful Installs: {len(successes)}")
    print(f"Failed Installs: {len(failures)}")
    print(f"Average Install Time: {avg_duration:.2f}s")
    print("="*40)

if __name__ == "__main__":
    main()
