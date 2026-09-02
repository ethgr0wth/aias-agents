# AiOS Runtime Server B — Architecture Reference

**Interchained LLC**
**Confidential — For Internal Distribution**

---

## 1. Executive Summary

AiOS Runtime Server B is a standalone, security-isolated code execution environment that powers the KeyStone IDE and agent deployment pipeline. It runs on a dedicated machine, completely separated from the main AiAS API (Server A). Server A authenticates users and proxies requests; Server B executes code in ephemeral sandboxed sessions. This split-server architecture ensures that untrusted code execution never runs on the same machine as user data, authentication, or billing.

---

## 2. Why Two Servers?

| Concern | Server A (AiAS API) | Server B (Runtime) |
|---|---|---|
| **Role** | User-facing API, auth, billing, data | Code execution, file I/O, process management |
| **Trust level** | Trusted — handles credentials, sessions, Stripe | Untrusted — runs arbitrary user code |
| **Network exposure** | Public internet (HTTPS) | Internal only (`127.0.0.1:8099`) |
| **Data persistence** | Redis + PostgreSQL (permanent) | Ephemeral — everything lost on restart |
| **Failure blast radius** | Auth, billing, workspaces | Only active runtime sessions |
| **Scaling** | Vertical (single API server) | Horizontal (add more runtime boxes) |

**Key principle:** If Server B crashes, gets OOM-killed, or is compromised by malicious user code, Server A and all user data remain unaffected.

---

## 3. Architecture Diagram

```
                          ┌──────────────────────────────────┐
                          │         PUBLIC INTERNET           │
                          └──────────────┬───────────────────┘
                                         │ HTTPS
                          ┌──────────────▼───────────────────┐
                          │         SERVER A (AiAS API)       │
                          │  FastAPI + Express.js             │
                          │  ────────────────────────         │
                          │  Auth (session/API key)           │
                          │  User management, billing         │
                          │  Workspace data (Redis/Postgres)  │
                          │  KeyStone IDE frontend            │
                          │  ────────────────────────         │
                          │  /api/runtime/* → PROXY           │
                          └──────────────┬───────────────────┘
                                         │ HMAC-signed HTTP
                                         │ (internal network only)
                          ┌──────────────▼───────────────────┐
                          │       SERVER B (Runtime)          │
                          │  FastAPI on 127.0.0.1:8099        │
                          │  ────────────────────────         │
                          │  Session sandboxes                │
                          │  Code execution (Python/Node)     │
                          │  Git factory (bare repos)         │
                          │  Process management               │
                          │  Resource enforcement             │
                          │  ────────────────────────         │
                          │  Zero AiAS imports                │
                          │  Zero user credentials            │
                          │  Ephemeral by design              │
                          └──────────────────────────────────┘
```

---

## 4. Security Model

### 4.1 Network Isolation

- Server B binds to `127.0.0.1:8099` — never exposed to the internet
- Nginx allowlist restricts connections to Server A's IP only
- `RUNTIME_ALLOWED_IPS` environment variable enforces IP filtering at the application layer
- Dual-layer: even if Nginx is misconfigured, the app rejects unknown IPs

### 4.2 HMAC-SHA256 Authentication

Every request from Server A to Server B is cryptographically signed:

```
Signature = HMAC-SHA256(
    key  = DerivedKey(master_secret, time_window),
    data = METHOD + PATH + BODY + TIMESTAMP + NONCE + USER_CONTEXT
)
```

**Properties:**

| Feature | Detail |
|---|---|
| Key rotation | Every 5 minutes (configurable) |
| Clock skew tolerance | ±1 rotation window |
| Request TTL | 120 seconds — stale requests rejected |
| Replay protection | Nonce dedup cache (10,000 entries, auto-pruning) |
| Scope binding | Signature covers method + path — prevents cross-endpoint replay |
| User context binding | Signed user_id + org_id travels with every request |

### 4.3 Zero Trust Between Servers

- Server B has **zero imports** from the AiAS codebase
- Server B stores **no user credentials** — it receives user_id/org_id as signed context
- Server A is always the **source of truth** for identity and authorization
- Server B makes **no outbound calls** to Server A

