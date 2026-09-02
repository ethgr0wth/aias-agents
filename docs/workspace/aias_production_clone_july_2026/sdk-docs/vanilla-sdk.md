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

---

## JavaScript API

### Opening & Closing

```javascript
// Open the chat
AiAssist.open();

// Close the chat
AiAssist.close();

// Toggle open/close
AiAssist.toggle();

// Check if open
const isOpen = AiAssist.isOpen();
```

### Sending Messages

```javascript
// Send a message programmatically
AiAssist.sendMessage('Hello, I need help with my order');

// Send with metadata
AiAssist.sendMessage('Help with order #12345', {
  orderId: '12345',
  customerTier: 'premium'
});
```

### Conversation Management

```javascript
// Get current conversation ID
const workspaceId = AiAssist.getWorkspaceId();

// Get all messages
const messages = AiAssist.getMessages();

// Get current mode ('ai' or 'human')
const mode = AiAssist.getMode();

// Update context mid-conversation
AiAssist.updateContext({
  currentPage: '/products',
  cartValue: 150
});

// Clear conversation and start fresh
AiAssist.clearConversation();

// End conversation (triggers onConversationEnd)
AiAssist.endConversation();
```

### User Identification

```javascript
// Identify the user (for personalization & CRM sync)
AiAssist.identify({
  userId: 'user_123',
  email: 'customer@example.com',
  name: 'John Doe',
  plan: 'pro',
  // Any custom attributes
  customField: 'value'
});

// Clear user identity
AiAssist.clearIdentity();
```

### Visibility Control

```javascript
// Hide the widget completely
AiAssist.hide();

// Show the widget
AiAssist.show();

// Update position
AiAssist.setPosition('bottom-left');
```

### Destroying the Widget

```javascript
// Remove widget from page completely
AiAssist.destroy();
```

---

## Theming

### Preset Themes

```javascript
AiAssist.init({
  apiKey: 'your-api-key',
  theme: 'dark'  // or 'light'
});
```

### Custom Theme

```javascript
AiAssist.init({
  apiKey: 'your-api-key',
  theme: {
    mode: 'dark',
    primaryColor: '#00D4FF',
    backgroundColor: '#0A0A0B',
    textColor: '#FFFFFF',
    borderRadius: '12px',
    fontFamily: 'Inter, system-ui, sans-serif'
  }
});
```

### CSS Overrides

The widget uses Shadow DOM for isolation, but you can still customize with CSS variables:

```css
:root {
  --aiassist-primary: #FF6B00;
  --aiassist-bg: #1A1A1A;
  --aiassist-text: #FFFFFF;
  --aiassist-radius: 16px;
}
```

Or target the widget container:

```css
#aiassist-widget {
  /* Position overrides */
}
```

---

## Events

### Using Callbacks

```javascript
AiAssist.init({
  apiKey: 'your-api-key',
  
  onReady: () => {
    console.log('Widget is ready');
  },
  
  onOpen: () => {
    // Track in analytics
    gtag('event', 'chat_opened');
  },
  
  onClose: () => {
    gtag('event', 'chat_closed');
  },
  
  onMessage: (message) => {
    console.log('New message:', message);
    // message.role: 'user' | 'ai' | 'human'
    // message.content: string
    // message.id: string
  },
  
  onConversationStart: (workspaceId) => {
    console.log('Conversation started:', workspaceId);
  },
  
  onConversationEnd: (data) => {
    // Send to CRM
    fetch('/api/conversations', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  },
  
  onModeChange: (mode) => {
    if (mode === 'human') {
      console.log('Human agent took over');
    }
  },
  
  onError: (error) => {
    console.error('Chat error:', error);
    // Maybe show fallback contact options
  }
});
```

### Using Event Listeners

```javascript
// Alternative: DOM event listeners
document.addEventListener('aiassist:ready', () => {
  console.log('Widget ready');
});

document.addEventListener('aiassist:message', (e) => {
  console.log('Message:', e.detail);
});

document.addEventListener('aiassist:open', () => {
  console.log('Chat opened');
});

document.addEventListener('aiassist:close', () => {
  console.log('Chat closed');
});

document.addEventListener('aiassist:mode:change', (e) => {
  console.log('Mode changed to:', e.detail.mode);
  // 'ai' or 'human'
});

document.addEventListener('aiassist:conversation:start', (e) => {
  console.log('Conversation started:', e.detail.workspaceId);
});

document.addEventListener('aiassist:conversation:end', (e) => {
  console.log('Conversation ended:', e.detail.workspaceId);
});
```

