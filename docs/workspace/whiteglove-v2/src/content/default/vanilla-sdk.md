---
title: Vanilla JS SDK
icon: Code
category: Developers
order: 3
description: Lightweight JavaScript widget for any website.
---

# Vanilla JS SDK Documentation

> `@aiassist/vanilla` - Drop-in AI chat widget for any website

No React, no build step required. Just add a script tag and you're done.

## Installation

### Option 1: CDN (Recommended)

```html
<script src="https://cdn.aiassist.net/widget.js"></script>
```

### Option 2: NPM

```bash
npm install @aiassist/vanilla
```

```javascript
import AiAssist from '@aiassist/vanilla';
```

### Option 3: Self-Hosted

Download `widget.js` and `widget.css` from releases and host on your own CDN.

---

## Quick Start

```html
<!DOCTYPE html>
<html>
<head>
  <title>My Website</title>
</head>
<body>
  <!-- Your website content -->
  
  <!-- Add AiAssist -->
  <script src="https://cdn.aiassist.net/widget.js"></script>
  <script>
    AiAssist.init({
      apiKey: 'your-api-key'
    });
  </script>
</body>
</html>
```

That's it! A chat bubble appears in the bottom-right corner.

---

## Configuration

### `AiAssist.init(options)`

Initialize the widget with your configuration.

```javascript
AiAssist.init({
  // Required
  apiKey: 'your-api-key',
  
  // Optional - Appearance
  position: 'bottom-right',        // 'bottom-right', 'bottom-left', 'top-right', 'top-left'
  theme: 'dark',                   // 'dark', 'light', or custom object
  zIndex: 9999,                    // CSS z-index for the widget
  
  // Optional - Behavior
  autoOpen: false,                 // Open chat automatically on load
  autoOpenDelay: 5000,             // Delay before auto-open (ms)
  greeting: 'Hi! How can I help?', // Welcome message
  placeholder: 'Type a message...', // Input placeholder
  
  // Optional - AI Configuration
  systemPrompt: 'You are a helpful assistant.',
  
  // Optional - Branding
  title: 'Support Chat',           // Header title
  subtitle: 'We typically reply instantly',
  logo: 'https://yoursite.com/logo.png',
  poweredBy: true,                 // Show "Powered by AiAssist"
  
  // Optional - Callbacks
  onReady: () => console.log('Widget loaded'),
  onOpen: () => console.log('Chat opened'),
  onClose: () => console.log('Chat closed'),
  onMessage: (message) => console.log('Message:', message),
  onError: (error) => console.error('Error:', error)
});
```
