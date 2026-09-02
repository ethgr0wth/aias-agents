# Voice API Reference

**Version:** 1.0  
**Base URL:** `https://your-domain.com/api`  
**Authentication:** API Key (Bearer token)

## Overview

The Voice API provides text-to-speech synthesis and intelligent content processing through voice action endpoints. All endpoints require an active subscription and API key authentication.

## Authentication

Include your API key in the Authorization header:

```
Authorization: Bearer aai_your_api_key_here
```

API keys can be generated from the Dashboard under "API Keys". Both standard (`aai_`) and extended (`aai_pub_`, `aai_srv_`) keys are supported.

---

## Text-to-Speech Endpoints

### Synthesize Speech

Convert text to audio using Google Cloud TTS.

**Endpoint:** `POST /api/tts/synthesize`

**Headers:**
```
Authorization: Bearer aai_xxx
Content-Type: application/json
```

**Request Body:**
```json
{
  "text": "Hello, this is a test message.",
  "voice_id": "en-US-Chirp3-HD-Puck",
  "speaking_rate": 1.0,
  "pitch": 0.0
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `text` | string | Yes | - | Text to synthesize (max 5000 chars) |
| `voice_id` | string | No | `en-US-Wavenet-D` | Voice identifier |
| `speaking_rate` | float | No | 1.0 | Speed (0.25-4.0) |
| `pitch` | float | No | 0.0 | Pitch adjustment (-20.0 to 20.0) |

**Response:**
```json
{
  "audio_content": "//NExAAQ8...<base64 MP3>",
  "duration_seconds": 2.4,
  "voice_used": "en-US-Chirp3-HD-Puck",
  "protocol_used": "chirp",
  "is_fallback": false,
  "credentials_source": "byok",
  "usage_chars": 31
}
```

| Field | Type | Description |
|-------|------|-------------|
| `audio_content` | string | Base64-encoded MP3 audio |
| `duration_seconds` | float | Audio duration |
| `voice_used` | string | Actual voice used (may differ if fallback) |
| `protocol_used` | string | `wavenet` or `chirp` |
| `is_fallback` | boolean | Whether fallback voice was used |
| `credentials_source` | string | `byok` (user's credentials) or `platform` |
| `usage_chars` | integer | Characters synthesized |

**Errors:**
- `401` - Invalid or missing API key
- `403` - Subscription required
- `429` - Rate limit exceeded or quota exhausted
- `500` - Synthesis failed

---

### List Available Voices

Get all available TTS voices.

**Endpoint:** `GET /api/tts/voices`

**Response:**
```json
{
  "voices": [
    {
      "id": "en-US-Chirp3-HD-Puck",
      "name": "Puck",
      "gender": "Male",
      "accent": "American",
      "type": "chirp"
    },
    {
      "id": "en-US-Wavenet-D",
      "name": "David",
      "gender": "Male",
      "accent": "American",
      "type": "wavenet"
    }
  ]
}
```

---

## Voice Action Endpoints

Intelligent content processing with optional TTS response. All voice action endpoints share a common request/response structure with action-specific enhancements.

### Common Request Structure

```json
{
  "content": "The main content to process",
  "context": ["Optional array of previous messages for context"],
  "include_audio": true,
  "voice_id": "en-US-Chirp3-HD-Puck"
}
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `content` | string | Yes | - | Main content to process |
| `context` | string[] | No | `[]` | Previous messages for context |
| `include_audio` | boolean | No | `false` | Include TTS of result |
| `voice_id` | string | No | User's default | Voice for TTS |

### Common Response Structure

```json
{
  "action": "explain",
  "result": {
    "text": "The processed result text...",
    "audio_content": "<base64 if requested>",
    "tokens_used": 150
  },
  "processing_time_ms": 1200
}
```

---

### Explain Content

Transform raw input into clear, understandable explanation.

**Endpoint:** `POST /api/voice/actions/explain`

**Use Cases:**
- Explain technical jargon in simple terms
- Break down complex concepts
- Provide context for unfamiliar topics

**Example Request:**
```json
{
  "content": "The API uses OAuth 2.0 with PKCE flow for authentication, requiring a code verifier and challenge.",
  "include_audio": true
}
```

