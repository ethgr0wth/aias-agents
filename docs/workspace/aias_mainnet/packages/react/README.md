# @aiassist-secure/react

[![npm version](https://img.shields.io/npm/v/@aiassist-secure/react.svg)](https://www.npmjs.com/package/@aiassist-secure/react)
[![React](https://img.shields.io/badge/React-17+-61DAFB.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue.svg)](https://www.typescriptlang.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

**Production-ready React components for AiAssist Secure** - Add enterprise AI chat to your React app in minutes. Includes shadow mode, human-in-the-loop detection, theming, and more.

---

## Features

- **Floating Widget** - One-line integration, bottom-right chat bubble
- **Embedded Chat** - Full control, embed anywhere in your layout
- **Shadow Mode UI** - Visual indicators for pending approvals
- **Human Handoff** - Automatic UI updates when humans take over
- **Typing Indicators** - Real-time "AI is typing..." animation
- **Full Theming** - Match your brand with custom themes
- **Dark/Light Mode** - Built-in theme switching
- **TypeScript** - Complete type definitions

---

## Installation

```bash
npm install @aiassist-secure/react
# or
yarn add @aiassist-secure/react
# or
pnpm add @aiassist-secure/react
```

---

## Quick Start: Floating Widget

Add a chat widget to your app with just one component:

```tsx
import { AiAssistChatWidget } from '@aiassist-secure/react';

function App() {
  return (
    <div>
      <h1>My App</h1>
      
      {/* That's it! A floating chat bubble appears */}
      <AiAssistChatWidget
        config={{
          apiKey: 'your-api-key',
          greeting: 'Hey there! How can I help you today?',
          systemPrompt: 'You are a friendly support agent for Acme Inc.'
        }}
        position="bottom-right"
      />
    </div>
  );
}
```

---

## Embedded Chat

For full control, embed the chat directly in your layout:

```tsx
import { AiAssistChat } from '@aiassist-secure/react';

function SupportPage() {
  return (
    <div className="support-container">
      <h1>Customer Support</h1>
      
      <div style={{ height: '600px', width: '400px' }}>
        <AiAssistChat
          config={{
            apiKey: 'your-api-key',
            systemPrompt: 'You are a helpful customer support agent.',
            context: {
              user_id: 'user_123',
              plan: 'enterprise'
            }
          }}
          showHeader={true}
          showSuggestions={true}
          suggestions={[
            'Track my order',
            'Request a refund',
            'Talk to a human'
          ]}
          onClose={() => navigate('/home')}
        />
      </div>
    </div>
  );
}
```

---

## Shadow Mode (Enterprise)

Handle AI drafts that require human approval:

```tsx
import { AiAssistChat } from '@aiassist-secure/react';

function EnterpriseSupport() {
  return (
    <AiAssistChat
      config={{
        apiKey: 'your-api-key',
        onMessage: (message) => {
          // Shadow mode: AI drafted a response awaiting approval
          if (message.pending_approval) {
            console.log('Draft pending approval:', message.content);
            // Show visual indicator that message is pending
          }
        },
        onModeChange: (mode) => {
          switch (mode) {
            case 'ai':
              console.log('AI is handling conversation');
              break;
            case 'shadow':
              console.log('Shadow mode: AI drafts require approval');
              // Update UI to show "Supervisor reviewing..."
              break;
            case 'takeover':
              console.log('Human agent has taken control');
              // Show "Speaking with Agent Sarah"
              break;
          }
        }
      }}
    />
  );
}
```

---

## Human-in-the-Loop Detection

Automatically detect when a human takes over:

```tsx
import { useState } from 'react';
import { AiAssistChat, Mode } from '@aiassist-secure/react';

function SmartChat() {
  const [mode, setMode] = useState<Mode>('ai');
  const [agentName, setAgentName] = useState<string | null>(null);

  return (
    <div>
      {/* Dynamic header based on who's responding */}
      <header className="chat-header">
        {mode === 'ai' && <span>AI Assistant</span>}
        {mode === 'shadow' && <span>AI Assistant (Supervised)</span>}
        {mode === 'takeover' && <span>Agent {agentName || 'Support'}</span>}
      </header>

      <AiAssistChat
        config={{
          apiKey: 'your-api-key',
          onModeChange: (newMode, details) => {
            setMode(newMode);
            if (details?.agent_name) {
              setAgentName(details.agent_name);
            }
          }
        }}
      />
    </div>
  );
}
```

---

## Custom Theming

Match your brand with a custom theme:

```tsx
import { AiAssistChatWidget, AiAssistTheme } from '@aiassist-secure/react';

const darkPurpleTheme: AiAssistTheme = {
  primary: '#8B5CF6',       // Violet accent
  background: '#0F0F1A',    // Dark background
  surface: '#1A1A2E',       // Card/header background
  text: '#FFFFFF',          // Main text
  textMuted: '#9CA3AF',     // Secondary text
  border: '#2D2D44',        // Border color
  radius: '16px',           // Rounded corners
  fontFamily: '"Inter", system-ui, sans-serif',
};

function App() {
  return (
    <AiAssistChatWidget
      config={{ apiKey: 'your-api-key' }}
      theme={darkPurpleTheme}
      position="bottom-right"
    />
  );
}
```

---

## Theme Provider

Share theme across multiple components:

```tsx
import { 
  AiAssistThemeProvider, 
  AiAssistChat, 
  useAiAssistTheme 
} from '@aiassist-secure/react';

function ChatHeader() {
  const { theme } = useAiAssistTheme();
  
  return (
    <div style={{ 
      backgroundColor: theme.surface,
      color: theme.text,
      padding: '16px',
      borderRadius: theme.radius
    }}>
      <h2>Support Chat</h2>
    </div>
  );
}

function App() {
  return (
    <AiAssistThemeProvider theme={{ primary: '#10B981' }}>
      <ChatHeader />
      <AiAssistChat config={{ apiKey: 'your-api-key' }} />
    </AiAssistThemeProvider>
  );
}
```

---

## Direct API Access

Use the API client for custom implementations:

```tsx
import { AiAssistAPI } from '@aiassist-secure/react';

const api = new AiAssistAPI({
  apiKey: 'your-api-key',
});

// Create workspace with system prompt
const { workspace, messages } = await api.createWorkspace({
  initialMessage: 'Hello!',
  systemPrompt: 'Be helpful and concise.',
  context: { user_tier: 'premium' }
});

// Send a follow-up message
const response = await api.sendMessage(workspace.id, 'What can you do?');

// Check for shadow mode
if (response.pending_approval) {
  console.log('Message pending approval');
}

// Get full history
const history = await api.getMessages(workspace.id);

// End conversation
await api.endConversation(workspace.id);
```

---

## Event Callbacks

Track everything happening in your chat:

```tsx
<AiAssistChat
  config={{
    apiKey: 'your-api-key',
    
    // New message received
    onMessage: (message) => {
      analytics.track('chat_message', {
        role: message.role,
        pending: message.pending_approval,
        mode: message.mode
      });
    },
    
    // Mode changed (AI/Shadow/Human)
    onModeChange: (mode) => {
      if (mode === 'takeover') {
        analytics.track('human_takeover');
      }
    },
    
    // Error occurred
    onError: (error) => {
      Sentry.captureException(error);
    },
    
    // Conversation ended
    onConversationEnd: () => {
      showFeedbackModal();
    }
  }}
/>
```

---

## Configuration Reference

### AiAssistConfig

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `apiKey` | `string` | Yes | Your AiAssist API key |
| `endpoint` | `string` | No | Custom API endpoint |
| `greeting` | `string` | No | Initial greeting message |
| `systemPrompt` | `string` | No | System prompt for AI behavior |
| `context` | `object` | No | Additional context for AI |
| `onMessage` | `(msg) => void` | No | New message callback |
| `onModeChange` | `(mode) => void` | No | Mode change callback |
| `onError` | `(err) => void` | No | Error callback |
| `onConversationEnd` | `() => void` | No | Conversation ended callback |

### AiAssistChatProps

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `config` | `AiAssistConfig` | Required | Configuration object |
| `theme` | `AiAssistTheme` | Default | Custom theme |
| `showHeader` | `boolean` | `true` | Show header bar |
| `showSuggestions` | `boolean` | `true` | Show suggestion buttons |
| `suggestions` | `string[]` | Default | Custom suggestions |
| `placeholder` | `string` | Auto | Input placeholder |
| `title` | `string` | `"AiAssist"` | Header title |
| `subtitle` | `string` | Auto | Header subtitle |
| `onClose` | `() => void` | - | Close handler |

### AiAssistChatWidgetProps

All `AiAssistChatProps` plus:

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `position` | `"bottom-right"` \| `"bottom-left"` \| `"top-right"` \| `"top-left"` | `"bottom-right"` | Widget position |
| `bubbleIcon` | `ReactNode` | Default | Custom bubble icon |
| `defaultOpen` | `boolean` | `false` | Start with chat open |

---

## TypeScript Types

```tsx
import type {
  // Configuration
  AiAssistConfig,
  AiAssistTheme,
  AiAssistChatProps,
  AiAssistChatWidgetProps,
  
  // Data types
  Message,
  Workspace,
  Mode,  // 'ai' | 'shadow' | 'takeover'
} from '@aiassist-secure/react';
```

---

## Related Packages

| Package | Description |
|---------|-------------|
| [@aiassist-secure/core](https://www.npmjs.com/package/@aiassist-secure/core) | Framework-agnostic TypeScript client |
| [@aiassist-secure/vanilla](https://www.npmjs.com/package/@aiassist-secure/vanilla) | Drop-in widget for any website |

---

## Links

- [Documentation](https://aiassist.net/developer-docs/react)
- [Live Demo](https://aiassist.net/demo)
- [GitHub](https://github.com/aiassistsecure/aiassist-react)

---

## License

MIT License - [Interchained LLC](https://interchained.com)
