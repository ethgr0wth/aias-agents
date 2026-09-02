# AiAssist Secure Reseller Program

## Overview

The Reseller Program enables partners to earn revenue by referring new customers to AiAssist Secure. Resellers receive a revenue share on successful conversions and gain free Pro-level platform access while meeting monthly quotas.

**Key Principles:**
- Performance-based access (must meet quotas to maintain free access)
- Revenue share paid only after customer renewal (30+ days)
- Admin-blind isolation (resellers cannot see client data)
- Transparent earnings with real-time dashboards

---

## Business Rules

### Reseller Eligibility & Access

| Rule | Description |
|------|-------------|
| **Role** | `reseller` - distinct from client, manager, super_admin |
| **Platform Access** | Full Pro-level features while quota is met |
| **Client Isolation** | Admin-blind - no access to referred customer resources |
| **First Conversion** | Unlocks full platform access immediately |
| **Quota Failure** | 7-day grace period, then must subscribe to continue |

### Performance Tiers & Revenue Share

Resellers are assigned a performance tier based on monthly conversions. Tier determines both revenue share percentage and platform status.

| Tier | Monthly Conversions | Revenue Share | Status |
|------|---------------------|---------------|--------|
| `starter` | 1-2 | 5% | Active |
| `growth` | 3-10 | 10% | Active |
| `elite` | 10+ | 20% | Active |

**Tier Evaluation:** Recalculated monthly based on confirmed conversions. Tier upgrades apply immediately when threshold is crossed. Downgrades apply at next month start.

Revenue share is calculated on the subscription amount paid by the referred customer.

### Quota Requirements (Ramping Schedule)

| Period | Required Conversions/Month | Notes |
|--------|---------------------------|-------|
| Month 1 | 1 | Onboarding period |
| Month 2 | 1-2 | Ramping up |
| Month 3 | 3 | Building momentum |
| Months 4-5 | 4-5 | Growth phase |
| Months 6-12+ | 6-10 | Mature reseller |

**Partial Month Onboarding:** If a reseller joins mid-month, quota is prorated:
- Days 1-10: Full month quota applies
- Days 11-20: 66% of quota (rounded up)
- Days 21+: 33% of quota (rounded up, minimum 1)

**Grace Period:** If quota is missed at month end, reseller has 7 days to correct. Notification sent on day 1 and day 5 of grace period. After grace period expires, they must subscribe to a paid plan to maintain access.

---

## Conversion Attribution Rules

### What Counts as a Conversion

A conversion is credited to a reseller when ALL conditions are met:

1. **Lead captured** via reseller's smart link, banner, or widget
2. **New customer** - email not already an existing member
3. **Not recycled** - email not already claimed by another reseller
4. **Paid subscription** - customer completes checkout
5. **Renewal confirmed** - customer's subscription renews (30+ days after signup)

### What Does NOT Count

| Scenario | Reason |
|----------|--------|
| Existing member signs up via link | Already a customer |
| Lead already claimed by another reseller | Duplicate prevention |
| Customer cancels before first renewal | No renewal = no credit |
| Customer refunds/chargebacks | Reversed transaction |

### Self-Referral Policy

Self-referrals ARE allowed. If a reseller purchases through their own link:
- They receive revenue share (after 30-day renewal)
- No discount is applied (full price)
- Same renewal requirement applies

---

## Payout System

### 30-Day Rolling Availability

| Event | Timeline |
|-------|----------|
| Customer signs up | Day 0 - Lead converted, pending |
| First billing cycle | Day 0-30 - Monitoring period |
| Customer renews | Day 30+ - Conversion confirmed |
| Funds become claimable | Next payout cycle after renewal |

**Why 30 Days?** Chargebacks and refunds typically occur within the first billing cycle. By requiring renewal before credit, we eliminate chargeback risk entirely.

### Renewal Confirmation (Stripe Integration)

Conversion confirmation is triggered by Stripe webhooks:

