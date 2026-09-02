---
title: Custom Tooling System (v2) — Full Stack
---
# Custom Tooling System (v2)

## What & Why
Build the custom tooling engine that lets users define tools (webhook endpoints, built-in actions) their AI agents can call mid-conversation. This is the core differentiator — turning chat-only AI into AI that *does things*. Incorporates Oracle's five enhancement pillars: Tool Identity at Runtime, Deterministic Mode, Execution Policy Layer, Tool Result Validation, and Tool Replay.

Key architectural decision: **Dynamic tool resolution per-turn** (not session-start). Tools are resolved fresh each orchestrator turn, so adding/removing/updating tools mid-conversation takes effect immediately.

## Done looks like
- Users can create, edit, enable/disable, and delete custom tools via workspace settings UI
- Tools support two types: webhook (external HTTP endpoint) and built-in (internal actions)
- AI agents automatically discover and use enabled tools during conversations
- Every tool invocation returns structured identity metadata (tool name, status, confidence, duration) that the AI can reason about
- Workspace owners can set tool execution mode: `auto` (AI decides), `required` (AI must use tools), `disabled` (pure chat)
- Per-workspace execution policies enforce guardrails: max calls per turn, allowed/blocked tool lists, require-approval flag
- Webhook responses are validated against user-defined JSON schemas with size limits and type enforcement
- Every tool invocation is logged with full context and can be replayed from the invocation log
- Plan tier enforcement: Free=2 tools/100 inv/mo, Basic=5/1K, Pro=20/10K, Enterprise=unlimited
- Works across all 12 LLM providers (OpenAI, Anthropic, Groq, Gemini, Mistral, xAI, Together, OpenRouter, DeepSeek, Fireworks, Perplexity, PIN)

## Out of scope
- Tool marketplace / sharing between users (future)
- Tool versioning (in-place updates for now)
- Tool chaining (one tool calling another)
- Mobile dashboard widget for tools (separate task)
- Built-in actions beyond the initial four (send_email, create_note, escalate, schedule_callback)

## Tasks

### Phase 1: Data Layer & CRUD API
1. **Pydantic models & Redis storage** — Define `CustomTool`, `ToolInvocation`, `ExecutionPolicy`, `ToolResultEnvelope` models. Build Redis storage methods for tool CRUD, invocation logging, and execution policy storage. Keys: `tools:{workspace_id}:{tool_id}`, `tools:workspace:{workspace_id}` (SET), `tools:org:{org_id}` (SET), `tool_secrets:{tool_id}:{name}`, `tool_invocations:{tool_id}` (LIST capped at 100), `tool_policy:{workspace_id}`.

2. **CRUD API routes** — Workspace-scoped endpoints: list, create, get, update, delete, test (dry-run), invocations. Org-scoped endpoints for managers. Include plan-tier enforcement on tool count. Mount at `/api/workspaces/{id}/tools`.

3. **Secret storage for webhook auth** — Fernet-encrypted secret storage for webhook auth tokens. Secrets never returned in API responses. Decrypt only at execution time.

### Phase 2: Execution Engine
4. **Webhook executor with SSRF protection** — `execute_webhook_tool()` with URL allowlist/blocklist (no localhost, private IPs, cloud metadata), httpx async client, timeout enforcement (max 30s), retry logic.

5. **Tool Result Envelope & Validation** — Every tool result wrapped in `{ tool, tool_id, status, data, confidence, duration_ms, invocation_id }`. Webhook responses validated against optional user-defined JSON schema. Size limit (100KB default). Type enforcement. Malformed responses return structured error rather than raw data to the LLM.

6. **Deterministic mode** — Add `tool_mode` field to workspace settings (`auto | required | disabled`). `required` forces `tool_choice: "required"` in provider calls. `disabled` strips tools from context entirely. `auto` is the current behavior. Map to each provider's native format.

7. **Execution policy enforcement** — Per-workspace `ExecutionPolicy`: `max_calls_per_turn`, `allowed_tools[]`, `blocked_tools[]`, `require_approval`. Policy checked before each tool invocation. Approval mode queues the tool call and waits for WebSocket confirmation from a manager. Rate limits: max 10 calls/message, 100/min/workspace.

### Phase 3: Orchestrator Integration
8. **Dynamic per-turn tool resolution** — In `_build_tools_list()`, fetch workspace + org tools from Redis each turn. Filter by enabled, role, plan, and execution policy (allowed/blocked). Merge with existing built-in tools (escalation, web search). No caching at session level — tools are always fresh.

9. **Provider-specific tool format translation** — Extend the existing provider branching in `_build_tools_list()` to convert custom tool definitions to OpenAI `tools[]`, Anthropic `tools[]`, and Gemini `function_declarations` formats. PIN network tools passed as standard OpenAI format.

10. **Tool call detection and execution loop** — Extend the existing tool_call handling (currently escalation + web search) to dispatch custom tool calls. Execute webhook or built-in action, wrap result in Tool Result Envelope, feed back to LLM as tool response. Support multi-turn tool calling (LLM calls tool → gets result → may call another tool → until done).

### Phase 4: Invocation Log & Replay
11. **Invocation logging** — Log every invocation to Redis LIST with full context: tool_id, workspace_id, user_id, arguments, response envelope, duration_ms, timestamp. Capped at 100 per tool. Add API endpoint to query invocation history with filtering.

12. **Tool replay engine** — API endpoint to replay a logged invocation: re-execute the same tool with the same arguments, return both original and replayed results side-by-side. Enables debugging and session simulation. Replay calls are flagged as `replay: true` in logs.

### Phase 5: UI
13. **Tools list page** — Workspace settings tab showing all tools with enable/disable toggle, invocation count, last-used timestamp. Add/edit tool modal with name, description, type picker, webhook config, parameter builder, scope selector, role/plan restrictions.

14. **Test panel** — Dry-run interface in the tool editor: enter sample arguments, execute tool, see response + validation results. No LLM involved — direct tool execution.

15. **Execution policy settings** — UI for workspace owners to configure tool mode (auto/required/disabled), max calls, allowed/blocked tools, and approval requirement.

16. **Invocation log viewer** — Table view of recent invocations per tool with arguments, status, duration, and a replay button.

### Phase 6: Built-in Actions
17. **Initial built-in tools** — Implement four built-in actions that don't require webhooks: `send_email` (via SMTP config), `create_note` (save to workspace), `escalate` (trigger shadow/takeover mode), `schedule_callback` (set timed reminder via Redis).

## Relevant files
- `aias_production_clone/docs/custom-tooling-plan.md`
- `aias_production_clone/api/services/ai_orchestrator.py:182-207`
- `aias_production_clone/api/services/ai_orchestrator.py:540-815`
- `aias_production_clone/api/services/ai_orchestrator.py:1112-1190`
- `aias_production_clone/api/models/schemas.py`
- `aias_production_clone/api/routes/users.py`
- `aias_production_clone/api/services/web_search.py`
- `aias_production_clone/api/services/web_extraction.py`
- `aias_production_clone/api/config.py`