### 4.4 Auth Chain Flow

```
User → Server A (session cookie or Bearer aai_xxx API key)
     → Validates identity (JWT/session + plan check: Pro/Enterprise required)
     → Signs request with HMAC (method + path + body + timestamp + nonce + user_context)
     → Server B validates: IP allowlist → HMAC signature → nonce uniqueness → request freshness
     → Executes tool → returns result
```

---

## 5. Session Model

### 5.1 Ephemeral Sessions

All sessions are ephemeral. They exist only in Server B's memory and filesystem. If Server B restarts, all sessions are gone. Server A is the source of truth.

| Property | Default | Configurable |
|---|---|---|
| TTL | 3600s (1 hour) | Per-session via RuntimePolicy |
| Grace period | 1800s (30 min) after TTL expiry | `grace_period_seconds` |
| Golden image | `runtime-golden-v2-node-python` | Per-session |
| Bare repo | Always preserved on cleanup/destroy | Never deleted |

### 5.2 Session Lifecycle

```
CREATE → ACTIVE → (TTL expires) → GRACE PERIOD → REMOVED
                        │
                    CLEANUP (files wiped, bare repo kept)
                        │
                    RESPAWN (checkout from bare repo, reinstall deps)
                        │
                    ACTIVE again
                        │
                    DESTROY (explicit delete, bare repo still kept)
```

### 5.3 Filesystem Zones

Each session gets isolated directories:

```
/tmp/runtime_b/
├── workspaces/{session_id}/     # Writable — user code lives here
├── tmp/{session_id}/            # Writable — scratch space
├── output/{session_id}/         # Writable — process logs
├── cache/{session_id}/          # Writable — session-local cache
├── readonly-base/{session_id}/  # Read-only base files
├── artifacts/{session_id}/      # Exported build artifacts
├── git/{session_id}/repo.git    # Bare git repo (NEVER deleted)
└── shared/                      # Cross-session package cache
    ├── npm-cache/
    └── pip-cache/
```

### 5.4 Environment-Scoped Sessions

Sessions can be scoped to a KeyStone `environment_id`. When a user returns to the same environment, the new session auto-clones the previous session's bare repo and checks out all files instantly — no re-upload needed.

```
Redis key: env_last_session:{org_id}:{user_id}:{environment_id} → session_id
```

---

## 6. Resource Enforcement

Every session has hard resource limits enforced at the OS level via `setrlimit`:

| Resource | Default Limit | Enforcement |
|---|---|---|
| Memory | 1024 MB | `RLIMIT_DATA` per subprocess |
| CPU time | 30 seconds | `RLIMIT_CPU` per subprocess |
| Disk | 512 MB | Checked before every file write |
| Processes | 10 concurrent | Checked before every process spawn |
| Output | 200 KB | Truncated by policy after execution |

Limits are applied via `preexec_fn` on every `subprocess.run` and `subprocess.Popen` call. There is no way for user code to bypass them.

---

## 7. Backpressure & Queue

Server B has an in-memory execution queue to prevent overload:

| Parameter | Default | Purpose |
|---|---|---|
| `RUNTIME_MAX_CONCURRENT` | 10 | Max simultaneous executions |
| `RUNTIME_MAX_QUEUE_DEPTH` | 50 | Max pending requests before rejection |
| `RUNTIME_MAX_PER_USER` | 3 | Max concurrent requests per user |

Overflow returns **HTTP 429** with a descriptive error. Queue metrics (wait time, execution time, rejection count) are tracked and exposed via `/metrics`.

Queued paths: `/run_code`, `/clone_repo`, `/install_node_deps`, `/install_python_deps`, `/install_package`, `/start_process`.

---

## 8. Tool Gateway

Server B exposes 23 scoped tools. No raw shell access. Every tool operates within the session's workspace sandbox.

### 8.1 Deployment Tools

