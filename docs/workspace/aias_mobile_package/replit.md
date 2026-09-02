# AiAssist Secure Mobile Application

## Overview

This is a Capacitor-based mobile shell that wraps the AiAssist Secure web application (https://aiassist.net) for iOS and Android platforms. The app provides native mobile capabilities while leveraging the existing web UI.

## Recent Changes

- **2026-01-03**: Initial project setup
  - Created Capacitor project structure
  - Configured WebView to point to https://aiassist.net
  - Set up splash screen and status bar styling
  - Added deep linking support
  - Implemented secure storage via Preferences plugin
  - Created Express dev server for local preview

## Project Architecture

### Core Technologies
- **Capacitor 8.x** - Native bridge for iOS/Android
- **Express.js** - Development server
- **Node.js 20** - Runtime

### Capacitor Plugins
- `@capacitor/splash-screen` - Native splash screens
- `@capacitor/status-bar` - Status bar styling
- `@capacitor/preferences` - Secure storage
- `@capacitor/app` - Deep links, lifecycle
- `@capacitor/browser` - External links
- `@capacitor/haptics` - Tactile feedback
- `@capacitor/keyboard` - Keyboard handling
- `@capacitor/network` - Network monitoring
- `@capacitor/push-notifications` - Push notifications
- `@capacitor/share` - Native share sheet
- `@capacitor/local-notifications` - Local notifications

## Key Files

| File | Purpose |
|------|---------|
| `capacitor.config.ts` | Capacitor configuration |
| `www/index.html` | Loading/splash screen |
| `www/js/app.js` | Native bridge JavaScript |
| `src/server.js` | Express dev server |
| `WORKPLAN.md` | Detailed project workplan |
| `DEPLOYMENT.md` | iOS & Android deployment guide |

## Running the Project

### Development Preview
The app runs on port 5000 with a preview of the loading screen:
```bash
npm run dev
```

### Building for Mobile

**iOS:**
```bash
npm run cap:add:ios    # First time only
npm run build:ios      # Opens Xcode
```

**Android:**
```bash
npm run cap:add:android  # First time only
npm run build:android    # Opens Android Studio
```

## User Preferences

- Dark theme UI (#1a1a2e background)
- Purple accent color (#6366f1)
- Mobile-first design

## AiAssist API Integration

The app connects to the AiAssist Secure platform which provides:
- OpenAI-compatible chat completions
- Multi-provider AI (Groq, OpenAI, Anthropic, Gemini, Mistral)
- Workspaces and conversation management
- Deployed Agents with custom personas
- Knowledge Base for RAG context
- Shadow Mode for draft approval
- App Builder (Quests)
- Voice Actions
- CRM (Contacts, Leads)

## Deep Links

Supported URL schemes:
- `aiassist://workspace/{id}` - Open workspace
- `aiassist://agent/{id}` - Open deployed agent
- `aiassist://chat` - Open chat interface
