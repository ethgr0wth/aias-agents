# AiAssist Secure — Developer Documentation

> Build AI-powered applications with the AiAssist Secure API

## Overview

AiAssist Secure provides a comprehensive API for integrating AI capabilities into your applications. The platform offers:

- **OpenAI-compatible chat completions API** for easy integration
- **Multi-provider support** (Groq, OpenAI, Anthropic, Gemini, Mistral)
- **BYOK (Bring Your Own Key)** architecture for flexible provider management
- **Deployed Agents** for customized AI assistants
- **Knowledge Base** for RAG-style context injection
- **Conversation Memory** for context-aware interactions
- **Real-time chat** via WebSocket

---

## Quick Start

### 1. Get Your API Key

1. Log into your AiAssist Secure dashboard
2. Navigate to **API Keys** section
3. Click **Generate New Key**
4. Copy your key (format: `aai_xxxxxxxxxxxxxxxx`)

### 2. Make Your First Request

```bash
curl -X POST https://your-domain.com/v1/chat/completions \
  -H "Authorization: Bearer aai_your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-3.3-70b-versatile",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Hello!"}
    ],
    "temperature": 0.7,
    "max_tokens": 1024
  }'
```

### 3. Response Format

```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1704067200,
  "model": "llama-3.3-70b-versatile",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How can I help you today?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 10,
    "total_tokens": 35
  }
}
```

---

## Authentication

All API requests require authentication via Bearer token.

### API Key Authentication

```
Authorization: Bearer aai_your_api_key
```

API keys are prefixed with `aai_` and can be generated in your dashboard. Keys can have:
- **Usage limits** (tokens per day/month)
- **Provider restrictions** (limit to specific AI providers)
- **Rate limits** (requests per minute)

### Session Authentication (Internal APIs)

Internal dashboard APIs use cookie-based session authentication. Sessions are HTTP-only cookies with 7-day expiration.

---

## Public API Reference

Base URL: `/v1`

### Chat Completions

**POST** `/v1/chat/completions`

Create an AI chat completion. OpenAI-compatible endpoint.