| Tool | Purpose |
|---|---|
| `clone_repo` | Git clone into session workspace |
| `checkout_ref` | Switch branch/tag/commit |
| `detect_stack` | Detect Node/Python/Docker from project files |
| `install_node_deps` | `npm install` or `npm ci` with shared cache |
| `install_python_deps` | `pip install -r requirements.txt` in venv |
| `write_env_file` | Write `.env` from key-value dict |
| `start_process` | Launch a named process (e.g., `npm start`) |
| `stop_process` | Terminate a running process |
| `check_port` | TCP port check |
| `http_health_check` | HTTP GET health probe |
| `stream_logs` | Tail process stdout/stderr |
| `capture_preview_metadata` | Process logs + health for deployment card |
| `export_artifacts` | Copy build output to artifacts directory |
| `export_artifact` | Export a single file |

### 8.2 Code Execution Tools

| Tool | Purpose |
|---|---|
| `run_code` | Execute Python or Node.js snippet with timeout |
| `install_package` | Install a single pip/npm package on-demand |
| `read_file` | Read file content from workspace |
| `write_file` | Write file to workspace (disk quota enforced) |
| `list_directory` | List directory entries |
| `search_in_files` | Regex search across workspace files |
| `functions_mapping` | Python AST: extract function names, args, line numbers |
| `bracket_tracker` | Bracket/paren/brace balance checker |

### 8.3 Session Management Tools

| Tool | Purpose |
|---|---|
| `session_reset` | Wipe workspace, keep session alive |
| `commit_workspace` | Auto-commit workspace changes to bare repo |
| `workspace_diff` | Git diff of uncommitted workspace changes |
| `sync_workspace` | Receive gzipped tarball from KeyStone, extract + commit |

---

## 9. Git Factory

Every session gets a bare git repo that acts as a persistent version control layer:

### 9.1 Smart HTTP Server

Server B exposes a full Git smart HTTP interface per session:

```
GET  /git/{session_id}/info/refs?service=git-upload-pack
POST /git/{session_id}/git-upload-pack
POST /git/{session_id}/git-receive-pack
```

All git endpoints are HMAC-secured through the same auth middleware.

### 9.2 Git Hooks

**Pre-receive hook** (size enforcement):
- Max file size: 50 MB per file
- Max push size: 200 MB total
- Rejects pushes that exceed either limit

**Post-receive hook** (auto-deployment):
- Auto-checks out pushed code into the workspace
- Restarts all running processes if code changed
- Reports new HEAD hash back to the session state

### 9.3 Bare Repo Persistence

The bare repo at `/git/{session_id}/repo.git` is **never deleted** — not on cleanup, not on destroy, not on force-destroy. This means:

- A cleaned-up session can respawn instantly by checking out from its bare repo
- Environment-scoped sessions clone the previous session's bare repo for continuity
- KeyStone workspace sync commits to bare repo on upload

---

## 10. Shared Package Cache

Server B maintains a cross-session shared cache for npm and pip packages:

```
/tmp/runtime_b/shared/
├── npm-cache/    # --cache argument for all npm commands
├── pip-cache/    # --cache-dir argument for all pip commands
└── .cache.lock   # flock-based mutual exclusion
```

- All `npm install` and `pip install` commands use `--prefer-offline` with the shared cache
- File-level locking (`fcntl.flock`) prevents cache corruption from concurrent installs
- **Pre-warm on startup**: Optionally pre-downloads common packages (React, Express, FastAPI, etc.) into cache before any session needs them
- Cache status (size, file count) exposed via `/cache/status`
- Manual clear via `POST /cache/clear`

---

## 11. Activity Tracking

Server B tracks user activity per session, stored in Redis:

| Activity Kind | Tracked When |
|---|---|
| `session_create` | New session created |
| `session_respawn` | Session respawned from bare repo |
| `page_visit` | User navigates in KeyStone |
| `click` | User clicks UI element |
| `cookie_update` | Session cookie state changes |
| `git_push` / `git_pull` | Git operations |
| `process_start` / `process_stop` | Process lifecycle |
| `file_edit` | File write or workspace commit |
| `code_run` | Code execution |
| `idle_ping` | Keepalive |

**Session keep-alive:** As long as the user is active (clicking, navigating, cookie alive), the session TTL refreshes. Idle sessions enter grace period, then are cleaned up.

---

## 12. Observability

### 12.1 Endpoints