```
Webhook: invoice.paid
├── Check if subscription_id matches a pending ConversionEvent
├── Verify billing_period > 1 (not the initial invoice)
├── Update ConversionEvent.status = 'confirmed'
├── Set ConversionEvent.confirmed_at = now()
├── Add share_amount to reseller's available_earnings
└── Increment reseller's monthly conversion count

Webhook: customer.subscription.deleted
├── If within 30 days of ConversionEvent creation
├── Mark ConversionEvent.status = 'reversed'
└── Do NOT credit reseller (no action needed since not yet confirmed)

Webhook: charge.refunded
├── If ConversionEvent is still 'pending'
├── Mark ConversionEvent.status = 'reversed'
└── No earnings adjustment (was never credited)
```

**Admin Override:** If Stripe webhook fails to fire or manual adjustment is needed:
- Admin can mark conversion as confirmed via Reseller Panel
- Requires admin note explaining reason
- Logged in audit trail with override flag

### Payout Method

**USDT on Binance Smart Chain (BEP-20)**
- Reseller provides BSC wallet address
- Minimum payout: $50 USDT
- Processing: Manual admin approval
- Network: BEP-20 (Binance Smart Chain)

*Why USDT only?* Crypto payouts scale globally without regional restrictions. CashApp/PayPal can be added later once volume justifies the manual overhead.

### Payout Workflow

```
1. Reseller views available balance in dashboard
2. Reseller submits payout claim with:
   - Amount to claim
   - BSC wallet address (BEP-20)
3. Claim enters "pending" status
4. Admin reviews claim in Reseller Panel
5. Admin approves/rejects with optional note
6. Both parties see confirmation
7. Admin processes payment externally
8. Admin marks claim as "completed"
9. Transaction logged in audit trail
```

---

## Lead & Referral Tracking

### Smart Link System

Each reseller receives unique referral assets:

```
Referral URL Format:
https://app.aiassist.io/ref/{reseller_code}

Example:
https://app.aiassist.io/ref/JOHN2024
```

**Link Features:**
- Unique per reseller
- Tracks clicks and conversions
- 30-day attribution cookie
- Works on all landing pages

### Smart Banners

Embeddable HTML banners for reseller websites:

```html
<iframe 
  src="https://app.aiassist.io/embed/banner/{reseller_code}" 
  width="728" 
  height="90"
></iframe>
```

**Banner Sizes:**
- Leaderboard: 728x90
- Medium Rectangle: 300x250
- Skyscraper: 160x600

### Embed Widget

JavaScript widget for seamless integration:

```html
<script src="https://app.aiassist.io/widget.js"></script>
<div data-aiassist-widget data-reseller="{reseller_code}"></div>
```

**Widget Features:**
- Branded with AiAssist Secure
- Shows pricing and features
- Direct signup flow
- Attribution tracked automatically

---

## Data Models

### Reseller

```typescript
interface Reseller {
  id: string;
  user_id: string;                    // Links to User
  reseller_code: string;              // Unique referral code
  status: 'active' | 'grace_period' | 'suspended' | 'churned';
  tier: 'starter' | 'growth' | 'elite';  // Based on performance
  onboarded_at: string;               // ISO timestamp
  first_conversion_at: string | null; // When first sale happened
  
  // Payout settings
  payout_method: 'usdt_bsc' | null;
  bsc_wallet_address: string | null;  // BEP-20 wallet for payouts
  
  // Stats (denormalized for quick access)
  total_leads: number;
  total_conversions: number;
  total_earnings: number;
  pending_earnings: number;
  available_earnings: number;
}
```

### ReferralLink

```typescript
interface ReferralLink {
  id: string;
  reseller_id: string;
  code: string;                       // Short code for URL
  type: 'link' | 'banner' | 'widget';
  label: string;                      // Reseller's custom label
  clicks: number;
  leads: number;
  conversions: number;
  created_at: string;
  active: boolean;
}
```

### Lead

