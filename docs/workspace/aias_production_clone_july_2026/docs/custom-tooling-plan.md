# Custom Tooling - Implementation Plan

**AiAssist Secure - Extensible AI Function Calling**

Let users define custom tools/functions the AI can invoke during conversations.

---

## Executive Summary

**What:** A plugin system where users define "tools" (webhooks, actions, integrations) that the AI can call mid-conversation.

**Why:** 
- Differentiator from basic chat wrappers
- Enterprise customers need their AI to DO things, not just talk
- Natural upsell path (free: 2 tools, pro: 10, enterprise: unlimited)

**Example:** User asks "What's my order status?" → AI calls their custom "Check Order" tool → returns real data.

---

## User Experience

### Defining a Tool

```
Workspace Settings → Custom Tools → + Add Tool

┌─────────────────────────────────────────────────┐
│ Tool Configuration                              │
├─────────────────────────────────────────────────┤
│ Name: Check Order Status                        │
│ Description: Look up order by ID or email       │
│                                                 │
│ Type: ○ Webhook  ○ Built-in Action              │
│                                                 │
│ Endpoint: https://api.store.com/orders/lookup  │
│ Method: POST                                    │
│ Auth Header: X-API-Key: ••••••••••              │
│                                                 │
│ Parameters:                                     │
│ ┌─────────────┬──────────┬────────────────────┐│
│ │ Name        │ Type     │ Description        ││
│ ├─────────────┼──────────┼────────────────────┤│
│ │ order_id    │ string   │ Order ID or email  ││
│ │ include_    │ boolean  │ Include tracking   ││
│ │ tracking    │          │ info               ││
│ └─────────────┴──────────┴────────────────────┘│
│                                                 │
│ Scope: ○ This workspace  ○ All workspaces      │
│                                                 │
│ [ Test Tool ]  [ Save ]                         │
└─────────────────────────────────────────────────┘
```

### AI Using the Tool

**User:** "What's the status of order #12345?"

**AI (internal):** *Detects need for order lookup → calls Check Order Status tool*

**Tool returns:** `{"status": "shipped", "tracking": "1Z999...", "eta": "Jan 15"}`

**AI:** "Your order #12345 has shipped! Tracking number is 1Z999... and it should arrive by January 15th."

---

## Tool Definition Schema

```typescript
interface CustomTool {
  id: string;                    // uuid
  workspace_id: string;          // owning workspace
  org_id?: string;               // optional org-level scope
  
  // Identity
  name: string;                  // "Check Order Status"
  description: string;           // AI reads this to decide when to use
  
  // Execution
  type: "webhook" | "builtin";
  
  // Webhook config (if type === "webhook")
  webhook?: {
    url: string;                 // https://api.example.com/action
    method: "GET" | "POST" | "PUT" | "DELETE";
    headers?: Record<string, string>;  // Static headers
    auth_secret_id?: string;     // Reference to stored secret
    timeout_ms?: number;         // Default 10000
    retry_count?: number;        // Default 1
  };
  
  // Built-in action (if type === "builtin")
  builtin_action?: string;       // "send_email", "create_ticket", etc.
  
  // Parameters (JSON Schema format - OpenAI compatible)
  parameters: {
    type: "object";
    properties: Record<string, {
      type: string;
      description: string;
      enum?: string[];
    }>;
    required?: string[];
  };
  
  // Scope & Access
  scope: "workspace" | "organization";
  enabled: boolean;
  allowed_roles?: string[];      // ["admin", "manager"] or null for all
  plan_required?: string;        // "pro", "enterprise", or null
  
  // Metadata
  created_at: string;
  updated_at: string;
  last_invoked_at?: string;
  invocation_count: number;
}
```

---

## Enforcement Scope

Tools are resolved at session start. The orchestrator builds a "tool palette" based on:

| Check | Logic |
|-------|-------|
| Workspace | Tool belongs to this workspace OR org-level tool for this org |
| Enabled | `enabled === true` |
| Role | User role in `allowed_roles` (or `allowed_roles` is null) |
| Plan | User plan >= `plan_required` (or `plan_required` is null) |

**Resolution order:**
1. Get workspace-scoped tools for this workspace
2. Get org-scoped tools for this workspace's org
3. Filter by enabled, role, plan
4. Inject into AI context as function definitions

---

## Storage Design

### Redis Keys

