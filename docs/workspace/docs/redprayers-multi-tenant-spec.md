# redPrayers Multi-Tenant SaaS Specification

**Version:** 3.0
**Date:** February 2026
**Status:** Phase 1–7 Implemented, tenant_zero fully eliminated
**Brand:** saas-signal.com (HQ) → redPrayers (product)

---

## 1. Vision

redPrayers is a multi-tenant lead intelligence SaaS product. AiAssist Secure (AiAS) is the unified auth and infrastructure hub. Users register/login at **saas-signal.com**, get redirected to the **AiAS dashboard** to obtain their API key, then connect redPrayers using that key.

Every tenant gets strict data isolation: settings, contacts, dispatch rules, ambassadors, scan history, invite codes, and team chat. All data is scoped to `org:{org_id}:radar:*` Redis keys. There is no default org, no fallback org, and no shared namespace — services fail fast if org_id is missing.

---

## 2. Architecture

### Backend
- **Entry:** FastAPI API server (`saas-signal/api/main.py`)
- **Auth:** AiAS API key validation only (`aai_` prefix, validated via AiAS `/v1/organization` endpoint, cached 15min in Redis)
- **Routes:**
  - `/api/auth/validate` + `/api/auth/check` + `/api/auth/me` — API key auth
  - `/api/settings/*` — CRUD for all config (Reddit, Telegram, AiAS, Netrows, ScrapingDog, presets, auto-scan)
  - `/api/radar/*` — scan sources (22+ platforms), streaming SSE, intent analysis, keyword generation, lead chat, outreach
  - `/api/contacts/*` — pipeline contacts, discovered leads, status management
  - `/api/radar/dispatch/*` — ambassador management, invite codes, LeadPacket generation, Telegram dispatch, webhooks, activity log
  - `/api/team-chat/*` — org-scoped team messaging

### Frontend
- **Framework:** React + TypeScript + Vite + Tailwind + Framer Motion
- **Auth UI:** `AuthGate.tsx` — AiAS API key input only
- **Settings UI:** `SettingsModal.tsx` — tabs for Telegram, Reddit, AiAS, Netrows, Keywords, Auto-Scan
- **Core UI:** Dual layout (Mobile + Desktop) with Radar, Discover, Pipeline (Kanban), Team Chat, Activity Log, Agent Mode
- **API Client:** `ui/src/lib/api.ts` — `authFetch` wrapper with Bearer token injection, 401 interceptor

### Storage
- **Engine:** `StorageService` class (Redis-backed, org_id required)
- **Key Pattern:** `org:{org_id}:radar:*` — all data strictly org-scoped
- **Global Keys:** `invite:{code}`, `dispatch:lookup:{dispatch_id}`, `bot:pending_invite:{chat_id}`, `auth:cache:{key_hash}`

---

## 3. Multi-Tenant Data Isolation

### 3.1 Enforcement Rules

1. **StorageService** — `__init__` raises `ValueError` if `org_id` is empty/None
2. **AiasService** — `__init__` raises `ValueError` if `org_id` is empty/None
3. **ScrapingDogService** — `__init__` raises `ValueError` if `org_id` is empty/None
4. **DispatchBotService** — `org_id` allowed empty only for the global webhook handler (it only needs the bot token to answer Telegram callbacks, never touches storage directly)
5. **All route handlers** — receive `org_id` via `auth["org_id"]` from `Depends(validate_aias_key)`
6. **No defaults** — no service accepts a default org_id; callers must always provide one explicitly

### 3.2 Auth Flow

```
User                    saas-signal.com           AiAS Backend           redPrayers
  │                          │                        │                      │
  │── Visit LP ─────────────▶│                        │                      │
  │── Click Register ───────▶│── Redirect ───────────▶│                      │
  │                          │                        │── Create user + org  │
  │── View Dashboard ────────────────────────────────▶│                      │
  │── Copy API Key (aai_xxx) ─────────────────────────│                      │
  │── Open redPrayers ───────────────────────────────────────────────────────▶│
  │── Enter API Key ─────────────────────────────────────────────────────────▶│
  │                          │                        │◀── Validate key ─────│
  │                          │                        │    GET /v1/organization
  │                          │                        │    (Bearer aai_xxx)  │
  │                          │                        │── Return org_id ────▶│
  │◀── Authenticated (org-scoped) ───────────────────────────────────────────│
```

