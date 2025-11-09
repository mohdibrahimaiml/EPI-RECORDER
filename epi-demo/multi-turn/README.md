# Multi-Turn Conversation Demo

This demo captures a complete conversation with context and follow-ups.

## What's Captured

- Multiple sequential API calls
- Conversation context maintenance
- Message history across turns
- Complete interaction flow

## Try It Yourself

### Turn 1: Initial Question
```bash
curl https://api.openai.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
    "model": "gpt-4",
    "messages": [
      {
        "role": "user",
        "content": "What is the capital of France?"
      }
    ]
  }'
```

### Turn 2: Follow-up
```bash
curl https://api.openai.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
    "model": "gpt-4",
    "messages": [
      {
        "role": "user",
        "content": "What is the capital of France?"
      },
      {
        "role": "assistant",
        "content": "The capital of France is Paris."
      },
      {
        "role": "user",
        "content": "What is its population?"
      }
    ]
  }'
```

### Turn 3: Deeper Context
```bash
curl https://api.openai.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
    "model": "gpt-4",
    "messages": [
      {
        "role": "user",
        "content": "What is the capital of France?"
      },
      {
        "role": "assistant",
        "content": "The capital of France is Paris."
      },
      {
        "role": "user",
        "content": "What is its population?"
      },
      {
        "role": "assistant",
        "content": "Paris has approximately 2.2 million people within city limits, and over 12 million in the metropolitan area."
      },
      {
        "role": "user",
        "content": "What are the top tourist attractions there?"
      }
    ]
  }'
```

## View the Recording

Open `multi-turn.epi` with:
- [EPI Viewer](https://epi-viewer.example.com) (drag & drop)
- CLI: `epi view multi-turn.epi`

The viewer will show the complete conversation flow with context.
