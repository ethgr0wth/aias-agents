# AI-Powered CRM: Invisible Co-Pilot System

## Design Specification Document

---

## 1. System Overview

### 1.1 Vision
An AI-powered CRM where clients experience seamless AI assistance, while administrators have full real-time control to monitor, guide, and take over conversations invisibly. The system manages the complete customer lifecycle from initial contact through project delivery.

### 1.2 Core Principles
- **Invisible Intervention**: Clients never see the seam between AI and human
- **Real-Time Control**: Admins can observe and act on any conversation instantly
- **Context Persistence**: Every interaction is preserved and searchable
- **Lifecycle Tracking**: Customers flow through defined stages with full visibility

### 1.3 Key Features
1. **Virtual Chat Workspaces** - Each conversation is a managed space
2. **Admin Shadow Mode** - Watch conversations in real-time
3. **Directive Injection** - Guide AI behavior without client awareness
4. **Seamless Takeover** - Transition from AI to human invisibly
5. **Customer Lifecycle CRM** - Track from lead to delivery

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                                 │
├─────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐              ┌─────────────────────────────┐   │
│  │   Client Chat   │              │      Admin Portal           │   │
│  │   (React SPA)   │              │      (React SPA)            │   │
│  │                 │              │                             │   │
│  │  - Chat UI      │              │  - Dashboard                │   │
│  │  - WebSocket    │              │  - Workspace Monitor        │   │
│  │                 │              │  - Directive Panel          │   │
│  │                 │              │  - Lifecycle Manager        │   │
│  └────────┬────────┘              └─────────────┬───────────────┘   │
│           │                                     │                    │
└───────────┼─────────────────────────────────────┼────────────────────┘
            │                                     │
            │ WebSocket + REST                    │ WebSocket + REST
            │                                     │
┌───────────┴─────────────────────────────────────┴────────────────────┐
│                         API LAYER (FastAPI)                          │
├──────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐   │
│  │   Auth       │  │  REST API    │  │   WebSocket Gateway      │   │
│  │   Module     │  │  Endpoints   │  │   (Socket.IO)            │   │
│  │              │  │              │  │                          │   │
│  │  - Login     │  │  - /users    │  │  - /client namespace     │   │
│  │  - Sessions  │  │  - /contacts │  │  - /admin namespace      │   │
│  │  - Cookies   │  │  - /projects │  │  - Real-time events      │   │
│  │  - RBAC      │  │  - /workspaces│ │  - Presence tracking     │   │
│  └──────────────┘  └──────────────┘  └──────────────────────────┘   │
│                              │                                       │
│  ┌───────────────────────────┴───────────────────────────────────┐  │
│  │                  CONVERSATION ORCHESTRATOR                     │  │
│  │                                                                │  │
│  │  - Mode Management (AI / Shadow / Takeover)                    │  │
│  │  - Directive Merging (Global → Workspace → Message)            │  │
│  │  - AI Response Generation (Groq Integration)                   │  │
│  │  - Handoff Logic (Invisible Transitions)                       │  │
│  │  - Audit Logging                                               │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                              │                                       │
└──────────────────────────────┼───────────────────────────────────────┘
                               │
