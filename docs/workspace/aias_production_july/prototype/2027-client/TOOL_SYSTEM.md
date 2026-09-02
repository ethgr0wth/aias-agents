# Tool System — 2027 Client (Tool-Complete)

> Desktop 12 tools = hosted baseline, not premium. 22 runtime tools + catalog marketplace = additive. Unified palette, permissioned per plan.

---

## 1. The Drift We Fix

march_2026:

- Quests desktop (Electron) `packages/workspace/src/tools/all.ts` `TOOLS_BY_NAME ALL_AI_SDK_TOOLS getToolByType` 12 tools: `ReadFile WriteFile EditFile Glob Grep FileTree RunShellCommand RunDiagnostics RunGitCommands Choose Think Unavailable` — base.ts `BaseInputSchema explanation param`
  - `read-file.ts 414LOC image/pdf/audio/video 10MB base64 addLineNumbers binary detect max 2000 lines`
  - `edit-file.ts 707LOC SimpleReplacer LineTrimmedReplacer BlockAnchorReplacer Levenshtein similarity thresholds`
  - `run-shell-command.ts 718LOC`
  - etc 12 total
  - `app-builder.ts 338LOC picks [EditFile,Glob,Grep,ReadFile,RunDiagnostics,RunShellCommand,Think,WriteFile] system prompt fileTree AGENTS.md package.json deps security refusal tone proactive + ShouldContinue checks pending tool parts`
  - `chat.ts picks [ReadFile,Glob,Grep] read-only conversational`

- Keystone hosted (SaaS) `api/routes/quests.py KEYSTONE_IDE_TOOLS 5 OpenAI function tools` → `_execute_ide_tool auto-recovery rate-limit/context overflow/max_tokens` IDE Tools: `clone_repo read_file search_files glob_files list_functions` — only 5! Gap 7 tools missing vs desktop (EditFile WriteFile RunShellCommand RunDiagnostics Choose etc) — next gen must bridge

- Runtime Server B `ALLOWED_TOOLS 22`: `clone_repo checkout_ref detect_stack install_node_deps install_python_deps write_env_file start_process stop_process check_port http_health_check stream_logs capture_preview_metadata export_artifacts run_code install_package read_file write_file list_directory search_in_files functions_mapping bracket_tracker export_artifact session_reset`

- But Server A proxy `DEPLOYMENT_TOOLS+SAFE_CODE_TOOLS=ALLOWED_TOOLS 14` only! Drift 22 vs 14 — `functions_mapping bracket_tracker export_artifact` etc not proxied — 2027 client must reconcile

- Custom tools `api/routes/custom_tools.py 19781B + org_router` + `tool_executor.py 61KB`:
  - `TOOL_PLAN_LIMITS free 2/100 basic 5/1000 pro 20/10000 enterprise -1/-1`
  - `ToolType webhook|builtin ToolMode auto|required|disabled ToolScope workspace|organization|public WebhookMethod GET|POST|PUT|DELETE`
  - `WebhookConfig {url method=POST headers? auth_secret_id? timeout_ms=10000 retry_count=1}`
  - `ToolParameters object+properties Type ToolParameterProperty {type=string desc enum?}`
  - `ToolResponseSchema {type=object properties? required? max_size_bytes=102400}`
  - `CustomToolCreate {name desc type=webhook webhook? builtin_action? parameters={} response_schema? scope=workspace enabled=true allowed_roles? plan_required? trigger_keywords?}`
  - `ToolResultEnvelope {tool tool_id status success|error|validation_error data? error? confidence duration_ms invocation_id}`
  - `ExecutionPolicy {tool_mode=auto max_tools_per_turn=5 max_calls_per_minute=100 timeout_ms=30000 allow_parallel=false require_confirmation=false fallback=continue allowed_tools? blocked_tools? blocked_domains?}`
  - `VALID_BUILTIN_ACTIONS 23`: `create_note escalate→SHADOW schedule_callback Redis tool_callback:{wid}:{8char} SETEX TTL delay_minutes*60 calculate json_transform timestamp_util validate_data regex_test create_task create_ticket status_check log_expense read_url summarize sentiment_analysis translate extract_keywords draft_email meeting_prep draft_proposal generate_invoice knowledge_search faq_lookup send_email signal_scan — execute_code sunsetted`
  - `SSRF BLOCKED_HOSTS localhost 127.0.0.1 0.0.0.0 169.254.169.254 metadata.google.internal is_allowed_url scheme http/https IP private/loopback/link_local/reserved/multicast via ipaddress+getaddrinfo Limits MAX_RESPONSE_SIZE 102400 MAX_TIMEOUT_S 30 MAX_TOOL_CALLS_PER_MESSAGE 10`
  - `_llm_complete via test_api_key providers groq|openai|anthropic|gemini|mistral|xai|together|openrouter|deepseek|fireworks|perplexity or production orchestrator.get_client_for_user`
  - `execute_tool builds envelope validates schema validate_response_schema logs via storage.log_tool_invocation + increment_tool_invocation_count Webhook retry capped 3 backoff 0.5*(attempt+1)s extracts Bearer from storage.get_tool_secret`
  - Storage redis_storage 9809-10300 `create_custom_tool list_custom_tools list_org_tools create_org_tool update_custom_tool delete_custom_tool log_tool_invocation get_execution_policy seed_public_tools enable_public_tool etc`
  - Frontend `ToolsHub.tsx 94KB + WorkspaceTools.tsx 49KB` — dusty but functional

