# WebExtractionService Specification

**Version**: 1.0  
**Status**: Draft  
**Created**: December 2025

## Overview

The WebExtractionService provides real-time webpage content extraction capabilities, enabling the AI to fetch and process live content from any URL. This service operates independently of search engines, allowing direct URL access when users specify a target site.

### Key Capabilities

1. **Direct URL Extraction** - Fetch content from user-specified URLs bypassing search engines
2. **Clean Content Parsing** - Strip ads, navigation, scripts, and extract main content
3. **Markdown Output** - Return structured, LLM-optimized markdown
4. **JavaScript Rendering** - Handle dynamic SPAs via Puppeteer fallback
5. **Smart Caching** - 5-minute TTL to avoid redundant fetches
6. **Rate Limiting** - Per-domain throttling to respect server limits

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
│         │  - Rate limiting  │                   │
│         │  - robots.txt     │                   │
│         └─────────┬─────────┘                   │
│                   │                             │                │
│         ┌─────────▼─────────────────────────────▼───┐           │
│         │            ContentExtractor               │           │
│         │  - Main content detection                 │           │
│         │  - Script/ad removal                      │           │
│         │  - Heading preservation                   │           │
│         │  - Markdown generation                    │           │
│         └─────────┬─────────────────────────────────┘           │
│                   │                                              │
│         ┌─────────▼─────────┐                                   │
│         │  ExtractionCache  │                                   │
│         │  - Redis-backed   │                                   │
│         │  - 5-min TTL      │                                   │
│         └───────────────────┘                                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

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

**Tool Definition:**
```json
{
  "name": "visit_url",
  "description": "Fetch and extract content from a specific webpage URL. Use when user mentions a website or URL they want to learn about.",
  "parameters": {
    "url": {
      "type": "string",
      "description": "The full URL to extract content from"
    },
    "extract_links": {
      "type": "boolean",
      "description": "Whether to include discovered links in the output",
      "default": false
    },
    "max_content_length": {
      "type": "integer",
      "description": "Maximum content length in characters",
      "default": 15000
    }
  }
}
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

## Data Models

### ExtractionRequest

```python
@dataclass
class ExtractionRequest:
    url: str
    user_id: str
    workspace_id: Optional[str] = None
    extract_links: bool = False
    max_content_length: int = 15000
    timeout_seconds: int = 30
    use_browser: Optional[bool] = None  # None = auto-detect
    tool_call_id: Optional[str] = None
```

### ExtractionResult

```python
@dataclass
class ExtractionResult:
    success: bool
    url: str
    title: str
    content: str  # Clean markdown
    content_length: int
    extracted_at: str  # ISO timestamp
    
    # Metadata
    domain: str
    description: Optional[str] = None
    author: Optional[str] = None
    published_date: Optional[str] = None
    language: Optional[str] = None
    
    # Links (if extract_links=True)
    links: List[ExtractedLink] = field(default_factory=list)
    
    # Performance
    fetch_method: str = "http"  # "http" or "browser"
    latency_ms: int = 0
    cached: bool = False
    
    # Errors
    error_code: Optional[str] = None
    error_message: Optional[str] = None

@dataclass
class ExtractedLink:
    text: str
    url: str
    is_internal: bool
```

### Error Codes

```python
class ExtractionErrorCode(str, Enum):
    URL_BLOCKED = "URL_BLOCKED"           # robots.txt or blocklist
    FETCH_FAILED = "FETCH_FAILED"         # HTTP error
    TIMEOUT = "TIMEOUT"                   # Request timeout
    RATE_LIMITED = "RATE_LIMITED"         # Per-domain throttle
    CONTENT_TOO_LARGE = "CONTENT_TOO_LARGE"
    PARSE_FAILED = "PARSE_FAILED"         # Content extraction error
    BROWSER_ERROR = "BROWSER_ERROR"       # Puppeteer failure
    INVALID_URL = "INVALID_URL"
