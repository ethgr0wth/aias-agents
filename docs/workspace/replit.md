# AiAssist Secure

## Overview
AiAssist Secure is a security-first AI orchestration platform offering a multi-user AI-as-a-Service experience. It features a React frontend and FastAPI Python backend, enabling chat interactions with AI assistants, workspace management, user authentication, and API key management. The platform is evolving into a Bring-Your-Own-Key (BYOK) AI Content Infrastructure Platform, aiming to support multi-tenant blog generation, custom domains, and embeddable widgets.

## User Preferences
Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend
- **Framework**: React with TypeScript, Vite, Tailwind CSS, and shadcn/ui.
- **State Management**: TanStack React Query for server state.
- **Routing**: Wouter.
- **Animations**: Framer Motion.
- **3D Graphics**: React Three Fiber + Drei for cinematic backgrounds.
- **Theme System**: Provider-based context system supporting multiple themes with dark/light modes and persistence.

### Backend
- **Dual Server**: Express.js (reverse proxy, static files) and FastAPI (business logic, authentication, AI orchestration).
- **Real-time**: Socket.IO for chat.
- **Data Storage**: Redis for primary persistence. PostgreSQL schema defined with Drizzle ORM for future migration.
- **Authentication**: Session-based with HTTP-only cookies, supporting multiple user roles and plan types. API key system for programmatic access.
- **AI Integration**: Multi-provider BYOK support (Groq, OpenAI, Anthropic, Gemini, Mistral) with a Python-based AI orchestrator. Supports workspace modes: AI (autonomous), Shadow (AI drafts, human approval), and Takeover (human control).
- **Conversation Memory**: Two-lane system (short-term buffer + session memory in Redis) for context-aware responses with configurable scopes and safety features.
- **API Structure**: Comprehensive REST API for authentication, user management, workspaces, contacts, directives, subscriptions, pricing, and an OpenAI-compatible chat completions endpoint.
- **Programmatic Model Selection**: API requests can specify LLM models, overriding agent defaults.
- **Pricing and Subscription System**: Phase-based, seat-based tiers, integrated with Stripe for checkout and managing subscription lifecycle.
- **Organization-Level Resource Sharing**: API keys and workspaces can be shared within an organization.
- **Secure Tier Encryption (Admin-Blind Messages)**: Double-envelope AES-256-GCM encryption for message content at rest, with per-org Tenant Master Key (TMK) and per-workspace Data Encryption Key (DEK).
- **Quests Builder (KeyStone IDE)**: Full IDE workspace at `/keystone/:id` with 3-panel layout (Files | Monaco Editor | Tabbed Right Panel). Right panel has 4 tabs: Chat (AI assistant with SSE streaming), Terminal (code runner with Python/Node toggle, package installer), Deploy (7-card deployment lifecycle: clone, stack detect, deps, env vars, processes, health checks, export), Ledger (tool invocation feed with auto-refresh and filtering). Integrates AiOS Runtime for execution (auto-creates/reuses runtime session on load). File panel includes search-in-files and Python code analysis tools (functions map, bracket check). Theme-aware with mobile responsive layout (4-tab bottom nav + overflow More menu).
- **Agent Auto-Integration**: Deploys a template into a live agent with ready-to-use code snippets and supports public API targeting specific agents.
- **Provider Dogfooding**: Session tools utilize the user's configured LLM providers.
- **Custom Tooling System v2**: Dual-catalog tool system with Private (org-created) and Public (platform-curated) tools, featuring SSRF-hardened webhook executor, per-provider tool format translation, and encrypted secret storage.
- **FlashCards / Study Buddy (BYOK)**: AI flashcard study at `/flashcards`. Backend at `aias_production_april/api/routes/flashcards.py` — Redis storage (`fc:user:{uid}:decks`, `fc:deck:{id}`, `fc:deck:{id}:cards`, `fc:card:{id}`), SM-2 spaced repetition, multi-choice quiz UX with AI-generated distractors. Calls user's BYOK provider via `X-AiAssist-Provider` / `X-AiAssist-Model` headers, falling back to user's preferred provider. Supports 11 providers (groq, openai, anthropic, gemini, mistral, openrouter, deepseek, together, perplexity, xai, fireworks). 4 deck-creation modes: topic prompt, paste text, upload doc, manual. Endpoints: list/get/create/patch/delete decks, add/edit/delete cards, regenerate distractors, study/next, review (rating: again/hard/good/easy). Frontend: `client/src/pages/FlashCards.tsx` (landing with marquee starter prompts and provider picker) + `client/src/lib/flashcardsApi.ts` (typed API client with localStorage-backed provider/model selection). Linked from Dashboard.tsx desktop+mobile navs and Study Buddy app card below AI Voice; also in MobileDashboard ALL_APPS. Deck editor + study session pages are next-iteration work.

