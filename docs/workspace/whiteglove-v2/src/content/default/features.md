---
title: Core Features
icon: Sparkles
description: Security-First AI Orchestration.
category: Getting Started
order: 2
---
order: 1
---

## The Secure AI Orchestration Layer

AiAssist Secure is the missing link between your enterprise data and public AI models. We provide a **security-first** orchestration layer that manages keys, logs, and context retrieval so you don't have to.

> "Build AI apps with the security your CISO demands."

---

## Bring Your Own Keys (BYOK)

We believe you should own your infrastructure. AiAssist Secure allows you to:

| Component | BYOK Support |
|-----------|--------------|
| **LLM Providers** | OpenAI, Anthropic, Azure, Bedrock |
| **Vector DBs** | Pinecone, Weaviate, Milvus, Chroma |
| **Identity** | Okta, Auth0, Azure AD |
| **Storage** | S3, GCS, Azure Blob |

We act as a **stateless pass-through** for your credentials. We never store your API keys or data at rest.

---

## Observability & Analytics

Gain complete visibility into your AI application performance and costs:

### Real-Time Metrics
- **Token Usage**: Track input/output tokens per model, user, and request.
- **Latency**: Measure TTM (Time to First Token) and total generation time.
- **Error Rates**: Monitor API failures, rate limits, and timeouts.

### Cost Control
Set budget limits per project or user. Receive alerts when spending anomalies are detected.

---

## Enterprise-Ready

Designed for high-scale, mission-critical applications:

- **99.99% SLA**: Guaranteed uptime for the orchestration API.
- **SOC 2 Type II**: Independently audited security controls.
- **Single Tenant Option**: Deploy a dedicated instance in your VPC.
- **24/7 Support**: Enterprise support with dedicated technical account managers.

---

## Integration Ecosystem

Connect to your existing tools with one click:

```typescript
import { AiAssist } from '@aiassist/sdk';

const client = new AiAssist({
  apiKey: process.env.AIASSIST_API_KEY,
  provider: 'azure-openai', // Route to your Azure instance
  observability: true      // Enable auto-logging
});

const response = await client.chat.completions.create({
  model: 'gpt-4',
  messages: [{ role: 'user', content: 'Explain BYOK.' }]
});
```

Works with Vercel AI SDK, LangChain, and LlamaIndex out of the box.
