# AiAS Public API — Tools Specification

**Version:** 1.0
**Base URL:** `https://api.aiassist.net`
**Auth:** Bearer token (`Authorization: Bearer aai_xxxxxxxxxxxx`)
**Owner:** Interchained LLC

---

## Overview

The AiAS public API exposes two families of capabilities:

1. **Inference tools** — AI-callable functions wired into `/v1/chat/completions` so any LLM (OpenAI, Anthropic, Gemini, Groq, Mistral, etc.) can invoke them through standard tool/function-calling.
2. **Direct REST tools** — Plain HTTP endpoints any client can call without an LLM in the loop, used by Keystone, the SDKs, and third-party integrations.

This document is the canonical reference for both surfaces.

---

## 1. Inference Tools (LLM-callable)

These tools are advertised to the LLM through its native tool-calling format. The orchestrator translates between OpenAI, Anthropic, and Gemini schemas automatically — clients only pick the model and we ship the right shape.

### 1.1 `search_web`

Search the public web and return ranked evidence with citation IDs.

| Property | Value |
|---|---|
| Function name | `search_web` |
| Backed by | Tavily (primary) → DuckDuckGo (fallback) |
| Required plan | Any plan with a configured provider |
| Quality tiers | `premium`, `standard`, `best_effort` |
| Caching | 5-minute TTL on Evidence Bundles |

**Parameters**

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `query` | string | yes | — | Specific, contextual search query |
| `max_results` | integer | no | `3` | 1–5 results to return |

**OpenAI / Groq / Mistral / DeepSeek / OpenRouter / xAI tool schema**

```json
{
  "type": "function",
  "function": {
    "name": "search_web",
    "description": "Search the web for current information... Results include citation IDs like [SRC-001].",
    "parameters": {
      "type": "object",
      "properties": {
        "query": { "type": "string" },
        "max_results": { "type": "integer", "default": 3 }
      },
      "required": ["query"]
    }
  }
}
```

**Anthropic schema**

```json
{
  "name": "search_web",
  "description": "...",
  "input_schema": {
    "type": "object",
    "properties": {
      "query": { "type": "string" },
      "max_results": { "type": "integer", "default": 3 }
    },
    "required": ["query"]
  }
}
```

**Gemini schema**

```json
{
  "function_declarations": [{
    "name": "search_web",
    "description": "...",
    "parameters": {
      "type": "object",
      "properties": {
        "query": { "type": "string" },
        "max_results": { "type": "integer" }
      },
      "required": ["query"]
    }
  }]
}
```

**Returned tool result (to the model)**

```
[SRC-001] Title: ...
URL: ...
Domain: ...
Snippet: ...
Confidence: 0.87
Published: 2026-04-12

[SRC-002] ...
```

The model is instructed to cite using the `[SRC-###]` IDs.

**Safety / hygiene**
- Secret patterns (`sk-…`, `tvly-…`, `gsk_…`, `AIza…`, `Bearer …`, `password=…`) blocked at query time.
- Internal hosts blocked: `localhost`, `127.0.0.1`, RFC1918 ranges, `.internal`, `.local`, `.lan`.
- Email and phone patterns scrubbed pre-flight.
- Per-plan daily limits: free `10`, basic `50`, pro `200`, enterprise unlimited.

---

### 1.2 `visit_url`

Fetch a specific webpage and return clean readable text.

| Property | Value |
|---|---|
| Function name | `visit_url` |
| Backed by | Internal Web Extraction Service (HTTP fetch + readability + headless browser fallback) |
| Required plan | Any plan |
| Caching | 5-minute TTL per URL |

**When to call (description shipped to the model)**
- User asks "what's on [website]" or "show me [domain]"
- User wants info about a specific URL they mentioned
- User asks to visit, check, or read a page
- The model needs the actual page content (use `search_web` to find candidates first)

**Parameters**

| Field | Type | Required | Default | Description |
|---|---|---|---|---|
| `url` | string | yes | — | Full URL with `http://` or `https://` |
| `include_links` | boolean | no | `false` | Include extracted link list in response |

**OpenAI schema**

```json
{
  "type": "function",
  "function": {
    "name": "visit_url",
    "description": "Fetch and extract the main content from a specific webpage...",
    "parameters": {
      "type": "object",
      "properties": {
        "url": { "type": "string" },
        "include_links": { "type": "boolean", "default": false }
      },
      "required": ["url"]
    }
  }
}
```

Anthropic and Gemini variants are structurally identical (different envelope keys: `input_schema` for Anthropic, `function_declarations` for Gemini).

**Returned tool result (to the model)**

Markdown-formatted extracted content, capped at the requested `max_content_length` (default 15 000 chars). Includes title, domain, description, and optionally a links section.

**SSRF protection**

