# Wireframes — 2027 Command Deck

> Layout: Credential Vault drawer + Env Deck top bar + IDE center + Tool Palette right + Runtime Station bottom + Chat right + Artifact Forge modal + WebSocket presence top

---

## 1. Global Shell

```
┌─ Top Bar ──────────────────────────────────────────────────────────────┐
│ [AiAS 2027] Environments [my-react-app ▼] file_root data/quests/o/e  │
│ Sync: ● idle last 2m [Timeline] Bareness ⚠ GC 241MB  Binding ✓      │
│ Presence ● 2 online typing ... [User1 typing App.tsx:45] WS ●       │
│ Credential Vault [aai_srv_ ****abcd groq ALWAYS ✓] [PIN 1240 creds]  │
│ Env Limit 2/5 [████▒▒] pro Plan free0 basic1 pro5 ent100 Upgrade CTA  │
│ Queue wait 12ms exec 234ms depth 0/50 per-user 0/3 429 none           │
└──────────────────────────────────────────────────────────────────────┘
┌─ Left Nav ──┐┌─ Center IDE ─────────┐┌─ Tool Palette ─┐┌─ Chat ─────┐
│ [Vault]     ││ File Tree depth10    ││ Desktop 12     ││ 3 modes    │
│ [Envs]      ││ App.tsxFuncs▼Brace✓  ││ Runtime 22 drift⚠││ Keystone   │
│ [IDE]       ││ Monaco editor   [    ││ Workspace 2/10 ││ Focus docs │
│ [Tools]     ││ surgical preview diff]││ Org 1/-1 ent   ││ Gex debug  │
│ [Runtime]   ││ Terminal logs health ││ Catalog public ││ SSE meta   │
│ [Forge]     ││ preview /q/e iframe ││ Ledger replay  ││ chunk tool │
│ [Playground││ [Preview Open]       ││ Policy auto etc││ start exec │
│ [PIN]       ││ ...                  ││                ││ done error │
│ [WS Logs]   ││                      ││                ││ artifact   │
│ [Settings]  ││                      ││                ││ forge stage│
└──────────────┘└─────────────────────┘└────────────────┘│ voice etc  │
              ┌─ Runtime Station bottom ─────────────────┘│ timeline   │
              │ Sessions processes queue queueMiddleware bug│ Presence ● │
              │ Enforcer cache npm-cache pip-cache lock   │ Typing 15s │
              │ Git bare leak GC cron | sync debounce10s  │ Shadow inbox│
              │ Run .~snippet.py NODE_PATH venv rewrite   │ approve etc│
              └───────────────────────────────────────────┘└────────────┘
┌─ Bottom ───────────────────────────────────────────────────────────────┐
│ Status: Server A 32 routers + File Guard 50MB/5MB blocked exts names  │
│ malicious destr SVG symlink guard + bare leak + QueueMiddleware lambda│
│ + RLIMIT_DATA→AS + secret in start.sh leak + CORS PathBased fix +     │
│ SecurityHeaders CSP HSTS + PIN heartbeat + subscription lifecycle WS   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 2. Vault Drawer Flow

Open → sees:

- Active key card with masked key click reveal TOTP gate + scopes domain IP usage RPM meter + scopes
- BYOK list drag to priority order + primary/backup toggle + test button → `GET /v1/models` with header override → green/red
- Headers section: X-Provider ALWAYS pill green, X-Byok (none) + override ephemeral warning, X-Agent-Id none, X-Session-Token 7d expiry 2026-07-21
- Resolution badge: header_override → groq → BYOK ✓ credit_based false
- PIN credits 1240/10000 bar price slider $0.05-0.50/1K region us-east tier verified >90% 20tok/s green
- Upgrade bar free 0 envs → pro 5 envs

Test flow:

1. User clicks Test groq primary key
2. Client sends `GET https://api.aiassist.net/v1/models` with `Authorization: Bearer sk-proj-... + X-AiAssist-Provider: groq`
3. Backend dynamic fetch `https://api.groq.com/openai/v1/models` filter whisper/tts/guard/vision/preview, naming Llama etc priority sort
4. Surface green check + models list `llama-3.3-70b-versatile llama-3.1-8b-instant mixtral-8x7b-32768` + context_window
5. Audit log: tested at 10:42 by IP ...

---

## 3. Env Deck Flow