- Artifacts `artifacts.py 2276B ArtifactCreate {name prompt source_code target_stack="" desc="" provider="" model="" session_id="" chat_messages=[] status=ready} POST id GET limit offset PATCH DELETE Storage 9741-9800 save/get/list/update/delete Frontend ArtifactPortal 77KB 21 EXAMPLE_PROMPTS Web Scraper Support Agent etc Flow createSession persona agentic architecture event loop LLM core via https://api.aiassist.net/v1/chat/completions + headers Authorization Bearer {AIAS_API_KEY} X-Agent-Id X-AiAssist-Provider={AIAS_PROVIDER default groq} memory via POST/GET /api/workspaces/{WORKSPACE_ID}/messages|memory/facts SQLite fallback zero-setup requests only env vars AIAS_API_KEY WORKSPACE_ID AGENT_ID AIAS_PROVIDER handleGenerate streams POST /{sid}/chat/stream with X-AiAssist-Provider parses SSE data: {type chunk content} extracts code via <<<FILE agent.py>>>...<<<END>>> regex fallback ``` fence live streamingCode stage timer 3s labels Initializing Analyzing Designing Writing Finalizing detectStack heuristic Requests/BeautifulSoup FastAPI LangChain OpenAI SDK Stdlib TS JS Rust saveArtifact POST populateSessionMetadata temp session JSON {directives[] knowledge_items[]} → POST /{sid}/directives|knowledge handleChat etc Routes client/src/App.tsx /dashboard/artifact-portal FeatureHost mapping badge icon Cpu gradient cyan→blue mobile MobileDashboard catalog id artifacts href /app/v1/artifact-portal group build`

2027: Unified Tool Palette

---

## 2. Unified Palette

```ts
type ToolSource = "desktop-quests" | "runtime-server-b" | "custom-workspace" | "custom-org" | "custom-public" | "builtin-action"

interface UnifiedTool {
  id: string
  name: string // EditFile | run_code | create_note etc
  source: ToolSource
  description: string
  parameters: ToolParameters // object+properties property {type desc enum?}
  response_schema?: ToolResponseSchema // type object properties required max_size_bytes 102400
  scope: "workspace" | "organization" | "public" | "global"
  enabled: boolean
  plan_required?: "free" | "basic" | "pro" | "enterprise"
  trigger_keywords?: string[] // keyword match pre-execution for non-native providers [LIVE TOOL DATA] injection
  allowed_roles?: string[]
  native: boolean // true for openai|anthropic|mistral native tools_list, false for fallback pre-executor keyword match
  builtin_action?: string // for custom builtin type: VALID_BUILTIN_ACTIONS 23
  webhook?: WebhookConfig
  usage: { limit: number, used: number, meter: number } // per TOOL_PLAN_LIMITS
  invocation_count: number
  last_invoked_at?: string
  created_at: string
}