### P2P Inference Network (PIN)
A decentralized Ollama marketplace for LLM inference, featuring:
- **Authentication & Registration**: Operator-level authentication and automatic node registration with multi-node support.
- **API Modes**: Supports `ollama` native API and OpenAI-compatible API modes for diverse inference backends.
- **Interview System**: A per-node quality assurance protocol validating LLMs before production traffic, with dual tracks (Standard for Ollama, Advanced for OpenAI) based on API mode, specific benchmarks, prompts, and performance thresholds.
- **Quality Tiers**: Assigns operators to `verified`, `standard`, `slow`, or `failed` tiers based on accuracy and speed metrics, affecting routing priority.
- **Anti-Gaming Measures**: Randomised prompts, server-side timestamp verification, periodic spot-checks, and anomaly detection.
- **Retry Policy**: Cooldown and attempt limits for failed interviews.

### SaaS-Signal Public API (v1)
A public API providing:
- **Endpoints**: Scan, stream scan, sources, signals, score, enrich, usage, and tools.
- **Authentication**: AiAS API key via Bearer token.
- **Response Envelope**: Standardized JSON response with metadata.
- **LLM Integration**: OpenAI function-calling tool definitions, MCP manifest, and LangChain format support.
- **Sources**: Integration with 22+ public data sources (e.g., Reddit, Twitter, LinkedIn).
- **Intent Categories**: Categorizes signals into various intent types (e.g., buying, evaluating, hiring).

### SDKs
- **TypeScript**: `@redprayers/intelligence` package with typed client, SSE async iterator, and auto-retry.
- **Python**: `redprayers-intelligence` package with sync/async httpx clients, Pydantic v2 models, and SSE streaming generators.

### Agent Runtime Fabric (ARF)
- **Backend**: FastAPI-based session-based sandbox with 22 tools for deployment and safe coding operations.
- **Frontend**: Static HTML/JS/CSS served by FastAPI.
- **Tool Gateway**: Scoped operations for code execution, file system interaction, and deployment tasks, avoiding raw shell access.
- **Policy Engine**: Per-session TTL, max execution time, output size limits, and configurable network modes.
- **Ledger**: Logs all tool invocations.
- **Runtime Zones**: Defined writable and read-only file system zones for session isolation.

## External Dependencies

### Third-Party Services
- **BYOK LLM Providers**: Groq, OpenAI, Anthropic, Gemini, Mistral (user-provided API keys).
- **Redis**: In-memory data store.
- **Google TTS**: Voice synthesis.
- **Stripe**: Payment processing for subscriptions.

### Environment Variables
- `DATABASE_URL` (PostgreSQL)
- `REDIS_URL`
- `SESSION_SECRET`
- `GOOGLE_TTS_CREDENTIALS`
- `STRIPE_WEBHOOK_SECRET`

