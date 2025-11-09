# OpenAI Streaming Demo

This demo captures a streaming chat completion with real-time token delivery.

## What's Captured

- Streaming API request
- Token-by-token response chunks
- Server-sent events (SSE) stream
- Complete timing and latency data

## Try It Yourself

```bash
curl https://api.openai.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
    "model": "gpt-4",
    "messages": [
      {
        "role": "user",
        "content": "Write a haiku about programming."
      }
    ],
    "stream": true
  }'
```

## View the Recording

Open `openai-streaming.epi` with:
- [EPI Viewer](https://epi-viewer.example.com) (drag & drop)
- CLI: `epi view openai-streaming.epi`

The viewer will show token-by-token replay of the streamed response.