The URL must pass `validate_extraction_url`, which blocks:
- `localhost`, `127.0.0.0/8`
- RFC1918 (`10.0.0.0/8`, `172.16/12`, `192.168/16`)
- `169.254.0.0/16` (link-local + cloud metadata)
- IPv6 link-local (`fe80:`), unique-local (`fc`/`fd`), `::1`
- `.local`, `.internal`, `.localhost` TLDs
- Cloud metadata hosts (`metadata.*`, `instance-data*`)

---

### 1.3 `escalate_to_human`

Fires only when the user explicitly asks for a human agent. The orchestrator returns a fixed acknowledgement and pings the workspace's escalation channel.

| Property | Value |
|---|---|
| Function name | `escalate_to_human` |
| Required plan | Any |
| Trigger phrases | `"speak to a human"`, `"talk to a manager"`, `"get me a human"`, `"I want a real person"`, `"transfer me to a human"`, etc. |

**Parameters** — none

The prompt explicitly forbids the model from calling this tool for general questions, complaints, or unanswerable queries.

---

### 1.4 Custom Tools (per-organization)

Organizations can register their own tools through the Custom Tooling System v2. They appear in the chat completions tool list automatically and follow the same multi-format translation pipeline.

| Catalog | Visibility | Author |
|---|---|---|
| `private` | Org-only | Org admin |
| `public` | All users | Platform-curated |

Each tool definition includes:

```python
{
  "id": "ct_xxx",
  "name": "lookup_invoice",
  "description": "Find an invoice by number or customer name.",
  "parameters": {
    "type": "object",
    "properties": {
      "invoice_number": { "type": "string", "description": "..." },
      "customer_name":  { "type": "string", "description": "..." }
    },
    "required": ["invoice_number"]
  }
}
```

Dispatched to the orgs' configured webhook executor. The executor enforces SSRF rules, signs requests with HMAC, and stores secrets encrypted (envelope encryption, per-org TMK).

Function name on the wire is prefixed with `custom_` and dashes are replaced with underscores: tool id `ct-abc-123` becomes function `custom_ct_abc_123`.

---

## 2. Direct REST Endpoints

All endpoints are mounted under `/v1/*` on the public API router and `/api/v1/*` on the proxy router (alias). Bearer auth is required everywhere.

### 2.1 `POST /v1/chat/completions`

OpenAI-compatible chat completion endpoint. See the dedicated chat-completions guide for full request/response shape — relevant to this doc:

- Tools attach via the standard `tools` array (OpenAI shape) and the orchestrator translates them per-provider.
- `tool_choice` is honored: `"auto"`, `"required"`, `{"type":"function","function":{"name":"search_web"}}`.
- `web_search_enabled` (workspace setting) controls whether `search_web` and `visit_url` get auto-injected for native (non-custom) tool runs.
- The orchestrator includes a deprecation/unknown-model shim — requests with retired or unrecognized model ids are transparently rerouted to the user's configured default for that provider, then to `DEFAULT_MODELS[provider]`, then to a final platform default.

---

### 2.2 `POST /v1/web/extract`

Direct REST counterpart of the `visit_url` inference tool. Free utility — no LLM in the loop.

**Request**

```json
{
  "url": "https://example.com/article",
  "extract_links": false,
  "max_content_length": 15000,
  "use_browser": null
}
```

| Field | Type | Default | Notes |
|---|---|---|---|
| `url` | string | — | Required, must be public HTTP(S). SSRF-validated. |
| `extract_links` | boolean | `false` | Include outbound links list. |
| `max_content_length` | integer | `15000` | Clamped to `[100, 15000]`. |
| `use_browser` | boolean? | `null` | Force headless browser. `null` = auto. |

**Response — `WebExtractResponse`**

```json
{
  "success": true,
  "url": "https://example.com/article",
  "title": "Article title",
  "content": "Markdown-cleaned body...",
  "content_length": 4231,
  "extracted_at": "2026-04-16T20:14:32Z",
  "domain": "example.com",
  "description": "Meta description if present",
  "fetch_method": "http",
  "latency_ms": 412,
  "cached": false,
  "error_code": null,
  "error_message": null
}
```

**Error codes (when `success: false`)**

| Code | Meaning |
|---|---|
| `INVALID_URL` | URL failed SSRF validation |
| `BLOCKED_DOMAIN` | Domain on platform deny list |
| `FETCH_FAILED` | Network or HTTP error |
| `TIMEOUT` | Upstream timed out |
| `EMPTY_CONTENT` | Page returned no extractable text |

---

### 2.3 `POST /v1/search`

Direct REST counterpart of `search_web` — used by Keystone Lite Focus mode.

**Request**

```json
{
  "query": "agentic browser launch 2026",
  "search_depth": "basic",
  "max_results": 5
}
```