#### Request Body

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `model` | string | No | Model ID (default: user's configured default) |
| `messages` | array | Yes | Array of message objects |
| `temperature` | number | No | Sampling temperature (0-2, default: 0.7) |
| `max_tokens` | number | No | Maximum tokens to generate |
| `stream` | boolean | No | Enable streaming responses |

#### Message Object

| Field | Type | Description |
|-------|------|-------------|
| `role` | string | `system`, `user`, or `assistant` |
| `content` | string | Message content |

#### Headers

| Header | Description |
|--------|-------------|
| `Authorization` | Required. Bearer token with API key |
| `X-AiAssist-Provider` | Optional. Override provider (groq, openai, anthropic, gemini, mistral) |

#### Example

```javascript
const response = await fetch('https://your-domain.com/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer aai_your_api_key',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    model: 'gpt-4o',
    messages: [
      { role: 'user', content: 'Explain quantum computing in simple terms' }
    ],
    max_tokens: 500
  })
});

const data = await response.json();
console.log(data.choices[0].message.content);
```

---

### List Models

**GET** `/v1/models`

Returns available models for the authenticated user.

#### Response

```json
{
  "object": "list",
  "data": [
    {
      "id": "llama-3.3-70b-versatile",
      "name": "Llama 3.3 70B",
      "context_window": 128000,
      "max_output": 32768
    },
    {
      "id": "gpt-4o",
      "name": "GPT-4o",
      "context_window": 128000,
      "max_output": 4096
    }
  ]
}
```

---

### Check Usage

**GET** `/v1/usage`

Returns current API usage statistics.

#### Response

```json
{
  "requests_today": 150,
  "tokens_today": 45000,
  "requests_this_month": 3200,
  "tokens_this_month": 1200000
}
```

---

### Health Check

**GET** `/v1/health`

Returns API health status. No authentication required.

---

### Provider Info

**GET** `/v1/provider`

Returns the current provider configuration for the API key.

---

### Check Availability

**GET** `/v1/availability`

Check if the API is available and the key is valid.

---

## Supported Providers (11 Total)

AiAssist Secure supports **11 LLM providers** via BYOK (Bring Your Own Key):

| Provider | ID | Console URL |
|----------|-----|-------------|
| Groq | `groq` | console.groq.com/keys |
| OpenAI | `openai` | platform.openai.com/api-keys |
| Anthropic | `anthropic` | console.anthropic.com |
| Google Gemini | `gemini` | aistudio.google.com/apikey |
| Mistral AI | `mistral` | console.mistral.ai/api-keys |
| xAI (Grok) | `xai` | console.x.ai |
| Together AI | `together` | api.together.xyz/settings/api-keys |
| OpenRouter | `openrouter` | openrouter.ai/keys |
| DeepSeek | `deepseek` | platform.deepseek.com/api_keys |
| Fireworks AI | `fireworks` | fireworks.ai/api-keys |
| Perplexity | `perplexity` | perplexity.ai/settings/api |

---

## Supported Models

### Groq (Default)
- `llama-3.3-70b-versatile` — Llama 3.3 70B (recommended)
- `llama-3.1-8b-instant` — Llama 3.1 8B (fast)
- `llama-3.1-70b-versatile` — Llama 3.1 70B
- `qwen-qwq-32b` — Qwen QwQ 32B
- `deepseek-r1-distill-llama-70b` — DeepSeek R1 Distill 70B
- `mixtral-8x7b-32768` — Mixtral 8x7B
- `llama3-groq-70b-8192-tool-use-preview` — Llama 3 70B Tool Use

### OpenAI
- `gpt-4o` — GPT-4o (recommended)
- `gpt-4o-mini` — GPT-4o Mini (fast/cheap)
- `gpt-4.1` — GPT-4.1
- `gpt-4.1-mini` — GPT-4.1 Mini
- `gpt-4.1-nano` — GPT-4.1 Nano

### Anthropic
- `claude-3-5-sonnet-20241022` — Claude 3.5 Sonnet (recommended)
- `claude-3-opus-20240229` — Claude 3 Opus
- `claude-3-haiku-20240307` — Claude 3 Haiku (fast)

### Google Gemini
- `gemini-2.0-flash` — Gemini 2.0 Flash
- `gemini-1.5-pro` — Gemini 1.5 Pro
- `gemini-1.5-flash` — Gemini 1.5 Flash

### Mistral AI
- `mistral-large-latest` — Mistral Large
- `mistral-medium-latest` — Mistral Medium
- `mistral-small-latest` — Mistral Small
- `codestral-latest` — Codestral (code-focused)

### xAI (Grok)
- `grok-2` — Grok 2
- `grok-2-mini` — Grok 2 Mini
- `grok-beta` — Grok Beta

### Together AI
- `meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo` — Llama 3.1 405B
- `meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo` — Llama 3.1 70B
- `mistralai/Mixtral-8x22B-Instruct-v0.1` — Mixtral 8x22B
- `Qwen/Qwen2-72B-Instruct` — Qwen 2 72B

### OpenRouter
Access 100+ models through a single API:
- `anthropic/claude-3.5-sonnet`
- `openai/gpt-4o`
- `google/gemini-pro-1.5`
- `meta-llama/llama-3.1-405b-instruct`
- And many more...

### DeepSeek
- `deepseek-chat` — DeepSeek Chat
- `deepseek-coder` — DeepSeek Coder
- `deepseek-reasoner` — DeepSeek Reasoner

### Fireworks AI
- `accounts/fireworks/models/llama-v3p1-405b-instruct` — Llama 3.1 405B
- `accounts/fireworks/models/llama-v3p1-70b-instruct` — Llama 3.1 70B
- `accounts/fireworks/models/mixtral-8x22b-instruct` — Mixtral 8x22B
- `accounts/fireworks/models/qwen2-72b-instruct` — Qwen 2 72B

### Perplexity
- `sonar-pro` — Sonar Pro (with web search)
- `sonar` — Sonar
- `sonar-reasoning` — Sonar Reasoning
- `sonar-deep-research` — Sonar Deep Research

---

## Private API Reference

These endpoints require session authentication (logged-in users).

Base URL: `/api`

---

### Authentication

#### Login

**POST** `/api/auth/login`

```json
{
  "email": "user@example.com",
  "password": "your_password"
}
```

#### Logout

**POST** `/api/auth/logout`

#### Get Current User

**GET** `/api/auth/me`

Returns the authenticated user's profile.

#### Register

**POST** `/api/auth/register`

```json
{
  "email": "user@example.com",
  "password": "your_password",
  "display_name": "John Doe"
}
```

#### Two-Factor Authentication

- **POST** `/api/auth/verify-2fa` — Verify 2FA code during login

---

### User Management

#### Get Profile

**GET** `/api/user/me`

#### Update Profile

**PUT** `/api/user/profile`

```json
{
  "display_name": "New Name",
  "email": "newemail@example.com"
}
```

#### Change Password

**PUT** `/api/user/password`

```json
{
  "current_password": "old_password",
  "new_password": "new_password"
}
```

---

### API Keys

#### List API Keys

**GET** `/api/user/api-keys`

#### Create API Key

**POST** `/api/user/api-keys`

```json
{
  "name": "My App Key",
  "description": "Key for my mobile app"
}
```

#### Delete API Key

**DELETE** `/api/user/api-keys/{key_id}`

#### Extended API Keys (with usage limits)

- **GET** `/api/user/api-keys-extended` — List all extended keys
- **POST** `/api/user/api-keys-extended` — Create extended key
- **DELETE** `/api/user/api-keys-extended/{key_id}` — Delete key
- **GET** `/api/user/api-keys-extended/{key_id}/usage` — Get usage stats
- **GET** `/api/user/api-keys-extended/{key_id}/usage-stats` — Detailed stats
- **GET** `/api/user/api-keys-extended/{key_id}/usage-limits` — Get limits
- **PUT** `/api/user/api-keys-extended/{key_id}/usage-limits` — Set limits

---

### Provider Configuration (BYOK)

#### Get Groq Configuration

**GET** `/api/user/providers/groq`

#### Save Groq API Key

**POST** `/api/user/providers/groq`

```json
{
  "api_key": "gsk_xxxxxxxxxxxxxxxx"
}
```

#### Delete Provider

**DELETE** `/api/user/providers/groq`

---

### Workspaces

Workspaces are conversation containers for AI interactions.

#### List Workspaces

**GET** `/api/user/workspaces`

#### Create Workspace

**POST** `/api/workspaces`

```json
{
  "name": "Customer Support Bot",
  "client_id": "optional_client_reference"
}
```

#### Get Workspace

**GET** `/api/workspaces/{workspace_id}`

#### Update Workspace

**PATCH** `/api/workspaces/{workspace_id}`

```json
{
  "name": "Updated Name",
  "mode": "ai"
}
```

#### Workspace Modes

- `ai` — Fully autonomous AI responses
- `shadow` — AI drafts, human approves
- `takeover` — Human control only

---

### Messages

#### Get Workspace Messages

**GET** `/api/workspaces/{workspace_id}/messages`

Query params:
- `limit` — Number of messages (default: 50)
- `before` — Pagination cursor

#### Send Message

**POST** `/api/workspaces/{workspace_id}/messages`

```json
{
  "content": "Hello, I need help with my order",
  "role": "user"
}
```

#### Clear Messages

**DELETE** `/api/workspaces/{workspace_id}/messages`

---

### Shadow Mode (Draft Approval)

For workspaces in `shadow` mode, AI responses require human approval.

#### Get Pending Drafts

**GET** `/api/workspaces/drafts/pending`

#### Approve Draft

**POST** `/api/workspaces/drafts/{draft_id}/approve`

```json
{
  "edited_content": "Optional: modified response text"
}
```

#### Reject Draft

**POST** `/api/workspaces/drafts/{draft_id}/reject`

```json
{
  "reason": "Response was inaccurate"
}
```

#### Regenerate Draft

**POST** `/api/workspaces/drafts/{draft_id}/regenerate`

```json
{
  "directive": "Make the response more concise"
}
```

---

### Knowledge Base (Training Contexts)

Store custom knowledge for AI context injection.

#### List Contexts

**GET** `/api/user/training-contexts`

#### Create Context

**POST** `/api/user/training-contexts`

```json
{
  "title": "Company Information",
  "content": "Our company was founded in 2020...",
  "category": "company"
}
```

#### Update Context

**PUT** `/api/user/training-contexts/{ctx_id}`

#### Delete Context

**DELETE** `/api/user/training-contexts/{ctx_id}`

---

### AI Directives

Customize AI behavior with directives.

#### List Directives

**GET** `/api/directives`

#### Create Directive

**POST** `/api/directives`

```json
{
  "directive_type": "persona",
  "content": "You are a friendly customer service agent named Alex",
  "active": true,
  "priority": 1
}
```

#### Directive Types

- `persona` — Define AI personality/role
- `constraint` — Add behavioral constraints
- `style` — Response style guidelines
- `knowledge` — Inject specific knowledge

#### Update Directive

**PATCH** `/api/directives/{directive_id}`

#### Delete Directive

**DELETE** `/api/directives/{directive_id}`

---

### Deployed Agents

Create and manage deployable AI agents.

#### List Agents

**GET** `/api/deployed-agents`

#### Create Agent

**POST** `/api/deployed-agents`

```json
{
  "name": "Support Bot",
  "persona": "You are a helpful support agent",
  "model": "llama-3.3-70b-versatile",
  "temperature": 0.7,
  "inherit_global_directives": true,
  "inherit_global_kb": true
}
```

#### Activate Agent

**POST** `/api/deployed-agents/{agent_id}/activate`

#### Deactivate All

**POST** `/api/deployed-agents/deactivate`

#### Redeploy Agent

**POST** `/api/deployed-agents/{agent_id}/redeploy`

#### Archive Agent

**POST** `/api/deployed-agents/{agent_id}/archive`

---

### Contacts (CRM)

Manage customer contacts.

#### List Contacts

**GET** `/api/contacts`

#### Create Contact

**POST** `/api/contacts`

```json
{
  "email": "customer@example.com",
  "name": "Jane Doe",
  "phone": "+1234567890",
  "company": "Acme Inc"
}
```

#### Update Contact

**PATCH** `/api/contacts/{contact_id}`

#### Update Lifecycle

**PATCH** `/api/contacts/{contact_id}/lifecycle`

```json
{
  "lifecycle_stage": "customer"
}
```

---

### Leads

Track and manage leads from embedded widgets.

#### List Leads

**GET** `/api/leads`

#### Get Lead

**GET** `/api/leads/{lead_id}`

#### Update Lead

**PATCH** `/api/leads/{lead_id}`

#### Convert Lead to Contact

**POST** `/api/leads/{lead_id}/convert`

---

### Subscriptions

#### Get Subscription Status

**GET** `/api/subscription/status`

#### Activate Subscription

**POST** `/api/subscription/activate`

```json
{
  "license_key": "XXXX-XXXX-XXXX-XXXX"
}
```

#### Cancel Subscription

**POST** `/api/subscription/cancel`

#### Reactivate Subscription

**POST** `/api/subscription/reactivate`

#### Get Subscription History

**GET** `/api/subscription/history`

---

### Licenses

#### Activate License

**POST** `/api/licenses/activate`

```json
{
  "license_key": "XXXX-XXXX-XXXX-XXXX"
}
```

#### Get My License

**GET** `/api/licenses/me`

#### Validate License

**GET** `/api/licenses/v2/validate/{license_key}`

#### Get License Hierarchy

**GET** `/api/licenses/v2/hierarchy`

---

### Billing

#### Get Seat Pricing

**GET** `/api/billing/seat-pricing`

#### Create Checkout Session

**POST** `/api/billing/checkout`

```json
{
  "plan_id": "team",
  "seats": 5,
  "billing_cycle": "monthly"
}
```

#### Upgrade Seats

**POST** `/api/billing/upgrade-seats`

```json
{
  "additional_seats": 3
}
```

---

### Organizations

#### Get My Organization

**GET** `/api/organizations/me`

#### Get Organization Members

**GET** `/api/organizations/my/members`

#### Get Organization Seats

**GET** `/api/organizations/my/seats`

---

### Memory Settings

#### Get Workspace Memory Settings

**GET** `/api/memory/workspaces/{workspace_id}/settings/memory`

#### Update Memory Settings

**PATCH** `/api/memory/workspaces/{workspace_id}/settings/memory`

```json
{
  "conversation_memory_enabled": true
}
```

#### Export Session Memory

**GET** `/api/memory/user/sessions/{session_id}/export`

---

### App Builder (Quests)

Build apps with AI assistance.

#### List Environments

**GET** `/api/quests/environments`

#### Create Environment

**POST** `/api/quests/environments`

```json
{
  "name": "My React App",
  "description": "A simple todo app",
  "template_id": "react"
}
```

#### File Operations

- **GET** `/api/quests/environments/{env_id}/files/tree` — Get file tree
- **GET** `/api/quests/environments/{env_id}/files/read?path=src/App.js` — Read file
- **POST** `/api/quests/environments/{env_id}/files/write` — Write file
- **POST** `/api/quests/environments/{env_id}/files/mkdir` — Create directory
- **DELETE** `/api/quests/environments/{env_id}/files/delete?path=file.txt` — Delete file
- **POST** `/api/quests/environments/{env_id}/files/rename` — Rename file

#### Chat with AI

**POST** `/api/quests/environments/{env_id}/chat`

```json
{
  "message": "Create a login form with email and password fields"
}
```

#### Download Project

**GET** `/api/quests/environments/{env_id}/files/download-all`

Returns a ZIP file of the entire project.

#### Templates

**GET** `/api/quests/templates`

Available templates: `blank`, `react`, `nextjs`, `express`, `fastapi`

---

### Voice Actions

AI voice synthesis and actions.

#### Text-to-Speech

**POST** `/api/voice/speak`

```json
{
  "text": "Hello, how can I help you?",
  "voice": "en-US-Wavenet-D"
}
```

#### Explain Content

**POST** `/api/voice/explain`

#### Summarize Content

**POST** `/api/voice/summarize`

---

## Webhooks

### Stripe Webhook

**POST** `/api/webhooks/stripe`

Handles Stripe payment events:
- `checkout.session.completed`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.paid`
- `invoice.payment_failed`

---

## Rate Limits

| Plan | Requests/min | Tokens/day |
|------|--------------|------------|
| Free | 10 | 10,000 |
| Basic | 60 | 100,000 |
| Pro | 120 | 500,000 |
| Enterprise | Unlimited | Unlimited |

Rate limit headers included in responses:
- `X-RateLimit-Limit`
- `X-RateLimit-Remaining`
- `X-RateLimit-Reset`

---

## Error Handling

### Error Response Format

```json
{
  "detail": "Error message here"
}
```

### Common HTTP Status Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request — Invalid parameters |
| 401 | Unauthorized — Invalid or missing API key |
| 402 | Payment Required — Subscription inactive |
| 403 | Forbidden — Insufficient permissions |
| 404 | Not Found — Resource doesn't exist |
| 429 | Too Many Requests — Rate limit exceeded |
| 500 | Internal Server Error |

---

## WebSocket API

Real-time communication for chat interfaces.

### Connection

```javascript
import { io } from 'socket.io-client';

const socket = io('https://your-domain.com', {
  path: '/socket.io',
  auth: {
    token: 'session_token'
  }
});
```

### Events

#### Client → Server

- `join_workspace` — Join a workspace room
- `send_message` — Send a chat message
- `typing_start` — User started typing
- `typing_stop` — User stopped typing

#### Server → Client

- `new_message` — New message received
- `draft_created` — AI draft ready for approval
- `draft_approved` — Draft was approved
- `draft_rejected` — Draft was rejected
- `typing_indicator` — Someone is typing

---

## SDK Examples

### Python

```python
import requests

API_KEY = "aai_your_api_key"
BASE_URL = "https://your-domain.com/v1"

def chat(message: str, model: str = "llama-3.3-70b-versatile"):
    response = requests.post(
        f"{BASE_URL}/chat/completions",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": model,
            "messages": [{"role": "user", "content": message}]
        }
    )
    return response.json()["choices"][0]["message"]["content"]