┌──────────────────────────────┴───────────────────────────────────────┐
│                         DATA LAYER                                    │
├──────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────┐    ┌────────────────────────┐ │
│  │  Redis (localhost:6379/12)     │    │   Groq API             │ │
│  │  Namespace: "aiconsult"        │    │                        │ │
│  │                                │    │  - LLama 3.3 70B       │ │
│  │  - Users         (hash)        │    │  - Chat Completions    │ │
│  │  - Contacts      (hash)        │    │                        │ │
│  │  - Projects      (hash)        │    └────────────────────────┘ │
│  │  - Workspaces    (hash)        │                               │
│  │  - Messages      (sorted set)  │                               │
│  │  - Directives    (hash)        │                               │
│  │  - Sessions      (hash + TTL)  │                               │
│  │  - Presence      (pub/sub)     │                               │
│  │  - Audit Events  (stream)      │                               │
│  └─────────────────────────────────┘                               │
└──────────────────────────────────────────────────────────────────────┘
```

### 2.2 Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | React 19, TypeScript, Tailwind CSS | Client & Admin UI |
| Real-Time | Socket.IO (python-socketio) | Bi-directional communication |
| Backend | Python FastAPI | REST API + WebSocket |
| AI | Groq (LLama 3.3 70B) | Conversation intelligence |
| Database | Redis (localhost:6379/12) | Persistent storage (namespace: aiconsult) |
| Sessions | Cookie-based (httponly) | Authentication via Redis |
| Cache | Redis pub/sub | Real-time presence & events |

---

## 2.3 Redis Configuration

### Connection
- **Host**: localhost
- **Port**: 6379
- **Database**: 12
- **Namespace**: `aiconsult`

### Key Structure (All keys prefixed with namespace)
```
aiconsult:users:{id}              → Hash (user data)
aiconsult:users:email:{email}     → String (id lookup by email)
aiconsult:contacts:{id}           → Hash (contact data)
aiconsult:contacts:org:{org_id}   → Set (contact IDs per org)
aiconsult:projects:{id}           → Hash (project data)
aiconsult:projects:contact:{id}   → Set (project IDs per contact)
aiconsult:workspaces:{id}         → Hash (workspace data)
aiconsult:workspaces:active       → Set (active workspace IDs)
aiconsult:messages:{ws_id}        → Sorted Set (messages by timestamp)
aiconsult:directives:global       → Hash (global AI directives)
aiconsult:directives:ws:{ws_id}   → Hash (workspace-specific directives)
aiconsult:sessions:{token}        → Hash (session data, with TTL)
aiconsult:presence:{ws_id}        → Hash (user presence per workspace)
aiconsult:audit                   → Stream (audit events)
```

### Environment Variables
```
REDIS_URL=redis://localhost:6379/12
REDIS_NAMESPACE=aiconsult
```

---

## 3. Data Models

### 3.1 Entity Relationship Diagram

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│  Organization   │       │      User       │       │    Contact      │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ id (PK)         │◄──────│ organization_id │       │ id (PK)         │
│ name            │       │ id (PK)         │       │ organization_id │
│ tier            │       │ email           │       │ name            │
│ settings (JSON) │       │ password_hash   │       │ email           │
│ created_at      │       │ role            │       │ company         │
│ updated_at      │       │ display_name    │       │ lifecycle_stage │
└─────────────────┘       │ created_at      │       │ metadata (JSON) │
                          └─────────────────┘       │ created_at      │
                                  │                 │ updated_at      │
                                  │                 └────────┬────────┘
                                  │                          │
                                  ▼                          │
┌─────────────────┐       ┌─────────────────┐               │
│    Project      │◄──────│ Conversation    │               │
├─────────────────┤       │   Workspace     │◄──────────────┘
│ id (PK)         │       ├─────────────────┤
│ contact_id      │       │ id (PK)         │
│ name            │       │ contact_id      │
│ status          │       │ project_id      │
│ stage           │       │ assigned_to     │
│ description     │       │ mode            │──────┐
│ metadata (JSON) │       │ tone_preset     │      │
│ created_at      │       │ status          │      │
│ updated_at      │       │ created_at      │      │
└─────────────────┘       │ updated_at      │      │
                          └────────┬────────┘      │
                                   │               │
         ┌─────────────────────────┼───────────────┘
         │                         │
         ▼                         ▼
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│    Message      │       │   Directive     │       │  AuditEvent     │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ id (PK)         │       │ id (PK)         │       │ id (PK)         │
│ workspace_id    │       │ workspace_id    │       │ workspace_id    │
│ role            │       │ created_by      │       │ user_id         │
│ content         │       │ content         │       │ event_type      │
│ metadata (JSON) │       │ priority        │       │ payload (JSON)  │
│ visible_to_client│      │ active          │       │ occurred_at     │
│ created_at      │       │ expires_at      │       └─────────────────┘
└─────────────────┘       │ created_at      │
                          └─────────────────┘
```

### 3.2 Model Definitions

#### 3.2.1 Organization
```python
class Organization:
    id: UUID (PK)
    name: str
    tier: Enum["free", "pro", "enterprise"]
    settings: JSON  # Custom AI settings, branding, etc.
    created_at: datetime
    updated_at: datetime
```

