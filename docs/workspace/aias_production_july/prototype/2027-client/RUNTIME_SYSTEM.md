# Runtime System — 2027 Client (Server B Isolated Execution)

> Server B is ephemeral. Server A is source of truth. Every session lost on restart. GC leak exists.

---

## 1. Session Lifecycle

```
Client → /api/runtime/sessions {policy environment_id} → Server A runtime.py get_runtime_user Bearer aai_ OR cookie/header _session_token_from requires pro|enterprise or manager → proxy_request POST sessions Server B /sessions with X-Runtime-Context JSON{user_id org_id} signed via RotatingSecretAuth HMAC-SHA256(master time//rotation) window ±1 timestamp TTL 120s nonce 10k LRU → RuntimeManager create_session UUID policy defaults mkdir 5 zones workspaces tmp output cache readonly-base + check env_last_session org:user:env TTL7d if prev bare git clone --bare prev→new checkout first branch or HEAD fast path else init_bare_repo registry Redis TTL session_meta TTL ttl JSON etc active_sessions set → return state id/user/org/env/created_at/golden_image runtime-golden-v2-node-python status active/resetting/destroyed/cleaned policy last_activity git_head preserve_bare

→ sync_workspace tar.gz: Tar packing from QuestsFileService file_root data/quests/{org}/{env} exclude .git node_modules __pycache__ .venv venv → raw POST Server B /sessions/{sid}/sync_workspace as gzip raw binary proxied via proxy_request_raw preserving content-type → secure tar extract: skip symlinks/dev files reject absolute/.. ensures target.startswith workspace+sep counting files → git add -A && commit sync from keystone if bare exists reports venv status

→ run_code: validates cwd inside workspace via relative_to injects NODE_PATH writes .~snippet.py/.js .~snippet outside? Writes .~snippet.py inside workspace/.tmp? Actually writes .~snippet.py under workspace root hidden, runs, unlink snippet, finally cleans temp if no workdir. Env binding mandatory PR#34: checks session.environment_id vs requested; mismatch 409 runtime environment does not match session binding; unbound session + env-bearing request 409 session has no environment binding; missing workspace 409 sync the environment before execution. Policy max_output_bytes 200k truncation. preexec_fn setrlimit RLIMIT_CPU + optional RLIMIT_DATA vs AS, disk quota, process limit before spawn. NODE_PATH injection venv/bin:node_modules/.bin:$PATH rewrites python→venv python logs output/<sid>/<name>.log Popen env. Code analysis functions_mapping ast parse, bracket_tracker stack.

→ processes: detect_stack package.json etc → install_node_deps Npm ci if frozen_lockfile && package-lock else install --cache <shared> --prefer-offline fcntl lock 180s + install_python_deps pip --cache-dir <shared> _ensure_venv cascade python3 -m venv → --without-pip → ensurepip --upgrade → bootstrap urllib get-pip.py fallback checks bin existence → write_env_file sorted .env via json.dumps(v)[1:-1] escaping → start_process checks tracker limit injects VIRTUAL_ENV PATH logs output/<sid>/<name>.log Popen preexec_fn env + check_port http_health_check stream_logs capture_preview_metadata export_artifacts.

→ git: push http://.../api/runtime/git/<sid>/git-receive-pack → Server A proxy_raw → Server B git-receive-pack --stateless-rpc bare updated → post-receive checkout -f workspace → _handle_post_receive updates git_head → _restart_session_processes. info/refs pkt-line header, upload-pack pull records git_pull/push git_head.

→ commit: workspace_commit_manager debounce 10s threading.Timer mark_dirty → schedule _fire_commit proxy POST sessions/{id}/commit_workspace message flush_now cancel + notify_file_change hook in quests.py write endpoint.

→ cleanup: SESSION_CLEANUP_INTERVAL 120s thread loop grace_expired sessions git/<sid>/repo.git disk removal tracking bare preserved (leak) + expired sessions still in active set but meta missing → cleanup preserve bare + set_grace TTL grace_seconds → later grace expires → cleanup_disk + remove active set. Bare never GC → disk growth linear with sessions.

```

Diagram in UI as timeline for 2027 client: create → sync (packing/uploading/extracting/committing) → detect_stack → install deps fcntl shared cache → write_env_file → start_process → run_code loop → git push post-receive checkout restart → commit_manager debounce auto-commit → cleanup grace → grace expired remove.

---

## 2. Models (runtime_server/models.py)

