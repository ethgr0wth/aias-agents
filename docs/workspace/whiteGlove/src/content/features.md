---
title: Core Features
icon: Sparkles
description: What WhiteGlove does
category: Getting Started
order: 3
---

## Agentic UX Framework

WhiteGlove is more than a component library — it's an **AI-powered experience engine** that adapts to user intent in real-time.

> "Websites that listen, understand, and respond."

---

## Intelligent Event Tracking

Automatically capture user behavior without manual instrumentation:

| Event Type | What We Track | Why It Matters |
|------------|---------------|----------------|
| **Scroll Depth** | How far users scroll | Measures content engagement |
| **Click Patterns** | What users interact with | Reveals interest areas |
| **Hover Behavior** | What catches attention | Pre-click intent signals |
| **Dwell Time** | Where users pause | Deep engagement indicator |
| **Exit Intent** | When users are leaving | Last chance to convert |

All events are batched and processed locally before sending to the AI engine — no performance impact.

---

## AI Intent Engine

The LLM-powered brain that interprets behavior patterns and generates insights:

### How It Works

1. **Collect** — Events stream into a local buffer
2. **Batch** — Events are grouped into meaningful sessions
3. **Analyze** — LLM processes patterns and context
4. **Infer** — Intent classification with confidence scores
5. **Act** — Suggested mutations or direct actions

### Intent Categories

- **Curious** — Browsing, exploring, gathering information
- **Interested** — Reading deeply, comparing options
- **Ready** — Showing buying signals, seeking next steps
- **Confused** — Backtracking, re-reading, searching
- **Leaving** — Exit intent detected, disengagement

---

## Dynamic Mutations

Safe, constrained changes that adapt your site without breaking layouts:

### Mutation Types

| Mutation | Description | Use Case |
|----------|-------------|----------|
| `show_section` | Reveal hidden content | Show testimonials to interested users |
| `hide_section` | Collapse distracting content | Remove noise for focused users |
| `highlight` | Draw attention to element | Emphasize CTAs for ready users |
| `update_text` | Change copy dynamically | Personalize messaging |
| `trigger_modal` | Show contextual popup | Exit intent capture |
| `scroll_to` | Navigate to section | Guide confused users |

### Safety Guarantees

- Mutations are **reversible** — undo any change instantly
- Mutations are **constrained** — only predefined actions allowed
- Mutations are **logged** — full audit trail for debugging

---

## Natural Language Navigation

Users tell your site what they want via the `⌘K` command bar:

### Example Commands

- *"Show me pricing"* → Navigates to pricing content
- *"How does security work?"* → Opens architecture section
- *"I have questions"* → Jumps to FAQ
- *"Take me back"* → Returns to directory

The AI interprets natural language and maps to your content structure automatically.

---

## Engagement Scoring

Real-time scoring system that tracks user journey state:

```
Score: 0-20   → Browsing (cold)
Score: 21-50  → Curious (warming)
Score: 51-80  → Interested (hot)
Score: 81-100 → Ready to convert
```

Scores update based on:
- Time on page
- Scroll depth
- Interaction count
- Content focus areas
- Return visits

---

## Developer Experience

### Simple Integration

```tsx
import { WhiteGloveProvider, EngagementTracker } from '@whiteglove/react'

function App() {
  return (
    <WhiteGloveProvider>
      <EngagementTracker />
      <YourApp />
    </WhiteGloveProvider>
  )
}
```

### Event Hooks

```tsx
const { state, trackEvent, triggerMutation } = useWhiteGlove()

// Manual event tracking
trackEvent({ type: 'button_click', target: 'cta-primary' })

// Check engagement state
if (state.engagementScore > 80) {
  triggerMutation('show_section', 'social-proof')
}
```

### Full TypeScript Support

Every hook, component, and config option is fully typed. Get autocomplete and type safety out of the box.