print(chat("What is the capital of France?"))
```

### JavaScript/TypeScript

```typescript
const API_KEY = 'aai_your_api_key';
const BASE_URL = 'https://your-domain.com/v1';

async function chat(message: string, model = 'llama-3.3-70b-versatile') {
  const response = await fetch(`${BASE_URL}/chat/completions`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      model,
      messages: [{ role: 'user', content: message }]
    })
  });
  
  const data = await response.json();
  return data.choices[0].message.content;
}

chat('Explain machine learning').then(console.log);
```

### OpenAI SDK Compatible

```python
from openai import OpenAI

client = OpenAI(
    api_key="aai_your_api_key",
    base_url="https://your-domain.com/v1"
)

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)

print(response.choices[0].message.content)
```

---

## Best Practices

### 1. Use System Messages

Always include a system message to set context:

```json
{
  "messages": [
    {"role": "system", "content": "You are a helpful assistant for a SaaS company."},
    {"role": "user", "content": "How do I reset my password?"}
  ]
}
```

### 2. Handle Rate Limits

```python
import time

def chat_with_retry(message, max_retries=3):
    for attempt in range(max_retries):
        response = chat(message)
        if response.status_code == 429:
            wait_time = int(response.headers.get('X-RateLimit-Reset', 60))
            time.sleep(wait_time)
            continue
        return response
    raise Exception("Rate limit exceeded after retries")
```

### 3. Stream Long Responses

For better UX with long responses, use streaming:

```javascript
const response = await fetch('/v1/chat/completions', {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${API_KEY}` },
  body: JSON.stringify({
    model: 'llama-3.3-70b-versatile',
    messages: [{ role: 'user', content: 'Write a long story' }],
    stream: true
  })
});

const reader = response.body.getReader();
while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  console.log(new TextDecoder().decode(value));
}
```

### 4. Secure Your API Keys

- Never expose API keys in client-side code
- Use environment variables
- Rotate keys periodically
- Set usage limits per key

---

## Support

- **Documentation**: This file
- **Dashboard**: https://your-domain.com/dashboard
- **Email**: support@your-domain.com

---

*Last updated: January 2026*