```typescript
interface Lead {
  id: string;
  reseller_id: string;
  referral_link_id: string;
  email: string;                      // Raw for admin, consider hashing
  email_hash: string;                 // For duplicate detection
  source_url: string;                 // Where they came from
  ip_hash: string;                    // Fraud detection
  status: 'captured' | 'signed_up' | 'subscribed' | 'renewed' | 'churned';
  captured_at: string;
  signed_up_at: string | null;
  subscribed_at: string | null;
  renewed_at: string | null;
  user_id: string | null;             // Links to User after signup
}
```

### ConversionEvent

```typescript
interface ConversionEvent {
  id: string;
  reseller_id: string;
  lead_id: string;
  user_id: string;                    // Converted customer
  subscription_id: string;            // Stripe subscription
  
  // Financial
  revenue_amount: number;             // What customer paid
  share_percentage: number;           // 5%, 10%, or 20%
  share_amount: number;               // Reseller's cut
  
  // Status
  status: 'pending' | 'confirmed' | 'paid' | 'reversed';
  
  // Timestamps
  subscribed_at: string;
  renewal_due_at: string;             // When renewal expected
  confirmed_at: string | null;        // When renewal happened
  paid_at: string | null;             // When reseller was paid
  
  // Audit
  billing_period: number;             // Which billing cycle
}
```

### MonthlyQuota

```typescript
interface MonthlyQuota {
  id: string;
  reseller_id: string;
  month: string;                      // YYYY-MM format
  
  // Targets
  required_conversions: number;       // Based on tenure
  achieved_conversions: number;
  
  // Status
  status: 'in_progress' | 'met' | 'grace_period' | 'failed';
  grace_period_ends_at: string | null;
  
  // Timestamps
  evaluated_at: string | null;
}
```

### PayoutClaim

```typescript
interface PayoutClaim {
  id: string;
  reseller_id: string;
  
  // Claim details
  amount: number;
  method: 'usdt_bsc';
  bsc_wallet_address: string;         // BEP-20 wallet address
  
  // Status
  status: 'pending' | 'approved' | 'rejected' | 'completed';
  
  // Admin handling
  reviewed_by: string | null;         // Admin user_id
  reviewed_at: string | null;
  admin_note: string | null;
  
  // Audit
  created_at: string;
  completed_at: string | null;
  transaction_hash: string | null;    // For crypto payments
}
```

---

## API Endpoints

### Public (Referral Tracking)

```
GET  /ref/{reseller_code}              -> Redirect to signup with attribution
GET  /embed/banner/{reseller_code}     -> Render banner HTML
GET  /api/widget/{reseller_code}       -> Widget configuration
POST /api/leads/capture                -> Capture lead (email + reseller attribution)
```

### Reseller Dashboard

```
GET  /api/reseller/profile             -> Get reseller profile & stats
GET  /api/reseller/links               -> List referral links
POST /api/reseller/links               -> Create new referral link
GET  /api/reseller/leads               -> List captured leads
GET  /api/reseller/conversions         -> List conversions & earnings
GET  /api/reseller/quota               -> Current quota status
GET  /api/reseller/earnings            -> Earnings breakdown
POST /api/reseller/payout/claim        -> Submit payout claim
GET  /api/reseller/payout/history      -> Payout history
PUT  /api/reseller/payout/settings     -> Update payout method/address
```

### Admin Reseller Panel

```
GET  /api/admin/resellers              -> List all resellers
GET  /api/admin/resellers/{id}         -> Reseller detail with leads/conversions
GET  /api/admin/resellers/{id}/leads   -> All leads for reseller
GET  /api/admin/resellers/{id}/conversions -> All conversions
GET  /api/admin/reseller-stats         -> Aggregate stats
GET  /api/admin/payout-claims          -> List pending payout claims
PUT  /api/admin/payout-claims/{id}     -> Approve/reject claim
POST /api/admin/payout-claims/{id}/complete -> Mark as completed
```

---

## Dashboards

### Reseller Dashboard

