# RapidAPI Integration Workplan

**AiAssist Secure → RapidAPI Marketplace**

This document outlines the comprehensive plan to list AiAssist Secure on RapidAPI as a distribution channel alongside our direct Stripe billing.

---

## Executive Summary

**Goal:** List AiAssist Secure API on RapidAPI to gain exposure to 4M+ developers while maintaining our direct Stripe billing channel.

**Timeline:** ~1 week to full listing

**Revenue Split:** RapidAPI takes 20-30%, we keep 70-80%

**Strategy:** RapidAPI for discovery/small customers, direct Stripe for enterprise/high-value deals

---

## Phase 1: Pre-Integration Prep (Day 1-2)

### 1.1 Export OpenAPI Specification

FastAPI auto-generates OpenAPI spec. We need to clean it up for RapidAPI.

**Tasks:**
- [ ] Access current spec at `https://api.aiassist.net/openapi.json`
- [ ] Review and enhance descriptions for all endpoints
- [ ] Add example requests/responses
- [ ] Remove internal/admin endpoints not for public consumption

**Endpoints to expose on RapidAPI:**

| Endpoint | Method | Description | Public? |
|----------|--------|-------------|---------|
| `/v1/chat/completions` | POST | OpenAI-compatible chat completions | ✅ Yes |
| `/v1/models` | GET | List available models | ✅ Yes |
| `/api/workspaces` | POST | Create workspace | ✅ Yes |
| `/api/workspaces/{id}/messages` | POST | Send message | ✅ Yes |
| `/api/workspaces/{id}/messages` | GET | Get messages | ✅ Yes |
| `/api/workspaces/{id}/end` | POST | End conversation | ✅ Yes |
| `/api/workspaces/{id}/typing` | GET | Typing status | ✅ Yes |

**Endpoints to EXCLUDE:**
- `/api/admin/*` - Admin routes
- `/api/auth/*` - Internal auth (RapidAPI handles auth)
- `/api/subscriptions/*` - Stripe billing (separate channel)
- `/api/pin/*` - PIN network (internal)
- `/api/reseller/*` - Reseller management

### 1.2 Prepare Marketing Assets

- [ ] API Logo (512x512 PNG, transparent background)
- [ ] Short description (1-2 sentences for search results)
- [ ] Long description (full marketing copy with use cases)
- [ ] Category selection: `AI`, `Machine Learning`, `Chatbots`
- [ ] Tags: `ai`, `chatbot`, `openai`, `llm`, `customer-support`, `shadow-mode`

**Short Description Draft:**
> Enterprise AI chat API with shadow mode, human-in-the-loop, and BYOK support. Add AI assistants to any app with human oversight.

**Long Description Draft:**
```markdown
## AiAssist Secure API

Add enterprise-grade AI chat to your application with built-in human oversight.

### Key Features

- **Shadow Mode** - AI drafts responses, humans approve before sending
- **Human-in-the-Loop** - Seamless AI-to-human handoff
- **BYOK** - Bring your own OpenAI/Anthropic/Groq API keys
- **OpenAI Compatible** - Drop-in replacement for OpenAI chat API
- **Managed Workspaces** - Persistent conversation threads with context

### Use Cases

- Customer support chatbots with human escalation
- AI assistants that require compliance review
- Training environments for AI response quality
- White-label chat widgets for agencies

### Why AiAssist Secure?

Unlike raw LLM APIs, AiAssist Secure provides the orchestration layer:
conversation memory, mode detection, approval workflows, and multi-tenant workspaces.

Perfect for teams that need AI power with human control.
```

---

## Phase 2: Auth Bridge Implementation (Day 2-3)

### 2.1 How RapidAPI Auth Works

RapidAPI sends these headers with every request:

```
x-rapidapi-key: <subscriber's RapidAPI key>
x-rapidapi-host: aiassist-secure.p.rapidapi.com
x-rapidapi-user: <subscriber's RapidAPI user ID>
```

We need to map these to our internal API key system.

### 2.2 Auth Bridge Middleware

**File:** `api/middleware/rapidapi_auth.py`

