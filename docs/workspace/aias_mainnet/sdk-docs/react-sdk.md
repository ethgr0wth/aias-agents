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

#### Returns

| Property | Type | Description |
|----------|------|-------------|
| `messages` | `Message[]` | All messages in current conversation |
| `isTyping` | `boolean` | Whether AI is generating response |
| `mode` | `'ai' \| 'human'` | Current conversation mode |
| `workspaceId` | `string \| null` | Current workspace ID |
| `isConnected` | `boolean` | Connection status |
| `sendMessage` | `(content: string) => Promise<void>` | Send a message |
| `clearConversation` | `() => void` | Clear and start new conversation |
| `setSystemPrompt` | `(prompt: string) => void` | Update system prompt |

---

### `useTypingPreview()`

Access real-time typing preview (for admin interfaces).

```tsx
import { useTypingPreview } from '@aiassist/react';

function AdminView({ workspaceId }) {
  const { text, isTyping } = useTypingPreview(workspaceId);

  return isTyping ? (
    <div className="typing-preview">
      Customer is typing: {text}
    </div>
  ) : null;
}
```

---

## Theming

### Using Preset Themes

```tsx
<AiAssistProvider theme="dark">
  {/* dark theme */}
</AiAssistProvider>

<AiAssistProvider theme="light">
  {/* light theme */}
</AiAssistProvider>
```

### Custom Theme

```tsx
const customTheme = {
  mode: 'dark',
  colors: {
    primary: '#00D4FF',      // Accent color
    background: '#0A0A0B',   // Main background
    surface: '#1A1A1B',      // Card/input backgrounds
    text: '#FFFFFF',         // Primary text
    textMuted: '#FFFFFF80',  // Secondary text
    border: '#FFFFFF10',     // Borders
    userBubble: '#00D4FF20', // User message background
    aiBubble: '#FFFFFF08',   // AI message background
  },
  fonts: {
    body: 'Inter, system-ui, sans-serif',
    mono: 'JetBrains Mono, monospace',
  },
  borderRadius: {
    sm: '8px',
    md: '12px',
    lg: '16px',
    full: '9999px',
  },
  shadows: {
    glow: '0 0 20px rgba(0, 212, 255, 0.3)',
  }
};

<AiAssistProvider theme={customTheme}>
  <AiAssistChat />
</AiAssistProvider>
```

### CSS Variables

You can also override styles using CSS variables:

```css
:root {
  --aiassist-primary: #00D4FF;
  --aiassist-background: #0A0A0B;
  --aiassist-surface: #1A1A1B;
  --aiassist-text: #FFFFFF;
  --aiassist-border-radius: 12px;
}
```

---

## Events & Callbacks

### Message Events

```tsx
<AiAssistChat
  onMessageSent={(message) => {
    // Track user engagement
    analytics.track('chat_message_sent', {
      content: message.content,
      timestamp: message.createdAt
    });
  }}
  onMessageReceived={(message) => {
    // Log AI responses
    console.log('AI said:', message.content);
  }}
/>
```

### Conversation Lifecycle

```tsx
<AiAssistChat
  onConversationStart={(workspaceId) => {
    // Store workspace ID for later reference
    sessionStorage.setItem('chatWorkspaceId', workspaceId);
  }}
  onConversationEnd={(data) => {
    // Send conversation summary to CRM
    sendToHubspot({
      messages: data.messages,
      duration: data.duration,
      resolved: data.mode === 'ai' // AI handled it
    });
  }}
/>
```

### Mode Changes

```tsx
<AiAssistChat
  onModeChange={(mode) => {
    if (mode === 'human') {
      // Human took over - maybe show different UI
      showHumanSupportBanner();
    }
  }}
/>
```

---

## TypeScript Types

```typescript
interface Message {
  id: string;
  role: 'user' | 'ai' | 'human' | 'system';
  content: string;
  createdAt: string;
  metadata?: Record<string, any>;
}

interface ConversationData {
  workspaceId: string;
  messages: Message[];
  duration: number; // seconds
  mode: 'ai' | 'human';
  metadata?: Record<string, any>;
}

interface ThemeConfig {
  mode: 'dark' | 'light';
  colors: {
    primary: string;
    background: string;
    surface: string;
    text: string;
    textMuted: string;
    border: string;
    userBubble: string;
    aiBubble: string;
  };
  fonts?: {
    body?: string;
    mono?: string;
  };
  borderRadius?: {
    sm?: string;
    md?: string;
    lg?: string;
    full?: string;
  };
}
```

---

## Examples

### Basic Chat Page

```tsx
import { AiAssistProvider, AiAssistChat } from '@aiassist/react';

export default function ChatPage() {
  return (
    <AiAssistProvider apiKey={process.env.AIASSIST_API_KEY}>
      <AiAssistChat 
        systemPrompt="You are a helpful customer support agent."
      />
    </AiAssistProvider>
  );
}
```

### Floating Widget

```tsx
import { AiAssistProvider, ChatBubble } from '@aiassist/react';

export default function App() {
  return (
    <AiAssistProvider apiKey={process.env.AIASSIST_API_KEY}>
      <YourAppContent />
      <ChatBubble position="bottom-right" />
    </AiAssistProvider>
  );
}
```

### Embedded in Dashboard

```tsx
import { AiAssistProvider, ChatWidget } from '@aiassist/react';

export default function Dashboard() {
  return (
    <AiAssistProvider apiKey={process.env.AIASSIST_API_KEY}>
      <div className="dashboard-layout">
        <Sidebar />
        <MainContent />
        <aside className="support-panel">
          <ChatWidget height={400} showHeader={true} />
        </aside>
      </div>
    </AiAssistProvider>
  );
}
```

### With Analytics Integration

```tsx
import { AiAssistProvider, AiAssistChat } from '@aiassist/react';
import { useAnalytics } from './analytics';

export default function SupportChat() {
  const { track } = useAnalytics();

  return (
    <AiAssistProvider apiKey={process.env.AIASSIST_API_KEY}>
      <AiAssistChat
        onMessageSent={(msg) => track('support_message', { type: 'user' })}
        onMessageReceived={(msg) => track('support_message', { type: 'ai' })}
        onConversationEnd={(data) => {
          track('support_conversation_complete', {
            messages: data.messages.length,
            duration: data.duration,
            handledByAI: data.mode === 'ai'
          });
        }}
      />
    </AiAssistProvider>
  );
}
```

---

## Troubleshooting

### Chat not loading

1. Check your API key is correct
2. Verify the endpoint is accessible
3. Check browser console for errors
4. Ensure `AiAssistProvider` wraps your chat components

### Styling conflicts

1. AiAssist uses scoped CSS - conflicts are rare
2. If needed, increase specificity with wrapper class
3. Use CSS variables for overrides

### TypeScript errors

Ensure you have the latest version:

```bash
npm update @aiassist/react
```

---

## Next Steps

- [Theming Guide](./theming.md) - Deep dive into customization
- [Human Takeover Guide](./human-takeover.md) - Set up admin monitoring
- [API Reference](./api-reference.md) - Full API documentation
