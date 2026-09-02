---
title: System Architecture
icon: Blocks
description: BYOK control plane design
category: Getting Started
order: 1
---

## Platform Overview

AiAS operates as a **BYOK Control Plane** — you bring your LLM provider API keys, we handle routing, failover, analytics, and team management.

> "Your keys, your costs, our infrastructure."

---

## System Diagram

```
┌─────────────────────────────────────────────────┐
│  Your Application                               │
│  WhiteGlove • Chat UI • API Client • Agents     │
└───────────────────────┬─────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────┐
│  AiAS Control Plane                             │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐  │
│  │ Key Vault  │ │  Router    │ │ Analytics  │  │
│  │ AES-256    │ │ Failover   │ │ Real-time  │  │
│  └────────────┘ └────────────┘ └────────────┘  │
└───────────────────────┬─────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────┐
│  LLM Providers (YOUR keys, YOUR accounts)       │
│  OpenAI • Anthropic • Groq • Mistral • Ollama   │
└─────────────────────────────────────────────────┘
```

---

## Core Principles

### Zero Markup on Inference

AiAS never touches your inference costs. When you use GPT-4o, you pay OpenAI directly at their published rate. No hidden fees, no token markup.

### Unified API Surface

One API endpoint, multiple providers. Our OpenAI-compatible format means you can switch between GPT-4 and Claude with a single parameter change:

```javascript
// Switch providers with one line
const response = await aias.chat({
  model: "claude-3-5-sonnet", // or "gpt-4o"
  messages: [{ role: "user", content: "Hello!" }]
})
```

### Security by Default

Keys are encrypted at rest using AES-256. They're never logged, never included in responses, and can be rotated instantly from your dashboard.

---

## Supported Providers

| Provider | Models | Streaming | Function Calling |
|----------|--------|-----------|------------------|
| **OpenAI** | GPT-4o, GPT-4 Turbo, GPT-3.5 | ✓ | ✓ |
| **Anthropic** | Claude 3.5 Sonnet, Claude 3 Opus, Haiku | ✓ | ✓ |
| **Groq** | Llama 3.3 70B, Mixtral 8x7B | ✓ | ✓ |
| **Mistral** | Mistral Large, Mistral Medium | ✓ | ✓ |
| **Google** | Gemini Pro, Gemini Flash | ✓ | ✓ |
| **Self-hosted** | Ollama, vLLM, LocalAI | ✓ | Varies |

---

## Request Flow

1. **Your app** sends a chat completion request to AiAS
2. **Key retrieval** — we decrypt your stored API key for the target provider
3. **Routing** — request is sent to the appropriate provider endpoint
4. **Streaming** — response tokens stream back in real-time
5. **Metering** — usage is recorded for analytics (tokens, latency, cost)
6. **Failover** — if the provider fails, automatic retry to your backup

---

## Failover Configuration

Configure priority chains for automatic failover:

```yaml
failover_chain:
  primary: openai/gpt-4o
  fallbacks:
    - anthropic/claude-3-5-sonnet
    - groq/llama-3.3-70b
  
  triggers:
    - timeout: 30s
    - status_codes: [500, 502, 503]
    - rate_limited: true
```

When your primary provider is slow or unavailable, AiAS automatically routes to your next available option.

---

## Data Flow & Privacy

| Data Type | Storage | Retention | Your Control |
|-----------|---------|-----------|--------------|
| API Keys | Encrypted at rest | Until deleted | Rotate/revoke anytime |
| Conversations | Your workspace | Configurable | Export/delete anytime |
| Usage Metrics | Aggregated | 90 days | View in dashboard |
| Logs | Anonymized | 30 days | No PII stored |

**We do not train on your data.** Ever.
