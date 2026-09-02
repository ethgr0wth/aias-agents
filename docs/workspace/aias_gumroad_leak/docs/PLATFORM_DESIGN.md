# AiAssist Multi-User Platform Design Document

## Overview

AiAssist is evolving from a single-tenant AI consulting CRM into a multi-user AI-as-a-Service platform. Users can sign up, purchase API access, and integrate AI capabilities into their own applications using our API.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React)                         │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   Public Site   │  User Dashboard │      Admin Panel            │
│   - Landing     │  - API Keys     │   - User Management         │
│   - Pricing     │  - Usage Stats  │   - Analytics               │
│   - Signup      │  - Billing      │   - Workspace Monitor       │
└─────────────────┴─────────────────┴─────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND                             │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   Auth Routes   │   API Routes    │     Admin Routes            │
│   - /auth/*     │   - /v1/chat    │   - /admin/*                │
│                 │   - /v1/models  │                             │
└─────────────────┴─────────────────┴─────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
         ┌────────┐     ┌─────────┐     ┌──────────┐
         │ Redis  │     │  GROQ   │     │ PostgreSQL│
         │ Cache  │     │   API   │     │  (future) │
         └────────┘     └─────────┘     └──────────┘
```

## Data Models

### User (Extended)
```python
User:
  id: str (UUID)
  email: str (unique)
  password_hash: str
  display_name: str
  role: enum (client, reseller, manager, super_admin)
  plan: enum (free, basic, pro, enterprise)
  organization_id: str (optional)
  is_active: bool
  email_verified: bool
  created_at: datetime
  updated_at: datetime
```

### API Key
```python
ApiKey:
  id: str (UUID)
  user_id: str (FK -> User)
  key_hash: str (hashed, never stored plain)
  key_prefix: str (first 8 chars for display: "aai_xxxx...")
  name: str (user-defined label)
  permissions: list[str] (scopes)
  rate_limit: int (requests per minute)
  is_active: bool
  last_used_at: datetime
  expires_at: datetime (optional)
  created_at: datetime
```

### Usage Record
```python
UsageRecord:
  id: str (UUID)
  user_id: str (FK -> User)
  api_key_id: str (FK -> ApiKey)
  model: str (e.g., "llama-3.3-70b-versatile")
  input_tokens: int
  output_tokens: int
  total_tokens: int
  cost_usd: float
  endpoint: str
  timestamp: datetime
```

### Plan/Subscription
```python
Plan:
  id: str
  name: str (free, basic, pro, enterprise)
  price_monthly: float
  price_yearly: float
  models_allowed: list[str]
  rate_limit_rpm: int (requests per minute)
  monthly_token_limit: int
  features: dict
```

## Pricing Tiers

| Feature | Free | Basic ($19/mo) | Pro ($49/mo) | Enterprise ($199/mo) |
|---------|------|----------------|--------------|----------------------|
| Models | Llama 70B | Llama 70B | Llama 70B, Mixtral | All Models |
| Rate Limit | 10 RPM | 60 RPM | 120 RPM | 600 RPM |
| Monthly Tokens | 100K | 1M | 5M | 25M |
| API Keys | 1 | 3 | 10 | Unlimited |
| Support | Community | Email | Priority | Dedicated |
| Workspaces | 1 | 5 | 25 | Unlimited |

## API Design

### Authentication
All API requests use Bearer token authentication:
```
Authorization: Bearer aai_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

API keys are prefixed with `aai_` for easy identification.

### Public API Endpoints

#### Chat Completion
```
POST /v1/chat/completions
Authorization: Bearer aai_xxxxx

Request:
{
  "model": "llama-3.3-70b-versatile",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
  ],
  "temperature": 0.7,
  "max_tokens": 1024,
  "stream": false
}

Response:
{
  "id": "chat-xxxxx",
  "object": "chat.completion",
  "created": 1702000000,
  "model": "llama-3.3-70b-versatile",
  "choices": [{
    "index": 0,
    "message": {"role": "assistant", "content": "Hello! How can I help?"},
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 20,
    "completion_tokens": 10,
    "total_tokens": 30
  }
}
```

#### List Models
```
GET /v1/models
Authorization: Bearer aai_xxxxx

Response:
{
  "data": [
    {"id": "llama-3.3-70b-versatile", "tier": "basic"},
    {"id": "mixtral-8x7b-32768", "tier": "pro"},
    {"id": "llama-3.1-8b-instant", "tier": "basic"}
  ]
}
```

#### Get Usage
```
GET /v1/usage
Authorization: Bearer aai_xxxxx

Response:
{
  "period": "2024-12",
  "tokens_used": 45000,
  "tokens_limit": 1000000,
  "requests": 150
}
```

### User Dashboard Endpoints

```
GET /api/user/me              - Get current user profile
PATCH /api/user/me            - Update profile
GET /api/user/api-keys        - List user's API keys
POST /api/user/api-keys       - Create new API key
DELETE /api/user/api-keys/:id - Revoke API key
GET /api/user/usage           - Get usage statistics
GET /api/user/billing         - Get billing information
```

## Frontend Routes

```
/                    - Landing page (marketing)
/pricing             - Pricing page
/login               - User login
/register            - User registration
/dashboard           - User dashboard (authenticated)
/dashboard/api-keys  - API key management
/dashboard/usage     - Usage statistics
/dashboard/settings  - Account settings
/docs                - API documentation
/admin/*             - Admin panel (existing)
```

## Implementation Phases

### Phase 1: User System (Current Sprint)
- [x] User registration with email/password
- [x] User login with session/cookie auth
- [x] User dashboard page
- [x] API key generation and management
- [x] Basic usage tracking

### Phase 2: Public API
- [ ] OpenAI-compatible chat completions endpoint
- [ ] API key authentication middleware
- [ ] Rate limiting per user/plan
- [ ] Usage metering and logging

### Phase 3: Pricing & Billing
- [ ] Pricing page with tier comparison
- [ ] Stripe integration for payments
- [ ] Subscription management
- [ ] Invoice generation

### Phase 4: Advanced Features
- [ ] Streaming responses
- [ ] Fine-tuning support
- [ ] Custom model deployment
- [ ] Team/organization features

## Security Considerations

1. **API Key Storage**: Keys are hashed using bcrypt before storage
2. **Rate Limiting**: Redis-based sliding window rate limiting
3. **Input Validation**: All inputs validated with Pydantic
4. **CORS**: Strict CORS policy for API endpoints
5. **Audit Logging**: All API calls logged for security review

## Redis Key Structure

```
aiconsult:users:{user_id}           - User data
aiconsult:api_keys:{key_hash}       - API key lookup
aiconsult:user_keys:{user_id}       - User's API key IDs (set)
aiconsult:usage:{user_id}:{month}   - Monthly usage counters
aiconsult:rate_limit:{key_id}       - Rate limit counters
```

## Environment Variables

```
GROQ_API_KEY          - Groq API key for AI inference
REDIS_URL             - Redis connection string
DATABASE_URL          - PostgreSQL (future)
SESSION_SECRET        - Cookie signing secret
STRIPE_SECRET_KEY     - Stripe payments (future)
```