**Logic:**
```python
async def rapidapi_auth_middleware(request, call_next):
    rapidapi_key = request.headers.get("x-rapidapi-key")
    rapidapi_user = request.headers.get("x-rapidapi-user")
    
    if rapidapi_key:
        # Look up or create internal API key for this RapidAPI user
        internal_key = await get_or_create_rapidapi_mapping(
            rapidapi_key=rapidapi_key,
            rapidapi_user=rapidapi_user
        )
        # Inject our API key into request for downstream handlers
        request.state.api_key = internal_key
        request.state.source = "rapidapi"
    
    return await call_next(request)
```

### 2.3 RapidAPI User Mapping Table

**Schema:**
```sql
CREATE TABLE rapidapi_mappings (
    id UUID PRIMARY KEY,
    rapidapi_key VARCHAR(255) UNIQUE NOT NULL,
    rapidapi_user VARCHAR(255),
    internal_api_key_id UUID REFERENCES api_keys(id),
    rapidapi_plan VARCHAR(50),  -- 'free', 'basic', 'pro', 'enterprise'
    created_at TIMESTAMP DEFAULT NOW(),
    last_used_at TIMESTAMP
);
```

**Index:** `CREATE INDEX idx_rapidapi_key ON rapidapi_mappings(rapidapi_key);`

### 2.4 Plan Mapping

| RapidAPI Plan | Internal Plan | Rate Limits |
|---------------|---------------|-------------|
| Free | free | 100 requests/month |
| Basic ($29/mo) | basic | 1,000 requests/month |
| Pro ($99/mo) | pro | 10,000 requests/month |
| Enterprise ($299/mo) | enterprise | 100,000 requests/month |

RapidAPI enforces rate limits on their end. We track usage for our analytics.

---

## Phase 3: RapidAPI Listing Setup (Day 3-4)

### 3.1 Create API Project

