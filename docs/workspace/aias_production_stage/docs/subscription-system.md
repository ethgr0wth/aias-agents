# Subscription System Work Plan

## Overview

This document outlines the architecture and implementation plan for a complete subscription management system that integrates with the existing licensing infrastructure and prepares for Stripe payment processing.

---

## 1. Current State Analysis

### What We Have
- **License keys** with `duration_days` field
- **Plan types**: free, basic, pro, enterprise
- **License activation** that sets `expires_at` based on duration
- **Batch generation** for bulk license creation
- **Organization/seat management** for team licenses

### What's Missing
- **Subscription lifecycle management** (active → grace period → expired → cancelled)
- **Background workers** for automated expiration/renewal processing
- **Notification system** for expiration warnings
- **Payment integration** for automated billing
- **Subscription status API** for real-time status checks

---

## 2. Subscription Lifecycle

### 2.1 Subscription States

```
┌─────────────┐
│   PENDING   │ ← License created but not activated
└──────┬──────┘
       │ activate
       ▼
┌─────────────┐
│   ACTIVE    │ ← User has full access
└──────┬──────┘
       │ expires_at - 7 days
       ▼
┌─────────────┐
│   WARNING   │ ← Expiration warning sent
└──────┬──────┘
       │ expires_at reached
       ▼
┌─────────────┐
│   GRACE     │ ← 7-day grace period (limited access)
└──────┬──────┘
       │ grace period ends OR payment fails
       ▼
┌─────────────┐
│   EXPIRED   │ ← No access, can reactivate
└──────┬──────┘
       │ manual cancel
       ▼
┌─────────────┐
│  CANCELLED  │ ← User cancelled, no renewal
└─────────────┘
```

### 2.2 State Transitions

| From | To | Trigger | Action |
|------|-----|---------|--------|
| PENDING | ACTIVE | License activation | Set expires_at, start access |
| ACTIVE | WARNING | 7 days before expiry | Send warning email |
| ACTIVE | GRACE | expires_at reached | Limit features, send notice |
| WARNING | GRACE | expires_at reached | Same as above |
| GRACE | EXPIRED | grace_period_end | Revoke access |
| GRACE | ACTIVE | Payment received | Extend expires_at |
| EXPIRED | ACTIVE | New payment/license | Reactivate subscription |
| ANY | CANCELLED | User cancels | Stop auto-renewal |

### 2.3 License/Seat/Organization Synchronization

**Critical**: Subscription state changes MUST update related entities to maintain access control integrity.

#### State Transition Side Effects

| Transition | License Update | Seat Update | Organization Update |
|------------|----------------|-------------|---------------------|
| PENDING → ACTIVE | Set `status=active`, `activated_at`, `expires_at` | Mark all seats as `active` | Set `status=active` |
| ACTIVE → GRACE | Set `status=grace` | Keep seats active (limited features) | Set `status=grace` |
| GRACE → EXPIRED | Set `status=expired` | Set all seats to `suspended` | Set `status=suspended` |
| GRACE → ACTIVE | Set `status=active`, extend `expires_at` | Restore all seats to `active` | Set `status=active` |
| ANY → CANCELLED | Set `status=cancelled`, `cancelled_at` | Set all seats to `revoked` | Set `status=cancelled` |

#### Synchronization Function

