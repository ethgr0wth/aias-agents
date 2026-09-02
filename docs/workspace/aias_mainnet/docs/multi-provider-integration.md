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

### Existing Storage Methods (Already Implemented)

The following methods already exist in `api/services/redis_storage.py`:

| Method | Purpose | Line |
|--------|---------|------|
| `save_provider_credential(user_id, provider, encrypted_key, key_prefix)` | Store encrypted API key | 1919 |
| `get_provider_credential(user_id, provider)` | Get credential metadata (no key) | 1951 |
| `get_provider_credential_with_key(user_id, provider)` | Get credential + decrypted key | 1973 |
| `delete_provider_credential(user_id, provider)` | Remove credential | 1990 |
| `update_provider_credential_status(user_id, provider, status)` | Update status (active/invalid) | 1999 |

The encryption utilities exist in `api/utils/encryption.py`:
- `encrypt_api_key(plaintext)` → encrypted string
- `decrypt_api_key(encrypted)` → plaintext

**No new storage methods needed for basic multi-provider support.**

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

### Tier 2 (Future)

- Together AI
- Fireworks AI
- Cohere
- Perplexity
- AWS Bedrock
- Azure OpenAI

---

## Production-Hardening Requirements (Oracle Recommendations)

### 1. Dynamic Model Lists (Don't Hardcode)

Models go stale fast. Treat static config as **defaults only**.

**Implementation:**
- `GET /api/providers` returns cached provider models
- Background refresh calls provider `/models` endpoints (where supported) every 6 hours
- Cache results in Redis: `provider_models:{provider}` → `{models: [...], refreshed_at: ...}`
- If provider doesn't support `/models`, use static defaults

```python
# Providers that support /models endpoint
PROVIDERS_WITH_MODELS_ENDPOINT = ["openai", "groq", "mistral"]

async def refresh_provider_models(provider: str, api_key: str) -> List[str]:
    """Fetch current models from provider. Falls back to defaults on failure."""
    if provider not in PROVIDERS_WITH_MODELS_ENDPOINT:
        return PROVIDERS[provider].default_models
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{PROVIDERS[provider].base_url}/models",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            response.raise_for_status()
            data = response.json()
            return [m["id"] for m in data.get("data", [])]
    except Exception:
        return PROVIDERS[provider].default_models
```

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

```python
def resolve_provider(
    model: str,
    header_override: Optional[str],
    user_default: Optional[str]
) -> ProviderType:
    # 1. Explicit header override
    if header_override:
        return ProviderType(header_override)
    
    # 2. Model inference
    inferred = get_provider_for_model(model)
    if inferred:
        return inferred
    
    # 3. User default
    if user_default:
        return ProviderType(user_default)
    
    # 4. Platform default
    return ProviderType.GROQ
```

### 3. Provider Adapter Pattern (No if/else Spaghetti)

Create one interface per provider for easy extension:

```python
from typing import Protocol, AsyncIterator

class ProviderAdapter(Protocol):
    """Protocol for provider adapters. Implement for each provider."""
    provider: ProviderType
    
    async def complete(
        self,
        *,
        api_key: str,
        model: str,
        messages: list,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> dict:
        """Non-streaming completion."""
        ...
    
    async def stream(
        self,
        *,
        api_key: str,
        model: str,
        messages: list,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> AsyncIterator[dict]:
        """Streaming completion."""
        ...
    
    def normalize_error(self, exc: Exception, status_code: int | None) -> tuple[int, str]:
        """Convert provider error to (status_code, message)."""
        ...
    
    def supports_model(self, model: str) -> bool:
        """Check if adapter handles this model."""
        ...
```

**Router Flow:**
```
resolve provider → fetch key → call adapter → normalize response → record usage
```

**File Structure:**
```
api/providers/
├── __init__.py
├── config.py           # Provider configs, model defaults
├── router.py           # Main routing logic
├── adapters/
│   ├── __init__.py
│   ├── base.py         # ProviderAdapter Protocol
│   ├── openai_compat.py  # OpenAI, Groq, Mistral
│   ├── anthropic.py
│   └── gemini.py
└── health.py           # Provider health checks
```

