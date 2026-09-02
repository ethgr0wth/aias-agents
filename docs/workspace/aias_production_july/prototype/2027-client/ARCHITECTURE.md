# AiAS 2027 Client — Architecture

> Built from 81KB backend survey of march_2026. No client/web assumptions.

---

## 0. Principles

1. **Backend is source of truth, frontend is projection.** Never send NQL (spec §11.1). Backend authoritative on permissions (§15). Frontend gating for clarity only.
2. **Credential passport on every request.** X-AiAssist-Provider header ALWAYS (Mark's rule), plus Byok, Agent-Id, Session-Token, Bearer aai_. No silent fallback.
3. **Environment binding mandatory.** PR #34: environment_id on every run_code, 409 destroy-recreate-retry with re-sync, not crash.
4. **Tool parity.** Desktop Quests 12 tools = hosted baseline, not premium. 22 runtime tools + catalog marketplace additive.
5. **Real-time over poll.** 3s polling for messages is legacy. WebSocket /client + /admin with join_workspace, typing 15s TTL, presence, shadow drafts.
6. **v1.1 envelope native.** All responses {data, meta{request_id 16hex next_cursor}, error{code message details}}. Cursor pagination, not page numbers. Capability checks before button enable.
7. **File operations are guarded operations.** 50MB file / 5MB content, BLOCKED_EXT, BLOCKED_NAMES, MALICIOUS_PAT, symlink realpath + post_write_verify delete symlink, destructive guard new/old<0.3 comment placeholder block, SHA256 base_hash conflict detection.
8. **Surgical edits over full rewrites.** insert/replace/delete line-based, reverse order preserve numbers, unified diff preview, find_function_boundaries brace-count string/comment aware.

---

## 1. Topology

```
┌──────────────────────────────────────────────────────────────┐
│ 2027 Client (prototype/2027-client/app/index.html)           │
│  Tailwind CDN + Monaco (lazy) + XState-ish fetch manager     │
│  Credential Vault | Env Deck | IDE v2 | Tool Palette |       │
│  Runtime Station | Artifact Forge | Chat 3 modes | WS        │
└──────────────┬───────────────────────────────────────────────┘
               │ HTTPS /api /v1 /invite /socket.io /quests-preview
               ▼
┌──────────────────────────────────────────────────────────────┐
│ Express server/index.ts :5000 (proxy)                        │
│  Proxy /api /v1 /invite /socket.io /api/v1/pin/ws            │
│  Dynamic /quests-preview/:envId → FASTAPI file_root process  │
└──────────────┬───────────────────────────────────────────────┘
               ▼
┌──────────────────────────────────────────────────────────────┐
│ FastAPI api/main.py :8000 — 32 routers, 55 module inventory  │
│  Middleware: PathBasedCORS (public wildcard /v1/ embed        │
│  webhooks keystone bearer, blog/leads duality dashboard      │
│  detection .replit.dev .app .repl.co localhost DASHBOARD_)   │
│  SecurityHeaders CSP HSTS nosniff SAMEORIGIN strict-origin   │
│  Redis primary prefix aiconsult:/aai: + dual NEDB shim       │
│  Workers: PIN heartbeat daemon asyncio + subscription 60s    │
│  WS: Socket.IO 4.8.1 ASGI /client + /admin namespaces        │
│  Routers: auth users org seats env providers subscription     │
│  billing webhooks pricing_admin reseller control_center etc  │
│  workspaces (CRM invisible co-pilot ai/shadow/takeover)      │
│  contacts leads directives artifacts documents memory          │
│  templates workspaces_stable code_generator deployed_agents │
│  blog embed playground (Oracle) quests (Keystone) pin         │
│  custom_tools artifacts tts voice_actions image_gen           │
│  flashcards web_extraction public_api v1..v11 stable + v1.1  │
└──────────────┬────────────────────────┬───────────────────────┘
               │ HMAC RotatingSecret    │ Redis keys quests:env:{id}
               │ METHOD:PATH:BODY_      │ quests:org:{org}:envs
               │ TIMESTAMP+NONCE+CONTEXT│ pin:operators nodes etc
               ▼                        ▼
┌─────────────────────────┐  ┌────────────────────────────┐
│ runtime_server Server B │  │ Redis + Filesystem         │
│ :8099 internal 127.0.0.1│  │ data/quests/{org}/{env}/   │
│ allowlist + HMAC ±1 win │  │ .quests/project-state.json │
│ TTL 120s nonce 10k LRU  │  │ {selectedAgentName,        │
│ 5 zones workspaces/tmp/ │  │ selectedModelURI,          │
│ output/cache/readonly-  │  │ promptDraft}              │
│ base + artifacts + git/ │  │ RUNTIME_ROOT /tmp/runtime_b│
│ {sid}/repo.git bare     │  │ workspaces/<sid> tmp/<sid>  │
│ bare leak → no GC       │  │ output/<sid> cache/<sid>  │
│ RuntimeManager 47KB     │  │ readonly-base artifacts   │
│ CacheManager fcntl lock │  │ shared/npm-cache pip-cache│
│ ExecutionQueue Sem 10/24│  │ git/<sid>/repo.git        │
│ per-user 3/4 + queue    │  │ Storage keys ses_logs etc │
│ ResourceEnforcer        │  │ session_meta TTL 3600     │
│ setrlimit DATA not RSS  │  │ grace TTL 1800 cleanup    │
│ bug QueueMiddleware     │  │ env_last_session TTL7d    │
│ call_next immediately   │  │ session_env TTL7d manifest│
│ rather than lambda      │  │ TTL7200 etc               │
└─────────────────────────┘  └────────────────────────────┘
```

---

## 2. Layer Model

### 2.1 Credential Layer (src/lib/api-client.ts)

```
CredentialPassport {
  primary: { type: Bearer aai_ | aai_pub_ | aai_srv_, token, scopes: chat:completion workspace:* ..., domainRestrictions, usageLimits, ipAllowlist, createdAt, lastUsed },
  byok: {
    groq: { keys: [{key, role: primary|backup, masked, lastTested, tokensUsedToday}], preferred: provider, priority: number, modelPreferences },
    openai: {...}, anthropic, gemini, mistral, xai, together, openrouter, deepseek, fireworks, perplexity, pin (credit-based)
  },
  headers: {
    "X-AiAssist-Provider": "<always> — groq|openai|anthropic|gemini|mistral|xai|together|openrouter|deepseek|fireworks|perplexity|pin",
    "X-AiAssist-Byok": "<optional raw key override>",
    "X-Agent-Id": "<deployed-agent-id optional>",
    "X-Session-Token": "<session_token for cross-origin Keystone Lite windowed apps>",
    "Authorization": "Bearer aai_xxx | session cookie",
    "X-API-Key": "alternative to Bearer"
  },
  resolution: header_override → model_inference get_provider_for_model → user_default → PIN fallback,
  rateLimit: { rpm, monthly_tokens, api_keys, models: [...] } per PLAN_LIMITS free 10 rpm basic 120 pro 300 ent 600,
  display: vault drawer with masked keys + test + usage meter + scopes + domain + IP + primary/backup toggle + priority drag
}
```

Rules:
- X-AiAssist-Provider ALWAYS sent — no exceptions (Mark's rule)
- Dual transport: same-origin cookie OR cross-origin X-Session-Token header (Keystone Lite windowed apps)
- Bearer aai_ for /api/keystone + /v1/ + embed public, cookie for dashboard private /api/*
- Extended types aai_pub_ / aai_srv_ with scopes
- BYOK multi-key per provider primary/backup
- Credit-based PIN: pin_get_user_billing credits_balance <=0 → insufficient error
- Models cache 5min Groq dynamic fetch filter whisper/tts/guard/vision/preview, priority sort llama-3.3>3.1>mixtral>gemma>qwen>deepseek

### 2.2 Environment Layer (src/lib/env-manager.ts)

```
EnvironmentDeck {
  org_id, user_id, id, name, description, template_id, status active|paused|expired, llm_provider, llm_model,
  file_root: data/quests/{org}/{env}, preview_port, .quests/project-state.json {selectedAgentName, selectedModelURI, promptDraft},
  limits: free 0 basic1 pro5 ent100 meter with bar,
  sync: {
    packing: tar.gz exclude .git node_modules __pycache__ .venv venv,
    secureExtract: skip symlinks/dev absolute/.. target.startswith workspace+sep counting files,
    debounce: 10s threading.Timer mark_dirty → _fire_commit proxy POST sessions/{id}/commit_workspace message flush_now cancel,
    notify: notify_file_change → commit manager,
    status: idle|packing|uploading|extracting|committing|error,
    timeline: WorkspaceDiff git add -A diff --cached --quiet commit AiAS author,
    fastPath: checkout_from_previous_bare git clone --bare prev→new checkout first branch or HEAD,
    ttl: env_last_session org:user:env TTL7d session_env TTL7d,
    leakWarning: bare git/<sid>/repo.git never GC → disk growth need cron GC,
    recovery: 409 environment binding mismatch → auto destroy + recreate + re-sync toast no data loss
  },
  stack: detect_stack package.json requirements.txt pyproject.toml Pipfile Dockerfile → auto install,
  nodeDeps: npm ci if frozen_lockfile && package-lock else install + --cache <shared> --prefer-offline fcntl lock 180s,
  pythonDeps: pip --cache-dir <shared> cascade venv python3 -m venv → --without-pip → ensurepip --upgrade → bootstrap urllib get-pip.py fallback checks bin existence,
  policy: RuntimePolicy ttl3600 grace1800 exec30 output200k mem1024 cpu30 disk512 processes10 network allowlisted|deny,
  sessionState: id/user/org/env/created_at/golden_image runtime-golden-v2-node-python status active|resetting|destroyed|cleaned policy last_activity git_head preserve_bare
}
```

Rules:
- File root visible always, not hidden abstraction
- Sync status live with packing/exclude list
- Commit timeline with diff view
- 409 mandatory binding: client MUST include environment_id per PR #34, handle destroy-recreate-retry automatically
- Bare leak GC: needs cron admin, warn in UI when disk usage > threshold

### 2.3 File Layer (QuestsFileService)

```
FileGuard {
  validatePath: abspath strip leading slashes \ remove .. replace re \.\.+ '' normpath join root, full_path.startswith(root) else traversal error, filename safety,
  verifyNoSymlinks: abspath loop parent != root && != dirname check islink → error, exists realpath startswith root else outside sandbox,
  postWriteVerify: islink → rm → error, realpath startswith root else rm outside sandbox,
  blockedExt: .exe .dll .so .dylib .bin .sh .bash .zsh .ps1 .bat .cmd,
  blockedNames: passwd shadow .bashrc .zshrc .profile .ssh id_rsa id_ed25519,
  maliciousPat: rm -rf / sudo chmod 777 eval( exec( __import__( subprocess. os.system os.popen shell=True crypto miner keylogger reverse shell bind shell payload= exploit malware trojan backdoor rootkit ransomware phishing steal password|credential|token|cookie bypass auth|security|firewall,
  contentSafety: content.lower() regex malicious patterns,
  maxFile: 50MB, maxContent: 5MB, maxFilesPerEnv: 1000,
  destructiveGuard: original>500 && new/old<0.3 && _is_mostly_comments_or_placeholders → block,
  binaryDetect: 10MB read limit,
  tree: maxDepth10, stat size modified,
  hash: SHA256 conflict detection base_hash,
  diffPreview: unified_diff,
  applyEdits: reverse order preserve numbers, operations_applied, new_hash, new_size, conflict bool + message,
  previewEdits: without apply,
  functionBoundaries: find_function_boundaries content function_name regex JS/TS Go Rust Python C++ brace counting string/comment aware Python indent fallback,
  listFunctions: regex c_function method js_function arrow go rust python,
  glob: pattern **/* default, files count,
  grep: pattern regex file_pattern count,
  download: FileResponse single, download-all zip exclude node_modules __pycache__ .git venv .venv Tempfile cleanup background task safe name alnum -_ safe,
  github: validate github.com {owner}/{repo} regex, url branch main subdir, clone target,
  templates: 5 builtins react-vite next-app node-express python-fastapi blank copy_template_files _create_builtin_template writes index.html/js/etc blank README name/desc + registry path quests-engine/registry submodule live copy
}
```

Rules:
- Surgical edits mandatory over full rewrites for >500 char files
- Hash conflict before edit
- Preview before Apply All
- Myers diff 8000 lines cap
- Monaco lazy + function tree + bracket balanced guard

### 2.4 Runtime Layer (src/lib/runtime-client.ts)

```
RuntimeStation {
  sessions: { sid, user_id, org_id, env_id, policy, git_head, status, created_at, last_activity },
  processes: { sid: { name: { Popen pid cmd port } } } specs {repo_dir, command, port} logs {name: Path output/<sid>/<name>.log},
  queue: ExecutionQueue Semaphore MAX_CONCURRENT 10 prod 24 MAX_QUEUE_DEPTH 50 prod 88 MAX_PER_USER 3 prod 4 user_counts pending execute acquire wait_ms exec total_completed/errors exec_ms release metrics snapshot avg wait/exec sliding 1000→500,
  queueMiddleware: QUEUED_PATHS /run_code /clone_repo /install_node_deps /install_python_deps /install_package /start_process bug call_next(request) creates coroutine immediately not after admission → lambda fix needed,
  enforcer: SessionResourceTracker active_processes disk_usage_bytes limits measure du -sb fallback rglob make_preexec_fn setrlimit RLIMIT_CPU max_cpu optional RLIMIT_DATA vs AS stronger, disk quota check before writes process limit before spawn,
  storageKeys: tool_ledger 10k session_logs 1k TTL7200 user_logs 999 TTL86400 org_logs error_counts hash tool_counts latency:{tool} list500 manifest:{sid}:{eco} TTL7200 session_metrics session_meta TTL ttl JSON session_id user_id org_id created_at last_activity last_page last_click cookie_snapshot activity_count active_sessions set activity_stream 500 TTL2*ttl user_activity 1000 TTL86400 session_grace TTL grace env_last_session org:user:env TTL7d session_env TTL7d etc methods register/touch/record_activity/get_activity_stream/user_activity/session_activity_summary breakdown500 get_session_meta list_all_sessions remove_session deletes meta/set/logs/metrics/activity/grace/env expired via exists grace expired,
  sessionActivity: ts session_id user_id kind page_visit click cookie_update api_call git_push git_pull process_start process_stop file_edit code_run session_create session_respawn idle_ping custom page element_id cookie_keys metadata ip user_agent,
  gitHookConfig: max_file 50MB max_push 200MB auto_checkout true restart_on_push,
  gitFlows: client push http://.../api/runtime/git/{sid}/git-receive-pack → Server A proxy_raw preserve content-type application/x-git-*-result → Server B git-receive-pack --stateless-rpc → bare updated → post-receive checkout -f workspace → _handle_post_receive git_head → _restart_session_processes, info/refs pkt-line header, upload-pack pull,
  cleanupLoop: 120s grace_expired → cleanup_session_disk remove tracking bare preserved + expired → cleanup preserve bare + set_grace grace_secs 1800,
  tools: clone_repo checkout_ref detect_stack install_node_deps install_python_deps write_env_file start_process stop_process check_port http_health_check stream_logs capture_preview_metadata export_artifacts run_code (env binding 409 if mismatch workspace 409 output truncation policy) install_package read_file write_file quota list_directory search_in_files functions_mapping bracket_tracker export_artifact session_reset 22 allowed but Server A proxy ALLOWED_TOOLS only 14 = drift,
  codeAnalysis: functions_mapping ast parse, bracket_tracker stack ()[]{} balanced, search_in_files regex rglob max200 trunc240, git bare hooks bash post-receive auto-checkout echo HEAD pre-receive size checks,
  executionFlows: create→sync→run POST /api/runtime/sessions env_id → Server B create UUID mkdirs register Redis TTL check env_last_session prev bare clone bare + checkout else init_bare POST /api/runtime/sync_workspace tar.gz QuestsFileService exclude .git node_modules etc raw POST Server B /sessions/{sid}/sync_workspace secure extract git add -A commit sync from keystone + POST /run_code validates env binding workspace exists runs snippet .~snippet.py/.js with venv injection NODE_PATH preexec_fn limits checks max_output_bytes,
  proxy: api/routes/runtime.py 689lines DEPLOYMENT_TOOLS+SAFE_CODE_TOOLS=ALLOWED_TOOLS 14 ledger in-memory 5000 _env_sessions map env→session get_runtime_user Bearer aai_ via get_api_key_by_secret OR cookie/header _session_token_from requires pro|enterprise or manager proxies all to runtime_proxy logs ledger handles sync_workspace tar from QuestsFileService exclude _commit manager routes commit_message flush_commit,
  runtime_proxy.py 192lines RUNTIME_REMOTE_URL context X-Runtime-Context signs RotatingSecretAuth duplicate shared_secret.py POST/GET/DELETE requests latency log _proxy_status/_proxy_error 429/400+ map proxy_request_raw binary git/tar proxy_health /health,
  runtime_service.py legacy in-process without enforcer/cache/grace fallback if REMOTE_URL unset per DEPLOYMENT.md comment current returns 503,
  workspace_commit_manager.py debounce 10s Timer mark_dirty schedule _fire_commit proxy POST sessions/{id}/commit_workspace message flush_now cancel
}
```

### 2.5 IDE v2 (Keystone)

```
KeystoneV2 {
  agents: {
    app-builder: [EditFile Glob Grep ReadFile RunDiagnostics RunShellCommand Think WriteFile] system prompt fileTree AGENTS.md package.json deps security refusal tone/style runtime env notes Be proactive balance Doing right thing vs not surprising user + ShouldContinue pending tool parts + explanation param batch tool calls parallel,
    chat: [ReadFile Glob Grep] read-only conversational
  },
  xstate: {
    agentMachine: Starting->RequestingLLM->ProcessingResponse->ExecutingToolCalls->Finishing actors llmRequestLogic executeToolCallMachine onStart onFinish saveMaxStepsMessage shouldContinue retry backoff exp baseLLMRetryDelayMs*2^(retry-1),
    sessionMachine: owns agentRef queue queuedMessages saveQueuedMessage updateSession generateSessionTitle,
    workspaceMachine: top-level sessionRefsBySubdomain Map<AppSubdomain ActorRef[]> previews runtimes heartbeat createSession addMessage restartRuntime message union CheckoutVersionParentEvent CreatePreviewParentEvent SessionMachineParentEvent WorkspaceServerParentEvent,
    runtime: dev server lifecycle PortManager reserve getPackageManager execaNodeForApp getFramework @netlify/build-info etc
  },
  server: Hono user apps all-proxy assets heartbeat redirect shim-iframe shim-script websocket-proxy,
  chatModes: {
    keystoneIDE: _build_quests_system_prompt <<FILE>>>/<<EDIT>>> markers Api.AiAssist.net/v1 ref read_only teaching mode + 4k file list + line-numbered 50k 5files 30k each extraction regex _extract_file_references _read_files_for_context _truncate_context 60k strip code blocks old msgs dir detection regex parsing REPLACE lines X-Y/INSERT/DELETE writes via write_file edits via _apply_pending_edits streaming loop tool_round KEYSTONE_IDE_TOOLS 5 OpenAI function tools auto-recovery rate-limit/context overflow/max_tokens,
    focus: docs only .md README first,
    gex: debug fixes AiAS API usage
  },
  ideTools: 5 listed vs desktop 12 — gap to close in 2027,
  frontend: QuestsWorkspace 208k // @ts-nocheck port fileTree FileNode selectedFile openTabs[] tabContents Record<path {content,original}> Monaco refs stream AbortController TOOL_COLORS clone blue run_code emerald read_file amber search purple extractFilePaths <<<FILE|CREATE (.*)>>> extractEditPaths <<<EDIT ParsedBlock text|file|edit filename language editOps[] parseContentForDisplay overlap detectStreamingBlock tail computeDiff Myers 8000 cap streaming SSE approxTokens len/3.5 incremental marker Apply All GitHub clone modal context reset read-only toggle temp maxTokens persona artifacts loader /api/artifacts?limit=100 import via write file + ext map python:.py ts:.ts artifact to env import search bracket/function resizable panels,
  QuestsPortal env grid/list filter status environments_count limit features chat file_ops templates preview build create dialog framer-motion cards delete optimistic,
  shim: error-overlay overlay recovery-overlay injected into iframe,
  fileTree ignore .gitignore filter,
  projectState: .quests/project-state.json selectedAgentName selectedModelURI promptDraft migration,
  aiGateway: canonicalize migrate generate sort models fetch-model(s) fetch-credits metadata set-auth-headers
}
```

### 2.6 Tool System

Per TOOL_SYSTEM.md.

### 2.7 v1.1 Enveloped API

```
Envelope {
  data: stripped engine metadata no _ prefix + seq exposed,
  meta: { request_id 16hex, next_cursor optional },
  error: { code, message, details } code WORKSPACE_NOT_FOUND 404 THREAD_ROOT_NOT_FOUND 404 MESSAGE_NOT_FOUND 404 RUN_NOT_FOUND 404 AGENT_NOT_ON_ROSTER 404 WORKSPACE_FORBIDDEN 403 MESSAGE_FORBIDDEN 403 CAPABILITY_REQUIRED 403 ROSTER_FULL 409 RUN_TRANSITION_INVALID 409 MESSAGE_DELETED 409 WORKSPACE_KIND_INVALID 422 ACTIVATION_MODE_INVALID 422 AI_POLICY_INVALID 422 VALIDATION 422 + 503 NEDB_REQUIRED,
  guard: V11Error -> enveloped error stable code,
  pub: docs no _ prefix seq exposed for cursors,
  capabilities: _BASE_CAPS team.view conversations.create messages.send agents.view agents.activate,
  browserNeverSendsNQL spec §11.1 backend auth §15,
  thinLayer: route bodies validate scope/shape, query CAS transaction v1_1_native 39 checks proven test_nedb_v11_foundation.py
}
```

### 2.8 Realtime (WebSocket)

```
SocketIO {
  sio AsyncServer cors_allowed_origins * logger off engineio off,
  namespaces: /client connect disconnect join_workspace workspace_id validation enter_room ws:{id} send_message content role USER add_message safe_dump emit admin message_new mode !=TAKEOVER typing true orchestrator.generate_response typing false AI role add_message metadata model emit room + admin shadow drafts latest emit draft_created awaiting_approval, /admin subscribe_dashboard subscribe_workspace send_as_ai change_mode ai|shadow|takeover inject_directive,
  typing: Redis typing:{wsId} 15s TTL typing_start/stop/preview 15s,
  client_sessions admin_subscriptions presence,
  2027 replaces 3s poll with WS join + typing indicators + shadow inbox
}
```

---

## 3. File Layout for Prototype

```
prototype/2027-client/
  BACKEND_BASELINE.md — 81KB full
  README.md — vision credential-aware env-bound tool-complete
  ARCHITECTURE.md — this file
  CREDENTIAL_SYSTEM.md
  ENVIRONMENT_SYSTEM.md
  TOOL_SYSTEM.md
  RUNTIME_SYSTEM.md
  KEYSTONE_IDE_V2.md
  WIREFRAMES.md
  app/
    index.html — single-file Tailwind CDN polished interactive
  src/
    lib/
      api-client.ts — credential-aware + 409 handling
      env-manager.ts — env binding + sync + commit timeline
      runtime-client.ts — Server B HMAC + queue + process mgmt
      tool-palette.ts — unified 12+22+catalog+ledger
    types/
      runtime.ts — mirrors models.py
      keystone.ts — mirrors quests_service
      envelope.ts — v1.1 data/meta/error
    components/ — TSX sketches spec not built
  package.json — meta
```

---

## 4. API Mapping Every Pixel

| UI surface | Backend endpoint | File |
|-----------|-----------------|------|
| Credential vault | GET /api/providers + users api-keys + provider credentials | users.py providers.py |
| Env deck limit meter | GET/PATCH /api/keystone/environments + count + ENV_LIMITS free0 basic1 pro5 ent100 | quests.py quotas |
| File tree | GET /api/keystone/environments/{id}/files/tree maxDepth10 + read/hash/function/functions/glob/grep/download | quests_service get_file_tree 10MB binary detect |
| File edit surgical | POST /api/keystone/environments/{id}/files/edit insert/replace/delete base_hash diff preview unified reverse + preview | apply_edits apply_edit_operations generate_diff_preview |
| Mkdir/rename/delete | POST/DELETE /api/keystone/environments/{id}/files/mkdir|delete|rename | QuestsFileService |
| Git clone | POST github/clone url branch subdir → /api/keystone/environments/{id}/github/clone | github URL pattern |
| Chat non-stream | POST /api/keystone/environments/{id}/chat/reset + /chat + /chat/history | _build_*_system_prompt context extraction truncation |
| Chat stream SSE | POST /api/keystone/environments/{id}/chat/stream tool_round KEYSTONE_IDE_TOOLS | streaming loop + IDE tools + auto-recovery |
| Templates | GET /api/keystone/templates/{id} + copy_template_files 5 builtins + registry submodule | TemplateService REGISTRY_PATH |
| Status run/stop/logs/process | GET /api/keystone/status POST /run|stop|restart GET /process /logs?lines= /git/init/status/add/commit/log | QuestsFileService |
| Runtime sessions | POST /api/runtime/sessions GET /sessions env_id → Server B create UUID + env_last_session | runtime.py |
| Runtime sync | POST /api/runtime/sync_workspace tar.gz QuestsFileService exclude .git node_modules... → Server B secure extract | sync_workspace_from_tar |
| Runtime run_code | POST /api/runtime/run_code env binding mandatory 409 destroy-recreate-retry | runtime_manager run_code |
| Runtime processes | POST /api/runtime/start_process stop_process list check_port http_health_check stream_logs capture_preview_metadata export_artifacts | RuntimeManager |
| Runtime git smart | POST /api/runtime/git/{sid}/info/refs upload-pack receive-pack proxy_raw preserve content-type | git bare + hooks |
| Runtime workspace diff | GET /sessions/{sid}/workspace_diff + commit_workspace debounce 10s mark_dirty | workspace_commit_manager |
| Tool workspace | GET/POST /api/workspaces/{id}/tools + {tool_id}/test/invocations/replay + policy | custom_tools.py TOOL_PLAN_LIMITS |
| Tool org | GET/POST /api/org/tools + public/catalog enable/disable | org_router enable_public_tool etc |
| Artifact forge | POST /api/artifacts GET limit offset PATCH DELETE + POST /api/playground/sessions {sid}/chat/stream extraction <<<FILE>>> fallback fence stage timer labels stack heuristic | artifacts.py playground.py |
| Playground sessions | POST/GET/PATCH/DELETE /api/playground/sessions + /sessions/{id}/chat stream web_tool none|search|visit voiceActionScope directives guidance|tone|context|constraint knowledge manual/upload web extraction visit_url tool pre-execution keyword [LIVE TOOL DATA] | playground.py |
| PIN | GET /api/v1/pin/network status stats operators models health POST /api/v1/pin/chat/completions credits WSS /api/v1/pin/ws AUTH REGISTER_NODE PONG HEARTBEAT etc | pin.py WsManager pin_service storage pin_* |
| Workspaces CRM | /api/workspaces CRUD bulk-mode mode-summary messages directives typing drafts approve/reject/regenerate + WS /client + /admin | workspaces.py DESIGN.md |
| Public API | /v1/chat/completions models providers usage search intelligence | public_api.py X-Provider ALWAYS |
| v1.1 | /api/v1.1 envelope data/meta/error request_id 16hex next_cursor capability checks team.view etc browser never NQL | v1_1.py v1_1_native.py 39 checks |
| WS | /client join_workspace send_message typing_start/stop/preview 15s TTL + /admin subscribe dashboard workspace send_as_ai change_mode inject_directive presence | websocket.py |
| Middleware | PathBasedCORS public wildcard /v1/ embed webhooks keystone bearer blog/leads duality dashboard detection + SecurityHeaders CSP HSTS + PIN heartbeat + subscription lifecycle | main.py |

---

## 5. Security Checklist for 2027 Client

- [ ] Path resolving startswith root + realpath symlink guard + post_write_verify delete symlink + blocked ext/names + malicious pattern + destructive guard + blocked IP private/reserved SSRF + git hooks size + RotatingSecretAuth ±1 window 120s TTL 10k LRU + IP allowlist + quota + anon 20/hr + keystone 30/min file 100/min env create 1/hr
- [ ] CORS identical preserve — avoid net::ERR_FAILED regression
- [ ] Blob leak GC cron for bare git/<sid>/repo.git
- [ ] QueueMiddleware lambda fix call_next(request) coroutine immediate → lambda
- [ ] Hardcoded secret in start.sh rotated
- [ ] RLIMIT_DATA → RLIMIT_AS
- [ ] Bare never GC disk growth warning threshold UI

---

Generated 2026-07-14 for 2027 credential-aware env-bound tool-complete client
Branch feature/2027-client-prototype → march_2026