```python
def sync_subscription_state(
    subscription: Subscription,
    new_status: str,
    pipe=None,
    new_expires_at: str = None,
    plan_code: str = None
):
    """
    Atomically update subscription and all related entities.
    Uses Redis pipeline for atomic multi-key updates.
    
    IMPORTANT: Pass explicit new_expires_at and plan_code when extending
    subscriptions to ensure all entities get updated values, not stale
    snapshot data from the subscription object.
    
    Args:
        subscription: The subscription object (may have stale data)
        new_status: The new status to set
        pipe: Optional Redis pipeline for batching
        new_expires_at: Updated expires_at (use for renewals/extensions)
        plan_code: Explicit plan code (use when plan should be preserved)
    """
    use_pipe = pipe is not None
    if not use_pipe:
        pipe = redis.pipeline()
    
    # Use explicit values if provided, otherwise fall back to subscription
    effective_expires = new_expires_at or subscription.expires_at
    effective_plan = plan_code or subscription.plan_code
    
    # Determine if plan should be preserved (active access states)
    preserves_plan = new_status in ["active", "warning"]
    entitlement_plan = effective_plan if preserves_plan else "none"
    
    # 1. Update subscription hash
    pipe.hset(f"subscription:{subscription.id}", "status", new_status)
    if new_expires_at:
        pipe.hset(f"subscription:{subscription.id}", "expires_at", new_expires_at)
    
    # 2. Update license hash with same status AND expires_at
    license_key = f"license:{subscription.license_id}"
    license_updates = {"status": new_status}
    if new_expires_at:
        license_updates["expires_at"] = new_expires_at
    pipe.hset(license_key, mapping=license_updates)
    
    # 3. Update organization if exists
    if subscription.org_id:
        org_status = "active" if new_status in ["active", "warning"] else new_status
        pipe.hset(f"org:{subscription.org_id}", "status", org_status)
        
        # 4. Update all seats for this organization
        seat_ids = redis.smembers(f"org:{subscription.org_id}:seats")
        seat_status = get_seat_status_for_subscription(new_status)
        for seat_id in seat_ids:
            pipe.hset(f"seat:{seat_id}", "status", seat_status)
    
    # 5. Update user entitlements cache with fresh values
    pipe.hset(f"user:{subscription.user_id}:entitlements", mapping={
        "plan": entitlement_plan,  # Preserved for active/warning states
        "subscription_status": new_status,
        "expires_at": effective_expires
    })
    
    if not use_pipe:
        pipe.execute()

def get_seat_status_for_subscription(sub_status: str) -> str:
    """Map subscription status to seat status."""
    return {
        "active": "active",
        "warning": "active",  # Keep seats active during warning
        "grace": "active",    # Keep seats during grace (limited features)
        "expired": "suspended",
        "cancelled": "revoked"
    }.get(sub_status, "suspended")
```

#### Access Check Integration

Every API request must verify current subscription status:

```python
def check_access(user_id: str, required_plan: str = None) -> bool:
    """
    Fast access check using cached entitlements.
    
    Status behavior:
    - active: Full access, plan checks apply
    - warning: Full access (expiring soon), plan checks apply
    - grace: Limited access (payment failed), plan checks may fail
    - expired/cancelled: No access
    """
    entitlements = redis.hgetall(f"user:{user_id}:entitlements")
    
    if not entitlements:
        return False
    
    status = entitlements.get("subscription_status")
    user_plan = entitlements.get("plan", "free")
    
    # Active and warning states have full access
    if status in ["active", "warning"]:
        if required_plan:
            # Plan is preserved for both active and warning states
            return plan_includes(user_plan, required_plan)
        return True
    
    # Grace period = limited access (e.g., read-only, no new features)
    if status == "grace":
        # Could implement limited feature set here
        # For now, deny access to gated features during grace
        return False
    
    # Expired, cancelled, or unknown = no access
    return False

def plan_includes(user_plan: str, required_plan: str) -> bool:
    """Check if user's plan includes the required plan level."""
    plan_hierarchy = {
        "free": 0,
        "basic": 1,
        "pro": 2,
        "enterprise": 3
    }
    user_level = plan_hierarchy.get(user_plan, 0)
    required_level = plan_hierarchy.get(required_plan, 0)
    return user_level >= required_level
```

---

## 3. Redis Data Structures

### 3.1 Subscription Record
```
Key: subscription:{subscription_id}
Type: HASH
Fields:
  - id: string (UUID)
  - user_id: string
  - org_id: string (optional)
  - license_id: string
  - plan_code: string (free|basic|pro|enterprise)
  - status: string (pending|active|warning|grace|expired|cancelled)
  - status_reason: string (optional - "payment_failed"|"manual_revoke"|"expired"|"cancelled_by_user")
  - started_at: string (ISO timestamp)
  - expires_at: string (ISO timestamp)
  - grace_ends_at: string (ISO timestamp, expires_at + 7 days)
  - stripe_subscription_id: string (optional, for Stripe sync)
  - stripe_customer_id: string (optional)
  - auto_renew: string (true|false)
  - last_payment_at: string (ISO timestamp)
  - next_billing_at: string (ISO timestamp)
  - cancelled_at: string (ISO timestamp, optional)
```

### 3.2 Expiration Tracking (Sorted Set)
```
Key: subscriptions:expiring
Type: ZSET
Score: Unix timestamp of expires_at
Member: subscription_id

Purpose: Efficiently query subscriptions expiring in a time range
Example: ZRANGEBYSCORE subscriptions:expiring {now} {now + 7 days}
```