**Stats Overview:**
- Total Leads Captured
- Total Conversions (confirmed)
- Pending Conversions (awaiting renewal)
- Current Month Progress (X/Y quota)
- Revenue Share Tier (5%/10%/20%)

**Earnings Panel:**
- Pending Earnings (awaiting renewal)
- Available Balance (claimable)
- Total Paid Out (lifetime)
- Claim Payout button

**Referral Assets:**
- List of smart links with stats
- Banner embed codes
- Widget embed code
- Create new link button

**Leads & Conversions Table:**
- Lead email (partial masked)
- Capture date
- Status (captured/signed up/subscribed/renewed)
- Revenue & share amount

### Admin Reseller Panel

**Overview Cards:**
- Total Active Resellers
- Total Pending Payouts
- This Month's Conversions
- Total Revenue via Resellers

**Reseller Table:**
- Reseller name/email
- Status (active/grace/suspended)
- Leads / Conversions / Earnings
- Current quota status
- Actions (view detail, suspend)

**Payout Queue:**
- Pending claims list
- Reseller name
- Amount requested
- BSC wallet address
- Approve / Reject buttons
- Mark Complete button

**Conversion Audit Log:**
- All conversions with reseller attribution
- Stripe subscription links
- Renewal status
- Revenue share calculations

---

## Security Considerations

### Access Control
- Resellers have role `reseller` in RBAC system
- Cannot access any client workspaces, API keys, or data
- Can only see their own leads and conversions
- Admin can see all reseller data

### Lead Protection
- Store raw emails for admin reporting
- Hash emails for duplicate detection across resellers
- IP hashing for fraud detection
- Never expose other resellers' leads

### Payout Security
- Validate BSC addresses (EIP-55 checksum verification)
- Require admin approval for all payouts
- Immutable audit log for all claims
- Confirmation on both reseller and admin dashboards

### Attribution Integrity
- Signed referral links (prevent tampering)
- 30-day attribution window (cookie-based)
- First-touch attribution (first reseller wins)
- Immutable conversion events (no backdating)

---

## Implementation Phases

### Phase 1: Foundation (Week 1-2)
- [ ] Create data models in schemas
- [ ] Implement Redis storage functions
- [ ] Build reseller registration flow
- [ ] Create referral link generation

### Phase 2: Tracking (Week 2-3)
- [ ] Implement smart link redirect handler
- [ ] Build lead capture endpoint
- [ ] Add duplicate detection (existing members, claimed leads)
- [ ] Hook Stripe webhook for conversion tracking

### Phase 3: Earnings (Week 3-4)
- [ ] Implement renewal detection (30-day confirmation)
- [ ] Build revenue share calculator (tier-based)
- [ ] Create monthly quota evaluator
- [ ] Implement grace period logic

### Phase 4: Payouts (Week 4-5)
- [ ] Build payout claim submission
- [ ] Create admin approval workflow
- [ ] Add confirmation notifications
- [ ] Implement payout history

### Phase 5: Dashboards (Week 5-6)
- [ ] Build reseller dashboard UI
- [ ] Create admin reseller panel
- [ ] Add real-time stats updates
- [ ] Implement referral asset management

### Phase 6: Marketing Assets (Week 6-7)
- [ ] Create embeddable banner system
- [ ] Build JavaScript widget
- [ ] Add banner size variants
- [ ] Create asset preview for resellers

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Reseller activation rate | >60% complete first conversion |
| Average conversions/reseller | 3-5/month |
| Reseller retention (6 months) | >40% |
| Payout claim success rate | >95% |
| Lead-to-conversion rate | >10% |

---

## Open Questions

1. **Reseller onboarding** - Self-signup or admin invitation only?
2. **Minimum payout threshold** - $50 USDT as proposed?
3. **Quota ramp customization** - Fixed schedule or performance-based?
4. **Multi-tier products** - Different share rates for different plans?
5. **Reseller support** - Dedicated channel or standard support?

---

## Changelog

| Date | Change |
|------|--------|
| 2024-12-28 | Initial specification created |
