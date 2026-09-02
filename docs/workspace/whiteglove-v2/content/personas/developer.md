---
id: developer
title: "Developer Persona"
priority: medium
---

# For Developers

WhiteGlove is built with developers in mind. Full TypeScript support, React hooks-based architecture, and complete control over every mutation.

## Quick Install

```bash
npm install whiteglove
```

## Usage

```tsx
import { WhiteGloveProvider, useWhiteGlove } from 'whiteglove'

function App() {
  return (
    <WhiteGloveProvider config={config}>
      <YourContent />
    </WhiteGloveProvider>
  )
}
```

## API

- `useWhiteGlove()` — Access state and dispatch actions
- `useEventTracker()` — Track custom events
- `configureAiAS()` — Configure LLM endpoint

## Why Developers Love WhiteGlove

- **Type-safe** — Full TypeScript support
- **Zero config** — Works out of the box
- **Extensible** — Override any behavior
- **Open source** — MIT licensed
