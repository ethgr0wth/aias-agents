---
title: Shadow Mode Specification
description: AI-assisted responses requiring human approval before sending.
category: Security
icon: Eye
order: 2
---

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

---

## WebSocket Events

| Event | Payload | Subscribers |
|-------|---------|-------------|
| `draft_created` | `{workspace_id, message, user_message}` | Dashboard |
| `draft_approved` | `{workspace_id, message}` | End-user widget, Dashboard |
| `draft_regenerated` | `{workspace_id, message, directive}` | Dashboard |
| `draft_rejected` | `{workspace_id, message_id}` | Dashboard |

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

## Appendix: Mode Comparison

| Aspect | AI Mode | Shadow Mode | Takeover Mode |
|--------|---------|-------------|---------------|
| AI generates response | ✅ Yes | ✅ Yes | ❌ No |
| Response visible immediately | ✅ Yes | ❌ No (pending) | N/A |
| Human approval required | ❌ No | ✅ Yes | N/A |
| Human can edit before send | ❌ No | ✅ Yes | ✅ Yes |
| Best for | Trusted AI, high volume | Pilots, regulated | Escalations |
