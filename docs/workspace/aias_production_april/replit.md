# AiAssist Secure

## Overview
AiAssist Secure is a security-first AI orchestration platform offering a multi-user AI-as-a-Service experience. It features a React frontend and FastAPI Python backend, enabling chat interactions with AI assistants, workspace management, user authentication, and API key management. The platform is evolving into a Bring-Your-Own-Key (BYOK) AI Content Infrastructure Platform, aiming to support multi-tenant blog generation, custom domains, and embeddable widgets.

## User Preferences
Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend
- **Framework**: React with TypeScript, Vite, Tailwind CSS, and shadcn/ui (New York style).
- **State Management**: TanStack React Query for server state.
- **Routing**: Wouter.
- **Animations**: Framer Motion.
- **3D Graphics**: React Three Fiber + Drei for cinematic backgrounds.
- **Theme System**: Provider-based context system (`client/src/themes/`) supporting multiple themes (Malachi, Athena, Yvette, Patriot) with dark/light modes and persistence via localStorage. Themes feature advanced 3D animations and particle effects.

### Backend
- **Dual Server**: Express.js (reverse proxy, static files) and FastAPI (business logic, authentication, AI orchestration).
- **Real-time**: Socket.IO for chat.
- **Data Storage**: Redis for primary persistence (users, workspaces, messages, sessions, API keys). PostgreSQL schema defined with Drizzle ORM for future migration.
- **Authentication**: Session-based with HTTP-only cookies, supporting `client`, `reseller`, `manager`, `super_admin` roles and `free`, `basic`, `pro`, `enterprise` plan types. API key system (`aai_` prefixed) for programmatic access.
- **AI Integration**: Multi-provider BYOK support (Groq, OpenAI, Anthropic, Gemini, Mistral) with a Python-based AI orchestrator. Supports workspace modes: AI (autonomous), Shadow (AI drafts, human approval), and Takeover (human control).
- **Shadow Mode (Enterprise)**: AI drafts require manager approval before sending to clients, with specific API endpoints and WebSocket events for real-time updates.
- **Conversation Memory**: Two-lane system (short-term buffer + session memory in Redis) for context-aware responses. Configurable memory scopes (USER, WORKSPACE, CONVERSATION, LEAD) with opt-in activation, safety features (PII filtering, circuit breaker), and fact management (deduplication, priority).
- **API Structure**: Comprehensive REST API for authentication, user management, workspaces, contacts, directives, subscriptions, pricing, and an OpenAI-compatible chat completions endpoint.
- **Programmatic Model Selection**: API requests can specify LLM models, overriding agent defaults, with provider auto-detection and validation.
- **Pricing System**: Phase-based, seat-based tiers, dynamically configured via admin API and integrated with Stripe for checkout.
- **Subscription System**: Manages subscription lifecycle (pending, active, warning, grace, expired/cancelled) with background workers and Stripe webhook integration.
- **Organization-Level Resource Sharing**: API keys and workspaces can be shared within an organization, with automatic migration upon license activation.
- **Quests Builder**: An AI-assisted app development environment embedded within the FastAPI backend, providing isolated environments, file system operations, LLM integration, and templates. Features **surgical code editing** with line-based insert/replace/delete operations to prevent AI from truncating code. See `docs/surgical-editing.md` for details.

### P2P Inference Network (PIN)
A decentralized Ollama marketplace where operators connect their localhost LLM instances via authenticated daemon (`pin-clientd` v2.1.0). Features WebSocket-only security (no public endpoint exposure), credit-based billing, and USDT payouts on BSC.

#### PIN Authentication & Node Registration
- **Operator-level authentication**: Single operator API key for all nodes
- **Automatic node registration**: Daemon sends `REGISTER_NODE` with alias, models, capacity, region on connect
- **Multi-node support**: Config array allows one daemon to register multiple logical nodes
- **Duplicate naming**: Server auto-suffixes (a, b, c) for operators registering same alias multiple times

#### PIN API Modes
The daemon supports two API modes for flexibility:
- **`ollama` (default)**: Native Ollama API format (`/api/chat`, `/api/tags`)
- **`openai`**: OpenAI-compatible format (`/v1/chat/completions`, `/v1/models`)

This allows operators to use:
- Standard Ollama instances
- OpenAI-compatible servers (vLLM, text-generation-inference, LMStudio, etc.)
- Any backend that speaks OpenAI format

Each node specifies all required fields:

```json
{
  "clientId": "op_xxx",
  "apiSecret": "secret",
  "nodes": [
    { "alias": "GPU-1", "inferenceUri": "http://localhost:11434", "apiMode": "ollama", "region": "us-east", "capacity": 10 },
    { "alias": "vLLM-1", "inferenceUri": "http://localhost:8000", "apiMode": "openai", "region": "us-west", "capacity": 20 }
  ]
}
```

#### PIN Interview System
Quality assurance protocol for validating operator LLMs before production traffic. Interviews are now per-node (not per-operator) - triggered on REGISTER_NODE.