### 4. OpenAI Responses API Awareness

OpenAI is pushing toward their Responses API, but `/v1/chat/completions` still works. Keep our public API OpenAI-compatible but:
- Continue calling `/v1/chat/completions` for now
- Design adapter to easily swap to Responses API later

### 5. Gemini-Specific Considerations

Gemini's API differs significantly:
- Different endpoint pattern: `/models/{model}:generateContent`
- Different message format: `contents` with `parts`
- System instruction is separate field
- Auth via `x-goog-api-key` header

```python
class GeminiAdapter:
    """Gemini requires special handling for messages and auth."""
    
    def _convert_messages(self, messages: list) -> tuple[list, Optional[str]]:
        """Convert OpenAI messages to Gemini format."""
        contents = []
        system_instruction = None
        
        for msg in messages:
            if msg["role"] == "system":
                system_instruction = msg["content"]
            else:
                role = "user" if msg["role"] == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg["content"]}]
                })
        
        return contents, system_instruction
```

### 6. Reliability Patterns

**Timeouts & Retries:**
```python
PROVIDER_TIMEOUTS = {
    "groq": 30.0,      # Groq is fast
    "openai": 60.0,
    "anthropic": 90.0,  # Claude can be slow
    "gemini": 60.0,
    "mistral": 60.0,
}

async def call_with_retry(adapter, **kwargs):
    """One retry on 429/503, with exponential backoff."""
    for attempt in range(2):
        try:
            return await adapter.complete(**kwargs)
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (429, 503) and attempt == 0:
                await asyncio.sleep(1.0 * (attempt + 1))
                continue
            raise
```

**Circuit Breaker:**
```python
# Store in Redis
provider_health:{provider} = {
    "last_error": "2024-12-19T10:30:00Z",
    "error_count": 3,
    "status": "degraded"  # healthy | degraded | down
}
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

```python
def get_api_key_for_request(
    user_id: str,
    provider: ProviderType,
    user_plan: str
) -> tuple[str, bool]:
    """
    Returns (api_key, is_byok).
    Falls back to platform Groq only if no BYOK and plan allows.
    """
    # Try user's BYOK first
    cred = storage.get_provider_credential_with_key(user_id, provider.value)
    if cred:
        return cred[1], True  # (decrypted_key, is_byok=True)
    
    # No BYOK - check platform fallback
    if provider == ProviderType.GROQ or user_plan in ["basic", "pro", "enterprise"]:
        # Use platform Groq
        return os.environ.get("GROQ_API_KEY"), False
    
    raise ValueError(f"No API key configured for {provider.value}. Add your key in the dashboard.")
```

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

---

## Architecture Design

### Provider Configuration Module

**File**: `api/providers/config.py`

```python
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel

class ProviderType(str, Enum):
    GROQ = "groq"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GEMINI = "gemini"
    MISTRAL = "mistral"

class ProviderModel(BaseModel):
    id: str
    name: str
    context_window: int
    max_output: int

class ProviderConfig(BaseModel):
    id: ProviderType
    name: str
    base_url: str
    auth_header: str  # "Authorization" or "x-api-key"
    auth_prefix: str  # "Bearer " or ""
    default_models: List[ProviderModel]  # Defaults, may be refreshed
    requires_version_header: bool = False
    version_header: Optional[str] = None
    supports_models_endpoint: bool = False  # Can we fetch /models?
    timeout: float = 60.0
    docs_url: str
    console_url: str  # Where users get API keys