### 3.3 Grace Period Tracking (Sorted Set)
```
Key: subscriptions:grace_ending
Type: ZSET
Score: Unix timestamp of grace_ends_at
Member: subscription_id

Purpose: Track grace period expirations for final revocation
```

### 3.4 Subscription Events Stream
```
Key: subscription:events
Type: STREAM
Fields per entry:
  - event_type: string (activated|renewed|expired|cancelled|payment_failed|warning_sent)
  - subscription_id: string
  - user_id: string
  - plan_code: string
  - timestamp: string
  - metadata: JSON string (additional event data)

Purpose: Audit log and event-driven processing
```

### 3.5 User → Subscription Index
```
Key: user:{user_id}:subscription
Type: STRING
Value: subscription_id

Purpose: Quick lookup of user's active subscription
```

---

## 4. Background Workers

### 4.1 Worker Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    WORKER SCHEDULER                          │
│  (Redis-based distributed locks prevent duplicate runs)     │
└─────────────────────────────────────────────────────────────┘
        │              │                │              │
        ▼              ▼                ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  EXPIRATION  │ │  GRACE       │ │ NOTIFICATION │ │   RENEWAL    │
│   CHECKER    │ │  PROCESSOR   │ │   SENDER     │ │  PROCESSOR   │
│              │ │              │ │              │ │              │
│ Runs: 1/hour │ │ Runs: 1/hour │ │ Runs: 1/day  │ │ Runs: 1/hour │
└──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘
```

### 4.2 Expiration Checker Worker

**Purpose**: Move subscriptions from ACTIVE/WARNING to GRACE when expires_at is reached

**Frequency**: Every hour

**Important Implementation Notes**:
- Always parse ISO strings to datetime objects before comparison
- Use `sync_subscription_state()` to update all related entities atomically
- ZSET scores must be Unix timestamps (floats), not ISO strings

**Logic**:
```python
from datetime import datetime, timedelta
from dateutil.parser import isoparse  # Proper ISO parsing

def parse_iso_datetime(iso_string: str) -> datetime:
    """Parse ISO string to datetime. Handle None/empty gracefully."""
    if not iso_string:
        return None
    return isoparse(iso_string)

def check_expirations():
    now = datetime.utcnow()
    now_ts = now.timestamp()
    
    # Find subscriptions that just expired (score <= now)
    expired_ids = redis.zrangebyscore(
        "subscriptions:expiring",
        "-inf",
        now_ts
    )
    
    for sub_id in expired_ids:
        subscription = get_subscription(sub_id)
        
        # Double-check expiration with proper datetime parsing
        expires_at = parse_iso_datetime(subscription.expires_at)
        if expires_at and expires_at > now:
            # Not actually expired yet, skip (ZSET score mismatch)
            continue
        
        if subscription.status in ["active", "warning"]:
            # Move to grace period
            grace_ends = now + timedelta(days=GRACE_PERIOD_DAYS)
            
            # Use pipeline for atomic updates
            pipe = redis.pipeline()
            
            # Update subscription and sync all related entities
            pipe.hset(f"subscription:{sub_id}", mapping={
                "status": "grace",
                "grace_ends_at": grace_ends.isoformat()
            })
            
            # Sync license, org, seats atomically
            sync_subscription_state(subscription, "grace", pipe)
            
            # Add to grace tracking ZSET with Unix timestamp
            pipe.zadd("subscriptions:grace_ending", {
                sub_id: grace_ends.timestamp()
            })
            
            # Remove from expiring set
            pipe.zrem("subscriptions:expiring", sub_id)
            
            # Execute all updates atomically
            pipe.execute()
            
            # Log event (after successful update)
            log_subscription_event("entered_grace", sub_id)
            
            # Queue notification
            queue_notification(subscription.user_id, "grace_period_started")
        else:
            # Already processed, just clean up ZSET
            redis.zrem("subscriptions:expiring", sub_id)
