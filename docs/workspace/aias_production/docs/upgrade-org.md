# Environments: Organization Upgrade System

> Work Plan for Secure & Enterprise Environment Management

**Status:** Design Specification  
**Created:** December 2024  
**Target Tiers:** Secure, Enterprise

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [The Problem We're Solving](#the-problem-were-solving)
3. [Core Concepts](#core-concepts)
4. [Data Model](#data-model)
5. [Team Member Management](#team-member-management)
6. [Plan Limits & Licensing](#plan-limits--licensing)
7. [Environment Lifecycle](#environment-lifecycle)
8. [Resource Scoping](#resource-scoping)
9. [API & Authentication](#api--authentication)
10. [User Interface](#user-interface)
11. [Migration Strategy](#migration-strategy)
12. [Implementation Phases](#implementation-phases)

---

## Executive Summary

**Environments** are upgraded organizations that provide complete isolation of resources (workspaces, API keys, KB, directives) while sharing team membership through a parent license.

**Key Benefits:**
- Customers can run separate AI deployments (Sales Bot, Support Bot, Internal Tool) without cross-contamination
- Team members are managed centrally via the parent license
- Clean separation of concerns without complex API-key-level configuration
- Builds on existing organization infrastructure

**Plan Allocation:**
- **Secure:** Up to 2 environments
- **Enterprise:** Unlimited environments (per license agreement)

---

## The Problem We're Solving

### Current Limitation

Today, organizations have:
- One shared set of workspaces
- One shared knowledge base
- One shared set of directives
- One shared pool of API keys

This creates problems when customers want to:
- Run different AI personas for different use cases
- Keep client projects completely separate
- Have different KB/directives for Sales vs Support vs Internal

### Previous Approach (Rejected)

We considered API-key-specific resources (KB, directives, templates per key), but this:
- Adds complexity to every API call
- Requires rebuilding tested infrastructure
- Creates confusing inheritance chains

### New Approach: Environments

Instead of scoping to API keys, we scope to **environments**:
- Each environment is a complete, isolated workspace
- Team members are shared across all environments (via parent license)
- Switching environments is like switching organizations, but better
- Reuses all existing infrastructure with minimal changes

---

## Core Concepts

### Terminology

| Term | Definition |
|------|------------|
| **License** | The parent subscription (Secure/Enterprise) that owns everything |
| **Environment** | An isolated container for resources (workspaces, API keys, KB, directives) |
| **Primary Environment** | The first/default environment created when claiming a license |
| **Member** | A user with access to environments under a license |

### Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                        LICENSE                               │
│                  (Secure or Enterprise)                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   👥 TEAM MEMBERS (shared across all environments)           │
│   ─────────────────────────────────────────────              │
│   • Alice (Owner)                                            │
│   • Bob (Admin)                                              │
│   • Carol (Member)                                           │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   🏢 ENVIRONMENT: "Sales"        🏢 ENVIRONMENT: "Support"   │
│   ──────────────────────         ────────────────────────    │
│   • Workspaces                   • Workspaces                │
│   • API Keys                     • API Keys                  │
│   • Knowledge Base               • Knowledge Base            │
│   • Directives                   • Directives                │
│   • Conversation Memory          • Conversation Memory       │
│                                                              │
│   (Completely isolated)          (Completely isolated)       │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Key Principles

1. **License owns members, environments own resources**
   - Team members are managed at the license level
   - Resources are scoped to individual environments

2. **Parent admin controls everything**
   - License owner can create/delete environments
   - License owner can grant/revoke member access per environment
   - License owner can transfer ownership

3. **Environment isolation is absolute**
   - No data sharing between environments
   - Separate API keys, separate KB, separate everything
   - Switching environments = switching context entirely

---

## Data Model

### New Tables/Redis Structures

#### Environment

```python
class Environment:
    id: str                      # env_xxx unique ID
    slug: str                    # URL-safe name (e.g., "acme-sales")
    display_name: str            # Human-readable (e.g., "Acme Sales")
    license_id: str              # FK to parent license
    organization_id: str         # FK to underlying organization (for migration)
    status: str                  # active, suspended, archived
    is_primary: bool             # True for first environment under license
    created_at: datetime
    created_by: str              # User who created it
    settings: dict               # Environment-specific settings
```

#### Environment Membership

```python
class EnvironmentMembership:
    id: str
    environment_id: str          # FK to environment
    user_id: str                 # FK to user
    role: str                    # owner, admin, member, viewer
    granted_by: str              # Who granted access
    granted_at: datetime
```

#### License Extension

```python
class License:
    # ... existing fields ...
    
    # New fields
    max_environments: int        # 2 for Pro, 5 for Secure, -1 (unlimited) for Enterprise
    environments: List[str]      # List of environment IDs
```

### Redis Key Patterns

```
# Environment data
aai:env:{env_id}                  → Environment hash
aai:env:{env_id}:members          → Set of user IDs with access
aai:env:{env_id}:workspaces       → Set of workspace IDs
aai:env:{env_id}:apikeys          → Set of API key IDs
aai:env:{env_id}:kb               → KB content (markdown)
aai:env:{env_id}:directives       → Hash of directive IDs

# License to environments mapping
aai:license:{license_id}:envs     → Set of environment IDs

# User's active environment per session
aai:user:{user_id}:active_env     → Current environment ID

# Indexes
aai:env:by_slug:{slug}            → Environment ID (for slug lookups)
```

### Resource Scoping Updates

All existing resources gain an `environment_id` field:

| Resource | Current Scope | New Scope |
|----------|--------------|-----------|
| Workspace | organization_id | environment_id |
| API Key | organization_id | environment_id |
| Directive | workspace_id | environment_id (global) or workspace_id |
| KB | workspace_id | environment_id (global) or workspace_id |
| Message | workspace_id | (unchanged - inherits from workspace) |

---

## Team Member Management

### License-Level Membership

Team members are managed at the **license level**, not the environment level.

```
┌─────────────────────────────────────────────────────────────┐
│                    LICENSE MEMBERS                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   👤 Alice (Owner)                                           │
│      └── Access: All environments (automatic)                │
│                                                              │
│   👤 Bob (Admin)                                             │
│      └── Access: Sales, Support (granted by Alice)           │
│                                                              │
│   👤 Carol (Member)                                          │
│      └── Access: Support only (granted by Alice)             │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Access Control Matrix

| Role | Create Env | Delete Env | Manage Members | Access Resources | View Only |
|------|------------|------------|----------------|------------------|-----------|
| Owner | ✅ | ✅ | ✅ | ✅ | ✅ |
| Admin | ✅ | ❌ | ✅ (within granted envs) | ✅ | ✅ |
| Member | ❌ | ❌ | ❌ | ✅ | ✅ |
| Viewer | ❌ | ❌ | ❌ | ❌ | ✅ |

### Granting Environment Access

1. **Owner/Admin** goes to License Settings → Members
2. Clicks on a member → "Manage Environment Access"
3. Toggles which environments they can access
4. Member sees only their granted environments in the switcher

### Revoking Access

- Removing environment access = immediate (session invalidation)
- Removing from license = removes from all environments
- Deleting an environment = all members lose access to that env

---

## Plan Limits & Licensing

### Environment Limits

| Plan | Max Environments | Notes |
|------|-----------------|-------|
| Free | 0 | No environments (uses legacy org model) |
| Basic | 0 | No environments (uses legacy org model) |
| Pro | 2 | Entry-level multi-environment support |
| Secure | 5 | Enhanced environment isolation |
| Enterprise | Unlimited | Per license agreement (stored in license record) |

### Enforcement Points

1. **Creation:** Check `license.max_environments` vs `license.environments.length`
2. **API:** Validate environment access on every authenticated request
3. **Dashboard:** Show "Upgrade" prompt when limit reached

### Upsell Flow

When a user reaches their plan limit:
```
┌─────────────────────────────────────────────────────────────┐
│                                                              │
│   ⚠️ Environment Limit Reached                               │
│                                                              │
│   Your plan includes X environments.                         │
│   You're currently using X of X.                             │
│                                                              │
│   Upgrade to the next tier for more environments.            │
│                                                              │
│   [Upgrade Now]  [Maybe Later]                               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Environment Lifecycle

### Creating an Environment

**Step 1: Claim/Create**
```
POST /api/environments
{
    "display_name": "Sales Bot",
    "slug": "sales-bot"  // optional, auto-generated if not provided
}
```

**Step 2: System Actions**
1. Validate plan allows more environments
2. Validate slug uniqueness
3. Create environment record
4. Create underlying organization (or link existing)
5. Grant creator as owner
6. Return environment details

### Switching Environments

**API:**
```
POST /api/environments/{env_id}/switch
```

**Effect:**
- Updates user's `active_environment_id` in session
- All subsequent requests scoped to that environment
- Dashboard refreshes with new environment context

### Deleting an Environment

**Soft Delete:**
1. Mark status = "archived"
2. Resources remain but are inaccessible
3. Can be restored within 30 days

**Hard Delete (after 30 days or manual):**
1. Delete all workspaces and messages
2. Revoke all API keys
3. Delete KB and directives
4. Remove from license's environment list
5. Free up the slug for reuse

---

## Resource Scoping

### How Resources Are Scoped

When a user is in Environment "Sales":

| Action | Sees |
|--------|------|
| List Workspaces | Only workspaces in "Sales" env |
| List API Keys | Only keys created in "Sales" env |
| Get KB | Only "Sales" environment KB |
| List Directives | Global "Sales" directives + workspace directives |
| Send Message | Messages in workspaces under "Sales" |

### API Key Scoping

API keys are created within an environment and can only access that environment's resources:

```python
# When API key is used
api_key = validate_api_key(request.headers["Authorization"])
environment_id = api_key.environment_id

# All resource lookups filtered by environment_id
workspaces = get_workspaces(environment_id=environment_id)
```

### Cross-Environment Prevention

- No endpoint allows accessing resources outside active environment
- API keys cannot be "shared" across environments
- Each environment has its own rate limits and quotas

---

## API & Authentication

### Session Context

Every authenticated request includes environment context:

```python
class SessionContext:
    user_id: str
    license_id: str
    active_environment_id: str
    environment_role: str  # owner, admin, member, viewer
```

### Updated Endpoints

| Endpoint | Change |
|----------|--------|
| `GET /api/workspaces` | Filter by `active_environment_id` |
| `POST /api/workspaces` | Set `environment_id` from session |
| `GET /api/apikeys` | Filter by `active_environment_id` |
| `POST /api/apikeys` | Set `environment_id` from session |
| `GET /api/kb` | Return environment-level KB |
| `PUT /api/kb` | Update environment-level KB |

### New Endpoints

```
# Environment Management
GET    /api/environments              # List user's accessible environments
POST   /api/environments              # Create new environment
GET    /api/environments/{id}         # Get environment details
PATCH  /api/environments/{id}         # Update environment settings
DELETE /api/environments/{id}         # Archive environment

# Switching
POST   /api/environments/{id}/switch  # Set as active environment

# Member Management (License Owner/Admin only)
GET    /api/license/members                      # List all license members
POST   /api/license/members                      # Invite new member
DELETE /api/license/members/{user_id}            # Remove from license
PATCH  /api/license/members/{user_id}/environments  # Update env access
```

---

## User Interface

### Dashboard Header

```
┌────────────────────────────────────────────────────────────────────┐
│  🏢 Sales Bot ▾  │  Dashboard  Workspaces  API Keys  KB  Settings  │
└────────────────────────────────────────────────────────────────────┘
         │
         ▼ (dropdown)
   ┌──────────────────────────┐
   │ 🏢 Sales Bot          ✓  │
   │ 🏢 Support Bot           │
   │ ─────────────────────────│
   │ + Create Environment     │  ← shows limit: "1 of 2 used"
   │ ─────────────────────────│
   │ ⚙️ Manage Environments    │
   └──────────────────────────┘
```

### Environment Switcher Behavior

- **Click environment:** Switch immediately, page refreshes with new context
- **Keyboard shortcut:** `Cmd/Ctrl + E` opens switcher, type to filter
- **Visual indicator:** Environment name always visible in header
- **Color coding:** Each environment can have a color for quick recognition

### Settings → Environments Page

```
┌─────────────────────────────────────────────────────────────┐
│  ENVIRONMENTS                               [+ Create New]  │
│  ──────────────────────────────────────────────────────────  │
│                                                              │
│  Usage: 2 of 2 environments (Secure plan)    [Upgrade]       │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ 🏢 Sales Bot                              [Primary]     ││
│  │    Created: Dec 15, 2024                                ││
│  │    Workspaces: 12  |  API Keys: 3  |  Members: 4        ││
│  │    [Rename]  [Settings]  [Archive]                      ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ 🏢 Support Bot                                          ││
│  │    Created: Dec 20, 2024                                ││
│  │    Workspaces: 5   |  API Keys: 2  |  Members: 2        ││
│  │    [Rename]  [Settings]  [Archive]                      ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Settings → Team Members Page

```
┌─────────────────────────────────────────────────────────────┐
│  TEAM MEMBERS                               [+ Invite]       │
│  ──────────────────────────────────────────────────────────  │
│                                                              │
│  Seats: 3 of 5 used (Secure plan)                           │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ 👤 Alice Smith (you)                       Owner        ││
│  │    alice@company.com                                    ││
│  │    Access: All environments (automatic)                 ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ 👤 Bob Johnson                             Admin        ││
│  │    bob@company.com                                      ││
│  │    Access: Sales Bot, Support Bot    [Manage Access]    ││
│  │    [Change Role ▾]  [Remove]                            ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ 👤 Carol Davis                             Member       ││
│  │    carol@company.com                                    ││
│  │    Access: Support Bot only          [Manage Access]    ││
│  │    [Change Role ▾]  [Remove]                            ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Mobile Responsive

- Environment switcher becomes full-screen modal on mobile
- Swipe gestures to switch between environments (optional)
- Settings pages use accordion pattern

---

## Migration Strategy

### For Existing Organizations

When a user upgrades to Secure/Enterprise:

1. **Auto-create Primary Environment**
   - Name: Organization name or "Primary"
   - Migrate all existing workspaces, API keys, KB, directives
   - Set `is_primary = true`

2. **Preserve Organization ID**
   - Environment links to existing organization
   - No data loss, just new wrapper

3. **Set User as Owner**
   - Existing org owner becomes environment owner
   - Existing org members become environment members (all envs)

### For New Signups

1. License activation prompts: "Name your first environment"
2. Primary environment created with that name
3. User lands in dashboard with environment context

### Backward Compatibility

- Lower-tier users continue using organizations without environments
- API endpoints work identically (environment_id = null means legacy mode)
- No breaking changes to existing integrations

---

## Implementation Phases

### Phase 1: Data Model & Storage (Week 1)

- [ ] Add Environment model to `api/models.py`
- [ ] Add EnvironmentMembership model
- [ ] Extend License model with `max_environments` and `environments` list
- [ ] Add `environment_id` to Workspace, ApiKey, Directive, KB models
- [ ] Create Redis key patterns and storage methods
- [ ] Add migration script for existing organizations

### Phase 2: Core API (Week 2)

- [ ] Create environment CRUD endpoints
- [ ] Add environment switching endpoint
- [ ] Update session/auth to include `active_environment_id`
- [ ] Update all resource endpoints to filter by environment
- [ ] Add plan limit enforcement
- [ ] Update API key authentication to respect environment scoping

### Phase 3: Team Management (Week 3)

- [ ] Add license-level member management endpoints
- [ ] Add per-environment access control
- [ ] Implement access grant/revoke flows
- [ ] Add role-based permissions checks
- [ ] Create invite flow with environment selection

### Phase 4: Dashboard UI (Week 4)

- [ ] Add environment switcher to header
- [ ] Create Environments settings page
- [ ] Update Team Members page with environment access controls
- [ ] Add environment context indicator throughout dashboard
- [ ] Implement creation/deletion flows with confirmations
- [ ] Add mobile-responsive layouts

### Phase 5: Polish & Testing (Week 5)

- [ ] End-to-end testing of all flows
- [ ] Migration testing with production data samples
- [ ] Performance testing (switching, loading, etc.)
- [ ] Security audit (isolation verification)
- [ ] Documentation updates
- [ ] User onboarding flow for upgrades

---

## Finalized Decisions

| Question | Decision |
|----------|----------|
| **Slug uniqueness** | Per-license unique (each customer can have `sales` slug independently) |
| **Default environment** | User preference in settings, fallback to primary environment |
| **Deletion policy** | 90-day soft delete minimum, tied to license lifecycle |
| **Cross-environment reporting** | Yes, License Overview dashboard with aggregate stats |

---

## Success Metrics

- **Adoption:** % of Secure/Enterprise users creating 2+ environments
- **Retention:** Churn rate for multi-environment users vs single
- **Usage:** Average workspaces per environment
- **Support:** Tickets related to environment management (should be low)

---

*Document maintained by AiAssist Engineering. Last updated December 2024.*