### AiOS Runtime (Server A / Server B Architecture)
- **Server A** (AiAS API): `api/routes/runtime.py` — mounted at `/api/runtime/*` with dual auth (session cookie or Bearer `aai_` API key). All requests proxy to Server B via `api/services/runtime_proxy.py`. Returns HTTP 503 when `RUNTIME_REMOTE_URL` is not set (no local runtime fallback).
- **Server B** (Standalone): `runtime_server/` — self-contained FastAPI app on port 8099, zero AiAS imports. Runs code execution on a dedicated machine for security/resource isolation.
- **Auth Chain**: Server A authenticates users (JWT/API key + enterprise check) → signs internal request with HMAC-SHA256 rotating key (method+path+body+timestamp+nonce+user_context bound) → Server B validates IP allowlist + HMAC signature (including signed user context) + session ownership.
- **Replay Protection**: 30s request TTL, nonce dedup cache with auto-pruning, signature binds method+path to prevent cross-endpoint replay.
- **Execution Queue**: In-memory backpressure (max concurrent, max queue depth, per-user limits). Overflow returns HTTP 429.
- **Resource Enforcement**: Per-session limits via `setrlimit` — max memory (1024MB), CPU time (30s), disk quota (512MB), process count (10). Checked before spawning processes and writing files.
- **Observability**: Redis-backed (`runtime_b:*` namespace) — per-session/user/org logs, tool counts, latency tracking, error classification. Endpoints: `/health`, `/metrics`, `/logs/session/{id}`, `/logs/user/{id}`.
- **Session Semantics**: All sessions are ephemeral. Lost on Server B restart. Server A is source of truth. TTL defaults to 3600s. Bare git repos are always preserved — never deleted on cleanup, destroy, or force-destroy.
- **Git Factory**: Smart HTTP git server per session (`/git/{session_id}/info/refs`, `/git/{session_id}/git-upload-pack`, `/git/{session_id}/git-receive-pack`). HMAC-secured. Pre-receive hook enforces file/push size limits. Post-receive hook auto-checkouts pushed code and restarts running processes.
- **Session Lifecycle**: Cleanup wipes workspace files, `.venv`, `node_modules`, temp dirs, artifacts — bare repo always stays. Respawn checks out from bare repo instantly. Files live in Keystone (source of truth), Server B is just an ephemeral working copy. +30 min grace period after TTL expiry before session tracking is removed (configurable via `grace_period_seconds` in RuntimePolicy, default 1800s).
- **Environment-Scoped Auto-Checkout**: Sessions accept `environment_id` to scope to a Keystone environment. When a user returns to the same environment, their new session auto-clones the previous session's bare repo and checks out all files instantly. Mapping stored in Redis as `env_last_session:{user_id}:{environment_id}`.
- **Keystone Workspace Sync**: `POST /api/runtime/sync_workspace` on Server A tars up a Keystone environment's file_root (skipping .git, node_modules, __pycache__, venv) and sends the gzip tarball to Server B's `POST /sessions/{id}/sync_workspace`. Server B extracts into workspace and auto-commits to bare repo. This makes Keystone the source of truth for initial workspace state.
- **Activity Tracking**: Tied to Keystone/AiAS activity — page visits, click monitoring, cookie state tracked per session in Redis. As long as user is active (clicking, cookie alive), session stays alive. TTL auto-cleanup enters grace period first, then removes tracking.
- **Admin Session Management**: `GET /admin/sessions` (list all with user/org/disk/process/activity metadata), `DELETE /admin/sessions/{id}` (force destroy), `GET /admin/sessions/stats` (aggregates), `GET /admin/sessions/{id}/activity` (full activity stream). Gated behind super_admin auth on Server A.
- **Tool Gateway**: 23 scoped tools — `run_code` (Python/Node), file I/O, code analysis, deployment tools (clone, deps, processes, health checks).
- **Standalone Dev UI**: `agent_runtime/` on port 3000 — debug cockpit for direct API testing.
- **KeyStone Integration**: QuestsWorkspace.tsx auto-creates/reuses runtime sessions, wires all tools through the Deploy and Terminal tabs, displays ledger feed. Sessions can be scoped to an environment_id for bare repo continuity.
- **Env Vars**: `RUNTIME_REMOTE_URL`, `RUNTIME_SHARED_SECRET`, `RUNTIME_ALLOWED_IPS`, `RUNTIME_KEY_ROTATION_INTERVAL`, `RUNTIME_MAX_CONCURRENT`, `RUNTIME_MAX_QUEUE_DEPTH`, `RUNTIME_MAX_PER_USER`, `RUNTIME_SESSION_TTL`, `RUNTIME_CLEANUP_INTERVAL`

### whoami.com.co
A standalone open identity platform — "linkinbio + GitHub for the AI web."
- **Directory**: `whoami/`
- **Frontend**: React + TypeScript + Vite + Tailwind CSS on port 3000. Wouter routing. Pages: Landing, Discover, ProfilePage, Create, About.
- **Backend**: Express.js API on port 3001. Redis for all data persistence. Profiles stored as JSON objects keyed by slug (`whoami:profile:{slug}`), slug index in a Redis set (`whoami:profiles:index`). Seed data auto-loaded on first boot.
- **API Routes**: `GET /api/profiles` (list/search/filter), `GET /api/profiles/:slug` (single), `POST /api/profiles` (create), `PUT /api/profiles/:slug` (update), `DELETE /api/profiles/:slug` (delete), `GET /api/profiles/:slug/profile.json` (structured export with Schema.org), `GET /api/profiles/:slug/profile.md` (markdown), `GET /api/profiles/:slug/llms.txt` (LLM-readable), `GET /api/health`.
- **Auth**: Passkey-based (WebAuthn) — 1 profile per passkey per device. (Stubbed in frontend, not yet wired to real WebAuthn.)
- **Profile Types**: person, company, project, organization, publication, agent, community, event.
- **Product Rules**: No social features, no posts, no chat, no seeding. Create-only model. Redis-only storage.
- **Workflow**: `whoami` — runs `bash start.sh` which starts both API (tsx) and Vite dev server.
- **Port**: 3000 (webview), 3001 (API, proxied via Vite).