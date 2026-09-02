# AiAssist - Design Documentation

## Overview

AiAssist is an AI-as-a-Service platform that enables businesses and developers to integrate AI consulting capabilities into their applications. Users can sign up, manage their AI knowledge base, generate API keys, and access AI through both the web interface and programmatic API.

---

## Current State (What's Built)

### Authentication & User Management
- Session-based authentication with HTTP-only cookies
- User registration and login
- Role-based access control (client, reseller, manager, super_admin)
- Plan types (free, basic, pro, enterprise) with different capabilities
- API key generation (`aai_` prefixed keys) for programmatic access

### Workspaces & Chat
- Multi-tenant workspace system
- Real-time chat via Socket.IO
- Three workspace modes:
  - **AI Mode**: Autonomous AI responses
  - **Shadow Mode**: AI drafts responses, human approves
  - **Takeover Mode**: Human takes full control
- Message history and conversation threading

### AI Orchestration
- Groq API integration (Llama 3.3 70B, Llama 3.1 8B, Mixtral 8x7B)
- Dynamic system prompt building with:
  - Directives (persona, tone, context, constraints, guidance)
  - Knowledge Base injection (per-user, automatically applied)
  - Response templates
- Model access controlled by user plan

### Knowledge Base
- User-owned training contexts
- Categories: company info, products, FAQ, technical, policies, custom
- Automatically injected into all AI conversations for the user
- CRUD operations via API and UI

### Admin Features
- User management dashboard
- Workspace overview
- Contact/CRM system
- Directive management per workspace
- License key generation and management

### API & SDKs
- OpenAI-compatible public API endpoint (`/v1/chat/completions`)
- Rate limiting per plan tier
- Usage logging skeleton (tracks API calls)
- SDK examples for React, vanilla JS, and Python

### Frontend
- React + TypeScript + Vite
- Tailwind CSS + shadcn/ui components
- Pages: Home, Dashboard, Workspaces, Knowledge Base, Pricing, Admin Panel
- Framer Motion animations

---