**Dual Interview Tracks:**
The system uses different interview tracks based on API mode:

| Track | API Mode | Benchmark Requirement | Prompts | Thresholds |
|-------|----------|----------------------|---------|------------|
| **Standard** | `ollama` | Must have llama3:8b, mistral:7b, qwen2:7b, or gemma2:7b | 5 prompts (factual, instruction, math) | 90%/20 tok/s verified |
| **Advanced** | `openai` | None (uses first model) | 7 prompts (reasoning, code, complex math) | 95%/30 tok/s verified |

OpenAI-mode operators (vLLM, TGI, LocalAI) skip benchmark checks but face harder questions including multi-step reasoning, code generation, and algebra problems.

**Interview Flow:**
1. **On Connect**: Server sends `INTERVIEW_REQUEST` with test prompts + expected responses
2. **Daemon Executes**: Runs prompts against local LLM, records timing metrics
3. **Daemon Returns**: `INTERVIEW_RESULT` with responses + latency data
4. **Server Validates**: Checks accuracy and speed against mode-specific thresholds
5. **Tier Assignment**: Operator receives quality tier affecting routing priority

**Speed Metrics Collected:**
- `ttft_ms` - Time-to-first-token (responsiveness)
- `tokens_per_sec` - Token throughput
- `total_latency_ms` - End-to-end completion time

**Quality Tests (by track):**
- **Standard (Ollama)**: Factual accuracy, instruction following, simple math, coherence
- **Advanced (OpenAI)**: Multi-step reasoning, code generation, complex math, JSON formatting, logic puzzles

**Quality Tiers (Ollama mode):**
| Tier | Requirements | Routing Priority |
|------|--------------|------------------|
| `verified` | >90% accuracy, >20 tok/s | Highest |
| `standard` | >70% accuracy, >10 tok/s | Normal |
| `slow` | >70% accuracy, <10 tok/s | Low (budget tier) |
| `failed` | <70% accuracy | Blocked from production |

**Quality Tiers (OpenAI mode - stricter):**
| Tier | Requirements | Routing Priority |
|------|--------------|------------------|
| `verified` | >95% accuracy, >30 tok/s | Highest |
| `standard` | >85% accuracy, >20 tok/s | Normal |
| `slow` | >85% accuracy, <20 tok/s | Low (budget tier) |
| `failed` | <85% accuracy or <15 tok/s | Blocked from production |

**Operator Metadata Stored:**
```
quality_tier: verified | standard | slow | failed
avg_tokens_per_sec: float
avg_ttft_ms: int
accuracy_score: 0-100
last_interview: timestamp
interview_attempts: int
```

**Anti-Gaming Measures:**
- Server generates randomized prompt variants
- Timestamps verified server-side
- Periodic spot-checks during operation
- Anomaly detection for suspiciously perfect scores

**Retry Policy:**
- Failed operators can retry after 1-hour cooldown
- Maximum 3 attempts per 24-hour period
- Passing interview resets attempt counter

**Message Types:**
```rust
// Server → Daemon
INTERVIEW_REQUEST {
    interview_id: String,
    model: String,
    prompts: Vec<InterviewPrompt>,
    timeout_ms: u32,
}

struct InterviewPrompt {
    id: String,
    prompt: String,
    expected_contains: Option<Vec<String>>,  // fuzzy match
    expected_exact: Option<String>,          // exact match
    max_tokens: u32,
}

// Daemon → Server
INTERVIEW_RESULT {
    interview_id: String,
    model: String,
    results: Vec<PromptResult>,
}

struct PromptResult {
    prompt_id: String,
    response: String,
    ttft_ms: u32,
    total_ms: u32,
    tokens_generated: u32,
    error: Option<String>,
}
```

**Implementation Files:**
- Daemon: `pin-clientd/src/main.rs` (interview executor)
- Server: `api/routes/pin.py` (interview orchestration)
- Service: `api/services/pin_service.py` (validation logic, tier assignment)
- Storage: Redis keys `pin:interview:{operator_id}`, `pin:operator:{id}:tier`

## External Dependencies

### Third-Party Services
- **BYOK LLM Providers**: Groq, OpenAI, Anthropic, Gemini, Mistral (user-provided API keys).
- **Redis**: In-memory data store.
- **Google TTS**: Voice synthesis (Wavenet & Chirp) with usage tracking.
- **Stripe**: Payment processing for subscriptions.

### Environment Variables
- `DATABASE_URL` (PostgreSQL)
- `REDIS_URL`
- `SESSION_SECRET`
- `GOOGLE_TTS_CREDENTIALS`
- `STRIPE_WEBHOOK_SECRET`

### Key NPM Dependencies
- `@tanstack/react-query`
- `drizzle-orm` / `drizzle-zod`
- `express` / `http-proxy-middleware`
- `framer-motion`
- `react-markdown`
- `socket.io-client`

### Key Python Dependencies
- `fastapi` / `uvicorn`
- `socketio`
- `groq`
- `redis`
- `pydantic`