| Field | Type | Default | Notes |
|---|---|---|---|
| `query` | string | — | Required. Goes through the same hygiene rules as the inference tool. |
| `search_depth` | string | `"basic"` | `"basic"` faster, `"advanced"` more comprehensive. |
| `max_results` | integer | `5` | Clamped `[1, 10]`. |

**Response — `WebSearchResponse`**

```json
{
  "success": true,
  "query": "agentic browser launch 2026",
  "results": [
    { "title": "...", "url": "...", "content": "snippet" }
  ],
  "quality_tier": "standard",
  "error": null
}
```

---

### 2.4 `GET /v1/health`

Liveness check. Returns API version, uptime, dependency status (Redis, provider config cache).

---

### 2.5 `GET /v1/models`

Returns available models the caller can use, filtered by their configured providers.

---

### 2.6 `GET /v1/providers`

Returns the caller's configured providers, each with default model and full model list (used by Keystone and the CRM provider cache).

```json
{
  "providers": [
    {
      "id": "groq",
      "name": "Groq",
      "models": [
        { "id": "llama-3.3-70b-versatile", "name": "Llama 3.3 70B Versatile",
          "provider": "groq", "context_window": 128000, "max_output": 32768 }
      ]
    }
  ]
}
```

---

### 2.7 `GET /v1/usage`

Per-key usage stats (requests, tokens, search calls, extractions) for the current billing period.

---

### 2.8 `GET /v1/organization`, `GET /v1/provider`, `GET /v1/availability`

- `organization` — returns the org tied to the API key
- `provider` — returns the caller's primary provider config
- `availability` — staff/agent presence for the workspace (used by CRM/escalation flows)

---

## 3. Intelligence API (SaaS-Signal v1)

Pro / Enterprise only. Mounted under `/v1/intelligence/*` and aliased at `/api/v1/intelligence/*`. All responses use the standard envelope:

```json
{
  "data": { ... },
  "meta": {
    "request_id": "req_abc123",
    "timestamp": "2026-04-16T20:00:00Z",
    "version": "1.0.0",
    "org_id": "org_xxx",
    "processing_ms": 412
  }
}
```

### 3.1 `GET /v1/intelligence/sources`

List the registered signal sources (Reddit, Hacker News, Twitter, ProductHunt, IndieHackers, GitHub Trending, etc. — 22+ sources).

**Response**

```json
{
  "data": {
    "sources": [
      { "id": "reddit", "name": "Reddit", "category": "community", "supports_keywords": true },
      { "id": "hn",     "name": "Hacker News", "category": "tech", "supports_keywords": true },
      ...
    ]
  },
  "meta": { ... }
}
```

---

### 3.2 `POST /v1/intelligence/scan`

Scan one or more sources for signals matching keywords.

**Request**

```json
{
  "sources": ["reddit", "hn", "twitter"],
  "keywords": ["agentic", "byok", "ai gateway"],
  "limit": 25,
  "category": "recent",
  "subreddits": ["r/LocalLLaMA", "r/MachineLearning"]
}
```

| Field | Type | Default | Notes |
|---|---|---|---|
| `sources` | string[] | — | Required. Max 10. Each must exist in the source registry. |
| `keywords` | string[] | `[]` | OR-joined search terms |
| `limit` | integer | `25` | Per-source result cap, clamped `[1, 50]` |
| `category` | string | `"recent"` | Source-specific category (`recent`, `top`, `hot`, etc.) |
| `subreddits` | string[] | `[]` | Reddit-only filter |

**Response**

```json
{
  "data": {
    "results": [
      {
        "source": "reddit",
        "title": "...",
        "url": "...",
        "author": "...",
        "score": 142,
        "comments": 38,
        "created_at": "2026-04-15T14:22:11Z",
        "intent": "evaluating",
        "snippet": "..."
      }
    ],
    "total": 47,
    "sources_scanned": ["reddit", "hn"],
    "sources_failed": [
      { "source": "twitter", "error": "rate limited" }
    ]
  },
  "meta": { ... }
}
```

Sources are scanned concurrently with `asyncio.gather`. A failed source returns an error entry instead of failing the whole request.

**Intent categorization**

Each signal is classified into one of:

`buying`, `evaluating`, `hiring`, `complaining`, `recommending`, `learning`, `building`, `announcing`, `asking`, `comparing`.

---

### 3.3 `POST /v1/intelligence/extract-keywords`

LLM-assisted keyword expansion for campaign building. The signal scanner uses keywords; this endpoint helps users grow their keyword set conversationally.

**Request**