## Technical Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React)                        │
│                  Port 5000 (via Express)                    │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              Express Proxy Server (Port 5000)               │
│         - Serves static files                               │
│         - Proxies /api/* and /socket.io to FastAPI          │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              FastAPI Backend (Port 8000)                    │
│         - Authentication & Authorization                    │
│         - Business Logic                                    │
│         - AI Orchestration                                  │
│         - WebSocket (Socket.IO)                             │
└─────────────────────┬───────────────────────────────────────┘
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│     Redis       │     │    Groq API     │
│  (All Data)     │     │   (LLM Calls)   │
└─────────────────┘     └─────────────────┘
```

---

## What's Missing (Commercial Readiness Gap)

### 1. Billing & Payments (Critical)
- [ ] Payment processing integration (Stripe recommended)
- [ ] Subscription management (create, upgrade, downgrade, cancel)
- [ ] Checkout flow for plan purchases
- [ ] Customer billing portal access
- [ ] Webhook handling for payment events
- [ ] Invoice generation and history

### 2. Usage Metering & Enforcement
- [ ] Token counting per API request
- [ ] Daily/monthly usage aggregation
- [ ] Real-time quota checks before API calls
- [ ] Overage handling (block, notify, or charge)
- [ ] Usage dashboard for users
- [ ] Usage-based billing support

### 3. Plan Enforcement
- [ ] Gate features by plan tier
- [ ] Model access restrictions (working but not enforced)
- [ ] Rate limit enforcement (structure exists, needs testing)
- [ ] Upgrade prompts when limits reached

### 4. Production Persistence
- [ ] Migrate critical data to PostgreSQL (schema exists in Drizzle)
- [ ] Database backups and recovery
- [ ] Data export functionality

### 5. User Account Features
- [ ] Email verification
- [ ] Password reset flow
- [ ] Account deletion/data export (GDPR)
- [ ] Two-factor authentication

### 6. Admin & Operations
- [ ] Revenue dashboard
- [ ] Subscription management tools
- [ ] Usage analytics
- [ ] Error monitoring and alerting
- [ ] Audit logging for compliance

---

## Billing Integration Design

### Recommended: Stripe Billing

#### Data Model Updates

```typescript
// New fields for User
{
  stripe_customer_id: string | null;
  subscription_id: string | null;
  subscription_status: 'active' | 'past_due' | 'canceled' | 'trialing' | null;
  current_period_end: Date | null;
}

// New table: Subscriptions
{
  id: string;
  user_id: string;
  stripe_subscription_id: string;
  stripe_price_id: string;
  plan: PlanType;
  status: SubscriptionStatus;
  current_period_start: Date;
  current_period_end: Date;
  cancel_at_period_end: boolean;
}

// New table: UsageRecords (enhanced)
{
  id: string;
  user_id: string;
  api_key_id: string;
  date: Date;
  request_count: number;
  token_count: number;
  model: string;
}
```

#### Stripe Products/Prices Mapping

| Plan       | Price/Month | Requests/Month | Models Available        |
|------------|-------------|----------------|-------------------------|
| Free       | $0          | 100            | Llama 3.1 8B            |
| Basic      | $29         | 5,000          | Llama 3.1 8B            |
| Pro        | $99         | 25,000         | All models              |
| Enterprise | Custom      | Unlimited      | All models + priority   |

#### Webhook Events to Handle

- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.payment_succeeded`
- `invoice.payment_failed`

#### User Flows

1. **Checkout**: Pricing page → Stripe Checkout → Webhook updates user plan
2. **Manage Billing**: Dashboard → Stripe Customer Portal
3. **Upgrade**: Dashboard prompt → Stripe Checkout with proration
4. **Cancel**: Customer Portal → Webhook marks subscription canceled

---

## Priority Roadmap

### Phase 1: Billing & Subscriptions (Weeks 1-3)
**Goal**: Users can purchase and manage subscriptions

- [ ] Stripe integration setup
- [ ] Checkout API endpoints
- [ ] Webhook processor
- [ ] Update user plan on successful payment
- [ ] Pricing page with real checkout buttons
- [ ] Dashboard "Manage Billing" button
- [ ] Basic subscription enforcement

### Phase 2: Usage Metering (Weeks 4-5)
**Goal**: Track and enforce usage limits

- [ ] Token counting on AI responses
- [ ] Usage aggregation (daily totals)
- [ ] Quota checking before API calls
- [ ] Usage dashboard UI
- [ ] Overage notifications

### Phase 3: Production Hardening (Weeks 6-7)
**Goal**: Production-ready persistence and monitoring

- [ ] Migrate users/subscriptions to PostgreSQL
- [ ] Database backup strategy
- [ ] Error monitoring (Sentry or similar)
- [ ] Audit logging

### Phase 4: Polish & Growth (Weeks 8+)
**Goal**: Complete user experience

- [ ] Email verification
- [ ] Password reset
- [ ] Team/organization management
- [ ] Invoice history page
- [ ] Usage analytics dashboard
- [ ] Marketing site improvements

---

## API Endpoints Needed for Billing

```
POST /api/billing/create-checkout-session
  - Creates Stripe Checkout session for selected plan
  - Returns checkout URL

POST /api/billing/create-portal-session
  - Creates Stripe Customer Portal session
  - Returns portal URL

POST /api/webhooks/stripe
  - Handles Stripe webhook events
  - Updates user subscription status

GET /api/user/subscription
  - Returns current subscription details
  - Plan, status, usage, limits

GET /api/user/usage
  - Returns usage statistics
  - Current period requests/tokens
  - Remaining quota
```

---

## Environment Variables Needed

```
# Stripe
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_BASIC=price_...
STRIPE_PRICE_PRO=price_...
STRIPE_PRICE_ENTERPRISE=price_...

# Email (for verification/password reset)
SMTP_HOST=...
SMTP_USER=...
SMTP_PASSWORD=...
```

---

## Success Criteria

### MVP Complete When:
1. Users can sign up and start with free tier
2. Users can upgrade to paid plans via Stripe Checkout
3. Usage is tracked and displayed in dashboard
4. Limits are enforced (API returns error when quota exceeded)
5. Users can manage/cancel subscriptions via portal
6. Webhooks reliably sync subscription status

### Production Ready When:
1. All critical data in PostgreSQL with backups
2. Email verification working
3. Password reset working
4. Error monitoring in place
5. Audit logs for compliance
6. Load tested for expected traffic

---

## Notes

- Redis remains suitable for session storage and caching
- PostgreSQL (via Drizzle ORM) for persistent business data
- Consider usage-based billing for enterprise (Stripe Metering)
- Plan for multi-currency support if going international
