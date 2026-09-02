# @aiassist-secure/vanilla

[![npm version](https://img.shields.io/npm/v/@aiassist-secure/vanilla.svg)](https://www.npmjs.com/package/@aiassist-secure/vanilla)
[![CDN](https://img.shields.io/badge/CDN-Available-success.svg)](https://cdn.aiassist.net/widget.js)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Bundle Size](https://img.shields.io/badge/minified-35KB-blue.svg)]()

**Drop-in AI chat widget for any website** - No framework required. Add enterprise AI support to any site with a single script tag.

Works with **WordPress, Shopify, Squarespace, Webflow, static HTML**, and more.

---

## Features

- **Zero Dependencies** - Single script, no build step required
- **Shadow DOM** - Styles isolated from your site
- **Shadow Mode** - AI drafts require human approval
- **Human Handoff** - Seamless AI-to-human transition
- **Lead Capture** - Collect emails before chat starts
- **Dark/Light Themes** - Built-in theme support
- **TypeScript** - Full type definitions included
- **CDN + npm** - Use via CDN or install via npm

---

## Quick Start (CDN)

Add two lines to your HTML:

```html
<script src="https://cdn.aiassist.net/widget.js"></script>
<script>
  AiAssist.init({
    apiKey: 'your-api-key'
  });
</script>
```

**That's it!** A chat bubble appears in the bottom-right corner.

---

## Installation via npm

```bash
npm install @aiassist-secure/vanilla
```

```javascript
import AiAssist from '@aiassist-secure/vanilla';

AiAssist.init({
  apiKey: 'your-api-key',
  position: 'bottom-right'
});
```

---

## Full Example

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>My Website</title>
</head>
<body>
  <h1>Welcome to My Site</h1>
  <p>We're here to help 24/7</p>
  
  <!-- AiAssist Chat Widget -->
  <script src="https://cdn.aiassist.net/widget.js"></script>
  <script>
    AiAssist.init({
      apiKey: 'your-api-key',
      
      // Branding
      title: 'Acme Support',
      subtitle: 'We typically reply in minutes',
      greeting: 'Hi there! How can I help you today?',
      
      // Behavior
      position: 'bottom-right',
      theme: 'dark',
      autoOpen: false,
      requireEmail: true,
      
      // AI Configuration
      systemPrompt: 'You are a friendly support agent for Acme Inc. Be helpful, concise, and professional.',
      
      // Callbacks
      onReady: () => console.log('Chat widget loaded'),
      onMessage: (msg) => console.log('New message:', msg),
      onLeadCapture: (lead) => {
        // Send to your CRM
        fetch('/api/leads', {
          method: 'POST',
          body: JSON.stringify(lead)
        });
      }
    });
  </script>
</body>
</html>
```

---

## Shadow Mode (Enterprise)

AI drafts are reviewed by a human before being sent:

```javascript
AiAssist.init({
  apiKey: 'your-api-key',
  
  onMessage: (message) => {
    // Check if message is pending approval
    if (message.pending_approval) {
      console.log('AI draft awaiting supervisor approval');
      // The message shows a "pending" indicator in the UI
    }
  },
  
  onModeChange: (mode) => {
    switch (mode) {
      case 'ai':
        console.log('AI is responding');
        break;
      case 'shadow':
        console.log('AI drafts being supervised');
        break;
      case 'takeover':
        console.log('Human agent has taken over');
        // Widget automatically shows "Speaking with Agent"
        break;
    }
  }
});
```

---

## Human-in-the-Loop

Detect when a human agent joins the conversation:

```javascript
AiAssist.init({
  apiKey: 'your-api-key',
  
  onModeChange: (mode) => {
    if (mode === 'takeover') {
      // Update your page to show human support is active
      document.getElementById('support-status').textContent = 
        'You are now speaking with a human agent';
    }
  }
});
```

---

## Lead Capture

Collect customer emails before starting the chat:

```javascript
AiAssist.init({
  apiKey: 'your-api-key',
  requireEmail: true,  // Show email form first
  
  onLeadCapture: (lead) => {
    console.log('Captured lead:', lead.email);
    
    // Send to your CRM, email service, or database
    fetch('https://your-api.com/leads', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: lead.email,
        source: 'chat_widget',
        timestamp: new Date().toISOString()
      })
    });
  }
});
```

---

## Programmatic Control

Control the widget from your JavaScript:

```javascript
// Get widget instance
const widget = AiAssist.getInstance();

// Open/close/toggle the chat
widget.open();
widget.close();
widget.toggle();

// Send a message programmatically
await widget.send('I need help with my order #12345');

// Get current conversation info
const workspaceId = widget.getWorkspaceId();
const messages = widget.getMessages();
const isOpen = widget.isOpen();

// End the conversation
await widget.endConversation();

// Destroy the widget completely
AiAssist.destroy();
```

---

## DOM Events

Listen for widget events on the document:

```javascript
// Widget fully loaded and ready
document.addEventListener('aiassist:ready', () => {
  console.log('Widget initialized');
});

// Chat window opened
document.addEventListener('aiassist:open', () => {
  console.log('User opened chat');
  analytics.track('chat_opened');
});

// Chat window closed
document.addEventListener('aiassist:close', () => {
  console.log('User closed chat');
});

// New message received
document.addEventListener('aiassist:message', (e) => {
  const message = e.detail;
  console.log(`${message.role}: ${message.content}`);
  
  if (message.pending_approval) {
    console.log('Message pending approval');
  }
});

// Mode changed (AI/Shadow/Human)
document.addEventListener('aiassist:mode:change', (e) => {
  console.log('Mode changed to:', e.detail.mode);
});

// Lead captured
document.addEventListener('aiassist:lead:capture', (e) => {
  console.log('Lead email:', e.detail.email);
});

// Conversation ended
document.addEventListener('aiassist:conversation:end', () => {
  console.log('Conversation ended');
});
```

---

## Configuration Reference

```javascript
AiAssist.init({
  // Required
  apiKey: 'your-api-key',
  
  // API Settings
  endpoint: 'https://api.aiassist.net',  // Custom endpoint
  
  // Position & Appearance
  position: 'bottom-right',   // bottom-right, bottom-left, top-right, top-left
  theme: 'dark',              // 'dark' or 'light'
  zIndex: 999999,             // CSS z-index
  
  // Branding
  title: 'AI Assistant',      // Header title
  subtitle: 'Ask me anything', // Header subtitle  
  placeholder: 'Type your message...', // Input placeholder
  poweredBy: true,            // Show "Powered by AiAssist"
  
  // Behavior
  greeting: null,             // Initial greeting message
  systemPrompt: null,         // AI system prompt
  context: {},                // Additional context object
  autoOpen: false,            // Auto-open on page load
  autoOpenDelay: 3000,        // Delay before auto-open (ms)
  requireEmail: true,         // Require email before chat
  
  // Callbacks
  onReady: () => {},                      // Widget initialized
  onOpen: () => {},                       // Chat opened
  onClose: () => {},                      // Chat closed
  onMessage: (message) => {},             // New message
  onError: (error) => {},                 // Error occurred
  onConversationStart: (workspaceId) => {}, // Conversation started
  onConversationEnd: () => {},            // Conversation ended
  onModeChange: (mode) => {},             // Mode changed (ai/shadow/takeover)
  onLeadCapture: (lead) => {}             // Email captured
});
```

---

## WordPress Integration

For WordPress sites, you can add the widget via:

### Option 1: Theme Footer

Add to your theme's `footer.php` or via **Appearance > Theme Editor**:

```php
<script src="https://cdn.aiassist.net/widget.js"></script>
<script>
  AiAssist.init({
    apiKey: '<?php echo get_option("aiassist_api_key"); ?>',
    title: '<?php bloginfo("name"); ?> Support'
  });
</script>
```

### Option 2: Plugin

Use our official WordPress plugin:

1. Download from [aiassist.net/wordpress](https://aiassist.net/wordpress)
2. Upload to `/wp-content/plugins/`
3. Activate and configure in **Settings > AiAssist**

---

## TypeScript Support

Type definitions are included:

```typescript
import AiAssist, { 
  AiAssistConfig, 
  Message,
  Mode 
} from '@aiassist-secure/vanilla';

const config: AiAssistConfig = {
  apiKey: 'your-api-key',
  onMessage: (message: Message) => {
    console.log(message.content);
    if (message.pending_approval) {
      console.log('Pending approval');
    }
  },
  onModeChange: (mode: Mode) => {
    console.log('Mode:', mode); // 'ai' | 'shadow' | 'takeover'
  }
};

AiAssist.init(config);
```

**CDN users:** Download type definitions from `https://cdn.aiassist.net/widget.d.ts`

---

## Browser Support

| Browser | Version |
|---------|---------|
| Chrome | 80+ |
| Firefox | 75+ |
| Safari | 14+ |
| Edge | 80+ |

---

## Related Packages

| Package | Description |
|---------|-------------|
| [@aiassist-secure/react](https://www.npmjs.com/package/@aiassist-secure/react) | React components |
| [@aiassist-secure/core](https://www.npmjs.com/package/@aiassist-secure/core) | TypeScript API client |

---

## Links

- [Documentation](https://aiassist.net/developer-docs/vanilla)
- [Live Demo](https://aiassist.net/demo)
- [CDN Setup Guide](https://aiassist.net/developer-docs/cdn)
- [WordPress Plugin](https://aiassist.net/wordpress)

---

## Support

- Documentation: [aiassist.net/docs](https://aiassist.net/docs)
- Developer Docs: [aiassist.net/developer-docs](https://aiassist.net/developer-docs)
- Email: support@aiassist.net

---

## License

MIT License - [Interchained LLC](https://interchained.com)
