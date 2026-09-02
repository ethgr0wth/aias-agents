# AGENTS.md — AiAssist Secure Platform Guide

> Comprehensive reference for AI agents and collaborators working on this codebase

**Last Updated:** January 2026

---

## Executive Summary

AiAssist Secure is a **BYOK (Bring Your Own Key) AI platform** that enables businesses to safely deploy AI across multiple use cases. Users bring their own LLM API keys (OpenAI, Anthropic, Groq, etc.), and the platform provides security, orchestration, and production-hardening layers.

**Core Philosophy:** Users control their AI costs and data. Billing-linked API keys never touch client-side code.

---

## Platform Architecture

### Technology Stack

| Layer | Technology |
|-------|------------|
| Frontend | React + TypeScript + Vite + TailwindCSS + shadcn/ui |
| Backend | Express.js (proxy, port 5000) → FastAPI (business logic, port 8000) |
| Storage | Redis (primary) + PostgreSQL (schema/future migrations) |
| Real-time | Socket.IO via `/socket.io` endpoint |
| Auth | Session-based (HTTP-only cookies, 7-day expiry) |

### Key Directories

```
├── api/                      # FastAPI backend
│   ├── routes/               # API endpoints
│   ├── services/             # Business logic (ai_orchestrator, redis_storage, etc.)
│   ├── providers/            # LLM provider adapters (config.py has all 11)
│   └── models/schemas.py     # Pydantic models
├── client/src/               # React frontend
│   ├── pages/                # Route pages (Dashboard, QuestsWorkspace, etc.)
│   ├── components/           # Reusable UI components
│   └── hooks/                # Custom React hooks
├── server/                   # Express.js proxy
├── shared/                   # Shared types (schema.ts for Drizzle)
├── docs/                     # Design specifications (24+ docs)
└── data/quests/              # App Builder file storage (org-scoped)
```

---

## Major Subsystems

### 1. Multi-Provider AI Infrastructure

**Files:** `api/providers/config.py`, `api/services/ai_orchestrator.py`, `api/routes/public_api.py`

11 supported LLM providers:
- **Tier 1 (Launch):** Groq, OpenAI, Anthropic, Google Gemini, Mistral
- **Tier 2:** xAI (Grok), Together AI, OpenRouter, DeepSeek, Fireworks, Perplexity

**Provider Priority Chain:**
1. Request-level `model` parameter override
2. Agent/workspace default model
3. User's first configured provider's default
4. Ultimate fallback: Groq llama-3.3-70b

**Dynamic Model Lists:** Cached every 6 hours via provider `/models` endpoints.

**See:** `docs/multi-provider-integration.md` (1171 lines)

---

### 2. App Builder (Quests Integration)

**Files:** `api/routes/quests.py`, `api/services/quests_service.py`, `client/src/pages/QuestsWorkspace.tsx`

AI-assisted app development environments embedded within AiAssist:
- Organization-scoped file isolation at `/data/quests/{org_id}/{env_id}/`
- **No runtime execution** (`RUNTIME_DISABLED = True`) — AI generates/edits files only
- Path-based preview routing (not subdomains)
- Environment limits by plan: Free=5, Basic=10, Pro=50, Enterprise=1000

**Security Guardrails:**
- 50MB file limit, blocks .exe/.dll/.sh/.bat
- AI moderation blocks malware/exploit patterns
- Rate limiting: 30 chat/min, 100 file ops/min, 1 env/hour create

**Critical Fix (Jan 2026):** AI now reads file content before editing via `_extract_file_references()` and `_read_files_for_context()`. Without this, AI outputs placeholder comments instead of code.

**See:** `docs/quests-integration-workplan.md` (489 lines)

---

### 3. Shadow Mode (Enterprise)

**Files:** `api/services/ai_orchestrator.py`, `client/src/pages/Dashboard.tsx` (PendingDraftsQueue)

Human-in-the-loop AI responses:
1. User sends message
2. AI generates draft (not visible to user)
3. Manager reviews via dashboard
4. Approve/Edit/Regenerate/Reject
5. Approved response delivered to user

**Message Schema Extensions:**
- `pending_approval`, `approved_at`, `approved_by`
- `draft_original`, `human_edited`, `regenerate_directive`

**API Endpoints:** `GET /api/workspaces/drafts/pending`, `POST /api/workspaces/drafts/{id}/approve|reject|regenerate`

**See:** `docs/shadow-mode-specification.md` (420 lines)

---

### 4. Conversation Memory

**Files:** `api/services/conversation_memory.py`, integrated in `ai_orchestrator.py`

