# AiAssist Secure - Agency Edition

**Envato CodeCanyon Product Specification**

*The enterprise-grade AI chat infrastructure for agencies who demand total control.*

---

## Product Positioning

**Tagline:** *Own your AI. Own your data. Own your clients.*

**Category:** AI / Chatbots / Customer Support

**Pricing:**
| License | Price | Use Case |
|---------|-------|----------|
| **Regular** | $599 | Single project/client deployment |
| **Extended** | $1,299 | Unlimited clients, white-label, resale rights |

**Target Buyer:** Digital agencies, AI consultancies, SaaS builders, enterprise IT teams

---

## Why This Pricing?

### Regular License ($599)

For developers and small teams deploying for **one end product**:
- Build a chatbot for your own SaaS
- Deploy for a single client project
- Internal business tool

### Extended License ($1,299)

For agencies deploying for **multiple clients** or reselling:
- White-label for unlimited client projects
- Sub-license to clients as part of your service
- Build and sell products that incorporate AiAS
- Agency retainer model (deploy once, bill monthly)

**ROI Math:**
- 3 client deployments @ $599 = $1,797
- Extended license = $1,299
- **Savings: $498** (and unlimited from there)

---

## Competitive Landscape

| Competitor | Price | What You Get | The Gap |
|------------|-------|--------------|---------|
| Magic AI | $69-149 | Script + hosted dependency | No control, vendor lock-in |
| Crisp | $45/seat/mo | SaaS seats | No ownership, ongoing cost |
| Tidio | $29/seat/mo | Basic chatbot | Limited AI, no BYOK |
| **AiAS Regular** | **$599 one-time** | **Full self-hosted** | **Total control** |
| **AiAS Extended** | **$1,299 one-time** | **Unlimited clients** | **Agency scale** |

**Value proposition:** Pay once, own forever. No per-seat fees. No vendor dependency. Your servers, your data, your rules.

---

## What's In The Box (All Licenses)

Both Regular and Extended licenses include **everything**. The only difference is usage scope.

### Core Platform

| Component | Included | Description |
|-----------|----------|-------------|
| React Dashboard | ✅ | Full admin UI with workspace management |
| FastAPI Backend | ✅ | Production-ready API server |
| Multi-Theme System | ✅ | 4 premium themes (Malachi, Athena, Yvette, Patriot) |
| Chat Widget | ✅ | Embeddable widget for client sites |
| Voice Integration | ✅ | Google TTS support (BYOK) |
| WebSocket Real-time | ✅ | Live typing indicators, instant messaging |
| Redis Storage | ✅ | High-performance session/message store |
| PostgreSQL Support | ✅ | Optional advanced persistence |

### AI Capabilities

| Feature | Included | Description |
|---------|----------|-------------|
| BYOK Multi-Provider | ✅ | OpenAI, Anthropic, Groq, Gemini, Mistral |
| Conversation Memory | ✅ | Context-aware responses with memory scopes |
| Workspace Modes | ✅ | AI / Shadow / Takeover switching |
| Shadow Mode | ✅ | AI drafts, humans approve before sending |
| Model Selection | ✅ | Per-workspace model configuration |
| Streaming Responses | ✅ | Real-time token streaming |
| PIN Network Ready | ✅ | Connect to decentralized inference (optional) |

### Agency Features

| Feature | Included | Description |
|---------|----------|-------------|
| White-Label Ready | ✅ | Remove all AiAS branding |
| Multi-Workspace | ✅ | Unlimited workspaces per install |
| Role-Based Access | ✅ | Client, Manager, Admin, Super Admin roles |
| API Key Management | ✅ | Generate keys for programmatic access |
| Contact Management | ✅ | Lead capture and CRM basics |
| Directive System | ✅ | Custom AI behavior per workspace |
| Multi-Tier Approvals | ✅ | Enterprise approval workflows |
| Audit Logging | ✅ | Compliance-ready activity tracking |
| Analytics Dashboard | ✅ | Usage stats, response metrics |

### Developer Tools

| Feature | Included | Description |
|---------|----------|-------------|
| OpenAI-Compatible API | ✅ | Drop-in `/v1/chat/completions` |
| TypeScript SDK | ✅ | `@aiassist-secure/core` |
| React SDK | ✅ | `@aiassist-secure/react` |
| Vanilla JS SDK | ✅ | `@aiassist-secure/vanilla` |
| Python SDK | ✅ | `aiassist-secure` (PyPI) |
| Full Source Code | ✅ | No obfuscation, fully customizable |
| Full Documentation | ✅ | Setup guides, API reference |
| Docker Deployment | ✅ | Production-ready containers |