- Click environment card → opens IDE v2 with file_root displayed + sync status
- New env dialog: name desc template select 5 builtins + registry submodule live list `basic angular astro htmx nextjs nuxt micro-chatbot ai-chess chat-with-files prompt-library empty` tiles + plan limit check `count >= limit 403` → upgrade CTA
- Import GitHub: paste url `https://github.com/owner/repo(.git)?` + validation regex + branch default main subdir → clones via `QuestsFileService.github_clone` → file tree populates
- Sync now button → packing tar.gz exclude list displayed size progress → uploading → extracting secure skip symlinks/dev absolute/.. ensure startswith → committing diff stats added modified deleted unified diff preview timer 10s debounce

409 recovery flow (automatic):

```
User triggers run_code but session belongs to previous env → Backend 409 does not match session binding
→ Toast: Env binding mismatch (session abc123 ↔ env e456). Recreating...
→ Auto: DELETE /api/runtime/sessions/abc123 → POST /api/runtime/sessions {environment_id: e456} → new sid def456
→ Auto: sync_workspace_from_tar file_root → def456 secure extract → git add -A commit sync from keystone
→ Auto: retry run_code with new sid + same code cwd → success
→ Toast: Recreated session def456 + re-synced 87 files 12MB — no data loss, file_root persists
```

Bare GC warning: when `runtime.cache.status()` sizes MB via rglob > threshold (500MB) → banner `⚠ Bare repos 241MB + growing nightly — GC cron nightly arch S3 del? [Admin] /admin/sessions stats`

---

## 4. IDE v2 Flow

- File tree click → reads file `GET /files/read?path=` + hash + functions + bracket balanced + binary detect 10MB + max 2000 lines addLineNumbers
- Select function from dropdown → `GET /files/function?path=&function_name=` → returns start end lines via brace counting string/comment aware + jumps Monaco to range
- Edit flow:

1. User types in Monaco or clicks surgical edit toolbar insert@10 content...
2. Preview diff button → `POST /files/edit/preview {path operations}` → unified_diff generated reverse order preserve numbers diff_preview returned
3. Show Myers diff 8000 cap side-by-side original vs new hash
4. Destructive guard check `original>500 && new/old<0.3 && mostly-comments → block` → warning banner refactor rather than delete?
5. Conflict check base_hash SHA256 vs current hash → if mismatch fail with Retry Fetch Latest
6. Apply → `POST /files/edit {path base_hash operations}` → writes via `FileService.write_file` edits via `_apply_pending_edits` + `notify_file_change → commit manager debounce 10s Timer → proxy POST sessions/{id}/commit_workspace` + updates git_head if commit + restarts procs if restart_on_push

- Glob `**/*.tsx` → files list filter `count` → grep `"useState"` → results with file path line col + preview count
- Download zip → `GET /files/download-all` exclude node_modules __pycache__ .git venv .venv tempfile background cleanup safe name alnum -_
- Preview → `/quests-preview/{envId}` iframe shim-client injected error-overlay recovery-overlay + health check `check_port http_health_check stream_logs capture_preview_metadata`

---

## 5. Tool Palette Flow

- Click Desktop 12 tab → shows all 12 with param schemas + explanation param + batch parallel guidance
- Click Runtime 22 tab → shows full 22 + drift warning ⚠ 8 not proxied Server A vs B (functions_mapping bracket_tracker etc) → action reconcile button → shows diff list Server B allowed vs Server A allowed
- Click Workspace tab → meter free 2/100 etc + custom tools list with method POST headers timeout retry trigger_keywords + SSRF check `is_allowed_url http/https BLOCKED_HOSTS private IP` green/red + test button → `POST /tools/{id}/test {arguments:{}}` → ToolResultEnvelope confidence duration invocation_id status + invocations limit 100 replay button
- Click Org tab → org tools + public catalog enable/disable enable_public_tool copies to org/workspace + test
- Ledger tab → recent 20/100 invocation records 10:42:01 run_code 231ms success confidence 1.0 Replay button replay vs original diff + policy mode auto max 5/turn 100/min etc allowed_tools blocked_tools blocked_domains
- Policy editor → execution policy form tool_mode auto required disabled max_tools_per_turn max_calls_per_min max_calls_per_min timeout allow_parallel require_confirmation fallback continue allowed_tools blocked_tools blocked_domains

SSRF test interactive:

```
Test URL: https://api.example.com/webhook -> is_allowed_url? scheme http/https hostname not in BLOCKED_HOSTS localhost 127.0.0.1 0.0.0.0 169.254.169.254 metadata.google.internal instance-data resolved IP not private/loopback/link_local/reserved/multicast via ipaddress + getaddrinfo -> ✓ safe
Method: POST timeout 10s retry 1
[Send test] -> ToolResultEnvelope 200 123ms data {ok:true}
```

