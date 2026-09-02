# Keystone Lite - Product Specification

## Overview
Keystone Lite is a standalone desktop application for AI-powered code debugging, editing, and project creation. It leverages AiAS APIs for multi-model AI capabilities while providing a lightweight, portable development environment.

**Tagline:** "Your AI coding companion - powered by any model"

## Target Users
- Developers who want AI-assisted debugging without IDE lock-in
- Keystone builders working locally
- Enterprise teams needing a deployable code assistant
- Privacy-conscious developers using self-hosted models

## Core Requirements
- Requires AiAS API key (clearly disclosed)
- No user authentication layer
- Works offline for editing, online for AI features
- Cross-platform: Windows, macOS, Linux

---

## Architecture

### Tech Stack
```
┌─────────────────────────────────────────┐
│           Electron Shell                │
├─────────────────────────────────────────┤
│  Main Process (Node.js)                 │
│  ├── File System Access                 │
│  ├── electron-store (settings)          │
│  └── IPC Bridge                         │
├─────────────────────────────────────────┤
│  Renderer Process (React + TypeScript)  │
│  ├── Monaco Editor                      │
│  ├── Chat Interface                     │
│  ├── File Explorer                      │
│  └── Tailwind CSS + shadcn/ui          │
├─────────────────────────────────────────┤
│  External APIs                          │
│  ├── AiAS API (api.aiassist.net)       │
│  ├── Custom OpenAI-compatible endpoints │
│  └── Local Ollama/vLLM instances       │
└─────────────────────────────────────────┘
```

### Directory Structure
```
keystone-lite/
├── src/
│   ├── main/           # Electron main process
│   │   ├── index.ts    # Entry point
│   │   ├── ipc.ts      # IPC handlers
│   │   └── store.ts    # Settings persistence
│   └── renderer/       # React frontend
│       ├── components/ # UI components
│       ├── pages/      # App pages
│       ├── hooks/      # Custom hooks
│       ├── lib/        # Utilities
│       └── styles/     # Tailwind config
├── assets/             # Icons, images
├── templates/          # Project templates
├── package.json
├── electron-builder.yml
└── vite.config.ts
```

---

## Features

### 1. File Explorer
- Local filesystem access via Electron APIs
- Folder tree with expand/collapse
- File operations: create, rename, delete, duplicate
- Drag-and-drop support
- Recent projects list

### 2. Monaco Editor
- Multi-tab editing
- Syntax highlighting (30+ languages)
- Auto-detect language from extension
- Line numbers with error indicators
- Minimap navigation
- Find/replace with regex support

### 3. Chat Panel
- Context-aware chat with selected files
- File attachment badges showing context
- Streaming responses
- Message history (per session)
- Copy code blocks
- Apply suggested edits

### 4. Multi-Model Support

#### Provider Options
| Provider | Models | API Type |
|----------|--------|----------|
| Groq | llama-3.3-70b, mixtral-8x7b | AiAS |
| OpenAI | gpt-4o, gpt-4o-mini | AiAS |
| Anthropic | claude-3.5-sonnet, claude-3-opus | AiAS |
| Google | gemini-1.5-pro, gemini-1.5-flash | AiAS |
| Mistral | mistral-large, codestral | AiAS |
| PIN Network | Operator models | AiAS |
| Custom | User-defined | Direct |

#### Model Selector UI
```
┌────────────────────────────────────┐
│ [Groq ▼] / [llama-3.3-70b-versatile ▼] 🟢 │
└────────────────────────────────────┘
```
- Provider dropdown
- Model dropdown (filtered by provider)
- Status indicator (green/yellow/red)
- "Test Connection" button