```
# Tool definitions
tools:{workspace_id}:{tool_id} → JSON tool object

# Workspace tool index
tools:workspace:{workspace_id} → SET of tool_ids

# Org tool index  
tools:org:{org_id} → SET of tool_ids

# Secrets (encrypted)
tool_secrets:{tool_id}:{secret_name} → encrypted value

# Invocation log (recent)
tool_invocations:{tool_id} → LIST of recent invocations (capped at 100)
```

---

## API Routes

```
# CRUD
GET    /api/workspaces/{id}/tools          # List tools for workspace
POST   /api/workspaces/{id}/tools          # Create tool
GET    /api/workspaces/{id}/tools/{tid}    # Get tool
PUT    /api/workspaces/{id}/tools/{tid}    # Update tool
DELETE /api/workspaces/{id}/tools/{tid}    # Delete tool

# Testing
POST   /api/workspaces/{id}/tools/{tid}/test   # Dry-run with sample input

# Invocations (audit)
GET    /api/workspaces/{id}/tools/{tid}/invocations  # Recent invocations

# Org-level tools (manager+)
GET    /api/orgs/{id}/tools
POST   /api/orgs/{id}/tools
...
```

---

## Orchestrator Integration

### Current Flow

```
User message → Orchestrator → LLM → Response
```

### With Tools

```
User message 
    ↓
Orchestrator (loads scoped tools)
    ↓
LLM (with tool definitions)
    ↓
[If tool_call in response]
    → Execute tool (webhook/builtin)
    → Get result
    → Feed back to LLM
    → Continue until no more tool calls
    ↓
Final Response
```

### Provider Compatibility

All 12 supported providers work with custom tools:

| Provider | Tool Format | Notes |
|----------|-------------|-------|
| OpenAI | `tools` array | Native function calling |
| Anthropic | `tools` array | Native support |
| Groq | `tools` array | OpenAI-compatible |
| Google Gemini | `function_declarations` | Slight format difference |
| Mistral | `tools` array | OpenAI-compatible |
| xAI Grok | `tools` array | OpenAI-compatible |
| Together AI | `tools` array | OpenAI-compatible |
| OpenRouter | `tools` array | Routes to underlying model |
| DeepSeek | `tools` array | OpenAI-compatible |
| Fireworks | `tools` array | OpenAI-compatible |
| Perplexity | `tools` array | OpenAI-compatible |
| **PIN** | `tools` array | P2P network, operator LLMs |

The orchestrator translates our unified tool schema to provider-specific formats.

---

## Webhook Execution

```python
async def execute_webhook_tool(tool: CustomTool, arguments: dict) -> dict:
    """Execute a webhook tool with security guardrails."""
    
    # 1. Validate URL (SSRF protection)
    if not is_allowed_url(tool.webhook.url):
        raise ToolExecutionError("URL not allowed")
    
    # 2. Build request
    headers = tool.webhook.headers.copy()
    if tool.webhook.auth_secret_id:
        secret = await get_decrypted_secret(tool.webhook.auth_secret_id)
        headers["Authorization"] = f"Bearer {secret}"
    
    # 3. Execute with timeout
    async with httpx.AsyncClient(timeout=tool.webhook.timeout_ms / 1000) as client:
        response = await client.request(
            method=tool.webhook.method,
            url=tool.webhook.url,
            json=arguments,
            headers=headers
        )
    
    # 4. Log invocation
    await log_tool_invocation(tool.id, arguments, response.status_code)
    
    # 5. Return result
    if response.status_code >= 400:
        return {"error": f"Tool returned {response.status_code}"}
    
    return response.json()
```

---

## Built-in Actions

Start with a few built-in tools users can enable:

| Action | Description | Parameters |
|--------|-------------|------------|
| `send_email` | Send email via configured SMTP | to, subject, body |
| `create_note` | Save a note to workspace | title, content |
| `escalate` | Switch to shadow/takeover mode | reason |
| `schedule_callback` | Set reminder for follow-up | time, message |

These don't require webhooks - they execute internally.

---

## Security

### SSRF Protection

