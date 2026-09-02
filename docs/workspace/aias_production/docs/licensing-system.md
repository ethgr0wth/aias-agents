# Licensing System Design Document (Redis-Only)

## Overview

This document describes the comprehensive licensing system for AiAssist using Redis as the sole data store. The system enables:
- Seat-based subscriptions with configurable durations
- Organization and team structures
- Admin bulk license generation
- Team leader seat management
- License activation and bearer tracking

## Current State

### Existing Implementation
- Simple license keys stored in Redis with basic fields (id, key, plan, status, duration_days)
- Basic activation ties a license to a single user
- Hard-coded PlanType enum (free, basic, pro, enterprise)
- Users have optional `organization_id` but no organization entity exists
- `api/routes/licenses.py` has basic CRUD and batch generation

### Enhancements Needed
1. Subscription plans with configurable duration/seats/pricing
2. Batch generation with metadata tracking (purpose, notes, creator)
3. Organization entity with team structure
4. Seat roster and bearer tracking
5. Seat invitation/claiming workflow

---

## Redis Data Model

### Key Naming Convention
All keys use the prefix from `api/config.py` (default: `aai:`) followed by entity type and ID.

### 1. Subscription Plans

Defines available subscription tiers with features and limits.

```
Key: aai:plans:{plan_code}
Type: Hash
Fields:
  - id: string (UUID)
  - code: string (free, basic, pro, enterprise)
  - name: string
  - billing_cycle_months: int
  - default_seats: int
  - max_seats: int (0 = unlimited)
  - price_cents: int
  - features: JSON string
  - is_active: "true" | "false"
  - created_at: ISO timestamp
  - updated_at: ISO timestamp

Index: aai:plans:all (Set of plan codes)
```

### 2. License Batches

Groups licenses for tracking and management.

```
Key: aai:batches:{batch_id}
Type: Hash
Fields:
  - id: string (UUID)
  - plan_code: string
  - creator_id: string (admin user ID)
  - seat_count: int
  - duration_days: int
  - quantity: int
  - purpose: string
  - notes: string
  - status: draft | generated | partially_used | exhausted | cancelled
  - metadata: JSON string
  - created_at: ISO timestamp
  - updated_at: ISO timestamp

Indexes:
  - aai:batches:all (Set of batch IDs)
  - aai:batches:plan:{plan_code} (Set of batch IDs by plan)
  - aai:batches:status:{status} (Set of batch IDs by status)
```

### 3. License Keys (Enhanced)

```
Key: aai:licenses:{license_id}
Type: Hash
Fields:
  - id: string (UUID)
  - key: string (aai_lic_xxxx format)
  - batch_id: string (optional)
  - plan_code: string
  - organization_id: string (set on activation)
  - activated_by: string (user ID who activated)
  - seat_count: int
  - duration_days: int
  - status: available | active | expired | revoked
  - activated_at: ISO timestamp
  - expires_at: ISO timestamp
  - revoked_at: ISO timestamp
  - revoke_reason: string
  - created_at: ISO timestamp
  - updated_at: ISO timestamp

Indexes:
  - aai:licenses:all (Set of license IDs)
  - aai:licenses:key:{license_key} -> license_id (String lookup)
  - aai:licenses:batch:{batch_id} (Set of license IDs in batch)
  - aai:licenses:org:{org_id} (Set of license IDs for org)
  - aai:licenses:status:{status} (Set of license IDs by status)
  - aai:licenses:user:{user_id} -> license_id (String - user's active license)
```

### 4. Organizations

Team/company entity that holds licenses and members.

```
Key: aai:orgs:{org_id}
Type: Hash
Fields:
  - id: string (UUID)
  - name: string
  - slug: string (URL-friendly)
  - active_license_id: string
  - plan_code: string
  - seats_total: int
  - seats_allocated: int
  - owner_id: string (user ID)
  - settings: JSON string
  - status: active | suspended | cancelled
  - created_at: ISO timestamp
  - updated_at: ISO timestamp

Indexes:
  - aai:orgs:all (Set of org IDs)
  - aai:orgs:slug:{slug} -> org_id (String lookup)
  - aai:orgs:owner:{user_id} (Set of org IDs owned by user)
```

### 5. Organization Members

Tracks membership and roles within organizations.

```
Key: aai:org_members:{member_id}
Type: Hash
Fields:
  - id: string (UUID)
  - organization_id: string
  - user_id: string
  - role: owner | admin | team_leader | member
  - seat_id: string
  - invited_by: string (user ID)
  - invited_at: ISO timestamp
  - joined_at: ISO timestamp
  - status: pending | active | suspended | removed
  - created_at: ISO timestamp
  - updated_at: ISO timestamp

Indexes:
  - aai:orgs:{org_id}:members (Set of member IDs)
  - aai:users:{user_id}:memberships (Set of member IDs for user)
```

### 6. License Seats

Individual seats that can be assigned to users.

