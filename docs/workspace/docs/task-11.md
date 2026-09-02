---
title: ServerBuddy — Standalone Server Management App
---
# ServerBuddy — Standalone Server Management App

## What & Why
Build ServerBuddy, a standalone double-gated server management tool in `serverBuddy/`. It provides 3 capabilities: (1) an AI agent chat with expandable server-side tools, (2) an allowlisted emulated shell, and (3) an audit log. Protected by dual authentication — AiAS API key validated remotely via the same pattern SaaS-Signal uses (`/v1/health` + `/v1/organization`) plus an env password (`SERVERBUDDY_PASSWORD`). Designed to be hosted anywhere — zero direct Redis/DB access to AiAS. Uses AiAS workspaces for persistent chat sessions.

## Done looks like
- A standalone FastAPI + React (Vite) app running from `serverBuddy/` on its own port
- Login screen requiring both an AiAS API key (`aai_` prefix) and the env password
- Key validated remotely using the SaaS-Signal auth pattern: call AiAS `/v1/health` with Bearer token to verify + get user/org/plan info, call `/v1/organization` for org ID, cache results in Redis for 15 min — no token waste, no direct AiAS DB access
- Second gate: env password checked against `SERVERBUDDY_PASSWORD`
- Session persists via JWT after successful dual-gate auth
- **Dashboard tab**: Robot avatar header with agent chat bubble, 2x4 grid of quick-action tool cards (Check Status, View Logs, Restart Service, Deploy Release, Disk Usage, Manage Trash, Load Wallet, Rotate Workers) — tapping a card sends a pre-built prompt to the agent
- **Shell tab**: Terminal-style emulated shell (`oracle@server:~$` prompt) where typed commands are validated against a server-side allowlist before execution; blocked commands show a denial message
- **Audit tab**: Chronological log of all agent tool invocations and shell commands with timestamps, user, and result status
- Agent chat proxied through AiAS `/v1/chat/completions` using the user's API key as Bearer token — BYOK provider config, org context all come for free
- Workspace-backed persistent sessions: on first login, creates (or reconnects to) an AiAS workspace tagged `[ServerBuddy]` for persistent chat history across sessions
- 8 starter server tools on the backend: `check_status`, `view_logs`, `restart_service`, `deploy_release`, `disk_usage`, `manage_trash`, `load_wallet`, `rotate_workers`
- Shell allowlist configurable via Python set; initial safe commands: `ls`, `df`, `du`, `top`, `uptime`, `ps`, `free`, `whoami`, `date`, `cat`, `tail`, `head`, `grep`, `status`, `logs`, `restart`
- `AIAS_BASE_URL` env var configures which AiAS instance to connect to
- Dark sci-fi UI matching the mockup (steel blue/indigo palette, glowing borders, monospace terminal font)

## Out of scope
- Direct Redis/DB access to AiAS internals (everything goes through AiAS HTTP API)
- WebSocket/real-time streaming (standard request/response for v1)
- File upload/download through shell
- Multi-user concurrent sessions (single-operator tool for now)
- Mobile-specific responsive layout (desktop-first)

## Tasks
1. **Project scaffold** — Create `serverBuddy/` with FastAPI backend (`server/`) and React+Vite+Tailwind frontend (`client/`), configure Vite proxy to backend, and set up the start script and workflow.

2. **Dual-gate authentication** — Port the SaaS-Signal auth pattern (`saas-signal/api/middleware/auth.py`) into ServerBuddy: validate AiAS key via `/v1/health` + `/v1/organization` with Redis caching. Add the second gate (check password against `SERVERBUDDY_PASSWORD` env var). Issue a session JWT on success. Build `POST /api/auth/login` and the login UI screen.

3. **Workspace session persistence** — On successful auth, call AiAS API to list user workspaces and find one tagged `[ServerBuddy]`, or create a new one. Store workspace ID in the session JWT. Use this workspace for all agent chat so history persists across logins.

4. **Server tools backend** — Implement 8 tool functions as Python callables with a tool registry. Build `POST /api/agent/chat` that forwards to AiAS `/v1/chat/completions` with tool definitions in OpenAI function-calling format, executes tool calls server-side, and returns the final response.

5. **Allowlisted shell backend** — Build `POST /api/shell/exec` that parses the command, checks the base command against a configurable allowlist, executes via subprocess with 30s timeout and 64KB output limit, returns stdout/stderr. Rejected commands return a denial message.

6. **Audit logging** — In-memory audit store (capped at 500 entries) recording every agent tool invocation and shell command with timestamp, user, command/tool, args, result, and status. Expose `GET /api/audit` with pagination.

7. **Dashboard tab UI** — Robot avatar with speech bubble at top, 2x4 quick-action tool card grid, chat interaction area. Tapping a card sends a prompt to the agent. Free-form chat input also available.

8. **Shell tab UI** — Dark terminal with monospace font, `oracle@server:~$` prompt, command input with history (up/down arrows), scrollable command/response output.

9. **Audit tab UI** — Chronological log with color-coded status indicators (green=success, red=error, yellow=denied).

10. **Workflow & wiring** — Add Replit workflow, wire `AIAS_BASE_URL` to local AiAS instance, verify full flow: login → dashboard tools → shell commands → audit trail.

## Relevant files
- `saas-signal/api/middleware/auth.py`
- `aias_production_clone/api/routes/public_api.py:112-132`
- `aias_production_clone/api/routes/public_api.py:185-519`
- `aias_production_clone/api/services/redis_storage.py:812-900`