```

## Components

### 1. FetchCoordinator

Handles HTTP fetching with retry logic, rate limiting, and robots.txt compliance.

```python
class FetchCoordinator:
    """
    Coordinates fetching with:
    - Automatic retry with exponential backoff
    - Per-domain rate limiting (1 req/sec default)
    - robots.txt caching and compliance
    - User-agent rotation
    - Redirect following (max 5 hops)
    """
    
    async def fetch(self, url: str, use_browser: bool = False) -> FetchResult:
        # 1. Check rate limit
        # 2. Check robots.txt (if enabled)
        # 3. Attempt HTTP fetch
        # 4. If JS-heavy content detected or use_browser=True, use Puppeteer
        # 5. Return raw HTML
        pass
```

**Rate Limiting Strategy:**
- Default: 1 request per second per domain
- Configurable per-domain overrides
- Uses Redis sliding window counter

**Retry Policy:**
- Max 3 attempts
- Exponential backoff: 1s, 2s, 4s
- Retry on: 429, 500, 502, 503, 504

### 2. BrowserPool

Manages Puppeteer browser instances for JavaScript-rendered content.

```python
class BrowserPool:
    """
    Manages browser instances with:
    - Connection pooling (max 3 concurrent browsers)
    - Page timeout (30s default)
    - Memory cleanup
    - Screenshot capability (optional)
    """
    
    async def render(self, url: str, timeout: int = 30) -> str:
        # 1. Get browser from pool
        # 2. Navigate to URL
        # 3. Wait for network idle
        # 4. Extract rendered HTML
        # 5. Return to pool
        pass
```

**JS Detection Heuristics:**
- Empty or minimal body content after HTTP fetch
- Known SPA frameworks (React, Angular, Vue indicators)
- Meta tags suggesting CSR
- Domain patterns (known SPA sites)

### 3. ContentExtractor

Parses HTML and extracts clean, structured content.

```python
class ContentExtractor:
    """
    Extracts main content using:
    - Readability-style algorithms
    - Boilerplate removal
    - Heading structure preservation
    - Code block detection
    - Table formatting
    - Image alt text extraction
    """
    
    def extract(self, html: str, url: str) -> ExtractedContent:
        # 1. Parse HTML
        # 2. Remove scripts, styles, nav, footer, ads
        # 3. Identify main content container
        # 4. Extract and format as markdown
        # 5. Truncate to max_content_length
        pass
```

**Content Scoring:**
- Paragraph density
- Text-to-link ratio
- Container size
- Class/ID semantic hints (article, main, content, post)

**Removal Targets:**
- `<script>`, `<style>`, `<noscript>`
- `<nav>`, `<header>`, `<footer>`, `<aside>`
- Elements with ad-related classes/IDs
- Cookie consent banners
- Social sharing widgets
- Comment sections

### 4. ExtractionCache

Redis-backed caching with domain-aware TTL.

```python
class ExtractionCache:
    """
    Caching layer with:
    - 5-minute default TTL
    - Domain-specific TTL overrides
    - Content hash deduplication
    - Cache-aside pattern
    """
    
    DEFAULT_TTL = 300  # 5 minutes
    
    DOMAIN_TTL_OVERRIDES = {
        "news.ycombinator.com": 60,    # Fast-changing
        "reddit.com": 60,
        "twitter.com": 60,
        "wikipedia.org": 3600,          # Slow-changing
        "docs.python.org": 3600,
    }
```

## API Endpoints

### POST /api/web-extraction

Extract content from a single URL.

**Request:**
```json
{
  "url": "https://example.com/article",
  "extract_links": false,
  "max_content_length": 15000,
  "use_browser": null
}
```

**Response:**
```json
{
  "success": true,
  "result": {
    "url": "https://example.com/article",
    "title": "Example Article Title",
    "content": "# Example Article Title\n\nThis is the extracted content in markdown format...",
    "content_length": 5432,
    "extracted_at": "2025-12-30T10:15:00Z",
    "domain": "example.com",
    "description": "Article meta description",
    "fetch_method": "http",
    "latency_ms": 342,
    "cached": false
  }
}
```

### POST /api/web-extraction/batch

Extract content from multiple URLs (for search integration).

**Request:**
```json
{
  "urls": [
    "https://example1.com/article",
    "https://example2.com/post"
  ],
  "max_content_per_url": 5000,
  "max_total_content": 15000
}
```

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "url": "https://example1.com/article",
      "success": true,
      "title": "Article 1",
      "content": "...",
      "content_length": 4500
    },
    {
      "url": "https://example2.com/post",
      "success": true,
      "title": "Article 2",
      "content": "...",
      "content_length": 3200
    }
  ],
  "total_latency_ms": 1250
}
```

