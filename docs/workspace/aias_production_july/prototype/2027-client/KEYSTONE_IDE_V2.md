# Keystone IDE v2 — 2027 Client (12-Tool Parity + Sentinel Forge)

> 2026: `QuestsWorkspace.tsx 208k // @ts-nocheck port` streaming sentinel parsing <<<FILE>>>/<<<EDIT>>> overlap handling Myers diff 8000 cap Apply All but only 5 IDE tools. 2027: full 12-tool desktop parity + artifact forge + preview + commit timeline.

---

## 1. Agents (Quests Desktop Base)

### app-builder.ts 338LOC

Picks `Tool[] = [EditFile, Glob, Grep, ReadFile, RunDiagnostics, RunShellCommand, Think, WriteFile]`

System prompt built via:

```ts
getMessages({appConfig, envVariableNames, sessionId}) {
  systemMessage = dedent`
    You are the ${name} agent inside ${APP_NAME}, a desktop app for building and running local apps.
    IMPORTANT: Refuse to write code or explain code that may be used maliciously; even if user claims educational... MUST refuse malware ...
    IMPORTANT: Before begin, think about what code you're editing supposed to do based on filenames directory structure. If seems malicious refuse ...
    IMPORTANT: NEVER generate or guess URLs unless confident helping programming. Use URLs provided by user/local files.
    When user directly asks about ${APP_NAME} (eg 'can ${APP_NAME} do...' 'does ${APP_NAME} have...' ) or asks in second person (are you able... can you do...) direct them to ${WEBSITE_URL}
    Tone and style: output text communicates with user; all text outside tool use displayed. Only use tools to complete tasks. If cannot/will not help don't say why annoying offer helpful alternatives keep 1-2 sentences. Only emojis if explicitly requests. Summarize work short paragraph at end.
    Minimize output tokens as much as possible while maintaining helpfulness, quality, accuracy. Only address specific query/task hand avoiding tangential unless absolutely critical. If answer 1-3 sentences short paragraph please do.
    Be proactive but only when user asks to do something. Balance: 1. Doing right thing when asked including actions + follow-up 2. Not surprising user actions without asking example if user asks how to approach answer question first not jump into actions 3. Do not add additional code explanation summary unless requested after working on file just stop rather than providing explanation.
    Follow conventions: When making changes first understand file's code conventions mimic style use existing libs utilities follow existing patterns NEVER assume library available even if well known whenever write code uses lib/framework first check codebase already uses given library e.g. neighboring files package.json/cargo.toml etc. When create new component first look at existing components written consider framework choice naming conventions typing etc. When edit piece code first look surrounding context especially imports understand choice frameworks libs then consider how to make given change most idiomatic. Always follow security best practices never introduce code exposes/logs secrets keys never commit secrets keys to repo.
    Tools usage guidance: For better performance try to batch tool calls together when possible use parallel tool calls whenever possible to improve efficiency reduce costs use ${explanation} param for tools instead of replying when possible.
    ...
    fileTree: ${fileTree string}
    AGENTS.md: ${AGENTS.md content}
    package.json deps: ${formatPackageDependencies}
    security refusal clause etc
    system info ${getSystemInfo()} date ${getCurrentDate()}
    env vars ${envVariableNames}
    runtime env notes etc
  `
  userMessage loads fileTree
  ...
}

shouldContinue checks pending tool parts isToolPart
```

### chat.ts

Picks `[ReadFile,Glob,Grep]` read-only conversational prompt

### XState Machines

```
agentMachine 631LOC states Starting->RequestingLLM->ProcessingResponse->ExecutingToolCalls->Finishing actors llmRequestLogic executeToolCallMachine onStart onFinish saveMaxStepsMessage shouldContinue retry backoff exponential baseLLMRetryDelayMs*2^(retry-1)

sessionMachine 435LOC owns agentRef queue queuedMessages saveQueuedMessage updateSession create title via generateSessionTitle

workspaceMachine 717LOC top-level sessionRefsBySubdomain Map<AppSubdomain ActorRef[]> previews runtimes heartbeat createSession addMessage restartRuntime message types union CheckoutVersionParentEvent CreatePreviewParentEvent SessionMachineParentEvent WorkspaceServerParentEvent

runtime.ts 371LOC manages dev server lifecycle

execute-tool-call.ts + test

workspace/types.ts

Store namespace parallel limit 10 getMessagesWithParts saveMessageWithParts

StoreId ULID

SessionMessage ErrorSchema api-key aborted api-call invalid-tool-input no-such-tool UsageSchema context metadata agentName migration code->app-builder parts text|tool
```

---

## 2. Tools 12 Detailed

