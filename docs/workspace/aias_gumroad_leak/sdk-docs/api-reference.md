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

### Requirements

You must have the corresponding provider API key configured in your dashboard to use a model:

```json
{
  "error": {
    "code": "PROVIDER_NOT_CONFIGURED",
    "message": "No API key configured for openai. Model 'gpt-4o' requires an OpenAI API key."
  }
}
```

---

## HTTP Endpoints

### Workspaces

A workspace represents a single chat conversation session.

---

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

**Response:**
```json
{
  "workspace": {
    "id": "ws_abc123",
    "mode": "ai",
    "status": "active",
    "title": "Order Support",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  },
  "messages": [
    {
      "id": "msg_001",
      "role": "user",
      "content": "Hello, I need help with my order",
      "visible_to_client": true,
      "created_at": "2024-01-15T10:30:00Z"
    },
    {
      "id": "msg_002",
      "role": "ai",
      "content": "Hi! I'd be happy to help with your order. Could you please provide your order number?",
      "visible_to_client": true,
      "created_at": "2024-01-15T10:30:01Z",
      "metadata": {
        "model": "llama-3.3-70b-versatile",
        "tokens": 42
      }
    }
  ]
}
```

---

#### Get Workspace

Retrieve workspace details.

```http
GET /api/workspaces/{workspace_id}
```

**Response:**
```json
{
  "workspace": {
    "id": "ws_abc123",
    "mode": "ai",
    "status": "active",
    "title": "Order Support",
    "contact_id": "contact_456",
    "assigned_to": null,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:35:00Z"
  }
}
```

---

#### List Workspaces (Admin)

List all workspaces. Requires manager/admin role.

```http
GET /api/workspaces?active_only=true
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `active_only` | boolean | `true` | Only return active workspaces |
| `limit` | integer | `50` | Max results to return |
| `offset` | integer | `0` | Pagination offset |
| `mode` | string | - | Filter by mode: `ai`, `takeover` |

**Response:**
```json
{
  "workspaces": [
    {
      "id": "ws_abc123",
      "mode": "ai",
      "status": "active",
      "title": "Order Support",
      "updated_at": "2024-01-15T10:35:00Z"
    },
    {
      "id": "ws_def456",
      "mode": "takeover",
      "status": "active",
      "title": "Billing Issue",
      "updated_at": "2024-01-15T10:32:00Z"
    }
  ],
  "total": 42,
  "limit": 50,
  "offset": 0
}
```

---

#### Update Workspace (Admin)

Change workspace mode or status. Requires manager/admin role.

```http
PATCH /api/workspaces/{workspace_id}
```

**Request Body:**
```json
{
  "mode": "takeover",
  "assigned_to": "admin_789"
}
```

**Mode Values:**
| Mode | Description |
|------|-------------|
| `ai` | AI handles all responses |
| `takeover` | Human takes over, AI paused |
| `shadow` | AI drafts, human approves (future) |

**Response:**
```json
{
  "workspace": {
    "id": "ws_abc123",
    "mode": "takeover",
    "status": "active",
    "assigned_to": "admin_789",
    "updated_at": "2024-01-15T10:40:00Z"
  }
}
```

---

### Messages

---

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

**Response:**
```json
{
  "user_message": {
    "id": "msg_003",
    "role": "user",
    "content": "My order number is #12345",
    "visible_to_client": true,
    "created_at": "2024-01-15T10:31:00Z"
  },
  "responses": [
    {
      "id": "msg_004",
      "role": "ai",
      "content": "Thank you! I found order #12345. It was shipped yesterday and should arrive by Friday.",
      "visible_to_client": true,
      "created_at": "2024-01-15T10:31:02Z",
      "metadata": {
        "model": "llama-3.3-70b-versatile"
      }
    }
  ],
  "mode": "ai"
}
```

**Note:** If workspace is in `takeover` mode, no AI response is generated. The `responses` array will be empty.

---

#### Get Messages

Retrieve all messages in a workspace.

```http
GET /api/workspaces/{workspace_id}/messages
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | `100` | Max messages to return |
| `after` | string | - | Return messages after this message ID |
| `include_hidden` | boolean | `false` | Include admin-only messages (requires admin) |

**Response:**
```json
{
  "messages": [
    {
      "id": "msg_001",
      "role": "user",
      "content": "Hello, I need help",
      "visible_to_client": true,
      "created_at": "2024-01-15T10:30:00Z"
    },
    {
      "id": "msg_002",
      "role": "ai",
      "content": "Hi! How can I help you today?",
      "visible_to_client": true,
      "created_at": "2024-01-15T10:30:01Z"
    }
  ]
}
```