```

### 4.3 Grace Period Processor Worker

**Purpose**: Expire subscriptions when grace period ends

**Frequency**: Every hour

**Logic**:
```python
def process_grace_periods():
    now = datetime.utcnow()
    now_ts = now.timestamp()
    
    # Find grace periods that ended
    ended_ids = redis.zrangebyscore(
        "subscriptions:grace_ending",
        "-inf",
        now_ts
    )
    
    for sub_id in ended_ids:
        subscription = get_subscription(sub_id)
        
        if subscription.status == "grace":
            # Parse timestamps properly for comparison
            last_payment = parse_iso_datetime(subscription.last_payment_at)
            expires_at = parse_iso_datetime(subscription.expires_at)
            
            # Check if payment came in after original expiration
            if last_payment and expires_at and last_payment > expires_at:
                # Payment received, reactivate
                reactivate_subscription(sub_id)
            else:
                # No payment, expire and sync all entities
                pipe = redis.pipeline()
                pipe.hset(f"subscription:{sub_id}", "status", "expired")
                sync_subscription_state(subscription, "expired", pipe)
                pipe.zrem("subscriptions:grace_ending", sub_id)
                pipe.execute()
                
                log_subscription_event("expired", sub_id)
                queue_notification(subscription.user_id, "subscription_expired")
        else:
            # Already processed, just clean up ZSET
            redis.zrem("subscriptions:grace_ending", sub_id)
```

### 4.4 Notification Sender Worker

**Purpose**: Send expiration warnings and reminders

**Frequency**: Daily

**Important**: Uses TTL guard to prevent spamming users with duplicate warnings.

**Logic**:
```python
WARNING_SENT_TTL = 7 * 24 * 60 * 60  # 7 days - only warn once per cycle

def send_notifications():
    now = datetime.utcnow()
    now_ts = now.timestamp()
    warning_threshold = now + timedelta(days=7)
    
    # Find subscriptions expiring in next 7 days
    expiring_soon = redis.zrangebyscore(
        "subscriptions:expiring",
        now_ts,
        warning_threshold.timestamp()
    )
    
    for sub_id in expiring_soon:
        try:
            # Check if warning already sent this cycle (TTL guard)
            warning_key = f"subscription:{sub_id}:warning_sent"
            if redis.exists(warning_key):
                continue  # Already warned, skip
            
            subscription = get_subscription(sub_id)
            
            if subscription.status == "active":
                # Parse expires_at string to datetime for arithmetic
                expires_at = parse_iso_datetime(subscription.expires_at)
                if not expires_at:
                    continue
                
                # Calculate days remaining
                days_left = (expires_at - now).days
                
                # Update to warning status while preserving plan
                pipe = redis.pipeline()
                pipe.hset(f"subscription:{sub_id}", "status", "warning")
                # Set TTL guard to prevent duplicate warnings
                pipe.set(warning_key, "1", ex=WARNING_SENT_TTL)
                sync_subscription_state(
                    subscription,
                    "warning",
                    pipe,
                    plan_code=subscription.plan_code
                )
                pipe.execute()
                
                # Queue warning notification
                queue_notification(
                    subscription.user_id,
                    "expiration_warning",
                    {"days_remaining": days_left}
                )
                
                log_subscription_event("warning_sent", sub_id)
        
        except Exception as e:
            # Per-subscription error isolation - don't let one bad record stall the batch
            logger.error(f"Failed to process warning for {sub_id}: {e}")
            continue
```

### 4.5 Renewal Processor Worker

**Purpose**: Process auto-renewals via Stripe (post-integration)

**Frequency**: Every hour

**Logic**:
```python
def process_renewals():
    now = datetime.utcnow()
    renewal_window = now + timedelta(days=3)  # Attempt 3 days before expiry
    
    # Find subscriptions due for renewal
    due_for_renewal = redis.zrangebyscore(
        "subscriptions:expiring",
        now.timestamp(),
        renewal_window.timestamp()
    )
    
    for sub_id in due_for_renewal:
        subscription = get_subscription(sub_id)
        
        if subscription.auto_renew and subscription.stripe_subscription_id:
            try:
                # Stripe handles the actual charge
                # We just verify the subscription is still valid
                stripe_sub = stripe.Subscription.retrieve(
                    subscription.stripe_subscription_id
                )
                
                if stripe_sub.status == "active":
                    # Extend our subscription
                    extend_subscription(sub_id, days=30)  # or billing period
                    log_subscription_event("renewed", sub_id)
                    
            except stripe.error.StripeError as e:
                log_subscription_event("renewal_failed", sub_id, {"error": str(e)})
                queue_notification(subscription.user_id, "payment_failed")
```

### 4.6 Distributed Lock Pattern

To prevent duplicate worker runs in a multi-instance environment:

```python
WORKER_LOCK_TTL = 300  # 5 minutes

def acquire_worker_lock(worker_name: str) -> bool:
    lock_key = f"worker:lock:{worker_name}"
    return redis.set(lock_key, "locked", nx=True, ex=WORKER_LOCK_TTL)

def release_worker_lock(worker_name: str):
    redis.delete(f"worker:lock:{worker_name}")

