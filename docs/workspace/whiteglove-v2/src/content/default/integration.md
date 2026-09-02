---
title: Integration Guide
icon: Plug
category: Developers
order: 2
description: Step-by-step instructions for 3rd-party tool integration.
---

# AiAssist Integration Guide

Complete documentation for integrating AiAssist into your applications. Whether you're using our SDK, React components, WordPress plugin, or building a custom integration with our API directly.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Authentication](#authentication)
3. [JavaScript SDK](#javascript-sdk)
4. [Security Best Practices](#security-best-practices)
5. [Error Handling](#error-handling)
6. [Rate Limits](#rate-limits)
7. [Examples](#examples)

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

---

## Security Best Practices

### 1. Key Management
- Never expose your **API Key** in client-side code (except when using the `client_id` restricted keys for the Widget).
- Rotate keys immediately if you suspect a leak.
- Use environment variables to store keys.

### 2. Domain Restriction
- Configure allowed domains for your API keys in the dashboard to prevent unauthorized usage from other websites.

### 3. Rate Limiting
- Implement backoff strategies for 429 errors.
- Cache responses where possible to reduce API calls.

---

## Error Handling

The API uses standard HTTP status codes:

| Code | Meaning | Action |
|------|---------|--------|
| `200` | OK | Success |
| `400` | Bad Request | Check your parameters |
| `401` | Unauthorized | Check your API key |
| `403` | Forbidden | Check permissions/plan |
| `404` | Not Found | Resource does not exist |
| `429` | Too Many Requests | Slow down (backoff) |
| `500` | Server Error | Contact support |

---

## Rate Limits

Limits depend on your plan:

- **Free**: 100 requests/day
- **Pro**: 10,000 requests/day
- **Enterprise**: Unlimited (custom)

Headers provided in response:
- `X-RateLimit-Limit`: Total request limit
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Time until reset

---

## Examples

### Python Request

```python
import requests

url = "https://api.aiassist.net/v1/chat/completions"
headers = {
    "X-API-Key": "aai_your_key",
    "Content-Type": "application/json"
}
data = {
    "messages": [{"role": "user", "content": "Hello"}]
}

response = requests.post(url, headers=headers, json=data)
print(response.json())
```

### Node.js Request

```javascript
const axios = require('axios');

async function chat() {
  const response = await axios.post('https://api.aiassist.net/v1/chat/completions', {
    messages: [{ role: 'user', content: 'Hello' }]
  }, {
    headers: { 'X-API-Key': 'aai_your_key' }
  });
  console.log(response.data);
}
chat();
```
