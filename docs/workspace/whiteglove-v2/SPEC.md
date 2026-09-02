# WhiteGlove

> An Agentic UX Framework - AI-powered adaptive websites that respond to human intent in real-time.

## Vision

WhiteGlove is an open-source React framework that creates websites which adapt their content and styling based on user behavior. Powered by AI inference through [AiAS (AiAssist Secure)](https://aiassist.net), it watches how users interact and dynamically personalizes the experience.

**The hook for developers:**
> "Drop this on your landing page. It watches how users behave and adapts in real-time using AI. Free, open source, bring your own LLM key."

**Distribution strategy:**
```
GitHub stars → Clone/Fork → Need AiAS API key → Sign up → Credits
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      FRONTEND (React + Vite)                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  /content/*.md        Markdown Knowledge Base                   │
│  ├── hero.md          (content variants, personas, messaging)  │
│  ├── features.md                                                │
│  ├── pricing.md                                                 │
│  └── personas/                                                  │
│                                                                 │
│  EventTracker         Captures browser events                   │
│  ├── scroll depth                                               │
│  ├── click patterns                                             │
│  ├── hover duration                                             │
│  ├── dwell time                                                 │
│  └── rage clicks                                                │
│                                                                 │
│  IntentEngine         Batches events → AiAS inference           │
│  MutationEngine       Applies CSS/content mutations             │
│  ContentRenderer      Parses markdown → React components        │
│                                                                 │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              │ POST /v1/chat/completions
                              │ (OpenAI-compatible API)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        AiAS BACKEND                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  BYOK LLM Routing     Groq / OpenAI / Anthropic / Gemini       │
│  Credits Tracking     Usage-based billing                       │
│  API Key Auth         aai_xxx prefixed keys                     │
│                                                                 │
│  Endpoint: https://aiassist.net/api/v1/chat/completions        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Components

| Component | Purpose | Key Features |
|-----------|---------|--------------|
| **EventTracker** | Hooks into DOM events | scroll, click, hover, dwell, rage-click, exit-intent |
| **IntentEngine** | AI inference layer | Debounces events, builds context, calls AiAS |
| **MutationEngine** | Applies AI decisions | CSS vars, class swaps, show/hide, content priority |
| **ContentRenderer** | Markdown → React | Frontmatter parsing, variant support, mutation targets |
| **ConfigProvider** | Global settings | API key, thresholds, mutation rules, debug mode |
| **CommandBar** | Prompt navigation | Natural language site navigation, intent expression |

---

## Prompt-Based Navigation

Instead of traditional menu links, users navigate via natural language:

### Command Bar
A subtle, always-accessible input (like Spotlight/Raycast) where users type what they want:

```
┌─────────────────────────────────────────────────────┐
│  🔍  "Show me pricing for startups"                │
└─────────────────────────────────────────────────────┘
```

### Example Commands
| User Says | AI Does |
|-----------|---------|
| "Show me pricing" | Scrolls to pricing, highlights it |
| "I'm a developer" | Loads developer persona content, reorders features |
| "What makes you different?" | Surfaces differentiators, comparison section |
| "I have security questions" | Jumps to FAQ, filters to security-related Q&As |
| "Make this simpler" | Collapses detailed sections, shows summaries |
| "I'm ready to sign up" | Scrolls to CTA, applies urgency styling |

### Implementation
The CommandBar sends user input to AiAS with page context:

```json
{
  "role": "user",
  "content": {
    "command": "Show me pricing for startups",
    "availableSections": ["hero", "features", "pricing", "testimonials", "faq"],
    "availablePersonas": ["developer", "founder", "enterprise"],
    "currentState": { "visibleSections": [...], "scrollPosition": 0.3 }
  }
}
```

Response includes navigation + mutations:
```json
{
  "navigation": {
    "scrollTo": "pricing",
    "highlight": true
  },
  "mutations": {
    "prioritize": "personas/founder",
    "css": { "--pricing-emphasis": "startup-tier" }
  }
}
```

---

## Constrained Style Mutations (LLM Safety)

To prevent Llama (or any LLM) from breaking layouts with hallucinated CSS, mutations are **constrained to predefined options**.

### The Problem
Unconstrained LLM output could produce:
```css
/* Dangerous - LLM might hallucinate this */
background: url('javascript:alert(1)');
font-size: 9999px;
position: fixed; top: -1000px;
```

### The Solution: Allowlists
Each markdown file defines what CSS variables can be mutated and their valid values:

```yaml
---
id: hero
mutations:
  css_vars:
    --hero-size: 
      - default
      - compact  
      - expanded
    --cta-color:
      - "#3b82f6"   # blue (default)
      - "#ef4444"   # red (urgency)
      - "#10b981"   # green (success)
    --urgency-mode:
      - "off"
      - "soft"      # subtle pulse
      - "strong"    # bold animation
  content_variants:
    headline:
      - default: "Build faster with AI"
      - social_proof: "Join 500+ teams using AiAS"
      - urgency: "Limited time: 50% off"
---
```

### Validation Flow
```
LLM Response                    Validator                      DOM
     │                              │                            │
     │  --cta-color: "#ef4444"     │                            │
     ├─────────────────────────────►│                            │
     │                              │ ✅ In allowlist            │
     │                              ├───────────────────────────►│ Applied
     │                              │                            │
     │  --cta-color: "red"         │                            │
     ├─────────────────────────────►│                            │
     │                              │ ❌ Not in allowlist        │
     │                              │    Use default             │
     │                              ├───────────────────────────►│ Fallback
```

### Benefits
1. **Safe** - LLM can't inject arbitrary CSS or break layouts
2. **Predictable** - You control exactly what can change
3. **Fast** - Validation is a simple lookup, no parsing
4. **Designer-friendly** - Design system stays intact

### Config Example
```javascript
// whiteglove.config.js
export default {
  mutations: {
    validateCss: true,        // Enforce allowlists
    fallbackOnInvalid: true,  // Use defaults if LLM hallucinates
    logRejections: true,      // Debug mode: log rejected mutations
  }
}
```

---

## Event → Mutation Flow

### 1. Capture
User interacts with the page:
- Scrolls 70% down
- Hovers on pricing for 3 seconds
- Clicks FAQ twice
- Mouse moves toward browser close button (exit intent)

### 2. Batch
Every 2-3 seconds, EventTracker bundles signals:
```javascript
{
  sessionId: "abc123",
  timestamp: 1706123456789,
  events: [
    { type: "scroll", depth: 0.7, velocity: "slow" },
    { type: "hover", target: "pricing", duration: 3000 },
    { type: "click", target: "faq", count: 2 },
    { type: "exit_intent", triggered: true }
  ],
  currentState: {
    visibleSections: ["hero", "features", "pricing"],
    hiddenSections: ["testimonials"],
    activePersona: null,
    timeOnPage: 45000
  }
}
```

### 3. Infer
IntentEngine sends to AiAS:
```json
POST /v1/chat/completions
{
  "model": "llama-3.3-70b-versatile",
  "messages": [
    {
      "role": "system",
      "content": "You are a UX agent. Analyze user behavior and return JSON mutations to personalize their experience. Available content: [hero, features, pricing, testimonials, faq, personas/developer, personas/founder, personas/enterprise]. Respond ONLY with valid JSON."
    },
    {
      "role": "user", 
      "content": "{events: [...], currentState: {...}}"
    }
  ],
  "response_format": { "type": "json_object" }
}
```

### 4. Mutate
AiAS returns mutation instructions:
```json
{
  "reasoning": "User showing exit intent after hovering on pricing - likely price-sensitive. Surface social proof to build trust.",
  "mutations": {
    "show": ["testimonials"],
    "hide": [],
    "prioritize": "personas/founder",
    "reorder": ["testimonials", "pricing", "features"],
    "css": {
      "--cta-urgency": "true",
      "--hero-variant": "social-proof"
    },
    "content": {
      "hero.headline": "Join 500+ founders who switched to AiAS",
      "cta.text": "Start Free Trial"
    }
  }
}
```

### 5. Apply
MutationEngine updates the DOM:
- Injects CSS custom properties
- Shows/hides sections with smooth transitions
- Swaps content variants
- Reorders sections based on priority

---

## Markdown Knowledge Base

### Directory Structure
```
/content
  ├── _config.yaml              # Site metadata, section order, defaults
  ├── hero.md                   # Hero section with variants
  ├── features.md               # Feature blocks
  ├── pricing.md                # Pricing tiers
  ├── testimonials.md           # Social proof
  ├── faq.md                    # Q&A pairs
  ├── cta.md                    # Call-to-action variants
  └── personas/
       ├── developer.md         # Developer-focused messaging
       ├── founder.md           # Founder/startup messaging
       └── enterprise.md        # Enterprise messaging
```

### Frontmatter Schema
Each markdown file includes AI-readable metadata:

```yaml
---
id: pricing
title: "Pricing"
priority: high
triggers:
  - scroll_to_pricing
  - click_pricing_link
  - referrer_contains_pricing
variants:
  default:
    headline: "Simple, transparent pricing"
    subheadline: "No hidden fees. Cancel anytime."
  urgency:
    headline: "Prices increase February 1st"
    subheadline: "Lock in your rate today"
  social_proof:
    headline: "Trusted by 500+ companies"
    subheadline: "See why teams choose AiAS"
mutations:
  allow_hide: false
  allow_reorder: true
  css_targets:
    - --pricing-highlight
    - --tier-emphasis
---

## Starter
$0/month
- 1,000 credits
- Community support

## Pro  
$29/month
- 50,000 credits
- Priority support
- Custom agents
```

---

## AiAS Integration

### Authentication
Users need an AiAS API key to use WhiteGlove:

```javascript
// whiteglove.config.js
export default {
  aias: {
    apiKey: process.env.AIAS_API_KEY, // aai_xxx
    endpoint: "https://aiassist.net/api/v1/chat/completions",
    model: "llama-3.3-70b-versatile", // or user's preferred model
  },
  events: {
    debounceMs: 2000,
    batchSize: 10,
  },
  mutations: {
    transitionMs: 300,
    debugMode: false,
  }
}
```

### Getting an API Key
1. Sign up at [aiassist.net](https://aiassist.net)
2. Navigate to Settings → API Keys
3. Create a new key (prefixed with `aai_`)
4. Add credits to your account
5. Configure WhiteGlove with your key

### Credit Usage
Each AI inference call uses credits based on the LLM model:
- Groq (Llama 3.3 70B): ~0.001 credits per call
- OpenAI (GPT-4): ~0.01 credits per call
- Anthropic (Claude): ~0.01 credits per call

Typical usage: 5-10 inference calls per user session = minimal credit usage.

---

## CommandBar Onboarding Flow

Since prompt-based navigation is unconventional, we guide users into it progressively:

### 1. Passive Hints
Subtle animated placeholder text cycles through example commands:
```
🔍  Try: "Show me pricing" ...
🔍  Try: "I'm a developer" ...
🔍  Try: "What makes you different?" ...
```

### 2. Contextual Nudges
After 10 seconds of scrolling without interaction, a soft tooltip appears:
```
┌─────────────────────────────────────────┐
│  💡 Looking for something specific?    │
│     Just ask in the command bar →      │
└─────────────────────────────────────────┘
```

### 3. Quick Action Buttons
Pre-filled suggestion chips below the CommandBar (training wheels):
```
[ 💰 Pricing ] [ 👩‍💻 I'm a developer ] [ ❓ How it works ]
```
Clicking a chip = simulates typing that command. Instant gratification.

### 4. First Interaction Reward
When they type anything:
- Page visibly adapts (smooth transitions)
- Subtle success animation on CommandBar
- Optional: "✨ Page adapted to your request" toast

### 5. Progressive Confidence
After 2-3 successful interactions:
- Hide the quick action chips
- Reduce hint frequency
- They've learned the pattern

**Goal:** Show them the magic before asking them to perform it.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Framework | React 18+ with Vite |
| Styling | **Tailwind CSS + Aceternity UI** (glassmorphism, 3D effects, parallax) |
| Animation | Framer Motion (spring physics, smooth transitions) |
| Markdown | react-markdown with gray-matter (frontmatter parsing) |
| State | React Context + useReducer |
| HTTP | Fetch API (no heavy deps) |
| Build | Vite with static export option |

### Aceternity UI Components
Premium visual effects out of the box:
- **3D Cards** - Tilt on hover with depth
- **Spotlight** - Cursor-following gradient glow
- **Background Beams** - Animated light rays
- **Floating Navbar** - Glassmorphism header
- **Text Generate Effect** - Typewriter with fade
- **Bento Grid** - Modern card layouts
- **Meteors** - Particle effects for CTAs

---

## MVP Scope

### Phase 1: Core (Initial Release)
- [ ] React + Vite + Tailwind scaffold
- [ ] EventTracker hook (scroll, click, hover, dwell)
- [ ] ContentRenderer (markdown with frontmatter)
- [ ] IntentEngine (AiAS integration)
- [ ] MutationEngine (CSS vars, show/hide)
- [ ] Demo landing page (AiAS marketing content)
- [ ] README with setup instructions

### Phase 2: Polish
- [ ] Streaming responses for smoother UX
- [ ] "Watch Me Adapt" debug mode (shows AI reasoning)
- [ ] More event types (exit intent, tab blur, rage clicks)
- [ ] Analytics hooks (what mutations convert)
- [ ] Preset themes/layouts

### Phase 3: Ecosystem
- [ ] npm package for easy integration
- [ ] CLI scaffolding tool
- [ ] Headless mode (bring your own components)
- [ ] A/B testing integration
- [ ] Webhook notifications

---

## Demo Experience

The WhiteGlove demo page will showcase:

1. **Live Adaptation** - As users browse, the page visibly adapts
2. **Debug Panel** - Toggle to see AI reasoning in real-time
3. **Event Feed** - Shows what behaviors are being tracked
4. **Mutation Log** - Shows what changes the AI made and why
5. **AiAS Pitch** - Naturally leads to signing up for AiAS

---

## File Structure

```
whiteGlove/
├── SPEC.md                     # This document
├── README.md                   # Setup and usage guide
├── package.json
├── vite.config.ts
├── tailwind.config.js
├── tsconfig.json
├── index.html
├── public/
│   └── favicon.svg
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── config.ts               # WhiteGlove configuration
│   ├── components/
│   │   ├── Layout.tsx
│   │   ├── Section.tsx
│   │   └── DebugPanel.tsx
│   ├── hooks/
│   │   ├── useEventTracker.ts
│   │   ├── useIntentEngine.ts
│   │   └── useMutationEngine.ts
│   ├── lib/
│   │   ├── contentLoader.ts
│   │   ├── aiasClient.ts
│   │   └── types.ts
│   ├── context/
│   │   └── WhiteGloveProvider.tsx
│   └── styles/
│       └── globals.css
└── content/
    ├── _config.yaml
    ├── hero.md
    ├── features.md
    ├── pricing.md
    ├── testimonials.md
    ├── faq.md
    └── personas/
        ├── developer.md
        ├── founder.md
        └── enterprise.md
```

---

## Design Philosophy

### For Users
- **Invisible magic** - Adaptation feels natural, not creepy
- **Respectful** - No dark patterns, just helpful personalization
- **Fast** - Mutations are smooth, never jarring
- **Private** - All behavior analysis happens via their own API key

### For Developers
- **Zero config to start** - Works out of the box
- **Infinitely customizable** - Override anything
- **Markdown-first** - Content updates need no code
- **Type-safe** - Full TypeScript support

### For AiAS
- **Distribution channel** - Every deployment drives signups
- **Credit usage** - Sustainable business model
- **Showcase** - Demonstrates AiAS capabilities in production

---

## Open Questions

1. **Offline fallback** - What happens when AiAS is unreachable?
2. **Rate limiting** - How to prevent abuse of inference calls?
3. **Caching** - Should we cache mutation decisions?
4. **Privacy** - How to handle GDPR/cookie consent for tracking?
5. **SEO** - How to ensure adaptive content is still crawlable?

---

## Success Metrics

- GitHub stars
- Forks/clones
- AiAS signups attributed to WhiteGlove
- Credit usage from WhiteGlove deployments
- Community contributions

---

*Built with AI. Powered by [AiAS](https://aiassist.net).*