Two-lane architecture (no embeddings):
- **Short-Term Buffer:** Last 20 turns injected verbatim
- **Session Memory:** Extracted facts stored in Redis per session

**Prompt Assembly Order:**
1. System directives
2. Session memory facts
3. Short-term buffer
4. User question

**Memory Scopes:** USER, WORKSPACE, CONVERSATION, LEAD

**Safety:** Circuit breaker (5 failures, 60s reset), kill-switch, PII filtering, 0.75 confidence threshold

**See:** `docs/conversation-memory-architecture.md` (1888 lines)

---

### 5. Licensing & Subscriptions

**Files:** `api/routes/licenses.py`, `api/services/redis_storage.py`

**Licensing Features:**
- Seat-based subscriptions with configurable durations
- Batch generation for reseller distribution
- Organization and team structures
- License keys: `LIC-XXXX-XXXX-XXXX` format

**Subscription Lifecycle:**
```
PENDING → ACTIVE → WARNING (7d before expiry) → GRACE (7d after) → EXPIRED
```

**State Sync:** Atomic updates across subscription, license, organization, seats, and user entitlements.

**Stripe Integration:** Webhook handler with idempotency. Requires `STRIPE_WEBHOOK_SECRET`.

**See:** `docs/licensing-system.md` (579 lines), `docs/subscription-system.md` (1189 lines)

---

### 6. Reseller Program

**Files:** `api/routes/reseller.py`, `client/src/pages/ResellerPortal.tsx`

Partners earn revenue by referring customers:
- **Tiers:** Starter (5%), Growth (10%), Elite (20%) revenue share
- **Quotas:** Ramp from 1/month to 6-10/month over 12 months
- **30-Day Payout:** Credit after customer's first renewal
- **Admin-Blind:** Resellers cannot see client data

**See:** `docs/reseller-program-workplan.md` (553 lines)

---

### 7. BYOK Blog Platform (Roadmap)

**Status:** Design specification, not fully implemented

Multi-tenant AI-powered content generation:
- Custom domains (blog.company.com)
- Brand voice engine
- Embeddable widgets
- SEO management

**See:** `docs/byok-blog-platform-workplan.md` (854 lines)

---

### 8. Voice Synthesis & Web Search

**Voice (Google TTS):**
- Platform credentials or BYOK Google Cloud service account
- Wavenet & Chirp protocols
- Per-protocol usage tracking

