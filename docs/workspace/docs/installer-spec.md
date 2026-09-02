# AiAS Self-Hosted Installer Specification

## Overview

A professional PHP-based installation wizard for self-hosted AiAS deployments. The installer provides a polished, multi-step setup experience that configures all system-wide settings without requiring manual file editing.

**Target Users:** Agencies deploying AiAS for their clients

**Deployment Model:** Upload files → Visit URL → Follow wizard → Done

**Distribution Model:** Two-tier package delivery
- **Public Shell:** Installer, frontend, basic structure (ships with purchase)
- **Proprietary Core:** AI services, business logic (delivered after license verification)

---

## Design Goals

1. **Zero-friction setup** - Upload files, visit URL, follow wizard
2. **Professional aesthetics** - Modern UI with dark/light mode, smooth animations
3. **Complete configuration** - Expose all hardcoded system settings
4. **Validation** - Test connections before saving
5. **Security** - Generate secrets, validate inputs, lock after install

---

## Visual Design

### Theme
- Dark mode default with light mode toggle
- Accent color: Brand purple (#8B5CF6) or user-selectable
- Clean typography (Inter or system fonts)
- Subtle animations on step transitions
- Progress indicator showing completion

### Components
- Card-based layout for each configuration section
- Toggle switches for boolean settings
- Number inputs with increment/decrement for limits
- Connection test buttons with success/error states
- Collapsible advanced sections

---

## Installation Flow

### Step 1: Welcome
- Epic branding moment (logo, tagline)
- System requirements check:
  - PHP 8.0+
  - Python 3.11+
  - Node.js 20+
  - Redis connection
  - PostgreSQL connection
  - Write permissions
- "Begin Installation" button

### Step 2: License Verification

**Envato Purchase Code:**
| Field | Description |
|-------|-------------|
| Purchase Code | Envato/marketplace purchase code |
| Email | Buyer's email for license binding |
| "Verify License" button | Validates with api.aiassist.net |

**Verification Flow:**
1. User enters purchase code + email
2. Installer calls `api.aiassist.net/verify`
3. API validates code with Envato/internal database
4. On success: returns download token + license key
5. On failure: shows error (invalid code, already used, expired)

**License Response:**
```json
{
  "valid": true,
  "license_key": "AIAS-XXXX-XXXX-XXXX",
  "download_token": "temp_token_expires_1hr",
  "allowed_domains": 1,
  "support_until": "2026-01-16",
  "features": ["quests", "blog", "pin", "memory"]
}
```

### Step 3: Core Download

**Proprietary Package Delivery:**
- Shows download progress bar
- Fetches core files using download token
- Extracts to appropriate directories
- Verifies file integrity (checksums)

**Files Delivered:**
| Package | Contents |
|---------|----------|
| `core-services.zip` | ai_orchestrator.py, conversation_memory.py, redis_storage.py |
| `core-routes.zip` | workspaces.py, quests.py, pin.py, blog.py |
| `core-providers.zip` | Provider adapters and configs |

**Integrity Check:**
- SHA256 verification of each package
- File count validation
- Version compatibility check

### Step 4: Database & Cache

**PostgreSQL:**
| Field | Description |
|-------|-------------|
| Host | Database server hostname |
| Port | Database port (default: 5432) |
| Database | Database name |
| Username | Database user |
| Password | Database password |
| Connection string preview | Auto-generated from fields |
| "Test Connection" button | Validates connectivity |

**Redis:**
| Field | Description |
|-------|-------------|
| URL | Full Redis URL (or use fields below) |
| Host | Redis server hostname |
| Port | Redis port (default: 6379) |
| Password | Redis password (optional) |
| "Test Connection" button | Validates connectivity |

### Step 5: Admin Account

| Field | Description |
|-------|-------------|
| Email | Admin email (validated format) |
| Password | Admin password (strength indicator) |
| Confirm Password | Must match |
| Display Name | Admin display name |

### Step 6: Feature Modules

Toggle on/off with descriptions:

| Module | Description | Default |
|--------|-------------|---------|
| App Builder (Quests) | AI-assisted code generation environment | ON |
| Blog Generator | AI content creation for blogs | ON |
| PIN Network | Decentralized inference marketplace | OFF |
| Web Search Tools | Real-time web search for AI | ON |
| Conversation Memory | Long-term context retention | ON |
| Shadow Mode | Human-in-the-loop approval | ON |

### Step 7: Rate Limits & Quotas

**Anonymous Access:**
| Setting | Default | Description |
|---------|---------|-------------|
| Rate limit (requests) | 20 | Max requests for anonymous users |
| Rate window (seconds) | 3600 | Time window for rate limiting |

**Authenticated Users:**
| Setting | Default | Description |
|---------|---------|-------------|
| Requests per minute | 60 | Per-user request limit |
| Requests per hour | 600 | Hourly request limit |

**API Keys:**
| Setting | Default | Description |
|---------|---------|-------------|
| Rate limit per minute | 10 | Per-key request limit |

**Free Tier:**
| Setting | Default | Description |
|---------|---------|-------------|
| Message limit | 50 | Max messages for free users |
| Window (days) | 30 | Rolling window for limit |

**Web Extraction:**
| Setting | Default | Description |
|---------|---------|-------------|
| Daily limit per user | 100 | Max extractions per day |

### Step 8: Session & Cache Settings

**Sessions:**
| Setting | Default | Description |
|---------|---------|-------------|
| Session expiry (days) | 7 | How long sessions remain valid |
| Session cookie name | `session_id` | Cookie identifier |

**Cache TTLs:**
| Setting | Default | Description |
|---------|---------|-------------|
| Web search cache (seconds) | 300 | Cache duration for search results |
| Memory session TTL (days) | 7 | How long memory sessions persist |

**Workers:**
| Setting | Default | Description |
|---------|---------|-------------|
| Worker lock TTL (seconds) | 300 | Lock duration for background workers |

### Step 9: AI Provider Defaults

**Default Models per Provider:**

| Provider | Default Model |
|----------|---------------|
| groq | llama-3.3-70b-versatile |
| openai | gpt-4o |
| anthropic | claude-3-5-sonnet-20241022 |
| gemini | gemini-1.5-pro |
| mistral | mistral-large-latest |
| xai | grok-2-1212 |
| together | meta-llama/Llama-3.3-70B-Instruct-Turbo |
| openrouter | anthropic/claude-3.5-sonnet |
| deepseek | deepseek-chat |
| fireworks | accounts/fireworks/models/llama-v3p3-70b-instruct |
| perplexity | sonar-pro |

**Fallback Models per Provider:**

| Provider | Fallback Model |
|----------|----------------|
| groq | moonshotai/kimi-k2-instruct |
| openai | gpt-4o-mini |
| anthropic | claude-3-5-haiku-20241022 |
| gemini | gemini-1.5-flash |
| mistral | mistral-small-latest |
| xai | grok-3-fast |
| together | meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo |
| openrouter | meta-llama/llama-3.3-70b-instruct |
| deepseek | deepseek-chat |
| fireworks | accounts/fireworks/models/llama-v3p1-8b-instruct |
| perplexity | sonar |

**Provider Timeouts:**
| Setting | Default | Description |
|---------|---------|-------------|
| Default timeout (seconds) | 60 | Standard provider timeout |
| Anthropic timeout | 90 | Extended for Claude |
| Groq timeout | 30 | Faster for Groq |

**Token Limits:**
| Setting | Default | Description |
|---------|---------|-------------|
| Default max tokens | 1024 | Standard completion limit |
| Blog generation max tokens | 2048 | Extended for content generation |

### Step 10: Conversation Memory

**Circuit Breaker:**
| Setting | Default | Description |
|---------|---------|-------------|
| Failure threshold | 5 | Failures before circuit opens |
| Reset timeout (seconds) | 60 | Time before circuit resets |

**Context Budgets per Provider:**
| Provider | Token Budget |
|----------|--------------|
| groq | 6000 |
| openai | 8000 |
| anthropic | 8000 |
| gemini | 10000 |
| mistral | 6000 |

**Fact Priority Weights:**
| Fact Type | Priority Weight |
|-----------|-----------------|
| preference | 3 |
| constraint | 3 |
| identity | 2 |
| context | 1 |

### Step 11: PIN Network (if enabled)

**Economics:**
| Setting | Default | Description |
|---------|---------|-------------|
| Protocol fee percent | 10% | Platform fee on transactions |

**Timing:**
| Setting | Default | Description |
|---------|---------|-------------|
| Heartbeat TTL (seconds) | 60 | Time before node marked stale |
| Operator timeout (seconds) | 30 | Request timeout to operators |
| Health check interval (seconds) | 30 | Frequency of health checks |

**Interviews:**
| Setting | Default | Description |
|---------|---------|-------------|
| Interview timeout (seconds) | 180 | Max time for interview completion |
| Retry cooldown (hours) | 1 | Wait time between retries |
| Max attempts per day | 3 | Daily interview attempt limit |

**Benchmark Models:**
Editable list of required models for interviews:
- llama3:8b
- mistral:7b
- qwen2:7b
- gemma2:7b

**Quality Tier Thresholds (Ollama Mode):**
| Setting | Default | Description |
|---------|---------|-------------|
| Verified accuracy % | 90 | Minimum accuracy for verified tier |
| Verified tokens/sec | 20 | Minimum speed for verified tier |
| Standard accuracy % | 70 | Minimum accuracy for standard tier |
| Standard tokens/sec | 10 | Minimum speed for standard tier |
| Minimum tokens/sec | 10 | Absolute floor (below = failed) |

**Quality Tier Thresholds (OpenAI Mode - Stricter):**
| Setting | Default | Description |
|---------|---------|-------------|
| Verified accuracy % | 95 | Minimum accuracy for verified tier |
| Verified tokens/sec | 30 | Minimum speed for verified tier |
| Standard accuracy % | 85 | Minimum accuracy for standard tier |
| Standard tokens/sec | 20 | Minimum speed for standard tier |
| Minimum tokens/sec | 15 | Absolute floor (below = failed) |

### Step 12: Subscriptions & Billing

**Grace Period:**
| Setting | Default | Description |
|---------|---------|-------------|
| Grace period days | 7 | Days after expiry before suspension |
| Warning days before expiry | 7 | When to start warning users |

### Step 13: App Builder Limits (if enabled)

**Environment Limits per Plan:**
| Plan | Environments | Storage (MB) |
|------|--------------|--------------|
| free | 0 | 50 |
| basic | 1 | 200 |
| pro | 5 | 1000 |
| enterprise | 100 | 5000 |

**Limits:**
| Setting | Default | Description |
|---------|---------|-------------|
| Max repo size (MB) | 50 | Maximum project size |
| Max output lines | 500 | Console output limit |

### Step 14: Web Search Limits (if enabled)

**Searches per Plan:**
| Plan | Daily Limit |
|------|-------------|
| free | 10 |
| basic | 50 |
| pro | 200 |
| enterprise | 999999 |

**Blocked Domains:**
Editable list of domains to block from search results.

### Step 15: Security

**Secrets (auto-generated with option to customize):**
| Setting | Description |
|---------|-------------|
| Session secret | Used for session encryption (auto-generated) |
| PIN encryption key | Used for PIN network encryption (auto-generated) |

**CORS:**
| Setting | Default | Description |
|---------|---------|-------------|
| Allowed origins | * | Comma-separated origins or * for all |

**Content Limits:**
| Setting | Default | Description |
|---------|---------|-------------|
| Max text content length | 10000 | Maximum content in messages |
| Max display name length | 100 | Maximum name field length |

### Step 16: Human Escalation

**Trigger Phrases:**
Editable list of phrases that trigger human handoff:
- speak to a human
- talk to a human
- speak to a manager
- talk to a manager
- speak to a supervisor
- get me a human
- I want a real person
- let me speak to someone
- transfer me to a human
- I need human help

**Single Word Triggers:**
- help
- human
- manager
- supervisor
- agent
- person
- representative

**Escalation Message:**
Customizable response when escalation triggers:
> "I've notified our team that you'd like to speak with a human. Someone will be with you shortly. Thank you for your patience!"

### Step 17: Review & Install

- Summary of all configured settings
- Collapsible sections for each category
- "Edit" links to jump back to any step
- Final validation of all settings
- "Install" button

### Step 18: Complete

- Success message with celebration animation
- Generated config file location
- Environment file location
- Next steps:
  1. Start backend: `python -m uvicorn api.main:app --host 0.0.0.0 --port 8000`
  2. Start frontend: `npm run dev`
  3. Access dashboard: `https://your-domain.com`
- "Launch Dashboard" button
- "Lock Installer" option (creates install.lock to prevent re-running)

---

## Technical Implementation

### File Structure

```
installer/
├── index.php              # Main entry point & router
├── config.php             # Installer configuration
├── assets/
│   ├── css/
│   │   └── installer.css  # All styles (dark/light themes)
│   └── js/
│       └── installer.js   # Step navigation, validation, animations
├── templates/
│   ├── header.php         # Common header with progress bar
│   ├── footer.php         # Common footer with navigation
│   └── steps/
│       ├── 01-welcome.php
│       ├── 02-database.php
│       ├── 03-admin.php
│       ├── 04-features.php
│       ├── 05-rates.php
│       ├── 06-sessions.php
│       ├── 07-providers.php
│       ├── 08-memory.php
│       ├── 09-pin.php
│       ├── 10-subscriptions.php
│       ├── 11-quests.php
│       ├── 12-websearch.php
│       ├── 13-security.php
│       ├── 14-escalation.php
│       ├── 15-review.php
│       └── 16-complete.php
├── includes/
│   ├── validators.php     # Input validation functions
│   ├── connectors.php     # DB/Redis connection testing
│   └── writers.php        # Config file generation
└── install.lock           # Created after successful install
```

### Output Files

**1. `.env` file (environment variables):**
```env
# Generated by AiAS Installer
# Date: 2025-01-16

# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Redis
REDIS_URL=redis://:password@host:6379/0

# Security
SESSION_SECRET=<generated-64-char-hex>
PIN_ENCRYPTION_KEY=<generated-base64-key>
```

**2. `config/app.json` (application settings):**
```json
{
  "version": "1.0.0",
  "generated_at": "2025-01-16T12:00:00Z",
  
  "features": {
    "quests_enabled": true,
    "blog_enabled": true,
    "pin_enabled": false,
    "web_search_enabled": true,
    "memory_enabled": true,
    "shadow_mode_enabled": true
  },
  
  "rate_limits": {
    "anonymous_limit": 20,
    "anonymous_window": 3600,
    "requests_per_minute": 60,
    "requests_per_hour": 600,
    "api_key_per_minute": 10,
    "free_tier_limit": 50,
    "free_tier_window_days": 30,
    "web_extraction_daily": 100
  },
  
  "sessions": {
    "expiry_days": 7,
    "cookie_name": "session_id",
    "memory_ttl_days": 7,
    "cache_ttl_seconds": 300,
    "worker_lock_ttl": 300
  },
  
  "providers": {
    "default_models": {
      "groq": "llama-3.3-70b-versatile",
      "openai": "gpt-4o"
    },
    "fallback_models": {
      "groq": "moonshotai/kimi-k2-instruct",
      "openai": "gpt-4o-mini"
    },
    "timeouts": {
      "default": 60,
      "anthropic": 90,
      "groq": 30
    },
    "max_tokens": {
      "default": 1024,
      "blog": 2048
    }
  },
  
  "memory": {
    "circuit_breaker": {
      "failure_threshold": 5,
      "reset_timeout": 60
    },
    "context_budgets": {
      "groq": 6000,
      "openai": 8000
    },
    "fact_priorities": {
      "preference": 3,
      "constraint": 3,
      "identity": 2,
      "context": 1
    }
  },
  
  "pin": {
    "protocol_fee_percent": 0.10,
    "heartbeat_ttl": 60,
    "operator_timeout": 30,
    "health_check_interval": 30,
    "interview_timeout": 180,
    "interview_retry_cooldown_hours": 1,
    "interview_max_attempts_per_day": 3,
    "benchmark_models": ["llama3:8b", "mistral:7b", "qwen2:7b", "gemma2:7b"],
    "tier_thresholds_ollama": {
      "verified_accuracy": 90,
      "verified_tokens_per_sec": 20,
      "standard_accuracy": 70,
      "standard_tokens_per_sec": 10,
      "min_tokens_per_sec": 10
    },
    "tier_thresholds_openai": {
      "verified_accuracy": 95,
      "verified_tokens_per_sec": 30,
      "standard_accuracy": 85,
      "standard_tokens_per_sec": 20,
      "min_tokens_per_sec": 15
    }
  },
  
  "subscriptions": {
    "grace_period_days": 7,
    "warning_days_before": 7
  },
  
  "quests": {
    "limits": {
      "free": {"environments": 0, "storage_mb": 50},
      "basic": {"environments": 1, "storage_mb": 200},
      "pro": {"environments": 5, "storage_mb": 1000},
      "enterprise": {"environments": 100, "storage_mb": 5000}
    },
    "max_repo_size_mb": 50,
    "max_output_lines": 500
  },
  
  "web_search": {
    "limits": {
      "free": 10,
      "basic": 50,
      "pro": 200,
      "enterprise": 999999
    },
    "blocked_domains": []
  },
  
  "security": {
    "cors_allowed_origins": "*",
    "max_text_content_length": 10000,
    "max_display_name_length": 100
  },
  
  "escalation": {
    "trigger_phrases": [
      "speak to a human",
      "talk to a human",
      "speak to a manager"
    ],
    "single_word_triggers": ["help", "human", "manager"],
    "response_message": "I've notified our team that you'd like to speak with a human. Someone will be with you shortly. Thank you for your patience!"
  }
}
```

### Config Loader (Python)

New `api/config_loader.py` that:
1. Reads `config/app.json` on startup
2. Provides typed access to all settings
3. Falls back to current hardcoded defaults if config missing
4. Validates config structure on load

```python
# Example usage
from api.config_loader import config

# Feature flags
if config.features.quests_enabled:
    app.include_router(quests.router)

# Rate limits
limit = config.rate_limits.anonymous_limit

# Provider settings
timeout = config.providers.timeouts.get("anthropic", 60)
```

### Feature Flag Integration

Each optional module checks config before loading:

```python
# In api/main.py
from api.config_loader import config

if config.features.quests_enabled:
    from api.routes import quests
    app.include_router(quests.router, prefix="/api/app-builder", tags=["quests"])

if config.features.blog_enabled:
    from api.routes import blog
    app.include_router(blog.router, prefix="/api/blog", tags=["blog"])

if config.features.pin_enabled:
    from api.routes import pin
    app.include_router(pin.router, prefix="/api/pin", tags=["pin"])
```

---

## Security Considerations

1. **Installer lock** - After successful install, create `install.lock` to prevent re-running
2. **Secret generation** - Use `random_bytes(32)` for cryptographically secure secrets
3. **Input validation** - Sanitize all inputs, validate email format, check password strength
4. **Connection testing** - Verify DB/Redis connections work before proceeding
5. **File permissions** - Check write access to config directories before attempting save
6. **HTTPS recommendation** - Display warning banner if not using HTTPS
7. **Admin password requirements** - Minimum 8 characters, mixed case, numbers

---

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

---

## Dependencies

- PHP 8.0+ with extensions:
  - PDO (PostgreSQL driver)
  - Redis extension
  - JSON extension
  - OpenSSL extension
- No external PHP packages required (vanilla PHP)

---

## Internationalization (Future)

Structure supports future i18n:
```
installer/
├── lang/
│   ├── en.php
│   ├── es.php
│   └── zh.php
```

---

## Package Split (Distribution Model)

### Public Shell Package (Ships with Purchase)

What the customer downloads from Envato/marketplace:

```
aiassist-agency/
├── installer/              # PHP installation wizard
│   ├── index.php
│   ├── config.php
│   ├── assets/
│   ├── templates/
│   └── includes/
├── client/                 # React frontend (minified)
│   ├── dist/
│   └── index.html
├── server/                 # Express proxy (basic)
│   └── index.js
├── shared/                 # TypeScript schemas
│   └── schema.ts
├── api/                    # Python skeleton
│   ├── main.py             # Basic app loader
│   ├── models/             # Pydantic schemas
│   └── __init__.py
├── config/                 # Empty, populated by installer
├── .env.example
├── package.json
├── requirements.txt
├── docker-compose.yml      # Optional Docker setup
└── README.md
```

### Proprietary Core Package (Delivered After Verification)

Downloaded during Step 3 after license validates:

```
core-services.zip
├── api/services/
│   ├── ai_orchestrator.py
│   ├── conversation_memory.py
│   ├── redis_storage.py
│   ├── subscription_service.py
│   ├── blog_generator.py
│   ├── web_search.py
│   └── web_extraction.py

core-routes.zip
├── api/routes/
│   ├── workspaces.py
│   ├── quests.py
│   ├── pin.py
│   ├── blog.py
│   ├── memory.py
│   └── webhooks.py

core-providers.zip
├── api/providers/
│   ├── router.py
│   ├── config.py
│   └── adapters/
```

### License API Endpoints

**Verify License:**
```
POST https://api.aiassist.net/license/verify
{
  "purchase_code": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "email": "buyer@example.com",
  "domain": "agency.example.com"
}

Response:
{
  "valid": true,
  "license_key": "AIAS-XXXX-XXXX-XXXX",
  "download_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_expires": "2025-01-16T13:00:00Z",
  "allowed_domains": 1,
  "support_until": "2026-01-16",
  "features": ["quests", "blog", "pin", "memory", "shadow_mode"]
}
```

**Download Core:**
```
GET https://api.aiassist.net/license/download/{package}
Authorization: Bearer {download_token}

Packages: core-services, core-routes, core-providers
Returns: ZIP file with SHA256 checksum header
```

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.1.0 | 2025-01-16 | Added license verification, core download, package split |
| 1.0.0 | 2025-01-16 | Initial specification |
