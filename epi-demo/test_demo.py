"""
Comprehensive test script for EPI demo
Tests that all .epi files are valid and properly structured
"""
import sys
import zipfile
import json
from pathlib import Path

def test_epi_file(filepath):
    """Test that an .epi file is valid."""
    print(f"\n{'='*60}")
    print(f"Testing: {filepath}")
    print('='*60)
    
    path = Path(filepath)
    
    # Test 1: File exists
    if not path.exists():
        print("❌ FAIL: File does not exist")
        return False
    print("✓ File exists")
    
    # Test 2: Is a valid ZIP
    try:
        with zipfile.ZipFile(path, 'r') as zf:
            files = zf.namelist()
            print(f"✓ Valid ZIP archive with {len(files)} files")
    except Exception as e:
        print(f"❌ FAIL: Not a valid ZIP: {e}")
        return False
    
    # Test 3: Contains required files
    required_files = ['manifest.json', 'steps.jsonl', 'environment.json', 'mimetype']
    for req_file in required_files:
        if req_file in files:
            print(f"✓ Contains {req_file}")
        else:
            print(f"❌ FAIL: Missing {req_file}")
            return False
    
    # Test 4: Manifest is valid JSON
    try:
        with zipfile.ZipFile(path, 'r') as zf:
            manifest_data = zf.read('manifest.json')
            manifest = json.loads(manifest_data)
            print(f"✓ Valid manifest.json")
            print(f"  - Session ID: {manifest.get('session_id', 'N/A')}")
            print(f"  - Workflow: {manifest.get('workflow_name', 'N/A')}")
            print(f"  - Steps: {manifest.get('step_count', 'N/A')}")
    except Exception as e:
        print(f"❌ FAIL: Invalid manifest.json: {e}")
        return False
    
    # Test 5: Steps is valid JSONL
    try:
        with zipfile.ZipFile(path, 'r') as zf:
            steps_data = zf.read('steps.jsonl').decode('utf-8')
            steps = [json.loads(line) for line in steps_data.strip().split('\n')]
            print(f"✓ Valid steps.jsonl with {len(steps)} steps")
            
            # Verify first and last steps
            if steps:
                if steps[0]['kind'] == 'session.start':
                    print(f"✓ Starts with session.start")
                else:
                    print(f"⚠ Warning: First step is {steps[0]['kind']}, expected session.start")
                
                if steps[-1]['kind'] == 'session.end':
                    print(f"✓ Ends with session.end")
                else:
                    print(f"⚠ Warning: Last step is {steps[-1]['kind']}, expected session.end")
    except Exception as e:
        print(f"❌ FAIL: Invalid steps.jsonl: {e}")
        return False
    
    # Test 6: Environment is valid JSON
    try:
        with zipfile.ZipFile(path, 'r') as zf:
            env_data = zf.read('environment.json')
            env = json.loads(env_data)
            print(f"✓ Valid environment.json")
            print(f"  - Platform: {env.get('platform', 'N/A')}")
            print(f"  - Python: {env.get('python_version', 'N/A')}")
    except Exception as e:
        print(f"❌ FAIL: Invalid environment.json: {e}")
        return False
    
    # Test 7: Mimetype is correct
    try:
        with zipfile.ZipFile(path, 'r') as zf:
            mimetype = zf.read('mimetype').decode('utf-8')
            if mimetype == 'application/vnd.epi+zip':
                print(f"✓ Correct mimetype: {mimetype}")
            else:
                print(f"⚠ Warning: Mimetype is '{mimetype}', expected 'application/vnd.epi+zip'")
    except Exception as e:
        print(f"❌ FAIL: Invalid mimetype: {e}")
        return False
    
    print(f"\n✅ ALL TESTS PASSED for {path.name}")
    return True

def main():
    print("🧪 EPI Demo Test Suite")
    print("="*60)
    
    # Test demo-generated files
    demo_files = [
        'demo/basic_demo.epi',
        'demo/multi_step_demo.epi'
    ]
    
    # Test example files
    example_files = [
        'basic-usage/basic-usage.epi',
        'openai-streaming/openai-streaming.epi',
        'multi-turn/multi-turn.epi'
    ]
    
    all_files = demo_files + example_files
    results = {}
    
    for filepath in all_files:
        full_path = Path(__file__).parent / filepath
        results[filepath] = test_epi_file(full_path)
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print('='*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for filepath, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {filepath}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Demo is fully functional.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