```
Key: aai:seats:{seat_id}
Type: Hash
Fields:
  - id: string (UUID)
  - license_id: string
  - organization_id: string
  - user_id: string (null until claimed)
  - invitation_email: string
  - invitation_token: string
  - invited_by: string (user ID)
  - status: available | invited | claimed | revoked
  - invited_at: ISO timestamp
  - claimed_at: ISO timestamp
  - revoked_at: ISO timestamp
  - created_at: ISO timestamp
  - updated_at: ISO timestamp

Indexes:
  - aai:licenses:{license_id}:seats (Set of seat IDs)
  - aai:orgs:{org_id}:seats (Set of seat IDs)
  - aai:seats:token:{token} -> seat_id (String lookup for claiming)
  - aai:seats:email:{email} (Set of seat IDs invited to email)
  - aai:users:{user_id}:seat -> seat_id (String - user's current seat)
```

---

## API Endpoints

### Admin License Management

#### Initialize Default Plans (called on startup)
```
POST /api/admin/plans/init
Response: { plans: Plan[], message: string }
```

#### List Subscription Plans
```
GET /api/admin/plans
Response: { plans: Plan[], count: number }
```

#### Create License Batch
```
POST /api/admin/license-batches
Body: { plan_code, seat_count, duration_days, quantity, purpose?, notes? }
Response: { batch: Batch, licenses: License[] }
```

#### List License Batches
```
GET /api/admin/license-batches
Query: ?status=generated&plan_code=basic
Response: { batches: Batch[], count: number }
```

#### Get Batch Details
```
GET /api/admin/license-batches/{batch_id}
Response: { batch: Batch, licenses: License[], stats: {} }
```

#### List All Licenses
```
GET /api/admin/licenses
Query: ?status=available&batch_id=xxx
Response: { licenses: License[], count: number, stats: {} }
```

#### Revoke License
```
POST /api/admin/licenses/{license_id}/revoke
Body: { reason: string }
Response: { license: License, affected_seats: number }
```

### License Activation Flow

#### Activate License
```
POST /api/licenses/activate
Body: { license_key: string, organization_name?: string }
Response: { 
  license: License, 
  organization: Organization, 
  seat: Seat,
  message: string 
}
```

#### Get My License Info
```
GET /api/licenses/me
Response: { 
  license: License | null, 
  organization: Organization | null,
  seat: Seat | null,
  days_remaining: number | null
}
```

### Seat Management

#### List Organization Seats
```
GET /api/organizations/{org_id}/seats
Response: { seats: Seat[], available: number, used: number }
```

#### Invite User to Seat
```
POST /api/organizations/{org_id}/seats/invite
Body: { email: string }
Response: { seat: Seat, invitation_sent: boolean }
```

#### Claim Seat
```
POST /api/seats/claim
Body: { invitation_token: string }
Response: { seat: Seat, organization: Organization }
```

#### Revoke Seat
```
POST /api/organizations/{org_id}/seats/{seat_id}/revoke
Response: { seat: Seat }
```

### Organization Management

#### Get My Organization
```
GET /api/organizations/me
Response: { organization: Organization, members: Member[], seats: Seat[] }
```

#### Update Organization
```
PATCH /api/organizations/{org_id}
Body: { name?, settings? }
Response: { organization: Organization }
```

#### List Members
```
GET /api/organizations/{org_id}/members
Response: { members: Member[], count: number }
```

#### Remove Member
```
DELETE /api/organizations/{org_id}/members/{member_id}
Response: { removed: boolean, seat_freed: boolean }
```

---

## Workflows

### License Activation Workflow

```
Team Leader has a license key
         │
         ▼
┌─────────────────────────────────────┐
│  POST /api/licenses/activate        │
│  { license_key, organization_name } │
└─────────────────┬───────────────────┘
                  │
                  ▼
         ┌────────────────┐
         │ Lookup key in  │
         │ Redis index    │
         └────────┬───────┘
                  │
                  ▼
         ┌────────────────┐
         │ Validate:      │
         │ status=AVAILABLE│
         └────────┬───────┘
                  │
         ┌────────┴────────┐
         │                 │
         ▼                 ▼
   User has Org?      No Org?
         │                 │
         ▼                 ▼
   Link license       Create new Org
   to existing Org    with provided name
         │                 │
         └────────┬────────┘
                  │
                  ▼
         ┌────────────────┐
         │ Create seats   │
         │ (seat_count)   │
         │ in Redis       │
         └────────┬───────┘
                  │
                  ▼
         ┌────────────────┐
         │ Assign seat #1 │
         │ to activator   │
         └────────┬───────┘
                  │
                  ▼
         ┌────────────────┐
         │ Update:        │
         │ - License      │
         │ - Org seats    │
         │ - User plan    │
         └────────┬───────┘
                  │
                  ▼
         ┌────────────────┐
         │ Log audit event│
         └────────────────┘
```

### Seat Invitation Workflow

