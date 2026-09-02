---
title: Platform Overview
icon: CircuitBoard
description: Complete AI chat SDK with human takeover.
category: Getting Started
order: 1
---

# AiAssist SDK

> Drop-in AI chat with seamless human takeover. Ship ChatGPT-quality conversations in minutes.

## What is AiAssist?

AiAssist is a complete live chat SDK that combines AI-powered responses with invisible human takeover. Your customers talk to AI, but when needed, your team can seamlessly step in - the customer never knows the difference.

**Perfect for:**
- SaaS products needing smart support
- E-commerce sites wanting AI-first sales chat
- Any app that needs both automation AND human touch

## Key Features

- **AI-First Chat** - Powered by Llama 3.3 70B via Groq for fast, intelligent responses
- **Invisible Human Takeover** - Admins can take control anytime, responses appear as AI
- **Live Typing Preview** - See what customers type before they send (admin only)
- **Real-Time Monitoring** - Dashboard to watch all conversations live
- **AI Directives** - Inject context, tone, or instructions on-the-fly
- **Beautiful UI** - Polished, animated components ready for production
- **Customizable** - Theming, branding, positioning - make it yours

## Packages

| Package | Description | Install |
|---------|-------------|---------|
| `@aiassist/react` | React components + hooks | `npm install @aiassist/react` |
| `@aiassist/vanilla` | Plain JS widget (also available via CDN) | `npm install @aiassist/vanilla` |
| `aiassist` | Python server SDK | `pip install aiassist` |

## Quick Start

### Option 1: React

```bash
npm install @aiassist/react
```

```tsx
import { AiAssistChat, AiAssistProvider } from '@aiassist/react';

function App() {
  return (
    <AiAssistProvider 
      apiKey="your-api-key"
      // Or use your own Groq key:
      // groqApiKey="your-groq-key"
    >
      <AiAssistChat />
    </AiAssistProvider>
  );
}
```

### Option 2: Vanilla JS / HTML

```html
<!-- Add to your HTML -->
<script src="https://cdn.aiassist.net/widget.js"></script>
<script>
  AiAssist.init({
    apiKey: 'your-api-key',
    position: 'bottom-right',
    theme: 'dark'
  });
</script>
```

### Option 3: Self-Hosted (Python Backend)

```bash
pip install aiassist
```

```python
from fastapi import FastAPI
from aiassist import AiAssistRouter, AiAssistConfig

app = FastAPI()

config = AiAssistConfig(
    groq_api_key="your-groq-key",
    redis_url="redis://localhost:6379"
)

app.include_router(AiAssistRouter(config))
```

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Your App      │     │  AiAssist SDK   │     │  Admin Panel    │
│  (React/HTML)   │────▶│   (Backend)     │◀────│  (Dashboard)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │   Groq / LLM    │
                        │   (AI Engine)   │
                        └─────────────────┘
```

**Deployment Options:**
1. **Managed** - Use our hosted backend, just drop in the widget
2. **Self-Hosted** - Run the Python SDK on your infrastructure
3. **Hybrid** - Use our AI proxy with your own database

## Pricing

| Plan | Conversations/mo | Features | Price |
|------|------------------|----------|-------|
| **Free** | 100 | AI chat, basic styling | $0 |
| **Pro** | 5,000 | Human takeover, typing preview, custom branding | $49/mo |
| **Business** | 25,000 | Analytics, webhooks, priority support | $149/mo |
| **Enterprise** | Unlimited | SSO, SLA, dedicated support | Custom |

**Bring Your Own Key (BYOK):** Use your own Groq API key and only pay for our platform features.

## Documentation

- [React SDK Guide](./react-sdk.md)
- [Vanilla JS Guide](./vanilla-sdk.md)
- [Python Server SDK](./python-sdk.md)
- [API Reference](./api-reference.md)
- [Theming Guide](./theming.md)
- [Human Takeover Guide](./human-takeover.md)
