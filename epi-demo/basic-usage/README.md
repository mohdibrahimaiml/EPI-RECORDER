# Basic Usage Demo

This demo shows a simple OpenAI API call captured as an EPI file.

## What's Captured

- A single chat completion request
- System and user messages
- Model configuration (temperature, max tokens)
- Complete response with timing

## Try It Yourself

```bash
curl https://api.openai.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
    "model": "gpt-4",
    "messages": [
      {
        "role": "system",
        "content": "You are a helpful assistant."
      },
      {
        "role": "user",
        "content": "Explain quantum computing in one paragraph."
      }
    ],
    "temperature": 0.7,
    "max_tokens": 150
  }'
```

## View the Recording

Open `basic-usage.epi` with:
- [EPI Viewer](https://epi-viewer.example.com) (drag & drop)
- CLI: `epi view basic-usage.epi`
