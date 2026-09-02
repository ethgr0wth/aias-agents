# redPrayers Bot 🤖 - Ambassador Dispatch System

## Overview

The redPrayers Bot is a Telegram-based dispatch system that bridges the redPrayers Radar lead intelligence platform with human sales ambassadors. When an admin identifies a high-value lead, they can instantly dispatch a structured **Lead Card** to an ambassador via Telegram, complete with AI-generated outreach materials and action tracking.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     redPrayers Radar (Web UI)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  Pipeline   │  │ Lead Detail │  │    Dispatch Tab         │  │
│  │   Kanban    │──│   Modal     │──│  (Admin-Only)           │  │
│  └─────────────┘  └─────────────┘  │  • Ambassador Picker    │  │
│                                     │  • Persona Editor       │  │
│                                     │  • Generate & Send      │  │
│                                     └───────────┬─────────────┘  │
└───────────────────────────────────────────────────│───────────────┘
                                                    │
                                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ /dispatch API   │  │  LeadPacket     │  │  TG Bot Service │  │
│  │ • /ambassadors  │──│  LLM Generator  │──│  • Send Cards   │  │
│  │ • /generate     │  │  (Groq/OpenAI)  │  │  • Webhooks     │  │
│  │ • /send         │  └─────────────────┘  └────────┬────────┘  │
│  │ • /webhook      │                                │           │
│  └─────────────────┘                                │           │
└─────────────────────────────────────────────────────│───────────┘
                                                      │
                                                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Telegram Bot API                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │  /start Handler │  │   Lead Card     │  │ Inline Buttons  │  │
│  │  (Registration) │  │   DM Delivery   │  │ (Callbacks)     │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                                      │
                                                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Ambassadors (Humans)                         │
│  Receive Lead Cards → Take Action → Tap Status Button           │
└─────────────────────────────────────────────────────────────────┘
```

---

## User Flows

### Flow 1: Ambassador Registration

```
Ambassador                    Telegram Bot                 Redis
    │                              │                          │
    │──── /start ─────────────────▶│                          │
    │                              │                          │
    │                              │──── Store ambassador ───▶│
    │                              │     chat_id, username     │
    │                              │     registered_at         │
    │                              │                          │
    │◀─── "Welcome! You're ────────│                          │
    │      registered for          │                          │
    │      Lead Dispatch."         │                          │
    │                              │                          │
```

### Flow 2: Lead Dispatch (Admin)

```
Admin (UI)              Backend                    TG Bot           Ambassador
    │                      │                          │                  │
    │── Open Lead Detail ─▶│                          │                  │
    │                      │                          │                  │
    │── Click Dispatch Tab │                          │                  │
    │                      │                          │                  │
    │◀─ Load ambassadors ──│◀─ GET /ambassadors ──────│                  │
    │   (auto-populated)   │                          │                  │
    │                      │                          │                  │
    │── Select ambassador  │                          │                  │
    │                      │                          │                  │
    │── Edit persona       │                          │                  │
    │   (optional tweak)   │                          │                  │
    │                      │                          │                  │
    │── Click Generate ───▶│                          │                  │
    │   & Send             │                          │                  │
    │                      │── LLM generates ────────▶│                  │
    │                      │   LeadPacket             │                  │
    │                      │                          │                  │
    │                      │── Format Lead Card ─────▶│                  │
    │                      │                          │                  │
    │                      │                          │── DM Lead Card ─▶│
    │                      │                          │   + Buttons      │
    │                      │                          │                  │
    │◀─ "Dispatched!" ─────│                          │                  │
    │                      │                          │                  │
```

### Flow 3: Ambassador Action (Button Callback)

```
Ambassador              Telegram Bot              Backend              Redis
    │                        │                       │                   │
    │── Tap "✅ Claimed" ───▶│                       │                   │
    │                        │                       │                   │
    │                        │── POST /webhook ─────▶│                   │
    │                        │   {lead_id, action}   │                   │
    │                        │                       │── Update status ─▶│
    │                        │                       │   dispatch:status │
    │                        │                       │                   │
    │◀─ "Lead claimed!" ─────│◀─ 200 OK ─────────────│                   │
    │                        │                       │                   │
```

---

## Data Models

### Ambassador (Redis)

**Primary key is `chat_id` (stable)** - usernames can change in Telegram.

```
Key: radar:ambassadors:{chat_id}
TTL: None (permanent)