def run_worker(worker_name: str, worker_func):
    if not acquire_worker_lock(worker_name):
        logger.info(f"Worker {worker_name} already running, skipping")
        return
    
    try:
        worker_func()
    finally:
        release_worker_lock(worker_name)
```

### 4.7 Subscription Extension Function

**Critical**: This function must update BOTH the subscription hash AND the expiration ZSET atomically.

```python
def extend_subscription(sub_id: str, days: int, billing_period_days: int = None):
    """
    Extend a subscription by the specified number of days.
    Updates hash fields AND ZSET scores atomically.
    """
    subscription = get_subscription(sub_id)
    
    # Calculate new expiration from current expires_at (not from now)
    current_expires = parse_iso_datetime(subscription.expires_at)
    if not current_expires or current_expires < datetime.utcnow():
        # Already expired, extend from now
        current_expires = datetime.utcnow()
    
    new_expires = current_expires + timedelta(days=days)
    new_expires_ts = new_expires.timestamp()
    
    # Calculate next billing date if applicable
    next_billing = None
    if billing_period_days:
        next_billing = new_expires - timedelta(days=3)  # Bill 3 days before expiry
    
    pipe = redis.pipeline()
    
    # 1. Update subscription hash
    updates = {
        "status": "active",
        "expires_at": new_expires.isoformat(),
        "last_payment_at": datetime.utcnow().isoformat()
    }
    if next_billing:
        updates["next_billing_at"] = next_billing.isoformat()
    
    pipe.hset(f"subscription:{sub_id}", mapping=updates)
    
    # 2. Update expiration ZSET with new score
    pipe.zadd("subscriptions:expiring", {sub_id: new_expires_ts})
    
    # 3. Remove from grace tracking if present
    pipe.zrem("subscriptions:grace_ending", sub_id)
    
    # 4. Sync license, org, seats to active status with NEW expires_at
    sync_subscription_state(
        subscription,
        "active",
        pipe,
        new_expires_at=new_expires.isoformat(),
        plan_code=subscription.plan_code
    )
    
    pipe.execute()
    
    return new_expires

def reactivate_subscription(sub_id: str):
    """
    Reactivate an expired/cancelled subscription after payment.
    Wrapper around extend_subscription with proper logging.
    """
    subscription = get_subscription(sub_id)
    
    # Get plan's billing period
    plan = get_plan(subscription.plan_code)
    billing_period = plan.billing_period_days or 30
    
    new_expires = extend_subscription(sub_id, billing_period, billing_period)
    
    log_subscription_event("reactivated", sub_id, {
        "new_expires_at": new_expires.isoformat()
    })
    
    queue_notification(subscription.user_id, "subscription_reactivated")
```

---

## 5. API Endpoints

### 5.1 Subscription Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/subscription/status` | Get current user's subscription |
| POST | `/api/subscription/activate` | Activate a license key |
| POST | `/api/subscription/cancel` | Cancel auto-renewal |
| POST | `/api/subscription/reactivate` | Reactivate cancelled/expired |
| GET | `/api/subscription/history` | Get subscription history |

### 5.2 Admin Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/admin/subscriptions` | List all subscriptions |
| GET | `/api/admin/subscriptions/expiring` | List expiring soon |
| POST | `/api/admin/subscriptions/{id}/extend` | Manually extend |
| POST | `/api/admin/subscriptions/{id}/revoke` | Force revoke access |

### 5.3 Webhook Endpoints (Stripe)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/webhooks/stripe` | Handle Stripe events |

---

## 6. Stripe Integration Preparation

### 6.1 Stripe Concepts Mapping

| AiAssist Concept | Stripe Concept |
|------------------|----------------|
| User | Customer |
| Plan (basic/pro/enterprise) | Product + Price |
| Subscription | Subscription |
| License Key | Promo Code / Coupon |
| Seat | Subscription Item quantity |

### 6.2 Required Stripe Webhook Events

| Event | Handler Action |
|-------|----------------|
| `customer.subscription.created` | Create local subscription record |
| `customer.subscription.updated` | Sync status changes |
| `customer.subscription.deleted` | Mark as cancelled |
| `invoice.paid` | Extend subscription, update last_payment_at |
| `invoice.payment_failed` | Enter grace period, notify user |
| `customer.subscription.trial_will_end` | Send trial ending notification |

