---
title: Multi-Provider Integration
description: Plan for supporting OpenAI, Anthropic, Gemini, and Mistral.
category: Platform
icon: Layers
order: 5
---

# Multi-Provider AI Integration Plan

## Overview

This document outlines the plan to extend AiAssist's public API (`/v1/chat/completions`) to support multiple AI providers beyond Groq. Users can bring their own API keys (BYOK) and select their preferred provider from the dashboard.

**Scope**: Client-side public API only. The internal admin AI (workspace chat) remains Groq-powered.

---

## Current State Analysis

### Existing Infrastructure (What We Have)

| Component | Location | Status |
|-----------|----------|--------|
| OpenAI-compatible endpoint | `api/routes/public_api.py` | ✅ Exists, hardcoded to Groq |
| Provider credential storage | `api/services/redis_storage.py` | ✅ Supports multiple providers |
| BYOK UI walkthrough | `client/src/components/GroqSetupWalkthrough.tsx` | ✅ Groq-only, needs generalization |
| Credential encryption | `api/utils/encryption.py` | ✅ Ready for any API key |
| Rate limiting | `api/routes/public_api.py` | ✅ Per-user, per-key |

### Key Finding: Minimal Changes Required

The current architecture is **already designed for multi-provider support**:

1. Redis stores credentials with provider type: `user_providers:{user_id}` → `{provider: cred_id}`
2. The `ProviderType` enum exists but only has `groq`
3. The public API just needs a provider router layer

---

## Supported Providers

### Tier 1 (Launch)

| Provider | API Endpoint | Auth Header | Default Models |
|----------|-------------|-------------|----------------|
| **Groq** (platform default) | `api.groq.com/openai/v1` | `Bearer {key}` | llama-3.3-70b-versatile, llama-3.1-8b-instant, mixtral-8x7b-32768 |
| **OpenAI** | `api.openai.com/v1` | `Bearer {key}` | gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-3.5-turbo |
| **Anthropic** | `api.anthropic.com/v1/messages` | `x-api-key: {key}` + `anthropic-version: 2023-06-01` | claude-3-5-sonnet-20241022, claude-3-opus-20240229, claude-3-haiku-20240307 |
| **Google Gemini** | `generativelanguage.googleapis.com/v1beta` | `x-goog-api-key: {key}` | gemini-1.5-pro, gemini-1.5-flash, gemini-pro |
| **Mistral** | `api.mistral.ai/v1` | `Bearer {key}` | mistral-large-latest, mistral-medium-latest, mistral-small-latest |

---

## Production-Hardening Requirements (Oracle Recommendations)

### 1. Dynamic Model Lists (Don't Hardcode)

Models go stale fast. Treat static config as **defaults only**.

**Implementation:**
- `GET /api/providers` returns cached provider models
- Background refresh calls provider `/models` endpoints (where supported) every 6 hours
- Cache results in Redis: `provider_models:{provider}` → `{models: [...], refreshed_at: ...}`
- If provider doesn't support `/models`, use static defaults

### 2. Explicit Provider Override Headers

Inference by model prefix is convenient, but enterprise customers need deterministic control.

**New Headers:**
- `X-AiAssist-Provider: openai|anthropic|gemini|mistral|groq` - Force specific provider
- `X-AiAssist-Byok: true|false` - Optional, for internal metrics

**Provider Resolution Priority:**
1. Explicit header override (`X-AiAssist-Provider`)
2. Model name inference (gpt-* → OpenAI, claude-* → Anthropic, etc.)
3. User's default provider setting
4. Platform default (Groq)

### 3. Provider Adapter Pattern (No if/else Spaghetti)

Create one interface per provider for easy extension.

**Router Flow:**
```
resolve provider → fetch key → call adapter → normalize response → record usage
```

---

## Fallback Policy

### Key Rule: No Silent Fallback on BYOK Failure

If a user's BYOK key fails (401/403):
- ❌ Don't silently switch to another provider
- ✅ Return clear error: "Your {provider} API key is invalid"
- ✅ Mark credential as invalid in Redis

### Exception: Platform Groq Fallback

If user has **no BYOK key configured** for the requested provider:
- Check if their plan allows platform credits
- If yes → route to platform Groq
- If no → return "No API key configured for {provider}"

---

## Usage Accounting

Record with these dimensions for billing and debugging:

```python
def record_usage(
    user_id: str,
    api_key_id: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    provider: str,
    using_byok: bool,
    request_id: str,  # Our internal ID
    provider_request_id: Optional[str] = None  # If provider returns one
):
    """Enhanced usage recording with provider dimensions."""
    usage_record = {
        "user_id": user_id,
        "api_key_id": api_key_id,
        "model": model,
        "provider": provider,
        "using_byok": using_byok,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "request_id": request_id,
        "provider_request_id": provider_request_id,
        "timestamp": datetime.utcnow().isoformat()
    }
    # Store in Redis list for analytics
    storage.r.lpush(key(f"usage_log:{user_id}"), json.dumps(usage_record))
    # Update counters
    storage.r.hincrby(key(f"usage:{user_id}"), "tokens_used", input_tokens + output_tokens)
```