{
  "chat_id": 123456789,
  "username": "john_sales",        // Display only, mutable
  "first_name": "John",
  "registered_at": "2025-01-23T10:00:00Z",
  "total_dispatches": 15,
  "total_won": 3
}

Index Key: radar:ambassadors:list  // Set of all chat_ids
```

### LeadPacket (Generated by LLM)

```json
{
  "lead_id": "abc123",
  "generated_at": "2025-01-23T10:30:00Z",
  "custom_directives": "Target is solo SEO consultant, not agency",
  
  "snapshot": {
    "score": 85,
    "platform": "reddit",
    "author": "JamMasterJulian",
    "title": "Why Smart Entrepreneurs Are Ditching ChatGPT...",
    "url": "https://reddit.com/r/SaaS/...",
    "insight": "Urgency implied by the call to action for a free SEO strategy session suggests readiness to invest in related services."
  },
  
  "persona": {
    "likely_role": "SEO coach / agency owner / founder",
    "pain_points": ["Tool fatigue", "Need for agent workflows vs basic chatbots"],
    "hook": "'Agent workflows > chatbots' + offer a quick comparison"
  },
  
  "copy_blocks": {
    "comment_reply": "Great breakdown! I've been exploring agent-based approaches too. The shift from basic chatbots to autonomous workflows has been a game-changer for client work. Happy to share some comparisons if helpful.",
    
    "dm_opener": "Hey! Saw your post on AI agents vs chatbots - really resonated. I work with a platform that does exactly what you described (autonomous agent workflows). Would you be open to a quick 5-min walkthrough?",
    
    "followup_24h": "Just following up on my earlier message. No pressure at all - I know you're probably swamped. If timing doesn't work, happy to send over a quick video demo instead.",
    
    "followup_72h": "Last ping from me! If this isn't on your radar right now, totally get it. Here's a 2-min demo link in case it's useful down the line: [link]",
    
    "cta_version": "Book a 15-min call here: [calendly_link]",
    "non_cta_version": "Happy to just chat async if that's easier - no sales pitch, just info sharing."
  },
  
  "objection_handles": {
    "why_not_perplexity": "Perplexity is great for research, but it's consumer-focused. AiAS is built for business workflows - think lead qualification, customer support automation, multi-step agent tasks.",
    
    "already_use_chatgpt": "ChatGPT is powerful but generic. AiAS lets you bring your own models, create specialized agents, and integrate directly into your product. It's the difference between a swiss army knife and a custom-built tool.",
    
    "not_another_tool": "Totally fair concern. The goal isn't to add another tool - it's to replace the 3-4 you're juggling now with one orchestration layer."
  }
}
```

### Dispatch Record (Redis)

Each dispatch has a unique `dispatch_id` for unambiguous status tracking.

```
Key: radar:dispatch:{dispatch_id}
TTL: 90 days

{
  "dispatch_id": "dsp_abc123_1706012345",  // lead_id + timestamp
  "lead_id": "abc123",
  "ambassador_chat_id": 123456789,
  "ambassador_username": "john_sales",     // Snapshot at dispatch time
  "message_id": 12345,                     // TG message ID for editing
  "dispatched_at": "2025-01-23T10:30:00Z",
  "status": "claimed",  // pending | claimed | sent | snoozed | not_fit | won
  "status_updated_at": "2025-01-23T11:00:00Z",
  "lead_packet_hash": "sha256:...",
  "notes": ""
}