---

## Technical Requirements

### Minimum Server Specs

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 2 cores | 4+ cores |
| RAM | 4 GB | 8+ GB |
| Storage | 20 GB SSD | 50+ GB SSD |
| OS | Ubuntu 20.04+ | Ubuntu 22.04 LTS |

### Required Services

| Service | Required | Notes |
|---------|----------|-------|
| Redis | ✅ | 6.x+ (can use managed Redis) |
| Node.js | ✅ | 18.x+ |
| Python | ✅ | 3.10+ |
| PostgreSQL | Optional | For advanced persistence |
| Nginx/Caddy | Recommended | Reverse proxy + SSL |

### BYOK Provider Requirements

Buyer supplies their own API keys for any/all of:
- OpenAI (GPT-4, GPT-4o, GPT-3.5)
- Anthropic (Claude 3, Claude 3.5)
- Groq (Llama 3, Mixtral)
- Google (Gemini Pro, Gemini Flash)
- Mistral (Mistral Large, Codestral)

---

## Installation

### Quick Start (5 minutes)

```bash
# Extract and setup
unzip aiassist-secure-agency-edition.zip
cd aiassist-secure

# Configure environment
cp .env.example .env
# Edit .env with your Redis URL and API keys

# Install dependencies
npm install
pip install -r requirements.txt

# Start services
npm run build
npm run start
```

### Docker Deployment (Recommended)

```bash
docker-compose up -d
```

Includes:
- FastAPI backend
- React frontend (pre-built)
- Redis instance
- Nginx reverse proxy
- Auto-SSL with Let's Encrypt

### One-Click Deploy

Supported platforms:
- DigitalOcean App Platform
- Railway
- Render
- AWS Lightsail
- Vultr
- Hetzner

---

## Licensing Terms

### Regular License ($599)

**Permitted:**
- ✅ Deploy on servers you control
- ✅ Modify source code for your needs
- ✅ Create unlimited workspaces
- ✅ Use commercially for **one end product**
- ✅ Integrate with your existing systems

**One End Product Means:**
- Your own SaaS application
- A single client project
- One internal business tool

**Not Permitted:**
- ❌ Deploy for multiple clients (need Extended)
- ❌ Resell or sub-license to others
- ❌ Redistribute source code
- ❌ Create competing marketplace product

---

### Extended License ($1,299)

**Everything in Regular, plus:**
- ✅ Deploy for **unlimited clients**
- ✅ White-label and rebrand completely
- ✅ Sub-license to clients as part of your service
- ✅ Build products that users pay to access
- ✅ Agency retainer model (deploy once, bill ongoing)

**Perfect For:**
- Digital agencies with multiple clients
- Consultancies offering AI solutions
- Managed service providers
- White-label resellers

**Not Permitted:**
- ❌ Resell the source code itself on marketplaces
- ❌ Claim original authorship
- ❌ Remove license file from deployments

---

### Support Included (Both Licenses)

| Support Type | Included | Duration |
|--------------|----------|----------|
| Documentation access | ✅ | Lifetime |
| Bug fix updates | ✅ | 12 months |
| Email support | ✅ | 6 months |
| Priority support | Available | $99/month add-on |
| Custom development | Available | Contact for quote |

### Update Policy

- **Minor updates** (bug fixes, security): Free for 12 months
- **Major updates** (new features): 50% discount for existing buyers
- **Breaking changes**: Migration guides provided

---

## Competitive Comparison

### vs. Magic AI (Envato - 9K+ sales)

| Aspect | Magic AI | AiAS Agency |
|--------|----------|-------------|
| Price | $69-149 | $599-1,299 |
| Self-hosted | Partial (calls home) | ✅ Fully standalone |
| Data ownership | Vendor dependency | ✅ 100% yours |
| BYOK | Limited (1-2 providers) | ✅ 5 providers |
| Shadow mode | ❌ | ✅ Full approval workflows |
| White-label | Partial | ✅ Complete |
| Multi-tenant | ❌ | ✅ Built-in |
| Source code | Obfuscated | ✅ Full access |

**Pitch:** *"Graduated from Magic AI? AiAS is your enterprise upgrade."*

### vs. Crisp (SaaS - $45/seat/mo)

| Aspect | Crisp | AiAS Agency |
|--------|-------|-------------|
| Pricing model | Per-seat recurring | One-time |
| 10 seats × 2 years | $10,800 | $599-1,299 |
| Data location | Their servers | Your servers |
| AI flexibility | Their models only | Any model (BYOK) |
| Customization | Limited config | Full source code |
| Vendor lock-in | High | None |