interface ToolInvocationRecord {
  id: string
  tool_id: string
  tool_name: string
  workspace_id: string
  user_id?: string
  arguments: any
  status: "success" | "error" | "validation_error"
  response_status?: number
  result?: any
  error?: string
  duration_ms: number
  confidence: number // 1.0 default
  is_replay: boolean
  timestamp: string
}

interface ToolLedger {
  invocations: ToolInvocationRecord[]
  total: number
  limit: number // 100
  plan_limit: { max_tools: number, max_invocations_monthly: number } // TOOL_PLAN_LIMITS
  execution_policy: ExecutionPolicy
}

// Full inventories:

// Desktop 12:
const DESKTOP_TOOLS = [
  "ReadFile", "WriteFile", "EditFile", "Glob", "Grep", "FileTree", "RunShellCommand", "RunDiagnostics", "RunGitCommands", "Choose", "Think", "Unavailable"
]

// Hosted current 5 (to be expanded to 12+):
const KEYSTONE_IDE_TOOLS_CURRENT = ["clone_repo", "read_file", "search_files", "glob_files", "list_functions"]

// Runtime Server B 22 (full):
const RUNTIME_TOOLS_FULL = [
  "clone_repo", "checkout_ref", "detect_stack", "install_node_deps", "install_python_deps", "write_env_file",
  "start_process", "stop_process", "check_port", "http_health_check", "stream_logs", "capture_preview_metadata",
  "export_artifacts", "run_code", "install_package", "read_file", "write_file", "list_directory",
  "search_in_files", "functions_mapping", "bracket_tracker", "export_artifact", "session_reset"
]

// Server A proxy 14 (drift to fix):
const SERVER_A_ALLOWED = ["clone_repo", "checkout_ref", "detect_stack", "install_node_deps", "install_python_deps",
  "write_env_file", "start_process", "stop_process", "check_port", "http_health_check", "stream_logs",
  "capture_preview_metadata", "export_artifacts", "export_artifact"] // missing run_code etc — actually DEPLOYMENT_TOOLS + SAFE_CODE_TOOLS = 14? check runtime.py

// Custom builtin 23:
const VALID_BUILTIN_ACTIONS = [
  "create_note", "escalate", "schedule_callback", "read_url", "knowledge_search", "calculate",
  "json_transform", "timestamp_util", "summarize", "sentiment_analysis", "translate", "extract_keywords",
  "draft_email", "create_task", "meeting_prep", "create_ticket", "faq_lookup", "regex_test", "draft_proposal",
  "status_check", "generate_invoice", "log_expense", "validate_data", "send_email", "signal_scan"
]