Index Keys:
- radar:dispatch:lead:{lead_id}           // Set of dispatch_ids for lead
- radar:dispatch:ambassador:{chat_id}     // Set of dispatch_ids for ambassador
```

### Idempotency Rules

1. **One active dispatch per lead+ambassador pair** - Re-dispatching same lead to same ambassador updates existing record (doesn't create duplicate)
2. **LeadPacket regeneration** - Calling `/generate` with same lead_id + directives returns cached packet (7-day TTL), use `force_regenerate=true` to override
3. **Send idempotency** - If dispatch_id exists with status != "won", resending updates the message (edit vs new send)

---

## API Endpoints

### GET /api/radar/dispatch/ambassadors

Returns list of registered ambassadors.

**Response:**
```json
{
  "ambassadors": [
    {
      "username": "john_sales",
      "first_name": "John",
      "registered_at": "2025-01-23T10:00:00Z",
      "stats": {
        "total_dispatches": 15,
        "total_won": 3,
        "win_rate": 0.20
      }
    }
  ]
}
```

### POST /api/radar/dispatch/generate

Generates LeadPacket using LLM with optional custom directives.

**Request:**
```json
{
  "lead_id": "abc123",
  "custom_directives": "Target is solo SEO consultant, price-sensitive"
}
```

**Response:**
```json
{
  "lead_packet": { ... },
  "tokens_used": 1250
}
```

### POST /api/radar/dispatch/send

Sends Lead Card to ambassador via Telegram. Uses `chat_id` (stable identifier).

**Request:**
```json
{
  "lead_id": "abc123",
  "ambassador_chat_id": 123456789,
  "lead_packet": { ... }
}
```

**Response:**
```json
{
  "success": true,
  "dispatch_id": "dsp_abc123_1706012345",
  "message_id": 12345,
  "dispatched_at": "2025-01-23T10:30:00Z"
}
```

### POST /api/radar/dispatch/webhook

Telegram callback webhook for button actions. Callback data includes `dispatch_id` for unambiguous status updates.

**Callback Data Format:**
```
{action}:{dispatch_id}
e.g., "claimed:dsp_abc123_1706012345"
```

**Request (from Telegram):**
```json
{
  "callback_query": {
    "id": "123",
    "from": { "id": 123456789, "username": "john_sales" },
    "data": "claimed:dsp_abc123_1706012345"
  }
}
```

**Validation:**
- Verify `from.id` matches `ambassador_chat_id` in dispatch record
- Reject if dispatch_id not found or ambassador mismatch

### GET /api/radar/dispatch/status/{lead_id}

Get dispatch status for a lead.

**Response:**
```json
{
  "lead_id": "abc123",
  "dispatches": [
    {
      "ambassador": "john_sales",
      "status": "claimed",
      "dispatched_at": "2025-01-23T10:30:00Z"
    }
  ]
}
```

---

## Lead Card Format (Telegram Message)

```
🔥 HOT LEAD • 85

📌 Why Smart Entrepreneurs Are Ditching ChatGPT for Perplexity AI Agents

👤 @JamMasterJulian • Reddit
🔗 View Post

━━━━━━━━━━━━━━━━━━━━━━

💡 INSIGHT
Urgency implied by the call to action for a free SEO strategy session suggests readiness to invest.

━━━━━━━━━━━━━━━━━━━━━━

🎯 PERSONA
SEO coach / agency owner / founder
Pain: Tool fatigue, needs agent workflows
Hook: "Agent workflows > chatbots" comparison

━━━━━━━━━━━━━━━━━━━━━━

📝 COPY BLOCKS

💬 Comment Reply:
```
Great breakdown! I've been exploring agent-based approaches too...
```

✉️ DM Opener:
```
Hey! Saw your post on AI agents vs chatbots - really resonated...
```

⏰ Follow-up (24h):
```
Just following up on my earlier message...
```

⏰ Follow-up (72h):
```
Last ping from me! Here's a 2-min demo link...
```

━━━━━━━━━━━━━━━━━━━━━━

🛡️ OBJECTION HANDLES

❓ "Why not Perplexity?"
→ Perplexity is consumer-focused. AiAS is built for business workflows...

❓ "I already use ChatGPT"
→ ChatGPT is powerful but generic. AiAS lets you BYOK...

❓ "Not another tool..."
→ Goal isn't to add - it's to replace 3-4 you're juggling...

━━━━━━━━━━━━━━━━━━━━━━

