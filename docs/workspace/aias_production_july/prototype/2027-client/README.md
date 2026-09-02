# AiAS 2027 Client — Credential-Aware, Environment-Bound, Tool-Complete

> The next-generation client prototype. Built from a full backend inventory of march_2026 (55 routers, runtime Server B, Keystone/Quests, PIN, custom tools, v1.1 envelope, WebSocket realtime).

**Status:** Prototype branch `feature/2027-client-prototype`
**Baseline:** `docs/BACKEND_SURVEY_2027_BASELINE.md` (81KB, 400+ capabilities mapped)
**Directive:** Ignore existing client/ and web/ — design from bare metal for 2027

---

## Vision: AiOS Command Deck

The 2026 client is a dashboard that polls. The 2027 client is a command deck that binds.

Three words: **Credential-Aware, Environment-Bound, Tool-Complete**

### Credential-Aware
Today: hidden Bearer tokens, leaked BYOK, confused X-AiAssist-Provider header (Mark's rule: ALWAYS send it), three key types aai_/aai_pub_/aai_srv_ with scopes/domain/IP limits nobody surfaces.

2027: Every request carries a credential passport you can SEE, AUDIT, and SWAP. BYOK primary/backup per provider, domain restrictions, usage meters, IP allowlists — all in a vault drawer, not buried in settings.

- Header contract visible: `X-AiAssist-Provider` (ALWAYS) + `X-AiAssist-Byok` + `X-Agent-Id` + `X-Session-Token` + `Authorization: Bearer aai_`
- Dual auth: cookie session_id + X-Session-Token for cross-origin Keystone Lite windowed apps
- Key types surfaced: standard, extended pub/srv with scopes chat:completion workspace:* etc
- Provider router: header override → model inference → user default → PIN fallback (credit-based)

### Environment-Bound
Today: file_root is `data/quests/{org_id}/{env_id}/` on disk but abstracted away, env limit free:0 basic:1 pro:5 ent:100 hits as surprise 403, PR #34 env binding mandatory 409 destroys session without retry UX, bare git repos leak forever, sync tar excludes .git node_modules __pycache__ .venv silently, commit manager debounce 10s invisible.

2027: Environments are first-class citizens you live in. File root path visible, sync status live, commit timeline, 409 destroy-recreate-retry handled automatically, limit meter always on.

- Env picker with limit bar (free 0 / basic 1 / pro 5 / ent 100)
- File root display: `data/quests/{org}/{env}` + preview_port + .quests/project-state.json {selectedAgentName, selectedModelURI, promptDraft}
- Sync indicator: tar.gz pack exclude list, debounce 10s auto-commit, diff view, GC warning for bare leak
- 409 recovery: "environment binding mismatch" → auto destroy + recreate + re-sync with toast, no data loss
- Stack detection: package.json / requirements.txt / pyproject.toml / Pipfile / Dockerfile → auto install with fcntl shared cache
- Venv cascade visualization: python3 -m venv → --without-pip → ensurepip → get-pip.py bootstrap

### Tool-Complete
Today: Desktop Quests has 12 tools (EditFile, Glob, Grep, ReadFile, RunDiagnostics, RunShellCommand, Think, WriteFile, FileTree, RunGitCommands, Choose, FunctionsMapping) vs hosted Keystone only 5 (clone_repo, read_file, search_files, glob_files, list_functions). Runtime Server B allows 22 tools but Server A only exposes 14 (drift). Custom tools workspace/org/public catalog exists but no marketplace UI. Ledger 5000 entries invisible.

2027: Unified tool palette — desktop parity + runtime + custom catalog + ledger, permissioned per plan TOOL_PLAN_LIMITS free 2/100 basic 5/1000 pro 20/10000 ent -1, SSRF-guarded webhooks, builtin 23 actions, envelope with confidence/duration/invocation_id.

- Tool drawer: All 12 desktop + 22 runtime (run_code, install_package, read_file, write_file, list_directory, search_in_files, functions_mapping, bracket_tracker, export_artifact, clone_repo, checkout_ref, detect_stack, install_node_deps, install_python_deps, write_env_file, start_process, stop_process, check_port, http_health_check, stream_logs, capture_preview_metadata, export_artifacts, session_reset) + custom workspace/org/public
- Catalog marketplace: enable/disable public tools, test/replay with SSRF check (BLOCKED_HOSTS localhost 127.0.0.1 0.0.0.0 169.254.169.254 metadata.google.internal, private IP via ipaddress)
- Builtins: create_note, escalate→SHADOW, schedule_callback Redis SETEX, calculate, json_transform, timestamp_util, validate_data, regex_test, create_task, create_ticket, status_check, log_expense, read_url, summarize, sentiment_analysis, translate, extract_keywords, draft_email, meeting_prep, draft_proposal, generate_invoice, knowledge_search, faq_lookup, send_email, signal_scan (execute_code sunsetted)
- Ledger: invocation history 100 limit, replay, confidence, duration, status success/error/validation_error, policy tool_mode max_tools_per_turn max_calls_per_minute timeout allow_parallel require_confirmation fallback

---

## What's in this prototype folder

```
prototype/2027-client/
├── BACKEND_BASELINE.md      — 81KB full inventory (copied from docs/)
├── README.md                — this file, vision
├── ARCHITECTURE.md          — technical architecture for 2027 client
├── CREDENTIAL_SYSTEM.md     — credential-aware design, header contract, vault
├── ENVIRONMENT_SYSTEM.md    — environment-bound design, sync, 409, GC
├── TOOL_SYSTEM.md           — tool-complete unification
├── RUNTIME_SYSTEM.md        — Server B session lifecycle, queue, enforcer, storage
├── KEYSTONE_IDE_V2.md       — IDE v2 with 12-tool parity, sentinel parsing, artifacts
├── WIREFRAMES.md            — UX flows, command deck layout
├── app/
│   └── index.html           — INTERACTIVE PROTOTYPE (single file, polished, no build)
├── src/
│   ├── lib/
│   │   ├── api-client.ts    — credential-aware client (X-Provider ALWAYS + 409 handling)
│   │   ├── env-manager.ts   — env binding + sync + commit timeline
│   │   ├── runtime-client.ts — Server B HMAC + queue + process mgmt
│   │   └── tool-palette.ts  — unified 12 + 22 + catalog + ledger
│   ├── types/
│   │   ├── runtime.ts       — mirrors runtime_server/models.py
│   │   ├── keystone.ts      — mirrors quests_service models
│   │   └── envelope.ts      — v1.1 data/meta/error
│   └── components/          — TSX sketches (not built, spec)
└── package.json             — prototype meta
```

---

## Quick start — Interactive prototype

Open `app/index.html` directly in browser (no build). It's a single-file Tailwind CDN + vanilla JS simulation of:

- Credential vault (provider picker, BYOK toggle, scopes, limit meter)
- Environment deck (limit bar free0/basic1/pro5/ent100, file_root, sync status, commit timeline, 409 recovery)
- Keystone IDE v2 (file tree depth 10, Monaco mock, function map, bracket guard, hash conflict, sentinel parsing <<<FILE>>> / <<<EDIT>>> REPLACE lines)
- Tool palette (desktop 12 + runtime 22 + catalog + ledger with replay)
- Runtime station (sessions, processes, logs stream, port health, preview iframe /quests-preview/:envId, queue metrics wait/exec, resource enforcer)
- Chat 3 modes (keystone / focus docs-only / gex debug) with SSE streaming meta/chunk/tool_start/exec/done + artifact forge stage timer Initializing Analyzing Designing Writing Finalizing + stack detection
- WebSocket realtime (join_workspace, typing 15s TTL, presence, shadow draft inbox approve/reject/regenerate)

```
open prototype/2027-client/app/index.html
```

---

## Backend guarantee

Every pixel maps to a real endpoint in march_2026:

- `api/main.py` 32 routers + PathBasedCORS critical fix + SecurityHeaders + PIN heartbeat + subscription lifecycle + Socket.IO ASGI
- `runtime_server/` 41KB app + 47KB manager + 10KB storage + 7KB cache + 4KB queue + 3KB enforcer + hardcoded secret leak in start.sh
- `quests-engine/` pnpm monorepo Electron v1.7.5-beta.3 workspace core 23k LOC agents tools machines XState lib 70+ ai-gateway shim-client registry templates
- `api/routes/quests.py` 3324 LOC + `quests_service.py` 47KB — env CRUD, FS ops with BLOCKED_EXT/BLOCKED_NAMES/MALICIOUS_PAT/destructive guard/symlink realpath/hash conflict, surgical edits diff preview, file analysis ast + bracket stack, template service 5 builtins + registry submodule
- All 55 routers inventoried

See BACKEND_BASELINE.md for 800-line taxonomy.

---

## Next steps to ship

1. **Auth layer:** Implement src/lib/api-client.ts with credential passport (X-Provider ALWAYS, 409 retry)
2. **Env layer:** Env picker + file_root + sync tar + commit debounce 10s + GC cron for bare leak
3. **Tool layer:** Unify 12 + 22 + catalog, expose ledger, SSRF test UI
4. **Runtime layer:** Session lifecycle TTL 3600 grace 1800 cleanup 120s, process mgmt, fcntl cache, venv cascade viz
5. **IDE layer:** Monaco + file tree depth 10 + function map + bracket guard + sentinel parsing + Myers diff 8000 lines + artifact deploy to Keystone
6. **Realtime layer:** Replace 3s poll with Socket.IO /client + /admin join_workspace typing 15s presence shadow drafts
7. **v1.1 migration:** Consume envelope {data, meta{request_id 16hex next_cursor}, error{code}} + capabilities team.view etc, browser never sends NQL

Branch: `feature/2027-client-prototype` → PR to `march_2026`
