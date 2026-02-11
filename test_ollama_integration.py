"""
Test Ollama integration with EPI Recorder

This script demonstrates using a local Ollama model (DeepSeek-R1)
with EPI recorder - FREE LLM calls for development/testing!
"""

from openai import OpenAI
from epi_recorder import record, wrap_openai
import sys

def test_ollama_with_epi():
    """Test that Ollama works with EPI recording"""
    
    print("TESTING OLLAMA + EPI INTEGRATION")
    print()
    
    # Create Ollama client (OpenAI-compatible API)
    client = OpenAI(
        base_url="http://localhost:11434/v1",
        api_key="ollama"  # Doesn't matter for local
    )
    
    # Wrap with EPI tracing
    client = wrap_openai(client)
    
    # Record a simple conversation
    print("📝 Recording test conversation to 'ollama_test.epi'...")
    
    try:
        with record("ollama_test.epi", goal="Test Ollama integration") as epi:
            response = client.chat.completions.create(
                model="deepseek-r1:7b",
                messages=[
                    {"role": "user", "content": "Write a haiku about coding"}
                ],
                temperature=0.7
            )
            
            content = response.choices[0].message.content
            print(f"\n🤖 DeepSeek-R1 response:\n{content}\n")
            
            # Log custom metadata
            epi.log_step(
                kind="custom.test",
                content={
                    "test_type": "ollama_integration",
                    "model": "deepseek-r1:7b",
                    "success": True
                }
            )
        
        print("✅ SUCCESS! .epi file created at: ollama_test.epi")
        print("\nNow verify it:")
        print("  epi verify ollama_test.epi")
        print("  epi view ollama_test.epi")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print("\nMake sure:")
        print("  1. Ollama is running: ollama serve")
        print("  2. Model is pulled: ollama pull deepseek-r1:7b")
        print("  3. Model is available: ollama list")
        return False

def generate_test_data():
    """Generate multiple .epi files for analytics testing"""
    
    print("\n📊 Generating test data for analytics...\n")
    
    client = wrap_openai(OpenAI(
        base_url="http://localhost:11434/v1",
        api_key="ollama"
    ))
    
    prompts = [
        "Explain recursion in one sentence",
        "What is a closure?",
        "Difference between sync and async?",
        "What are generators in Python?",
        "Explain decorators"
    ]
    
    for i, prompt in enumerate(prompts):
        try:
            with record(f"test_run_{i+1}.epi", goal=f"Test {i+1}") as epi:
                response = client.chat.completions.create(
                    model="deepseek-r1:7b",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7
                )
                print(f"  ✓ Created test_run_{i+1}.epi")
        except Exception as e:
            print(f"  ✗ Failed test_run_{i+1}.epi: {e}")
    
    print("\n✅ Test data generated!")
    print("\nNow test analytics:")
    print("  from epi_recorder import AgentAnalytics")
    print("  analytics = AgentAnalytics('.')")
    print("  analytics.success_rate_over_time()")

if __name__ == "__main__":
    # Test basic integration
    success = test_ollama_with_epi()
    
    if success and "--generate-data" in sys.argv:
        generate_test_data()