[✅ Claimed] [📝 Sent] [⏰ Snooze]
[🧊 Not a Fit] [🏁 Won]
```

---

## UI Components

### Dispatch Tab (Admin-Only)

Location: Lead Detail Modal → 4th tab after "Insights | Chat | Outreach"

**Visibility:** Only shown to admin users

**Components:**

1. **Ambassador Dropdown**
   - Auto-populated from registered ambassadors
   - Shows username + stats (dispatches, win rate)
   - Empty state: "No ambassadors registered yet"

2. **Persona Editor (Collapsible)**
   - Default prompt shown (expandable)
   - Text area for custom directives
   - Placeholder: "e.g., Target is solo consultant, price-sensitive"

3. **Generate & Send Button**
   - Primary action button
   - States: Default → Generating... → Sending... → Dispatched ✓
   - Disabled if no ambassador selected

4. **Dispatch History**
   - Shows previous dispatches for this lead
   - Ambassador, status, timestamp
   - Status badges with colors

---

## Redis Keys

| Key Pattern | Purpose | TTL |
|-------------|---------|-----|
| `radar:ambassadors:{chat_id}` | Ambassador profile (chat_id = primary key) | None |
| `radar:ambassadors:list` | Set of all ambassador chat_ids | None |
| `radar:dispatch:{dispatch_id}` | Dispatch record | 90 days |
| `radar:dispatch:lead:{lead_id}` | Set of dispatch_ids for a lead | 90 days |
| `radar:dispatch:ambassador:{chat_id}` | Set of dispatch_ids for an ambassador | 90 days |
| `radar:dispatch:active:{lead_id}:{chat_id}` | Active dispatch_id for lead+ambassador pair (idempotency) | 90 days |
| `radar:lead_packet:{lead_id}:{directives_hash}` | Cached LeadPacket | 7 days |

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELEGRAM_BOT_TOKEN` | Bot token from @BotFather | Yes |
| `TELEGRAM_WEBHOOK_SECRET` | Secret for validating webhooks | Yes (auto-generated) |
| `GROQ_API_KEY` | For LeadPacket LLM generation | Yes (existing) |

---

## LLM Prompt Template (LeadPacket Generation)

```
You are an expert B2B sales copywriter for AiAS (aiassist.net), an AI-as-a-Service platform. 

Given this lead intelligence, generate a complete outreach package.

LEAD DATA:
- Score: {score}
- Platform: {platform}
- Author: {author}
- Title: {title}
- Content: {content}
- Insight: {insight}

CUSTOM DIRECTIVES (if provided):
{custom_directives}

PRODUCT CONTEXT:
AiAS is a BYOK (Bring Your Own Key) AI platform that lets businesses:
- Create custom AI agents with their own LLM keys
- Embed AI chat widgets in their products
- Automate customer support with autonomous workflows
- Multi-tenant AI infrastructure

TARGET ICP:
- SaaS founders needing embedded AI
- Agencies offering AI services to clients
- Businesses tired of expensive chatbot solutions
- Developers wanting BYOK flexibility

Generate a JSON response with:
1. persona: likely_role, pain_points (array), hook
2. copy_blocks: comment_reply, dm_opener, followup_24h, followup_72h, cta_version, non_cta_version
3. objection_handles: why_not_perplexity, already_use_chatgpt, not_another_tool

Keep copy conversational, non-salesy, and human. Focus on value, not features.
```

---

## Security Considerations

1. **Admin-Only Access**
   - Dispatch tab only visible to admin users
   - API endpoints protected by admin auth middleware

2. **Webhook Validation**
   - Telegram webhooks validated with secret token
   - Reject requests without valid signature

3. **Rate Limiting**
   - Max 10 dispatches per lead
   - Max 50 dispatches per hour per admin

4. **Ambassador Verification**
   - Only registered ambassadors can receive dispatches
   - Unregistered chat_ids rejected

---

## Success Metrics

| Metric | Description |
|--------|-------------|
| Dispatch Volume | Total leads dispatched per day/week |
| Claim Rate | % of dispatched leads claimed by ambassadors |
| Response Rate | % of claimed leads where outreach was sent |
| Win Rate | % of dispatched leads marked as "won" |
| Time to Claim | Avg time from dispatch to claim |
| Time to Won | Avg time from dispatch to won |

---

## Future Enhancements (Post-MVP)

1. **Multi-Ambassador Dispatch** - Send same lead to multiple ambassadors
2. **Auto-Assignment Rules** - Route leads by score, platform, or keywords
3. **Ambassador Leaderboard** - Gamification with rankings
4. **Dispatch Templates** - Save custom directive presets
5. **Slack Integration** - Alternative to Telegram
6. **Voice Notes** - TTS-generated voice briefings

---

## Implementation Checklist

- [ ] Create Telegram bot service (`telegram_bot_service.py`)
- [ ] Add ambassador storage methods to `storage_service.py`
- [ ] Add LeadPacket generation to `aias_service.py`
- [ ] Create dispatch routes (`/api/radar/dispatch/*`)
- [ ] Build Lead Card formatter with Telegram markdown
- [ ] Add Dispatch tab to lead detail modal (UI)
- [ ] Wire button callbacks to status updates
- [ ] Set up Telegram webhook endpoint
- [ ] Request `TELEGRAM_BOT_TOKEN` from user