```python
BLOCKED_HOSTS = [
    "localhost", "127.0.0.1", "0.0.0.0",
    "169.254.169.254",  # AWS metadata
    "metadata.google.internal",
    # Private IP ranges
]

def is_allowed_url(url: str) -> bool:
    parsed = urlparse(url)
    if parsed.hostname in BLOCKED_HOSTS:
        return False
    # Check for private IP ranges
    try:
        ip = ipaddress.ip_address(parsed.hostname)
        if ip.is_private or ip.is_loopback:
            return False
    except ValueError:
        pass  # Not an IP, hostname is fine
    return True
```

### Secret Storage

- Secrets encrypted at rest (Fernet/AES-256)
- Never logged or returned in API responses
- Separate encryption key per org (optional)

### Rate Limiting

- Max 10 tool calls per message
- Max 100 tool invocations per minute per workspace
- Timeout cap at 30 seconds

### Audit Logging

Every invocation logged:
```json
{
  "tool_id": "...",
  "workspace_id": "...",
  "user_id": "...",
  "arguments": {...},
  "response_status": 200,
  "duration_ms": 150,
  "timestamp": "..."
}
```

---

## UI Components

### Tools List Page

```
/workspace/{id}/settings/tools

┌──────────────────────────────────────────────────────┐
│ Custom Tools                          [ + Add Tool ] │
├──────────────────────────────────────────────────────┤
│ ┌────────────────────────────────────────────────┐   │
│ │ 🔧 Check Order Status              ✅ Enabled  │   │
│ │    Webhook · POST · 47 invocations             │   │
│ │    [ Edit ] [ Test ] [ Disable ]               │   │
│ └────────────────────────────────────────────────┘   │
│ ┌────────────────────────────────────────────────┐   │
│ │ 📧 Send Email                      ✅ Enabled  │   │
│ │    Built-in · 12 invocations                   │   │
│ │    [ Edit ] [ Test ] [ Disable ]               │   │
│ └────────────────────────────────────────────────┘   │
│ ┌────────────────────────────────────────────────┐   │
│ │ 🎫 Create Zendesk Ticket           ❌ Disabled │   │
│ │    Webhook · POST · 0 invocations              │   │
│ │    [ Edit ] [ Test ] [ Enable ]                │   │
│ └────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

### Tool Editor Modal

- Name, description inputs
- Type selector (webhook/builtin)
- URL, method, headers for webhooks
- Parameters builder (add/remove params with types)
- Scope selector
- Role/plan restrictions
- Test panel with sample input/output

### Invocation Log

```
Tool: Check Order Status
Recent Invocations (last 24h)

| Time     | Input              | Status | Duration |
|----------|-------------------|--------|----------|
| 2:30 PM  | {"order_id":"123"}| 200    | 145ms    |
| 1:15 PM  | {"order_id":"456"}| 200    | 132ms    |
| 12:00 PM | {"order_id":"789"}| 404    | 98ms     |
```

---

## Pricing Tiers

| Plan | Custom Tools | Invocations/mo |
|------|--------------|----------------|
| Free | 2 | 100 |
| Basic | 5 | 1,000 |
| Pro | 20 | 10,000 |
| Enterprise | Unlimited | Unlimited |

---

## Implementation Phases

### Phase 1: Foundation
- [ ] Tool schema definition
- [ ] Redis storage layer
- [ ] Basic CRUD API routes
- [ ] Webhook execution with security

### Phase 2: Orchestrator
- [ ] Tool injection into chat context
- [ ] Provider-specific format translation
- [ ] Tool call detection and execution loop
- [ ] Result feeding back to LLM

### Phase 3: UI
- [ ] Tools list page in workspace settings
- [ ] Tool editor modal with parameter builder
- [ ] Test panel for dry-run
- [ ] Invocation log viewer

### Phase 4: Polish
- [ ] Built-in actions (email, notes, escalate)
- [ ] Org-level tool sharing
- [ ] Plan tier enforcement
- [ ] Analytics dashboard for tool usage

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Time to create first tool | < 3 minutes |
| Webhook execution p95 latency | < 500ms |
| Tool adoption rate | 30% of workspaces |
| Invocations per active workspace | 50+/week |

---

## Open Questions

1. **Should tools be versioned?** (Edit creates new version vs in-place update)
2. **Tool marketplace?** (Share/sell tools between users)
3. **Conditional tools?** (Only available during certain modes)
4. **Tool chaining?** (One tool calls another)

---

*Document Version: 1.0*  
*Last Updated: January 2026*  
*Author: Interchained / AiAssist Secure Team*
