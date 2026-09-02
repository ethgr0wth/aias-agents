# AiAssist Integration Guide

Complete documentation for integrating AiAssist into your applications. Whether you're using our SDK, React components, WordPress plugin, or building a custom integration with our API directly.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Authentication](#authentication)
3. [API Reference](#api-reference)
   - [Chat Completions API](#chat-completions-api)
   - [Workspaces API](#workspaces-api)
4. [JavaScript SDK](#javascript-sdk)
5. [React SDK](#react-sdk)
6. [WordPress Plugin](#wordpress-plugin)
7. [Security Best Practices](#security-best-practices)
8. [Error Handling](#error-handling)
9. [Rate Limits](#rate-limits)
10. [Examples](#examples)

---

## Getting Started

### Base URL

All API requests should be made to:

```
Production: https://api.aiassist.net
Development: http://localhost:5000
```

### Quick Start

1. **Sign up** at [aiassist.net](https://aiassist.net) and create an account
2. **Generate an API key** from your Dashboard → API Keys
3. **Choose your integration method**:
   - **SDK/Widget**: Fastest setup, pre-built UI
   - **React Component**: For React applications
   - **WordPress Plugin**: One-click installation
   - **Direct API**: Full control, custom implementations

---

## Authentication

AiAssist uses API keys for authentication. All API requests must include your API key in the request headers.

### API Key Format

API keys are prefixed with `aai_` for easy identification:
```
aai_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Authentication Header

Include your API key in the `X-API-Key` header:

```bash
curl -X POST https://api.aiassist.net/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: aai_your_api_key_here" \
  -d '{
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### API Key Types

| Type | Use Case | Permissions |
|------|----------|-------------|
| **Standard** | Server-side integrations | Full API access |
| **Extended** | Team/Organization use | Shared across team members |

---

## API Reference

### Chat Completions API

OpenAI-compatible chat completions endpoint. Drop-in replacement for OpenAI's API.

#### Endpoint

```
POST /v1/chat/completions
```

#### Request

```json
{
  "model": "llama-3.3-70b-versatile",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is the capital of France?"}
  ],
  "temperature": 0.7,
  "max_tokens": 1024,
  "stream": false
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model` | string | No | Model to use. Defaults to your plan's best available model |
| `messages` | array | Yes | Array of message objects with `role` and `content` |
| `temperature` | number | No | Sampling temperature (0-2). Default: 0.7 |
| `max_tokens` | number | No | Maximum tokens to generate. Default: 1024 |
| `stream` | boolean | No | Enable streaming responses. Default: false |
| `top_p` | number | No | Nucleus sampling parameter. Default: 1.0 |

#### Response

```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1703123456,
  "model": "llama-3.3-70b-versatile",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "The capital of France is Paris."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 10,
    "total_tokens": 35
  }
}
```

#### Streaming

Enable streaming for real-time responses:

```javascript
const response = await fetch('https://api.aiassist.net/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': 'aai_your_api_key'
  },
  body: JSON.stringify({
    model: 'llama-3.3-70b-versatile',
    messages: [{ role: 'user', content: 'Tell me a story' }],
    stream: true
  })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  const chunk = decoder.decode(value);
  const lines = chunk.split('\n').filter(line => line.startsWith('data: '));
  
  for (const line of lines) {
    const data = line.slice(6);
    if (data === '[DONE]') break;
    
    const parsed = JSON.parse(data);
    const content = parsed.choices[0]?.delta?.content || '';
    process.stdout.write(content);
  }
}
```

#### Available Models

```
GET /v1/models
```

Returns available models based on your plan:

```json
{
  "data": [
    {
      "id": "llama-3.3-70b-versatile",
      "object": "model",
      "owned_by": "groq"
    },
    {
      "id": "llama-3.1-8b-instant", 
      "object": "model",
      "owned_by": "groq"
    },
    {
      "id": "mixtral-8x7b-32768",
      "object": "model", 
      "owned_by": "groq"
    }
  ]
}
```

---

### Workspaces API

Workspaces provide managed conversation threads with built-in AI orchestration, human takeover support, and message history.

#### Create Workspace

```
POST /api/workspaces
```

```json
{
  "initial_message": "Hello, I need help with my order",
  "client_id": "unique-client-identifier",
  "metadata": {
    "source": "website",
    "page": "/checkout"
  }
}
```

**Response:**

```json
{
  "workspace": {
    "id": "ws_abc123",
    "client_id": "unique-client-identifier",
    "mode": "ai",
    "status": "active",
    "created_at": "2024-01-15T10:30:00Z"
  },
  "messages": [
    {
      "id": "msg_1",
      "role": "user",
      "content": "Hello, I need help with my order",
      "created_at": "2024-01-15T10:30:00Z"
    },
    {
      "id": "msg_2", 
      "role": "ai",
      "content": "Hi! I'd be happy to help you with your order. Could you please provide your order number?",
      "created_at": "2024-01-15T10:30:01Z"
    }
  ]
}
```

#### Get Workspace by Client ID

Retrieve or create a workspace for a specific client:

```
GET /api/workspaces/by-client/{client_id}
```

**Response:**

```json
{
  "exists": true,
  "workspace": {
    "id": "ws_abc123",
    "mode": "ai",
    "status": "active"
  },
  "messages": [...]
}
```

#### Send Message

```
POST /api/workspaces/{workspace_id}/messages
```

```json
{
  "content": "My order number is #12345"
}
```

**Response:**

```json
{
  "user_message": {
    "id": "msg_3",
    "role": "user",
    "content": "My order number is #12345"
  },
  "responses": [
    {
      "id": "msg_4",
      "role": "ai",
      "content": "Thank you! I found your order #12345. It was placed on January 10th and is currently in transit..."
    }
  ],
  "mode": "ai"
}
```

#### Get Messages

```
GET /api/workspaces/{workspace_id}/messages
```

**Response:**

```json
{
  "messages": [
    {"id": "msg_1", "role": "user", "content": "...", "created_at": "..."},
    {"id": "msg_2", "role": "ai", "content": "...", "created_at": "..."}
  ]
}
```

#### Workspace Modes

| Mode | Description |
|------|-------------|
| `ai` | AI handles all responses automatically |
| `shadow` | AI drafts responses, human approves before sending |
| `takeover` / `human` | Human agent responds directly |

---

## JavaScript SDK

### Installation

```html
<!-- CDN -->
<script src="https://cdn.aiassist.net/widget.min.js"></script>

<!-- Or download and self-host -->
<script src="/js/aiassist-widget.min.js"></script>
```

### Basic Usage

```html
<!DOCTYPE html>
<html>
<head>
  <title>My Website</title>
</head>
<body>
  <!-- Your page content -->
  
  <!-- AiAssist Widget -->
  <script src="https://cdn.aiassist.net/widget.min.js"></script>
  <script>
    AiAssist.init({
      apiKey: 'aai_your_api_key',
      position: 'bottom-right',
      theme: 'dark'
    });
  </script>
</body>
</html>
```

### Configuration Options

```javascript
AiAssist.init({
  // Required
  apiKey: 'aai_your_api_key',
  
  // Positioning
  position: 'bottom-right',  // 'bottom-right' | 'bottom-left'
  offsetX: 20,               // Horizontal offset in pixels
  offsetY: 20,               // Vertical offset in pixels
  
  // Appearance
  theme: 'dark',             // 'dark' | 'light' | 'auto'
  primaryColor: '#22d3ee',   // Accent color (hex)
  borderRadius: 16,          // Widget border radius
  
  // Branding
  title: 'Support',          // Widget header title
  subtitle: 'How can we help?',
  avatarUrl: '/logo.png',    // Custom avatar image
  
  // Behavior
  greeting: 'Hi! How can I assist you today?',
  placeholder: 'Type your message...',
  autoOpen: false,           // Auto-open on page load
  autoOpenDelay: 5000,       // Delay before auto-open (ms)
  
  // Client Identification
  clientId: 'user_123',      // Unique identifier for this user
  metadata: {                // Custom metadata
    name: 'John Doe',
    email: 'john@example.com',
    plan: 'pro'
  },
  
  // Callbacks
  onOpen: () => console.log('Widget opened'),
  onClose: () => console.log('Widget closed'),
  onMessage: (message) => console.log('New message:', message),
  onModeChange: (mode) => console.log('Mode changed to:', mode)
});
```

### API Methods

```javascript
// Open the widget
AiAssist.open();

// Close the widget
AiAssist.close();

// Toggle open/closed
AiAssist.toggle();

// Send a message programmatically
AiAssist.sendMessage('Hello from my app!');

// Update client metadata
AiAssist.setMetadata({
  name: 'Jane Doe',
  customField: 'value'
});

// Set client identifier
AiAssist.setClientId('user_456');

// Destroy the widget
AiAssist.destroy();
```

### Custom Styling

Override default styles with CSS:

```css
/* Widget button */
.aiassist-button {
  background: linear-gradient(135deg, #22d3ee, #8b5cf6) !important;
  box-shadow: 0 4px 20px rgba(34, 211, 238, 0.4) !important;
}

/* Chat container */
.aiassist-container {
  font-family: 'Inter', sans-serif !important;
}

/* Message bubbles */
.aiassist-message-user {
  background: #22d3ee !important;
}

.aiassist-message-ai {
  background: rgba(255, 255, 255, 0.1) !important;
}

/* Input field */
.aiassist-input {
  border-color: rgba(255, 255, 255, 0.2) !important;
}

.aiassist-input:focus {
  border-color: #22d3ee !important;
}
```

---

## React SDK

### Installation

```bash
npm install @aiassist/react
# or
yarn add @aiassist/react
# or
pnpm add @aiassist/react
```

### Floating Widget (Quickest Setup)

The easiest way to add AiAssist to your React app:

```tsx
import { AiAssistChatWidget } from '@aiassist/react';

function App() {
  return (
    <div>
      <h1>My App</h1>
      <AiAssistChatWidget
        config={{
          apiKey: 'aai_your_api_key',
          greeting: 'How can I help you today?',
        }}
        position="bottom-right"
      />
    </div>
  );
}
```

### Embedded Chat

For more control, embed the chat directly in your layout:

```tsx
import { AiAssistChat } from '@aiassist/react';

function SupportPage() {
  return (
    <div style={{ height: '600px' }}>
      <AiAssistChat
        config={{
          apiKey: 'aai_your_api_key',
          systemPrompt: 'You are a helpful customer support agent.',
        }}
        onClose={() => console.log('Chat closed')}
      />
    </div>
  );
}
```

### Configuration Options

#### AiAssistConfig

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `apiKey` | `string` | Yes | Your AiAssist API key |
| `endpoint` | `string` | No | Custom API endpoint (default: `https://api.aiassist.net`) |
| `greeting` | `string` | No | Initial greeting message |
| `systemPrompt` | `string` | No | System prompt to customize AI behavior |
| `context` | `object` | No | Additional context passed to the AI |
| `onModeChange` | `(mode) => void` | No | Callback when mode changes between AI and human |
| `onMessage` | `(message) => void` | No | Callback when a new message is received |
| `onError` | `(error) => void` | No | Callback for error handling |

#### AiAssistChatProps

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `config` | `AiAssistConfig` | Required | Configuration object |
| `theme` | `AiAssistTheme` | - | Custom theme |
| `onClose` | `() => void` | - | Close button handler |
| `showHeader` | `boolean` | `true` | Show the header |
| `showSuggestions` | `boolean` | `true` | Show suggestion buttons |
| `suggestions` | `string[]` | Default | Custom suggestions |
| `placeholder` | `string` | Auto | Input placeholder |
| `title` | `string` | `"AiAssist"` | Header title |
| `subtitle` | `string` | Auto | Header subtitle |

#### AiAssistChatWidgetProps

Extends `AiAssistChatProps` with:

| Property | Type | Default | Description |
|----------|------|---------|-------------|
| `position` | `"bottom-right"` \| `"bottom-left"` \| `"top-right"` \| `"top-left"` | `"bottom-right"` | Widget position |
| `bubbleIcon` | `ReactNode` | Default icon | Custom bubble icon |
| `defaultOpen` | `boolean` | `false` | Start with chat open |

### Custom Theming

Customize the look and feel with a theme object:

```tsx
import { AiAssistChatWidget } from '@aiassist/react';
import type { AiAssistTheme } from '@aiassist/react';

const customTheme: AiAssistTheme = {
  primary: '#6366f1',      // Primary/accent color
  background: '#1e1e2e',   // Main background
  surface: '#2a2a3e',      // Card/header background
  text: '#ffffff',         // Main text color
  textMuted: '#a1a1aa',    // Secondary text
  border: '#3f3f46',       // Border color
  radius: '12px',          // Border radius
  fontFamily: 'Inter, sans-serif',
};

function App() {
  return (
    <AiAssistChatWidget
      config={{ apiKey: 'aai_your_api_key' }}
      theme={customTheme}
    />
  );
}
```

### Using the Theme Provider

For advanced theming across multiple components:

```tsx
import { AiAssistThemeProvider, AiAssistChat, useAiAssistTheme } from '@aiassist/react';

function CustomHeader() {
  const { theme } = useAiAssistTheme();
  return (
    <div style={{ backgroundColor: theme.surface }}>
      Custom Header
    </div>
  );
}

function App() {
  return (
    <AiAssistThemeProvider theme={{ primary: '#10b981' }}>
      <CustomHeader />
      <AiAssistChat config={{ apiKey: 'aai_your_api_key' }} />
    </AiAssistThemeProvider>
  );
}
```

### API Client (Headless Mode)

Use the API client directly for custom implementations:

```tsx
import { AiAssistAPI } from '@aiassist/react';

const api = new AiAssistAPI({
  apiKey: 'aai_your_api_key',
});

// Create a workspace and start a conversation
const { workspace, messages } = await api.createWorkspace({
  initialMessage: 'Hello!',
  systemPrompt: 'Be helpful and concise.',
});

// Send a message
const response = await api.sendMessage(workspace.id, 'What can you do?');

// Poll for updates
const updatedMessages = await api.getMessages(workspace.id);
```

### Event Callbacks

#### Mode Changes

The chat can switch between AI and human modes:

```tsx
<AiAssistChat
  config={{
    apiKey: 'aai_your_api_key',
    onModeChange: (mode) => {
      if (mode === 'human') {
        console.log('A human agent has joined');
      }
    },
  }}
/>
```

#### Message Tracking

Track all messages for analytics or logging:

```tsx
<AiAssistChat
  config={{
    apiKey: 'aai_your_api_key',
    onMessage: (message) => {
      analytics.track('chat_message', {
        role: message.role,
        timestamp: message.created_at,
      });
    },
  }}
/>
```

### TypeScript Types

Full TypeScript support with exported types:

```typescript
import type {
  Message,
  AiAssistConfig,
  AiAssistTheme,
  AiAssistChatProps,
  AiAssistChatWidgetProps,
  Mode,
} from '@aiassist/react';

// Message type
interface Message {
  id: string;
  role: 'user' | 'ai' | 'human' | 'system';
  content: string;
  created_at: string;
}

// Mode type
type Mode = 'ai' | 'human' | 'shadow' | 'takeover';
```

---

## WordPress Plugin

### Installation

1. Download the AiAssist WordPress plugin from your Dashboard
2. Go to **Plugins → Add New → Upload Plugin**
3. Upload the ZIP file and click **Install Now**
4. Activate the plugin

### Configuration

1. Go to **Settings → AiAssist**
2. Enter your API key
3. Configure widget appearance
4. Save changes

### Shortcode

Embed the chat widget anywhere using shortcodes:

```
[aiassist_chat]
```

With options:

```
[aiassist_chat 
  position="bottom-right" 
  theme="dark" 
  title="Help Desk"
  primary_color="#22d3ee"
]
```

### Widget Settings

| Setting | Description | Default |
|---------|-------------|---------|
| API Key | Your AiAssist API key | Required |
| Position | Widget position on screen | bottom-right |
| Theme | Color theme | dark |
| Title | Widget header title | Support |
| Primary Color | Accent color | #22d3ee |
| Auto Open | Open widget automatically | No |
| Show on Pages | Specific pages to show widget | All |
| Hide on Pages | Pages to hide widget | None |

### PHP Functions

For developers who want more control:

```php
// Check if AiAssist is active
if (function_exists('aiassist_is_active')) {
  if (aiassist_is_active()) {
    // Plugin is active and configured
  }
}

// Manually render the widget
if (function_exists('aiassist_render_widget')) {
  aiassist_render_widget([
    'position' => 'bottom-left',
    'theme' => 'light'
  ]);
}

// Get current configuration
$config = aiassist_get_config();
```

### Hooks and Filters

```php
// Modify widget configuration
add_filter('aiassist_widget_config', function($config) {
  // Add custom metadata
  $config['metadata'] = [
    'user_id' => get_current_user_id(),
    'user_email' => wp_get_current_user()->user_email
  ];
  return $config;
});

// Conditionally show/hide widget
add_filter('aiassist_should_display', function($display) {
  // Hide on checkout page
  if (is_checkout()) {
    return false;
  }
  return $display;
});

// After widget loads
add_action('aiassist_widget_loaded', function() {
  // Custom initialization
});
```

### WooCommerce Integration

```php
// Pass order context to widget
add_filter('aiassist_widget_config', function($config) {
  if (is_order_received_page()) {
    $order_id = get_query_var('order-received');
    $order = wc_get_order($order_id);
    
    $config['metadata']['order_id'] = $order_id;
    $config['metadata']['order_total'] = $order->get_total();
    $config['greeting'] = 'Thanks for your order! Need help with anything?';
  }
  return $config;
});
```

---

## Security Best Practices

### API Key Protection

**Never expose API keys in client-side code for production.**

For client-side integrations, use a proxy endpoint:

```javascript
// ❌ BAD - API key exposed
fetch('https://api.aiassist.net/v1/chat/completions', {
  headers: { 'X-API-Key': 'aai_secret_key' }
});

// ✅ GOOD - Use your backend as proxy
fetch('/api/chat', {
  method: 'POST',
  body: JSON.stringify({ message: 'Hello' })
});
```

Backend proxy example (Node.js):

```javascript
app.post('/api/chat', async (req, res) => {
  const response = await fetch('https://api.aiassist.net/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': process.env.AIASSIST_API_KEY  // Server-side only
    },
    body: JSON.stringify({
      messages: [{ role: 'user', content: req.body.message }]
    })
  });
  
  const data = await response.json();
  res.json(data);
});
```

### CORS Configuration

For widgets embedded on your domain, CORS is handled automatically. For custom domains:

```javascript
// Include origin in requests
fetch('https://api.aiassist.net/v1/chat/completions', {
  headers: {
    'Origin': 'https://yourdomain.com'
  }
});
```

### Rate Limiting

Implement client-side rate limiting to prevent abuse:

```javascript
class RateLimiter {
  constructor(maxRequests, windowMs) {
    this.maxRequests = maxRequests;
    this.windowMs = windowMs;
    this.requests = [];
  }

  canMakeRequest() {
    const now = Date.now();
    this.requests = this.requests.filter(t => now - t < this.windowMs);
    
    if (this.requests.length >= this.maxRequests) {
      return false;
    }
    
    this.requests.push(now);
    return true;
  }
}

const limiter = new RateLimiter(10, 60000); // 10 requests per minute

async function sendMessage(content) {
  if (!limiter.canMakeRequest()) {
    throw new Error('Rate limit exceeded. Please wait.');
  }
  // ... send request
}
```

---

## Error Handling

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Invalid or missing API key |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 429 | Too Many Requests - Rate limit exceeded |
| 500 | Internal Server Error |

### Error Response Format

```json
{
  "error": {
    "code": "invalid_api_key",
    "message": "The provided API key is invalid or expired.",
    "details": {}
  }
}
```

### Common Errors

| Error Code | Cause | Solution |
|------------|-------|----------|
| `invalid_api_key` | API key is wrong or expired | Check your API key in Dashboard |
| `rate_limit_exceeded` | Too many requests | Implement backoff, upgrade plan |
| `model_not_available` | Model not available for your plan | Use a different model or upgrade |
| `quota_exceeded` | Monthly quota exhausted | Wait for reset or upgrade plan |
| `workspace_not_found` | Invalid workspace ID | Check workspace ID or create new |

### Retry Logic

```javascript
async function fetchWithRetry(url, options, maxRetries = 3) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(url, options);
      
      if (response.status === 429) {
        const retryAfter = response.headers.get('Retry-After') || 5;
        await new Promise(r => setTimeout(r, retryAfter * 1000));
        continue;
      }
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      
      return response;
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      await new Promise(r => setTimeout(r, Math.pow(2, i) * 1000));
    }
  }
}
```

---

## Rate Limits

### Default Limits by Plan

| Plan | Requests/min | Requests/day | Tokens/day |
|------|--------------|--------------|------------|
| Free | 10 | 100 | 10,000 |
| Basic | 30 | 1,000 | 100,000 |
| Pro | 60 | 10,000 | 1,000,000 |
| Enterprise | Custom | Custom | Custom |

### Rate Limit Headers

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1703123456
```

### Check Usage

```
GET /v1/usage
```

```json
{
  "usage": {
    "requests_today": 234,
    "tokens_today": 45678,
    "requests_limit": 1000,
    "tokens_limit": 100000
  }
}
```

---

## Examples

### Customer Support Bot

```javascript
const AiAssist = require('@aiassist/node');

const client = new AiAssist({ apiKey: process.env.AIASSIST_API_KEY });

async function handleCustomerQuery(customerId, query) {
  // Get or create workspace for this customer
  const workspace = await client.workspaces.getOrCreate({
    clientId: customerId,
    metadata: {
      source: 'support_portal'
    }
  });
  
  // Send message and get response
  const response = await client.workspaces.sendMessage(workspace.id, {
    content: query
  });
  
  return response.responses[0].content;
}
```

### E-commerce Order Assistant

```javascript
AiAssist.init({
  apiKey: 'aai_your_key',
  metadata: {
    customerId: window.CUSTOMER_ID,
    cartValue: window.CART_TOTAL,
    currentPage: window.location.pathname
  },
  greeting: 'Hi! Looking for help with your order?',
  
  onMessage: (message) => {
    // Track in analytics
    analytics.track('Chat Message', {
      role: message.role,
      page: window.location.pathname
    });
  }
});
```

### Multi-language Support

The AI automatically responds in the user's language. No configuration needed:

```javascript
// User writes in Spanish
await client.chat.completions.create({
  messages: [
    { role: 'user', content: '¿Cuál es el estado de mi pedido?' }
  ]
});
// AI responds in Spanish automatically
```

### Streaming Chat UI

```javascript
async function streamChat(userMessage, onChunk) {
  const response = await fetch('https://api.aiassist.net/v1/chat/completions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': API_KEY
    },
    body: JSON.stringify({
      messages: [{ role: 'user', content: userMessage }],
      stream: true
    })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6);
        if (data === '[DONE]') return;
        
        try {
          const parsed = JSON.parse(data);
          const content = parsed.choices[0]?.delta?.content;
          if (content) onChunk(content);
        } catch (e) {}
      }
    }
  }
}

// Usage
let fullResponse = '';
await streamChat('Tell me a story', (chunk) => {
  fullResponse += chunk;
  document.getElementById('response').textContent = fullResponse;
});
```

---

## Support

- **Documentation**: [docs.aiassist.net](https://docs.aiassist.net)
- **API Status**: [status.aiassist.net](https://status.aiassist.net)
- **Email**: support@aiassist.net
- **Discord**: [discord.gg/aiassist](https://discord.gg/aiassist)

---

*Last updated: December 2024*
*API Version: v1*
