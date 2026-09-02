# PIN OpenAI Proxy

A lightweight proxy server that allows PIN daemon to use OpenAI as an inference backend.

## How It Works

```
PIN Daemon → localhost:8000 (this proxy) → api.openai.com
```

The proxy:
- Binds to `127.0.0.1:8000` (localhost only, never exposed publicly)
- Forwards requests to OpenAI with your API key injected server-side
- Streams responses back for PIN interviews
- Supports all PIN-required endpoints

## Setup

1. Set your OpenAI API key:
```bash
export OPENAI_API_KEY=sk-your-key-here
```

2. Run the proxy:
```bash
python pin-proxy/server.py
```

3. Configure PIN daemon:
```json
{
  "clientId": "op_xxx",
  "apiSecret": "your-secret",
  "nodes": [
    {
      "alias": "openai-proxy",
      "inferenceUri": "http://localhost:8000",
      "apiMode": "openai",
      "region": "local",
      "capacity": 10
    }
  ]
}
```

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/v1/models` | GET | List available models |
| `/v1/models/{id}` | GET | Get specific model |
| `/v1/chat/completions` | POST | Chat completions (streaming supported) |
| `/v1/completions` | POST | Legacy completions (streaming supported) |
| `/v1/embeddings` | POST | Text embeddings |

## Available Models

### GPT-4.1 Series (Latest)
- `gpt-4.1` - Latest flagship model
- `gpt-4.1-mini` - Fast, affordable
- `gpt-4.1-nano` - Fastest, most affordable
- `gpt-4.1-preview` - Preview features

### O-Series Reasoning Models
- `o4-mini` - Latest reasoning model
- `o3` - Advanced reasoning
- `o3-mini` - Balanced reasoning
- `o1`, `o1-mini`, `o1-preview` - First-gen reasoning

### GPT-4o Series
- `gpt-4o` - Multimodal flagship
- `gpt-4o-mini` - Fast multimodal
- `gpt-4o-audio-preview` - Audio capabilities

### GPT-4 & GPT-3.5
- `gpt-4-turbo`, `gpt-4`, `gpt-4-32k`
- `gpt-3.5-turbo`, `gpt-3.5-turbo-16k`
- `gpt-3.5-turbo-instruct` (for legacy completions)

### Embeddings
- `text-embedding-3-large`
- `text-embedding-3-small`
- `text-embedding-ada-002`

## PIN Compatibility

This proxy fully supports PIN daemon's OpenAI mode:

- **Interview System**: `/v1/chat/completions` for interview prompts
- **Legacy Scoring**: `/v1/completions` for legacy scoring prompts
- **Model Discovery**: `/v1/models` for available model list
- **Streaming**: Full SSE streaming with proper `data:` frames and `[DONE]`
- **Error Handling**: Proper HTTP status codes forwarded for failure detection

## Security

- Only binds to `127.0.0.1` (localhost) - never exposed publicly
- API key stays server-side, never sent to PIN
- PIN daemon connects locally only
- No credentials logged or exposed

## Troubleshooting

**"OPENAI_API_KEY not configured"**
```bash
export OPENAI_API_KEY=sk-your-key-here
```

**Connection refused**
Make sure the proxy is running:
```bash
python pin-proxy/server.py
```

**Model not found**
Check if the model is in the available list:
```bash
curl http://localhost:8000/v1/models
```
