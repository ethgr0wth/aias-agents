# WhiteGlove

> An Agentic UX Framework — AI-powered spatial navigation with depth, motion, and natural language.

## What is WhiteGlove?

WhiteGlove is an open-source React framework for building **spatial web experiences with AI-powered adaptation**. Instead of flat pages connected by links, WhiteGlove treats the web as a 3D space where users navigate through "rooms" of content with smooth depth transitions — all while AI watches behavior and adapts the experience.

### The Prompt is Part of Every Website Now

WhiteGlove embeds AI directly into the browsing experience:

- **/ AI Command Bar** — Press `/` to navigate with natural language
- **🎤 Voice Control** — Say "Hey WhiteGlove" for hands-free navigation
- **🧠 Behavior Tracking** — Automatically captures scroll, click, hover, dwell time, exit intent
- **🎯 Intent Engine** — LLM analyzes behavior and suggests adaptive changes
- **📊 Engagement Scoring** — Real-time scoring influences dynamic mutations

### Spatial Navigation

Revolutionary content architecture for modern web:

- **🚪 Door Cards** — Content pages appear as doors in a directory; click to "enter" the room
- **🌊 Depth Transitions** — Smooth animations communicate spatial movement (zoom in/out, fade, blur)
- **📱 Mobile Gestures** — Swipe down to exit, tap to enter
- **📝 Markdown CMS** — Drop `.md` files in `/content/` and they auto-appear in the directory

### BYOK Security

- **🔐 Bring Your Own Key** — Use your own LLM API keys via AiAssist Secure
- **💸 No Markup** — Pay providers directly at their rates
- **🔄 Multi-Provider** — Switch between OpenAI, Anthropic, Groq without code changes

---

## Quick Start

### 1. Install

```bash
git clone https://github.com/interchained/whiteglove.git
cd whiteglove
npm install
```

### 2. Run

```bash
npm run dev
```

Visit `http://localhost:5000/v2` to see WhiteGlove in action.

---

## Adding Content

Drop Markdown files in `src/content/` with this frontmatter:

```markdown
---
title: Your Page Title
icon: Sparkles
description: Brief card description
category: Getting Started
order: 1
---

## Your Content

Write in standard Markdown...
```

**That's it!** The page automatically appears in the directory.

See `CONTENT_TEMPLATE.md` for full template with available icons and formatting examples.

### Available Icons

`Sparkles` · `Layers` · `Blocks` · `DollarSign` · `HelpCircle` · `Wrench` · `LayoutList` · `Zap` · `Shield` · `Code` · `Users` · `Settings` · `Globe` · `Lock` · `Rocket` · `BookOpen` · `MessageSquare` · `Terminal` · `Database` · `Key`

---

## How Spatial Navigation Works

```
┌─────────────────────────────────────────────────────┐
│  Directory View                                      │
│  Cards organized by category, each is a "door"       │
└───────────────────────┬─────────────────────────────┘
                        │ click / ⌘K / tap
                        ▼
┌─────────────────────────────────────────────────────┐
│  Depth Transition                                    │
│  Scale up, fade in, slide from bottom                │
└───────────────────────┬─────────────────────────────┘
                        ▼
┌─────────────────────────────────────────────────────┐
│  Content Room                                        │
│  Full page with styled Markdown rendering            │
│  Prev/Next navigation, swipe to exit                 │
└─────────────────────────────────────────────────────┘
```

---

## Command Bar

Press `/` (or `⌘K`) to open natural language navigation:

| Say This | WhiteGlove Does |
|----------|-----------------|
| "pricing" | Navigates to pricing page |
| "how does it work" | Opens architecture |
| "faq" | Jumps to FAQ |
| "security" | Opens security content |

The AI matches your query to content titles and descriptions.

---

## Voice Control

WhiteGlove supports hands-free voice navigation using the browser's built-in Web Speech API.

### Activation

1. Click the **microphone button** (bottom-left corner) to enable voice
2. Say **"Hey WhiteGlove"** — you'll hear a confirmation chime
3. Speak your command (e.g., "open pricing", "show architecture")
4. Watch it navigate and hear the spoken confirmation

### Wake Phrases

- "Hey WhiteGlove"
- "Hey White Glove"  
- "OK WhiteGlove"
- "Okay WhiteGlove"

### One-Shot Commands

You can combine the wake phrase with your command in one breath:

> "Hey WhiteGlove, show me the pricing"

### Voice Indicator States

| State | Appearance |
|-------|------------|
| Off | Gray mic icon |
| Listening | Green outline, waiting for wake word |
| Awake | Pulsing green, ready for command |
| Speaking | Volume icon, TTS playing |

### Technical Notes

- **100% client-side** — Uses browser Web Speech API, no backend calls
- **Zero cost** — No API usage, no quotas
- **Auto-restart** — Recognition continues after each command
- **Browser support** — Chrome, Edge, Safari (requires HTTPS in production)

---

## Project Structure

```
whiteGlove/
├── src/
│   ├── components/
│   │   ├── SpatialView.tsx       # Viewport & transitions
│   │   ├── CommandBar.tsx        # Natural language nav
│   │   └── ui/                   # Aceternity UI effects
│   ├── content/                  # Markdown pages (v2)
│   │   ├── architecture.md
│   │   ├── features.md
│   │   ├── pricing.md
│   │   └── ...
│   ├── context/
│   │   ├── WhiteGloveProvider.tsx
│   │   └── VoiceProvider.tsx       # Voice control & TTS
│   ├── lib/
│   │   ├── content.ts            # MD loader & parser
│   │   └── utils.ts
│   └── pages/
│       ├── V2Page.tsx            # Spatial navigation
│       └── LandingPage.tsx       # Adaptive UX (v1)
├── CONTENT_TEMPLATE.md           # Template for new pages
└── README.md
```

---

## Tech Stack

- **React 18** + TypeScript + Vite
- **Tailwind CSS** + shadcn/ui
- **Framer Motion** — Physics-based animations
- **Aceternity UI** — Spotlight, beams, gradients
- **gray-matter** — Markdown frontmatter parsing
- **react-markdown** — Custom component rendering

---

## Customization

### Theming

Modify colors in `tailwind.config.js`. The purple/pink gradient is the default accent.

### Custom Markdown Components

Edit `SpatialView.tsx` to add custom renderers:

```tsx
components={{
  Banner: ({ children }) => (
    <div className="bg-purple-500/10 p-4 rounded-xl">
      {children}
    </div>
  )
}}
```

### Categories

Create new categories by adding them to your frontmatter. They auto-group in the directory.

---

## Pricing

**WhiteGlove is free and open source** (MIT License).

For AI features (v1 adaptive UX), you need an [AiAssist Secure](https://aiassist.net) API key:
- Free tier available
- BYOK — bring your own provider keys (OpenAI, Anthropic, Groq)
- No inference markup

---

## About

**WhiteGlove** is built by [AiAssist Secure](https://aiassist.net), a product of **INTERCHAINED LLC**.

We believe the web should be spatial, adaptive, and intelligent. WhiteGlove is our contribution to making that vision accessible to everyone.

---

## Links

- [Content Template](./CONTENT_TEMPLATE.md)
- [AiAssist Secure](https://aiassist.net)
- [React SDK Demo](/sdk-test)
- [Core SDK Playground](/core-sdk)

---

Built with AI. Powered by [AiAssist Secure](https://aiassist.net).