```
Team Leader invites user@example.com
         │
         ▼
┌──────────────────────────────────┐
│ POST /organizations/{id}/seats/  │
│      invite { email }            │
└─────────────────┬────────────────┘
                  │
                  ▼
         ┌────────────────┐
         │ Check org has  │
         │ available seats│
         └────────┬───────┘
                  │
                  ▼
         ┌────────────────┐
         │ Find available │
         │ seat record    │
         └────────┬───────┘
                  │
                  ▼
         ┌────────────────┐
         │ Generate token │
         │ Update seat:   │
         │ - email        │
         │ - token        │
         │ - status=INVITED│
         └────────┬───────┘
                  │
                  ▼
         ┌────────────────┐
         │ Store token    │
         │ lookup index   │
         └────────┬───────┘
                  │
                  ▼
         ┌────────────────┐
         │ Return seat    │
         │ (email sent    │
         │  separately)   │
         └────────────────┘


User clicks invite link with token
         │
         ▼
┌──────────────────────────────────┐
│ POST /seats/claim                │
│ { invitation_token }             │
└─────────────────┬────────────────┘
                  │
                  ▼
         ┌────────────────┐
         │ Lookup seat by │
         │ token index    │
         └────────┬───────┘
                  │
                  ▼
         ┌────────────────┐
         │ Validate:      │
         │ status=INVITED │
         └────────┬───────┘
                  │
                  ▼
         ┌────────────────┐
         │ Update seat:   │
         │ - user_id      │
         │ - status=CLAIMED│
         │ - claimed_at   │
         └────────┬───────┘
                  │
                  ▼
         ┌────────────────┐
         │ Create org     │
         │ membership     │
         └────────┬───────┘
                  │
                  ▼
         ┌────────────────┐
         │ Update user:   │
         │ - plan         │
         │ - org_id       │
         └────────┬───────┘
                  │
                  ▼
         ┌────────────────┐
         │ Update org:    │
         │ seats_allocated│
         └────────────────┘
```

---

## Default Subscription Plans

Stored in Redis on initialization:

| Code | Name | Seats | Duration | Rate Limit | Models | Price |
|------|------|-------|----------|------------|--------|-------|
| free | Free | 1 | 30 days | 10/min | llama-3.1-8b | $0 |
| basic | Basic | 3 | 365 days | 30/min | llama-3.3-70b, mixtral | $99 |
| pro | Pro | 10 | 365 days | 60/min | All models | $299 |
| enterprise | Enterprise | 50 | 365 days | 120/min | All + priority | $999 |

---

## Security Considerations

1. **License Key Format**: `aai_lic_` prefix + 24 char random string (base58)
2. **Invitation Tokens**: 32 char random string, 7-day expiry (TTL enforced)
3. **Role-Based Access**:
   - Only org owners/admins can invite users
   - Only super_admins can generate/revoke licenses
4. **Audit Logging**: Redis Streams with XADD for compliance audit trail
5. **Atomic Operations**: Lua scripts for race-condition-free seat/license operations

---

## Critical Improvements (Implemented)

### 1. Lua Scripts for Atomic Operations

To prevent race conditions, the following operations use Redis Lua scripts:
- **License Activation** (`LUA_ACTIVATE_LICENSE`): Atomically updates license status, org, and user in single transaction
- **Seat Invitation** (`LUA_INVITE_SEAT`): Atomically sets invite status and creates token with TTL
- **Seat Claim** (`LUA_CLAIM_SEAT`): Atomically claims seat, updates org allocation, and user plan
- **Seat Revocation** (`LUA_REVOKE_SEAT`): Atomically revokes seat and cleans up user associations

### 2. Email Normalization

All email keys are normalized using `lower(trim(email))` for consistent lookups:
- User registration and login
- Seat invitation emails
- Email-to-seat index lookups

### 3. Redis Stream Audit Logging

Compliance audit trail using Redis Streams:
```
Stream: aai:audit:stream
Events: license_activated, seat_invited, seat_claimed, seat_revoked
Fields: event, timestamp, user_id, org_id, etc.
Max length: 100,000 entries (auto-trimmed)
```

### 4. TTL Rules

- **Invite tokens**: 7 days (`INVITE_TOKEN_TTL = 604800 seconds`)
- **Expired licenses**: 90 days retention for audit purposes

### 5. User -> License Relationship

Users access licenses through organizations, not direct pointers:
```
User -> organization_id -> Organization -> active_license_id -> License
```

This enables:
- Multiple users per license (seat-based)
- License transfers between organizations
- Clean seat assignment/revocation

---

## Implementation Checklist

- [x] Add Pydantic models for new entities (SubscriptionPlan, Batch, Organization, Seat)
- [x] Extend RedisStorage with plan management methods
- [x] Extend RedisStorage with batch generation methods
- [x] Extend RedisStorage with organization CRUD methods
- [x] Extend RedisStorage with seat lifecycle methods
- [x] Update license activation to create org and seats
- [x] Add Lua scripts for atomic operations
- [x] Add Redis Stream audit logging
- [x] Normalize email keys
- [x] Add TTL for invite tokens
- [ ] Add seat invitation/claim endpoints
- [ ] Add organization management endpoints
- [ ] Add admin endpoints for batch generation
- [ ] Build Admin UI for batch generation
- [ ] Add seat management UI for team leaders