**Key Points:**
- No separate redPrayers auth system
- AiAS API key (`aai_` prefix) is the sole credential, sent as `Bearer` token
- API key validated against AiAS `/v1/organization` — result cached in Redis for 15 minutes (`auth:cache:{key_hash}`)
- Organization ID extracted from validated key determines tenant scope
- On 401 from AiAS, cache entry purged immediately

### 3.3 Auth Implementation

**Backend Middleware (`saas-signal/api/middleware/auth.py`):**
```python
async def validate_aias_key(request: Request) -> dict:
    api_key = extract_bearer_token(request)
    if not api_key:
        raise HTTPException(401, "Missing Authorization header")
    if not api_key.startswith("aai_"):
        raise HTTPException(401, "Invalid token format")
    return await _validate_api_key(api_key)
```

Returns:
```python
{
    "user_id": str,
    "org_id": str,       # from AiAS organization_id
    "role": str,         # admin | ambassador | client
    "plan": str,         # free | basic | pro | enterprise
    "username": str,
    "api_key": str,
    "auth_type": "aias"
}
```

**Org Resolution:** Auth middleware calls AiAS `/v1/organization` endpoint (not `/api/auth/me`) to get the real `organization_id`. This ensures org_id always matches the AiAS org record — no user_id fallback.

### 3.4 Org-Scoped Storage

**Redis Key Namespace:**

| Data | Key Pattern |
|------|-------------|
| All settings | `org:{org_id}:radar:settings` |
| Locked contacts (pipeline) | `org:{org_id}:radar:contacts` |
| Discovered leads | `org:{org_id}:radar:discovered:*` |
| Ambassador profiles | `org:{org_id}:radar:ambassadors:{chat_id}` |
| Ambassador list | `org:{org_id}:radar:ambassadors:list` |
| Dispatch records | `org:{org_id}:radar:dispatch:{dispatch_id}` |
| Dispatch indexes | `org:{org_id}:radar:dispatch:lead:{id}` |
| Lead packets | `org:{org_id}:radar:lead_packet:{id}:{hash}` |
| Scanned post cache | `org:{org_id}:radar:scanned_posts` |
| Team chat messages | `org:{org_id}:radar:team_chat` |
| Team chat usernames | `org:{org_id}:radar:usernames:{ip_hash}` |
| Netrows usage | `org:{org_id}:radar:netrows:usage:{month}` |
| ScrapingDog usage | `org:{org_id}:radar:scrapingdog:usage:{month}` |
| Invite codes (org index) | `org:{org_id}:radar:invites` |

**Global Keys (not org-scoped):**

| Key | Purpose |
|-----|---------|
| `invite:{code}` | Invite code → org_id mapping (for ambassador registration) |
| `dispatch:lookup:{dispatch_id}` | Dispatch → org_id mapping (for webhook routing) |
| `bot:pending_invite:{chat_id}` | Temporary flag while ambassador is entering invite code (600s TTL) |
| `auth:cache:{key_hash}` | Cached auth validation result (900s TTL) |

---

## 4. Ambassador Invite Code System

### 4.1 Problem
The Telegram bot is shared across all orgs. When an ambassador sends `/start`, the bot doesn't know which org to register them under. Exposing `org_id` in deep links is a security risk.

### 4.2 Solution: Invite Codes
Org admins generate short 8-character alphanumeric invite codes. Ambassadors use these to register via the bot.

### 4.3 Flow

**Admin generates invite code:**
```
POST /api/radar/dispatch/invites/generate
Body: { "label": "RedPrayers Q1" }  // optional label
Response: { "success": true, "invite": { "code": "K7X2M9PL", "org_id": "...", "label": "RedPrayers Q1", "uses": 0 } }
```

**Ambassador registers via Telegram bot:**
```
Ambassador: /start
Bot: 👋 Welcome! To join as an ambassador, please send me your invite code.
Ambassador: K7X2M9PL
Bot: 🔥 Yo @username, you're in for RedPrayers Q1! ...
```

