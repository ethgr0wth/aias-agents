# redProxit RADAR 🎯

**AI-powered Reddit intelligence for finding high-intent leads before your competitors do.**

Stop manually scrolling through Reddit hoping to stumble upon potential customers. Radar scans, analyzes, and surfaces the signals that matter - people actively looking for what you build.

---

## The Problem

Every day, thousands of people post on Reddit asking for exactly what you sell:

> "Looking for an AI tool to automate customer support..."  
> "Anyone know a good SaaS for managing invoices?"  
> "Need recommendations for chatbot platforms..."

These are **buying signals**. Real people with real budgets ready to buy. But by the time you find them manually, someone else already DMed them.

## The Solution

Radar finds these signals **in real-time**, analyzes intent using AI, and serves them up Tinder-style for rapid review:

- **Swipe left** → Dismiss, move on
- **Swipe right** → Lock the contact, opens Reddit to engage

No more endless scrolling. No more missed opportunities. Just pure signal, zero noise.

---

## Features

### 🎯 Scope Panel
Configure your targeting before each scan:
- **Subreddits** (optional) - Focus on specific communities or leave empty to search all of Reddit
- **Include Keywords** (required) - What signals you're hunting for
- **Exclude Keywords** - Filter out noise (job postings, hiring, etc.)
- **Limit** - Control result volume (10/25/50/100)

### ⚡ Streaming Results
Signals appear one-by-one as they're analyzed - no waiting for batch processing. Watch your leads populate in real-time with a live progress bar.

### 🤖 AI Intent Analysis
Every post is analyzed for:
- **Intent Score** (0-100) - How likely is this person to buy?
- **Intent Note** - AI's reasoning for the score
- **Confidence** - How sure is the analysis?

High-intent signals bubble to the top. Stop wasting time on tire-kickers.

### 💾 Redis Persistence
All settings and locked contacts persist server-side:
- Credentials stored securely (never in localStorage)
- Locked contacts saved with timestamps
- Scan history preserved across sessions

### 🎴 Tinder-Style Card Interface
Keyboard navigation for power users:
- `←` or `J` to dismiss
- `→` or `K` to contact
- Swipe gestures on mobile

---

## Architecture

```
redProxit/
├── api/                    # FastAPI backend
│   ├── main.py            # Application entry point
│   ├── routes/
│   │   ├── radar.py       # Scan endpoints (POST /scan/stream)
│   │   ├── contacts.py    # Locked contacts CRUD
│   │   └── settings.py    # Credential management
│   └── services/
│       ├── reddit_service.py   # PRAW integration
│       ├── aias_service.py     # LLM intent analysis
│       └── storage_service.py  # Redis persistence
│
└── ui/                     # React + Vite frontend
    ├── src/
    │   ├── App.tsx        # Main application
    │   ├── components/
    │   │   ├── ScopePanel.tsx    # Targeting configuration
    │   │   ├── SignalCard.tsx    # Swipeable signal cards
    │   │   ├── HistoryDrawer.tsx # Locked contacts view
    │   │   └── SettingsModal.tsx # Credential management
    │   ├── hooks/
    │   │   └── useRadar.ts       # Streaming scan logic
    │   └── lib/
    │       ├── api.ts     # API client with SSE support
    │       └── types.ts   # TypeScript interfaces
    └── tailwind.config.js # Radar theme tokens
```

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Redis instance
- Reddit API credentials (optional - works with mock data for testing)
- AiAS endpoint or Groq API key (for intent analysis)

### 1. Start the Backend

```bash
cd redProxit/api
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### 2. Start the Frontend

```bash
cd redProxit/ui
npm install
npm run dev
```

### 3. Configure Credentials

Open the app → Settings (gear icon) → Add your:
- **Reddit credentials** from [reddit.com/prefs/apps](https://reddit.com/prefs/apps)
- **AiAS endpoint** or Groq API key for LLM analysis

That's it. Hit **Scan Now** and start locking leads.

---

## API Reference

### Radar Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/radar/scan/stream` | Stream scan results via SSE |
| `POST` | `/api/radar/scan` | Batch scan (non-streaming fallback) |
| `GET` | `/api/radar/status` | Check Reddit/AiAS connection status |

