# Shadow Mode Specification

## Overview

Shadow Mode enables AI-assisted responses that require human approval before reaching end users. This feature is designed for enterprise pilots, regulated industries, and teams building confidence in AI automation before enabling full autonomy.

**Version**: 1.0  
**Status**: Specification  
**Last Updated**: December 2025

---

## Philosophy

- **Speed + Trust**: AI does the drafting work, humans maintain quality control
- **Pilot-to-Production Path**: Shadow → measure accuracy → refine KB/directives → enable full AI
- **Zero End-User Disruption**: Users only see approved, polished responses
- **Learning Loop**: Human edits feed back into system improvements

---

## User Journey

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SHADOW MODE WORKFLOW                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   End User                    Dashboard                    AI System    │
│      │                           │                            │        │
│      │ "What's my order status?" │                            │        │
│      │──────────────────────────>│                            │        │
│      │                           │ draft_created event        │        │
│      │                           │<───────────────────────────│        │
│      │                           │                            │        │
│      │   (waiting...)            │ Manager reviews draft      │        │
│      │                           │                            │        │
│      │                           │ [Approve] [Edit] [Regen]   │        │
│      │                           │                            │        │
│      │                           │──── Approve ──────────────>│        │
│      │                           │                            │        │
│      │ "Your order #123 shipped" │                            │        │
│      │<──────────────────────────│                            │        │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Existing Components (Reuse)

| Component | Location | Status | Notes |
|-----------|----------|--------|-------|
| `WorkspaceMode.SHADOW` | `api/models/schemas.py` | ✅ Defined | Enum value exists, needs behavior |
| `visible_to_client` field | `api/models/schemas.py` | ✅ Exists | Already filters messages from end users |
| `require_manager` decorator | `api/routes/auth.py` | ✅ Exists | Auth for manager-only endpoints |
| WebSocket events | `api/websocket.py` | ✅ Exists | Can emit draft events |
| Dashboard workspace list | `client/src/pages/Dashboard.tsx` | ✅ Exists | Add pending drafts section |

---

## Implementation Notes (Architect Review)

### Key Integration Points

1. **MessageCreate Schema**: Must extend alongside Message model to accept draft fields during creation
2. **storage.add_message()**: Serialization logic must persist new draft fields to Redis
3. **AIOrchestrator.generate_response()**: Add optional `one_shot_directive: str` parameter for regeneration
4. **Routes avoid double-writes**: Orchestrator creates the message; routes must not duplicate

### Draft Queue Strategy

Drafts are stored in the existing message sorted set (`workspace:{id}:messages`) with `pending_approval=true`. No parallel set needed - just filter on read:

```python
# List messages (end user view)
messages = [m for m in all_messages if m.visible_to_client]

# List drafts (manager view)  
drafts = [m for m in all_messages if m.pending_approval]
```

### Response Flow in Shadow Mode

When `generate_response()` is called for a shadow-mode workspace:
1. Orchestrator generates AI response
2. Orchestrator calls `storage.add_message()` with `pending_approval=True, visible_to_client=False`
3. Orchestrator returns `None` to the calling route
4. Route returns empty AI response to end user (or "thinking" state)
5. WebSocket emits `draft_created` to dashboard subscribers

---

## Schema Changes

### Message Model Extensions

```python
# Add to api/models/schemas.py Message class

# Draft management
pending_approval: bool = False           # True if draft awaiting human review
approved_at: Optional[str] = None        # ISO timestamp when approved
approved_by: Optional[str] = None        # User ID who approved

# Edit tracking
draft_original: Optional[str] = None     # Original AI content if human edited
human_edited: bool = False               # True if human modified before approving

# Regeneration tracking
regenerate_directive: Optional[str] = None  # One-time constraint for regen
regeneration_count: int = 0                 # How many times regenerated
```

### Redis Storage Keys

```
workspace:{id}:drafts              # Set of pending draft message IDs
workspace:{id}:draft_count         # Counter for quick badge display
message:{id}:draft_metadata        # Hash with approval/edit details
```