| Endpoint | Purpose |
|---|---|
| `GET /health` | Session count, uptime, queue depth, Redis status, resource snapshots, cache status |
| `GET /metrics` | Tool invocation counts, error summary, per-tool latency averages, session count |
| `GET /logs` | Global tool execution ledger (last 10,000 entries) |
| `GET /logs/session/{id}` | Per-session tool history (last 1,000, 2h TTL) |
| `GET /logs/user/{id}` | Per-user tool history (last 1,000, 24h TTL) |
| `GET /cache/status` | npm + pip cache size and file counts |
| `POST /handshake` | Verify HMAC connectivity from Server A |

### 12.2 Redis Storage Schema

All observability data is stored in Redis under the `runtime_b:` namespace:

```
runtime_b:tool_ledger           → list (last 10,000 tool invocations)
runtime_b:session_logs:{sid}    → list (per-session, 2h TTL)
runtime_b:user_logs:{uid}       → list (per-user, 24h TTL)
runtime_b:org_logs:{oid}        → list (per-org, 24h TTL)
runtime_b:tool_counts           → hash (invocation counts per tool)
runtime_b:error_counts          → hash (error counts by classification)
runtime_b:latency:{tool}        → list (last 500 latency samples per tool)
runtime_b:session_meta:{sid}    → string (session metadata JSON, TTL = session TTL)
runtime_b:active_sessions       → set (all active session IDs)
runtime_b:activity_stream:{sid} → list (last 500 activity events)
runtime_b:session_grace:{sid}   → string (grace period marker)
runtime_b:env_last_session:{scope} → string (environment→session mapping, 7d TTL)
```

### 12.3 Error Classification

Errors are automatically classified for dashboarding:

| Class | Trigger |
|---|---|
| `timeout` | Execution exceeded time limit |
| `permission` | File system permission denied |
| `not_found` | File or directory missing |
| `oom` | Out of memory |
| `validation` | Invalid input |
| `resource_limit` | Process/disk quota exceeded |

---

## 13. Admin API

Gated behind `super_admin` auth on Server A:

| Endpoint | Purpose |
|---|---|
| `GET /admin/sessions` | List all sessions with user, org, disk, process, activity metadata |
| `DELETE /admin/sessions/{id}` | Force-destroy a session (bare repo preserved) |
| `GET /admin/sessions/stats` | Aggregate stats (total, active, stale, disk, processes) |
| `GET /admin/sessions/{id}/activity` | Full activity stream for a session |

---

## 14. KeyStone IDE Integration

The KeyStone IDE (`/keystone/:id`) integrates with Runtime Server B through Server A's proxy:

1. **Session creation**: `QuestsWorkspace.tsx` auto-creates a runtime session scoped to the environment
2. **Workspace sync**: Tars up KeyStone's file root, sends to Server B, which extracts and commits to bare repo
3. **Code execution**: Terminal tab sends `run_code` with Python/Node toggle
4. **Package install**: Terminal tab sends `install_package` for on-demand pip/npm installs
5. **Deploy tab**: 7-card deployment lifecycle (clone → detect stack → install deps → env vars → start processes → health checks → export)
6. **Ledger tab**: Real-time tool invocation feed with auto-refresh and filtering

---

## 15. Deployment

### 15.1 Production Setup

```bash
# On Server B machine:
cp -r runtime_server/ /opt/runtime_server/
cp deploy/env.example /opt/runtime_server/.env    # Configure secrets
pip install -r requirements.txt
cp deploy/runtime-server-b.service /etc/systemd/system/
systemctl enable --now runtime-server-b

# On Server A machine (add to AiAS env):
RUNTIME_REMOTE_URL=http://<server-b-internal-ip>:8099
RUNTIME_SHARED_SECRET=<matching-secret>
```

### 15.2 Environment Variables

**Server B:**

