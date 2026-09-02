---
title: Platform Architecture
icon: Network
category: Architecture
order: 1
description: Overview of the AiAssist infrastructure and licensing model.
---

# AiAssist Architecture & Licensing

## System Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                         FREE / PRO TIER                              │
│  ┌─────────────┐     ┌─────────────────────────────────────────┐    │
│  │ Customer    │     │         AiAssist HQ                     │    │
│  │ Website     │────▶│  api.aiassist.net                       │    │
│  │ (Widget)    │     │  ┌─────────┐ ┌─────────┐ ┌───────────┐  │    │
│  └─────────────┘     │  │ Rate    │ │ AI      │ │ Redis     │  │    │
│                      │  │ Limiter │ │ Engine  │ │ Storage   │  │    │
│  ┌─────────────┐     │  └─────────┘ └─────────┘ └───────────┘  │    │
│  │ Admin       │────▶│                                         │    │
│  │ Dashboard   │     │  admin.aiassist.net (Proprietary)       │    │
│  └─────────────┘     └─────────────────────────────────────────┘    │
18: └──────────────────────────────────────────────────────────────────────┘
19: 
20: ┌──────────────────────────────────────────────────────────────────────┐
21: │                      ENTERPRISE TIER (Licensed)                      │
22: │  ┌─────────────┐     ┌─────────────────────────────────────────┐    │
23: │  │ Customer    │     │       Customer's Infrastructure         │    │
24: │  │ Website     │────▶│  ┌─────────────────────────────────┐    │    │
25: │  │ (Widget)    │     │  │  AiAssist Python Server SDK     │    │    │
26: │  └─────────────┘     │  │  (License Key Required)         │    │    │
27: │                      │  │  ┌─────────┐ ┌───────────────┐  │    │    │
28: │  ┌─────────────┐     │  │  │ AI      │ │ Their Redis   │  │    │    │
29: │  │ Admin       │────▶│  │  │ Engine  │ │ Their Groq    │  │    │    │
30: │  │ Dashboard   │     │  │  └─────────┘ └───────────────┘  │    │    │
31: │  │ (Licensed)  │     │  └─────────────────────────────────┘    │    │
32: │  └─────────────┘     └─────────────────────────────────────────┘    │
33: │                                     │                                │
34: │                                     │ Telemetry / License Validation │
35: │                                     ▼                                │
36: │                      ┌─────────────────────────────────────────┐    │
37: │                      │  license.aiassist.net                   │    │
38: │                      │  (Usage tracking, billing, key checks)  │    │
39: │                      └─────────────────────────────────────────┘    │
40: └──────────────────────────────────────────────────────────────────────┘
```

## Tier Breakdown

### Free Tier
- **Widget**: Open source, MIT licensed
- **Backend**: Routes to `api.aiassist.net` (required)
- **Admin Dashboard**: Hosted at `admin.aiassist.net`
- **Limits**: 100 conversations/month, basic features
- **Data**: Stored on AiAssist infrastructure
- **Cannot self-host**

### Pro Tier ($49-149/month)
- Everything in Free, plus:
- **Higher limits**: 5,000-25,000 conversations/month
- **Human takeover**: Full admin features
- **Typing preview**: Real-time monitoring
- **Custom branding**: Remove "Powered by AiAssist"
- **Webhooks**: CRM integrations
- **Still routes through HQ** - cannot self-host

### Enterprise Tier (Custom Pricing)
- **License required**: Contact sales@aiassist.net
- **Self-hosted option**: Run on your infrastructure
- **Full SDK access**: Python server + Admin dashboard components
- **Your data, your control**: Redis, Groq key, everything yours
- **License key validation**: SDK phones home for license check
- **Usage telemetry**: Required for billing reconciliation
- **Annual contracts**: Minimum commitment
- **SLA & Support**: Dedicated account manager

---

## Why HQ Routing is Required (Free/Pro)

### 1. Rate Limiting
```
Client Widget → api.aiassist.net → Rate limit check → AI response
                      ↓
              If over limit: 429 Too Many Requests
