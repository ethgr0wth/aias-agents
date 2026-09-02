# Quests Builder Integration - AiAS Work Plan

**Version:** 1.1  
**Date:** January 2, 2026  
**Status:** ✅ APPROVED by Oracle 5.2

---

## Oracle Review Summary

**Verdict:** APPROVED with minor adjustments (clarifications, not rewrites)

**Key Confirmations:**
- Option A (Embedded Engine) is the correct call
- Use AiAS LLM adapters (treat Quests ai-gateway as reference only)
- Path-based preview routing for V1 (not subdomains)
- Phase 1 + 2 are launch-blocking; rest is iterative
- Confidence assessment (85%) is accurate

---

## Executive Summary

Integrate the open-source [QuestsOrg](https://github.com/quests-org/quests) app builder engine into AiAS as a free member benefit. The integration follows **Option A: Embedded Engine** - Quests core packages run within the existing AiAS FastAPI backend, with organization-scoped isolation.

**Goal:** Launch a web-deployable, multi-user AI app builder that:
- Drives AiAS subscriptions
- Provides hosted dev environments for non-technical users
- Preserves BYO-LLM philosophy
- Prepares API contracts for future mobile (Capacitor) client

---

## 1. Architecture Overview

### 1.1 Current AiAS Stack
```
┌─────────────────────────────────────────────────────────┐
│                     AiAS Platform                        │
├─────────────────────────────────────────────────────────┤
│  Frontend: React + Vite + TailwindCSS + shadcn/ui       │
│  Backend:  Express (proxy) → FastAPI (business logic)   │
│  Storage:  Redis (primary) + PostgreSQL (schema/future) │
│  Auth:     Session-based, org/user scoping              │
│  LLM:      BYOK - 11 providers supported                │
│  WebSocket: Socket.IO for real-time features            │
└─────────────────────────────────────────────────────────┘
```

### 1.2 Quests Engine Components (from repo analysis)
```
quests/
├── apps/studio/          # Electron app (SKIP - desktop only)
├── packages/
│   ├── ai-gateway/       # LLM adapters, streaming (REFERENCE ONLY - use AiAS adapters)
│   ├── workspace/        # File ops, tool execution (USE)
│   ├── chat/             # Chat orchestration (USE)
│   ├── tools/            # Tool definitions & routing (USE)
│   ├── ui/               # React components (EVALUATE)
│   └── shared/           # Types, utils (USE)
├── registry/             # Templates submodule (USE)
└── patches/              # Dependency patches (USE if needed)
```

### 1.3 Integrated Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                      AiAS Platform                           │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                   React Frontend                        │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │ │
│  │  │  Dashboard   │  │Code Generator│  │Quests Builder│  │ │
│  │  │  (existing)  │  │  (existing)  │  │   (NEW)      │  │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  │ │
│  └────────────────────────────────────────────────────────┘ │
│                              │                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                   FastAPI Backend                       │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │ │
│  │  │ /api/auth    │  │ /api/user    │  │ /api/quests  │  │ │
│  │  │ /api/ws      │  │ /api/admin   │  │   (NEW)      │  │ │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  │ │
│  │                                            │            │ │
│  │  ┌─────────────────────────────────────────────────┐   │ │
│  │  │            Quests Engine (Embedded)              │   │ │
│  │  │  ┌────────────┐ ┌────────────┐ ┌─────────────┐  │   │ │
│  │  │  │ AI Gateway │ │ Workspace  │ │ Tool Router │  │   │ │
│  │  │  │ (adapters) │ │ (file ops) │ │ (execution) │  │   │ │
│  │  │  └────────────┘ └────────────┘ └─────────────┘  │   │ │
│  │  └─────────────────────────────────────────────────┘   │ │
│  └────────────────────────────────────────────────────────┘ │
│                              │                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                    Storage Layer                        │ │
│  │  ┌──────────────┐  ┌───────────────────────────────┐   │ │
│  │  │    Redis     │  │  Scoped File System           │   │ │
│  │  │ (sessions,   │  │  /data/quests/{org}/{env}/    │   │ │
│  │  │  env config) │  │                               │   │ │
│  │  └──────────────┘  └───────────────────────────────┘   │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Data Models

### 2.1 Quests Environment
```python
class QuestsEnvironment:
    id: str                    # UUID
    org_id: str                # Owner organization
    user_id: str               # Creator user
    name: str                  # Display name
    description: str           # Optional description
    template_id: str | None    # Source template (if any)
    status: str                # active, paused, archived
    llm_provider: str          # groq, openai, anthropic, etc.
    llm_model: str             # Model ID for this environment
    file_root: str             # /data/quests/{org_id}/{env_id}/
    preview_port: int | None   # Assigned preview port (if running)
    created_at: datetime
    updated_at: datetime
    
    # Runtime state (not persisted)
    is_running: bool
    build_status: str          # idle, building, ready, error
```

### 2.2 Quests Chat Message
```python
class QuestsChatMessage:
    id: str
    environment_id: str
    role: str                  # user, assistant, system, tool
    content: str
    tool_calls: list | None    # For assistant tool invocations
    tool_results: list | None  # For tool responses
    files_created: list | None # Files created during this turn
    files_modified: list | None
    timestamp: datetime
```

### 2.3 Quests Template
```python
class QuestsTemplate:
    id: str
    name: str
    description: str
    category: str              # react, node, python, fullstack, etc.
    framework: str             # vite, next, hono, fastapi, etc.
    thumbnail_url: str | None
    files: dict                # Template file structure
    is_official: bool
```

---

## 3. API Specification

### 3.1 Environment Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/quests/environments` | List all environments for current org |
| POST | `/api/quests/environments` | Create new environment |
| GET | `/api/quests/environments/{id}` | Get environment details |
| PATCH | `/api/quests/environments/{id}` | Update environment settings |
| DELETE | `/api/quests/environments/{id}` | Archive/delete environment |
| POST | `/api/quests/environments/{id}/start` | Start environment runtime |
| POST | `/api/quests/environments/{id}/stop` | Stop environment runtime |

### 3.2 Chat & AI

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/quests/environments/{id}/chat` | Send message, get AI response |
| GET | `/api/quests/environments/{id}/chat/history` | Get chat history |
| DELETE | `/api/quests/environments/{id}/chat/history` | Clear chat history |
| POST | `/api/quests/environments/{id}/chat/regenerate` | Regenerate last response |

### 3.3 File Operations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/quests/environments/{id}/files/tree` | Get file tree |
| GET | `/api/quests/environments/{id}/files/read` | Read file content |
| POST | `/api/quests/environments/{id}/files/write` | Write file content |
| POST | `/api/quests/environments/{id}/files/mkdir` | Create directory |
| DELETE | `/api/quests/environments/{id}/files/delete` | Delete file/directory |
| POST | `/api/quests/environments/{id}/files/rename` | Rename/move file |

### 3.4 Tools & Execution

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/quests/tools` | List available tools |
| POST | `/api/quests/environments/{id}/tools/run` | Execute tool manually |
| GET | `/api/quests/environments/{id}/terminal` | Get terminal output |
| POST | `/api/quests/environments/{id}/terminal` | Send terminal command |

### 3.5 Preview & Build

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/quests/environments/{id}/preview` | Get preview URL |
| POST | `/api/quests/environments/{id}/build` | Trigger build |
| GET | `/api/quests/environments/{id}/build/status` | Get build status |
| GET | `/api/quests/environments/{id}/build/logs` | Get build logs |

### 3.6 Templates

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/quests/templates` | List available templates |
| GET | `/api/quests/templates/{id}` | Get template details |
| POST | `/api/quests/templates/{id}/use` | Create environment from template |

---

## 4. WebSocket Events

### 4.1 Client → Server
```typescript
// Join environment room
socket.emit('quests:join', { environment_id: string })

// Leave environment room
socket.emit('quests:leave', { environment_id: string })

// Send chat message (streaming)
socket.emit('quests:chat', { 
  environment_id: string, 
  message: string 
})

// Cancel ongoing generation
socket.emit('quests:cancel', { environment_id: string })
```

### 4.2 Server → Client
```typescript
// Chat token streaming
socket.on('quests:chat:token', { 
  environment_id: string,
  token: string,
  message_id: string 
})

// Chat complete
socket.on('quests:chat:complete', {
  environment_id: string,
  message: QuestsChatMessage
})

// Tool execution
socket.on('quests:tool:start', { tool_name: string, args: object })
socket.on('quests:tool:complete', { tool_name: string, result: object })

// File changes
socket.on('quests:file:created', { path: string })
socket.on('quests:file:modified', { path: string })
socket.on('quests:file:deleted', { path: string })

// Build updates
socket.on('quests:build:log', { line: string, level: string })
socket.on('quests:build:status', { status: string })

// Preview updates
socket.on('quests:preview:ready', { url: string })
socket.on('quests:preview:error', { error: string })
```

---

## 5. Security & Isolation

### 5.1 File System Isolation
- Each environment's `file_root` is strictly enforced
- Path traversal attacks prevented via normalization + validation
- All file operations resolve paths relative to environment root
- No symlinks allowed outside environment directory

### 5.2 Resource Limits
- Max environments per org: 10 (free), 50 (pro), unlimited (enterprise)
- Max file size: 10MB per file
- Max total storage per environment: 500MB
- Max concurrent builds: 1 per environment
- Build timeout: 5 minutes

### 5.3 LLM Key Management
- BYO-LLM keys stored encrypted in Redis (same as existing AiAS pattern)
- Keys scoped to environment or inherited from org settings
- Never logged or exposed in API responses
- **LLM Default Fallback Order** (Oracle approved):
  1. Environment-specific LLM (if set)
  2. Org default LLM
  3. User default LLM
  4. Block creation only if none exist

### 5.4 Preview Server Security
- Preview ports dynamically assigned from pool (9000-9999)
- **V1: Path-based routing** (Oracle approved) - Express proxies `/quests/:id/preview/*` to localhost preview port
- Preview servers bind to localhost only, proxied through Express
- Preview servers sandboxed to environment directory
- Auto-shutdown after 30 minutes of inactivity

---

## 6. UI Components

### 6.1 New Pages
| Route | Component | Description |
|-------|-----------|-------------|
| `/quests` | QuestsPortal | Main landing page with environment list |
| `/quests/:id` | QuestsWorkspace | Full workspace view with chat, files, preview |
| `/quests/new` | QuestsNewEnvironment | Template selection & environment creation |
| `/quests/settings` | QuestsSettings | Org-level Quests settings |

### 6.2 Workspace Layout
```
┌─────────────────────────────────────────────────────────────┐
│  [Logo] Quests Builder    [Env Name ▼]    [Settings] [User] │
├──────────────────┬──────────────────────────────────────────┤
│                  │                                          │
│   File Explorer  │              Chat Interface              │
│   ┌───────────┐  │   ┌────────────────────────────────────┐ │
│   │ 📁 src    │  │   │ User: Build me a todo app         │ │
│   │  ├ App.tsx│  │   │ AI: I'll create a React todo...   │ │
│   │  └ main.ts│  │   │ [files created: App.tsx, ...]     │ │
│   │ 📁 public │  │   └────────────────────────────────────┘ │
│   │ package.js│  │   ┌────────────────────────────────────┐ │
│   └───────────┘  │   │ [Type your message...]        [▶]  │ │
│                  │   └────────────────────────────────────┘ │
├──────────────────┴──────────────────────────────────────────┤
│  [Terminal]  [Build Logs]  [Preview: http://env.preview...] │
│  ┌──────────────────────────────────────────────────────────┤
│  │ $ npm run dev                                            │
│  │ > vite                                                   │
│  │ ready in 234ms                                           │
│  └──────────────────────────────────────────────────────────┘
└─────────────────────────────────────────────────────────────┘
```

### 6.3 Navigation Integration
Add "Quests Builder" to main AiAS navigation:
```
Dashboard | Workspaces | Code Generator | Quests Builder | Admin
```

---

## 7. Implementation Phases

### Phase 1: Foundation (Day 1)
- [ ] Clone QuestsOrg repo into `/quests-engine`
- [ ] Analyze package structure, identify usable modules
- [ ] Create data models in Redis storage
- [ ] Implement environment CRUD endpoints
- [ ] Basic file system isolation

### Phase 2: Core Engine (Day 2)
- [ ] Integrate Quests AI gateway or use existing AiAS LLM adapters
- [ ] Implement chat endpoint with streaming
- [ ] Implement file operations endpoints
- [ ] Add Socket.IO events for real-time updates

### Phase 3: UI Portal (Day 3)
- [ ] Create QuestsPortal page with environment list
- [ ] Create QuestsWorkspace with chat interface
- [ ] Create file explorer component
- [ ] Add template selection flow
- [ ] Integrate with navigation

### Phase 4: Build & Preview (Day 4)
- [ ] Implement build process management
- [ ] Add preview server routing
- [ ] Terminal output streaming
- [ ] Build logs display

### Phase 5: Polish & Mobile Prep (Day 5+)
- [ ] Onboarding flow for new users
- [ ] Error handling and edge cases
- [ ] Performance optimization
- [ ] Document API for Capacitor client
- [ ] Add to subscription/pricing tiers

---

## 8. Dependencies & Decisions

### 8.1 Open Questions
1. **Quests AI Gateway vs AiAS Adapters**: Should we use Quests' `ai-gateway` package or leverage our existing 11-provider infrastructure?
   - **Recommendation**: Use existing AiAS LLM infrastructure - already battle-tested, supports more providers, has our BYOK patterns

2. **Template Registry**: How do we sync/host templates?
   - **Recommendation**: Clone registry submodule, serve from `/api/quests/templates`, cache in Redis

3. **Preview Hosting**: How do we expose preview servers?
   - **Recommendation**: Use path-based routing through Express proxy: `/:env_id/preview/*` → localhost:preview_port

### 8.2 Technical Dependencies
- Node.js packages from Quests: May need pnpm workspace compatibility
- Potential TypeScript→Python bridge for Quests tools
- File watcher for real-time file sync

### 8.3 Risks
| Risk | Mitigation |
|------|------------|
| Quests packages have Electron dependencies | Carefully extract only headless components |
| Resource exhaustion from multiple environments | Implement strict limits, auto-pause inactive |
| Complex build process integration | Start with simple npm/pnpm commands |

---

## 9. Success Metrics

- **Launch**: Functional environment creation + chat in 3 days
- **Usage**: 10+ environments created in first week
- **Stability**: <1% error rate on chat completions
- **Performance**: <500ms cold start for environment API calls

---

## 10. Mobile Client Notes (Future)

The API is designed to be consumed by a Capacitor mobile client:
- All endpoints are stateless HTTP + WebSocket
- No web-specific assumptions (no cookies required, token auth supported)
- File tree as JSON (not HTML)
- Preview URLs work in mobile WebView
- WebSocket events for real-time updates work cross-platform

---

## Appendix A: File Structure After Integration

```
/
├── api/
│   ├── routes/
│   │   ├── quests.py           # NEW: Quests API endpoints
│   │   └── ...
│   ├── services/
│   │   ├── quests_engine.py    # NEW: Quests business logic
│   │   ├── quests_files.py     # NEW: Scoped file operations
│   │   └── ...
│   └── ...
├── client/src/
│   ├── pages/
│   │   ├── QuestsPortal.tsx    # NEW: Environment list
│   │   ├── QuestsWorkspace.tsx # NEW: Full workspace
│   │   └── ...
│   ├── components/
│   │   ├── quests/             # NEW: Quests-specific components
│   │   │   ├── FileExplorer.tsx
│   │   │   ├── ChatPane.tsx
│   │   │   ├── PreviewPane.tsx
│   │   │   └── TerminalPane.tsx
│   │   └── ...
│   └── ...
├── quests-engine/              # NEW: Cloned Quests repo
│   ├── packages/               # Core packages we use
│   └── registry/               # Template submodule
├── data/
│   └── quests/                 # NEW: Environment file storage
│       └── {org_id}/
│           └── {env_id}/
└── docs/
    └── quests-integration-workplan.md  # This document
```

---

## Approval

- [x] Architecture approved ✅
- [x] Data models approved ✅
- [x] API design approved ✅
- [x] UI wireframes approved ✅
- [x] Security review completed ✅
- [x] Ready to proceed with implementation ✅

**Approved by:** Oracle 5.2 (GPT) | January 2, 2026

---

*Document prepared by AI Agent | Last updated: January 2, 2026*
