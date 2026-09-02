---
title: Web Search Tool
icon: Search
category: RAG
order: 1
description: Real-time web search capabilities and provider fallback.
---

# Web Search Tool Specification

## Overview

The Web Search Tool provides AI assistants with the ability to search the web for real-time information. This is implemented as a local function/tool that all LLM providers can call, with the actual search logic handled by Python backend services.

**Key Design Principles:**
- Provider-agnostic: Results normalized into consistent Evidence format
- BYOK-first: Users can bring their own Tavily API key
- Graceful degradation: Falls back to DuckDuckGo when limits hit
- Audit-friendly: Logs metadata, not content

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        AI Orchestrator                          │
│  ┌─────────────┐    ┌──────────────┐    ┌─────────────────┐    │
│  │ LLM Request │───►│ Tool Handler │───►│ Response Merge  │    │
│  │ + Tools     │    │              │    │                 │    │
│  └─────────────┘    └──────┬───────┘    └─────────────────┘    │
│                            │                                    │
└────────────────────────────┼────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Web Search Service                          │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Query Hygiene (Preflight Check)             │   │
│  │  • Length validation (max 500 chars)                     │   │
│  │  • Secret detection (API keys, tokens, passwords)        │   │
│  │  • PII check (emails, phones - optional redaction)       │   │
│  │  • Internal URL blocking                                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│                             │                                   │
│                             ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Provider Arbitration Module                 │   │
│  │  Decision: Which provider + mode to use?                 │   │
│  │  1. Workspace BYOK key → mode=byok, tier=premium        │   │
│  │  2. User BYOK key → mode=byok, tier=premium             │   │
│  │  3. Org BYOK key → mode=byok, tier=premium              │   │
│  │  4. Platform key (if quota OK) → mode=platform, tier=std │   │
│  │  5. DuckDuckGo → mode=fallback, tier=best_effort        │   │
│  └─────────────────────────────────────────────────────────┘   │
│                             │                                   │
│                             ▼                                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Tavily API   │  │ DuckDuckGo   │  │ Evidence Cache       │  │
│  │ (Primary)    │  │ (Fallback)   │  │ (Redis TTL 5min)     │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                             │                                   │
│                             ▼                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   Evidence Layer                         │   │
│  │  Normalize results → Evidence objects with [SRC-###] IDs │   │
│  │  Generate evidence_prompt for LLM consumption            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                             │                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Search Providers

### 1. Tavily (Primary)
- **Purpose**: High-quality, AI-optimized search results
- **API**: `https://api.tavily.com/search`
- **Features**:
  - Returns clean, summarized content
  - Optimized for LLM consumption
  - Supports search depth (basic/advanced)
  - Includes relevance scoring
- **Quality Tier**: `premium` (BYOK) or `standard` (platform)

### 2. DuckDuckGo (Fallback)
- **Purpose**: Free fallback when Tavily limits are reached
- **Method**: Uses `duckduckgo-search` Python package
- **Features**:
  - No API key required
  - Rate-limited by DuckDuckGo
  - Basic search results
- **Quality Tier**: `best_effort`
- **Limitations**: Less reliable, may be blocked under heavy use

---

## Evidence Layer

Instead of returning raw provider results, the service normalizes everything into a consistent Evidence format with citation IDs.

### Evidence Object

```python
@dataclass
class Evidence:
    id: str              # "SRC-001", "SRC-002", etc.
    title: str           # Page title
    url: str             # Source URL
    domain: str          # Extracted domain (e.g., "docs.python.org")
    snippet: str         # 200-char summary
    published_date: Optional[str]  # If available
    confidence: float    # 0.0-1.0 relevance score
```

### Evidence Bundle (Response to LLM)

```python
@dataclass
class EvidenceBundle:
    query: str
    evidence: List[Evidence]
    evidence_prompt: str        # Pre-formatted text for LLM
    quality_tier: str           # "premium" | "standard" | "best_effort"
    provider_mode: str          # "byok" | "platform" | "fallback"
    tool_version: str           # "1.0"
    cached: bool                # Was this from cache?
```

### Evidence Prompt Format

The `evidence_prompt` is what gets injected into the LLM context:

```
Web Search Results for: "Python 3.12 new features"
Quality: Premium (Tavily BYOK)

[SRC-001] What's New In Python 3.12 - docs.python.org
Python 3.12 introduces improved error messages, per-interpreter GIL, and new typing features including TypedDict improvements...

[SRC-002] Python 3.12 Release Notes - python.org
Released October 2023. Major features include better debugging, f-string improvements, and performance enhancements...

[SRC-003] Python 3.12 Performance Guide - realpython.com
Benchmarks show 5-10% speed improvements in common operations...

---
Sources: 3 results from premium search. Citations use [SRC-###] format.
```

---

## Provider Arbitration Module

A deterministic function that decides which provider to use:

```python
def select_provider(user_id: str, workspace_id: str) -> ProviderDecision:
    """
    Returns:
        provider: "tavily" | "duckduckgo"
        mode: "byok" | "platform" | "fallback"
        quality_tier: "premium" | "standard" | "best_effort"
        api_key: Optional[str]
        reason: str
    """
    
    # 1. Check workspace-level BYOK
    ws_key = get_workspace_tavily_key(workspace_id)
    if ws_key:
        return ProviderDecision("tavily", "byok", "premium", ws_key, "workspace_byok")
    
    # 2. Check user-level BYOK
    user_key = get_user_tavily_key(user_id)
    if user_key:
        return ProviderDecision("tavily", "byok", "premium", user_key, "user_byok")
    
    # 3. Check org-level BYOK
    org_key = get_org_tavily_key(user_id)
    if org_key:
        return ProviderDecision("tavily", "byok", "premium", org_key, "org_byok")
    
    # 4. Check platform quota
    usage = get_platform_usage(user_id)
    if usage.remaining > 0 and PLATFORM_TAVILY_KEY:
        return ProviderDecision("tavily", "platform", "standard", PLATFORM_TAVILY_KEY, "platform_quota")
    
    # 5. Fallback to DuckDuckGo
    return ProviderDecision("duckduckgo", "fallback", "best_effort", None, "fallback")
```

---

## Query Hygiene & Policy Blocking

Before sending any query to a search provider, validate it:

### Preflight Checks

```python
def validate_query(query: str) -> ValidationResult:
    errors = []
    
    # 1. Length check (max 500 characters)
    if len(query) > 500:
        errors.append("QUERY_TOO_LONG")
    
    # 2. Secret detection patterns
    SECRET_PATTERNS = [
        r'[a-zA-Z0-9]{32,}',           # Long random strings (API keys)
        r'sk-[a-zA-Z0-9]{20,}',         # OpenAI keys
        r'tvly-[a-zA-Z0-9]{20,}',       # Tavily keys
        r'Bearer\s+[a-zA-Z0-9._-]+',    # Bearer tokens
        r'password[=:]\s*\S+',          # Password patterns
    ]
    for pattern in SECRET_PATTERNS:
        if re.search(pattern, query, re.I):
            errors.append("CONTAINS_SECRET")
            break
    
    # 3. Internal URL blocking
    BLOCKED_DOMAINS = ['localhost', '127.0.0.1', '10.', '192.168.', '.internal']
    for domain in BLOCKED_DOMAINS:
        if domain in query.lower():
            errors.append("INTERNAL_URL_BLOCKED")
            break
    
    # 4. Optional PII detection (if strict mode)
    if contains_email(query) or contains_phone(query):
        errors.append("CONTAINS_PII")
    
    return ValidationResult(valid=len(errors)==0, errors=errors)
```

### Error Response

If validation fails, return `POLICY_BLOCKED` with a safe explanation:

```json
{
  "success": false,
  "error_code": "POLICY_BLOCKED",
  "error": "Query contains patterns that cannot be sent to external search services.",
  "safe_message": "I cannot search for that query as it may contain sensitive information."
}
```

---

## Usage Tracking (Split BYOK vs Platform)

Track usage separately to be transparent with users:

### Redis Keys

```
# BYOK searches (no limit, just tracking)
web_search_usage:{user_id}:byok:{YYYY-MM-DD} → Integer

# Platform searches (subject to plan limits)
web_search_usage:{user_id}:platform:{YYYY-MM-DD} → Integer

# Fallback searches (tracking only)
web_search_usage:{user_id}:fallback:{YYYY-MM-DD} → Integer
```

---

## Domain Filter Semantics

### Behavior

| Filter | Behavior |
|--------|----------|
| `include_domains` | Soft boost - prioritize these but include others |
| `exclude_domains` | Hard block - never return results from these |
| `strict_allowlist=true` | Only return results from `include_domains` (Enterprise) |

---

## Audit Logging Schema

Log structured events without storing sensitive content:

```python
@dataclass
class SearchAuditEvent:
    tool_call_id: str           # UUID linking to LLM conversation
    user_id: str
    workspace_id: str
    query_hash: str             # SHA256 hash, not actual query
    timestamp: str              # ISO format
    provider: str               # "tavily" | "duckduckgo"
    provider_mode: str          # "byok" | "platform" | "fallback"
    quality_tier: str           # "premium" | "standard" | "best_effort"
    latency_ms: int
    result_count: int
    domains_returned: List[str] # Just domains, not URLs
    cached: bool
    outcome: str                # "success" | "error" | "policy_blocked"
    error_code: Optional[str]
```

**Storage**: Redis sorted set with timestamp score, keep last 10,000 entries.

---

## Function Schema

### OpenAI/Groq/OpenRouter Format

```json
{
  "type": "function",
  "function": {
    "name": "search_web",
    "description": "Search the web for current, real-time information. Use when you need up-to-date facts, news, prices, documentation, or information that may have changed after your training cutoff.",
    "parameters": {
      "type": "object",
      "properties": {
        "query": {
          "type": "string",
          "description": "The search query. Be specific and include relevant context."
        },
        "max_results": {
          "type": "integer",
          "description": "Number of results (1-5). Default is 3.",
          "default": 3
        }
      },
      "required": ["query"]
    }
  }
}
```

---

## Future Enhancements

1. **Multi-Provider Aggregation**: Fan-out to multiple providers, dedupe by URL
2. **Image Search**: Add image search capability
3. **News Search**: Dedicated news endpoint with date filtering
4. **Search Analytics**: Dashboard showing popular queries and usage patterns
