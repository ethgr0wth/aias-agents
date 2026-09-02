---
title: WordPress Plugin
icon: Globe
category: Developers
order: 4
description: Official WordPress integration guide and settings.
---

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