#### 3.2.2 User
```python
class User:
    id: UUID (PK)
    organization_id: UUID (FK → Organization)
    email: str (unique)
    password_hash: str
    role: Enum["client", "manager", "super_admin"]
    display_name: str
    avatar_url: str (optional)
    is_active: bool
    created_at: datetime
    updated_at: datetime
```

**Roles:**
- `client` - End users who chat (cannot access admin)
- `manager` - Can monitor, inject directives, take over assigned workspaces
- `super_admin` - Full access: global directives, all workspaces, user management

#### 3.2.3 Contact
```python
class Contact:
    id: UUID (PK)
    organization_id: UUID (FK → Organization)
    name: str
    email: str
    company: str (optional)
    phone: str (optional)
    lifecycle_stage: Enum["lead", "prospect", "opportunity", "customer", "churned"]
    source: str  # Where they came from
    metadata: JSON  # Custom fields
    created_at: datetime
    updated_at: datetime
```

#### 3.2.4 Project
```python
class Project:
    id: UUID (PK)
    contact_id: UUID (FK → Contact)
    organization_id: UUID (FK → Organization)
    name: str
    description: str
    status: Enum["draft", "scoping", "active", "on_hold", "completed", "cancelled"]
    stage: Enum["discovery", "proposal", "negotiation", "engineering", "delivery", "support"]
    value: Decimal (optional)  # Deal value
    metadata: JSON
    created_at: datetime
    updated_at: datetime
```

#### 3.2.5 ConversationWorkspace
```python
class ConversationWorkspace:
    id: UUID (PK)
    organization_id: UUID (FK → Organization)
    contact_id: UUID (FK → Contact, optional)
    project_id: UUID (FK → Project, optional)
    assigned_to: UUID (FK → User, optional)  # Manager assignment
    
    mode: Enum["ai", "shadow", "takeover"]
    # ai = AI responds autonomously
    # shadow = AI responds but manager watches live
    # takeover = Manager responds, AI silent
    
    tone_preset: str  # "professional", "friendly", "technical", etc.
    status: Enum["active", "waiting", "resolved", "archived"]
    
    title: str (auto-generated from first message)
    summary: str (AI-generated summary)
    
    client_last_seen: datetime
    manager_last_seen: datetime
    
    created_at: datetime
    updated_at: datetime
```

#### 3.2.6 Message
```python
class Message:
    id: UUID (PK)
    workspace_id: UUID (FK → ConversationWorkspace)
    
    role: Enum["user", "ai", "manager", "system"]
    # user = Client message
    # ai = AI-generated response
    # manager = Human manager (appears as AI to client)
    # system = System notifications (handoff, etc.)
    
    content: str
    
    visible_to_client: bool  # False for internal notes
    
    metadata: JSON  # Includes: model used, tokens, latency, directive_ids applied
    
    created_at: datetime
```

#### 3.2.7 Directive
```python
class Directive:
    id: UUID (PK)
    organization_id: UUID (FK → Organization, optional)  # NULL = global
    workspace_id: UUID (FK → ConversationWorkspace, optional)  # NULL = org-wide
    created_by: UUID (FK → User)
    
    content: str  # The instruction for AI
    
    priority: int  # Higher = more important (overrides lower)
    
    directive_type: Enum["tone", "context", "constraint", "persona"]
    # tone = "Be more formal", "Use technical language"
    # context = "Client is price-sensitive", "Interested in RAG"
    # constraint = "Do not discuss pricing", "Avoid competitor mentions"
    # persona = "You are Sarah, Lead Engineer"
    
    active: bool
    expires_at: datetime (optional)
    
    created_at: datetime
```

#### 3.2.8 AuditEvent
```python
class AuditEvent:
    id: UUID (PK)
    organization_id: UUID (FK → Organization)
    workspace_id: UUID (FK → ConversationWorkspace, optional)
    user_id: UUID (FK → User)
    
    event_type: Enum[
        "workspace_created",
        "mode_changed",
        "takeover_started",
        "takeover_ended",
        "directive_added",
        "directive_removed",
        "contact_linked",
        "project_linked",
        "lifecycle_changed"
    ]
    
    payload: JSON  # Event-specific data
    
    occurred_at: datetime
```