---

## 6. Runtime Station Flow

- Sessions list from `GET /admin/sessions` + stats active/total disk via file sizes stale >30m + metrics snapshot avg wait/exec sliding 1000→500 total_completed/errors
- Processes per session: vite dev :5173 PID 1234 logs output/<sid>/<name>.log stream live health check ✓ port ✓ + stop button
- Run code editor: Monaco small + env_id MUST + cwd selector file tree + [Run] button with 409 auto retry + output 200k meter policy max_output_bytes
- Queue metrics: depth 0/50 per-user 0/3 + queueMiddleware QUEUED_PATHS bug call_next immediately vs lambda indicator
- Cache: npm-cache 123MB 45 files pip-cache 89MB lock .cache.lock status via rglob + prewarm python 7/10 node 5/8 + config prewarm.json downloads without installing
- Git bare: list git/<sid>/repo.git size 241MB warning leak + HEAD branch main post-receive auto-checkout true restart_on_push true hooks size 50MB file 200MB push via rev-list + cat-file -s
- Cleanup timeline visualization: session_meta TTL 3600 → grace → grace expired → cleanup_disk + remove active set
- Security: IP allowlist + HMAC METHOD:PATH:BODY+TIMESTAMP+NONCE+CONTEXT JSON{user_id,org_id} ±1 window 120s TTL 10k nonce LRU + filesystem resolve_workspace_path + resolve_runtime_path + tar secure + exec setrlimit + quota + proc limit + git hooks size
- Admin: tool_ledger 5000 in-memory LEDGER array session_logs 1000 TTL7200 user_logs 999 etc manifest TTL7200 etc activity_stream 500 TTL2*ttl user_activity 1000 env_last_session TTL7d session_env TTL7d

---

## 7. Chat 3 Modes + WebSocket

- Tabs Keystone IDE (sentinel <<FILE>>/<<EDIT>>) / Focus docs-only README first / Gex debug fixes AiAS API
- Input: temperature maxTokens persona read-only toggle voiceToText append transcript voice session TTS playingMessageId audioRef webTool none/search/visit voiceActionScope
- Send → POST /chat/stream SSE tool_round KEYSTONE_IDE_TOOLS 5 auto-recovery rate-limit/context overflow/max_tokens + non-stream fallback
- Streaming: meta chunk content tokens current/max tool_start exec done done error token len/4 reasoning strip <tool><output><think> + approxTokens len/3.5 incremental marker detection Apply All + sequential tool calls then second completion call with tool results
- Artifact extraction: <<<FILE path>>>...<<<END>>> regex fallback ``` fence stage timer Initializing Analyzing Designing Writing Finalizing 3s labels stack heuristic
- Save artifact POST /artifacts id + populateSessionMetadata temp session JSON directives knowledge
- Import artifact to env via write file ext map + Deploy to Keystone POST /keystone/environments + write → redirect + Git clone offer detection github URL card + trace markdown injection
- Presence: WebSocket /client join_workspace workspace_id validation enter_room ws:{id} + typing 15s TTL typing_start/stop/preview + presence ● 2 online + shadow draft inbox latest draft emit draft_created awaiting_approval + admin /admin subscribe_dashboard subscribe_workspace send_as_ai change_mode ai|shadow|takeover inject_directive

2027: replace 3s poll in Workspaces.tsx 2800 lines + OraclePlayground 3000+ lines with WS real-time

---

## 8. Artifact Forge

- Standalone portal from `artifacts.py + ArtifactPortal.tsx 77KB` 21 example prompts Web Scraper Support Agent Research Agent etc + createSession persona agentic architecture event loop LLM core via https://api.aiassist.net/v1/chat/completions + headers Authorization Bearer {AIAS_API_KEY} X-Agent-Id X-AiAssist-Provider={AIAS_PROVIDER default groq} memory via POST/GET /api/workspaces/{WORKSPACE_ID}/messages|memory/facts SQLite fallback zero-setup requests only env vars + handleGenerate streams POST /{sid}/chat/stream X-AiAssist-Provider SSE data: type chunk content + code extraction via <<<FILE agent.py>>> fallback fence live streamingCode stage timer + detectStack heuristic + saveArtifact POST /api/artifacts + populateSessionMetadata + handleChat + Routes /dashboard/artifact-portal badge Cpu gradient cyan→blue mobile MobileDashboard catalog id artifacts href /app/v1/artifact-portal group build
- 2027 inline in IDE: right panel [Forge] tab shows streaming code + stages + stack badge + save + import to env + deploy to Keystone

---

See app/index.html for live interactive version