// ExecutionPolicy defaults:
const DEFAULT_POLICY: ExecutionPolicy = {
  tool_mode: "auto", max_tools_per_turn: 5, max_calls_per_minute: 100, timeout_ms: 30000,
  allow_parallel: false, require_confirmation: false, fallback: "continue"
}
```

---

## 3. Drawer UI

```
┌─ Tool Palette (unified) ─────────────────────────────────────┐
│ [Desktop 12] [Runtime 22] [Workspace] [Org] [Catalog] [Ledger]│
├───────────────────────────────────────────────────────────────┤
│ Search: [EditFile █]  Filter: all enabled required auto      │
│ Desktop (parity target hosted baseline)                      │
│  ✓ EditFile [surgical insert/replace/delete Levenshtein]   │
│    params: {explanation, path, operations[{action,start,end,content}] base_hash?}
│    response: {success operations_applied new_hash new_size conflict diff_preview}
│  ✓ ReadFile [414LOC image/pdf/audio/video 10MB base64 addLineNumbers binary 2000 lines]
│  ✓ WriteFile ...                                            │
│  ✓ Glob pattern **/*                                         │
│  ✓ Grep pattern regex file_pattern count                      │
│  ✓ FileTree depth 10 ignore .gitignore filter                │
│  ✓ RunShellCommand [718LOC] ...                              │
│  ✓ RunDiagnostics ...                                        │
│  ✓ RunGitCommands git init/status/add/commit/log ...         │
│  ✓ Choose interactive ...                                    │
│  ✓ Think explanation param tool usage guidance batch parallel │
│ Runtime Server B 22 (gap: 8 not in Server A proxy drift fix) │
│  ✓ clone_repo session_id repo_url target_dir                │
│  ✓ checkout_ref session_id repo_dir ref                      │
│  ⚠ functions_mapping [NOT PROXIED — drift!] server A missing│
│    → action: reconcile ALLOWED_TOOLS server A = server B 22  │
│  ⚠ bracket_tracker [NOT PROXIED] etc                         │
│  ✓ run_code session_id env_id code cwd policy output 200k   │
│    env binding mandatory PR#34 409 destroy-recreate-retry    │
│ Workspace (2/10) free limit [██▒▒]                           │
│  ● My Webhook POST https://api.example.com/hook              │
│    method POST headers {} auth_secret_id timeout 10s retry1 │
│    trigger_keywords: ["invoice", "create note"]              │
│    SSRF check: is_allowed_url http/https BLOCKED_HOSTS + private IP via ipaddress + getaddrinfo ✓ safe
│    size cap 100KB timeout 30s tool calls per msg 10          │
│    test [Test] replay [Replay] invocations 12/100            │
│ Org (1/-1) enterprise unlimited                              │
│ Catalog public marketplace 10 tools seeding:                  │
│  ○ Stripe tool [enable] ○ Notion tool [enable] etc           │
│  [enable_public_tool] copies to org/workspace                │
│ Ledger (recent 20/100)                                       │
│  10:42:01 run_code ████ 231ms success confidence 1.0 [Replay] │
│  10:41:55 create_note 89ms success data {note...} [Replay]   │
│  10:41:12 webhook POST 403 error SSRF blocked private IP ↓   │
│  [Export ledger 5000 in-memory LEDGER array for debug]       │
│ Policy: mode auto max 5/turn 100/min timeout 30s             │
│         allow_parallel false require_confirmation false fallback continue
│         allowed_tools? blocked_tools? blocked_domains?       │
└───────────────────────────────────────────────────────────────┘
```

- Gap indicators: ⚠ drift tools (functions_mapping, bracket_tracker, export_artifact, run_code etc) not in Server A proxy — show fix action reconcile
- SSRF test UI: method allowlist GET POST PUT DELETE, timeout min 15s, 50KB cap validation, `is_allowed_url` check result displayed
- Webhook retry capped 3 backoff 0.5*(attempt+1)s + Bearer extraction from `get_tool_secret`
- Tool test: `POST /{workspace_id}/tools/{tool_id}/test {arguments:{}}` → `ToolResultEnvelope` display with confidence duration invocation_id
- Replay: `POST /{workspace_id}/tools/{tool_id}/replay/{invocation_id}` with original vs replay diff
- Invocations limit 100 per tool via `list_tool_invocations tool_id limit min(limit,100)`
- Plan gate: `TOOL_PLAN_LIMITS free 2/100 basic 5/1000 pro 20/10000 enterprise -1/-1` → meter bar + upgrade CTA
- Builtin actions 23 visualized with LLM provider routing via `test_api_key providers groq/openai/...` or `orchestrator.get_client_for_user`
- Artifact extraction `<<<FILE agent.py>>>...<<<END>>> regex fallback ``` fence stage timer labels Initializing Analyzing Designing Writing Finalizing stack heuristic Requests/BeautifulSoup FastAPI LangChain OpenAI STDlib TS JS Rust saves via `POST /api/artifacts` + `populateSessionMetadata temp session JSON {directives[] knowledge_items[]} → POST`

---

## 4. Implementation

- `src/lib/tool-palette.ts` — fetch desktop tools static list + runtime `GET /api/runtime/health tools` + custom `GET /api/workspaces/{id}/tools + limit + invocations_monthly_limit` + org `GET /api/org/tools` + catalog `GET /api/org/tools/public/catalog with enabled_for_org` — unify into UnifiedTool[]
- `src/lib/api-client.ts` — credential passport injects X-Provider ALWAYS
- Tests: SSRF block list includes localhost 127.0.0.1 0.0.0.0 169.254.169.254 metadata.google.internal instance-data etc private/loopback/link_local/reserved/multicast via ipaddress lib in tool_executor.py — mirror same check client-side for pre-validation
- Webhook: validate method allowlist timeout 15s min 50KB cap, show real-time `is_allowed_url` result

See ARCHITECTURE.md §2.6 + app/index.html tool palette drawer.
