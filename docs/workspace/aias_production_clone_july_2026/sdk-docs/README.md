# AiAssist SDK

> Drop-in AI chat with seamless human takeover. Ship ChatGPT-quality conversations in minutes.

[![npm version](https://badge.fury.io/js/@aiassist%2Freact.svg)](https://www.npmjs.com/package/@aiassist/react)
[![PyPI version](https://badge.fury.io/py/aiassist.svg)](https://pypi.org/project/aiassist/)

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

## How It Works

### 1. Customer Opens Chat
They see a beautiful, responsive chat interface. First message creates a workspace.

### 2. AI Responds
Llama 3.3 70B generates intelligent, contextual responses. Fast (sub-second) thanks to Groq.

### 3. Admin Monitors (Optional)
Your team can watch conversations in real-time. See what customers type before they send.

### 4. Human Takes Over (When Needed)
One click switches to human mode. Your replies appear as AI responses - seamless handoff.

### 5. AI Resumes
Switch back to AI mode anytime. The AI picks up the conversation with full context.

## Example Use Cases

### SaaS Support
```tsx
<AiAssistChat 
  systemPrompt="You are a helpful support agent for Acme SaaS. 
    Help users with billing, features, and technical issues."
  escalationKeywords={['refund', 'cancel', 'speak to human']}
/>
```

### E-Commerce Sales
```tsx
<AiAssistChat 
  systemPrompt="You are a friendly sales assistant for a shoe store. 
    Help customers find the perfect shoes and answer sizing questions."
  productContext={currentProductPage}
/>
```

### Lead Generation
```tsx
<AiAssistChat 
  systemPrompt="You are a qualification bot for a consulting firm. 
    Gather info about the prospect's needs, budget, and timeline."
  onConversationEnd={(data) => sendToHubspot(data)}
/>
```

## Support

- **Documentation:** [aiassist.net/docs](https://aiassist.net/docs)
- **Developer Docs:** [aiassist.net/developer-docs](https://aiassist.net/developer-docs)
- **Discord:** [Join our community](https://discord.gg/aiassist)
- **Email:** support@aiassist.net

## License

MIT License - see [LICENSE](./LICENSE) for details.

---

Built with Groq, React, FastAPI, and Redis.