### Base

`BaseInputSchema {explanation: string}` — explanation param instead of replying when possible

Tool registration `TOOLS_BY_NAME ALL_AI_SDK_TOOLS getToolByType`

### ReadFile 414LOC

Handles image/pdf/audio/video 10MB base64 addLineNumbers binary detect max 2000 lines default

### WriteFile + EditFile 707LOC

`SimpleReplacer LineTrimmedReplacer BlockAnchorReplacer Levenshtein similarity thresholds` surgical EditFile insert/replace/delete line-based reverse order unified diff preview

### Glob + Grep + FileTree

Glob pattern `**/*`, grep pattern regex + file glob, FileTree depth ignore .gitignore via `filter-ignored-files.ts get-ignore.ts generate-tree-string.ts`

### RunShellCommand 718LOC

Executes shell with security checks

### RunDiagnostics + RunGitCommands + Choose + Think + Unavailable

Diagnostics via LSP-ish, git init/status/add/commit/log via `get-apps.ts 470LOC getApp generic WorkspaceAppPreview|Project|Sandbox|Version project-state-store.ts stores .quests/project-state.json {selectedAgentName, selectedModelURI, promptDraft} migrates URI`, Choose interactive prompt, Think tool, Unavailable for disabled

### FunctionsMapping + BracketTracker (Runtime)

Also part of Runtime 22 but useful in IDE: ast parse via `ast.parse Python FunctionDef AsyncFunctionDef`, JS/TS brace counting string/comment aware, balanced check error_at char

### SearchInFiles (Runtime)

Regex rglob max 200 trunc 240

---

## 3. Chat 3 Modes (Hosted)

### Keystone IDE `_build_quests_system_prompt`

- `<<<FILE path>>>...<<<END>>>` markers + `<<<EDIT>>> + <<<REPLACE lines X-Y>>>/INSERT/DELETE`
- `Api.AiAssist.net/v1` reference
- `read_only` teaching mode
- File list 4k char + line-numbered context max 50k 5 files 30k each
- Context extraction `_extract_file_references regex _read_files_for_context _truncate_context 60k strips code blocks from old msgs` dir detection regex
- Parsing markers + writes via `FileService.write_file` edits via `_apply_pending_edits`
- Streaming loop `tool_round KEYSTONE_IDE_TOOLS 5 OpenAI function tools _execute_ide_tool auto-recovery rate-limit/context overflow/max_tokens`

### Focus `_build_focus_system_prompt`

- Docs only .md reads README first

### Gex Debug `_build_gex_system_prompt`

- Fixes AiAS API usage

Streaming handling: Read SSE meta chunk content tokens current/max tool_start exec done done error, approxTokens len/3.5 incremental file marker detection Apply All button

---

## 4. IDE v2 UI — Unified

