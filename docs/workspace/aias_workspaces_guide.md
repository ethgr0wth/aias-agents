# Using AiAS Workspaces for Chat Completions

## Overview

AiAS gives you two ways to talk to AI through the API:

1. **OpenAI-compatible endpoint** — stateless, drop-in replacement for the OpenAI SDK
2. **Workspace endpoint** — stateful conversations that persist in the dashboard, support human handoff, memory, directives, and more

This guide covers both, starting with the basics.

---

## Authentication

Every API request needs your AiAS API key. Keys always start with `aai_`.

```
Authorization: Bearer aai_your_key_here
```

You can also use `X-API-Key: aai_your_key_here` as an alternative header.

Get your key from the dashboard at **Account Settings → API Keys**.

---

## Option 1 — OpenAI-Compatible (stateless)

If you already use the OpenAI SDK, just change the base URL. No other changes required.

### Endpoint

```
POST /v1/chat/completions
```

### Request

```json
{
  "model": "llama-3.3-70b-versatile",
  "messages": [
    { "role": "system", "content": "You are a helpful assistant." },
    { "role": "user", "content": "Explain transformer architecture in plain English." }
  ],
  "stream": false
}
```

### Response

Standard OpenAI format — you get `choices[0].message.content` back.

### With the OpenAI SDK

```python
from openai import OpenAI

client = OpenAI(
    api_key="aai_your_key_here",
    base_url="https://your-aias-domain.com/v1"
)

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {"role": "user", "content": "What is the capital of France?"}
    ]
)

print(response.choices[0].message.content)
```

### Streaming

```python
stream = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Tell me a short story."}],
    stream=True
)

for chunk in stream:
    print(chunk.choices[0].delta.content or "", end="", flush=True)
```

### Supported models

The model name determines the provider automatically:

| Provider | Example models |
|---|---|
| Groq | `llama-3.3-70b-versatile`, `llama-3.1-8b-instant` |
| OpenAI | `gpt-4o`, `gpt-4o-mini`, `o1-mini` |
| Anthropic | `claude-sonnet-4-20250514`, `claude-haiku-3-5-20241022` |
| Gemini | `gemini-2.0-flash`, `gemini-1.5-pro` |
| Mistral | `mistral-large-latest`, `mistral-small-latest` |

---

## Option 2 — Workspaces (stateful conversations)

Workspaces are persistent chat threads. Every message and AI response is stored and visible in your dashboard. They support:

- Full conversation history the AI remembers
- Human takeover / shadow mode
- Directives (standing instructions)
- Conversation memory with configurable scope
- Contact/lead tracking

### Step 1 — Create a workspace

```
POST /api/workspaces
Authorization: Bearer aai_your_key_here
Content-Type: application/json
```

```json
{
  "initial_message": "Hi, I need help with my billing",
  "client_id": "user-abc-123",
  "model": "llama-3.3-70b-versatile",
  "mode": "ai"
}
```

**Fields:**

| Field | Required | Description |
|---|---|---|
| `initial_message` | Yes | The first user message. AI responds immediately. |
| `client_id` | No | Your own identifier (user ID, session ID, etc). If an active workspace already exists for this client, it reuses it instead of creating a new one. |
| `model` | No | Model to use for this message. Defaults to your configured provider. |
| `system_prompt` | No | Override the system instructions for this workspace. |
| `mode` | No | `ai` (default), `shadow` (AI drafts, human approves), `takeover` (human only) |
| `max_tokens` | No | Cap the response length |

**Response:**

```json
{
  "workspace": {
    "id": "ws_xxxxxxxxxxx",
    "mode": "ai",
    "status": "active",
    "created_at": "2026-05-21T10:00:00Z"
  },
  "messages": [
    { "id": "msg_1", "role": "user", "content": "Hi, I need help with my billing" },
    { "id": "msg_2", "role": "assistant", "content": "Of course! I'd be happy to help with billing..." }
  ]
}
```

Save the `workspace.id` — you'll use it for every follow-up message.

---

### Step 2 — Send follow-up messages

```
POST /api/workspaces/{workspace_id}/messages
Authorization: Bearer aai_your_key_here
Content-Type: application/json
```

```json
{
  "content": "I was charged twice this month",
  "model": "llama-3.3-70b-versatile"
}
```

**Fields:**

| Field | Required | Description |
|---|---|---|
| `content` | Yes | The user's message |
| `model` | No | Override model for this message |

**Response** includes the user message and the AI reply.

---

### Step 3 — Resume an existing workspace

If you pass a `client_id` when creating a workspace and a workspace for that client already exists, AiAS returns the existing one — no duplicate threads.

You can also look up a workspace by client ID directly:

```
GET /api/workspaces/by-client/{client_id}
Authorization: Bearer aai_your_key_here
```

---

## Putting it together — full example

```python
import requests

BASE = "https://your-aias-domain.com"
HEADERS = {
    "Authorization": "Bearer aai_your_key_here",
    "Content-Type": "application/json"
}

# Start a conversation
res = requests.post(f"{BASE}/api/workspaces", headers=HEADERS, json={
    "initial_message": "I need help setting up my account",
    "client_id": "user-42",
    "model": "llama-3.3-70b-versatile"
})
data = res.json()
workspace_id = data["workspace"]["id"]
print("AI:", data["messages"][-1]["content"])

# Continue the conversation
res = requests.post(f"{BASE}/api/workspaces/{workspace_id}/messages", headers=HEADERS, json={
    "content": "What plan do you recommend for a small team of 5?"
})
reply = res.json()
print("AI:", reply["messages"][-1]["content"])
```

---

## Workspace modes

| Mode | What happens |
|---|---|
| `ai` | AI responds automatically to every message |
| `shadow` | AI drafts a response but it waits for a human to approve before sending |
| `takeover` | AI is off — a human handles the conversation manually |

Switch mode at any time:

```
PATCH /api/workspaces/{workspace_id}
```
```json
{ "mode": "shadow" }
```

---

## Quick reference

| Action | Method | Path |
|---|---|---|
| Stateless completion | POST | `/v1/chat/completions` |
| Create workspace | POST | `/api/workspaces` |
| Send message | POST | `/api/workspaces/{id}/messages` |
| Get workspace | GET | `/api/workspaces/{id}` |
| Find by client | GET | `/api/workspaces/by-client/{client_id}` |
| Update mode | PATCH | `/api/workspaces/{id}` |
| List workspaces | GET | `/api/user/workspaces` |