**Web Search:**
- Tavily (primary) + DuckDuckGo (fallback)
- Query hygiene: blocks secrets/PII
- Evidence layer with [SRC-###] citations

**See:** `docs/ai-voice-playground-spec.md`, `docs/web-search-tool-specification.md`

---

### 9. Enterprise E2EE Architecture

True end-to-end encryption for HIPAA/FedRAMP compliance:
- Platform **never** sees plaintext (client-mediated AI calls)
- BYOK API keys only
- Customer-controlled key management

**See:** `docs/enterprise-e2ee-architecture.md` (573 lines)

---

## API Reference Summary

### Public API (OpenAI-Compatible)

| Endpoint | Purpose |
|----------|---------|
| `POST /v1/chat/completions` | Chat completions (main public API) |
| `GET /v1/agents` | List deployed agents |
| `POST /v1/agents/{id}/chat` | Chat with specific agent |

**Auth:** `Authorization: Bearer aai_xxxxx`

### Internal APIs

| Prefix | Purpose |
|--------|---------|
| `/api/auth/*` | Login, logout, session |
| `/api/user/*` | Profile, API keys, provider settings |
| `/api/workspaces/*` | Workspace CRUD, messaging |
| `/api/directives/*` | AI behavior customization |
| `/api/quests/*` | App Builder environments, files, chat |
| `/api/admin/*` | Admin-only endpoints |
| `/api/licenses/*` | License activation, management |
| `/api/subscription/*` | Subscription status, cancel, reactivate |
| `/api/billing/checkout` | Create Stripe checkout |
| `/api/tts/*` | Voice synthesis |

**See:** `DEVELOPERS.md` (1168 lines) for complete reference

---

## Redis Key Patterns

All keys use namespace prefix (default: `aai:`):

| Pattern | Purpose |
|---------|---------|
| `aai:users:{id}` | User records |
| `aai:sessions:{token}` | Session data |
| `aai:workspaces:{id}` | Workspace config |
| `aai:workspace:{id}:messages` | Message sorted set |
| `aai:licenses:{id}` | License records |
| `aai:orgs:{id}` | Organization records |
| `aai:user_providers:{user_id}` | BYOK provider credentials |
| `aai:quests:env:{id}` | App Builder environments |
| `aai:provider_models:{provider}` | Cached model lists |

---

## User Roles & Permissions

| Role | Capabilities |
|------|--------------|
| `client` | Standard user, API access based on plan |
| `reseller` | Client + referral tracking + reseller portal |
| `manager` | Shadow mode approval, team management |
| `super_admin` | Full platform access, admin endpoints |

---

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | PostgreSQL connection (Drizzle) |
| `REDIS_URL` | Redis connection (default: localhost:6379/12) |
| `SESSION_SECRET` | Session encryption key |
| `GOOGLE_TTS_CREDENTIALS` | Platform TTS credentials (JSON) |
| `STRIPE_SECRET_KEY` | Stripe API key |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook verification |
| `GROQ_API_KEY` | Platform default Groq key (optional) |

---

## Common Agent Tasks

### Adding a New LLM Provider

1. Add to `ProviderType` enum in `api/models/schemas.py`
2. Add config in `api/providers/config.py` (base URL, auth header, default models)
3. Update frontend provider settings UI
4. Add to `DEVELOPERS.md` documentation

### Modifying App Builder AI Behavior

Key file: `api/services/quests_service.py`

- `_extract_file_references()` — Detects files mentioned in prompts
- `_read_files_for_context()` — Reads files to include in AI context
- Tool definitions in `CHAT_SYSTEM_PROMPT`

**Critical:** Always include file content in AI context for edit operations.

### Adding a Dashboard Feature

1. Add route in `client/src/App.tsx`
2. Create page in `client/src/pages/`
3. Add navigation link in Dashboard.tsx (both mobile and desktop nav)
4. Gate by plan/role if needed

### Extending Message Schema

1. Update `Message` class in `api/models/schemas.py`
2. Update Redis storage serialization in `redis_storage.py`
3. Update any affected WebSocket events

---

## Testing Considerations

- **No runtime execution** in App Builder — test file generation, not code execution
- Redis is required for all backend tests
- Frontend uses React Query — mock API responses
- Shadow Mode needs manager role to test approval flow
- License tests need batch generation capability

---

## Documentation Index

| Document | Lines | Purpose |
|----------|-------|---------|
| `docs/quests-integration-workplan.md` | 489 | App Builder design |
| `docs/shadow-mode-specification.md` | 420 | Human-in-the-loop AI |
| `docs/conversation-memory-architecture.md` | 1888 | Memory system design |
| `docs/licensing-system.md` | 579 | License data model |
| `docs/subscription-system.md` | 1189 | Subscription lifecycle |
| `docs/reseller-program-workplan.md` | 553 | Partner program |
| `docs/multi-provider-integration.md` | 1171 | BYOK providers |
| `docs/byok-blog-platform-workplan.md` | 854 | Blog platform roadmap |
| `docs/enterprise-e2ee-architecture.md` | 573 | Enterprise encryption |
| `docs/web-search-tool-specification.md` | 512 | Search integration |
| `docs/ai-voice-playground-spec.md` | 422 | Voice synthesis |
| `docs/wordpress-plugin-documentation.md` | 428 | WP plugin guide |
| `DEVELOPERS.md` | 1168 | Public API reference |
| `replit.md` | — | Project state summary |

---

## Known Issues & Recent Fixes

| Issue | Status | Notes |
|-------|--------|-------|
| App Builder AI outputs placeholder comments | ✅ Fixed | AI now reads file content before editing |
| License expiration blocks new key entry | ✅ Fixed | Form shows when `is_active=false` |
| App Builder link on public Home page | ✅ Fixed | Moved to Dashboard only (subscriber-gated) |

---

## Platform Evolution Timeline

- **Dec 2024:** Conversation memory architecture
- **Dec 2025:** Multi-provider BYOK (11 providers), Shadow Mode, Licensing System
- **Jan 2026:** App Builder (Quests) integration, Reseller Program, Enterprise E2EE design
- **Roadmap:** BYOK Blog Platform, WordPress Plugin, Mobile (Capacitor)

---

## Agent Best Practices

1. **Read before editing** — Always use grep/read to understand context before modifying code
2. **Check docs first** — Most features have detailed specs in `docs/`
3. **Preserve existing patterns** — Match code style, use existing utilities
4. **Test auth flows** — Many endpoints require specific roles
5. **Update replit.md** — Keep the project state summary current
6. **Redis is truth** — PostgreSQL is for schema/migrations, Redis is live data
