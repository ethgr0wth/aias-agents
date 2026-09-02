---
title: Web Extraction
icon: Download
category: RAG
order: 2
description: Service for scraping and processing web content.
---

# Web Extraction Service

> Real-time webpage content extraction for AI context.

**Status:** Specification  
**Version:** 1.0  
**Created:** December 2025

---

## Overview

The WebExtractionService provides real-time webpage content extraction capabilities, enabling the AI to fetch and process live content from any URL. This service operates independently of search engines, allowing direct URL access when users specify a target site.

### Key Capabilities

1. **Direct URL Extraction** - Fetch content from user-specified URLs bypassing search engines
2. **Clean Content Parsing** - Strip ads, navigation, scripts, and extract main content
3. **Markdown Output** - Return structured, LLM-optimized markdown
4. **JavaScript Rendering** - Handle dynamic SPAs via Puppeteer fallback
5. **Smart Caching** - 5-minute TTL to avoid redundant fetches
6. **Rate Limiting** - Per-domain throttling to respect server limits

---

## Usage Modes

### Mode 1: Direct URL Extraction

User explicitly provides a URL to extract content from.

```
User: "What's on interchained.org?"
     ↓
AI detects URL mention → calls visit_url tool
     ↓
WebExtractionService.extract("https://interchained.org")
     ↓
Returns clean markdown content
     ↓
AI generates response with live data
```

### Mode 2: Search + Extract (Future Integration)

Search providers discover URLs, then WebExtractionService extracts full content.

```
User: "What's the latest on AI regulations?"
     ↓
AI calls search_web tool
     ↓
Search providers return URLs with snippets
     ↓
WebExtractionService.extract_batch(top_3_urls)
     ↓
Returns aggregated markdown content
     ↓
AI generates comprehensive response
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    WebExtractionService                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │ FetchClient  │    │ BrowserPool  │    │ContentParser │       │
│  │  (HTTP/2)    │    │ (Puppeteer)  │    │ (Readability)│       │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘       │
│         │                   │                   │                │
│         └─────────┬─────────┘                   │                │
│                   │                             │                │
│         ┌─────────▼─────────┐                   │                │
│         │  FetchCoordinator │                   │                │
│         │  - Retry logic    │                   │                │
│         │  - Rate limiting  │                   │                │
│         └─────────┬─────────┘                   │                │
│                   │                             │                │
│         ┌─────────▼─────────────────────────────▼───┐           │
│         │            ContentExtractor               │           │
│         │  - Main content detection                 │           │
│         │  - Script/ad removal                      │           │
│         │  - Markdown generation                    │           │
│         └─────────┬─────────────────────────────────┘           │
│                   │                                              │
│         ┌─────────▼─────────┐                                   │
│         │  ExtractionCache  │                                   │
│         │  - Redis-backed   │                                   │
│         │  - 5-min TTL      │                                   │
│         └───────────────────┘                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Security Considerations

### URL Blocklist

- `localhost`, `127.0.0.1`
- `*.local`, `*.internal`
- `file://`, `ftp://`
- Private IP ranges

### Content Sanitization

- Remove all JavaScript from extracted content
- Strip data URIs
- Sanitize URLs in links
- Limit content length to prevent memory exhaustion

### Rate Limiting

- Global: 100 extractions/minute/workspace
- Per-domain: 1 request/second (configurable)
- Concurrent browser tabs: max 3

---

## Performance Targets

| Metric | Target |
|--------|--------|
| HTTP fetch latency | < 2s (p95) |
| Browser render latency | < 10s (p95) |
| Content parsing | < 100ms |
| Cache hit ratio | > 30% |
| Success rate | > 95% |
