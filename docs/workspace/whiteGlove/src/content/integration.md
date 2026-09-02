---
title: Integration Guide
icon: Wrench
description: Step-by-step setup
category: Getting Started
order: 2
---

## Get Started in 5 Minutes

From zero to AI-powered in a few simple steps.

---

## Quick Start

### Step 1: Install the SDK

Choose the SDK that fits your stack:

```bash
# For React applications
npm install @aiassist-secure/react

# For any JavaScript environment
npm install @aiassist-secure/core
```

### Step 2: Get Your API Key

1. Visit [aiassist.net](https://aiassist.net)
2. Create a free account
3. Navigate to **API Keys** in your dashboard
4. Click **Generate New Key**
5. Copy your `aai_*` prefixed key

> Keep your API key secure. Never commit it to version control.

### Step 3: Add Your First Provider Key

1. Go to **Key Vault** in your dashboard
2. Click **Add Provider Key**
3. Select your provider (OpenAI, Anthropic, etc.)
4. Paste your provider's API key
5. Save — it's now encrypted and ready to use

---

## React Integration

The React SDK provides pre-built components and hooks:

```tsx
import { 
  AiAssistProvider,
  AiAssistChatWidget,
  useAiAssist 
} from '@aiassist-secure/react'

function App() {
  return (
    <AiAssistProvider apiKey={process.env.AIAS_API_KEY}>
      <YourApp />
      <AiAssistChatWidget 
        position="bottom-right"
        greeting="Hi! How can I help today?"
      />
    </AiAssistProvider>
  )
}
```

### Available Components

| Component | Description |
|-----------|-------------|
| `AiAssistProvider` | Context provider, wrap your app |
| `AiAssistChatWidget` | Floating chat button + modal |
| `AiAssistChat` | Inline chat component |
| `AiAssistInput` | Standalone input with streaming |

### Hooks

```tsx
const { 
  sendMessage,      // Send a message
  messages,         // Conversation history
  isStreaming,      // Loading state
  workspaces,       // Available workspaces
  switchWorkspace   // Change active workspace
} = useAiAssist()
```

---

## Core SDK Integration

For Node.js, Edge, or vanilla JavaScript:

```javascript
import { AiAS } from '@aiassist-secure/core'

const client = new AiAS({
  apiKey: process.env.AIAS_API_KEY
})

// Simple completion
const response = await client.chat.completions.create({
  model: 'gpt-4o',
  messages: [
    { role: 'user', content: 'Hello!' }
  ]
})

console.log(response.choices[0].message.content)
```

### Streaming

```javascript
const stream = await client.chat.completions.create({
  model: 'claude-3-5-sonnet',
  messages: [{ role: 'user', content: 'Write a haiku' }],
  stream: true
})

for await (const chunk of stream) {
  process.stdout.write(chunk.choices[0]?.delta?.content || '')
}
```

---

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `apiKey` | string | — | Your AiAS API key (required) |
| `endpoint` | string | `api.aiassist.net` | Custom API endpoint |
| `timeout` | number | `30000` | Request timeout in ms |
| `retries` | number | `2` | Automatic retry attempts |

### Chat Widget Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `position` | string | `bottom-right` | Widget position |
| `greeting` | string | — | Initial message |
| `systemPrompt` | string | — | AI instructions |
| `requireEmail` | boolean | `false` | Gate behind email capture |
| `theme` | object | — | Custom styling |

---

## Environment Variables

We recommend using environment variables for configuration:

```bash
# .env
AIAS_API_KEY=aai_your_key_here
AIAS_ENDPOINT=https://api.aiassist.net
```

Then access in your code:

```javascript
const client = new AiAS({
  apiKey: process.env.AIAS_API_KEY
})
```

---

## Next Steps

- [View live examples](/sdk-test) — React SDK demo
- [Core SDK playground](/core-sdk) — API exploration
- [Read the architecture](/v2/architecture) — How it works