```py
RuntimePolicy session_ttl_seconds 3600 grace_period_seconds 1800 max_execution_seconds 30 max_output_bytes 200000 max_memory_mb 1024 max_cpu_seconds 30 max_disk_mb 512 max_processes 10 network_mode allowlisted|deny

SessionState session_id user_id org_id environment_id created_at golden_image runtime-golden-v2-node-python status active|resetting|destroyed|cleaned policy RuntimePolicy last_activity git_head preserve_bare_repo

SessionActivity ts session_id user_id kind page_visit click cookie_update api_call git_push git_pull process_start process_stop file_edit code_run session_create session_respawn idle_ping custom page element_id cookie_keys metadata ip user_agent

GitHookConfig max_file_size_bytes 50M max_push_size_bytes 200M auto_checkout true restart_on_push

CloneRepoRequest session_id repo_url target_dir
CheckoutRefRequest session_id repo_dir ref
DetectStackRequest session_id repo_dir
InstallNodeDepsRequest session_id repo_dir frozen_lockfile true
InstallPythonDepsRequest session_id repo_dir requirements_file requirements.txt
WriteEnvFileRequest session_id repo_dir env dict[str,str]
StartProcessRequest session_id repo_dir name command list[str] port int?
CheckPortRequest ...
HttpHealthCheckRequest ...
StreamLogsRequest ...
CapturePreviewMetadataRequest ...
ExportArtifactsRequest ...
RunCodeRequest session_id environment_id? code cwd environment binding + max_output truncation
InstallPackageRequest session_id packages[]
FileRequest session_id path
SearchInFilesRequest ...
FunctionsMappingRequest ...
BracketTrackerRequest ...
ArtifactRequest ...
WriteFileRequest ...
```

Plus ToolLog session_id user_id org_id tool request result latency_ms error_class classify_error name TimeoutError permission not_found oom validation else lower + package_state dict {sid:{eco:set}}

---

## 3. Security Stack

- AuthMiddleware: /health open rest IP allowlist RUNTIME_ALLOWED_IPS vs X-Real-IP/XFF/client host effective_ip 403 JSON seen/effective + HMAC payload METHOD:PATH:BODY_BYTES+TIMESTAMP+NONCE[:CONTEXT] context JSON{user_id,org_id} from X-Runtime-Context RotatingSecretAuth master → HMAC(master, window SHA256) per window time//interval valid keys [-skew,+skew] ±1 timestamp TTL 120s nonce replay OrderedDict 10k LRU constant-time compare pruning cutoff now-2*ttl

- Filesystem: resolve_workspace_path Path(root/path).resolve().startswith(root.resolve()) anti-traversal resolve_runtime_path only /runtime/{workspaces,tmp,output,cache}/ allowed rejects .. Tar extraction secure skips symlinks/dev files rejects absolute/.. ensures target.startswith workspace_resolved+sep

- Execution: make_preexec_fn setrlimit RLIMIT_CPU max_cpu_seconds optional RLIMIT_DATA note DATA not RSS AS would be stronger per doc, disk quota check before writes process limit before spawn, Git hooks pre-receive max file 50MB max push 200MB via rev-list + cat-file -s

---

## 4. Queue & Enforcer

- ExecutionQueue asyncio.Semaphore MAX_CONCURRENT 10 prod 24 MAX_QUEUE_DEPTH 50 prod 88 MAX_PER_USER 3 prod 4 _user_counts _pending execute(user_id, coro) admission increment pending/user acquire semaphore record wait_ms exec total_completed/errors exec_ms release decrement metrics avg wait/exec sliding 1000 truncated 500

- QueueMiddleware 6 paths /run_code /clone_repo /install_node_deps /install_python_deps /install_package /start_process go through queue → 429 too many requests on full. Bug: await queue.execute(user_id, call_next(request)) — call_next(request) creates coroutine immediately not after admission should be lambda

- ResourceEnforcer SessionResourceTracker active_processes disk_usage_bytes limits methods check limits measure_disk_usage try du -sb fallback rglob

- CacheManager npm-cache pip-cache lockfile .cache.lock status sizes MB via rglob file counts prewarm downloads without installing pip download --dest tmp --no-deps pkg npm init -y + npm install pkg uses same lock for whole run config via prewarm.json

---

## 5. Storage Redis Keys

```
runtime_b:tool_ledger 10000
session_logs:{sid} 1000 TTL7200
user_logs:{uid} 999 TTL86400
org_logs:{oid}
error_counts hash
tool_counts
latency:{tool} list 500
manifest:{sid}:{eco} TTL7200
session_metrics:{sid}
session_meta:{sid} TTL ttl JSON {session_id,user_id,org_id,created_at,last_activity,last_page,last_click,cookie_snapshot,activity_count}
active_sessions set
activity_stream:{sid} list 500 TTL 2*ttl
user_activity:{uid} 1000 TTL86400
session_grace:{sid} TTL grace
env_last_session:{org}:{user}:{env} TTL7d
session_env:{sid} TTL7d
```

Methods register/touch/record_activity/get_activity_stream/get_user_activity/get_session_activity_summary event breakdown last 500 get_session_meta list_all_sessions remove_session deletes meta/set/logs/metrics/activity/grace/env expired detection via exists checks grace expired via not meta and not grace

---

## 6. Endpoints (Server B full list)

