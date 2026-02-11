"""
Quick test of analytics engine
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from epi_recorder.analytics import AgentAnalytics
    print("SUCCESS: AgentAnalytics imported")
    
    # Test with current directory
    try:
        analytics = AgentAnalytics(".")
        print(f"SUCCESS: Loaded {len(analytics.artifacts)} artifacts")
        
        # Test summary
        summary = analytics.performance_summary()
        print(f"Total runs: {summary['total_runs']}")
        print(f"Success rate: {summary['success_rate']:.1f}%")
        
    except ValueError as e:
        print(f"INFO: {e}")
        print("(This is expected if no .epi files exist yet)")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        
except ImportError as e:
    print(f"ERROR: Could not import AgentAnalytics: {e}")
    import traceback
    traceback.print_exc()
