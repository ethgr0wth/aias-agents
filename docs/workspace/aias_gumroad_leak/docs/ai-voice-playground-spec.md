# AI Voice Playground Enhancement Specification

**Version:** 1.0  
**Date:** December 2025  
**Status:** Draft

## Overview

Enhance the AI Voice system platform-wide with a focus on the Oracle Playground experience. This specification covers BYOK Google TTS integration, voice action buttons for intelligent transcript processing, and seamless voice-text complementary input.

## Goals

1. **BYOK Google TTS** - Users bring their own Google Cloud credentials, bypassing platform usage limits
2. **Playground Voice Integration** - Add TTS playback to complement existing STT on the playground
3. **Voice Action Buttons** - Intelligent processing buttons with configurable scope
4. **Subscriber-Only Access** - All voice features require active subscription and API key authentication

## Architecture

### Current State

- **STT (Speech-to-Text):** Browser-native Web Speech API via `useVoiceToText` hook
- **TTS (Text-to-Speech):** Google Cloud TTS via `/api/tts/synthesize` with platform credentials
- **Usage Limits:** Per-protocol monthly limits (Wavenet: 1M chars, Chirp: 1M chars)
- **Voice Component:** `VoiceSession.tsx` with `ElectricOrb` visualization

### Target State

- **BYOK TTS:** Users can provide their own Google Cloud service account JSON
- **Priority Order:** User credentials → Platform credentials (with limits)
- **Action Buttons:** 4 AI-powered processing modes with scope toggle
- **API-First Design:** All endpoints designed for external integration (Zapier)

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

### Credential Validation

Before storing, validate:
- Valid JSON structure
- Required fields: `type`, `project_id`, `private_key`, `client_email`
- `type` must be `"service_account"`
- Optionally: Test synthesize with a short phrase

### API Endpoints

#### `POST /api/user/provider-keys/google-tts`
Add or update Google TTS credentials.

**Request:**
```json
{
  "credentials_json": "{...service account JSON...}"
}
```

**Response:**
```json
{
  "success": true,
  "project_id": "my-project-123",
  "message": "Google TTS credentials saved successfully"
}
```

#### `GET /api/user/provider-keys/google-tts`
Check if user has Google TTS credentials configured.

**Response:**
```json
{
  "configured": true,
  "project_id": "my-project-123",
  "created_at": "2025-12-29T10:00:00Z",
  "total_chars_synthesized": 45000
}
```

#### `DELETE /api/user/provider-keys/google-tts`
Remove user's Google TTS credentials.

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

### API Endpoint Updates

#### `POST /api/tts/synthesize` (Enhanced)

**Request:**
```json
{
  "text": "Hello world",
  "voice_id": "en-US-Chirp3-HD-Puck",
  "speaking_rate": 1.0,
  "pitch": 0.0
}
```

**Response:**
```json
{
  "audio_content": "<base64>",
  "duration_seconds": 1.2,
  "voice_used": "en-US-Chirp3-HD-Puck",
  "protocol_used": "chirp",
  "is_fallback": false,
  "credentials_source": "byok",  // NEW: "byok" | "platform"
  "usage_chars": 11
}
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

### Voice Features

1. **STT Input** - Click mic, speak, transcript appears in input field
2. **TTS Output** - Click "Listen" on any AI response to hear it
3. **Auto-TTS Mode** - Toggle to automatically speak AI responses
4. **Action Buttons** - Process input/transcript with specific AI prompts

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

### State Management

```typescript
interface VoiceActionState {
  activeAction: 'explain' | 'summarize' | 'extract' | 'decision' | null;
  scope: 'all_future' | 'next_only';
  isProcessing: boolean;
}
```

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

**Response:**
```json
{
  "action": "explain",
  "result": {
    "text": "This is explaining that the quarterly projections...",
    "audio_content": "<base64>",
    "tokens_used": 150
  },
  "processing_time_ms": 1200
}
```

### `POST /api/voice/actions/summarize`
**Subscriber-only with API key**

Summarize content concisely.

**Request/Response:** Same structure as explain

### `POST /api/voice/actions/extract-actions`
**Subscriber-only with API key**

Extract action items from content.

**Response includes structured data:**
```json
{
  "action": "extract_actions",
  "result": {
    "text": "Action items identified:\n1. Schedule meeting...",
    "action_items": [
      {"task": "Schedule meeting with design team", "priority": "high"},
      {"task": "Review Q4 budget proposal", "priority": "medium"}
    ],
    "audio_content": "<base64>",
    "tokens_used": 200
  }
}
```

### `POST /api/voice/actions/decision`
**Subscriber-only with API key**

Provide decision recommendation.

**Response includes structured data:**
```json
{
  "action": "decision",
  "result": {
    "text": "Based on the information provided...",
    "recommendation": "proceed",
    "confidence": 0.85,
    "key_factors": ["factor 1", "factor 2"],
    "risks": ["risk 1"],
    "audio_content": "<base64>",
    "tokens_used": 250
  }
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

```python
async def get_user_from_session_or_api_key(
    request: Request,
    session_user: Optional[User] = Depends(get_optional_current_user)
) -> User:
    # Check session first
    if session_user:
        return session_user
    
    # Check API key header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer aai_"):
        api_key = auth_header[7:]
        return validate_api_key(api_key)
    
    raise HTTPException(status_code=401, detail="Authentication required")
```

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

### Listen Button on Messages

```
┌─────────────────────────────────────────────────┐
│ AI Response text here...                        │
│                                                 │
│ [🔊 Listen] [📋 Copy]              2 mins ago  │
└─────────────────────────────────────────────────┘
```

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

## 9. Success Metrics

- **BYOK Adoption:** % of subscribers who add their own Google credentials
- **Voice Action Usage:** Number of action button invocations per user
- **TTS Engagement:** % of messages where "Listen" is clicked
- **API Integration:** External API calls to voice endpoints

---

## 10. Security Considerations

1. **Credential Encryption:** Google service account JSON encrypted at rest
2. **Credential Isolation:** Users can only access their own credentials
3. **Audit Logging:** Track credential additions/removals
4. **Rate Limiting:** Prevent abuse even with BYOK (per-minute limits)
5. **No Credential Echo:** Never return raw credentials in API responses