```
GET /health {status ok|degraded component aios-runtime-server-b uptime session_count tools sorted ALLOWED_TOOLS queue metrics snapshot redis connected|disconnected resource_usage all snapshots cache status ephemeral_notice}
POST /handshake {message hello universe component uptime session_count hmac_verified true}

POST /sessions {policy? environment_id?} → SessionState
GET /sessions → list
POST /session_reset/{sid}
DELETE /sessions/{sid}

POST /clone_repo {session_id repo_url target_dir}
POST /checkout_ref
POST /detect_stack
POST /install_node_deps
POST /install_python_deps
POST /write_env_file
GET /list_processes + POST /start_process POST /stop_process
POST /check_port
POST /http_health_check
POST /stream_logs
POST /capture_preview_metadata
POST /export_artifacts
POST /run_code {session_id environment_id? code cwd max_output_bytes policy} env binding 409 + workspace 409 + output truncation
POST /install_package {session_id packages}

GET /list_directory?session_id=&path=
GET /read_file?session_id=&path=
POST /write_file
POST /search_in_files
POST /functions_mapping
POST /bracket_tracker
POST /export_artifact

GET /git/{sid}/info/refs
POST /git/{sid}/git-upload-pack records git_pull
POST /git/{sid}/git-receive-pack records git_push+git_head + post-receive hook checkout-f restart

POST /sessions/{sid}/workspace_diff
POST /sessions/{sid}/commit_workspace {commit_message?}
POST /sessions/{sid}/sync_workspace raw gzip
POST /sessions/{sid}/cleanup
POST /sessions/{sid}/respawn

GET /logs
GET /logs/session/{id}
GET /logs/user/{id}
GET /metrics
GET /cache/{*}
DELETE /cache/{*}

GET /admin/sessions
DELETE /admin/sessions/{sid}
GET /admin/sessions/stats
GET /admin/sessions/{id}/activity
```

Reconciled with Server A proxy ALLOWED_TOOLS drift 14 vs 22 — fix merges lists, makes Server A = Server B + ledger.

---

## 7. UI — Runtime Station (2027)

```
┌─ Runtime Station — Server B :8099 internal HMAC ────────────────────┐
│ Session abc123 | env e456 ↔ my-react-app | file_root data/quests/o/  │
│ Policy ttl3600 grace1800 exec30 output200k mem1024 cpu30 disk512     │
│       proc10 network allowlisted | status active golden_image        │
│       runtime-golden-v2-node-python git_head abcdef last_activity 2m │
│ Zones: workspaces/tmp/output/cache/readonly-base/artifacts/git bare  │
│ Queue: MAX_CONCURRENT 10/24 prod 88 queue depth 50 per-user 3/4      │
│ Metrics: wait_ms avg 12 p99 120 exec_ms avg 234 p99 2100 tot comp 1245 err 12
│ Enforcer: active_proc 2/10 disk 341MB/512MB cpu secs 12/30           │
│ Cache: npm-cache 123MB 45 files pip-cache 89MB lock .cache.lock    │
│        prewarm: python 7/10 node 5/8 ✔                               │
│ Processes:                                                            │
│  ● vite dev :5173 PID 1234 [Logs] [Health ✓] [Port ✓ 5173] [Stop]  │
│    logs output/abc123/vite-dev.log stream ████ live                 │
│  ○ node server :3000 ○ stopped [Start] [Logs]                        │
│ Git: bare git/abc123/repo.git 241MB ⚠ leak GC cron nightly          │
│      HEAD abcdef branch main post-receive auto-checkout true        │
│      restart_on_push true hooks pre-receive 50MB file 200MB push    │
│ Sync: idle last 2m tar exclude .git node_modules __pycache__ .venv  │
│       fast_path 🚀 clone --bare prev→new checkout first branch       │
│ Run Code: [editor with Monaco] CWD /workspace env_id e456 MUST      │
│          [Run] 409 handler destroy-recreate-retry automatic          │
│          output 200k truncation meter [██████▒▒ 78%] policy          │
│          snippet .~snippet.py hidden unlink after run                │
│          NODE_PATH venv/bin:node_modules/.bin rewrite python→venv    │
│ Cleanup: session_meta TTL3600 → expired still in active set but meta │
│          missing → cleanup preserve bare + set_grace 1800 → grace    │
│          expired → cleanup_disk + remove active set. Timeline viz    │
│ Bare GC Warning: 241MB + growing nightly — schedule archive S3 + delete│
│ Security: IP allowlist 31.220.96.225 allowlisted via X-Real-IP/XFF   │
│          HMAC METHOD:PATH:BODY+TIMESTAMP+NONCE+CONTEXT context        │
│          JSON{user_id org_id} ±1 window 120s TTL 10k nonce LRU       │
│          Filesystem resolve_workspace_path Path resolve startswith root│
│          resolve_runtime_path only /runtime/{workspaces tmp output cache}│
│          Tar secure skip symlinks/dev absolute/.. target.startswith  │
│          Exec setrlimit DATA not RSS AS stronger + quota + proc limit │
│          Git hooks pre-receive size checks                            │
│ [Admin] /admin/sessions stats activity timeline + tool_ledger 5000    │
│         session_logs 1000 TTL7200 user_logs 999 TTL86400 etc         │
└───────────────────────────────────────────────────────────────────────┘
```

---

See ARCHITECTURE.md §2.4 + app/index.html runtime station + prototype src lib runtime-client.ts