## AI Tool Integration

### visit_url Tool

Added to the orchestrator's tool registry:

```python
VISIT_URL_TOOL = {
    "type": "function",
    "function": {
        "name": "visit_url",
        "description": "Fetch and extract the main content from a specific webpage. Use this when the user asks about a specific website, mentions a URL, or wants to know what's on a particular page. Returns the page content as clean, readable text.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The full URL to visit and extract content from (must include http:// or https://)"
                },
                "include_links": {
                    "type": "boolean",
                    "description": "Whether to include a list of links found on the page",
                    "default": False
                }
            },
            "required": ["url"]
        }
    }
}
```

### URL Detection Patterns

Force tool usage when user query contains:
- Explicit URLs: `https?://[^\s]+`
- Domain mentions: `what's on example.com`, `check out site.io`
- Site requests: `visit`, `go to`, `open`, `show me`, `what's on`

## Security Considerations

### URL Blocklist

```python
BLOCKED_URL_PATTERNS = [
    r'localhost',
    r'127\.0\.0\.1',
    r'10\.\d+\.\d+\.\d+',
    r'172\.(1[6-9]|2\d|3[01])\.\d+\.\d+',
    r'192\.168\.\d+\.\d+',
    r'.*\.local$',
    r'.*\.internal$',
    r'file://',
    r'ftp://',
]
```

### Content Sanitization

- Remove all JavaScript from extracted content
- Strip data URIs
- Sanitize URLs in links
- Limit content length to prevent memory exhaustion

### Rate Limiting

- Global: 100 extractions/minute/workspace
- Per-domain: 1 request/second (configurable)
- Concurrent browser tabs: max 3

## Redis Keys

```
# Cache
web_extract:cache:{url_hash}           # Cached extraction result (TTL: 300s)

# Rate Limiting
web_extract:rate:{domain}:{timestamp}  # Sliding window counter

# Robots.txt Cache
web_extract:robots:{domain}            # Parsed robots.txt (TTL: 3600s)

# Usage Tracking
web_extract:usage:{user_id}:{date}     # Daily usage counter

# Domain Throttle State
web_extract:throttle:{domain}          # Last request timestamp
```

## Usage Tracking

```python
@dataclass
class ExtractionUsage:
    user_id: str
    workspace_id: str
    date: str
    extractions_today: int
    bytes_extracted_today: int
    browser_renders_today: int
    cache_hits_today: int
```

## Performance Targets

| Metric | Target |
|--------|--------|
| HTTP fetch latency | < 2s (p95) |
| Browser render latency | < 10s (p95) |
| Content parsing | < 100ms |
| Cache hit ratio | > 30% |
| Success rate | > 95% |

## Future Enhancements

1. **PDF Extraction** - Extract text from PDF URLs
2. **Screenshot Mode** - Return page screenshot for visual content
3. **Structured Data** - Extract JSON-LD, Open Graph, schema.org
4. **Multi-page Crawl** - Follow pagination for long articles
5. **Content Diff** - Track changes to previously extracted pages

## Implementation Phases

### Phase 1: Core Extraction (Current)
- [ ] FetchCoordinator with HTTP fetching
- [ ] ContentExtractor with basic parsing
- [ ] Redis caching
- [ ] API endpoint
- [ ] visit_url tool integration

### Phase 2: Browser Support
- [ ] Puppeteer BrowserPool
- [ ] JS detection heuristics
- [ ] Auto-fallback to browser

### Phase 3: Advanced Features
- [ ] robots.txt compliance
- [ ] Per-domain rate limiting
- [ ] Batch extraction
- [ ] Link extraction

---

## Related Documents

- [Web Search Tool Specification](./web-search-tool-specification.md)
- [Multi-Provider Search Spec](./multi-provider-search-spec.md) (planned)
- [AI Orchestrator Documentation](./INTEGRATION.md)
