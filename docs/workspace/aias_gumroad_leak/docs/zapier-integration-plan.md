# Zapier Integration — Full Platform Coverage + AiO Node Integration

## Objective
Build a complete Zapier integration for AiAssist Secure that exposes the entire platform API surface as Zapier triggers, actions, and searches. Additionally, add native "Zapier" nodes to the AiO canvas editor so users can send/receive data to/from Zapier within their visual workflows.

## Scope

### Part A: Zapier App (Backend + CLI Package)

Create a Zapier app package using the Zapier CLI (`zapier-platform-core` + `zapier-platform-cli`) that wraps the existing AiAS REST API. Authentication uses the existing `aai_` API key system (Bearer token).

#### Authentication
- **Type**: API Key (custom auth)
- **Header**: `Authorization: Bearer aai_xxx`
- **Test endpoint**: `GET /api/users/me` to validate the key
- No OAuth needed — the existing API key system is already robust

#### Triggers (data flowing FROM AiAS → Zapier)
Triggers use polling or webhooks to notify Zapier when something happens in AiAS:

| # | Trigger | API Endpoint | Type |
|---|---------|-------------|------|
| 1 | New Chat Message | `GET /api/workspaces/{id}/messages` (poll latest) | Polling |
| 2 | New Workspace Created | `GET /api/workspaces` (poll for new) | Polling |
| 3 | New Artifact Created | `GET /api/artifacts` (poll for new) | Polling |
| 4 | New Contact | `GET /api/contacts` (poll for new) | Polling |
| 5 | New Lead Captured | `GET /api/leads/check/{id}` (poll) | Polling |
| 6 | AiO Workflow Completed | `GET /api/aio/workflows/{id}/runs` (poll for completed runs) | Polling |
| 7 | AiO Approval Needed | `GET /api/aio/approvals?status=pending` (poll) | Polling |
| 8 | New Document Uploaded | `GET /api/documents` (poll for new) | Polling |
| 9 | New Blog Post Generated | `GET /api/blog/blogs/{id}/posts` (poll) | Polling |
| 10 | Subscription Changed | `GET /api/billing/my-subscription` (poll for status change) | Polling |
| 11 | AiO Webhook (Instant) | Register/deregister via REST hook pattern using `POST /api/aio/hooks/{hook_id}` | REST Hook |

#### Actions (data flowing FROM Zapier → AiAS)
Actions let Zapier send data into AiAS:

| # | Action | API Endpoint | Method |
|---|--------|-------------|--------|
| 1 | Send Chat Message | `/api/workspaces/{id}/messages` | POST |
| 2 | Create Workspace | `/api/workspaces` | POST |
| 3 | Create Contact | `/api/contacts` | POST |
| 4 | Update Contact Lifecycle | `/api/contacts/{id}/lifecycle` | PATCH |
| 5 | Create Artifact | `/api/artifacts` | POST |
| 6 | Update Artifact | `/api/artifacts/{id}` | PATCH |
| 7 | Trigger AiO Workflow | `/api/aio/workflows/{id}/trigger` | POST |
| 8 | Approve/Reject AiO Task | `/api/aio/approvals/{id}/respond` | POST |
| 9 | Upload Document | `/api/documents/upload` | POST |
| 10 | Generate Blog Post | `/api/blog/blogs/{id}/generate/post` | POST |
| 11 | Generate Image | `/api/image-gen/generate` | POST |
| 12 | Synthesize Speech (TTS) | `/api/tts/synthesize` | POST |
| 13 | Create Environment | `/api/quests/environments` | POST |
| 14 | Run Code in Runtime | `/api/quests/environments/{id}/run` | POST |
| 15 | Chat with AI (Completions) | `/api/v1/chat/completions` | POST |
| 16 | Web Extract | `/api/web-extraction/extract` | POST |
| 17 | Create Directive | `/api/directives` | POST |
| 18 | Add Memory Fact | `/api/workspaces/{id}/memory/facts` | POST |
| 19 | Capture Lead | `/api/leads/capture` | POST |

#### Searches (lookup existing data)

| # | Search | API Endpoint | Method |
|---|--------|-------------|--------|
| 1 | Find Workspace | `/api/workspaces` | GET (filter by name) |
| 2 | Find Contact | `/api/contacts` | GET (filter by name/email) |
| 3 | Find Artifact | `/api/artifacts` | GET (filter by type/name) |
| 4 | Find AiO Workflow | `/api/aio/workflows` | GET (filter by name) |
| 5 | Get AiO Run Detail | `/api/aio/runs/{id}/detail` | GET |
| 6 | Find Document | `/api/documents` | GET (filter) |
| 7 | Find Blog | `/api/blog/blogs` | GET |
| 8 | Get Usage Stats | `/api/users/usage` | GET |

### Part B: Backend Support Endpoints

Add a few lightweight endpoints to support Zapier's polling/deduplication patterns:

1. **`GET /api/integrations/zapier/poll/{resource}`** — A unified polling endpoint that returns items sorted by `created_at` DESC with `since` parameter for deduplication. Covers: messages, workspaces, artifacts, contacts, leads, documents, blog_posts, aio_runs, aio_approvals. This avoids modifying existing endpoints.

2. **`POST /api/integrations/zapier/hooks`** — Register a Zapier REST Hook (subscribe URL) for instant AiO workflow triggers.

3. **`DELETE /api/integrations/zapier/hooks/{hook_id}`** — Unsubscribe a REST Hook.

4. **`GET /api/integrations/zapier/auth/test`** — Lightweight auth test that returns `{ user_id, org_id, plan, email }`.