---

## 4. API Specification

### 4.1 Authentication Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/auth/login` | Login with email/password, set session cookie | None |
| POST | `/api/auth/logout` | Clear session cookie | Required |
| GET | `/api/auth/me` | Get current user | Required |
| POST | `/api/auth/register` | Register new user (admin only) | Super Admin |

#### Login Request/Response
```json
// POST /api/auth/login
// Request
{
  "email": "admin@company.com",
  "password": "secure_password"
}

// Response (200 OK)
// Sets HttpOnly cookie: session_id
{
  "user": {
    "id": "uuid",
    "email": "admin@company.com",
    "role": "super_admin",
    "display_name": "Admin User",
    "organization": {
      "id": "uuid",
      "name": "AI Consult"
    }
  }
}
```

### 4.2 Workspace Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/workspaces` | Create new conversation workspace | Any |
| GET | `/api/workspaces` | List workspaces (filtered by role) | Manager+ |
| GET | `/api/workspaces/{id}` | Get workspace details | Owner/Manager+ |
| PATCH | `/api/workspaces/{id}` | Update workspace (mode, assignment) | Manager+ |
| GET | `/api/workspaces/{id}/messages` | Get message history | Owner/Manager+ |
| POST | `/api/workspaces/{id}/messages` | Send message (triggers AI if mode=ai) | Owner/Manager+ |

#### Create Workspace (Client Starting Chat)
```json
// POST /api/workspaces
// Request (anonymous client - creates guest contact)
{
  "initial_message": "I need help with AI integration"
}

// Response (201 Created)
{
  "workspace": {
    "id": "uuid",
    "mode": "ai",
    "status": "active",
    "created_at": "2024-12-17T..."
  },
  "messages": [
    {
      "id": "uuid",
      "role": "user",
      "content": "I need help with AI integration",
      "created_at": "..."
    },
    {
      "id": "uuid",
      "role": "ai",
      "content": "I can help with that. What type of AI integration...",
      "created_at": "..."
    }
  ],
  "session_token": "jwt_for_anonymous_access"
}
```

#### Admin: Update Workspace Mode
```json
// PATCH /api/workspaces/{id}
// Request
{
  "mode": "takeover",
  "assigned_to": "manager_user_id"
}

// Response (200 OK)
{
  "workspace": { ... },
  "audit_event": {
    "event_type": "mode_changed",
    "payload": { "from": "ai", "to": "takeover" }
  }
}
```

### 4.3 Directive Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/directives` | Create directive (global or workspace) | Manager+ |
| GET | `/api/directives` | List directives | Manager+ |
| PATCH | `/api/directives/{id}` | Update directive | Owner/Super Admin |
| DELETE | `/api/directives/{id}` | Deactivate directive | Owner/Super Admin |

#### Create Workspace Directive
```json
// POST /api/directives
{
  "workspace_id": "uuid",
  "content": "This client is interested in RAG solutions. Emphasize our expertise in retrieval-augmented generation.",
  "directive_type": "context",
  "priority": 10
}
```

### 4.4 Contact & Project Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| GET | `/api/contacts` | List contacts | Manager+ |
| POST | `/api/contacts` | Create contact | Manager+ |
| GET | `/api/contacts/{id}` | Get contact with history | Manager+ |
| PATCH | `/api/contacts/{id}` | Update contact/lifecycle | Manager+ |
| GET | `/api/projects` | List projects | Manager+ |
| POST | `/api/projects` | Create project | Manager+ |
| PATCH | `/api/projects/{id}` | Update project status | Manager+ |

---

## 5. WebSocket Events

### 5.1 Namespaces

| Namespace | Purpose | Auth |
|-----------|---------|------|
| `/client` | Client chat interface | Session token |
| `/admin` | Admin monitoring & control | Manager+ cookie |

### 5.2 Client Namespace Events

#### Client → Server
| Event | Payload | Description |
|-------|---------|-------------|
| `join_workspace` | `{ workspace_id }` | Join a conversation room |
| `send_message` | `{ workspace_id, content }` | Send a message |
| `typing_start` | `{ workspace_id }` | User started typing |
| `typing_stop` | `{ workspace_id }` | User stopped typing |