```json
{
  "prompt": "I'm targeting indie devs who want to add AI to their SaaS",
  "existing_keywords": ["llm", "ai sdk"],
  "model": "llama-3.3-70b-versatile",
  "provider": "groq"
}
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `prompt` | string | yes | Free-text describing the campaign |
| `existing_keywords` | string[] | no | Already-collected keywords (deduped against new ones) |
| `model` | string | no | Override model — falls back to the user's provider default |
| `provider` | string | no | Override provider — falls back to user's first configured provider |

**Behavior**

- BYOK: uses the caller's configured provider credentials
- If no model passed, picks from `provider_config.default_models[0].id`
- Filters out compound/router model ids (`/`, `compound`)
- Final fallback: `llama-3.3-70b-versatile`
- Currently supports providers: `groq`, `openai`, `anthropic`, `gemini`, `mistral`

**Response**

```json
{
  "data": {
    "new_keywords": ["indie hackers", "saas ai", "byok llm"],
    "all_keywords": ["llm", "ai sdk", "indie hackers", "saas ai", "byok llm"],
    "reply": "Got it — I added a few angles around indie SaaS builders adopting BYOK.",
    "model": "llama-3.3-70b-versatile",
    "provider": "groq"
  },
  "meta": { ... }
}
```

---

### 3.4 Roadmap (declared but not yet wired in this build)

Per `replit.md`, the SaaS-Signal Public API includes additional endpoints planned/staged in companion services:

| Endpoint | Purpose |
|---|---|
| `POST /v1/intelligence/stream-scan` | SSE-streamed scan for live dashboards |
| `GET /v1/intelligence/signals` | Replay historical signals from cache |
| `POST /v1/intelligence/score` | Re-score a signal against custom intent rubric |
| `POST /v1/intelligence/enrich` | Enrich signal author with public profile data |
| `GET /v1/intelligence/usage` | Per-key intelligence usage stats |
| `GET /v1/intelligence/tools` | LLM-callable tool manifest (OpenAI / MCP / LangChain formats) |

When live, these inherit the same envelope, auth, and Pro+ gating.

---

## 4. SDK Coverage

Both SDKs publish thin clients over these endpoints. Tools are first-class.

| SDK | Package | Notes |
|---|---|---|
| TypeScript | `@redprayers/intelligence` | Typed client, SSE async iterator for scan streaming, auto-retry on 5xx. |
| Python | `redprayers-intelligence` | sync + async `httpx` clients, Pydantic v2 models, SSE streaming generators. |

SDK examples (Python):

```python
from redprayers_intelligence import IntelClient

client = IntelClient(api_key="aai_xxx")

# REST search
hits = client.search("agentic browser launch", max_results=5)

# REST extract
page = client.extract("https://example.com/article", extract_links=True)

# Intelligence scan
result = client.intel.scan(
    sources=["reddit", "hn"],
    keywords=["byok", "ai gateway"],
    limit=25,
)
```

---

## 5. Tool Discovery for LLMs

For agents that prefer to fetch tool definitions at runtime (MCP, OpenAI function-calling, LangChain), three formats are exposed (or planned, see §3.4):

| Format | Endpoint (or location) | Notes |
|---|---|---|
| OpenAI function | Embedded in `/v1/chat/completions` `tools` array | Auto-attached when `web_search_enabled` is on |
| MCP manifest | `/v1/intelligence/tools?format=mcp` (planned) | Resource + tool definitions for MCP clients |
| LangChain Tool | `/v1/intelligence/tools?format=langchain` (planned) | Native LangChain `Tool` JSON |

---

## 6. Quick Reference

| Capability | Inference Tool | Direct REST | Auth | Pro+ |
|---|---|---|---|---|
| Web search | `search_web` | `POST /v1/search` | API key | No |
| Page extract | `visit_url` | `POST /v1/web/extract` | API key | No |
| Human escalate | `escalate_to_human` | (handled in chat completions) | API key | No |
| Custom tool | `custom_<id>` | (per-tool webhook) | API key | Org-defined |
| Signal sources | — | `GET /v1/intelligence/sources` | API key | Yes |
| Signal scan | — | `POST /v1/intelligence/scan` | API key | Yes |
| Keyword extract | — | `POST /v1/intelligence/extract-keywords` | API key | Yes |

---

## 7. Error Envelope (REST)

```json
{
  "detail": "Human-readable error",
  "error_code": "OPTIONAL_MACHINE_CODE"
}
```

Common HTTP statuses:

| Status | Meaning |
|---|---|
| `400` | Bad request — invalid params, blocked URL, unknown source |
| `401` | Missing or invalid bearer token |
| `403` | Plan does not include this endpoint |
| `429` | Rate limit / plan quota |
| `500` | Internal failure |
| `502` | Upstream provider error (LLM, search backend) |
| `503` | Storage/Redis unavailable |

---

*Interchained LLC — AiAS Public API Tools v1.0*
