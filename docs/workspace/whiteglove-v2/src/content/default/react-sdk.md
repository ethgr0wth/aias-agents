---
title: React SDK
icon: Code
category: Developers
order: 3
description: Components and hooks for building React-based chat interfaces.
---

# React SDK Documentation

> `@aiassist/react` - Beautiful AI chat components for React applications

## Installation

```bash
npm install @aiassist/react
# or
yarn add @aiassist/react
# or
pnpm add @aiassist/react
```

### Peer Dependencies

```bash
npm install react react-dom framer-motion
```

## Quick Start

```tsx
import { AiAssistProvider, AiAssistChat } from '@aiassist/react';

function App() {
  return (
    <AiAssistProvider apiKey="your-api-key">
      <AiAssistChat />
    </AiAssistProvider>
  );
}
```

## Components

### `<AiAssistProvider>`

Wraps your app and provides configuration context to all AiAssist components.

```tsx
<AiAssistProvider
  apiKey="your-api-key"
  endpoint="https://api.aiassist.net"  // or your self-hosted endpoint
  theme="dark"
  onError={(error) => console.error(error)}
>
  {children}
</AiAssistProvider>
```

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `apiKey` | `string` | required | Your AiAssist API key |
| `endpoint` | `string` | `https://api.aiassist.net` | API endpoint URL |
| `groqApiKey` | `string` | - | Your own Groq API key (BYOK mode) |
| `theme` | `'dark' \| 'light' \| ThemeConfig` | `'dark'` | Theme configuration |
| `onError` | `(error: Error) => void` | - | Global error handler |
| `debug` | `boolean` | `false` | Enable debug logging |

---

### `<AiAssistChat>`

The main chat interface component. Renders a full-screen immersive chat experience.

```tsx
<AiAssistChat
  systemPrompt="You are a helpful assistant for Acme Corp."
  placeholder="Ask me anything..."
  onMessageSent={(message) => trackEvent('chat_message', message)}
  onConversationStart={(workspaceId) => console.log('Started:', workspaceId)}
/>
```

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `systemPrompt` | `string` | - | Custom system prompt for AI behavior |
| `placeholder` | `string` | `'Ask about AI strategy...'` | Input placeholder text |
| `welcomeMessage` | `string` | - | Initial message shown to user |
| `userName` | `string` | `'You'` | Display name for user messages |
| `assistantName` | `string` | `'AiAssist'` | Display name for AI messages |
| `onMessageSent` | `(msg: Message) => void` | - | Callback when user sends message |
| `onMessageReceived` | `(msg: Message) => void` | - | Callback when AI responds |
| `onConversationStart` | `(id: string) => void` | - | Callback when conversation begins |
| `onConversationEnd` | `(data: ConversationData) => void` | - | Callback when conversation ends |
| `onModeChange` | `(mode: 'ai' \| 'human') => void` | - | Callback when mode switches |
| `className` | `string` | - | Additional CSS classes |
| `style` | `CSSProperties` | - | Inline styles |

---

### `<ChatBubble>`

A floating button that opens the chat widget. Use when you want chat as an overlay.

```tsx
<ChatBubble
  position="bottom-right"
  size="lg"
  pulseAnimation={true}
  unreadCount={2}
/>
```

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `position` | `'bottom-right' \| 'bottom-left' \| 'top-right' \| 'top-left'` | `'bottom-right'` | Screen position |
| `size` | `'sm' \| 'md' \| 'lg'` | `'md'` | Button size |
| `offset` | `{ x: number, y: number }` | `{ x: 20, y: 20 }` | Offset from screen edge |
| `pulseAnimation` | `boolean` | `true` | Show attention pulse animation |
| `unreadCount` | `number` | `0` | Badge showing unread messages |
| `icon` | `ReactNode` | `<MessageIcon />` | Custom icon |
| `onClick` | `() => void` | - | Custom click handler |

---

### `<ChatWidget>`

An inline embedded chat widget for use within your page layout.

```tsx
<ChatWidget
  height={500}
  showHeader={true}
  collapsible={false}
/>
```

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `width` | `number \| string` | `'100%'` | Widget width |
| `height` | `number \| string` | `600` | Widget height |
| `showHeader` | `boolean` | `true` | Show header with title |
| `collapsible` | `boolean` | `false` | Allow collapsing to header only |
| `defaultCollapsed` | `boolean` | `false` | Start in collapsed state |
| `borderRadius` | `number` | `12` | Border radius in pixels |

---

## Hooks

### `useAiAssist()`

Access the AiAssist context and control chat programmatically.

```tsx
import { useAiAssist } from '@aiassist/react';

function MyComponent() {
  const { 
    sendMessage, 
    messages, 
    isTyping, 
    mode,
    workspaceId,
    clearConversation 
  } = useAiAssist();

  return (
    <button onClick={() => sendMessage('Hello!')}>
      Send Hello
    </button>
  );
}
```