#### Server → Client
| Event | Payload | Description |
|-------|---------|-------------|
| `message_new` | `{ message }` | New message (AI or "AI" which is actually manager) |
| `typing_indicator` | `{ is_typing }` | Show typing animation |
| `workspace_updated` | `{ workspace }` | Status change (resolved, etc.) |

### 5.3 Admin Namespace Events

#### Admin → Server
| Event | Payload | Description |
|-------|---------|-------------|
| `subscribe_workspace` | `{ workspace_id }` | Start watching a workspace |
| `unsubscribe_workspace` | `{ workspace_id }` | Stop watching |
| `subscribe_dashboard` | `{}` | Get all workspace updates |
| `inject_directive` | `{ workspace_id, content, type }` | Add runtime directive |
| `send_as_ai` | `{ workspace_id, content }` | Manager sends as AI |
| `change_mode` | `{ workspace_id, mode }` | Switch workspace mode |

#### Server → Admin
| Event | Payload | Description |
|-------|---------|-------------|
| `workspace_list` | `{ workspaces[] }` | Current active workspaces |
| `workspace_update` | `{ workspace }` | Workspace state change |
| `message_new` | `{ workspace_id, message }` | New message in any watched workspace |
| `client_typing` | `{ workspace_id, is_typing }` | Client typing status |
| `client_presence` | `{ workspace_id, online }` | Client online/offline |

---

## 6. Conversation Orchestrator

### 6.1 Message Processing Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    MESSAGE RECEIVED                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. STORE MESSAGE                                                │
│     - Save to database                                           │
│     - Emit to admin subscribers (real-time)                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. CHECK WORKSPACE MODE                                         │
│     ┌─────────────┬─────────────┬─────────────┐                 │
│     │   mode=ai   │ mode=shadow │mode=takeover│                 │
│     │             │             │             │                 │
│     │ Continue to │ Continue to │   STOP      │                 │
│     │ AI response │ AI response │ (wait for   │                 │
│     │             │ + notify    │  manager)   │                 │
│     │             │   manager   │             │                 │
│     └─────────────┴─────────────┴─────────────┘                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. BUILD AI CONTEXT                                             │
│     a. Load conversation history (last N messages)               │
│     b. Load active directives (sorted by priority):              │
│        - Global org directives                                   │
│        - Workspace-specific directives                           │
│     c. Load contact/project context if linked                    │
│     d. Construct system prompt with merged directives            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. GENERATE AI RESPONSE                                         │
│     - Call Groq API with constructed prompt                      │
│     - Stream response tokens (optional)                          │
│     - Log: model, tokens, latency, directive_ids                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  5. DELIVER RESPONSE                                             │
│     - Store AI message                                           │
│     - Emit to client via WebSocket                               │
│     - Emit to admin subscribers                                  │
│     - Update workspace.updated_at                                │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Directive Merging Strategy

Directives are merged in priority order to form the system prompt:

```python
def build_system_prompt(workspace_id: str) -> str:
    base_prompt = """You are a senior technical consultant at an AI + Full-Stack consulting agency..."""
    
    # Load directives in priority order
    directives = get_active_directives(workspace_id)
    directives.sort(key=lambda d: d.priority, reverse=True)
    
    # Group by type
    tone_directives = [d for d in directives if d.type == "tone"]
    context_directives = [d for d in directives if d.type == "context"]
    constraint_directives = [d for d in directives if d.type == "constraint"]
    persona_directives = [d for d in directives if d.type == "persona"]
    
    # Build augmented prompt
    prompt = base_prompt
    
    if persona_directives:
        prompt = persona_directives[0].content  # Highest priority persona overrides
    
    if tone_directives:
        prompt += f"\n\nTone guidance: {'; '.join(d.content for d in tone_directives)}"
    
    if context_directives:
        prompt += f"\n\nContext about this client: {'; '.join(d.content for d in context_directives)}"
    
    if constraint_directives:
        prompt += f"\n\nConstraints: {'; '.join(d.content for d in constraint_directives)}"
    
    return prompt
```

### 6.3 Seamless Takeover Flow

