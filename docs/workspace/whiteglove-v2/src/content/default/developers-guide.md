---
title: Developers Guide
icon: BookOpen
category: Developers
order: 1
description: Comprehensive guide for building with the Secure API.
---

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
