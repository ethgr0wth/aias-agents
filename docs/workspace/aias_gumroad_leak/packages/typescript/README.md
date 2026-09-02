# @aiassist-secure/core

[![npm version](https://img.shields.io/npm/v/@aiassist-secure/core.svg)](https://www.npmjs.com/package/@aiassist-secure/core)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue.svg)](https://www.typescriptlang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

**Framework-agnostic TypeScript SDK for AiAssist Secure** - The enterprise AI orchestration platform with shadow mode, human-in-the-loop, and real-time typing indicators.

Works in **Node.js 18+** and **modern browsers**.

---

## Features

- **OpenAI-Compatible API** - Drop-in replacement syntax
- **Shadow Mode** - AI drafts require human approval before sending
- **Human-in-the-Loop** - Seamless AI-to-human handoff detection
- **Typing Preview** - Real-time "AI is typing..." indicators
- **Streaming** - Server-sent events for token-by-token output
- **Managed Workspaces** - Persistent conversation threads with context
- **Full TypeScript** - Complete type definitions included

---

## Installation

```bash
npm install @aiassist-secure/core
# or
yarn add @aiassist-secure/core
# or
pnpm add @aiassist-secure/core
```

---

## Quick Start

```typescript
import { AiAssistClient } from '@aiassist-secure/core';

const client = new AiAssistClient({ apiKey: 'aai_your_key' });

// Simple chat completion (OpenAI-compatible)
const response = await client.chat.completions.create({
  messages: [{ role: 'user', content: 'Hello!' }]
});

console.log(response.choices[0].message.content);
```

---

## Streaming Responses

Get real-time token-by-token output:

```typescript
const stream = await client.chat.completions.create({
  messages: [{ role: 'user', content: 'Write a haiku about coding' }],
  stream: true
});

for await (const chunk of stream) {
  const content = chunk.choices[0]?.delta?.content;
  if (content) {
    process.stdout.write(content); // Print each token as it arrives
  }
}
```

---

## Managed Workspaces

Create persistent conversation threads with full context:

```typescript
// Create a workspace with system prompt and context
const { workspace, messages } = await client.workspaces.create({
  clientId: 'user_123',
  initial_message: 'Hello!',
  system_prompt: 'You are a helpful customer support agent for Acme Inc.',
  context: {
    user_plan: 'enterprise',
    previous_tickets: 3
  }
});

console.log('Workspace ID:', workspace.id);
console.log('AI Response:', messages[0].content);

// Continue the conversation
const response = await client.workspaces.sendMessage(
  workspace.id,
  'I need help with my billing'
);

console.log('Mode:', response.mode); // 'ai' | 'shadow' | 'takeover'
console.log('Response:', response.responses[0].content);

// Get full conversation history
const history = await client.workspaces.getMessages(workspace.id);
```

---

## Shadow Mode (Enterprise)

In shadow mode, AI drafts require manager approval before being sent to the client. Perfect for training, compliance, and quality assurance:

```typescript
const response = await client.workspaces.sendMessage(workspace.id, 'Process my refund');

if (response.pending_approval) {
  console.log('AI drafted a response - awaiting manager approval');
  console.log('Draft:', response.responses[0].content);
  
  // The message won't be visible to the end-user until approved
  // Your manager dashboard can approve/reject/edit the draft
}

// Check workspace mode
console.log('Current mode:', response.mode);
// 'ai'      - Fully autonomous
// 'shadow'  - AI drafts, human approves  
// 'takeover' - Human control only
```

---

## Human-in-the-Loop Detection

Detect when a human agent takes over the conversation:

```typescript
const response = await client.workspaces.sendMessage(workspace.id, 'I want to speak to a human');

switch (response.mode) {
  case 'ai':
    console.log('AI is handling this conversation');
    break;
  case 'shadow':
    console.log('AI is drafting, but a human will review');
    break;
  case 'takeover':
    console.log('A human agent has taken control');
    // Update your UI to show "Speaking with Support Agent"
    break;
}
```

---

## Typing Preview

Show real-time "AI is typing..." indicators in your UI:

```typescript
// Poll for typing status (useful for chat UIs)
const status = await client.workspaces.getTypingStatus(workspace.id);

if (status.is_typing) {
  showTypingIndicator();
  console.log('AI is composing a response...');
} else {
  hideTypingIndicator();
}
```

---

## End Conversation

Gracefully close conversations with optional feedback:

```typescript
// End the conversation
await client.workspaces.endConversation(workspace.id);

// Or end with a reason/feedback
await client.workspaces.endConversation(workspace.id, {
  reason: 'resolved',
  feedback: 'Issue was resolved successfully'
});
```

---

## Configuration Options

```typescript
const client = new AiAssistClient({
  apiKey: 'aai_your_key',           // Required: Your API key
  baseURL: 'https://api.aiassist.net', // Custom endpoint
  timeout: 30000,                    // Request timeout (ms)
  maxRetries: 3,                     // Retry failed requests
  defaultHeaders: {                  // Custom headers
    'X-Custom-Header': 'value'
  }
});
```

---

## Error Handling

Typed errors for precise error handling:

```typescript
import {
  AiAssistClient,
  AuthenticationError,
  RateLimitError,
  APIError
} from '@aiassist-secure/core';

try {
  const response = await client.chat.completions.create({
    messages: [{ role: 'user', content: 'Hello' }]
  });
} catch (error) {
  if (error instanceof AuthenticationError) {
    console.error('Invalid API key - check your credentials');
  } else if (error instanceof RateLimitError) {
    console.error(`Rate limited. Retry after ${error.retryAfter} seconds`);
    // Implement exponential backoff
  } else if (error instanceof APIError) {
    console.error(`API error ${error.status}: ${error.message}`);
  }
}
```

---

## List Available Models

```typescript
const models = await client.models.list();

console.log('Available models:');
models.forEach(model => {
  console.log(`- ${model.id}: ${model.context_length} tokens`);
});

// Example output:
// - llama-3.3-70b-versatile: 128000 tokens
// - llama-3.1-8b-instant: 131072 tokens
// - mixtral-8x7b-32768: 32768 tokens
```

---

## TypeScript Types

Full type definitions included:

```typescript
import type {
  // Core types
  Message,
  ChatCompletion,
  ChatCompletionChunk,
  ChatCompletionCreateParams,
  
  // Workspace types
  Workspace,
  WorkspaceMessage,
  WorkspaceCreateParams,
  WorkspaceCreateResponse,
  SendMessageResponse,
  WorkspaceMode,        // 'ai' | 'shadow' | 'takeover'
  WorkspaceStatus,      // 'active' | 'ended'
  
  // Client types
  AiAssistClientOptions,
} from '@aiassist-secure/core';
```

---

## Browser Usage

Works directly in modern browsers via ESM:

```html
<script type="module">
  import { AiAssistClient } from 'https://esm.sh/@aiassist-secure/core';
  
  const client = new AiAssistClient({ 
    apiKey: 'aai_pub_your_domain_scoped_key' 
  });
  
  const response = await client.chat.completions.create({
    messages: [{ role: 'user', content: 'Hello from the browser!' }]
  });
  
  document.getElementById('output').textContent = 
    response.choices[0].message.content;
</script>
```

**Note:** Use domain-scoped public keys (`aai_pub_*`) for browser environments.

---

## Related Packages

| Package | Description |
|---------|-------------|
| [@aiassist-secure/react](https://www.npmjs.com/package/@aiassist-secure/react) | React components with built-in UI |
| [@aiassist-secure/vanilla](https://www.npmjs.com/package/@aiassist-secure/vanilla) | Drop-in widget for any website |

---

## Links

- [Documentation](https://aiassist.net/developer-docs/typescript)
- [API Reference](https://aiassist.net/api-reference)
- [GitHub](https://github.com/aiassistsecure/aiassist-js)
- [Discord Community](https://discord.gg/aiassist)

---

## License

MIT License - [Interchained LLC](https://interchained.com)