**Pitch:** *"Stop renting. Own your infrastructure."*

### vs. Intercom (Enterprise)

| Aspect | Intercom | AiAS Agency |
|--------|----------|-------------|
| Entry price | $74/seat/mo | $599 one-time |
| AI cost | Fin @ $0.99/resolution | BYOK (your cost) |
| Annual cost (10 seats) | $8,880+ | $599-1,299 |
| Vendor lock-in | High | None |
| White-label | ❌ | ✅ |
| Self-hosted | ❌ | ✅ |

**Pitch:** *"Intercom power without the enterprise price tag."*

---

## Marketing Assets

### Screenshots Required

1. Dashboard overview (dark theme, Malachi)
2. Chat widget embedded on sample website
3. Shadow mode approval interface
4. Workspace configuration panel
5. API key management screen
6. Theme showcase (all 4 themes in grid)
7. Mobile responsive views
8. Code snippet / SDK usage example

### Demo Video Outline (2-3 min)

| Section | Duration | Content |
|---------|----------|---------|
| Intro | 15s | "Enterprise AI chat you actually own" |
| Dashboard tour | 30s | Workspace creation, navigation |
| Live chat demo | 30s | Real AI conversation |
| Shadow mode | 30s | Show approval workflow in action |
| White-label | 20s | Theme switching, branding removal |
| BYOK setup | 20s | Connect OpenAI API key |
| Deployment | 20s | Docker one-liner, live site |
| CTA | 15s | "Own your AI infrastructure today" |

### Envato Description (HTML)

```html
<h2>Own Your AI. Own Your Data. Own Your Clients.</h2>

<p>AiAssist Secure is the <strong>enterprise-grade AI chat infrastructure</strong> for agencies and developers who demand total control.</p>

<p><strong>9,000+ developers bought Magic AI. But when they needed enterprise features, they came to us.</strong></p>

<h3>Why Teams Choose AiAS</h3>
<ul>
  <li><strong>100% Self-Hosted:</strong> Your servers, your data, zero vendor lock-in</li>
  <li><strong>BYOK (Bring Your Own Key):</strong> Use OpenAI, Anthropic, Groq, Gemini, or Mistral</li>
  <li><strong>Shadow Mode:</strong> AI drafts responses, humans approve before sending</li>
  <li><strong>White-Label Ready:</strong> Remove all branding, deploy for unlimited clients</li>
  <li><strong>Full Source Code:</strong> No obfuscation, completely customizable</li>
  <li><strong>One-Time Price:</strong> No per-seat fees, no recurring costs</li>
</ul>

<h3>Perfect For</h3>
<ul>
  <li>Digital agencies managing multiple client chatbots</li>
  <li>AI consultancies building custom solutions</li>
  <li>SaaS builders adding AI chat to their product</li>
  <li>Enterprise IT teams with data sovereignty requirements</li>
</ul>

<h3>What's Included</h3>
<ul>
  <li>Full React dashboard + FastAPI backend</li>
  <li>4 premium themes (dark/light modes)</li>
  <li>Embeddable chat widget</li>
  <li>TypeScript, React, Vanilla JS, and Python SDKs</li>
  <li>OpenAI-compatible API endpoint</li>
  <li>Docker deployment (one command)</li>
  <li>12 months of updates + 6 months email support</li>
</ul>

<h3>Two Licenses</h3>
<ul>
  <li><strong>Regular ($599):</strong> Single project deployment</li>
  <li><strong>Extended ($1,299):</strong> Unlimited clients, white-label, resale rights</li>
</ul>

<p><strong>Stop renting seats. Start owning infrastructure.</strong></p>
```

---

## Launch Checklist

### Pre-Launch

- [ ] Package source code (exclude .git, node_modules, __pycache__, .env)
- [ ] Create .env.example with all required variables
- [ ] Write installation documentation
- [ ] Record 2-3 min demo video
- [ ] Capture 8 high-quality screenshots
- [ ] Set up support email (support@aiassist.net)
- [ ] Test fresh install on clean Ubuntu server
- [ ] Test Docker deployment end-to-end
- [ ] Verify all 4 themes work correctly
- [ ] Test BYOK with all 5 providers

### Envato Submission

- [ ] Create seller account (if needed)
- [ ] Upload package ZIP (< 500MB)
- [ ] Fill product details completely
- [ ] Set Regular License: $599
- [ ] Set Extended License: $1,299
- [ ] Upload screenshots and video
- [ ] Write description (use HTML above)
- [ ] Set categories: PHP Scripts → AI
- [ ] Add tags: ai, chatbot, openai, claude, self-hosted, white-label
- [ ] Submit for review (1-7 days)