**Ambassador joins additional orgs:**
```
Ambassador: /register
Bot: 🔗 Got another invite code? Send it now and I'll add you to that project too.
Ambassador: AB3FGH12
Bot: 🔥 Yo @username, you're in for ProjectX! ...
```

**Re-registration (same org):**
If an ambassador enters an invite code for an org they're already in, the bot tells them they're already registered and refreshes their info.

### 4.4 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/radar/dispatch/invites/generate` | POST | Generate new invite code (auth required) |
| `/api/radar/dispatch/invites` | GET | List org's invite codes with use counts (auth required) |
| `/api/radar/dispatch/invites/{code}` | DELETE | Revoke an invite code (auth required) |

### 4.5 Storage

| Key | Type | TTL | Purpose |
|-----|------|-----|---------|
| `invite:{code}` | String (JSON) | None | Maps code → `{ code, org_id, label, created_at, uses }` |
| `org:{org_id}:radar:invites` | Set | None | Set of codes belonging to this org (for listing/cleanup) |
| `bot:pending_invite:{chat_id}` | String | 600s | Flag indicating bot is waiting for this user's invite code |

### 4.6 Multi-Org Ambassadors
- Same Telegram `chat_id` can be registered under multiple orgs
- Each org has its own ambassador record: `org:A:radar:ambassadors:123` vs `org:B:radar:ambassadors:123`
- Stats (total_dispatches, total_won) tracked independently per org
- No conflict — ambassadors can work for multiple projects simultaneously

---

## 5. Telegram Webhook & Dispatch Routing

### 5.1 Problem
The Telegram webhook receives callbacks (Interested/Pass/Won button taps) globally. We need to route each callback to the correct org.

### 5.2 Solution: Dispatch Lookup Index
When a dispatch is created, a global lookup key is written:
```
dispatch:lookup:{dispatch_id} → org_id  (90-day TTL)
```

### 5.3 Webhook Flow
```python
# 1. Parse callback data → extract dispatch_id
# 2. Look up org_id from global index
dispatch_org_id = redis.get(f"dispatch:lookup:{dispatch_id}")
if not dispatch_org_id:
    answer_callback("Dispatch not found")
    return

# 3. Load dispatch from org-scoped storage
storage = StorageService(org_id=dispatch_org_id)
dispatch = storage.get_dispatch(dispatch_id)

# 4. Use org-specific bot for responses
bot = DispatchBotService.from_org_settings(dispatch_org_id)
```

### 5.4 Bot Commands

| Command | Handler | Purpose |
|---------|---------|---------|
| `/start` | Sets pending_invite, asks for invite code | First-time ambassador onboarding |
| `/register` | Sets pending_invite, asks for invite code | Join additional orgs |
| _(any text while pending)_ | Validates invite code, registers ambassador | Complete registration |

---

## 6. Service Architecture

### 6.1 Service Constructors (all require org_id)

| Service | org_id Behavior | Notes |
|---------|----------------|-------|
| `StorageService(org_id)` | Required, raises ValueError if empty | All Redis operations scoped |
| `AiasService(org_id)` | Required, raises ValueError if empty | Reads LLM config from org settings |
| `ScrapingDogService(org_id=, api_key=)` | Required, raises ValueError if empty | Reads limits from org settings |
| `DispatchBotService(org_id=, bot_token=)` | Optional (empty for global webhook bot) | Per-org via `from_org_settings()` |

### 6.2 Route → Service Flow
```python
@router.get("/settings/")
async def get_settings(auth: dict = Depends(validate_aias_key)):
    storage = StorageService(org_id=auth["org_id"])  # fails if org_id missing
    return storage.get_settings()
```

### 6.3 Updated Routes

| File | Routes | Notes |
|------|--------|-------|
| `routes/auth.py` | validate, check, me | API-key-only auth |
| `routes/settings.py` | 10 handlers | All CRUD settings endpoints |
| `routes/contacts.py` | 10 handlers | Pipeline + discovered leads |
| `routes/team_chat.py` | 5 handlers | Messages + usernames |
| `routes/radar.py` | All handlers | Scan, stream, intent, keywords, outreach |
| `routes/dispatch.py` | All handlers | Invites, ambassadors, dispatch, webhook |