| Variable | Default | Description |
|---|---|---|
| `RUNTIME_HOST` | `127.0.0.1` | Bind address |
| `RUNTIME_PORT` | `8099` | Bind port |
| `RUNTIME_SHARED_SECRET` | (required) | Master HMAC secret |
| `RUNTIME_ALLOWED_IPS` | (empty) | Comma-separated IP allowlist |
| `RUNTIME_ROOT` | `/tmp/runtime_b` | Workspace root directory |
| `RUNTIME_REDIS_URL` | `redis://localhost:6379/12` | Redis connection |
| `RUNTIME_REDIS_NAMESPACE` | `runtime_b` | Redis key prefix |
| `RUNTIME_KEY_ROTATION_INTERVAL` | `300` | HMAC key rotation (seconds) |
| `RUNTIME_MAX_CONCURRENT` | `10` | Max simultaneous executions |
| `RUNTIME_MAX_QUEUE_DEPTH` | `50` | Max queued requests |
| `RUNTIME_MAX_PER_USER` | `3` | Per-user concurrency limit |
| `RUNTIME_SESSION_TTL` | `3600` | Default session TTL (seconds) |
| `RUNTIME_CLEANUP_INTERVAL` | `120` | Cleanup loop interval (seconds) |
| `RUNTIME_CACHE_PREWARM` | `0` | Pre-warm package cache on startup |
| `RUNTIME_SHARED_CACHE_ROOT` | `{RUNTIME_ROOT}/shared` | Shared cache directory |

**Server A (proxy config):**

| Variable | Default | Description |
|---|---|---|
| `RUNTIME_REMOTE_URL` | (empty) | Server B URL (e.g., `http://127.0.0.1:8099`) |
| `RUNTIME_SHARED_SECRET` | (empty) | Must match Server B |
| `RUNTIME_KEY_ROTATION_INTERVAL` | `300` | Must match Server B |
| `RUNTIME_PROXY_TIMEOUT` | `120` | Proxy request timeout (seconds) |

### 15.3 Systemd Service

```ini
[Unit]
Description=AiOS Runtime Server B
After=network.target redis.service

[Service]
Type=simple
User=runtime
Group=runtime
WorkingDirectory=/opt/runtime_server
EnvironmentFile=/opt/runtime_server/.env
ExecStart=/usr/bin/python3 run_server.py
Restart=always
RestartSec=5
LimitNOFILE=65536
LimitNPROC=4096

[Install]
WantedBy=multi-user.target
```

---

## 16. Codebase Map

```
runtime_server/
├── app.py                 # FastAPI app, all HTTP endpoints, middleware
├── runtime_manager.py     # Core: sessions, code exec, git, processes, lifecycle
├── models.py              # Pydantic models: policies, requests, session state
├── resource_enforcer.py   # setrlimit enforcement, disk quota tracking
├── shared_secret.py       # HMAC-SHA256 rotating key auth + replay protection
├── execution_queue.py     # Backpressure queue with per-user limits
├── storage.py             # Redis: tool ledger, activity, session meta
├── cache_manager.py       # Shared npm/pip cache with flock locking
├── run_server.py          # Uvicorn entry point
├── start.sh               # Dev startup script
└── deploy/
    ├── DEPLOYMENT.md
    ├── runtime-server-b.service
    └── nginx-runtime-b.conf

Server A proxy (in aias_production/):
├── api/routes/runtime.py           # /api/runtime/* route handlers + auth
└── api/services/runtime_proxy.py   # HMAC signing, HTTP proxy, error handling
```

---

## 17. Design Decisions

1. **No local fallback.** If `RUNTIME_REMOTE_URL` is not set, Server A returns HTTP 503. There is no in-process runtime fallback — code execution always happens on a separate machine.

2. **Bare repos are sacred.** Every cleanup, destroy, or force-destroy preserves the bare git repo. This is the user's code history. Workspace files are ephemeral; the repo is not.

3. **venv per session.** Each Python session gets its own `.venv` to prevent cross-session package conflicts. The shared pip cache makes venv creation fast.

4. **No raw shell.** The tool gateway provides scoped operations only. There is no `exec` or `shell` endpoint. Users interact through defined tools.

5. **Signed user context.** Server B never authenticates users directly. It trusts the HMAC-signed `X-Runtime-Context` header from Server A, which carries `user_id` and `org_id`.

---

*Interchained LLC — AiOS Runtime Server B v1.0.0*