### Contacts Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/contacts` | List all locked contacts |
| `POST` | `/api/contacts` | Save a locked contact |
| `DELETE` | `/api/contacts/{id}` | Remove a contact |

### Settings Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/settings/reddit` | Get Reddit config status |
| `POST` | `/api/settings/reddit` | Update Reddit credentials |
| `GET` | `/api/settings/aias` | Get AiAS config status |
| `POST` | `/api/settings/aias` | Update AiAS endpoint/key |

---

## Streaming Protocol

Radar uses Server-Sent Events (SSE) for real-time results:

```typescript
// Connection established, scanning begins
{ type: 'start', total: 25 }

// Each signal streamed as analyzed
{ type: 'signal', signal: {...}, progress: 1, total: 25 }
{ type: 'signal', signal: {...}, progress: 2, total: 25 }
// ...continues until complete

// Scan finished
{ type: 'done', total: 25 }
```

The UI updates progressively - you see leads as they're scored, not after a long wait.

---

## Intent Analysis

The AI scores every post on purchase intent:

```json
{
  "intent_score": 85,
  "intent_note": "Actively seeking AI automation tools with stated budget. High purchase intent.",
  "confidence": 0.92
}
```

**What the AI evaluates:**
- **Explicit buying signals** - Budget mentions, timeline, urgency
- **Problem awareness** - Clear pain points your solution addresses
- **Solution seeking** - Actively asking for recommendations
- **Qualification markers** - Business size, decision-making authority

Signals are auto-sorted by intent score. The hottest leads always appear first.

---

## Redis Schema

```
redproxit:settings          # JSON blob of all credentials/config
redproxit:contacts          # Sorted set of locked contacts (by timestamp)
```

Supports up to 1,000 contacts with automatic cleanup of oldest entries when limit is exceeded.

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `REDIS_URL` | Yes | Redis connection string |

All other credentials (Reddit, AiAS) are configured through the UI Settings modal and stored encrypted in Redis - not in environment variables or code.

---

## Why "Radar"?

Because you're not just searching Reddit - you're **detecting signals** in the noise. Like a radar room operator scanning for incoming targets, you're identifying high-intent leads before they hit anyone else's screen.

The green-on-black aesthetic isn't just for looks. It's a mental model: you're in the control room, watching signals appear on your scope, ready to lock and engage.

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `←` or `J` | Dismiss current signal |
| `→` or `K` | Lock contact (opens Reddit) |

Power users can review 50+ signals in under 5 minutes.

---

## Roadmap

- [ ] Scheduled scans with email/Slack/webhook alerts
- [ ] Multi-workspace keyword presets
- [ ] Export locked contacts to CRM (HubSpot, Pipedrive)
- [ ] Chrome extension for inline Reddit scanning
- [ ] Team mode with shared contact pools
- [ ] Historical analytics - conversion tracking

---

## Tech Stack

**Backend:**
- FastAPI (async Python web framework)
- PRAW (Reddit API wrapper)
- Redis (persistence layer)
- Pydantic (validation)

**Frontend:**
- React 18 + TypeScript
- Vite (build tooling)
- Tailwind CSS (styling)
- Framer Motion (animations)

**AI:**
- Groq/OpenAI via AiAS orchestration layer
- Custom intent analysis prompts

---

## Contributing

Found a bug? Have an idea? PRs welcome.

1. Fork the repo
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

MIT License - Build something great with it.

---

## Also Included: Poster (CLI)

The `redProxit.py` CLI tool generates subreddit-appropriate posts using AI:

```bash
python redProxit.py --subreddit selfhosted --context "Launching our new AI tool" --dry-run
```

See `docs/poster.md` for full documentation.

---

<p align="center">
  <strong>Stop scrolling. Start locking.</strong> 🎯
</p>