---

## API Endpoints

### List All Pending Drafts (Org-Scoped)

```
GET /api/workspaces/drafts
```

**Auth**: Manager or Super Admin  
**Response**:
```json
{
  "drafts": [
    {
      "workspace_id": "ws_abc123",
      "workspace_name": "Support Chat",
      "user_message": "What's my order status?",
      "ai_draft": "Your order #123 is currently in transit...",
      "message_id": "msg_xyz",
      "created_at": "2024-01-15T10:30:00Z",
      "regeneration_count": 0
    }
  ],
  "total": 1
}
```

### List Workspace Drafts

```
GET /api/workspaces/{workspace_id}/drafts
```

**Auth**: Workspace owner or Manager  
**Response**: Same structure, filtered to workspace

### Approve Draft

```
POST /api/workspaces/{workspace_id}/drafts/{message_id}/approve
```

**Body** (optional):
```json
{
  "edited_content": "Modified response text"  // If human edited
}
```

**Behavior**:
1. Set `pending_approval = false`
2. Set `visible_to_client = true`
3. Set `approved_at` and `approved_by`
4. If `edited_content` provided:
   - Store original in `draft_original`
   - Set `human_edited = true`
   - Update `content` with edited version
5. Emit `draft_approved` WebSocket event
6. Remove from drafts set

### Regenerate Draft

```
POST /api/workspaces/{workspace_id}/drafts/{message_id}/regenerate
```

**Body**:
```json
{
  "directive": "Be more concise and include the tracking number"
}
```

**Behavior**:
1. Fetch original user message from context
2. Call AI orchestrator with one-time directive layered on top
3. Replace draft content with new response
4. Increment `regeneration_count`
5. Store `regenerate_directive` for analytics
6. Emit `draft_regenerated` WebSocket event

### Reject Draft

```
POST /api/workspaces/{workspace_id}/drafts/{message_id}/reject
```

**Body** (optional):
```json
{
  "manual_response": "Let me check that for you..."  // Human replies instead
}
```

**Behavior**:
1. Delete the draft message OR mark as rejected
2. If `manual_response` provided:
   - Create new message with `role: human`
   - Set `visible_to_client = true`
3. Emit `draft_rejected` WebSocket event
4. Remove from drafts set

---

## AI Orchestrator Changes

### generate_response() Modification

```python
async def generate_response(self, workspace_id: str, user_message: str, ...):
    workspace = storage.get_workspace(workspace_id)
    
    if workspace.mode == WorkspaceMode.TAKEOVER:
        return None  # Human only
    
    # Generate AI response
    ai_response = await self._call_llm(...)
    
    if workspace.mode == WorkspaceMode.SHADOW:
        # Create as draft - hidden from end user
        ai_msg = storage.add_message(
            ws_id=workspace_id,
            content=ai_response,
            role=MessageRole.AI,
            visible_to_client=False,
            pending_approval=True
        )
        storage.add_to_drafts_queue(workspace_id, ai_msg.id)
        
        # Notify dashboard
        await emit_websocket_event("draft_created", {
            "workspace_id": workspace_id,
            "message": ai_msg
        })
        
        return None  # Don't return to end user widget
    
    # Normal AI mode - immediate response
    return ai_response
```

---

## WebSocket Events

| Event | Payload | Subscribers |
|-------|---------|-------------|
| `draft_created` | `{workspace_id, message, user_message}` | Dashboard |
| `draft_approved` | `{workspace_id, message}` | End-user widget, Dashboard |
| `draft_regenerated` | `{workspace_id, message, directive}` | Dashboard |
| `draft_rejected` | `{workspace_id, message_id}` | Dashboard |

---

## Dashboard UI Components

### Pending Drafts Queue

**Location**: New section in Dashboard or dedicated page  
**Access**: Managers and above

**Features**:
- Badge count in sidebar navigation
- Queue view with columns:
  - Workspace name (link to full conversation)
  - Customer message (what they asked)
  - AI draft (the proposed response)
  - Time waiting
  - Actions
