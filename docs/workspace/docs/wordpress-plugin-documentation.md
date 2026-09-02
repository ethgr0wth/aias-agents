# AiAssist WordPress Plugin Documentation

## Overview

The AiAssist WordPress Plugin provides a secure, side-by-side integration between WordPress and the AiAssist AI runtime.

**WordPress remains the content editor and publishing layer**, while all AI execution, model routing, security enforcement, and usage control are handled by the AiAssist platform.

Side-by-side means WordPress keeps full control of content and publishing, while AiAssist operates as a secure AI backend—no models, secrets, or provider APIs ever live inside WordPress.

This design allows users to safely use AI inside WordPress without exposing provider credentials or proprietary AI infrastructure. The plugin connects only to AiAssist-owned APIs, never directly to OpenAI, Groq, Anthropic, or other providers.

### Core Capabilities

- **AI Blog Post Generation** - Generate full posts with tone, length, and brand voice controls
- **AI Code Generation** - Generate code snippets in multiple languages
- **AI Chat Widget** - Embed a secure AI chat assistant on your site
- **Multi-Model Selection** - Choose from approved models exposed by AiAssist
- **Domain-Scoped Security** - Safe client API keys restricted to your site

---

## Installation

### Requirements
- WordPress 5.8 or higher
- PHP 7.4 or higher
- Active AiAssist account

### Installation Steps

1. Download the `aiassist-wordpress-plugin.zip` file
2. In WordPress Admin, go to **Plugins → Add New → Upload Plugin**
3. Upload the zip file and click **Install Now**
4. Activate the plugin
5. Go to **Settings → AiAssist** to configure your API key

---

## Configuration

### API Key Setup (Important)

AiAssist uses **scoped client API keys** designed specifically for frontend and CMS usage.

#### Required Key Type

**Client API Key (`aai_pub_`)**
- Domain-restricted (locked to your website)
- Feature-scoped (chat, blog, code, etc.)
- Rate-limited and token-capped
- Safe for WordPress and browser-adjacent usage

> ⚠️ **Do not use standard keys (`aai_`) inside WordPress.**
> Standard keys are server-only and must never be exposed to CMS plugins.

#### Setup Steps

1. Log into your AiAssist dashboard
2. Navigate to **Dashboard → API Keys**
3. Click **Create Client Key**
4. Restrict it to your domain (e.g., `yourdomain.com`)
5. Enable only the features you need (chat, blog, code)
6. Copy the key (starts with `aai_pub_`)
7. Paste it into **Settings → AiAssist** in WordPress

### Settings Options

| Setting | Description | Default |
|---------|-------------|---------|
| Client API Key | Your AiAssist client key (`aai_pub_`) | Required |
| API Endpoint | Your AiAssist instance URL | Required |
| Default Model | Preferred AI model for generation | Based on plan |
| Enable Chat Widget | Show chat on frontend | Disabled |
| Chat Position | Widget position | Bottom Right |
| Primary Color | Widget accent color | #6366f1 |
| Welcome Message | Initial chat greeting | Hello! How can I help? |

---

## Security Architecture

The AiAssist WordPress plugin follows a secure proxy architecture:

- **WordPress never executes AI models**
- **Provider credentials are never exposed**
- **All requests are validated by:**
  - Domain origin
  - Feature scope
  - Rate limits
  - Token caps

This means even if someone inspects your WordPress site's source code, they cannot:
- Access your AI provider credentials
- Bypass rate limits
- Use features not scoped to your key
- Make requests from unauthorized domains

**WordPress never handles billing, usage aggregation, or provider charges.** All usage is tracked and enforced by AiAssist.

> AI-generated content is advisory and should be reviewed before publication.

AiAssist is among the first platforms to offer domain-scoped AI access for CMS environments, allowing teams to build with AI safely without exposing secrets or provider credentials.

---

## Features

### 1. Blog Post Generation

Generate AI-assisted blog posts directly inside the WordPress editor.

#### How to Use

1. Go to **Posts → Add New** or edit an existing post
2. Open the **AiAssist** panel in the editor sidebar
3. Enter a topic or description
4. Choose:
   - **Tone**: Professional, Casual, Technical, Creative
   - **Length**: Short (~500 words), Medium (~1000 words), Long (~2000+ words)
   - **Model**: From your allowed model list
5. Click **Generate Post**
6. Review, edit, and publish

#### Example Prompt

```
Topic: Introduction to React Hooks
Tone: Technical
Length: Medium
Keywords: useState, useEffect, custom hooks
```

---

### 2. Code Generation

Generate code snippets in multiple programming languages.

#### Supported Languages
- JavaScript / TypeScript
- Python
- PHP
- HTML / CSS
- SQL
- More via platform updates

#### How to Use

1. Click the **AiAssist Code** button in the editor toolbar
2. Describe the code you need
3. Select a language
4. Click **Generate Code**
5. The result is inserted at your cursor

---

### 3. Chat Widget

Embed a secure AI chat assistant on your site.

#### Setup

1. Go to **Settings → AiAssist → Chat Widget**
2. Enable the widget
3. Configure:
   - Position
   - Color
   - Welcome message
   - Placeholder text

#### Shortcode

```
[aiassist_chat]
```

With options:
```
[aiassist_chat position="bottom-right" color="#3b82f6" welcome="How can I help?"]
```

#### Security Notes

- Uses domain-restricted client keys
- Cannot access admin data
- Cannot perform privileged actions
- Fully rate-limited and token-capped

