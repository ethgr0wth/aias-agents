---
title: FAQ
icon: HelpCircle
description: Common questions answered
category: Business
order: 6
---

## General Questions

### What is BYOK (Bring Your Own Key)?

BYOK means you use your own API keys from providers like OpenAI, Anthropic, and Groq. AiAS never touches your inference costs — you pay providers directly at their published rates. We only charge for the orchestration layer.

### Why use AiAS instead of calling providers directly?

Direct API calls work fine for simple use cases. AiAS adds value when you need:

- **Multi-provider support** — Switch models without code changes
- **Key management** — Encrypted vault, instant rotation, team access
- **Failover** — Automatic backup when providers are slow/down
- **Analytics** — Track usage, costs, latency across all providers
- **Team features** — Audit logs, quotas, role-based access

---

## Security

### How are my API keys protected?

Keys are encrypted at rest using AES-256 encryption. They are:

- Never logged in our systems
- Never included in API responses
- Never accessible to our staff
- Rotatable instantly from your dashboard
- Revocable with one click

### Where is my data stored?

Conversation data is stored in your workspace using encrypted storage. You have full control:

- Export data at any time
- Delete individual conversations or entire workspaces
- Configure retention policies
- Enable/disable conversation storage entirely

### Do you use my data for training?

**No.** We do not use your conversations, prompts, or responses to train any models. Your data is your data.

---

## Performance

### Does AiAS add latency?

Minimal. AiAS adds approximately 20-50ms for routing and key decryption. We run on edge infrastructure close to major LLM provider regions to minimize overhead.

### Is there rate limiting?

AiAS doesn't impose additional rate limits beyond what your providers allow. We respect and pass through provider rate limits. If you hit OpenAI's rate limit, you'll see their error — we don't mask it.

### Do you support streaming?

Yes. Full Server-Sent Events (SSE) streaming support for all providers. Both our React SDK and Core SDK handle streaming out of the box with proper backpressure handling.

---

## Providers

### Can I use self-hosted models?

Yes. Add your Ollama, vLLM, LocalAI, or any OpenAI-compatible endpoint as a custom provider. AiAS routes to it like any other provider.

```yaml
custom_provider:
  name: "My Local LLM"
  endpoint: "http://localhost:11434/v1"
  api_key: "optional"
  models:
    - llama3:8b
    - mistral:7b
```

### What happens if a provider goes down?

AiAS supports automatic failover. Configure backup providers in your dashboard — if your primary (e.g., OpenAI) is slow or unavailable, we automatically route to your backup (e.g., Anthropic or Groq).

### Which providers are supported?

| Provider | Status | Notes |
|----------|--------|-------|
| OpenAI | ✓ Full | All models including GPT-4o |
| Anthropic | ✓ Full | Claude 3.5 Sonnet, Opus, Haiku |
| Groq | ✓ Full | Ultra-fast Llama, Mixtral |
| Mistral | ✓ Full | Mistral Large, Medium |
| Google | ✓ Full | Gemini Pro, Flash |
| Self-hosted | ✓ Full | Any OpenAI-compatible API |

---

## Billing

### How does pricing work?

AiAS charges a flat monthly fee for the control plane. Your inference costs go directly to providers — we never mark them up. See our [Pricing](/v2/pricing) page for current tiers.

### Can I see my usage?

Yes. Your dashboard shows:

- Real-time token usage by provider and model
- Cost estimates based on provider rates
- Latency percentiles (p50, p95, p99)
- Request volume over time
- Per-user breakdowns (Team tier)

### Is there a free tier?

Yes. The free tier includes:

- 1 workspace
- 1 API key
- Community support
- Basic analytics

No credit card required to start.

---

## Getting Started

### How do I start?

1. Sign up at [aiassist.net](https://aiassist.net)
2. Add your first API key (OpenAI, Anthropic, etc.)
3. Create a workspace
4. Start making API calls

### Where can I find documentation?

- [Architecture Overview](/v2/architecture)
- [Core Features](/v2/features)
- [SDK Examples](/core-sdk)
- [API Reference](https://docs.aiassist.net)

### How do I get support?

- **Free tier**: Community Discord
- **Pro tier**: Email support, 24-hour response
- **Team tier**: Priority email, 4-hour response
- **Enterprise**: Dedicated support channel, SLA