### 6.3 Checkout Flow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   User      │     │  AiAssist   │     │   Stripe    │
│  Frontend   │     │   Backend   │     │   Checkout  │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       │ Click "Subscribe" │                   │
       │──────────────────>│                   │
       │                   │                   │
       │                   │ Create Checkout   │
       │                   │ Session           │
       │                   │──────────────────>│
       │                   │                   │
       │                   │ Return session.url│
       │                   │<──────────────────│
       │                   │                   │
       │ Redirect to Stripe│                   │
       │<──────────────────│                   │
       │                   │                   │
       │───────────────────────────────────────>
       │                   │                   │
       │    Complete Payment                   │
       │                   │                   │
       │ Redirect to success_url              │
       │<──────────────────────────────────────│
       │                   │                   │
       │                   │ Webhook: invoice.paid
       │                   │<──────────────────│
       │                   │                   │
       │                   │ Create/extend     │
       │                   │ subscription      │
       │                   │                   │
```

### 6.4 Webhook Handler Implementation

**Critical Requirements**:
- Verify webhook signatures to prevent spoofing
- Handle idempotently to survive duplicate deliveries
- Return 200 quickly to avoid Stripe retries
- Process events asynchronously when possible

#### Idempotency Pattern

```python
# Redis key for tracking processed events
# TTL: 7 days (Stripe retries for up to 3 days)
WEBHOOK_EVENT_TTL = 7 * 24 * 60 * 60

def is_event_processed(event_id: str) -> bool:
    """Check if we've already processed this Stripe event."""
    return redis.exists(f"stripe:event:{event_id}")

def mark_event_processed(event_id: str, result: str = "success"):
    """Mark event as processed with TTL."""
    redis.set(
        f"stripe:event:{event_id}",
        json.dumps({
            "processed_at": datetime.utcnow().isoformat(),
            "result": result
        }),
        ex=WEBHOOK_EVENT_TTL
    )