**Example Response:**
```json
{
  "action": "explain",
  "result": {
    "text": "This means the API uses a secure login method called OAuth 2.0. PKCE (pronounced 'pixie') adds extra security by creating a secret code that only your app knows. When you log in, you send a scrambled version of this code first, then prove you know the original code later. This prevents attackers from stealing your login even if they intercept the initial request.",
    "audio_content": "//NExAAQ8...",
    "tokens_used": 180
  },
  "processing_time_ms": 1450
}
```

---

### Summarize Content

Reduce content to key points and essential information.

**Endpoint:** `POST /api/voice/actions/summarize`

**Use Cases:**
- Summarize meeting transcripts
- Condense long documents
- Extract key takeaways

**Example Request:**
```json
{
  "content": "During today's meeting, we discussed the Q4 roadmap. Sarah mentioned that the mobile app redesign is behind schedule by two weeks due to the new accessibility requirements. John suggested we could parallel track the API updates while waiting for the design mockups. The team agreed to move the launch date from December 15th to January 5th. Marketing needs to be notified about the delay. Budget review is scheduled for next Tuesday.",
  "include_audio": false
}
```

**Example Response:**
```json
{
  "action": "summarize",
  "result": {
    "text": "**Summary:**\n- Mobile app redesign delayed 2 weeks (accessibility requirements)\n- New launch date: January 5th (from December 15th)\n- API updates will proceed in parallel with design work\n- Action needed: Notify marketing of delay\n- Next meeting: Budget review on Tuesday",
    "tokens_used": 120
  },
  "processing_time_ms": 980
}
```

---

### Extract Action Items

Identify tasks, to-dos, and actionable items from content.

**Endpoint:** `POST /api/voice/actions/extract-actions`

**Use Cases:**
- Process meeting notes into tasks
- Create to-do lists from conversations
- Identify commitments and deadlines

**Example Request:**
```json
{
  "content": "We need to update the pricing page by Friday. Can someone reach out to the design team about the new logo? Also, don't forget we promised the client a demo next week. I'll handle the documentation updates, but we need someone to test the API endpoints before release.",
  "include_audio": true
}
```

**Response (with structured data):**
```json
{
  "action": "extract_actions",
  "result": {
    "text": "**Action Items Identified:**\n\n1. Update pricing page (Due: Friday) - Unassigned\n2. Contact design team about new logo - Unassigned\n3. Schedule client demo (Due: Next week) - Unassigned\n4. Update documentation - Assigned to speaker\n5. Test API endpoints before release - Unassigned",
    "action_items": [
      {
        "task": "Update pricing page",
        "due_date": "Friday",
        "assignee": null,
        "priority": "high"
      },
      {
        "task": "Contact design team about new logo",
        "due_date": null,
        "assignee": null,
        "priority": "medium"
      },
      {
        "task": "Schedule client demo",
        "due_date": "next week",
        "assignee": null,
        "priority": "high"
      },
      {
        "task": "Update documentation",
        "due_date": null,
        "assignee": "speaker",
        "priority": "medium"
      },
      {
        "task": "Test API endpoints before release",
        "due_date": "before release",
        "assignee": null,
        "priority": "high"
      }
    ],
    "audio_content": "//NExAAQ8...",
    "tokens_used": 220
  },
  "processing_time_ms": 1650
}
```

---

### Decision Recommendation

Analyze content and provide structured decision guidance.

**Endpoint:** `POST /api/voice/actions/decision`

**Use Cases:**
- Evaluate options and trade-offs
- Get recommendations with reasoning
- Risk assessment for decisions

**Example Request:**
```json
{
  "content": "We're deciding between two vendors for our cloud infrastructure. Vendor A offers $50k/year with 99.9% uptime SLA but limited support hours. Vendor B is $65k/year with 99.99% uptime and 24/7 support. Our application handles financial transactions and any downtime directly impacts revenue.",
  "context": ["Previous discussion noted that last year's downtime cost us approximately $200k"],
  "include_audio": true
}
```