---

#### Send Admin Message (Admin)

Send a message as the AI (human impersonation). Requires manager/admin role.

```http
POST /api/workspaces/{workspace_id}/admin-message
```

**Request Body:**
```json
{
  "content": "I've processed your refund. You'll see it in 3-5 business days.",
  "visible_to_client": true
}
```

**Response:**
```json
{
  "message": {
    "id": "msg_005",
    "role": "manager",
    "content": "I've processed your refund. You'll see it in 3-5 business days.",
    "visible_to_client": true,
    "created_at": "2024-01-15T10:45:00Z",
    "metadata": {
      "sent_by": "admin_789",
      "display_as": "ai"
    }
  }
}
```

**Note:** To customers, this appears as an AI message. The `role: "manager"` is only visible to admins.

---

### Typing Preview

Real-time visibility into what customers are typing.

---

#### Get Typing Preview (Admin)

Get current typing state for a workspace.

```http
GET /api/workspaces/{workspace_id}/typing
```

**Response:**
```json
{
  "workspace_id": "ws_abc123",
  "text": "I'm having trouble with my pa",
  "is_typing": true
}
```

**Note:** Preview text expires after 15 seconds of inactivity.

---

#### Update Typing Preview

Called by client widget as user types. Throttle to max 3-4 calls/second.

```http
POST /api/workspaces/{workspace_id}/typing
```

**Request Body:**
```json
{
  "text": "I'm having trouble with my payment"
}
```

**Response:**
```json
{
  "ok": true
}
```

---

### Directives

Inject real-time instructions into AI behavior.

---

#### List Directives (Admin)

Get all directives for a workspace.

```http
GET /api/workspaces/{workspace_id}/directives
```

**Response:**
```json
{
  "directives": [
    {
      "id": "dir_001",
      "content": "Customer is a VIP. Be extra helpful.",
      "type": "context",
      "is_active": true,
      "priority": 50,
      "created_at": "2024-01-15T10:35:00Z"
    }
  ]
}
```

---

#### Add Directive (Admin)

Inject a new directive into the conversation.

```http
POST /api/workspaces/{workspace_id}/directives
```

**Request Body:**
```json
{
  "content": "Offer 10% discount if customer mentions price concerns",
  "type": "guidance"
}
```

**Directive Types:**
| Type | Priority | Description |
|------|----------|-------------|
| `system` | 100 | Core behavior rules (highest priority) |
| `context` | 50 | Background information about customer/situation |
| `tone` | 30 | Communication style adjustments |
| `guidance` | 10 | Soft suggestions for AI behavior |

**Response:**
```json
{
  "directive": {
    "id": "dir_002",
    "content": "Offer 10% discount if customer mentions price concerns",
    "type": "guidance",
    "is_active": true,
    "created_at": "2024-01-15T10:40:00Z"
  }
}
```

---

### Authentication

---

#### Login

Authenticate and get session token.

```http
POST /api/auth/login
```

**Request Body:**
```json
{
  "email": "admin@example.com",
  "password": "securepassword"
}
```

**Response:**
```json
{
  "user": {
    "id": "usr_123",
    "email": "admin@example.com",
    "role": "manager",
    "plan": "pro"
  },
  "token": "session_token_here"
}
```

**Note:** Session token is also set as HTTP-only cookie.

---

#### Get Current User

Get authenticated user details.

```http
GET /api/auth/me
```

**Response:**
```json
{
  "user": {
    "id": "usr_123",
    "email": "admin@example.com",
    "role": "manager",
    "plan": "pro",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

---

#### Logout

End session.

```http
POST /api/auth/logout
```

**Response:**
```json
{
  "ok": true
}
```

---

## WebSocket API

Real-time communication for live updates. Uses Socket.IO protocol.

**Endpoint:** `wss://api.aiassist.net/socket.io`

### Client Namespace (`/client`)

For customer-facing chat widgets.

---

#### Events: Client → Server

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

**`typing_preview`**
```json
{
  "workspace_id": "ws_abc123",
  "text": "I'm typing this..."
}
```

**`typing_start`**
```json
{
  "workspace_id": "ws_abc123"
}
```

**`typing_stop`**
```json
{
  "workspace_id": "ws_abc123"
}
```

---

#### Events: Server → Client

