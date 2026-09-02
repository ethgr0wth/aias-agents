# aiassist-secure-intelligence

Official Python SDK for the AiAS Intelligence API.

Scan 22+ online platforms for raw signal data — Reddit, Twitter/X, Hacker News, LinkedIn, Product Hunt, and more.

## Install

```bash
pip install aiassist-secure-intelligence
```

## Quick Start

```python
from aias_intelligence import AiASIntelligence

client = AiASIntelligence(api_key="aai_your_key_here")

# List available sources
resp = client.sources()
for src in resp["data"]["sources"]:
    print(f"{src['name']} ({'premium' if src['premium'] else 'free'})")

# Scan sources for raw data
results = client.scan(
    sources=["reddit", "hackernews", "devto"],
    keywords=["saas", "ai tools"],
    limit=20,
)

print(f"Found {results['data']['total']} results in {results['meta']['processing_ms']}ms")
for item in results["data"]["results"]:
    print(f"[{item['source']}] {item['title']} — {item['url']}")
```

## Async Usage

```python
from aias_intelligence import AiASIntelligenceAsync

async with AiASIntelligenceAsync(api_key="aai_your_key_here") as client:
    results = await client.scan(
        sources=["reddit", "hackernews"],
        keywords=["developer tools"],
    )
    print(results["data"]["total"])
```

## API

### `AiASIntelligence(api_key, base_url, timeout)`

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `api_key` | `str` | required | Your AiAS API key (`aai_...`) |
| `base_url` | `str` | `https://aiassist.net` | API base URL |
| `timeout` | `float` | `60.0` | Request timeout in seconds |

### `client.sources()`

Returns all available signal sources with premium/free status.

### `client.scan(sources, keywords, limit, category, subreddits)`

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `sources` | `list[str]` | required | Platforms to scan (max 10) |
| `keywords` | `list[str]` | `[]` | Search keywords |
| `limit` | `int` | `25` | Results per source (1-50) |
| `category` | `str` | `"recent"` | Sort category |
| `subreddits` | `list[str]` | `[]` | Filter specific subreddits |

### Available Sources

**Free:** reddit, hackernews, devto, lobsters, hashnode, betalist, echojs, wip, launchingnext, hackernoon, makerlog, alternativeto, saashub, tldr, changelog, indiehackers, producthunt, telegram

**Premium (requires Netrows key):** twitter, linkedin_jobs, linkedin_people, google_news

## Requirements

- Python 3.8+
- AiAS Pro or Enterprise plan
- Only dependency: `httpx`

## License

MIT
