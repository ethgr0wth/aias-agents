# Runtime Server

Runtime Server is an isolated execution service for agent workspaces. It
manages sessions, processes, package installation, file operations, previews,
artifact export, resource limits, queueing, and shared dependency caches behind
rotating HMAC request authentication.

## Security warning

This service executes code and shell commands. It must run on a dedicated host
or hardened sandbox and must never be exposed without network controls and the
required HMAC authentication secret.

## Features

- Per-session workspaces and process lifecycle management
- Concurrency and queue limits
- CPU, memory, disk, and process enforcement
- Shared package cache support
- Port and HTTP health checks
- Log streaming and preview metadata
- Artifact export
- Rotating HMAC signatures with timestamp and nonce replay protection
- Optional Redis-backed runtime state

See [ARCHITECTURE.md](./ARCHITECTURE.md) and
[deploy/DEPLOYMENT.md](./deploy/DEPLOYMENT.md) for deeper operational details.

## Requirements

- Python 3.11+
- Redis
- Any language runtimes and system tools that executed workloads require

## Quick start

```bash
cp .env.example .env
# Set a unique RUNTIME_SHARED_SECRET.

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

./start.sh
```

The default endpoint is `http://localhost:8099`.

## Required configuration

`RUNTIME_SHARED_SECRET` is mandatory. Runtime Server refuses to start without
it. The caller must use the same master secret to generate rotating HMAC
request signatures.

Generate a secret with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Restrict `RUNTIME_ALLOWED_IPS` to trusted callers and bind to a private network
where possible.

## Project layout

```text
runtime_server/
├── app.py                 # FastAPI endpoints and authentication middleware
├── runtime_manager.py     # Workspace and process lifecycle
├── execution_queue.py     # Admission control
├── resource_enforcer.py   # Runtime limits
├── cache_manager.py       # Shared dependency caches
├── storage.py             # Redis-backed state
├── shared_secret.py       # Rotating HMAC implementation
├── deploy/                # systemd/nginx deployment examples
└── start.sh
```

## Docker

The included image provides the Python runtime server. Install additional
language runtimes in a derived image if workloads require them.

```bash
docker build -t runtime-server .
docker run --rm --env-file .env -p 8099:8099 runtime-server
```

## License

MIT. See [LICENSE](./LICENSE).