All endpoints use the existing `aai_` API key auth — no new auth system needed.

### Part C: AiO Canvas Nodes — "Zapier In" & "Zapier Out"

Add two new node types to the AiO visual editor so workflows can interact with Zapier natively:

#### Node: `zapier_webhook_in` (Trigger Node)
- **Category**: Triggers
- **Purpose**: Receive data from Zapier into an AiO workflow
- **Config**: Auto-generates a unique webhook URL (uses existing `hook_id` mechanism)
- **Behavior**: Same as `webhook_trigger` but branded with Zapier icon and helper text showing the URL to paste into Zapier
- **Config Panel**: Shows the generated webhook URL with a copy button, payload preview, and field mapping

#### Node: `zapier_webhook_out` (Action Node)
- **Category**: Tools
- **Purpose**: Send data from an AiO workflow step TO a Zapier webhook (Catch Hook)
- **Config**: `webhook_url` (the Zapier Catch Hook URL), `payload_template` (JSON template with `{{node.field}}` variables)
- **Behavior**: HTTP POST to the Zapier Catch Hook URL with the resolved payload
- **Engine**: Reuse `_execute_http_node` logic with preset method=POST and content-type=application/json

#### Frontend Changes (AioCanvas.tsx)
- Add both nodes to the Node Palette under a new "Integrations" category (purple icon)
- Config panel forms for each node type
- Zapier-branded icons (use the Zapier "Z" bolt icon as SVG)

#### Backend Changes (aio_engine.py)
- Register `zapier_webhook_in` as alias for `webhook_trigger` in `_execute_node`
- Add `zapier_webhook_out` handler that POSTs to the configured URL with resolved template

### Part D: Zapier App Package Structure

```
zapier-app/
├── package.json
├── index.js                    # App definition (auth, triggers, actions, searches)
├── authentication.js           # API key auth config
├── triggers/
│   ├── newMessage.js
│   ├── newWorkspace.js
│   ├── newArtifact.js
│   ├── newContact.js
│   ├── newLead.js
│   ├── aioWorkflowCompleted.js
│   ├── aioApprovalNeeded.js
│   ├── newDocument.js
│   ├── newBlogPost.js
│   ├── subscriptionChanged.js
│   └── aioWebhook.js          # REST Hook (instant trigger)
├── actions/
│   ├── sendMessage.js
│   ├── createWorkspace.js
│   ├── createContact.js
│   ├── updateContactLifecycle.js
│   ├── createArtifact.js
│   ├── updateArtifact.js
│   ├── triggerAioWorkflow.js
│   ├── approveAioTask.js
│   ├── uploadDocument.js
│   ├── generateBlogPost.js
│   ├── generateImage.js
│   ├── synthesizeSpeech.js
│   ├── createEnvironment.js
│   ├── runCode.js
│   ├── chatCompletion.js
│   ├── webExtract.js
│   ├── createDirective.js
│   ├── addMemoryFact.js
│   └── captureLead.js
├── searches/
│   ├── findWorkspace.js
│   ├── findContact.js
│   ├── findArtifact.js
│   ├── findAioWorkflow.js
│   ├── getAioRunDetail.js
│   ├── findDocument.js
│   ├── findBlog.js
│   └── getUsageStats.js
└── test/
    ├── triggers.test.js
    ├── actions.test.js
    └── searches.test.js
```

## Files to Create/Modify

### New Files
- `zapier-app/` — Entire Zapier CLI app package (see structure above)
- `aias_production_clone/api/routes/zapier_integration.py` — Polling + hook endpoints
- `aias_production_clone/api/services/zapier_hooks.py` — REST Hook subscription management (Redis-backed)

### Modified Files
- `aias_production_clone/api/main.py` — Mount zapier_integration router
- `aias_production_clone/api/services/aio_engine.py` — Add `zapier_webhook_in` alias + `zapier_webhook_out` handler + fire REST hooks on run completion
- `aias_production_clone/client/src/pages/AioCanvas.tsx` — Add Integrations category, Zapier In/Out nodes, config panels, Zapier icons
- `aias_production_clone/api/routes/aio.py` — Hook registration endpoints for REST Hook pattern

### Sync Files (after all changes)
- Copy all modified files from `aias_production_clone/` → `aias_production/`

## Acceptance Criteria
1. Zapier app package builds and passes `zapier validate`
2. All 11 triggers return properly deduplicated data with `id` field
3. All 19 actions successfully call the corresponding AiAS endpoints
4. All 8 searches return filtered results
5. REST Hook trigger fires instantly when an AiO workflow completes
6. `zapier_webhook_in` node shows copyable webhook URL in the AiO config panel
7. `zapier_webhook_out` node sends HTTP POST to Zapier Catch Hooks with template-resolved payloads
8. Both new nodes appear in the AiO Node Palette under "Integrations" category
9. Auth test validates `aai_` API keys correctly
10. All backend polling endpoints support `since` parameter for deduplication

## Technical Notes
- Zapier CLI apps use `zapier-platform-core` v15+ (Node.js)
- Polling triggers must return items with a unique `id` field (Zapier uses this for dedup)
- REST Hook triggers use subscribe/unsubscribe pattern (Zapier manages the lifecycle)
- The Zapier app is a standalone Node.js package — does NOT run inside AiAS
- All Zapier → AiAS communication uses the public API with `aai_` keys
- AiO engine changes are minimal — `zapier_webhook_in` is an alias, `zapier_webhook_out` is just a POST
- No new auth system — everything piggybacks on existing API key infrastructure