---

## 7. Data Isolation Guarantees

1. **Storage:** Every Redis key prefixed with `org:{org_id}:` — services raise ValueError if org_id is empty
2. **API:** Auth middleware extracts org_id from AiAS `/v1/organization` before any storage access
3. **Services:** Each org's AiAS/Netrows/ScrapingDog keys used for that org's scans only
4. **Telegram Bot:** Per-org bot tokens via `from_org_settings(org_id)` with env-var fallback
5. **Webhook:** Uses `dispatch:lookup:{dispatch_id}` global index to route callbacks to correct org
6. **Ambassador Registration:** Via invite codes — org_id never exposed to ambassadors
7. **Scan Cache:** Scanned post dedup is per-org
8. **Team Chat:** Messages isolated per-org
9. **No defaults:** No service has a default org_id — no "tenant_zero", no empty string namespace

---

## 8. Completed Phases

### Phase 1: Auth Swap ✅
- AiAS API key validation via `/v1/organization` endpoint
- Redis cache (15min TTL) for validated keys
- Bearer-only auth — non-`aai_` tokens rejected with 401
- Frontend `authFetch` wrapper with 401 interceptor

### Phase 2: Org-Scoped Storage ✅
- All Redis keys use `org:{org_id}:radar:*` prefix
- StorageService requires explicit org_id (no defaults)
- All route handlers pass `auth["org_id"]` to services

### Phase 3: Migration Scripts ✅
- `scripts/backup_redis.py` — BGSAVE + JSON export
- `scripts/migrate_tenant_zero.py` — renames `org:tenant_zero:radar:*` → `org:{real_org_id}:radar:*`
- `scripts/prewarm_migration.py` — API verification post-migration
- `scripts/cleanup_legacy.py` — removes old keys after verification

### Phase 4: Legacy Cleanup ✅
- Removed `x-access-code` header support
- Removed all legacy key fallback helpers
- Removed `_legacy_key`, `_get_with_fallback`, `_list_with_migration`, `_set_with_migration`
- Tightened auth to API-key-only

### Phase 5: Per-Org Infrastructure ✅
- Per-org Telegram bot tokens via `from_org_settings()`
- Per-org ScrapingDog config
- Webhook routing via dispatch record's org_id field

### Phase 6: tenant_zero Elimination ✅
- Removed ALL `tenant_zero` references from application code (services, routes, middleware, frontend)
- Auth resolves real org_id via AiAS `/v1/organization` endpoint
- All services raise ValueError on empty org_id
- Data migrated from `org:tenant_zero:radar:*` to `org:{real_org_id}:radar:*`
- `REDPRAYERS_DEFAULT_ORG` env var removed

### Phase 7: Ambassador Invite System ✅
- Invite code generation, listing, revocation API
- Bot `/start` flow: asks for invite code, validates, registers under correct org
- Bot `/register` command: join additional orgs with new invite codes
- Re-registration detection (already registered → info refresh)
- Invite label displayed in welcome message
- `dispatch:lookup:{dispatch_id}` global index for webhook routing
- `scripts/backfill_dispatch_lookup.py` for existing dispatches

---

## 9. Migration History

### From redProxit (single-tenant) to saas-signal (multi-tenant)
1. Redis key namespace: `redproxit:*` → `org:tenant_zero:radar:*` (Phase 2–3)
2. Auth: access code → AiAS API key (Phase 1, 4)
3. tenant_zero elimination: `org:tenant_zero:radar:*` → `org:{real_org_id}:radar:*` (Phase 6)

### Migration Scripts (run in order on VPS)
| Script | Purpose | Idempotent |
|--------|---------|------------|
| `scripts/backup_redis.py` | BGSAVE + JSON export | Yes |
| `scripts/migrate_tenant_zero.py` | Rename tenant_zero keys to real org_id | Yes (skips existing) |
| `scripts/backfill_dispatch_lookup.py` | Create dispatch:lookup keys for existing dispatches | Yes (skips existing) |
| `scripts/cleanup_legacy.py` | Remove old `redproxit:*` keys | Yes (dry-run default) |

---

## 10. Environment Variables