---

## Embedding Options

### Floating Bubble (Default)

```javascript
AiAssist.init({
  apiKey: 'your-api-key',
  mode: 'bubble',
  position: 'bottom-right'
});
```

### Inline Embed

Embed directly in a container element:

```html
<div id="chat-container" style="width: 400px; height: 600px;"></div>

<script>
AiAssist.init({
  apiKey: 'your-api-key',
  mode: 'inline',
  container: '#chat-container'
});
</script>
```

### Full Page

```javascript
AiAssist.init({
  apiKey: 'your-api-key',
  mode: 'fullpage'
});
```

---

## Integration Examples

### With Google Analytics

```javascript
AiAssist.init({
  apiKey: 'your-api-key',
  onOpen: () => gtag('event', 'chat_open'),
  onMessage: (msg) => {
    gtag('event', 'chat_message', {
      role: msg.role,
      length: msg.content.length
    });
  },
  onConversationEnd: (data) => {
    gtag('event', 'chat_complete', {
      message_count: data.messages.length,
      duration: data.duration,
      handled_by: data.mode
    });
  }
});
```

### With Segment

```javascript
AiAssist.init({
  apiKey: 'your-api-key',
  onConversationEnd: (data) => {
    analytics.track('Support Conversation', {
      workspaceId: data.workspaceId,
      messages: data.messages.length,
      duration: data.duration,
      handledByAI: data.mode === 'ai'
    });
  }
});
```

### With HubSpot

```javascript
AiAssist.init({
  apiKey: 'your-api-key',
  onConversationEnd: async (data) => {
    // Create a support ticket
    await fetch('/api/hubspot/ticket', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        subject: 'Chat Conversation',
        content: data.messages.map(m => `${m.role}: ${m.content}`).join('\n'),
        customerEmail: currentUserEmail
      })
    });
  }
});
```

### E-commerce Product Context

```javascript
// On product pages, pass context to AI
AiAssist.init({
  apiKey: 'your-api-key',
  systemPrompt: `You are a sales assistant. The customer is viewing: 
    Product: ${productName}
    Price: ${productPrice}
    Category: ${productCategory}
    
    Help them with sizing, availability, and purchase decisions.`
});

// Update context when user navigates
window.addEventListener('productChange', (e) => {
  AiAssist.updateContext({
    systemPrompt: `Now viewing: ${e.detail.productName}...`
  });
});
```

---

## WordPress Integration

```php
// In your theme's footer.php or via plugin
<script src="https://cdn.aiassist.net/widget.js"></script>
<script>
AiAssist.init({
  apiKey: '<?php echo get_option("aiassist_api_key"); ?>',
  theme: '<?php echo get_option("aiassist_theme", "dark"); ?>'
});
</script>
```

---

## Shopify Integration

```liquid
<!-- In theme.liquid before </body> -->
<script src="https://cdn.aiassist.net/widget.js"></script>
<script>
AiAssist.init({
  apiKey: '{{ settings.aiassist_api_key }}',
  systemPrompt: `You are a helpful shopping assistant for {{ shop.name }}.
    {% if product %}
    Current product: {{ product.title }} - {{ product.price | money }}
    {% endif %}
  `
});

{% if customer %}
AiAssist.identify({
  email: '{{ customer.email }}',
  name: '{{ customer.name }}',
  ordersCount: {{ customer.orders_count }}
});
{% endif %}
</script>
```

---

## Browser Support

- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+
- Mobile browsers (iOS Safari, Chrome Android)

---

## Troubleshooting

### Widget not appearing

1. Check browser console for errors
2. Verify API key is correct
3. Ensure script is loaded (check Network tab)
4. Check z-index conflicts with your CSS

### Styling issues

1. Widget uses Shadow DOM - your CSS won't leak in
2. Use CSS variables for customization
3. Check `zIndex` option if widget appears behind other elements

### CORS errors

1. Ensure your domain is whitelisted in AiAssist dashboard
2. For local development, add `localhost` to allowed origins

---

## Security Notes

- Never expose your API key in client-side code on public repos
- Use environment variables or server-side injection
- API keys are domain-restricted for additional security
- Consider using short-lived tokens for sensitive applications

---

## Next Steps

- [Python Server SDK](./python-sdk.md) - Self-host the backend
- [API Reference](./api-reference.md) - Full API documentation
- [Theming Guide](./theming.md) - Deep customization