1. Go to https://rapidapi.com/hub
2. Click "My APIs" → "Add API Project"
3. Fill in:
   - **Name:** `AiAssist Secure` (don't include "API")
   - **Category:** `Artificial Intelligence`
   - **Team:** Your RapidAPI team

### 3.2 Configure Base URL

**Base URL:** `https://api.aiassist.net`

RapidAPI will proxy requests:
```
User → rapidapi.com/aiassist-secure → api.aiassist.net
```

### 3.3 Upload OpenAPI Spec

- Navigate to "Definitions" tab
- Upload cleaned `openapi.json`
- Verify all endpoints imported correctly
- Add example responses for each endpoint

### 3.4 Configure Pricing Plans

**Monetization Tab:**

| Plan | Price | Quota | Overage |
|------|-------|-------|---------|
| **Free** | $0/mo | 100 requests | Hard limit |
| **Basic** | $29/mo | 1,000 requests | $0.05/request |
| **Pro** | $99/mo | 10,000 requests | $0.03/request |
| **Enterprise** | $299/mo | 100,000 requests | $0.01/request |

### 3.5 Documentation

For each endpoint, ensure:
- [ ] Clear description
- [ ] All parameters documented
- [ ] Example request body
- [ ] Example response
- [ ] Error codes explained

---

## Phase 4: Testing (Day 4-5)

### 4.1 Test Auth Bridge

```bash
# Simulate RapidAPI request
curl -X POST https://api.aiassist.net/v1/chat/completions \
  -H "x-rapidapi-key: test-key-123" \
  -H "x-rapidapi-host: aiassist-secure.p.rapidapi.com" \
  -H "x-rapidapi-user: user-456" \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "Hello"}]}'
```

**Verify:**
- [ ] Request creates mapping if new user
- [ ] Request uses existing mapping if repeat user
- [ ] Rate limits respected
- [ ] Usage tracked in analytics

### 4.2 Test via RapidAPI Console

Before publishing:
- [ ] Test each endpoint in RapidAPI's web console
- [ ] Verify streaming works (SSE)
- [ ] Check error responses are clean
- [ ] Confirm latency is acceptable

### 4.3 Test Pricing Enforcement

- [ ] Free tier hits limit at 100 requests
- [ ] Upgrade flow works
- [ ] Overage billing triggers correctly

---

## Phase 5: Launch (Day 5-6)

### 5.1 Soft Launch

- [ ] Publish API as "Private" first
- [ ] Share with 2-3 beta testers
- [ ] Collect feedback
- [ ] Fix any issues

### 5.2 Public Launch

- [ ] Set visibility to "Public"
- [ ] API appears in RapidAPI search
- [ ] Monitor first 24 hours closely

### 5.3 Promotion

- [ ] Add "Available on RapidAPI" badge to website
- [ ] Tweet/post about availability
- [ ] Update SDK READMEs with RapidAPI option
- [ ] Add to API directories (Public APIs, APIs.guru)

---

## Phase 6: Ongoing Operations

### 6.1 Monitoring

Set up alerts for:
- [ ] Error rate > 5%
- [ ] Latency > 2s p95
- [ ] New subscriber signups
- [ ] Churn events

### 6.2 Analytics Dashboard

Track:
- Daily/weekly/monthly active users
- Requests per plan tier
- Conversion rate (free → paid)
- Revenue via RapidAPI

### 6.3 Support

- Monitor RapidAPI's built-in Q&A section
- Respond to user questions within 24h
- Update docs based on common questions

### 6.4 Version Management

When updating the API:
- Create new version in RapidAPI
- Maintain backwards compatibility
- Deprecate old versions with notice

---

## Revenue Projections

### Conservative Estimate (Month 1-3)

| Plan | Subscribers | MRR (before RapidAPI cut) | Net MRR (70%) |
|------|-------------|---------------------------|---------------|
| Free | 100 | $0 | $0 |
| Basic | 20 | $580 | $406 |
| Pro | 5 | $495 | $347 |
| Enterprise | 1 | $299 | $209 |
| **Total** | 126 | $1,374 | **$962** |

### Growth Estimate (Month 6-12)

| Plan | Subscribers | MRR (before cut) | Net MRR (70%) |
|------|-------------|------------------|---------------|
| Free | 500 | $0 | $0 |
| Basic | 80 | $2,320 | $1,624 |
| Pro | 30 | $2,970 | $2,079 |
| Enterprise | 10 | $2,990 | $2,093 |
| **Total** | 620 | $8,280 | **$5,796** |

---

## Dual-Channel Strategy

### RapidAPI Channel
- Discovery & self-serve
- SMB customers
- Developers testing/prototyping
- 70-80% margin after RapidAPI cut

### Direct Stripe Channel
- Enterprise deals
- Custom pricing
- White-label/reseller arrangements
- 97% margin (Stripe fees only)

**Upsell Path:**
RapidAPI user → Hits limits → Offer direct signup with better pricing/features

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| RapidAPI takes too much margin | Direct channel remains primary; RapidAPI is discovery |
| RapidAPI changes terms | No exclusivity; can delist anytime |
| Support burden increases | Self-serve docs, FAQ, rate limit enforcement |
| Competitors copy listing | Shadow mode + PIN network = hard to replicate |

---

## Success Criteria

**30 Days:**
- [ ] 50+ free tier users
- [ ] 10+ paid subscribers
- [ ] < 5% error rate
- [ ] 4+ star rating

**90 Days:**
- [ ] 200+ free tier users
- [ ] 50+ paid subscribers
- [ ] $2,000+ net MRR from RapidAPI
- [ ] Featured in RapidAPI collection

---

## Appendix: Implementation Checklist

### Pre-Launch
- [ ] Clean OpenAPI spec exported
- [ ] Marketing assets created
- [ ] Auth bridge middleware written
- [ ] Database migration for rapidapi_mappings
- [ ] Rate limiting configured
- [ ] Endpoints tested

### Launch
- [ ] RapidAPI project created
- [ ] Spec uploaded
- [ ] Pricing configured
- [ ] Documentation complete
- [ ] Beta testing done
- [ ] Public launch

### Post-Launch
- [ ] Monitoring alerts set up
- [ ] Analytics tracking
- [ ] Support workflow established
- [ ] Promotion executed

---

## Next Steps

1. **Review this plan** - Adjust timeline/pricing as needed
2. **Approve implementation** - Green light the auth bridge work
3. **Execute Phase 1** - Export and clean OpenAPI spec
4. **Build auth bridge** - ~2-4 hours of development
5. **Create listing** - ~1 hour of form filling
6. **Launch** - Go live on RapidAPI

---

*Document Version: 1.0*
*Last Updated: January 2026*
*Author: AiAssist Secure Team*
