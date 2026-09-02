---
title: Voice Playground
description: Specifications for BYOK TTS and Voice Action Buttons.
category: Agents
icon: Mic
order: 2
---

# AI Voice Playground Enhancement Specification

**Version:** 1.0  
**Status:** Draft

## Overview

Enhance the AI Voice system platform-wide with a focus on the Oracle Playground experience. This specification covers BYOK Google TTS integration, voice action buttons for intelligent transcript processing, and seamless voice-text complementary input.

## Goals

1. **BYOK Google TTS** - Users bring their own Google Cloud credentials, bypassing platform usage limits
2. **Playground Voice Integration** - Add TTS playback to complement existing STT on the playground
3. **Voice Action Buttons** - Intelligent processing buttons with configurable scope
4. **Subscriber-Only Access** - All voice features require active subscription and API key authentication

---

## 1. BYOK Google TTS Credentials

### User Flow

1. User navigates to Dashboard → Provider Settings
2. Clicks "Add Google TTS Credentials"
3. Uploads or pastes service account JSON
4. System validates JSON structure and stores encrypted
5. TTS requests automatically use user's credentials

### Storage Schema

```
Redis Key: {namespace}:user_provider_keys:{user_id}:google_tts
Value: {
  "credentials_json": "<encrypted>",
  "project_id": "extracted-from-json",
  "created_at": "ISO8601",
  "last_used_at": "ISO8601",
  "total_chars_synthesized": 0
}
```

### API Endpoints

#### `POST /api/user/provider-keys/google-tts`
Add or update Google TTS credentials.

**Request:**
```json
{
  "credentials_json": "{...service account JSON...}"
}
```

---

## 2. TTS Service with BYOK Support

### Updated Synthesis Flow

```
1. Receive synthesis request with user_id
2. Check for user's BYOK credentials
3. If BYOK exists:
   a. Use user's credentials (no platform limit check)
   b. Track usage in user's stats (for their visibility)
4. If no BYOK:
   a. Check platform usage limits
   b. Use platform credentials with fallback logic
5. Return audio + metadata
```

---

## 3. Playground Voice Integration

### Component Structure

```
OraclePlayground
├── Chat Area (existing)
│   └── Message bubbles with "Listen" button
├── Input Area
│   ├── Text input (existing)
│   ├── Voice input button (STT)
│   └── Send button
├── Voice Action Bar (NEW)
│   ├── Scope Toggle: [All Future] / [Next Only]
│   └── Action Buttons:
│       ├── Explain Content
│       ├── Summarize Content
│       ├── Extract Actions
│       └── Decision Rec
└── Voice Settings Panel (collapsible)
    ├── Voice selection
    ├── Speaking rate
    └── Auto-TTS toggle
```

---

## 4. Voice Action Buttons

### Button Definitions

| Button | Icon | Purpose | AI Prompt Template |
|--------|------|---------|-------------------|
| Explain Content | 💡 | Turn raw input into understanding | "Explain the following in clear, simple terms..." |
| Summarize Content | 📝 | Reduce noise | "Provide a concise summary of the key points..." |
| Extract Action Items | ✅ | Turn talk into work | "Extract all action items, tasks, and to-dos..." |
| Decision Recommendation | ⚖️ | Judgment, not generation | "Analyze the following and provide a recommendation..." |

### Scope Toggle

**"All Future" Mode:**
- Button stays active (highlighted)
- All subsequent messages are processed with the selected action
- Processing uses full conversation transcript as context
- Deactivate by clicking the button again

**"Next Only" Mode:**
- Button triggers one-time processing
- Only the next voice message is processed
- Returns to normal mode after processing

---

## 5. Voice Action API Endpoints

All endpoints require:
- Active subscription (`require_paid_plan`)
- Valid API key authentication

### `POST /api/voice/actions/explain`
**Subscriber-only with API key**

Process content with explanation prompt.

**Request:**
```json
{
  "content": "The quarterly projections show...",
  "context": ["previous message 1", "previous message 2"],
  "include_audio": true,
  "voice_id": "en-US-Chirp3-HD-Puck"
}
```

---

## 6. Authentication & Authorization

### Subscriber Check

```python
async def require_voice_access(user: User = Depends(get_current_user)):
    """Ensure user has voice feature access (paid plan)."""
    if user.plan == PlanType.free:
        raise HTTPException(
            status_code=403,
            detail="Voice features require an active subscription"
        )
    return user
```

### API Key Authentication

All `/api/voice/*` endpoints support both:
1. Session-based auth (for playground UI)
2. API key auth via `Authorization: Bearer aai_xxx` header (for Zapier)

---

## 7. UI/UX Specifications

### Voice Action Bar Design

```
┌─────────────────────────────────────────────────────────────┐
│  Scope: [All Future ▼]                                      │
│                                                             │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ 💡       │ │ 📝       │ │ ✅       │ │ ⚖️        │       │
│  │ Explain  │ │ Summarize│ │ Actions  │ │ Decide   │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### Button States

- **Inactive:** `bg-white/5 border-white/10`
- **Hover:** `bg-white/10 border-white/20`
- **Active (All Future mode):** `bg-purple-500/20 border-purple-500/50 ring-1 ring-purple-500/30`
- **Processing:** Subtle pulse animation

---

## 8. Implementation Phases

### Phase 1: BYOK Google TTS
1. Add credential storage endpoints
2. Update TTS synthesis to check for BYOK
3. Add UI for credential management in Dashboard

### Phase 2: Playground TTS
1. Add "Listen" button to AI response messages
2. Add voice settings panel
3. Add auto-TTS toggle

### Phase 3: Voice Action Buttons
1. Create action prompt templates
2. Build voice action API endpoints
3. Add action bar UI to playground
4. Implement scope toggle logic

### Phase 4: Polish & Integration
1. Add loading states and error handling
2. Optimize audio streaming
3. Document API for Zapier integration

---

## 10. Security Considerations

1. **Credential Encryption:** Google service account JSON encrypted at rest
2. **Credential Isolation:** Users can only access their own credentials
3. **Audit Logging:** Track credential additions/removals
4. **Rate Limiting:** Prevent abuse even with BYOK (per-minute limits)
5. **No Credential Echo:** Never return raw credentials in API responses