#### Custom Endpoints
Users can add OpenAI-compatible endpoints:
- Local Ollama (http://localhost:11434/v1)
- vLLM servers
- LMStudio
- Text Generation WebUI
- Any OpenAI-compatible API

### 5. Surgical Editing
Port existing Keystone surgical editing for precise AI code changes:
- Line-based insert/replace/delete
- Diff preview before applying
- Undo/redo support
- Conflict detection

### 6. Templates
Bundled project starters:
- React + TypeScript
- Next.js
- Express API
- FastAPI
- Static HTML/CSS/JS
- Electron App

### 7. Settings
```
┌─────────────────────────────────────────┐
│ Settings                                │
├─────────────────────────────────────────┤
│ API Configuration                       │
│ ├── AiAS API Key: [aai_••••••••••] ✓   │
│ ├── Default Provider: [Groq ▼]          │
│ └── Default Model: [llama-3.3-70b ▼]   │
│                                         │
│ Custom Endpoints                        │
│ ├── + Add Endpoint                      │
│ ├── Local Ollama    localhost:11434 🟢 │
│ └── vLLM Server     192.168.1.50   🟢  │
│                                         │
│ Editor Preferences                      │
│ ├── Theme: [Dark ▼]                     │
│ ├── Font Size: [14px]                   │
│ ├── Tab Size: [2 spaces ▼]              │
│ └── Word Wrap: [On ▼]                   │
│                                         │
│ AI Preferences                          │
│ ├── Temperature: [0.7]                  │
│ ├── Max Tokens: [4096]                  │
│ └── Stream Responses: [✓]               │
└─────────────────────────────────────────┘
```

---

## UI Layout

### Main Window
```
┌─────────────────────────────────────────────────────────────────┐
│ Keystone Lite                              [−][□][×]            │
├──────────────┬──────────────────────────────┬───────────────────┤
│ EXPLORER     │ main.ts              [×]     │ CHAT              │
│              │                              │                   │
│ ▼ my-project │  1 │ import express from    │ Using: Groq 🟢    │
│   ▼ src      │  2 │   'express';           │ llama-3.3-70b     │
│     main.ts  │  3 │                        │                   │
│     utils.ts │  4 │ const app = express(); │ ┌───────────────┐ │
│   package.js │  5 │                        │ │ How can I     │ │
│   tsconfig   │  6 │ app.get('/', (req, ==> │ │ help you?     │ │
│              │  7 │   res) => {            │ └───────────────┘ │
│              │  8 │   res.send('Hello');   │                   │
│ ──────────── │  9 │ });                    │ Context:          │
│ TEMPLATES    │ 10 │                        │ [main.ts ×]       │
│ + React      │ 11 │ app.listen(3000);      │ [utils.ts ×]      │
│ + Next.js    │                             │                   │
│ + Express    │                             │ [Ask AI...]       │
│ + FastAPI    │                             │ [Send ➤]          │
└──────────────┴──────────────────────────────┴───────────────────┘
│ Ready  │  TypeScript  │  UTF-8  │  LF  │  Ln 6, Col 15         │
└─────────────────────────────────────────────────────────────────┘
```

### First-Run Setup
```
┌─────────────────────────────────────────┐
│         Welcome to Keystone Lite        │
│                                         │
│    🔑 Enter your AiAS API Key          │
│    ┌─────────────────────────────────┐ │
│    │ aai_                            │ │
│    └─────────────────────────────────┘ │
│                                         │
│    Don't have a key?                   │
│    [Get one at aiassist.net →]         │
│                                         │
│    ☐ Remember this key                 │
│                                         │
│              [Continue →]               │
└─────────────────────────────────────────┘
```

---

## API Integration

### AiAS Chat Completions
```typescript
POST https://api.aiassist.net/api/chat/completions
Headers:
  Authorization: Bearer aai_xxxxx
  Content-Type: application/json

Body:
{
  "model": "llama-3.3-70b-versatile",
  "messages": [
    {
      "role": "system",
      "content": "You are a code assistant. When suggesting code changes, use the following format..."
    },
    {
      "role": "user", 
      "content": "Debug this code:\n```typescript\n{file_content}\n```\nError: {error_message}"
    }
  ],
  "stream": true,
  "temperature": 0.7
}
```

### Custom Endpoint Support
```typescript
interface CustomEndpoint {
  id: string;
  name: string;
  url: string;           // e.g., "http://localhost:11434/v1"
  apiKey?: string;       // Optional for local endpoints
  models: string[];      // Available models
  isOnline: boolean;     // Connection status
}
```

### Model Availability Check
```typescript
// For AiAS providers
GET https://api.aiassist.net/api/models
Authorization: Bearer aai_xxxxx

// For custom endpoints
GET {endpoint_url}/models
```

---

## Prompt Engineering

### System Prompt for Debugging
```
You are an expert code debugger. Analyze the provided code and:

1. Identify issues with specific line numbers
2. Categorize each issue (syntax, logic, security, performance)
3. Provide a fix for each issue

Respond in this JSON format:
{
  "summary": "Brief overview of issues found",
  "issues": [
    {
      "line": 15,
      "severity": "error|warning|info",
      "category": "syntax|logic|security|performance",
      "description": "What's wrong",
      "fix": "How to fix it",
      "code_before": "original code",
      "code_after": "fixed code"
    }
  ]
}
```

### System Prompt for Code Generation
```
You are a code assistant. When making changes to files:

1. Show the exact changes using surgical edit format
2. Explain what you're changing and why
3. Preserve existing code style and conventions

For file edits, use this format:
<<<EDIT filename.ts>>>
<<<DELETE lines 10-15>>>
<<<INSERT after line 20>>>
new code here
<<<END>>>
```

---

## Distribution

### Electron Builder Config
```yaml
appId: com.aiassist.keystone-lite
productName: Keystone Lite
directories:
  output: dist
files:
  - dist/**/*
  - package.json
mac:
  category: public.app-category.developer-tools
  icon: assets/icon.icns
win:
  icon: assets/icon.ico
linux:
  category: Development
  icon: assets/icon.png
```

### Package Formats
- **macOS:** .dmg, .zip
- **Windows:** .exe (NSIS installer), .zip
- **Linux:** .AppImage, .deb, .rpm

---

## Branding

### Messaging
- "Powered by AiAS"
- "Requires API Key"
- "Use any AI model"
- Clear link to get API key

### Colors (inherit from AiAS)
- Primary: Cyan (#00d4ff)
- Background: Dark (#0a0a0f)
- Accent: Matrix green (#00ff88)

---

## Success Metrics
- Download count
- API key activations
- Daily active users
- Conversion to full Keystone

## Future Enhancements
- Git integration
- Terminal panel
- Extension marketplace
- Team sharing (requires auth)
- VS Code extension port