```
┌───────────────────────────────────────────────────────────────────┐
│  MANAGER INITIATES TAKEOVER                                       │
│  (clicks "Take Over" button in admin)                             │
└───────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────────────┐
│  1. Update workspace.mode = "takeover"                            │
│  2. Update workspace.assigned_to = manager_id                     │
│  3. Create AuditEvent (takeover_started)                          │
│  4. Emit workspace_update to admin subscribers                    │
│  5. DO NOT notify client (invisible)                              │
└───────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────────────┐
│  MANAGER SENDS MESSAGE                                            │
│  (POST /api/workspaces/{id}/messages with role override)          │
└───────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────────────┐
│  1. Store message with role="manager"                             │
│  2. Emit to client as role="ai" (client sees AI responding)       │
│  3. Emit to admin with role="manager" (admin sees truth)          │
│  4. NO AI generation (manager is in control)                      │
└───────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────────────┐
│  MANAGER RELEASES CONTROL                                         │
│  (clicks "Return to AI" button)                                   │
└───────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────────────┐
│  1. Update workspace.mode = "ai" (or "shadow")                    │
│  2. Create AuditEvent (takeover_ended)                            │
│  3. Next client message triggers AI again                         │
└───────────────────────────────────────────────────────────────────┘
```

---

## 7. Admin Portal Wireframes

### 7.1 Dashboard View

