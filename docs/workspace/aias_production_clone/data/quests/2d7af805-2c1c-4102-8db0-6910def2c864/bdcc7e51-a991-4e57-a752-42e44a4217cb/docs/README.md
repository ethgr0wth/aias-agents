# AI Agent Documentation (AiAS Demo)

## Overview
This project is a minimal Python CLI “agent” that calls **AiAS** (AiAssist.net) using the OpenAI-compatible endpoint:
- `POST https://AiAssist.net/v1/chat/completions`

It sends user prompts as chat messages and prints the assistant response.

---

## Requirements
- Python 3.9+
- An AiAS API key (starts with `aai_...`)
- Dependencies (see `requirements.txt`): `requests`

---

## Configuration

### Option A: `config.json` (recommended)
Create or edit `config.json` in the project root:

```json
{
  "api_key": "aai_your_key_here",
  "base_url": "https://AiAssist.net",
  "model": "llama-3.3-70b-versatile",
  "agent_id": null,
  "provider": null,
  "temperature": 0.7,
  "max_tokens": 1024,
  "timeout_seconds": 30
}
```

**Fields**
- `api_key` (required): Your AiAS API key.
- `base_url` (optional): Defaults to `https://AiAssist.net`.
- `model` (optional): Defaults to `llama-3.3-70b-versatile`.
- `agent_id` (optional): If set, sent as header `X-Agent-Id` to target a deployed agent.
- `provider` (optional): If set, sent as header `X-AiAssist-Provider` (`groq`, `openai`, `anthropic`, `gemini`, `mistral`).
- `temperature`, `max_tokens`, `timeout_seconds` (optional): Generation + request tuning.

### Option B: Environment variables
If `config.json` is missing or incomplete, the agent uses env vars:
- `AIAS_API_KEY` (or `AIASSIST_API_KEY`)
- `AIAS_BASE_URL`
- `AIAS_MODEL`
- `AIAS_AGENT_ID`
- `AIAS_PROVIDER`
- `AIAS_TEMPERATURE`
- `AIAS_MAX_TOKENS`
- `AIAS_TIMEOUT_SECONDS`

Example (bash):
```bash
export AIAS_API_KEY="aai_your_key_here"
export AIAS_MODEL="llama-3.3-70b-versatile"
```

---

## Running the CLI

Install dependencies:
```bash
pip install -r requirements.txt
```

Run:
```bash
python agent.py
```

You should see:
```
AiAS Agent CLI
Type 'exit' or Ctrl+C to quit.

User:
```

---

## How the API Call Works

### Endpoint
`POST /v1/chat/completions`

### Headers used
- `Authorization: Bearer aai_...` (required)
- `Content-Type: application/json`
- `X-Agent-Id: ...` (optional)
- `X-AiAssist-Provider: ...` (optional)

### Request body example
```json
{
  "model": "llama-3.3-70b-versatile",
  "messages": [
    { "role": "user", "content": "Hello!" }
  ],
  "temperature": 0.7,
  "max_tokens": 1024,
  "stream": false
}
```

### Response parsing
The CLI prints:
- `response.json()["choices"][0]["message"]["content"]`

---

## Programmatic Usage (importing Agent)

```python
from agent import Agent, AgentConfig

cfg = AgentConfig(
    api_key="aai_your_key_here",
    base_url="https://AiAssist.net",
    model="llama-3.3-70b-versatile",
)

agent = Agent(cfg)
reply = agent.chat([{"role": "user", "content": "Write a haiku about APIs."}])
print(reply)
```

---

## Troubleshooting

- **401 Unauthorized**: API key missing/invalid. Ensure it starts with `aai_`.
- **402 Subscription inactive**: Account plan does not allow API usage.
- **429 Rate limit**: Slow down requests or upgrade plan.
- **Timeouts**: Increase `timeout_seconds` in `config.json`.

---

## Security Notes
- Do not commit real API keys to source control.
- Prefer environment variables or local-only `config.json` excluded by `.gitignore`.