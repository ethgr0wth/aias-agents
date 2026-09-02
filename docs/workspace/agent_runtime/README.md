# Agent Runtime Fabric (ARF) v0.4.0

Production-grade BYOK execution layer with a strict tool gateway. No raw shell — agents and bots get scoped Python/Node execution with policy gates before anything touches the runtime.

> **Security:** ARF executes untrusted code and does not provide end-user
> authentication by itself. Bind it to a private interface, place it behind an
> authenticated control plane, and run it in a dedicated sandbox or host.

## Tool Contract

### A) Deployment / app-runtime tools
- `clone_repo` — shallow clone into session workspace
- `checkout_ref` — switch branch/tag
- `detect_stack` — detect Node/Python/Docker
- `install_node_deps` — npm install/ci
- `install_python_deps` — pip install -r
- `write_env_file` — generate .env
- `start_process` — spawn and track background process
- `stop_process` — terminate tracked process
- `check_port` — TCP port probe
- `http_health_check` — GET health check
- `stream_logs` — tail process logs
- `capture_preview_metadata` — snapshot preview state
- `export_artifacts` — copy workspace dir to persistence

### B) Safe coding/file toolset
- `run_code` — execute Python or Node snippets in temp sandbox
- `install_package` — record to manifest (ledgered)
- `read_file` / `write_file` — scoped to runtime zones
- `list_directory` — directory listing
- `search_in_files` — regex search across files
- `functions_mapping` — AST-based function index (Python)
- `bracket_tracker` — bracket/brace balance checker
- `export_artifact` — copy single file to persistence
- `session_reset` — wipe session state

No raw shell endpoint is exposed.

## Architecture

- **Control Plane:** FastAPI backend with session management, policy enforcement, tool ledger
- **Frontend:** Dark cockpit UI with tabbed navigation (Session, Terminal, Files, Deploy, Tools, Ledger)
- **Execution Plane:** Isolated runtime zones per session with path traversal protection
- **Persistence Plane:** Tool ledger (JSONL) + package manifests survive session resets

## Runtime Filesystem Zones

- `/runtime/workspaces/{session}` — writable workspace
- `/runtime/tmp` — writable temp
- `/runtime/output` — writable logs/output
- `/runtime/cache` — writable cache
- `/runtime/readonly-base` — immutable base image

## Policy Controls

Per-session configurable:
- `session_ttl_seconds` (default 3600)
- `max_execution_seconds` (default 30)
- `max_output_bytes` (default 200KB)
- `max_memory_mb` (default 1024)
- `network_mode` ("deny" or "allowlisted")

## Run

```bash
cp .env.example .env
bash start.sh
```

Runs on port 3000 (configurable via `ARF_PORT` env var).

Runtime workspaces default to `/tmp/runtime`. The invocation ledger and package
manifests default to `./persistence`; runtime ledger files are intentionally
gitignored because requests and outputs may contain sensitive content.

## Docker

```bash
docker build -t agent-runtime .
docker run --rm -p 3000:3000 \
  -v arf-runtime:/runtime \
  -v arf-persistence:/persistence \
  agent-runtime
```

The image includes Python only. Extend it with Node.js or other toolchains
required by the workloads you intend to run.

## API

- `GET /health` — status + available tools list
- `POST /sessions` — create session with optional policy
- `POST /session_reset/{id}` — wipe session state
- `POST /{tool_name}` — execute tool (requires valid session_id)
- `GET /logs?limit=N` — read tool invocation ledger
- `GET /` — serves frontend UI

## License

MIT. See [LICENSE](./LICENSE).