PROVIDERS: Dict[ProviderType, ProviderConfig] = {
    ProviderType.GROQ: ProviderConfig(
        id=ProviderType.GROQ,
        name="Groq",
        base_url="https://api.groq.com/openai/v1",
        auth_header="Authorization",
        auth_prefix="Bearer ",
        supports_models_endpoint=True,
        timeout=30.0,
        docs_url="https://console.groq.com/docs",
        console_url="https://console.groq.com/keys",
        default_models=[
            ProviderModel(id="llama-3.3-70b-versatile", name="Llama 3.3 70B", context_window=128000, max_output=32768),
            ProviderModel(id="llama-3.1-8b-instant", name="Llama 3.1 8B", context_window=128000, max_output=8192),
            ProviderModel(id="mixtral-8x7b-32768", name="Mixtral 8x7B", context_window=32768, max_output=32768),
        ]
    ),
    ProviderType.OPENAI: ProviderConfig(
        id=ProviderType.OPENAI,
        name="OpenAI",
        base_url="https://api.openai.com/v1",
        auth_header="Authorization",
        auth_prefix="Bearer ",
        supports_models_endpoint=True,
        timeout=60.0,
        docs_url="https://platform.openai.com/docs",
        console_url="https://platform.openai.com/api-keys",
        default_models=[
            ProviderModel(id="gpt-4o", name="GPT-4o", context_window=128000, max_output=16384),
            ProviderModel(id="gpt-4o-mini", name="GPT-4o Mini", context_window=128000, max_output=16384),
            ProviderModel(id="gpt-4-turbo", name="GPT-4 Turbo", context_window=128000, max_output=4096),
            ProviderModel(id="gpt-3.5-turbo", name="GPT-3.5 Turbo", context_window=16385, max_output=4096),
        ]
    ),
    ProviderType.ANTHROPIC: ProviderConfig(
        id=ProviderType.ANTHROPIC,
        name="Anthropic",
        base_url="https://api.anthropic.com/v1",
        auth_header="x-api-key",
        auth_prefix="",
        requires_version_header=True,
        version_header="2023-06-01",
        timeout=90.0,
        docs_url="https://docs.anthropic.com",
        console_url="https://console.anthropic.com/settings/keys",
        default_models=[
            ProviderModel(id="claude-3-5-sonnet-20241022", name="Claude 3.5 Sonnet", context_window=200000, max_output=8192),
            ProviderModel(id="claude-3-opus-20240229", name="Claude 3 Opus", context_window=200000, max_output=4096),
            ProviderModel(id="claude-3-haiku-20240307", name="Claude 3 Haiku", context_window=200000, max_output=4096),
        ]
    ),
    ProviderType.GEMINI: ProviderConfig(
        id=ProviderType.GEMINI,
        name="Google Gemini",
        base_url="https://generativelanguage.googleapis.com/v1beta",
        auth_header="x-goog-api-key",
        auth_prefix="",
        timeout=60.0,
        docs_url="https://ai.google.dev/docs",
        console_url="https://aistudio.google.com/app/apikey",
        default_models=[
            ProviderModel(id="gemini-1.5-pro", name="Gemini 1.5 Pro", context_window=2000000, max_output=8192),
            ProviderModel(id="gemini-1.5-flash", name="Gemini 1.5 Flash", context_window=1000000, max_output=8192),
            ProviderModel(id="gemini-pro", name="Gemini Pro", context_window=32000, max_output=8192),
        ]
    ),
    ProviderType.MISTRAL: ProviderConfig(
        id=ProviderType.MISTRAL,
        name="Mistral AI",
        base_url="https://api.mistral.ai/v1",
        auth_header="Authorization",
        auth_prefix="Bearer ",
        supports_models_endpoint=True,
        timeout=60.0,
        docs_url="https://docs.mistral.ai",
        console_url="https://console.mistral.ai/api-keys",
        default_models=[
            ProviderModel(id="mistral-large-latest", name="Mistral Large", context_window=128000, max_output=8192),
            ProviderModel(id="mistral-medium-latest", name="Mistral Medium", context_window=32000, max_output=8192),
            ProviderModel(id="mistral-small-latest", name="Mistral Small", context_window=32000, max_output=8192),
        ]
    ),
}

def get_provider(provider_type: ProviderType) -> ProviderConfig:
    return PROVIDERS[provider_type]

def get_all_providers() -> List[ProviderConfig]:
    return list(PROVIDERS.values())

