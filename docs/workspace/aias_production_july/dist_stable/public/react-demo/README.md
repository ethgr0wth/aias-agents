# @aiassist/react Demo

This example demonstrates how to use the `@aiassist/react` package in a React application.

## Installation

```bash
npm install @aiassist/react
```

## Components

### AiAssistChat

Embedded chat component for direct integration into your page layout.

```tsx
import { AiAssistChat } from '@aiassist/react';

<AiAssistChat
  apiKey="your-api-key"
  apiUrl="https://api.aiassist.net"
  height="400px"
  placeholder="Type your message..."
  welcomeMessage="Hello! How can I help?"
  onMessageSent={(message) => console.log('Sent:', message)}
  onResponseReceived={(response) => console.log('Received:', response)}
/>
```

### AiAssistChatWidget

Floating widget that can be toggled open/closed.

```tsx
import { AiAssistChatWidget } from '@aiassist/react';

<AiAssistChatWidget
  apiKey="your-api-key"
  apiUrl="https://api.aiassist.net"
  position="bottom-right"
  theme={{
    primaryColor: '#667eea',
  }}
/>
```

### AiAssistProvider

Theme provider for consistent styling across components.

```tsx
import { AiAssistProvider, AiAssistChat } from '@aiassist/react';

<AiAssistProvider
  theme={{
    primaryColor: '#10b981',
    backgroundColor: '#f0fdf4',
    textColor: '#166534',
    borderRadius: '12px',
  }}
>
  <AiAssistChat apiKey="..." apiUrl="..." />
</AiAssistProvider>
```

## Running the Demo

```bash
npm install
npm run dev
```

Visit `http://localhost:5173` to see the demo.
