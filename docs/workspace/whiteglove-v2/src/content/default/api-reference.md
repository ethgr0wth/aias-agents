---
title: API Reference
icon: Code
category: Developers
order: 5
description: Full API documentation for endpoints and authentication.
---

# API Reference

> Complete HTTP and WebSocket API documentation for AiAssist

**Base URL:** `https://api.aiassist.net` (managed) or your self-hosted endpoint (enterprise)

**Authentication:** All requests require an API key in the header:
```
X-API-Key: your_api_key
```

---

## Model Selection

AiAssist supports dynamic model selection via the API. You can specify any model from your configured providers:

### Model Priority

1. **Request model** - If you specify a `model` in the API request, that model is used
2. **Agent default** - If no model specified and you have a deployed agent, the agent's model is used
3. **User's first configured provider** - Uses the default model of your first configured provider
4. **Ultimate fallback** - Falls back to `llama-3.3-70b-versatile` (Groq) if no providers configured

### Provider Auto-Detection

The provider is automatically detected from the model name:

| Model Prefix | Provider |
|-------------|----------|
| `gpt-*` | OpenAI |
| `claude-*` | Anthropic |
| `gemini-*` | Google Gemini |
| `mistral-*` | Mistral AI |
| `llama-*`, `mixtral-*` | Groq |
| `grok-*` | xAI |
| `deepseek-*` | DeepSeek |
| `sonar*` | Perplexity |
| `meta-llama/*`, `Qwen/*` | Together AI |
| `accounts/fireworks/*` | Fireworks AI |
| `provider/model` format | OpenRouter |

### Override Provider

Use the `X-AiAssist-Provider` header to force a specific provider:

```bash
curl -X POST https://api.aiassist.net/v1/chat/completions \
  -H "Authorization: Bearer aai_xxxxx" \
  -H "X-AiAssist-Provider: openai" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-4o", "messages": [{"role": "user", "content": "Hello"}]}'
```

---

## HTTP Endpoints

### Workspaces

A workspace represents a single chat conversation session.

#### Create Workspace

Start a new conversation.

```http
POST /api/workspaces
```

**Request Body:**
```json
{
  "initial_message": "Hello, I need help with my order",
  "title": "Order Support",
  "metadata": {
    "user_id": "usr_123",
    "page_url": "https://example.com/checkout"
  }
}
```

#### Get Workspace

Retrieve workspace details.

```http
GET /api/workspaces/{workspace_id}
```

#### List Workspaces (Admin)

List all workspaces. Requires manager/admin role.

```http
GET /api/workspaces?active_only=true
```

---

### Messages

#### Send Message

Send a message to a workspace.

```http
POST /api/workspaces/{workspace_id}/messages
```

**Request Body:**
```json
{
  "content": "My order number is #12345"
}
```

#### Get Messages

Retrieve all messages in a workspace.

```http
GET /api/workspaces/{workspace_id}/messages
```

---

### WebSocket API

Real-time communication for live updates. Uses Socket.IO protocol.

**Endpoint:** `wss://api.aiassist.net/socket.io`

#### Client Namespace (`/client`)

For customer-facing chat widgets.

**`join_workspace`**
```json
{
  "workspace_id": "ws_abc123"
}
```

**`send_message`**
```json
{
  "workspace_id": "ws_abc123",
  "content": "Hello, I need help"
}
```