```
┌─────────────────────────────────────────────────────────────────────────┐
│  ┌─────┐  AI+CONSULT Admin                    🔔  👤 Admin User  ▾     │
│  │ ● ● │                                                                 │
│  └─────┘                                                                 │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  📊 Dashboard    💬 Conversations    👥 Contacts    📁 Projects         │
│  ━━━━━━━━━━━━                                                           │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  ACTIVE CONVERSATIONS                                    View All │   │
│  ├─────────────────────────────────────────────────────────────────┤   │
│  │                                                                   │   │
│  │  ┌─────────────────────────────────────────────────────────────┐ │   │
│  │  │ ● LIVE   John Doe - Acme Corp                    2m ago     │ │   │
│  │  │          "What's your approach to RAG implementation?"       │ │   │
│  │  │          Mode: AI  │  Stage: Lead  │  Assigned: —           │ │   │
│  │  │                                            [Shadow] [Take Over] │ │   │
│  │  └─────────────────────────────────────────────────────────────┘ │   │
│  │                                                                   │   │
│  │  ┌─────────────────────────────────────────────────────────────┐ │   │
│  │  │ ● LIVE   Sarah Chen - TechStart                  5m ago     │ │   │
│  │  │          "Can you handle enterprise compliance?"             │ │   │
│  │  │          Mode: Shadow 👁️  │  Stage: Prospect  │  @Mike      │ │   │
│  │  │                                            [Take Over]        │ │   │
│  │  └─────────────────────────────────────────────────────────────┘ │   │
│  │                                                                   │   │
│  │  ┌─────────────────────────────────────────────────────────────┐ │   │
│  │  │ ○ WAITING   Alex Kim - BigCo                    15m ago     │ │   │
│  │  │          "Thanks, I'll discuss with my team"                 │ │   │
│  │  │          Mode: AI  │  Stage: Opportunity  │  Assigned: —     │ │   │
│  │  └─────────────────────────────────────────────────────────────┘ │   │
│  │                                                                   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────────────┐  ┌──────────────────────┐                     │
│  │  PIPELINE            │  │  RECENT ACTIVITY     │                     │
│  │                      │  │                      │                     │
│  │  Lead        12      │  │  • Mode change: AI→Shadow (2m)            │
│  │  Prospect     5      │  │  • New conversation (5m)                  │
│  │  Opportunity  3      │  │  • Project created (1h)                   │
│  │  Customer     8      │  │  • Directive added (2h)                   │
│  │                      │  │                      │                     │
│  └──────────────────────┘  └──────────────────────┘                     │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Workspace Monitor View

```
┌─────────────────────────────────────────────────────────────────────────┐
│  ← Back to Dashboard          Workspace: John Doe - Acme Corp           │
├──────────────────────────────────────────────┬──────────────────────────┤
│                                              │                          │
│  CONVERSATION                                │  CONTROL PANEL           │
│  ━━━━━━━━━━━━━                              │  ━━━━━━━━━━━━━           │
│                                              │                          │
│  ┌────────────────────────────────────────┐  │  Mode: ○ AI ● Shadow ○ Take│
│  │  👤 John Doe                    2:34 PM│  │                          │
│  │  I need help with AI integration for   │  │  ┌────────────────────┐ │
│  │  our customer support system.          │  │  │ [Take Over Now]    │ │
│  └────────────────────────────────────────┘  │  └────────────────────┘ │
│                                              │                          │
│  ┌────────────────────────────────────────┐  │  Tone: [Professional ▾] │
│  │  🤖 AI                          2:34 PM│  │                          │
│  │  I can help with that. We specialize   │  │  ACTIVE DIRECTIVES       │
│  │  in AI-powered support systems. Are    │  │  ━━━━━━━━━━━━━━━━━       │
│  │  you looking at chatbots, ticket       │  │                          │
│  │  routing, or knowledge base search?    │  │  ┌────────────────────┐ │
│  └────────────────────────────────────────┘  │  │ 📌 Context          │ │
│                                              │  │ "Enterprise client, │ │
│  ┌────────────────────────────────────────┐  │  │  budget ~$50k"      │ │
│  │  👤 John Doe                    2:35 PM│  │  │              [Edit] │ │
│  │  We're interested in a RAG system for  │  │  └────────────────────┘ │
│  │  our internal docs. About 50k docs.    │  │                          │
│  └────────────────────────────────────────┘  │  + Add Directive          │
│                                              │                          │
│  ┌────────────────────────────────────────┐  │  ─────────────────────── │
│  │  🤖 AI                          2:35 PM│  │                          │
│  │  50k documents is a solid use case     │  │  CONTACT INFO            │
│  │  for RAG. We'd typically recommend...  │  │                          │
│  │  [typing...]                           │  │  John Doe                │
│  └────────────────────────────────────────┘  │  Acme Corp               │
│                                              │  john@acme.com           │
│  ┌────────────────────────────────────────┐  │  Stage: Lead → [▾]       │
│  │  💬 Type to inject as AI...            │  │                          │
│  │                              [Send]    │  │  ─────────────────────── │
│  └────────────────────────────────────────┘  │                          │
│                                              │  QUICK ACTIONS            │
│  📝 Internal note (not visible to client)   │  • Link to Project        │
│  ┌────────────────────────────────────────┐  │  • Schedule Follow-up    │
│  │                                        │  │  • Mark as Resolved      │
│  └────────────────────────────────────────┘  │                          │
│                                              │                          │
└──────────────────────────────────────────────┴──────────────────────────┘
```

---

## 8. Implementation Phases

### Phase 1: Foundation (Week 1)
**Goal: Basic infrastructure with working auth and chat**

- [x] Design specification document
- [ ] Set up Python FastAPI project structure
- [ ] Implement SQLAlchemy models
- [ ] Create PostgreSQL database
- [ ] Cookie-based authentication (login/logout/sessions)
- [ ] Basic workspace CRUD API
- [ ] Groq integration for AI responses
- [ ] Update React frontend to use new API

**Deliverable:** Working chat with auth, no admin features yet

### Phase 2: Real-Time & Admin (Week 2)
**Goal: Live monitoring and basic control**

- [ ] Socket.IO integration (client + admin namespaces)
- [ ] Real-time message streaming
- [ ] Admin dashboard page (list active conversations)
- [ ] Workspace monitor page (live transcript)
- [ ] Mode switching (ai/shadow/takeover)
- [ ] Manager "send as AI" functionality
- [ ] Presence tracking

**Deliverable:** Admins can watch and take over conversations

### Phase 3: Directives & Intelligence (Week 3)
**Goal: AI behavior control**

- [ ] Directive CRUD API
- [ ] Directive UI in workspace monitor
- [ ] Directive merging in AI orchestrator
- [ ] Tone presets
- [ ] Quick response macros
- [ ] AI response quality logging

**Deliverable:** Admins can shape AI behavior per-conversation

### Phase 4: CRM Features (Week 4)
**Goal: Customer lifecycle management**

- [ ] Contact management UI
- [ ] Project tracking UI
- [ ] Lifecycle stage progression
- [ ] Link workspaces to contacts/projects
- [ ] Pipeline dashboard
- [ ] Audit event logging
- [ ] Search and filtering

**Deliverable:** Full CRM with conversation history

### Phase 5: Polish & Scale (Week 5+)
**Goal: Production readiness**

- [ ] Role-based access control refinement
- [ ] Organization multi-tenancy
- [ ] Email notifications
- [ ] Mobile-responsive admin
- [ ] Performance optimization
- [ ] Security audit
- [ ] Documentation

---

## 9. Security Considerations

### 9.1 Authentication
- HttpOnly cookies for session tokens
- Secure flag in production
- Session expiration (24h default, configurable)
- Password hashing with bcrypt

### 9.2 Authorization
- RBAC middleware on all routes
- Workspace access: owner, assigned manager, or super_admin
- Directive creation: manager+ for workspace, super_admin for global
- Audit logging for all admin actions

### 9.3 Data Protection
- Messages stored with encryption at rest (PostgreSQL)
- PII handling compliant with GDPR basics
- No client-side storage of sensitive data
- API rate limiting

### 9.4 WebSocket Security
- Token validation on connection
- Room-based isolation (workspace_id)
- Admin namespace requires manager+ role

---

## 10. File Structure

```
project/
├── server/                     # FastAPI Backend
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry
│   ├── config.py               # Environment config
│   ├── database.py             # SQLAlchemy setup
│   ├── models/                 # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── organization.py
│   │   ├── contact.py
│   │   ├── project.py
│   │   ├── workspace.py
│   │   ├── message.py
│   │   ├── directive.py
│   │   └── audit.py
│   ├── schemas/                # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── workspace.py
│   │   ├── message.py
│   │   └── directive.py
│   ├── routers/                # API routes
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── workspaces.py
│   │   ├── messages.py
│   │   ├── directives.py
│   │   ├── contacts.py
│   │   └── projects.py
│   ├── services/               # Business logic
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── ai_orchestrator.py
│   │   └── websocket_manager.py
│   └── middleware/
│       ├── __init__.py
│       └── auth.py
├── client/                     # React Frontend
│   └── src/
│       ├── pages/
│       │   ├── Home.tsx
│       │   ├── Login.tsx
│       │   ├── admin/
│       │   │   ├── Dashboard.tsx
│       │   │   ├── WorkspaceMonitor.tsx
│       │   │   ├── Contacts.tsx
│       │   │   └── Projects.tsx
│       │   └── ...
│       ├── components/
│       │   ├── chat/
│       │   │   └── ImmersiveChat.tsx
│       │   ├── admin/
│       │   │   ├── ConversationCard.tsx
│       │   │   ├── DirectivePanel.tsx
│       │   │   └── ...
│       │   └── ...
│       └── lib/
│           ├── api.ts
│           └── socket.ts
├── DESIGN.md                   # This document
├── requirements.txt            # Python dependencies
└── package.json                # Node dependencies
```

---

## Appendix A: Tone Presets

| Preset | Description | System Prompt Addition |
|--------|-------------|------------------------|
| Professional | Formal, business-focused | "Maintain a formal, professional tone. Use industry terminology." |
| Friendly | Warm, conversational | "Be warm and conversational while remaining helpful." |
| Technical | Deep technical detail | "Provide detailed technical explanations. Assume technical audience." |
| Executive | High-level, ROI-focused | "Focus on business outcomes, ROI, and strategic value." |
| Supportive | Patient, educational | "Be patient and educational. Explain concepts thoroughly." |

---

## Appendix B: Lifecycle Stages

| Stage | Description | Typical Actions |
|-------|-------------|-----------------|
| Lead | Initial contact, unknown intent | Qualify, understand needs |
| Prospect | Expressed interest, exploring | Demo, technical discussion |
| Opportunity | Active evaluation, potential deal | Proposal, scoping |
| Customer | Signed, active project | Delivery, support |
| Churned | Lost or ended relationship | Win-back, feedback |

---

*Document Version: 1.0*
*Last Updated: December 2024*