### Post-Launch

- [ ] Monitor first sales and reviews
- [ ] Respond to comments within 24h
- [ ] Track support tickets
- [ ] Request testimonials from buyers
- [ ] Plan first update (30 days post-launch)
- [ ] Create tutorial videos for common questions

---

## Revenue Projections

### Assumptions
- Envato fee: 37.5% (non-exclusive) or 30% (exclusive author tier)
- Mix: 70% Regular, 30% Extended
- Using non-exclusive (37.5%) for conservative estimates

### Conservative (Month 1-3)

| License | Sales/mo | Gross | Net (62.5%) |
|---------|----------|-------|-------------|
| Regular | 8 | $4,792 | $2,995 |
| Extended | 3 | $3,897 | $2,436 |
| **Total** | **11** | **$8,689** | **$5,431** |

### Growth (Month 6-12)

| License | Sales/mo | Gross | Net (62.5%) |
|---------|----------|-------|-------------|
| Regular | 20 | $11,980 | $7,488 |
| Extended | 10 | $12,990 | $8,119 |
| **Total** | **30** | **$24,970** | **$15,607** |

### Optimistic (Month 12+)

| License | Sales/mo | Gross | Net (70%*) |
|---------|----------|-------|------------|
| Regular | 35 | $20,965 | $14,676 |
| Extended | 20 | $25,980 | $18,186 |
| **Total** | **55** | **$46,945** | **$32,862** |

*Exclusive author tier (30% fee)

### Annual Projection (Year 1)

| Scenario | Total Sales | Gross Revenue | Net Revenue |
|----------|-------------|---------------|-------------|
| Conservative | 132 | $104,000 | $65,000 |
| Growth | 250 | $200,000 | $125,000 |
| Optimistic | 400 | $350,000 | $245,000 |

---

## File Structure (Deliverable)

```
aiassist-secure-agency-edition/
├── README.md                    # Getting started guide
├── LICENSE.md                   # License terms
├── CHANGELOG.md                 # Version history
├── .env.example                 # Environment template
├── docker-compose.yml           # One-command deployment
├── docker-compose.prod.yml      # Production config
├── Dockerfile                   # Container build
│
├── client/                      # React frontend
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── themes/              # 4 premium themes
│   │   └── ...
│   ├── public/
│   └── package.json
│
├── api/                         # FastAPI backend
│   ├── routes/
│   ├── services/
│   ├── models/
│   ├── middleware/
│   └── requirements.txt
│
├── packages/                    # Client SDKs
│   ├── typescript/              # @aiassist-secure/core
│   ├── react/                   # @aiassist-secure/react
│   ├── vanilla/                 # @aiassist-secure/vanilla
│   └── python-client/           # aiassist-secure (PyPI)
│
├── docs/
│   ├── installation.md
│   ├── configuration.md
│   ├── deployment.md
│   ├── api-reference.md
│   ├── sdk-usage.md
│   ├── shadow-mode.md
│   ├── theming.md
│   └── troubleshooting.md
│
└── scripts/
    ├── setup.sh                 # Initial setup
    ├── build.sh                 # Build for production
    ├── deploy.sh                # Deploy helpers
    └── backup.sh                # Database backup
```

---

## Success Metrics

### 30 Days
- [ ] 15+ total sales
- [ ] 4.5+ star rating
- [ ] < 5% refund rate
- [ ] Featured in "New Items" or category spotlight

### 90 Days
- [ ] 75+ total sales (~$45K gross)
- [ ] Top 10 in AI/Chatbot category
- [ ] 3+ verified customer testimonials
- [ ] Support response time < 12h average

### 6 Months
- [ ] 150+ total sales (~$100K gross)
- [ ] "Power Elite Author" progress
- [ ] Featured in Envato newsletters
- [ ] Community/Discord with active buyers

### 12 Months
- [ ] 300+ total sales (~$200K+ gross)
- [ ] Elite Author badge
- [ ] Recognized as THE enterprise AI chat on Envato
- [ ] Expansion products (themes, plugins, add-ons)

---

## Future Expansion Products

Once established, create add-on products:

| Product | Price | Description |
|---------|-------|-------------|
| Theme Pack | $49 | 6 additional premium themes |
| Analytics Pro | $99 | Advanced dashboard + reports |
| Mobile App Kit | $149 | React Native chat client |
| Zapier Integration | $79 | Connect 5,000+ apps |
| Training Videos | $49 | 2-hour masterclass |

---

*Document Version: 2.0*  
*Last Updated: January 2026*  
*Author: Interchained / AiAssist Secure Team*
