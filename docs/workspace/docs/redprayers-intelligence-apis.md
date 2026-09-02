# RedPrayers Intelligence API — v1 Specification

> **Version**: 1.0.0-draft  
> **Last Updated**: 2026-02-19  
> **Status**: Pre-release  
> **Base URL**: `https://signal.saas-signal.com/v1`

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture Principles](#architecture-principles)
3. [Authentication](#authentication)
4. [Response Envelope](#response-envelope)
5. [Rate Limits & Quotas](#rate-limits--quotas)
6. [Core Endpoints](#core-endpoints)
   - [POST /v1/scan](#post-v1scan)
   - [POST /v1/scan/stream](#post-v1scanstream)
   - [GET /v1/sources](#get-v1sources)
   - [GET /v1/signals](#get-v1signals)
   - [POST /v1/score](#post-v1score)
   - [POST /v1/enrich](#post-v1enrich)
   - [GET /v1/usage](#get-v1usage)
7. [AI & LLM Integration](#ai--llm-integration)
   - [GET /v1/tools](#get-v1tools)
   - [OpenAI Function Calling Schema](#openai-function-calling-schema)
   - [MCP Tool Manifest](#mcp-tool-manifest)
8. [Streaming Protocol](#streaming-protocol)
9. [Data Models](#data-models)
10. [Source Catalog](#source-catalog)
11. [Intent Scoring System](#intent-scoring-system)
12. [JavaScript/TypeScript SDK](#javascripttypescript-sdk)
13. [Python SDK](#python-sdk)
14. [Error Reference](#error-reference)
15. [Migration Guide (Internal → v1)](#migration-guide)
16. [Appendix: Existing Routes (Unchanged)](#appendix-existing-routes-unchanged)

---

## Overview

The RedPrayers Intelligence API provides programmatic access to real-time signal intelligence across 22+ online platforms. It scans Reddit, Twitter/X, LinkedIn, Hacker News, Product Hunt, Telegram, and 16 more sources to surface high-intent signals — people actively looking for solutions, hiring, evaluating tools, or expressing pain points.

Every response is structured for direct consumption by LLM agents, automation pipelines, and developer integrations. The API serves as the canonical data source for lead intelligence, content monitoring, and competitive analysis.

### Key Capabilities

- **Multi-source scanning** across 22+ platforms in a single API call
- **AI intent scoring** with confidence levels, categories, and reasoning
- **Real-time streaming** via SSE as signals arrive from each source
- **LLM-native** — tool definitions for OpenAI function calling, MCP protocol, LangChain, CrewAI
- **Multi-tenant isolation** — every request scoped to the authenticated organization
- **Deduplication** — automatic 30-day cache prevents rescanning known content

### Design Philosophy

- **Additive only**: The v1 API is a new layer mounted alongside the existing platform. All existing internal routes (`/api/radar/`, `/api/contacts/`, `/api/dispatch/`, `/api/settings/`, `/api/team-chat/`) remain completely untouched.
- **LLM-first responses**: Every field is named for machine readability. No HTML, no ambiguous strings. Scores are floats, timestamps are ISO 8601 or Unix epoch, categories are enums.
- **Bring Your Own Key (BYOK)**: Authentication uses your existing AiAS API key. No new key systems.

---

## Architecture Principles

```
┌─────────────────────────────────────────────────────────┐
│                    saas-signal Platform                  │
│                                                         │
│  ┌─────────────────┐     ┌────────────────────────────┐ │
│  │  Existing Routes │     │  NEW: /v1/ Public API      │ │
│  │  /api/radar/*    │     │  /v1/scan                  │ │
│  │  /api/contacts/* │     │  /v1/scan/stream           │ │
│  │  /api/dispatch/* │     │  /v1/sources               │ │
│  │  /api/settings/* │     │  /v1/signals               │ │
│  │  /api/team-chat/*│     │  /v1/score                 │ │
│  │                  │     │  /v1/enrich                │ │
│  │  (UNCHANGED)     │     │  /v1/usage                 │ │
│  │                  │     │  /v1/tools                 │ │
│  └────────┬─────────┘     └────────────┬───────────────┘ │
│           │                            │                 │
│           └──────────┬─────────────────┘                 │
│                      ▼                                   │
│  ┌─────────────────────────────────────────────────────┐ │
│  │           Shared Service Layer                      │ │
│  │  RedditService · TelegramService · AiasService      │ │
│  │  NetrowsService · StorageService · HackerNewsService│ │
│  │  ProductHuntService · 16+ more services             │ │
│  └─────────────────────────────────────────────────────┘ │
│                      ▼                                   │
│  ┌─────────────────────────────────────────────────────┐ │
│  │           Redis (org-scoped data isolation)         │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

The v1 endpoints reuse the same battle-tested service layer that powers the dashboard. No data duplication, no new storage — just a clean, standardized interface on top.

---

## Authentication

All v1 endpoints require a valid AiAS API key passed as a Bearer token.

```http
Authorization: Bearer aai_your_api_key_here
```

### How It Works

1. The API validates your key against the AiAS authentication service
2. Your organization ID is resolved from the key
3. All data access is scoped to your organization — zero cross-tenant leakage
4. Validation results are cached for 15 minutes to reduce latency

### Key Format

AiAS API keys use the `aai_` prefix:

```
aai_sk_live_abc123def456...
```

### Getting Your API Key

1. Sign in to [AiAssist](https://app.aiassist.net)
2. Navigate to Settings → API Keys
3. Generate a new key with the scopes you need
4. The key inherits your organization's plan tier and rate limits

### Authentication Errors

| Status | Code | Meaning |
|--------|------|---------|
| 401 | `missing_api_key` | No Authorization header provided |
| 401 | `invalid_api_key` | Key is malformed or revoked |
| 403 | `insufficient_plan` | Your plan doesn't include API access |
| 429 | `rate_limit_exceeded` | Too many requests for your tier |

---

## Response Envelope

All v1 responses use a consistent envelope format:

### Success Response

```json
{
  "data": { ... },
  "meta": {
    "request_id": "req_abc123",
    "org_id": "a9020cd2-ab92-4f8e-8420-66d5a6389ab0",
    "timestamp": "2026-02-19T22:48:00Z",
    "version": "1.0.0",
    "processing_ms": 1234
  }
}
```

### Error Response

```json
{
  "error": {
    "code": "invalid_source",
    "message": "Source 'myspace' is not supported",
    "details": {
      "supported_sources": ["reddit", "twitter", "hackernews", "..."]
    }
  },
  "meta": {
    "request_id": "req_def456",
    "timestamp": "2026-02-19T22:48:00Z",
    "version": "1.0.0"
  }
}
```

### Paginated Response

```json
{
  "data": [ ... ],
  "meta": {
    "request_id": "req_ghi789",
    "timestamp": "2026-02-19T22:48:00Z",
    "version": "1.0.0",
    "processing_ms": 456
  },
  "pagination": {
    "total": 247,
    "limit": 25,
    "offset": 0,
    "has_more": true
  }
}
```

---

## Rate Limits & Quotas

Rate limits are designed to keep the service usable for everyone — not to block legitimate usage. Pro plans have unlimited access; limits exist only to prevent abuse.

| Plan | Scans/min | Signals/day | Score Requests/min | Streaming |
|------|-----------|-------------|--------------------|-----------|
| Free | 10 | 1,000 | 20 | Yes |
| Basic | 30 | 10,000 | 60 | Yes |
| Pro | 120 | Unlimited | 300 | Yes |
| Enterprise | 300 | Unlimited | 600 | Yes |

### Rate Limit Headers

Every response includes rate limit information:

```http
X-RateLimit-Limit: 120
X-RateLimit-Remaining: 117
X-RateLimit-Reset: 1708383600
X-RateLimit-Window: 60
```

### Burst Handling

Short bursts above the per-minute limit are tolerated (up to 3x) — we'd rather you get your data than get blocked. Sustained abuse (sustained 10x+ over minutes) returns `429 Too Many Requests` with a `Retry-After` header. If you're hitting limits on Pro, something is likely misconfigured — reach out and we'll help.

---

## Core Endpoints

### POST /v1/scan

Scan one or more sources for signals matching your keywords. Returns AI-scored, structured signal data optimized for LLM consumption.

**Request:**

```http
POST /v1/scan
Authorization: Bearer aai_...
Content-Type: application/json
```

```json
{
  "sources": ["reddit", "hackernews", "twitter"],
  "keywords": {
    "include": ["looking for CRM", "need help with sales automation"],
    "exclude": ["hiring", "job posting"],
    "subreddits": ["SaaS", "startups", "sales"],
    "category": "recent"
  },
  "mode": "LEAD",
  "context": {
    "company_name": "Acme CRM",
    "campaign_intent": "Find SaaS founders struggling with sales pipeline",
    "campaign_mission": "Offer free pipeline audit",
    "campaign_urgency": "medium",
    "campaign_goal": "Book discovery calls"
  },
  "limit": 25,
  "min_intent_score": 0.5,
  "deduplicate": true
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `sources` | `string[]` | Yes | One or more source IDs from the [Source Catalog](#source-catalog) |
| `keywords.include` | `string[]` | Yes | Terms to match — signals must contain at least one |
| `keywords.exclude` | `string[]` | No | Terms to reject — signals containing these are filtered out |
| `keywords.subreddits` | `string[]` | No | Specific subreddits to scan (Reddit only) |
| `keywords.category` | `string` | No | Content category filter. Default: `"recent"` |
| `mode` | `enum` | No | `"LEAD"` (buying intent) or `"SEO"` (content opportunities). Default: `"LEAD"` |
| `context` | `object` | No | Campaign context for more accurate intent scoring |
| `context.company_name` | `string` | No | Your company/product name |
| `context.campaign_intent` | `string` | No | What you're looking for |
| `context.campaign_mission` | `string` | No | Your outreach approach |
| `context.campaign_urgency` | `string` | No | `"low"`, `"medium"`, `"high"` |
| `context.campaign_goal` | `string` | No | Desired outcome |
| `limit` | `integer` | No | Max signals per source. Default: 25, Max: 100 |
| `min_intent_score` | `float` | No | Minimum intent score threshold (0.0–1.0). Default: 0.0 |
| `deduplicate` | `boolean` | No | Skip previously scanned content. Default: true |

**Response:**

```json
{
  "data": {
    "signals": [
      {
        "id": "t3_abc123",
        "source": "reddit",
        "source_community": "r/SaaS",
        "title": "Frustrated with our current CRM - looking for alternatives",
        "content": "We've been using Salesforce for 2 years but it's overkill for our 10-person team...",
        "author": "startup_founder_42",
        "url": "https://reddit.com/r/SaaS/comments/abc123",
        "created_at": "2026-02-19T18:30:00Z",
        "created_utc": 1708371000,
        "intent": {
          "score": 0.92,
          "confidence": 0.88,
          "category": "evaluating",
          "urgency": "high",
          "reasoning": "Author explicitly seeking CRM alternatives, mentions budget constraints and team size — strong buying signal with immediate need"
        }
      }
    ],
    "scan_summary": {
      "total_fetched": 150,
      "total_scored": 87,
      "total_returned": 23,
      "skipped_cached": 63,
      "skipped_below_threshold": 64,
      "sources_scanned": ["reddit", "hackernews", "twitter"],
      "sources_failed": []
    }
  },
  "meta": {
    "request_id": "req_scan_abc123",
    "org_id": "a9020cd2-...",
    "timestamp": "2026-02-19T22:48:00Z",
    "version": "1.0.0",
    "processing_ms": 4521
  }
}
```

### Intent Categories

The `intent.category` field classifies each signal:

| Category | Description | Example |
|----------|-------------|---------|
| `buying` | Actively looking to purchase or subscribe | "Need a tool that does X" |
| `evaluating` | Comparing options, doing research | "Salesforce vs HubSpot — which is better?" |
| `frustrated` | Expressing pain with current solution | "Our CRM is driving me crazy" |
| `hiring` | Looking to hire or build a team | "Hiring senior DevOps engineer" |
| `building` | Creating something, potential integration partner | "Building a new SaaS product for..." |
| `asking` | Asking for advice or recommendations | "What do you all use for email marketing?" |
| `announcing` | Launching, shipping, or celebrating a milestone | "Just launched our MVP!" |
| `discussing` | General discussion, not actionable | "Thoughts on the future of AI?" |

---

### POST /v1/scan/stream

Same as `/v1/scan` but returns results via Server-Sent Events (SSE) as each source completes. Ideal for real-time UIs and LLM streaming pipelines.

**Request:** Same body as `POST /v1/scan`

**Response:** `text/event-stream`

See [Streaming Protocol](#streaming-protocol) for event format details.

---

### GET /v1/sources

List all available signal sources with their current status and capabilities.

**Request:**

```http
GET /v1/sources
Authorization: Bearer aai_...
```

**Response:**

```json
{
  "data": {
    "sources": [
      {
        "id": "reddit",
        "name": "Reddit",
        "description": "Reddit RSS feeds — free, no API key required",
        "status": "available",
        "requires_config": false,
        "capabilities": {
          "keyword_search": true,
          "subreddit_filter": true,
          "category_filter": false,
          "realtime": false,
          "max_results": 100
        },
        "rate_limit": {
          "requests_per_minute": 30,
          "cooldown_seconds": 0
        }
      },
      {
        "id": "twitter",
        "name": "Twitter / X",
        "description": "Twitter search via Netrows or ScrapingDog fallback",
        "status": "available",
        "requires_config": true,
        "config_fields": ["netrows_api_key"],
        "capabilities": {
          "keyword_search": true,
          "subreddit_filter": false,
          "category_filter": true,
          "realtime": true,
          "max_results": 50,
          "ai_hashtag_generation": true
        },
        "rate_limit": {
          "requests_per_minute": 10,
          "cooldown_seconds": 5
        }
      }
    ],
    "total": 22,
    "configured_count": 18,
    "unconfigured": ["telegram", "reddit_api", "scrapingdog_twitter"]
  },
  "meta": { "..." }
}
```

---

### GET /v1/signals

Retrieve previously scanned and scored signals from your organization's cache. Supports filtering, pagination, and JSONL bulk export.

**Request:**

```http
GET /v1/signals?source=reddit&min_score=0.7&limit=50&offset=0
Authorization: Bearer aai_...
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `source` | `string` | Filter by source ID |
| `min_score` | `float` | Minimum intent score (0.0–1.0) |
| `max_score` | `float` | Maximum intent score (0.0–1.0) |
| `category` | `string` | Filter by intent category |
| `status` | `string` | Filter by pipeline status: `new`, `contacted`, `replied`, `won`, `lost` |
| `author` | `string` | Filter by author username |
| `since` | `string` | ISO 8601 timestamp — only signals after this time |
| `until` | `string` | ISO 8601 timestamp — only signals before this time |
| `limit` | `integer` | Results per page (default: 25, max: 100) |
| `offset` | `integer` | Pagination offset |
| `format` | `string` | Response format: `json` (default) or `jsonl` for line-delimited streaming |
| `sort` | `string` | Sort by: `intent_score`, `created_at`, `confidence`. Default: `intent_score` |
| `order` | `string` | `desc` (default) or `asc` |

**Response (JSON):**

```json
{
  "data": [
    {
      "id": "t3_abc123",
      "source": "reddit",
      "source_community": "r/SaaS",
      "title": "Looking for CRM alternatives",
      "content": "...",
      "author": "startup_founder_42",
      "url": "https://reddit.com/r/SaaS/comments/abc123",
      "created_at": "2026-02-19T18:30:00Z",
      "intent": {
        "score": 0.92,
        "confidence": 0.88,
        "category": "evaluating",
        "urgency": "high",
        "reasoning": "Explicit request for CRM alternatives with budget mention"
      },
      "pipeline_status": "new",
      "locked_at": null
    }
  ],
  "meta": { "..." },
  "pagination": {
    "total": 247,
    "limit": 25,
    "offset": 0,
    "has_more": true
  }
}
```

**Response (JSONL):** When `format=jsonl`, returns `application/x-ndjson`:

```
{"id":"t3_abc123","source":"reddit","title":"Looking for CRM alternatives","intent":{"score":0.92,"category":"evaluating"},...}
{"id":"hn_456","source":"hackernews","title":"Ask HN: Best sales tools?","intent":{"score":0.85,"category":"asking"},...}
```

---

### POST /v1/score

Score arbitrary text content for intent signals. Accepts raw text, URLs, or structured post data. Useful for scoring content from your own data sources.

**Request:**

```json
{
  "items": [
    {
      "id": "custom_001",
      "text": "We've outgrown our current project management tool and need something that scales. Budget is $50/user/month. Anyone have recommendations?",
      "metadata": {
        "source": "slack",
        "author": "pm_lead",
        "channel": "#tools-discussion"
      }
    },
    {
      "id": "custom_002",
      "text": "Just published a blog post about our tech stack migration from monolith to microservices.",
      "metadata": {
        "source": "internal_feed"
      }
    }
  ],
  "keywords": {
    "include": ["project management", "scaling", "enterprise"],
    "exclude": ["free tier only"]
  },
  "mode": "LEAD",
  "context": {
    "company_name": "TaskFlow Pro",
    "campaign_intent": "Find teams outgrowing basic PM tools"
  }
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `items` | `array` | Yes | Array of content items to score (max 50 per request) |
| `items[].id` | `string` | Yes | Your unique identifier for this item |
| `items[].text` | `string` | Yes | The text content to analyze |
| `items[].title` | `string` | No | Optional title/subject line |
| `items[].metadata` | `object` | No | Arbitrary metadata passed through to the response |
| `keywords` | `object` | No | Keyword context for more relevant scoring |
| `mode` | `enum` | No | `"LEAD"` or `"SEO"`. Default: `"LEAD"` |
| `context` | `object` | No | Campaign context for scoring precision |

**Response:**

```json
{
  "data": {
    "scored_items": [
      {
        "id": "custom_001",
        "intent": {
          "score": 0.89,
          "confidence": 0.91,
          "category": "buying",
          "urgency": "high",
          "reasoning": "Explicit budget mention ($50/user/month), team growth pain point, actively seeking recommendations — strong purchase-ready signal"
        },
        "entities": {
          "budget": "$50/user/month",
          "team_signal": "outgrown current tool",
          "decision_stage": "evaluation"
        },
        "metadata": {
          "source": "slack",
          "author": "pm_lead",
          "channel": "#tools-discussion"
        }
      },
      {
        "id": "custom_002",
        "intent": {
          "score": 0.22,
          "confidence": 0.85,
          "category": "announcing",
          "urgency": "low",
          "reasoning": "Content sharing / announcement — no buying or evaluation signal detected"
        },
        "entities": {},
        "metadata": {
          "source": "internal_feed"
        }
      }
    ],
    "summary": {
      "total_scored": 2,
      "high_intent": 1,
      "medium_intent": 0,
      "low_intent": 1,
      "avg_score": 0.555
    }
  },
  "meta": { "..." }
}
```

---

### POST /v1/enrich

Generate AI-powered outreach content and lead intelligence for a specific signal. Wraps lead packet generation, outreach drafting, and strategic analysis.

**Request:**

```json
{
  "signal": {
    "id": "t3_abc123",
    "title": "Frustrated with our current CRM",
    "content": "We've been using Salesforce for 2 years but it's overkill...",
    "author": "startup_founder_42",
    "source": "reddit",
    "intent_score": 0.92
  },
  "generate": ["outreach", "analysis", "lead_packet"],
  "outreach_style": "helpful",
  "custom_directives": "Focus on their team size pain point. Mention free pilot program.",
  "campaign_mode": "LEAD"
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `signal` | `object` | Yes | The signal to enrich (from scan or signals endpoint) |
| `generate` | `string[]` | No | What to generate: `"outreach"`, `"analysis"`, `"lead_packet"`. Default: all |
| `outreach_style` | `enum` | No | `"helpful"`, `"curious"`, `"connector"`. Default: `"helpful"` |
| `custom_directives` | `string` | No | Additional instructions for the AI |
| `campaign_mode` | `string` | No | `"LEAD"` or `"SEO"`. Default: `"LEAD"` |

**Response:**

```json
{
  "data": {
    "outreach": {
      "message": "Hey startup_founder_42,\n\nSaw your post about Salesforce being overkill for a 10-person team — totally get it...",
      "style": "helpful",
      "word_count": 67,
      "tone": "conversational"
    },
    "analysis": {
      "pain_points": ["CRM complexity", "cost vs team size", "feature bloat"],
      "buying_stage": "evaluation",
      "recommended_approach": "Lead with simplicity angle, offer free trial or audit",
      "urgency_assessment": "Active — likely to make a decision within 2 weeks",
      "competitive_context": "Evaluating alternatives to Salesforce, budget-conscious"
    },
    "lead_packet": {
      "summary": "SaaS founder (10-person team) actively seeking Salesforce alternatives...",
      "talking_points": ["...", "..."],
      "objection_handlers": ["...", "..."],
      "recommended_cta": "Offer free 30-min pipeline audit"
    },
    "tokens_used": 1247,
    "cached": false
  },
  "meta": { "..." }
}
```

---

### GET /v1/usage

Get your organization's API usage statistics and quota status.

**Request:**

```http
GET /v1/usage
Authorization: Bearer aai_...
```

**Response:**

```json
{
  "data": {
    "plan": "pro",
    "billing_period": {
      "start": "2026-02-01T00:00:00Z",
      "end": "2026-02-28T23:59:59Z"
    },
    "scans": {
      "used": 342,
      "limit": null,
      "remaining": null
    },
    "signals_processed": {
      "used": 8_547,
      "limit": 50_000,
      "remaining": 41_453
    },
    "score_requests": {
      "used": 89,
      "limit": null,
      "remaining": null
    },
    "enrich_requests": {
      "used": 45,
      "limit": null,
      "remaining": null
    },
    "rate_limits": {
      "scans_per_minute": { "limit": 60, "current": 3 },
      "scores_per_minute": { "limit": 120, "current": 0 }
    },
    "cache": {
      "scanned_posts": 4_231,
      "ttl_days": 30
    }
  },
  "meta": { "..." }
}
```

---

## AI & LLM Integration

The v1 API is designed to be consumed directly by LLM agents. This section defines the tool schemas that allow OpenAI, Anthropic, Google, and open-source LLMs to use the API as a function-calling tool.

### GET /v1/tools

Returns machine-readable tool definitions in multiple formats.

**Query Parameters:**

| Parameter | Values | Description |
|-----------|--------|-------------|
| `format` | `openai`, `mcp`, `langchain`, `raw` | Tool definition format. Default: `openai` |

---

### OpenAI Function Calling Schema

```json
[
  {
    "type": "function",
    "function": {
      "name": "scan_signals",
      "description": "Scan online platforms (Reddit, Twitter, LinkedIn, Hacker News, etc.) for high-intent signals — people looking for solutions, hiring, evaluating tools, or expressing pain points. Returns AI-scored results with intent categories and confidence levels.",
      "parameters": {
        "type": "object",
        "properties": {
          "sources": {
            "type": "array",
            "items": {
              "type": "string",
              "enum": ["reddit", "twitter", "hackernews", "linkedin_jobs", "linkedin_people", "telegram", "producthunt", "indiehackers", "devto", "lobsters", "hashnode", "betalist", "echojs", "wip", "launchingnext", "hackernoon", "makerlog", "alternativeto", "saashub", "tldr", "changelog", "google_news", "indeed"]
            },
            "description": "Which platforms to scan. Use multiple for broader coverage."
          },
          "include_keywords": {
            "type": "array",
            "items": { "type": "string" },
            "description": "Keywords that signals must match. Example: ['looking for CRM', 'need sales tool']"
          },
          "exclude_keywords": {
            "type": "array",
            "items": { "type": "string" },
            "description": "Keywords to filter out. Example: ['hiring', 'job posting']"
          },
          "mode": {
            "type": "string",
            "enum": ["LEAD", "SEO"],
            "description": "LEAD mode scores for buying/evaluation intent. SEO mode scores for content/backlink opportunities."
          },
          "min_intent_score": {
            "type": "number",
            "minimum": 0,
            "maximum": 1,
            "description": "Only return signals with intent score >= this value. Range: 0.0 to 1.0"
          },
          "limit": {
            "type": "integer",
            "minimum": 1,
            "maximum": 100,
            "description": "Maximum signals to return per source. Default: 25"
          }
        },
        "required": ["sources", "include_keywords"]
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "score_content",
      "description": "Score arbitrary text for buying intent, frustration, hiring signals, or evaluation behavior. Works on any text — social posts, emails, support tickets, chat messages.",
      "parameters": {
        "type": "object",
        "properties": {
          "texts": {
            "type": "array",
            "items": { "type": "string" },
            "description": "Array of text content to score (max 50 items)"
          },
          "include_keywords": {
            "type": "array",
            "items": { "type": "string" },
            "description": "Context keywords for more relevant scoring"
          },
          "mode": {
            "type": "string",
            "enum": ["LEAD", "SEO"],
            "description": "Scoring mode. LEAD = buying intent, SEO = content opportunities"
          }
        },
        "required": ["texts"]
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "get_signal_sources",
      "description": "List all available signal intelligence sources with their current status, capabilities, and rate limits.",
      "parameters": {
        "type": "object",
        "properties": {},
        "required": []
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "enrich_signal",
      "description": "Generate AI-powered outreach messages, strategic analysis, and lead packets for a specific signal. Creates personalized, non-salesy outreach content.",
      "parameters": {
        "type": "object",
        "properties": {
          "signal_id": {
            "type": "string",
            "description": "The ID of the signal to enrich (from scan results)"
          },
          "outreach_style": {
            "type": "string",
            "enum": ["helpful", "curious", "connector"],
            "description": "Tone of the outreach message. helpful=lead with value, curious=ask smart questions, connector=offer introductions"
          },
          "custom_directives": {
            "type": "string",
            "description": "Additional instructions for the AI when generating content"
          }
        },
        "required": ["signal_id"]
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "get_cached_signals",
      "description": "Retrieve previously scanned signals from the cache with filtering by source, intent score, date range, and pipeline status.",
      "parameters": {
        "type": "object",
        "properties": {
          "source": {
            "type": "string",
            "description": "Filter by platform (e.g., 'reddit', 'twitter')"
          },
          "min_score": {
            "type": "number",
            "description": "Minimum intent score (0.0-1.0)"
          },
          "category": {
            "type": "string",
            "enum": ["buying", "evaluating", "frustrated", "hiring", "building", "asking", "announcing", "discussing"],
            "description": "Filter by intent category"
          },
          "status": {
            "type": "string",
            "enum": ["new", "contacted", "replied", "won", "lost"],
            "description": "Filter by pipeline status"
          },
          "limit": {
            "type": "integer",
            "description": "Max results to return (default: 25)"
          }
        },
        "required": []
      }
    }
  }
]
```

---

### MCP Tool Manifest

For Claude Desktop, Cursor, Windsurf, and other MCP-compatible clients:

```json
{
  "name": "redprayers-intelligence",
  "version": "1.0.0",
  "description": "Real-time signal intelligence across 22+ online platforms. Scans Reddit, Twitter, LinkedIn, Hacker News, and more for high-intent buying signals, hiring needs, and competitive intelligence.",
  "auth": {
    "type": "bearer",
    "token_env": "REDPRAYERS_API_KEY"
  },
  "tools": [
    {
      "name": "scan_signals",
      "description": "Scan online platforms for high-intent signals matching keywords. Returns AI-scored results with intent categories, confidence levels, and reasoning.",
      "inputSchema": {
        "type": "object",
        "properties": {
          "sources": {
            "type": "array",
            "items": { "type": "string" },
            "description": "Platforms to scan: reddit, twitter, hackernews, linkedin_jobs, linkedin_people, telegram, producthunt, indiehackers, devto, lobsters, hashnode, betalist, echojs, wip, launchingnext, hackernoon, makerlog, alternativeto, saashub, tldr, changelog, google_news, indeed"
          },
          "include_keywords": {
            "type": "array",
            "items": { "type": "string" },
            "description": "Keywords to match"
          },
          "exclude_keywords": {
            "type": "array",
            "items": { "type": "string" },
            "description": "Keywords to exclude"
          },
          "mode": { "type": "string", "enum": ["LEAD", "SEO"] },
          "min_intent_score": { "type": "number" },
          "limit": { "type": "integer" }
        },
        "required": ["sources", "include_keywords"]
      }
    },
    {
      "name": "score_content",
      "description": "Score arbitrary text for intent signals — buying, hiring, frustration, evaluation. Works on any text from any source.",
      "inputSchema": {
        "type": "object",
        "properties": {
          "texts": {
            "type": "array",
            "items": { "type": "string" },
            "description": "Texts to score (max 50)"
          },
          "include_keywords": {
            "type": "array",
            "items": { "type": "string" }
          },
          "mode": { "type": "string", "enum": ["LEAD", "SEO"] }
        },
        "required": ["texts"]
      }
    },
    {
      "name": "get_sources",
      "description": "List all available signal sources with status and capabilities.",
      "inputSchema": { "type": "object", "properties": {} }
    },
    {
      "name": "enrich_signal",
      "description": "Generate outreach messages, analysis, and lead packets for a signal.",
      "inputSchema": {
        "type": "object",
        "properties": {
          "signal_id": { "type": "string" },
          "outreach_style": { "type": "string", "enum": ["helpful", "curious", "connector"] },
          "custom_directives": { "type": "string" }
        },
        "required": ["signal_id"]
      }
    },
    {
      "name": "get_cached_signals",
      "description": "Retrieve previously scanned signals with filters.",
      "inputSchema": {
        "type": "object",
        "properties": {
          "source": { "type": "string" },
          "min_score": { "type": "number" },
          "category": { "type": "string" },
          "status": { "type": "string" },
          "limit": { "type": "integer" }
        }
      }
    }
  ]
}
```

---

## Streaming Protocol

The `/v1/scan/stream` endpoint uses Server-Sent Events (SSE) for real-time signal delivery.

### Event Types

```
event: scan_started
data: {"sources":["reddit","hackernews","twitter"],"total_sources":3,"estimated_seconds":15}

event: source_started
data: {"source":"reddit","position":1,"total_sources":3}

event: source_completed
data: {"source":"reddit","signals_found":12,"signals_scored":8,"processing_ms":2340}

event: signal
data: {"id":"t3_abc","source":"reddit","title":"Looking for CRM","intent":{"score":0.92,"category":"evaluating","reasoning":"..."}}

event: source_error
data: {"source":"twitter","error":"rate_limited","message":"Twitter rate limit exceeded, retry in 30s","retry_after":30}

event: scan_completed
data: {"total_signals":23,"total_sources_ok":2,"total_sources_failed":1,"processing_ms":8432,"cache_hits":45}
```

### Connection Example (JavaScript)

```javascript
const eventSource = new EventSource('/v1/scan/stream', {
  headers: { 'Authorization': 'Bearer aai_...' }
});

eventSource.addEventListener('signal', (event) => {
  const signal = JSON.parse(event.data);
  console.log(`[${signal.source}] ${signal.title} — Score: ${signal.intent.score}`);
});

eventSource.addEventListener('scan_completed', (event) => {
  const summary = JSON.parse(event.data);
  console.log(`Done! ${summary.total_signals} signals found`);
  eventSource.close();
});
```

### Connection Example (Python)

```python
import httpx_sse

async with httpx.AsyncClient() as client:
    async with httpx_sse.aconnect_sse(
        client, "POST", "https://signal.saas-signal.com/v1/scan/stream",
        json={"sources": ["reddit"], "keywords": {"include": ["CRM"]}},
        headers={"Authorization": "Bearer aai_..."}
    ) as sse:
        async for event in sse.aiter_sse():
            if event.event == "signal":
                signal = json.loads(event.data)
                print(f"Signal: {signal['title']} (score: {signal['intent']['score']})")
```

---

## Data Models

### Signal

The core data object returned by scan and signals endpoints.

```typescript
interface Signal {
  id: string;                    // Unique identifier (source-specific format)
  source: SourceId;              // Platform identifier
  source_community: string;      // Subreddit, channel, board, etc.
  title: string;                 // Post/content title
  content: string;               // Full text content
  author: string;                // Author username
  url: string;                   // Canonical URL to the original content
  created_at: string;            // ISO 8601 timestamp
  created_utc: number;           // Unix timestamp (seconds)
  intent: IntentAnalysis;        // AI-generated intent analysis
  pipeline_status?: PipelineStatus; // Lead pipeline status (if tracked)
  locked_at?: string;            // When the signal was added to pipeline
}

interface IntentAnalysis {
  score: number;                 // 0.0 to 1.0 — overall intent strength
  confidence: number;            // 0.0 to 1.0 — AI confidence in the score
  category: IntentCategory;      // Classification of the intent type
  urgency: "low" | "medium" | "high"; // Time sensitivity
  reasoning: string;             // Human-readable explanation of the score
}

type IntentCategory =
  | "buying"       // Actively looking to purchase
  | "evaluating"   // Comparing options
  | "frustrated"   // Pain with current solution
  | "hiring"       // Looking to hire
  | "building"     // Creating something
  | "asking"       // Seeking recommendations
  | "announcing"   // Launching/shipping
  | "discussing";  // General discussion

type PipelineStatus = "new" | "contacted" | "replied" | "won" | "lost";

type SourceId =
  | "reddit" | "twitter" | "hackernews" | "telegram"
  | "linkedin_jobs" | "linkedin_people"
  | "producthunt" | "indiehackers" | "devto" | "lobsters"
  | "hashnode" | "betalist" | "echojs" | "wip"
  | "launchingnext" | "hackernoon" | "makerlog"
  | "alternativeto" | "saashub" | "tldr" | "changelog"
  | "google_news" | "indeed";
```

### ScanRequest

```typescript
interface ScanRequest {
  sources: SourceId[];
  keywords: {
    include: string[];
    exclude?: string[];
    subreddits?: string[];       // Reddit-specific
    category?: string;           // Source-specific category
  };
  mode?: "LEAD" | "SEO";
  context?: CampaignContext;
  limit?: number;                // 1-100, default 25
  min_intent_score?: number;     // 0.0-1.0, default 0.0
  deduplicate?: boolean;         // default true
}

interface CampaignContext {
  company_name?: string;
  campaign_intent?: string;
  campaign_mission?: string;
  campaign_urgency?: string;
  campaign_goal?: string;
}
```

---

## Source Catalog

### Tier 1: No Configuration Required

These sources work immediately — no API keys, no setup.

| Source ID | Platform | Method | Rate Limit | Max Results |
|-----------|----------|--------|------------|-------------|
| `reddit` | Reddit | RSS feeds | 30/min | 100 |
| `hackernews` | Hacker News | Firebase API | 30/min | 100 |
| `devto` | DEV.to | Public API | 30/min | 50 |
| `lobsters` | Lobsters | RSS feed | 10/min | 50 |
| `hashnode` | Hashnode | GraphQL API | 20/min | 50 |
| `betalist` | BetaList | Scraping | 5/min | 30 |
| `echojs` | Echo JS | RSS feed | 10/min | 30 |
| `wip` | WIP.co | Public API | 10/min | 30 |
| `launchingnext` | LaunchingNext | Scraping | 5/min | 30 |
| `hackernoon` | HackerNoon | RSS feed | 10/min | 50 |
| `makerlog` | Makerlog | Public API | 10/min | 30 |
| `alternativeto` | AlternativeTo | Scraping | 5/min | 30 |
| `saashub` | SaaSHub | Scraping | 5/min | 30 |
| `tldr` | TLDR Newsletter | RSS feed | 10/min | 50 |
| `changelog` | Changelog | RSS feed | 10/min | 50 |
| `indiehackers` | Indie Hackers | Scraping | 5/min | 30 |
| `producthunt` | Product Hunt | Scraping | 5/min | 30 |

### Tier 2: Configuration Required

These sources require API keys or credentials configured in your org settings.

| Source ID | Platform | Config Required | Method |
|-----------|----------|----------------|--------|
| `twitter` | Twitter / X | Netrows API key | Netrows or ScrapingDog |
| `linkedin_jobs` | LinkedIn Jobs | Netrows API key | Netrows scraping |
| `linkedin_people` | LinkedIn People | Netrows API key | Netrows scraping |
| `google_news` | Google News | Netrows or ScrapingDog key | API scraping |
| `indeed` | Indeed Jobs | ScrapingDog API key | SERP scraping |
| `telegram` | Telegram | Telegram API credentials | Telethon client |

### Source Capabilities Matrix

| Capability | reddit | twitter | hackernews | linkedin_* | telegram | producthunt |
|------------|--------|---------|------------|------------|----------|-------------|
| Keyword search | Yes | Yes | Yes | Yes | Yes | Yes |
| Community filter | Subreddits | — | — | — | Channels | — |
| Category filter | — | Yes | — | — | — | — |
| AI hashtag gen | — | Yes | — | — | — | — |
| Realtime | — | Yes | — | — | Yes | — |
| Historical | 30 days | 7 days | 30 days | — | Unlimited | 7 days |

---

## Intent Scoring System

The AI intent scoring pipeline uses a multi-step analysis:

### Scoring Pipeline

```
Raw Content → Keyword Matching → AI Analysis → Score + Category + Reasoning
                                      ↑
                              Campaign Context
                              (if provided)
```

### Score Ranges

| Range | Label | Meaning |
|-------|-------|---------|
| 0.90–1.00 | **Critical** | Immediate buying/hiring signal with explicit need |
| 0.70–0.89 | **High** | Strong intent, likely evaluating or frustrated |
| 0.50–0.69 | **Medium** | Moderate interest, worth monitoring |
| 0.30–0.49 | **Low** | Tangentially related, general discussion |
| 0.00–0.29 | **Noise** | Not relevant to the keyword context |

### Mode Differences

**LEAD Mode** optimizes for:
- Buying signals and purchasing intent
- Frustration with current solutions
- Active evaluation of alternatives
- Budget mentions and decision timelines

**SEO Mode** optimizes for:
- Content gap opportunities
- Trending topics in your niche
- Backlink-worthy discussions
- Community engagement opportunities

### Context Enhancement

When `context` is provided, scoring accuracy improves significantly:

- **Without context**: Generic keyword-based scoring (~70% accuracy)
- **With context**: Company-aware scoring with competitive understanding (~90% accuracy)

---

## JavaScript/TypeScript SDK

### Installation

```bash
npm install @redprayers/intelligence
# or
yarn add @redprayers/intelligence
# or
pnpm add @redprayers/intelligence
```

### Quick Start

```typescript
import { RedPrayers } from '@redprayers/intelligence';

const rp = new RedPrayers({
  apiKey: process.env.REDPRAYERS_API_KEY, // Your AiAS API key
  baseUrl: 'https://signal.saas-signal.com', // Optional, defaults to production
});

// Scan for signals
const { data } = await rp.scan({
  sources: ['reddit', 'hackernews', 'twitter'],
  keywords: {
    include: ['looking for CRM', 'need sales tool'],
    exclude: ['hiring'],
  },
  mode: 'LEAD',
  minIntentScore: 0.6,
});

console.log(`Found ${data.signals.length} high-intent signals`);

for (const signal of data.signals) {
  console.log(`[${signal.source}] ${signal.title}`);
  console.log(`  Score: ${signal.intent.score} (${signal.intent.category})`);
  console.log(`  ${signal.intent.reasoning}`);
}
```

### Streaming

```typescript
const stream = rp.scan.stream({
  sources: ['reddit', 'twitter'],
  keywords: { include: ['AI tools'] },
});

for await (const event of stream) {
  if (event.type === 'signal') {
    console.log(`New signal: ${event.signal.title} (${event.signal.intent.score})`);
  } else if (event.type === 'source_completed') {
    console.log(`${event.source} done — ${event.signals_found} signals`);
  }
}
```

### Score Custom Content

```typescript
const { data } = await rp.score([
  { id: 'email_1', text: 'Looking to switch from HubSpot, budget approved' },
  { id: 'slack_2', text: 'Anyone tried Monday.com for project management?' },
], {
  keywords: { include: ['project management', 'CRM'] },
  mode: 'LEAD',
});

for (const item of data.scored_items) {
  console.log(`${item.id}: ${item.intent.score} (${item.intent.category})`);
}
```

### Enrich a Signal

```typescript
const { data } = await rp.enrich({
  signalId: 't3_abc123',
  generate: ['outreach', 'analysis'],
  outreachStyle: 'helpful',
});

console.log(data.outreach.message);
console.log(data.analysis.pain_points);
```

### Get Sources

```typescript
const { data } = await rp.sources();
const available = data.sources.filter(s => s.status === 'available');
console.log(`${available.length} sources ready`);
```

### Configuration Options

```typescript
const rp = new RedPrayers({
  apiKey: 'aai_...',
  baseUrl: 'https://signal.saas-signal.com',
  timeout: 30_000,        // Request timeout (ms)
  retries: 3,             // Auto-retry on 5xx/network errors
  retryDelay: 1000,       // Base delay between retries (ms)
  onRateLimit: (info) => {
    console.log(`Rate limited. Reset in ${info.retryAfter}s`);
  },
});
```

### TypeScript Types

The SDK exports all types for full IntelliSense support:

```typescript
import type {
  Signal,
  IntentAnalysis,
  IntentCategory,
  ScanRequest,
  ScanResponse,
  ScoreRequest,
  ScoreResponse,
  EnrichRequest,
  EnrichResponse,
  SourceInfo,
  UsageStats,
  StreamEvent,
  ScanStartedEvent,
  SignalEvent,
  SourceCompletedEvent,
  ScanCompletedEvent,
} from '@redprayers/intelligence';
```

---

## Python SDK

### Installation

```bash
pip install redprayers-intelligence
# or
poetry add redprayers-intelligence
```

### Quick Start

```python
from redprayers import RedPrayers

rp = RedPrayers(api_key="aai_...")

# Scan for signals
result = await rp.scan(
    sources=["reddit", "hackernews", "twitter"],
    keywords={"include": ["looking for CRM", "need sales tool"]},
    mode="LEAD",
    min_intent_score=0.6,
)

for signal in result.data.signals:
    print(f"[{signal.source}] {signal.title}")
    print(f"  Score: {signal.intent.score} ({signal.intent.category})")
    print(f"  {signal.intent.reasoning}")
```

### Streaming

```python
async for event in rp.scan.stream(
    sources=["reddit", "twitter"],
    keywords={"include": ["AI tools"]},
):
    if event.type == "signal":
        print(f"Signal: {event.signal.title} ({event.signal.intent.score})")
    elif event.type == "source_completed":
        print(f"{event.source} done — {event.signals_found} signals")
```

### Score Custom Content

```python
result = await rp.score(
    items=[
        {"id": "email_1", "text": "Looking to switch from HubSpot"},
        {"id": "slack_2", "text": "Anyone tried Monday.com?"},
    ],
    keywords={"include": ["project management", "CRM"]},
    mode="LEAD",
)

for item in result.data.scored_items:
    print(f"{item.id}: {item.intent.score} ({item.intent.category})")
```

### Enrich a Signal

```python
result = await rp.enrich(
    signal_id="t3_abc123",
    generate=["outreach", "analysis"],
    outreach_style="helpful",
)

print(result.data.outreach.message)
print(result.data.analysis.pain_points)
```

### Synchronous Usage

```python
from redprayers import RedPrayers

rp = RedPrayers(api_key="aai_...", sync=True)

# All methods work synchronously
result = rp.scan(sources=["reddit"], keywords={"include": ["CRM"]})
```

### Pydantic Models

All responses are typed with Pydantic models:

```python
from redprayers.models import (
    Signal,
    IntentAnalysis,
    ScanRequest,
    ScanResponse,
    ScoreResponse,
    EnrichResponse,
    SourceInfo,
    UsageStats,
)
```

### LangChain Integration

```python
from redprayers.integrations.langchain import RedPrayersTool

tool = RedPrayersTool(api_key="aai_...")

# Use as a LangChain tool
from langchain.agents import initialize_agent
agent = initialize_agent(tools=[tool], llm=llm)
result = agent.run("Find people on Reddit looking for CRM software")
```

### CrewAI Integration

```python
from redprayers.integrations.crewai import RedPrayersSignalTool

signal_tool = RedPrayersSignalTool(api_key="aai_...")

researcher = Agent(
    role="Lead Researcher",
    tools=[signal_tool],
    goal="Find high-intent prospects across social platforms"
)
```

---

## Error Reference

| HTTP Status | Error Code | Description |
|-------------|-----------|-------------|
| 400 | `invalid_request` | Malformed request body or missing required fields |
| 400 | `invalid_source` | Unrecognized source ID |
| 400 | `invalid_mode` | Mode must be "LEAD" or "SEO" |
| 400 | `too_many_items` | Score endpoint: max 50 items per request |
| 400 | `too_many_sources` | Scan: max 10 sources per request |
| 401 | `missing_api_key` | No Authorization header |
| 401 | `invalid_api_key` | Key is invalid, expired, or revoked |
| 403 | `insufficient_plan` | Your plan doesn't include this feature |
| 403 | `source_not_configured` | The requested source requires configuration |
| 404 | `signal_not_found` | Signal ID not found in your org's data |
| 429 | `rate_limit_exceeded` | Too many requests — check `Retry-After` header |
| 500 | `scoring_failed` | AI scoring service unavailable |
| 500 | `source_error` | External source returned an error |
| 502 | `upstream_timeout` | External source did not respond in time |
| 503 | `service_unavailable` | API is temporarily unavailable |

### Error Response Format

```json
{
  "error": {
    "code": "invalid_source",
    "message": "Source 'myspace' is not supported. See /v1/sources for available sources.",
    "details": {
      "invalid_sources": ["myspace"],
      "valid_sources": ["reddit", "twitter", "hackernews", "..."]
    }
  },
  "meta": {
    "request_id": "req_err_abc123",
    "timestamp": "2026-02-19T22:48:00Z",
    "version": "1.0.0"
  }
}
```

---

## Migration Guide

### Internal → v1 Mapping

If you're currently using the internal API routes, here's how they map to v1:

| Internal Route | v1 Route | Notes |
|---------------|----------|-------|
| `POST /api/radar/scan` | `POST /v1/scan` | Single source → multi-source, structured intent |
| `POST /api/radar/scan/stream` | `POST /v1/scan/stream` | Same SSE protocol, enriched event types |
| `GET /api/radar/status` | `GET /v1/sources` | More detail, capabilities, config status |
| `GET /api/contacts/` | `GET /v1/signals?status=new` | Unified signal model |
| `POST /api/dispatch/generate` | `POST /v1/enrich` | Combined outreach + analysis + lead packet |
| `GET /api/radar/cache/status` | `GET /v1/usage` | Expanded with full usage stats |
| — (new) | `POST /v1/score` | Score arbitrary content from any source |
| — (new) | `GET /v1/tools` | LLM tool definitions |

### Key Differences

1. **Multi-source scanning**: v1 `scan` accepts an array of sources; internal only does one at a time
2. **Structured intent**: v1 returns `intent.category`, `intent.urgency`, `intent.reasoning` — internal returns flat `intent_score` and `intent_note`
3. **Response envelope**: v1 wraps everything in `{data, meta}` — internal returns raw data
4. **JSONL support**: v1 signals endpoint supports `format=jsonl` for bulk export
5. **Tool definitions**: v1 includes `/tools` for LLM agent auto-discovery

### Coexistence

Both APIs run simultaneously. The internal routes remain fully functional and unchanged. You can migrate at your own pace.

---

## Appendix: Existing Routes (Unchanged)

The following internal routes continue to work exactly as before. The v1 API does not modify, wrap, or interfere with them in any way.

### Radar Routes (`/api/radar/`)
- `POST /api/radar/scan` — Single-source scan with intent scoring
- `POST /api/radar/scan/stream` — SSE streaming scan
- `GET /api/radar/status` — Service connection status
- `GET /api/radar/cache/status` — Scanned posts cache stats
- `DELETE /api/radar/cache/clear` — Clear scan cache
- `GET /api/radar/telegram/discover` — Discover Telegram channels
- `POST /api/radar/chat-lead` — AI chat about a lead
- `POST /api/radar/generate-outreach` — Generate outreach messages
- `POST /api/radar/generate-keywords` — AI keyword generation

### Contacts Routes (`/api/contacts/`)
- `GET /api/contacts/` — Get pipeline contacts
- `POST /api/contacts/` — Add contact to pipeline
- `PATCH /api/contacts/{id}/status` — Update contact status
- `DELETE /api/contacts/{id}` — Remove contact
- `DELETE /api/contacts/` — Clear all contacts
- `GET /api/contacts/discovered` — Get discovered leads
- `POST /api/contacts/discovered` — Add discovered lead
- `POST /api/contacts/discovered/{id}/approve` — Approve lead to pipeline
- `DELETE /api/contacts/discovered/{id}` — Dismiss lead
- `DELETE /api/contacts/discovered` — Clear discovered leads

### Dispatch Routes (`/api/dispatch/`)
- `POST /api/dispatch/generate` — Generate lead packet
- `POST /api/dispatch/send` — Send dispatch to ambassador
- `GET /api/dispatch/status/{lead_id}` — Get dispatch status
- `GET /api/dispatch/ambassadors` — List ambassadors
- `POST /api/dispatch/ambassadors/register` — Register ambassador (admin only)
- `POST /api/dispatch/invites/generate` — Generate invite code (admin only)
- `GET /api/dispatch/invites` — List invite codes
- `DELETE /api/dispatch/invites/{code}` — Revoke invite code
- `GET /api/dispatch/bot-status` — Telegram bot status
- `GET /api/dispatch/activity-log` — Dispatch activity log
- `GET /api/dispatch/stats` — Dispatch statistics
- `POST /api/dispatch/webhook` — Telegram webhook handler

### Settings Routes (`/api/settings/`)
- `GET /api/settings/` — Get org settings (role-filtered)
- `PUT /api/settings/reddit` — Update Reddit credentials
- `PUT /api/settings/aias` — Update AiAS config
- `PUT /api/settings/telegram` — Update Telegram credentials
- `POST /api/settings/presets` — Add keyword preset
- `DELETE /api/settings/presets/{name}` — Delete preset
- `PUT /api/settings/auto-scan` — Toggle auto-scan
- `PUT /api/settings/scrapingdog` — Update ScrapingDog config
- `GET /api/settings/scrapingdog/usage` — ScrapingDog usage stats
- `PUT /api/settings/netrows` — Update Netrows config
- `GET /api/settings/netrows/usage` — Netrows usage stats

### Team Chat Routes (`/api/team-chat/`)
- `GET /api/team-chat/messages` — Get chat messages
- `POST /api/team-chat/messages` — Send message
- `GET /api/team-chat/username` — Get username
- `POST /api/team-chat/username` — Set username

### Auth Routes (`/api/auth/`)
- `POST /api/auth/validate` — Validate API key
- `GET /api/auth/me` — Get authenticated user info