**Response (with structured data):**
```json
{
  "action": "decision",
  "result": {
    "text": "**Recommendation: Vendor B**\n\nBased on your financial transaction use case and the significant cost of downtime ($200k last year), the additional $15k/year investment in Vendor B is justified.\n\n**Key Factors:**\n1. Higher uptime SLA (99.99% vs 99.9%) - critical for financial applications\n2. 24/7 support - essential for transaction systems\n3. ROI calculation: $15k investment vs $200k potential downtime cost\n\n**Risks with Vendor A:**\n- Limited support during off-hours could extend incident resolution\n- Lower SLA acceptable for non-critical systems, not financial\n\n**Confidence: High (85%)**",
    "recommendation": "vendor_b",
    "confidence": 0.85,
    "key_factors": [
      "Higher uptime SLA critical for financial transactions",
      "24/7 support reduces incident resolution time",
      "Cost of downtime ($200k) far exceeds price difference ($15k)"
    ],
    "risks": [
      "Vendor B's higher cost may strain budget",
      "Dependency on single vendor for critical infrastructure"
    ],
    "alternatives_considered": [
      "Vendor A with supplemental support contract",
      "Multi-vendor redundancy approach"
    ],
    "audio_content": "//NExAAQ8...",
    "tokens_used": 380
  },
  "processing_time_ms": 2100
}
```

---

## BYOK Credentials Endpoints

Manage your own Google Cloud TTS credentials.

### Add Google TTS Credentials

**Endpoint:** `POST /api/user/provider-keys/google-tts`

**Request:**
```json
{
  "credentials_json": "{\"type\":\"service_account\",\"project_id\":\"my-project\",...}"
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

---

### Check Credentials Status

**Endpoint:** `GET /api/user/provider-keys/google-tts`

**Response:**
```json
{
  "configured": true,
  "project_id": "my-project-123",
  "created_at": "2025-12-29T10:00:00Z",
  "total_chars_synthesized": 45000
}
```

---

### Remove Credentials

**Endpoint:** `DELETE /api/user/provider-keys/google-tts`

**Response:**
```json
{
  "success": true,
  "message": "Google TTS credentials removed"
}
```

---

## Rate Limits

| Endpoint Type | Limit | Window |
|---------------|-------|--------|
| TTS Synthesis | 60 requests | 1 minute |
| Voice Actions | 30 requests | 1 minute |
| Credential Management | 10 requests | 1 minute |

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1703854800
```

---

## Error Responses

All errors follow a consistent format:

```json
{
  "detail": "Human-readable error message",
  "error_code": "QUOTA_EXCEEDED",
  "retry_after": 60
}
```

### Common Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `AUTH_REQUIRED` | 401 | Missing or invalid API key |
| `SUBSCRIPTION_REQUIRED` | 403 | Active subscription needed |
| `QUOTA_EXCEEDED` | 429 | Monthly TTS quota exhausted |
| `RATE_LIMITED` | 429 | Too many requests |
| `INVALID_VOICE` | 400 | Unknown voice_id |
| `TEXT_TOO_LONG` | 400 | Content exceeds 5000 chars |
| `SYNTHESIS_FAILED` | 500 | TTS engine error |
| `PROCESSING_FAILED` | 500 | AI processing error |

---

## Webhooks (Future)

Webhook support for async processing is planned for high-volume use cases.

---

## Code Examples

### Python

```python
import requests
import base64

API_KEY = "aai_your_key_here"
BASE_URL = "https://your-domain.com/api"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Synthesize speech
response = requests.post(
    f"{BASE_URL}/tts/synthesize",
    headers=headers,
    json={
        "text": "Hello from the API!",
        "voice_id": "en-US-Chirp3-HD-Puck"
    }
)

data = response.json()
audio_bytes = base64.b64decode(data["audio_content"])

with open("output.mp3", "wb") as f:
    f.write(audio_bytes)
```

### JavaScript

```javascript
const API_KEY = "aai_your_key_here";
const BASE_URL = "https://your-domain.com/api";

// Extract action items
const response = await fetch(`${BASE_URL}/voice/actions/extract-actions`, {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${API_KEY}`,
    "Content-Type": "application/json"
  },
  body: JSON.stringify({
    content: "We need to finish the report by Friday and schedule the review meeting.",
    include_audio: false
  })
});

const data = await response.json();
console.log(data.result.action_items);
```

### cURL

```bash
curl -X POST "https://your-domain.com/api/voice/actions/summarize" \
  -H "Authorization: Bearer aai_your_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Long meeting transcript here...",
    "include_audio": true,
    "voice_id": "en-US-Chirp3-HD-Puck"
  }'
```

---

## Changelog

### v1.0 (December 2025)
- Initial release
- TTS synthesis with BYOK support
- Voice action endpoints (explain, summarize, extract-actions, decision)
- API key authentication