```
Without HQ routing, users could bypass rate limits entirely.

### 2. Usage Tracking
Every API call is logged for:
- Billing (per-conversation pricing)
- Analytics dashboard
- Fair use enforcement

### 3. Admin Dashboard Access
The admin dashboard (`admin.aiassist.net`) is proprietary SaaS:
- Real-time conversation monitoring
- Typing preview (see what customers type before sending)
- Human takeover controls
- Directive injection
- Analytics & reporting

This is NOT open-sourced. It's a key differentiator.

### 4. Model Access
- Free tier: Limited to smaller models
- Pro tier: Access to Llama 3.3 70B
- We proxy Groq calls - users don't need API keys

---

## SDK Component Licensing

| Component | License | Available To |
|-----------|---------|--------------|
| `@aiassist/react` (Widget) | MIT | Everyone |
| `@aiassist/vanilla` (Widget) | MIT | Everyone |
| `@aiassist/react/admin` | Proprietary | Enterprise only |
| `aiassist` (Python SDK - Client) | MIT | Everyone |
| `aiassist` (Python SDK - Server) | Proprietary | Enterprise only |

### What "MIT Licensed" Means Here
The client widgets are open source, but they're designed to connect to HQ:

```javascript
// Default behavior (cannot be changed in free SDK)
AiAssist.init({
  apiKey: 'your-key',
  // endpoint is hardcoded to api.aiassist.net
});
```

Enterprise SDK unlocks:
```javascript
AiAssist.init({
  licenseKey: 'enterprise-license',
  endpoint: 'https://your-own-server.com/api'
});
```

---

## License Key System

### How It Works
```
┌─────────────────┐         ┌──────────────────────┐
│  Enterprise     │ ──────▶ │ license.aiassist.net │
│  Python Server  │         │                      │
│                 │ ◀────── │ Valid: true          │
│  License: xxx   │         │ Expires: 2025-12-31  │
│  License: xxx   │         │ Features: [...]      │
└─────────────────┘         └──────────────────────┘
```

### License Validation
- Checked on server startup
- Re-validated every 24 hours
- Grace period: 7 days if license server unreachable
- Telemetry: conversation counts, API calls (for billing)

### What Happens Without Valid License
```python
from aiassist import AiAssistRouter

# Without license - connects to HQ (free tier behavior)
router = AiAssistRouter(config)  

# With enterprise license - full self-hosted
router = AiAssistRouter(config, license_key="ent_xxx")
```

---

## Data Flow Comparison

### Free/Pro (Managed)
```
Customer → Widget → api.aiassist.net → Groq → Response
                          ↓
              Admin dashboard sees everything
              Usage tracked, rate limited
```

### Enterprise (Self-Hosted)
```
Customer → Widget → your-server.com → Your Groq Key → Response
                          ↓
              Your admin dashboard
              Your Redis storage
              License telemetry → license.aiassist.net
```

---

## Enterprise Onboarding Process

1. **Contact Sales**: sales@aiassist.net
2. **Needs Assessment**: Usage estimates, compliance requirements
3. **Contract**: Annual commitment, custom pricing
4. **License Issued**: Enterprise license key generated
5. **Onboarding**: Dedicated support for self-hosted setup
6. **Go Live**: License key activates full SDK
7. **Quarterly Reviews**: Usage reconciliation, renewals

---

## Security & Compliance

### Free/Pro
- Data stored in US/EU (choice during signup)
- SOC 2 Type II compliant infrastructure
- Encrypted at rest and in transit
- 30-day data retention (configurable on Pro)

### Enterprise
- Full data sovereignty - your infrastructure
- Compliance is your responsibility
- We provide: Security guidelines, best practices
- Optional: Security review add-on service

---

## Summary

| Feature | Free | Pro | Enterprise |
|---------|------|-----|------------|
| Widget SDK | ✅ | ✅ | ✅ |
| Routes through HQ | Required | Required | Optional |
| Admin Dashboard | Hosted | Hosted | Self-hosted |
| Self-hosted Backend | ❌ | ❌ | ✅ |
| License Key | ❌ | ❌ | Required |
| BYOK (Groq key) | ❌ | ✅ (proxied) | ✅ (direct) |
| Rate Limits | 100/mo | 5k-25k/mo | Unlimited |
| Support | Community | Email | Dedicated |
| Contract | None | Monthly | Annual |
