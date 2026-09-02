# Runtime Server B — Deployment Guide

## Architecture

Server B runs the AiOS Runtime execution environment on a dedicated machine.
Server A (AiAS API) proxies `/api/runtime/*` requests to Server B transparently.
Clients see no difference — same endpoints, same domain.

## Session Semantics

- All runtime sessions are **ephemeral**
- Sessions are lost on Server B restart
- Server A remains the source of truth for user/org data
- Session TTL defaults to 3600s (configurable via RuntimePolicy)
- Processes, files, and environments within a session are destroyed when the session is destroyed or Server B restarts

## Security

- Server B binds to `127.0.0.1:8099` — **not publicly accessible**
- IP allowlist: only Server A's IP is permitted (`RUNTIME_ALLOWED_IPS`)
- HMAC-SHA256 rotating shared secret with replay protection:
  - Signature covers: request body + timestamp + nonce
  - 30-second request TTL (rejects stale requests)
  - Nonce dedup cache (rejects replayed requests)
  - Key rotation interval: 5 minutes (configurable)
  - Clock skew tolerance: ±1 window

## Resource Enforcement (per session)

- `max_memory_mb`: 1024 (default) — enforced via setrlimit
- `max_cpu_seconds`: 30 (default) — enforced via setrlimit
- `max_disk_mb`: 512 (default) — checked before writes
- `max_processes`: 10 (default) — checked before process spawn
- `max_output_bytes`: 200KB (default) — truncates excessive output

## Backpressure / Queue

- `RUNTIME_MAX_CONCURRENT`: max simultaneous executions (default 10)
- `RUNTIME_MAX_QUEUE_DEPTH`: max pending requests (default 50)
- `RUNTIME_MAX_PER_USER`: max concurrent requests per user (default 3)
- Overflow returns HTTP 429 (Too Many Requests)

## Environment Variables

### Server B
| Variable | Default | Description |
|---|---|---|
| `RUNTIME_HOST` | `127.0.0.1` | Bind address (keep internal) |
| `RUNTIME_PORT` | `8099` | Bind port |
| `RUNTIME_REDIS_URL` | `redis://localhost:6379/12` | Redis connection |
| `RUNTIME_REDIS_NAMESPACE` | `runtime_b` | Redis key prefix |
| `RUNTIME_SHARED_SECRET` | (empty) | Master secret for HMAC auth |
| `RUNTIME_ALLOWED_IPS` | (empty) | Comma-separated allowlist |
| `RUNTIME_KEY_ROTATION_INTERVAL` | `300` | Key rotation seconds |
| `RUNTIME_ROOT` | `/tmp/runtime_b` | Workspace root |
| `RUNTIME_MAX_CONCURRENT` | `10` | Max concurrent executions |
| `RUNTIME_MAX_QUEUE_DEPTH` | `50` | Max queued requests |
| `RUNTIME_MAX_PER_USER` | `3` | Max per-user concurrency |

### Server A (add to AiAS env)
| Variable | Default | Description |
|---|---|---|
| `RUNTIME_REMOTE_URL` | (empty) | Server B URL, e.g. `http://127.0.0.1:8099` |
| `RUNTIME_SHARED_SECRET` | (empty) | Must match Server B |
| `RUNTIME_KEY_ROTATION_INTERVAL` | `300` | Must match Server B |
| `RUNTIME_PROXY_TIMEOUT` | `120` | Proxy request timeout |

When `RUNTIME_REMOTE_URL` is not set, Server A falls back to its local RuntimeManager (backward compatible).

## Setup Steps

1. Copy `runtime_server/` to Server B at `/opt/runtime_server/`
2. Copy `deploy/env.example` to `/opt/runtime_server/.env` and configure
3. Install deps: `pip install -r requirements.txt`
4. Install systemd service: `cp deploy/runtime-server-b.service /etc/systemd/system/`
5. Enable and start: `systemctl enable --now runtime-server-b`
6. On Server A, set `RUNTIME_REMOTE_URL=http://<server-b-ip>:8100` and matching `RUNTIME_SHARED_SECRET`

## Observability

- `GET /health` — session count, uptime, queue depth, resource usage, Redis status
- `GET /metrics` — tool counts, error summary, latency percentiles per tool
- `GET /logs` — recent tool execution ledger
- `GET /logs/session/{id}` — per-session log history
- `GET /logs/user/{id}` — per-user log history
- All logs stored in Redis under `runtime_b:*` namespace with automatic expiry