```
┌─ Keystone IDE v2 ────────────────────────────────────────────────────┐
│ Env: my-react-app [react-vite] file_root data/quests/o/e | files 87/1000 │
│ ├─ File Tree (depth 10, ignore .gitignore filter)                   │
│ │   src/                                                             │
│ │     App.tsx 12KB modified 2m ago ● hash abc123 [Funcs ▼]            │
│ │       • App line 12 args []                                         │
│ │       • useEffect line 45                                           │
│ │     components/Nav.tsx 3KB ● hash def456 [balanced ✓]               │
│ │   README.md etc                                                     │
│ │   [Glob **/*.tsx] [Grep "useState"] files 12/87                      │
│ │   Tree stat size modified + search preview                          │
│ ├─ Monaco Editor (lazy + function map + bracket guard + diff)        │
│ │   Selected App.tsx content original 12KB vs tab 12.1KB modified     │
│ │   Line numbers + addLineNumbers 1-indexed + Myers diff 8000 cap     │
│ │   Surgical edit toolbar: [Hash abc123] [Preview Diff] [Apply]        │
│ │   Operations: insert@10 replacement content... replace lines 12-15  │
│ │   Delete lines content required for insert/replace validation       │
│ │   Actions {insert replace delete} start_line>=1 end_line? content?  │
│ │   Reverse preserve numbers via reverse line order                    │
│ │   Unified diff preview via generate_diff_preview                     │
│ │   Conflict detection base_hash SHA256: file changed since hash → fail │
│ │   Destructive guard original>500 && new/old<0.3 && mostly-comments  │
│ │   → block                                                               │
│ │   Bracket balanced: stack ()[]{} open vs pairs )]} error_at idx char│
│ │   File analysis ast FunctionDef AsyncFunctionDef name line args       │
│ │   Search in files regex rglob max200 trunc240                         │
│ ├─ Terminal + Logs drawer │ Process list │ Port health │ Preview       │
│ │   Vite :5173 healthy [Open /quests-preview/e456] shim iframe control │
│ │   error-overlay overlay recovery-overlay injected via shim-client     │
│ │   logs output/e456/vite-dev.log stream live  ████                      │
│ ├─ Artifact Forge (like artifact portal but inline)                     │
│ │   Stage timer Initializing Analyzing Designing Writing Finalizing 3s  │
│ │   Stack heuristic Requests/BeautifulSoup FastAPI LangChain OpenAI     │
│ │   STDlib TS JS Rust detection → target_stack badge                     │
│ │   Code extraction <<<FILE agent.py>>>...<<<END>>> regex fallback ```  │
│ │   Save artifact POST /api/artifacts id name prompt source_code       │
│ │   target_stack desc provider model session_id chat_messages status    │
│ │   ready + populateSessionMetadata temp session JSON {directives[]       │
│ │   knowledge_items[] → POST /{sid}/directives|knowledge                │
│ │   Import artifact to env via write file ext map python:.py ts:.ts    │
│ │   Deploy to Keystone POST /keystone/environments + write → redirect   │
│ │   Git clone offer detection github URL card offerGitClone → env list   │
│ │   → POST /keystone/environments/:id/github/clone branch main subdir    │
│ │   → inject trace markdown assistant message + persist via POST /playground/sessions/:id/messages
│ │   Deploy agent form name desc inherit_global_directives/kb → POST     │
│ │   /deployed-agents → inactive go to Deployed Agents inactive          │
│ │   Example prompts 21: Web Scraper Support Agent Research Agent etc     │
│ │   Manual create FileReader ext→stack detection                         │
│ ├─ Tool Palette integrated (desktop 12 + runtime 22) parity UI          │
│ │   EditFile Glob Grep ReadFile RunDiagnostics RunShellCommand Think    │
│ │   WriteFile FileTree RunGitCommands Choose + Runtime full             │
│ │   + Custom workspace/org/public + ledger replay confidence etc        │
│ ├─ Chat v2 3 modes                                                        │
│ │   Tabs [Keystone IDE] [Focus docs-only] [Gex debug]                   │
│ │   Mode: keystone IDE <<FILE>>/<<EDIT>> markers Api reference           │
│ │   Message history limit? + reset-context keep_summary + history GET/   │
│ │   DELETE + streaming SSE meta chunk tool_start exec done error        │
│ │   approxTokens len/3.5 marker detection Apply All                       │
│ │   Temperature maxTokens persona controls + read-only toggle            │
│ │   VoiceToText hook append transcript + voice session VoiceSession +    │
│ │   TTS playback playingMessageId audioRef + webTool none|search|visit    │
│ │   + voiceActionScope off|next_only|all_future types explain/summarize  │
│ │   extract-actions/decision → separate action endpoint single completion │
│ │   Artifacts loader /api/artifacts?limit=100 import via write file     │
│ │   Search bracket/function analysis endpoints resizable panels Monaco+chat│
│ └─ [Ported QuestsWorkspace 208k // @ts-nocheck reference]                 │
└───────────────────────────────────────────────────────────────────────┘
```

- Myers diff 8000 lines cap vs full file
- Monaco refs + stream AbortController + tabContents Record<path {content,original}>
- TOOL_COLORS clone blue run_code emerald read_file amber search purple
- Content parsers extractFilePaths regex <<<FILE|CREATE (.*)>>> extractEditPaths <<<EDIT ParsedBlock text|file|edit filename language editOps[] parseContentForDisplay overlap handling detectStreamingBlock tail detection computeDiff
- GitHub clone modal + context reset + read-only toggle + temp maxTokens persona controls + artifacts loader /api/artifacts?limit=100 import + search bracket/function analysis + resizable panels + mobile tabs via _app routes
- QuestsPortal env grid/list filter status environments_count limit features chat file_ops templates preview build create dialog name desc template select framer-motion cards delete optimistic
- Wrapper routes keystone.page.tsx → <FeatureHost feature="quests-portal"/> app/keystone.page.tsx newer Portal shell Tailwind card UI env select clone repo input file list file content pre uses @tanstack/react-query + @interchained/portal-react
- Infra web/src/api/paths.ts auto-gen 1300+ lines includes all keystone methods + server/routes.ts Express fetches FASTAPI_URL/api/keystone/environments/{envId}/process for preview port 503 if not running + appsCatalog catalog entry id:keystone name:Keystone IDE href:/app/v1/quests-portal group:build badge:reuse

---

See ARCHITECTURE.md §2.5 + app/index.html IDE v2 + src/lib