- Expandable row to see full context
- Bulk approve for batch operations

### Draft Actions UI

```
┌─────────────────────────────────────────────────────────────────┐
│ Customer: "What's your return policy?"                         │
├─────────────────────────────────────────────────────────────────┤
│ AI Draft:                                                       │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Our return policy allows returns within 30 days of         │ │
│ │ purchase. Items must be unused and in original packaging.  │ │
│ │ [editable text area]                                        │ │
│ └─────────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│ [✓ Approve]  [↻ Regenerate]  [✗ Reject & Reply]               │
│                                                                 │
│ Regenerate with: [Add 14-day exception for holidays______] [Go]│
└─────────────────────────────────────────────────────────────────┘
```

### Workspace Mode Indicator

When viewing a shadow-mode workspace:
- Clear badge: "SHADOW MODE - Drafts require approval"
- Pending draft count in header
- Visual distinction for unapproved messages

---

## Metrics & Analytics (Phase 2)

Track to measure AI quality and team efficiency:

| Metric | Description | Use |
|--------|-------------|-----|
| Approval Rate | % of drafts approved without edits | AI accuracy indicator |
| Edit Rate | % of drafts that required human edits | KB improvement signal |
| Avg Approval Time | Time from draft creation to approval | Team responsiveness |
| Regeneration Rate | % of drafts that needed regeneration | Prompt tuning signal |
| Top Edit Patterns | Common phrases humans add/remove | Directive improvements |

---

## Migration Path

### Enabling Shadow Mode

1. Workspace owner or admin sets `mode = "shadow"` via API or dashboard
2. All new AI responses become drafts
3. Existing conversation history unaffected
4. End users experience slight delay (human approval time)

### Shadow → AI Mode Transition

When team is confident in AI quality:
1. Review metrics (approval rate, edit frequency)
2. Switch workspace to `mode = "ai"`
3. All new responses go directly to users
4. Historical drafts/approvals preserved for audit

---

## Security & Permissions

| Action | Required Role |
|--------|---------------|
| View drafts (own workspaces) | Client, Reseller |
| View drafts (all org workspaces) | Manager |
| Approve/Reject drafts | Manager, Super Admin |
| Change workspace mode | Manager, Super Admin |
| View metrics | Manager, Super Admin |

---

## Risk Mitigation

- **Human attention triggers**: Still fire on drafts (flagged conversations surface immediately)
- **Rate limiting**: Preserved for all modes
- **No duplicate notifications**: Draft approval only notifies once
- **Existing workspaces**: AI mode workspaces completely unaffected
- **Graceful degradation**: If no manager available, drafts queue (don't auto-approve)

---

## Implementation Phases

### Phase 1: Core Functionality
- [ ] Message schema extensions
- [ ] Redis storage for draft queue
- [ ] Orchestrator shadow mode logic
- [ ] Basic API endpoints (list, approve, reject)
- [ ] Dashboard pending drafts list

### Phase 2: Enhanced UX
- [ ] Inline editing in dashboard
- [ ] Regenerate with directive
- [ ] WebSocket real-time updates
- [ ] Bulk approve

### Phase 3: Analytics
- [ ] Approval/edit metrics
- [ ] Time tracking
- [ ] Pattern analysis
- [ ] Reporting dashboard

---

## Open Questions

1. **Timeout behavior**: Should drafts auto-expire after X hours? Or queue indefinitely?
2. **Notification channels**: Email/Slack alerts for pending drafts?
3. **Mobile support**: Approve drafts from mobile dashboard?

---

## Appendix: Mode Comparison

| Aspect | AI Mode | Shadow Mode | Takeover Mode |
|--------|---------|-------------|---------------|
| AI generates response | ✅ Yes | ✅ Yes | ❌ No |
| Response visible immediately | ✅ Yes | ❌ No (pending) | N/A |
| Human approval required | ❌ No | ✅ Yes | N/A |
| Human can edit before send | ❌ No | ✅ Yes | ✅ Yes |
| Best for | Trusted AI, high volume | Pilots, regulated | Escalations |