**`message_new`**
```json
{
  "message": {
    "id": "msg_001",
    "role": "ai",
    "content": "How can I help?",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

**`typing_indicator`**
```json
{
  "is_typing": true
}
```

**`workspace_update`**
```json
{
  "workspace": {
    "id": "ws_abc123",
    "mode": "takeover"
  }
}
```

---

### Admin Namespace (`/admin`)

For admin dashboard real-time updates.

---

#### Events: Admin → Server

**`subscribe_dashboard`**
```json
{}
```

**`subscribe_workspace`**
```json
{
  "workspace_id": "ws_abc123"
}
```

**`unsubscribe_workspace`**
```json
{
  "workspace_id": "ws_abc123"
}
```

**`send_as_ai`**
```json
{
  "workspace_id": "ws_abc123",
  "content": "I've processed your request.",
  "user_id": "admin_789"
}
```

**`change_mode`**
```json
{
  "workspace_id": "ws_abc123",
  "mode": "takeover",
  "user_id": "admin_789"
}
```

**`inject_directive`**
```json
{
  "workspace_id": "ws_abc123",
  "content": "Be more concise",
  "type": "tone",
  "user_id": "admin_789"
}
```

---

#### Events: Server → Admin

**`workspace_list`**
```json
{
  "workspaces": [...]
}
```

**`workspace_update`**
```json
{
  "workspace": {
    "id": "ws_abc123",
    "mode": "takeover"
  }
}
```

**`message_new`**
```json
{
  "workspace_id": "ws_abc123",
  "message": {
    "id": "msg_001",
    "role": "user",
    "content": "Help please"
  }
}
```

**`client_typing`**
```json
{
  "workspace_id": "ws_abc123",
  "is_typing": true
}
```

**`typing_preview`**
```json
{
  "workspace_id": "ws_abc123",
  "text": "Customer is typing this...",
  "is_typing": true
}
```

**`client_presence`**
```json
{
  "workspace_id": "ws_abc123",
  "online": true
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "You have exceeded your monthly conversation limit",
    "details": {
      "limit": 100,
      "used": 100,
      "resets_at": "2024-02-01T00:00:00Z"
    }
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Missing or invalid API key |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `RATE_LIMIT_EXCEEDED` | 429 | Rate limit exceeded |
| `PLAN_LIMIT_EXCEEDED` | 429 | Monthly plan limit reached |
| `INVALID_REQUEST` | 400 | Malformed request body |
| `WORKSPACE_CLOSED` | 400 | Workspace is no longer active |
| `AI_ERROR` | 500 | AI generation failed |
| `INTERNAL_ERROR` | 500 | Unexpected server error |

---

## Rate Limits

| Plan | Requests/min | Conversations/mo | Tokens/min |
|------|--------------|------------------|------------|
| Free | 20 | 100 | 10,000 |
| Pro | 100 | 5,000 | 100,000 |
| Business | 500 | 25,000 | 500,000 |
| Enterprise | Custom | Unlimited | Custom |

Rate limit headers are included in all responses:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1705320000
```

---

## Webhooks

Configure webhook URL in dashboard to receive real-time events.

### Event Types

| Event | Description |
|-------|-------------|
| `conversation.started` | New workspace created |
| `conversation.ended` | Workspace closed |
| `message.created` | New message (user or AI) |
| `mode.changed` | Workspace mode switched |
| `takeover.started` | Human took over |
| `takeover.ended` | Returned to AI mode |

### Webhook Payload

```json
{
  "id": "evt_abc123",
  "event": "message.created",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "workspace_id": "ws_abc123",
    "message": {
      "id": "msg_001",
      "role": "user",
      "content": "Hello"
    }
  }
}
```

### Signature Verification

Webhooks include an HMAC signature for verification:

```http
X-AiAssist-Signature: sha256=abc123...
```

```python
import hmac
import hashlib

def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

---

## SDK Examples

### JavaScript (Fetch)

```javascript
const API_KEY = 'your_api_key';
const BASE_URL = 'https://api.aiassist.net';

// Create workspace
const response = await fetch(`${BASE_URL}/api/workspaces`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': API_KEY
  },
  body: JSON.stringify({
    initial_message: 'Hello, I need help'
  })
});

const { workspace, messages } = await response.json();
```

### Python (Requests)

```python
import requests

API_KEY = 'your_api_key'
BASE_URL = 'https://api.aiassist.net'

# Create workspace
response = requests.post(
    f'{BASE_URL}/api/workspaces',
    headers={'X-API-Key': API_KEY},
    json={'initial_message': 'Hello, I need help'}
)

data = response.json()
workspace = data['workspace']
messages = data['messages']
```

### cURL

```bash
curl -X POST https://api.aiassist.net/api/workspaces \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key" \
  -d '{"initial_message": "Hello, I need help"}'
```