@app.post("/api/webhooks/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    
    # 1. Verify signature
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return Response(status_code=400, content="Invalid payload")
    except stripe.error.SignatureVerificationError:
        return Response(status_code=400, content="Invalid signature")
    
    event_id = event["id"]
    event_type = event["type"]
    
    # 2. Check idempotency - already processed?
    if is_event_processed(event_id):
        logger.info(f"Skipping duplicate event {event_id}")
        return Response(status_code=200, content="Already processed")
    
    # 3. Return 200 immediately, process async
    # (For critical events, process sync then return)
    try:
        result = await process_stripe_event(event_type, event["data"]["object"])
        mark_event_processed(event_id, result)
        return Response(status_code=200, content="Processed")
    except Exception as e:
        # Log to dead letter queue for manual review
        await queue_failed_event(event_id, event_type, str(e))
        mark_event_processed(event_id, f"failed: {str(e)}")
        # Return 200 to prevent Stripe retries for events we can't handle
        return Response(status_code=200, content="Logged for review")
```

#### Event Handlers

```python
async def process_stripe_event(event_type: str, data: dict) -> str:
    """Route Stripe events to appropriate handlers."""
    handlers = {
        "customer.subscription.created": handle_subscription_created,
        "customer.subscription.updated": handle_subscription_updated,
        "customer.subscription.deleted": handle_subscription_deleted,
        "invoice.paid": handle_invoice_paid,
        "invoice.payment_failed": handle_payment_failed,
    }
    
    handler = handlers.get(event_type)
    if not handler:
        return f"unhandled_event_type:{event_type}"
    
    return await handler(data)

async def handle_invoice_paid(invoice: dict) -> str:
    """
    Handle successful payment - extend subscription.
    This is the primary renewal mechanism.
    """
    stripe_sub_id = invoice.get("subscription")
    if not stripe_sub_id:
        return "no_subscription_on_invoice"
    
    # Find our subscription by Stripe ID
    sub_id = redis.get(f"stripe_sub:{stripe_sub_id}:local_id")
    if not sub_id:
        return "subscription_not_found"
    
    subscription = get_subscription(sub_id)
    
    # Get billing period from Stripe subscription
    stripe_sub = stripe.Subscription.retrieve(stripe_sub_id)
    period_end = datetime.fromtimestamp(stripe_sub.current_period_end)
    period_start = datetime.fromtimestamp(stripe_sub.current_period_start)
    billing_days = (period_end - period_start).days
    
    # Extend subscription
    extend_subscription(sub_id, billing_days, billing_days)
    
    # Sync seat quantity if changed
    if stripe_sub.items.data:
        new_quantity = stripe_sub.items.data[0].quantity
        sync_seat_quantity(subscription, new_quantity)
    
    log_subscription_event("payment_received", sub_id, {
        "invoice_id": invoice["id"],
        "amount": invoice["amount_paid"],
        "billing_days": billing_days
    })
    
    return "subscription_extended"

async def handle_payment_failed(invoice: dict) -> str:
    """
    Handle failed payment - enter grace period.
    Stripe will retry, but we start grace period immediately.
    """
    stripe_sub_id = invoice.get("subscription")
    if not stripe_sub_id:
        return "no_subscription_on_invoice"
    
    sub_id = redis.get(f"stripe_sub:{stripe_sub_id}:local_id")
    if not sub_id:
        return "subscription_not_found"
    
    subscription = get_subscription(sub_id)
    
    # Only enter grace if currently active
    if subscription.status in ["active", "warning"]:
        now = datetime.utcnow()
        grace_ends = now + timedelta(days=GRACE_PERIOD_DAYS)
        
        pipe = redis.pipeline()
        pipe.hset(f"subscription:{sub_id}", mapping={
            "status": "grace",
            "grace_ends_at": grace_ends.isoformat()
        })
        sync_subscription_state(subscription, "grace", pipe)
        pipe.zadd("subscriptions:grace_ending", {sub_id: grace_ends.timestamp()})
        pipe.execute()
        
        queue_notification(subscription.user_id, "payment_failed", {
            "next_retry": invoice.get("next_payment_attempt")
        })
        
        log_subscription_event("payment_failed", sub_id, {
            "invoice_id": invoice["id"],
            "attempt_count": invoice.get("attempt_count", 1)
        })
    
    return "grace_period_started"

def sync_seat_quantity(subscription, new_quantity: int):
    """
    Sync seat count when Stripe quantity changes.
    Add or remove seats as needed.
    """
    if not subscription.org_id:
        return
    
    current_seats = redis.scard(f"org:{subscription.org_id}:seats")
    
    if new_quantity > current_seats:
        # Add more seats (available for invitation)
        redis.hset(f"org:{subscription.org_id}", "seat_limit", str(new_quantity))
    elif new_quantity < current_seats:
        # Reduce seats - mark excess as "pending_removal"
        # Don't immediately revoke to avoid disruption
        # Mark seats as pending removal - don't immediately revoke
        # Seat reductions apply at next renewal unless manually enforced
        # This avoids customer pain from mid-cycle seat changes
        redis.hset(f"org:{subscription.org_id}", mapping={
            "seat_limit": str(new_quantity),
            "seats_pending_removal": str(current_seats - new_quantity)
        })
        queue_notification(subscription.user_id, "seats_reduced", {
            "new_limit": new_quantity,
            "current_used": current_seats,
            "message": "Seat reduction will apply at your next renewal"
        })
```

#### Dead Letter Queue for Failed Events

```python
async def queue_failed_event(event_id: str, event_type: str, error: str):
    """
    Add failed event to dead letter queue for manual review.
    Uses Redis Stream for reliable storage.
    """
    redis.xadd("stripe:dead_letter", {
        "event_id": event_id,
        "event_type": event_type,
        "error": error,
        "timestamp": datetime.utcnow().isoformat(),
        "retries": "0"
    }, maxlen=10000)  # Keep last 10k failed events

async def retry_failed_event(event_id: str):
    """
    Manually retry a failed event from dead letter queue.
    Called by admin action.
    """
    # Fetch original event from Stripe
    event = stripe.Event.retrieve(event_id)
    
    # Clear idempotency record to allow reprocessing
    redis.delete(f"stripe:event:{event_id}")
    
    # Reprocess
    result = await process_stripe_event(event.type, event.data.object)
    
    return result
```

---

## 7. Implementation Phases

### Phase 1: Subscription Infrastructure (No Stripe)
**Duration**: 3-5 days

**Tasks**:
1. ✅ Create `Subscription` Pydantic model
2. ✅ Add Redis storage methods for subscriptions
3. ✅ Create sorted sets for expiration tracking
4. ✅ Implement subscription status API endpoints
5. ✅ Connect license activation to subscription creation

**Deliverables**:
- Subscriptions created when licenses are activated
- Users can check their subscription status
- Expiration dates tracked in sorted sets

---

### Phase 2: Background Workers
**Duration**: 2-3 days

**Tasks**:
1. ✅ Create worker scheduler with distributed locks
2. ✅ Implement expiration checker worker
3. ✅ Implement grace period processor worker
4. ✅ Implement notification sender worker
5. ✅ Add worker monitoring/health endpoints

**Deliverables**:
- Workers run on schedule
- Subscriptions automatically transition through states
- Events logged to Redis stream

---

### Phase 3: Notification System
**Duration**: 2-3 days

**Tasks**:
1. ✅ Create notification queue in Redis
2. ✅ Implement email templates (expiration warning, grace period, expired)
3. ✅ Create notification worker to send emails
4. ✅ Add in-app notification support

**Deliverables**:
- Users receive email warnings before expiration
- In-app banners for subscription status

---

### Phase 4: Admin Dashboard Enhancements
**Duration**: 1-2 days

**Tasks**:
1. ✅ Add subscription list view in admin
2. ✅ Show expiring subscriptions
3. ✅ Add manual extend/revoke controls
4. ✅ Display subscription metrics

**Deliverables**:
- Admins can view and manage all subscriptions
- Dashboard shows subscription health metrics

---

### Phase 5: Stripe Integration
**Duration**: 3-5 days

**Tasks**:
1. ⬜ Set up Stripe products and prices
2. ⬜ Implement checkout session creation
3. ⬜ Create webhook handler for Stripe events
4. ⬜ Sync Stripe subscription status with local records
5. ⬜ Implement customer portal for self-service
6. ⬜ Add renewal processor worker

**Deliverables**:
- Users can purchase subscriptions via Stripe
- Automatic renewal processing
- Self-service subscription management

---

### Phase 6: Advanced Features
**Duration**: 2-3 days

**Tasks**:
1. ⬜ Promo codes / discount coupons
2. ⬜ Plan upgrade/downgrade with proration
3. ⬜ Usage-based billing components
4. ⬜ Invoice history and receipts

**Deliverables**:
- Complete subscription commerce experience

---

## 8. Testing Strategy

### Unit Tests
- Subscription state transitions
- Worker logic (mock Redis)
- Webhook signature verification

### Integration Tests
- Full lifecycle: activate → warning → grace → expire
- Stripe webhook processing (test mode)
- Worker scheduling and locking

### End-to-End Tests
- User activates license and gains access
- Subscription expires and access revoked
- Payment renews subscription

---

## 9. Monitoring & Alerts

### Key Metrics
- Active subscriptions by plan
- Subscriptions expiring in next 7 days
- Grace period conversion rate
- Failed payments
- Worker execution times

### Alerts
- Worker hasn't run in expected interval
- High number of failed payments
- Unusual cancellation spike
- Redis connection failures

---

## 10. Security Considerations

1. **Webhook Verification**: Always verify Stripe webhook signatures
2. **Idempotency**: Handle duplicate webhook deliveries gracefully
3. **PCI Compliance**: Never store card details, use Stripe tokens
4. **Audit Trail**: Log all subscription state changes
5. **Access Control**: Verify subscription status on every API request

---

## Appendix A: Pydantic Models

```python
class SubscriptionStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    WARNING = "warning"
    GRACE = "grace"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

class Subscription(BaseModel):
    id: str
    user_id: str
    org_id: Optional[str] = None
    license_id: str
    plan_code: str
    status: SubscriptionStatus
    started_at: str
    expires_at: str
    grace_ends_at: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    stripe_customer_id: Optional[str] = None
    auto_renew: bool = False
    last_payment_at: Optional[str] = None
    next_billing_at: Optional[str] = None
    cancelled_at: Optional[str] = None

class SubscriptionCreate(BaseModel):
    user_id: str
    license_id: str
    plan_code: str
    duration_days: int = 365

class SubscriptionEvent(BaseModel):
    event_type: str
    subscription_id: str
    user_id: str
    plan_code: str
    timestamp: str
    metadata: Optional[dict] = None
```

---

## Appendix B: Environment Variables

```bash
# Stripe Configuration (Phase 5)
STRIPE_SECRET_KEY=sk_...
STRIPE_PUBLISHABLE_KEY=pk_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Worker Configuration
WORKER_EXPIRATION_INTERVAL=3600  # 1 hour in seconds
WORKER_NOTIFICATION_INTERVAL=86400  # 1 day in seconds
WORKER_GRACE_PERIOD_DAYS=7

# Notification Configuration
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=notifications@aiassist.com
SMTP_PASSWORD=...
```

---

## Next Steps

1. Review and approve this plan
2. Begin Phase 1 implementation
3. Set up Stripe test account
4. Create email templates for notifications
