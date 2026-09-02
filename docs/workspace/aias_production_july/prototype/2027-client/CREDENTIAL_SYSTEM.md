# Credential System — 2027 Client (Credential-Aware)

> Every request carries a visible, auditable, swappable passport. No silent fallback.

---

## 1. The Leak We Fix

Current march_2026:

- `X-AiAssist-Provider` MUST be sent ALWAYS (Mark's rule) but hidden in lib — easy to miss → provider defaults to PIN unexpectedly
- Three key types `aai_` (standard), `aai_pub_` (publishable), `aai_srv_` (service) with scopes `chat:completion workspace:* contacts:* agents:* billing:*` + domain restrictions + usage limits + IP allowlists stored in `users.py` + `redis_storage.py` but no UI to surface
- BYOK multi-key per provider `primary/backup` + `preferred provider` + `model preferences` + `provider priority` — buried in `ProviderSettings 73k` component
- Dual transport: same-origin cookie `session_id` + cross-origin `X-Session-Token` header for Keystone Lite windowed apps — nobody knows both exist
- Bearer `aai_xxx` for `/api/keystone` + `/v1/` + `/embed/` vs cookie for `/api/*` private — CORS PathBased critical but invisible
- PIN credit-based vs BYOK key resolution — `pin_get_user_billing credits_balance <=0 → insufficient` error hits as generic 500
- Models cache 5min Groq dynamic fetch filter whisper/tts/guard/vision/preview, priority sort llama-3.3>3.1>mixtral>gemma>qwen>deepseek — not displayed

2027: Credential Passport

---

## 2. CredentialPassport Model

```ts
type KeyType = "aai_" | "aai_pub_" | "aai_srv_"
type KeyScope = "chat:completion" | "workspace:*" | "contacts:*" | "agents:*" | "billing:*" | "*"

interface ApiKeyRecord {
  id: string
  key_type: KeyType
  masked: string // aai_****_abcd
  name: string
  scopes: KeyScope[]
  domain_restrictions?: string[] // allowed origins
  ip_allowlist?: string[]
  usage_limit?: number // monthly tokens or req count
  usage_used: number
  created_at: string
  last_used?: string
  expires_at?: string
  rate_limit: { rpm: number, monthly_tokens: number } // per PLAN_LIMITS free 10 rpm etc
  models_allowed?: string[] // PLAN_LIMITS free ["llama-3.3-70b-versatile"] etc
}

interface ByokProviderKeys {
  provider: ProviderType // groq | openai | anthropic | gemini | mistral | xai | together | openrouter | deepseek | fireworks | perplexity | pin
  keys: Array<{
    masked: string
    role: "primary" | "backup"
    last_tested: string
    ok: boolean
    tokens_used_today?: number
  }>
  preferred_model?: string
  model_preferences?: string[]
  priority: number // drag to reorder in ProviderRouter
  api_mode?: "ollama" | "openai" // PIN only
  region?: "us-east" | "us-west" | "eu-west" | "eu-central" | "asia-pacific" | "global"
  price_per_1k?: number // PIN operator sets 0.05-0.50
}

interface HeaderContract {
  "X-AiAssist-Provider": string // ALWAYS — header_override in router.resolve_provider
  "X-AiAssist-Byok"?: string // optional raw key override — bypasses stored BYOK
  "X-Agent-Id"?: string // deployed-agent-id
  "X-Session-Token"?: string // cross-origin Keystone Lite windowed apps, same as cookie session_id 7d expiry
  "Authorization": string // Bearer aai_xxx | session fallback
  "X-API-Key"?: string // alternative to Bearer
}

interface CredentialPassport {
  active_key: ApiKeyRecord
  byok: Record<ProviderType, ByokProviderKeys>
  headers: HeaderContract
  resolution: {
    order: ["header_override", "model_inference", "user_default", "pin_fallback"]
    resolved_provider: ProviderType
    resolved_model: string
    is_byok: boolean
    is_credit_based: boolean // PIN
    credit_balance?: number // PIN
  }
  plan: PlanType // free | basic | pro | enterprise
  plan_limits: { rpm: number, monthly_tokens: number, api_keys: number, models: string[] }
}
```

---

## 3. Header Contract (Mark's Rule)

```ts
// ProviderRouter.resolve_provider
function resolve(header_override?: string, model?: string, user_default?: string): ProviderType {
  if (header_override) return ProviderType(header_override) // X-AiAssist-Provider wins
  const inferred = get_provider_for_model(model) // claude* → anthropic, gpt* → openai etc
  if (inferred) return inferred
  if (user_default) return ProviderType(user_default)
  return ProviderType.PIN // final fallback
}

function get_api_key(user_id, provider): [key, is_byok] {
  if (provider.is_credit_based) {
    const billing = pin_get_user_billing(user_id)
    if (!billing || billing.credits_balance <=0) throw "Insufficient PIN credits"
    return [user_id, false] // credit-based not BYOK
  }
  const cred = get_provider_credential_with_key(user_id, provider)
  if (cred) return [cred[1], true]
  throw `No API key for ${provider}`
}
```

2027 client:

- Always sends `X-AiAssist-Provider` — shown as pill in vault drawer, mem warning if missing
- Sends `X-AiAssist-Byok` only if user explicitly overrides in vault (raw key field)
- Sends `X-Agent-Id` only when deployed agent active
- Sends `X-Session-Token` when cross-origin (Keystone Lite windowed app) — detected via `window !== window.top` or `isMobileContext`
- Sends `Authorization: Bearer aai_xxx` for `/v1/` + `/api/keystone` + `/api/embed/`; cookie `session_id` for `/api/*` private; `X-API-Key` alternative

No silent PIN fallback — vault shows resolved provider + is_credit_based + credit_balance + why (header_override | inference | default | pin_fallback)

---

## 4. Vault Drawer UI

```
┌─ Credential Vault ─────────────────────────────┐
│ Active key: My Prod Key [aai_srv_] ● primary   │
│ Scopes: chat:completion workspace:* agents:* ✓  │
│ Domain: *.aiassist.net, localhost              │
│ IP: 31.220.96.225/32 allowlisted                │
│ Usage: 42,191 / 100,000 tokens (42%) [████▒▒]  │
│ RPM: 10 / 300 (free vs pro) limit              │
│ Models: llama-3.3-70b-versatile only (free) →  │
│ Upgrade bar: free 0 envs → pro 5 envs          │
│ Last used: 2m ago • Created 2026-06-01         │
├─ BYOK Providers (drag to priority) ────────────┤
│ [groq] primary sk-****abcd ✓ tested 1m ago     │
│        backup  sk-****efgh ⏳ not tested        │
│        preferred: llama-3.3-70b-versatile      │
│        models: compound, 3.1 8b, 3.3 70b, etc   │
│ [openai] primary ••••                         │
│ [anthropic] primary ••••                       │
│ [gemini] ...                                   │
│ [PIN] credits: 1,240 / 10,000 (12%)             │
│       price slider 0.05-0.50/1K $0.12 current   │
│       region: us-east ▼ interview tier         │
│       verified >90% 20tok/s ● green             │
│ Headers: X-Provider: groq ALWAYS ●             │
│          X-Byok: (none) + override button      │
│          X-Agent-Id: (none)                    │
│          X-Session-Token: 7d expiry 2026-07-21  │
│ Resolution: header_override → groq → BYOK ✓    │
└────────────────────────────────────────────────┘
```

- Masked keys click to reveal (copy + audit log)
- Test button calls `GET /v1/models` with header override to verify key
- Primary/backup toggle per provider
- Priority drag list maps to `provider priority` in `users.py`
- Domain restrictions + IP allowlist editable with SSRF guard same as custom_tools (BLOCKED_HOSTS)
- Scopes checkboxes with capability preview (team.view etc)
- Upgrade nudges: free 10 rpm → pro 300 rpm bar

---

## 5. Security

- Keys never in localStorage raw — only masked + session_id cookie HTTP-only + X-Session-Token header 7d expiry from `auth.py`
- BYOK keys stored server-side `user_providers:{user_id}` Redis, never client-side in `workspaces` anon 20/hr rate limit bypass risk
- `X-AiAssist-Byok` raw override only in-memory, not persisted, shows warning "ephemeral, not stored"
- TOTP 2FA gate for key reveal (TOTP 6-digit + backup codes from `users.py`)
- Audit log per key: created_at, last_used, IP, User-Agent (from SessionActivity)
- PIN operator HMAC `HMAC-SHA256(client_id + timestamp, api_secret)` 5min window — not in vault, separate WS auth

---

## 6. Implementation Notes

- `src/lib/api-client.ts` — wrapper around `apiRequest` from `lib/queryClient.ts` + `api.ts` Portal lib, but with CredentialPassport always injected
- Handles 401 Invalid or revoked API key (from `get_api_key_by_secret` false random funny error messages) → vault shows red + re-auth flow
- Handles 402 require_paid_plan → upgrade modal (useUpgradeModal per `use-available-models.ts`)
- Handles 403 plan gated + 403 env limit (ENV_LIMITS) → vault + env deck limit meter
- Handles 409 env binding mismatch → auto destroy-recreate-retry (see ENVIRONMENT_SYSTEM.md)
- Handles 429 too many requests → queue metrics wait_ms exec_ms + QueueMiddleware full error

See ARCHITECTURE.md §2.1 + app/index.html vault drawer interactive.