def get_provider_for_model(model_id: str) -> Optional[ProviderType]:
    """Determine provider from model ID prefix or known model names."""
    # GPT models → OpenAI
    if model_id.startswith("gpt-"):
        return ProviderType.OPENAI
    # Claude models → Anthropic
    if model_id.startswith("claude-"):
        return ProviderType.ANTHROPIC
    # Gemini models → Google
    if model_id.startswith("gemini-"):
        return ProviderType.GEMINI
    # Mistral models → Mistral
    if model_id.startswith("mistral-"):
        return ProviderType.MISTRAL
    # Llama/Mixtral → Groq (default)
    if model_id.startswith("llama-") or model_id.startswith("mixtral-"):
        return ProviderType.GROQ
    return None
```

---

### Provider Adapters

**File**: `api/providers/adapters/base.py`

```python
from typing import Protocol, AsyncIterator, Optional
from api.providers.config import ProviderType

class ProviderAdapter(Protocol):
    """Protocol for provider adapters."""
    provider: ProviderType
    
    async def complete(
        self,
        *,
        api_key: str,
        model: str,
        messages: list,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> dict:
        """Non-streaming completion. Returns OpenAI-format response."""
        ...
    
    async def stream(
        self,
        *,
        api_key: str,
        model: str,
        messages: list,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> AsyncIterator[dict]:
        """Streaming completion. Yields OpenAI-format chunks."""
        ...
    
    def normalize_error(self, exc: Exception, status_code: Optional[int]) -> tuple[int, str]:
        """Convert provider-specific error to (status_code, user_message)."""
        ...
    
    def supports_model(self, model: str) -> bool:
        """Check if this adapter handles the given model."""
        ...
```

**File**: `api/providers/adapters/openai_compat.py`

```python
import httpx
from typing import Dict, Any, Optional, AsyncIterator
from api.providers.config import ProviderType, get_provider

class OpenAICompatAdapter:
    """Adapter for OpenAI-compatible APIs (OpenAI, Groq, Mistral)."""
    
    def __init__(self, provider: ProviderType):
        self.provider = provider
        self.config = get_provider(provider)
    
    async def complete(
        self,
        *,
        api_key: str,
        model: str,
        messages: list,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> Dict[str, Any]:
        headers = {
            self.config.auth_header: f"{self.config.auth_prefix}{api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            response = await client.post(
                f"{self.config.base_url}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()
    
    async def stream(
        self,
        *,
        api_key: str,
        model: str,
        messages: list,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> AsyncIterator[Dict[str, Any]]:
        headers = {
            self.config.auth_header: f"{self.config.auth_prefix}{api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True
        }
        
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            async with client.stream(
                "POST",
                f"{self.config.base_url}/chat/completions",
                headers=headers,
                json=payload
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]
                        if data.strip() == "[DONE]":
                            break
                        yield json.loads(data)
    
    def normalize_error(self, exc: Exception, status_code: Optional[int]) -> tuple[int, str]:
        if status_code == 401:
            return 401, f"Invalid {self.config.name} API key"
        elif status_code == 403:
            return 403, f"{self.config.name} API key lacks required permissions"
        elif status_code == 429:
            return 429, f"{self.config.name} rate limit exceeded"
        elif status_code == 500:
            return 502, f"{self.config.name} service error"
        return 500, f"Error calling {self.config.name}"
    
    def supports_model(self, model: str) -> bool:
        prefixes = {
            ProviderType.OPENAI: ["gpt-"],
            ProviderType.GROQ: ["llama-", "mixtral-"],
            ProviderType.MISTRAL: ["mistral-"]
        }
        for prefix in prefixes.get(self.provider, []):
            if model.startswith(prefix):
                return True
        return False
```

**File**: `api/providers/adapters/anthropic.py`

```python
import httpx
from typing import Dict, Any, Optional, AsyncIterator
from api.providers.config import ProviderType, get_provider

class AnthropicAdapter:
    """Adapter for Anthropic Claude API."""
    
    provider = ProviderType.ANTHROPIC
    
    def __init__(self):
        self.config = get_provider(ProviderType.ANTHROPIC)
    
    async def complete(
        self,
        *,
        api_key: str,
        model: str,
        messages: list,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> Dict[str, Any]:
        headers = {
            "x-api-key": api_key,
            "anthropic-version": self.config.version_header,
            "Content-Type": "application/json"
        }
        
        # Convert messages format
        system_msg = ""
        anthropic_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                anthropic_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": anthropic_messages
        }
        if system_msg:
            payload["system"] = system_msg
        
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            response = await client.post(
                f"{self.config.base_url}/messages",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
        
        # Normalize to OpenAI format
        return {
            "id": data.get("id", ""),
            "object": "chat.completion",
            "model": model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": data["content"][0]["text"]
                },
                "finish_reason": data.get("stop_reason", "stop")
            }],
            "usage": {
                "prompt_tokens": data.get("usage", {}).get("input_tokens", 0),
                "completion_tokens": data.get("usage", {}).get("output_tokens", 0),
                "total_tokens": data.get("usage", {}).get("input_tokens", 0) + data.get("usage", {}).get("output_tokens", 0)
            }
        }
    
    def normalize_error(self, exc: Exception, status_code: Optional[int]) -> tuple[int, str]:
        if status_code == 401:
            return 401, "Invalid Anthropic API key"
        elif status_code == 403:
            return 403, "Anthropic API key lacks required permissions"
        elif status_code == 429:
            return 429, "Anthropic rate limit exceeded"
        return 500, "Error calling Anthropic"
    
    def supports_model(self, model: str) -> bool:
        return model.startswith("claude-")
```

**File**: `api/providers/adapters/gemini.py`

```python
import httpx
from typing import Dict, Any, Optional
from api.providers.config import ProviderType, get_provider

class GeminiAdapter:
    """Adapter for Google Gemini API."""
    
    provider = ProviderType.GEMINI
    
    def __init__(self):
        self.config = get_provider(ProviderType.GEMINI)
    
    async def complete(
        self,
        *,
        api_key: str,
        model: str,
        messages: list,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> Dict[str, Any]:
        headers = {
            "x-goog-api-key": api_key,
            "Content-Type": "application/json"
        }
        
        # Convert messages to Gemini format
        contents = []
        system_instruction = None
        for msg in messages:
            if msg["role"] == "system":
                system_instruction = msg["content"]
            else:
                role = "user" if msg["role"] == "user" else "model"
                contents.append({
                    "role": role,
                    "parts": [{"text": msg["content"]}]
                })
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens
            }
        }
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}
        
        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            response = await client.post(
                f"{self.config.base_url}/models/{model}:generateContent",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
        
        # Normalize to OpenAI format
        content = ""
        if data.get("candidates"):
            content = data["candidates"][0]["content"]["parts"][0]["text"]
        
        usage_metadata = data.get("usageMetadata", {})
        return {
            "id": f"gemini-{model}",
            "object": "chat.completion",
            "model": model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": usage_metadata.get("promptTokenCount", 0),
                "completion_tokens": usage_metadata.get("candidatesTokenCount", 0),
                "total_tokens": usage_metadata.get("totalTokenCount", 0)
            }
        }
    
    def normalize_error(self, exc: Exception, status_code: Optional[int]) -> tuple[int, str]:
        if status_code == 400:
            return 400, "Invalid request to Gemini API"
        elif status_code == 403:
            return 403, "Gemini API key invalid or lacks permissions"
        elif status_code == 429:
            return 429, "Gemini rate limit exceeded"
        return 500, "Error calling Gemini"
    
    def supports_model(self, model: str) -> bool:
        return model.startswith("gemini-")
```

---

### Provider Router

**File**: `api/providers/router.py`

```python
import asyncio
import uuid
from typing import Dict, Any, Optional
from api.providers.config import ProviderType, get_provider, get_provider_for_model
from api.providers.adapters.openai_compat import OpenAICompatAdapter
from api.providers.adapters.anthropic import AnthropicAdapter
from api.providers.adapters.gemini import GeminiAdapter
from api.services.redis_storage import storage

# Initialize adapters
ADAPTERS = {
    ProviderType.GROQ: OpenAICompatAdapter(ProviderType.GROQ),
    ProviderType.OPENAI: OpenAICompatAdapter(ProviderType.OPENAI),
    ProviderType.MISTRAL: OpenAICompatAdapter(ProviderType.MISTRAL),
    ProviderType.ANTHROPIC: AnthropicAdapter(),
    ProviderType.GEMINI: GeminiAdapter(),
}

class ProviderRouter:
    """Routes chat completion requests to the appropriate AI provider."""
    
    def resolve_provider(
        self,
        model: str,
        header_override: Optional[str] = None,
        user_default: Optional[str] = None
    ) -> ProviderType:
        """
        Resolve which provider to use.
        
        Priority:
        1. Explicit header override (X-AiAssist-Provider)
        2. Model name inference
        3. User's default provider
        4. Platform default (Groq)
        """
        if header_override:
            try:
                return ProviderType(header_override)
            except ValueError:
                pass
        
        inferred = get_provider_for_model(model)
        if inferred:
            return inferred
        
        if user_default:
            try:
                return ProviderType(user_default)
            except ValueError:
                pass
        
        return ProviderType.GROQ
    
    def get_api_key(
        self,
        user_id: str,
        provider: ProviderType,
        user_plan: str
    ) -> tuple[str, bool]:
        """
        Get API key for request.
        
        Returns (api_key, is_byok).
        Falls back to platform Groq if no BYOK and plan allows.
        """
        import os
        
        # Try user's BYOK first
        cred = storage.get_provider_credential_with_key(user_id, provider.value)
        if cred:
            return cred[1], True
        
        # No BYOK - check platform fallback
        if provider == ProviderType.GROQ:
            platform_key = os.environ.get("GROQ_API_KEY")
            if platform_key:
                return platform_key, False
        
        # For other providers, user must have BYOK
        raise ValueError(
            f"No API key configured for {provider.value}. "
            f"Add your {get_provider(provider).name} key in the dashboard."
        )
    
    async def route_completion(
        self,
        user_id: str,
        model: str,
        messages: list,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        header_override: Optional[str] = None,
        user_plan: str = "free"
    ) -> Dict[str, Any]:
        """Route a chat completion request to the appropriate provider."""
        # Get user's default provider
        user_default = storage.get_user_preferred_provider(user_id)
        
        # Resolve provider
        provider = self.resolve_provider(model, header_override, user_default)
        
        # Get API key
        api_key, is_byok = self.get_api_key(user_id, provider, user_plan)
        
        # Get adapter
        adapter = ADAPTERS[provider]
        
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        try:
            # Call with retry
            response = await self._call_with_retry(
                adapter, api_key, model, messages, temperature, max_tokens
            )
            
            # Add our metadata
            response["_aiassist"] = {
                "request_id": request_id,
                "provider": provider.value,
                "using_byok": is_byok
            }
            
            return response
            
        except Exception as e:
            # Handle BYOK key failure
            if is_byok:
                status_code = getattr(e, "response", None)
                if status_code:
                    status_code = status_code.status_code
                
                if status_code in (401, 403):
                    # Mark credential as invalid
                    storage.update_provider_credential_status(
                        user_id, provider.value, "invalid"
                    )
                
                code, message = adapter.normalize_error(e, status_code)
                raise ValueError(message)
            raise
    
    async def _call_with_retry(
        self,
        adapter,
        api_key: str,
        model: str,
        messages: list,
        temperature: float,
        max_tokens: int
    ) -> Dict[str, Any]:
        """Call adapter with one retry on 429/503."""
        import httpx
        
        for attempt in range(2):
            try:
                return await adapter.complete(
                    api_key=api_key,
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            except httpx.HTTPStatusError as e:
                if e.response.status_code in (429, 503) and attempt == 0:
                    await asyncio.sleep(1.0)
                    continue
                raise

router = ProviderRouter()
```

---

## API Endpoints

### New Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/providers` | List all supported providers with models (cached, refreshed periodically) |
| GET | `/api/user/providers` | Get user's configured providers |
| POST | `/api/user/providers/{provider}` | Add/update API key for provider |
| DELETE | `/api/user/providers/{provider}` | Remove API key for provider |
| PUT | `/api/user/providers/default` | Set default provider |

### Modified Endpoints

| Method | Path | Changes |
|--------|------|---------|
| POST | `/v1/chat/completions` | Add `X-AiAssist-Provider` header support, route to multiple providers |

### Request Headers

| Header | Description | Required |
|--------|-------------|----------|
| `Authorization` | `Bearer {aai_api_key}` | Yes |
| `X-AiAssist-Provider` | Force specific provider: `openai\|anthropic\|gemini\|mistral\|groq` | No |
| `X-AiAssist-Byok` | `true\|false` for metrics | No |

---

## Frontend Changes

### Provider Settings Component

**File**: `client/src/components/ProviderSettings.tsx`

A new component that:
1. Shows all available providers in a grid
2. Indicates which providers have API keys configured
3. Allows adding/removing keys per provider
4. Lets user select a preferred default provider
5. Shows provider health status badges

```
┌─────────────────────────────────────────────────────────────────┐
│ AI Provider Configuration                                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │    GROQ      │  │   OpenAI     │  │  Anthropic   │           │
│  │   ✓ Active   │  │   + Add Key  │  │   + Add Key  │           │
│  │  [Default]   │  │              │  │              │           │
│  │   ● Healthy  │  │              │  │              │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐                             │
│  │   Gemini     │  │   Mistral    │                             │
│  │   + Add Key  │  │   + Add Key  │                             │
│  └──────────────┘  └──────────────┘                             │
│                                                                  │
│  Default Provider: [Groq ▼]                                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Updated Walkthrough

**File**: `client/src/components/ProviderSetupWalkthrough.tsx`

Generalize `GroqSetupWalkthrough` to:
1. Accept provider type as prop
2. Show provider-specific console URLs
3. Display provider logo/branding
4. Update messaging to be provider-agnostic

---

## Implementation Checklist

### Backend (Phase 1)

- [ ] Create `api/providers/` directory structure
- [ ] Implement `config.py` with provider configs (treat models as defaults)
- [ ] Create adapter base protocol
- [ ] Implement `OpenAICompatAdapter` (Groq, OpenAI, Mistral)
- [ ] Implement `AnthropicAdapter`
- [ ] Implement `GeminiAdapter`
- [ ] Implement `ProviderRouter` with:
  - [ ] Provider resolution (header → model → default → Groq)
  - [ ] BYOK fallback to platform Groq
  - [ ] Retry logic (one retry on 429/503)
  - [ ] Error normalization
- [ ] Add `X-AiAssist-Provider` header support
- [ ] Create `GET /api/providers` endpoint with caching
- [ ] Create user provider CRUD endpoints
- [ ] Update usage recording with provider dimensions
- [ ] Add provider health tracking in Redis

### Frontend (Phase 2)

- [ ] Create `ProviderSettings.tsx` component
- [ ] Generalize walkthrough to `ProviderSetupWalkthrough.tsx`
- [ ] Add provider section to Dashboard
- [ ] Add provider health badges
- [ ] Update API key management UI

### Testing (Phase 3)

- [ ] Test each provider adapter
- [ ] Test fallback scenarios
- [ ] Test error handling per provider
- [ ] Test usage recording accuracy
- [ ] Load test with mixed providers

---

## Estimated Timeline

| Phase | Tasks | Hours |
|-------|-------|-------|
| Phase 1 | Backend provider infrastructure | 6-8 |
| Phase 2 | Frontend provider UI | 4-5 |
| Phase 3 | Testing & polish | 3-4 |
| **Total** | | **13-17 hours** |

---

## Notes

- BYOK users get unrestricted model access (no plan-based model limits)
- Platform users (using our Groq key) follow plan-based model restrictions
- Internal workspace chat continues to use platform Groq only
- This plan incorporates all Oracle recommendations for production readiness
