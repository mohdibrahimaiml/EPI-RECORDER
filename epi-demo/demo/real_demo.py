"""
Real EPI Demo - Using the actual epi-recorder package

This demonstrates the REAL functionality of epi-recorder.
No mock implementations - this is the actual production code.
"""
from epi_recorder import record

print("🎬 EPI Demo - Using Real epi-recorder Package\n")

# Example 1: Basic Recording
print("Example 1: Basic Recording")
print("-" * 60)
with record("../basic-usage/basic-usage.epi", workflow_name="Basic OpenAI Chat") as epi:
    # Simulate workflow steps
    epi.log_step("llm.request", {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Explain quantum computing in one paragraph."}
        ],
        "temperature": 0.7,
        "max_tokens": 150
    })
    
    epi.log_step("llm.response", {
        "choices": [{
            "message": {
                "role": "assistant",
                "content": "Quantum computing leverages quantum mechanics principles..."
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 25,
            "completion_tokens": 87,
            "total_tokens": 112
        }
    })

print("✓ Created basic-usage.epi using REAL epi-recorder\n")

# Example 2: Streaming Simulation
print("Example 2: Streaming Workflow")
print("-" * 60)
with record("../openai-streaming/openai-streaming.epi", 
            workflow_name="Streaming Chat Completion") as epi:
    
    epi.log_step("llm.request", {
        "model": "gpt-4",
        "messages": [{"role": "user", "content": "Write a haiku about AI"}],
        "stream": True
    })
    
    # Simulate streaming chunks
    chunks = ["Silicon", " minds", " awake", ",\n", 
              "Learning", " patterns", ",\n", 
              "Digital", " dreams", " unfold"]
    
    for chunk in chunks:
        epi.log_step("llm.stream_chunk", {
            "delta": {"content": chunk},
            "finish_reason": None
        })
    
    epi.log_step("llm.stream_chunk", {
        "delta": {},
        "finish_reason": "stop"
    })

print("✓ Created openai-streaming.epi using REAL epi-recorder\n")

# Example 3: Multi-Turn Conversation
print("Example 3: Multi-Turn Conversation")
print("-" * 60)
with record("../multi-turn/multi-turn.epi", 
            workflow_name="Multi-Turn Conversation") as epi:
    
    # Turn 1
    epi.log_step("llm.request", {
        "model": "gpt-4",
        "messages": [
            {"role": "user", "content": "What is the capital of France?"}
        ]
    })
    epi.log_step("llm.response", {
        "choices": [{
            "message": {
                "role": "assistant",
                "content": "The capital of France is Paris."
            }
        }]
    })
    
    # Turn 2
    epi.log_step("llm.request", {
        "model": "gpt-4",
        "messages": [
            {"role": "user", "content": "What is the capital of France?"},
            {"role": "assistant", "content": "The capital of France is Paris."},
            {"role": "user", "content": "What is its population?"}
        ]
    })
    epi.log_step("llm.response", {
        "choices": [{
            "message": {
                "role": "assistant",
                "content": "Paris has approximately 2.2 million people within city limits."
            }
        }]
    })
    
    # Turn 3
    epi.log_step("llm.request", {
        "model": "gpt-4",
        "messages": [
            {"role": "user", "content": "What is the capital of France?"},
            {"role": "assistant", "content": "The capital of France is Paris."},
            {"role": "user", "content": "What is its population?"},
            {"role": "assistant", "content": "Paris has approximately 2.2 million people."},
            {"role": "user", "content": "What are the top tourist attractions?"}
        ]
    })
    epi.log_step("llm.response", {
        "choices": [{
            "message": {
                "role": "assistant",
                "content": "Top attractions include the Eiffel Tower, Louvre Museum, Notre-Dame."
            }
        }]
    })

print("✓ Created multi-turn.epi using REAL epi-recorder\n")

print("\n" + "=" * 60)
print("✅ All examples created using REAL epi-recorder!")
print("=" * 60)
print("\nThese .epi files were created with the production epi-recorder package,")
print("including:")
print("  - Full manifest generation")
print("  - Cryptographic signing (Ed25519)")
print("  - Environment capture")
print("  - SHA-256 file hashing")
print("  - ZIP archive packaging")
print("\nVerify with:")
print("  python -m epi_cli.main verify ../basic-usage/basic-usage.epi")