### Required (Infrastructure)
| Variable | Purpose |
|----------|---------|
| `REDIS_URL` | Redis connection string (shared across tenants) |
| `AIAS_BASE_URL` | AiAS API endpoint for key validation |
| `TELEGRAM_BOT_TOKEN` | Default bot token (fallback when org has no custom bot) |

### Removed
| Variable | Reason |
|----------|--------|
| `REDPROXIT_ACCESS_CODE` | Replaced by AiAS API key auth |
| `REDPROXIT_AMBASSADOR_CODE` | Replaced by invite code system |
| `REDPRAYERS_DEFAULT_ORG` | No default org — services require explicit org_id |

---

## 11. Implementation Files

### Backend (saas-signal/api/)
| File | Purpose |
|------|---------|
| `main.py` | FastAPI app entry point, webhook registration |
| `middleware/auth.py` | AiAS key validation, Redis cache, org resolution via `/v1/organization` |
| `services/storage_service.py` | Org-scoped Redis storage, invite code management, pending invite state |
| `services/aias_service.py` | AiAS LLM integration (org-scoped) |
| `services/scrapingdog_service.py` | ScrapingDog/LinkedIn/Twitter/Indeed/News scraping (org-scoped) |
| `services/dispatch_bot_service.py` | Telegram dispatch bot, `/start` + `/register` handlers, invite code flow |
| `routes/auth.py` | Auth endpoints (validate, me, check) |
| `routes/settings.py` | Settings CRUD (org-scoped) |
| `routes/contacts.py` | Pipeline + discovered leads (org-scoped) |
| `routes/team_chat.py` | Team messaging (org-scoped) |
| `routes/radar.py` | Scan, stream, intent analysis (org-scoped) |
| `routes/dispatch.py` | Invite codes, ambassadors, dispatch, webhook routing |

### Frontend (saas-signal/ui/src/)
| File | Purpose |
|------|---------|
| `App.tsx` | Auth flow, logout, org_id display |
| `components/AuthGate.tsx` | API key auth UI |
| `components/SettingsModal.tsx` | Per-org settings including Telegram bot token |
| `components/ActivityLog.tsx` | Dispatch activity log with auth headers |
| `components/ContactsKanban.tsx` | Pipeline kanban board |
| `components/DiscoveredLeads.tsx` | Discovered leads view |
| `lib/api.ts` | authFetch wrapper, Bearer injection, 401 handling |

### Scripts (saas-signal/scripts/)
| Script | Purpose |
|--------|---------|
| `backup_redis.py` | BGSAVE + JSON export |
| `migrate_tenant_zero.py` | Rename tenant_zero keys to real org namespace |
| `backfill_dispatch_lookup.py` | Create global dispatch lookup keys for webhook routing |
| `cleanup_legacy.py` | Remove old `redproxit:*` keys |

---

## 12. Success Criteria

- [x] All services reject empty org_id (ValueError) — no silent shared namespace
- [x] Auth resolves real org_id via AiAS `/v1/organization` — no tenant_zero fallback
- [x] Data fully migrated from tenant_zero to real org namespace
- [x] Webhook routes Telegram callbacks to correct org via dispatch:lookup index
- [x] Ambassador registration via invite codes — org_id never exposed
- [x] Ambassadors can register for multiple orgs via `/register` command
- [x] Per-org Telegram bot tokens with env-var fallback
- [x] Settings changes in one org do not affect another org
- [x] Frontend handles 401 gracefully (clears session, redirects to auth)
- [ ] New user can register at saas-signal.com, get API key from AiAS, and use redPrayers within 5 minutes
- [ ] Two tenants operating simultaneously with zero data leakage (needs production testing)
- [ ] saas-signal.com landing page live with registration flow

---

## 13. Remaining Work

### saas-signal.com Landing Page
- [ ] Design and build landing page
- [ ] Registration form → AiAS auth
- [ ] Login form → AiAS auth → redirect to dashboard
- [ ] Docs/walkthrough content
- [ ] Domain setup

### Production Hardening
- [ ] Run `backfill_dispatch_lookup.py` on VPS
- [ ] Multi-tenant smoke test (two orgs simultaneously)
- [ ] Rate limiting on invite code generation
- [ ] Invite code expiration (optional)