---

### 4. Multi-Model Selection

Available models are controlled by your plan and enforced server-side by AiAssist. The plugin will only show models you have access to.

#### Common Models

| Model | Best For | Speed |
|-------|----------|-------|
| llama-3.3-70b-versatile | General purpose, high quality | Medium |
| llama-3.1-8b-instant | Quick responses, simple tasks | Fast |
| mixtral-8x7b-32768 | Technical content, longer context | Medium |

Models can be selected:
- Per-generation in the sidebar panel
- As a default in plugin settings
- Via shortcode attributes

---

## Shortcodes Reference

### Chat Widget
```
[aiassist_chat]
[aiassist_chat position="bottom-left" color="#10b981"]
```

### Blog Embed
```
[aiassist_blog token="your-embed-token" layout="grid" columns="3"]
[aiassist_blog token="your-embed-token" layout="list" limit="5"]
```

### Code Generation
```
[aiassist_code language="python" prompt="fibonacci function"]
```

---

## Authentication

**Provider APIs are never exposed.** All authentication goes through AiAssist's secure proxy.

### Client Key Validation

When a request is made from WordPress:

1. The `aai_pub_` key is sent in the request header
2. AiAssist validates:
   - Key exists and is active
   - Request origin matches allowed domain
   - Requested feature is in scope
   - Rate limits not exceeded
   - Token budget available
3. If valid, AiAssist forwards to the appropriate AI provider
4. Response is returned to WordPress

### Header Format

**Preferred:**
```
Authorization: Bearer aai_pub_your_client_key_here
```

**Also supported (legacy/compatibility):**
```
X-API-Key: aai_pub_your_client_key_here
```

### Embed Tokens vs Client Keys

- **Client API keys** authenticate the WordPress site
- **Embed tokens** scope access to specific blog content
- Both must validate for embeds to resolve

When using `[aiassist_blog]` shortcode, the client key authenticates the request while the embed token determines which blog content is accessible.

---

## Public AiAssist Endpoints

### Chat Completions (OpenAI-compatible)
```
POST /v1/chat/completions

{
  "model": "llama-3.3-70b-versatile",
  "messages": [
    {"role": "user", "content": "Your message"}
  ],
  "stream": false
}
```

### Blog Post Generation
```
POST /api/blog/blogs/{blog_id}/generate/post

{
  "topic": "Your topic",
  "keywords": ["keyword1", "keyword2"],
  "tone": "professional",
  "length": "medium"
}
```

### Embed Data
```
GET /api/embed/{embed_token}
GET /api/embed/{embed_token}/posts/{post_slug}
```

---

## Plugin File Structure

```
aiassist-wordpress-plugin/
├── aiassist.php              # Main plugin file
├── includes/
│   ├── class-aiassist-api.php      # API client
│   ├── class-aiassist-admin.php    # Admin settings
│   ├── class-aiassist-chat.php     # Chat widget
│   └── class-aiassist-shortcodes.php # Shortcode handlers
├── assets/
│   ├── css/
│   │   ├── admin.css
│   │   └── chat-widget.css
│   └── js/
│       ├── admin.js
│       └── chat-widget.js
├── blocks/
│   └── aiassist-chat/        # Gutenberg block
└── readme.txt
```

---

## Hooks and Filters

### Filters

```php
// Modify API request before sending
add_filter('aiassist_api_request', function($request, $endpoint) {
    // Modify request
    return $request;
}, 10, 2);

// Modify generated content before insertion
add_filter('aiassist_generated_content', function($content, $type) {
    // Process content
    return $content;
}, 10, 2);

// Filter available models
add_filter('aiassist_available_models', function($models) {
    // Modify model list
    return $models;
});
```

### Actions

```php
// After successful generation
add_action('aiassist_content_generated', function($content, $type, $options) {
    // Log, notify, etc.
}, 10, 3);

// Before API request
add_action('aiassist_before_request', function($endpoint, $data) {
    // Pre-request logic
}, 10, 2);
```

---

## Troubleshooting

### "Invalid API Key" Error

- Ensure you're using a **client key** (`aai_pub_`), not a standard key
- Check that the key is active in your AiAssist dashboard
- Verify the domain restriction matches your WordPress site

### "Domain Not Allowed" Error

- The client key is restricted to specific domains
- Add your WordPress domain to the key's allowed domains
- Include both `www` and non-`www` versions if needed

### "Feature Not Enabled" Error

- The requested feature (chat, blog, code) is not enabled for this key
- Edit your client key in AiAssist to enable the required features

### "Rate Limit Exceeded" Error

- You've exceeded the requests per minute/hour limit
- Wait and try again, or upgrade your plan for higher limits

### Chat Widget Not Appearing

1. Check that the widget is enabled in settings
2. Verify your client key has chat feature enabled
3. Check browser console for JavaScript errors
4. Ensure no theme/plugin conflicts

### Generated Content is Empty

- Check your token budget hasn't been exhausted
- Verify the model is available on your plan
- Try a shorter prompt or different model

---

## Support

For technical support:
- **Documentation**: Check this guide first
- **Dashboard**: View usage, manage keys, check status
- **Contact**: Reach out through your AiAssist dashboard

---

## Changelog

### 1.0.0
- Initial release
- Blog post generation with tone/length controls
- Code generation with language selection
- Chat widget with shortcode support
- Multi-model selection
- Domain-scoped client key authentication
