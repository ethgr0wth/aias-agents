# aiassist-secure-intelligence-signal

Official Python SDK for the **AiAS Intelligence Signal API** — real-time signal intelligence across 22+ online platforms with AI-powered intent scoring.

Built by [AiAssist Secure](https://aiassist.net) | API: [saas-signal.com](https://saas-signal.com)

## Features

- Sync (`AiASClient`) and async (`AsyncAiASClient`) clients
- Pydantic v2 models for all request/response types
- SSE streaming via generator/async generator
- Auto-retry with exponential backoff
- Custom exception hierarchy with status codes and request IDs
- Full type annotations (py.typed)
- Python 3.10+

## Installation

```bash
pip install aiassist-secure-intelligence-signal
```

## Quick Start

```python
from aias_intelligence_signal import AiASClient

client = AiASClient(api_key="aai_your_api_key_here")

# Scan Reddit and Hacker News for buying signals
result = client.scan(
    sources=["reddit", "hackernews"],
    keywords={"include": ["CRM", "project management"]},
    mode="LEAD",
    min_intent_score=0.6,
    limit=25,
)

for signal in result.data.signals:
    print(f"[{signal.intent.category}] {signal.title}")
    print(f"  Score: {signal.intent.score} | Source: {signal.source}")
    print(f"  URL: {signal.url}")
```

## Usage Examples

### Multi-Source Scan with Campaign Context

```python
from aias_intelligence_signal import AiASClient, Keywords, CampaignContext

client = AiASClient(api_key="aai_your_key")

result = client.scan(
    sources=["reddit", "hackernews", "devto", "producthunt"],
    keywords=Keywords(
        include=["workflow automation", "no-code", "zapier alternative"],
        exclude=["free", "open source"],
        subreddits=["SaaS", "startups", "Entrepreneur"],
    ),
    mode="LEAD",
    context=CampaignContext(
        company_name="FlowBot",
        campaign_intent="Find users frustrated with existing automation tools",
        campaign_goal="Generate qualified leads for enterprise plan",
    ),
    min_intent_score=0.5,
    limit=50,
)

summary = result.data.scan_summary
print(f"Found {summary.total_returned} high-intent signals")
print(f"Scanned {summary.total_fetched} posts across {len(summary.sources_scanned)} sources")
```

### Real-Time Streaming Scan

```python
for event in client.scan_stream(
    sources=["reddit", "twitter", "hackernews"],
    keywords={"include": ["AI agent", "LLM framework"]},
):
    if event.event == "scan_started":
        print(f"Scanning {event.data['total_sources']} sources...")
    elif event.event == "signal":
        print(f"  Found: {event.data['title']} (score: {event.data['intent']['score']})")
    elif event.event == "source_completed":
        print(f"  {event.data['source']}: {event.data['signals_found']} signals")
    elif event.event == "scan_completed":
        print(f"Done! {event.data['total_signals']} signals in {event.data['processing_ms']}ms")
```

### Async Client

```python
import asyncio
from aias_intelligence_signal import AsyncAiASClient

async def main():
    async with AsyncAiASClient(api_key="aai_your_key") as client:
        result = await client.scan(
            sources=["reddit", "hackernews"],
            keywords={"include": ["saas", "b2b"]},
            min_intent_score=0.7,
        )

        for signal in result.data.signals:
            print(f"{signal.title} — {signal.intent.score}")

        # Async streaming
        async for event in client.scan_stream(
            sources=["reddit"],
            keywords={"include": ["need CRM"]},
        ):
            if event.event == "signal":
                print(f"Live: {event.data['title']}")

asyncio.run(main())
```

### Score Your Own Content

```python
result = client.score(
    items=[
        {"id": "1", "text": "Looking for a CRM that integrates with Slack and has good API docs"},
        {"id": "2", "text": "Just launched my new side project for todo lists!"},
        {"id": "3", "text": "We need to migrate off Salesforce ASAP, budget approved"},
    ],
    keywords={"include": ["CRM", "Slack integration"]},
    mode="LEAD",
)

for scored in result.data["scores"]:
    print(f"{scored['id']}: {scored['category']} ({scored['score']}) — {scored['reasoning']}")
```

### Enrich a Signal with AI Outreach

```python
scan_result = client.scan(
    sources=["reddit"],
    keywords={"include": ["need help with analytics"]},
    min_intent_score=0.7,
    limit=5,
)

if scan_result.data.signals:
    top_signal = scan_result.data.signals[0]

    enriched = client.enrich(
        signal=top_signal.model_dump(),
        generate=["outreach", "analysis", "lead_packet"],
        outreach_style="helpful",
        custom_directives="Focus on our free tier and migration assistance",
    )

    print(enriched.data)
```

### List Available Sources

```python
sources = client.get_sources()

print(f"{len(sources.data)} sources available")
for source in sources.data:
    status = "(requires config)" if source.requires_config else "(ready)"
    print(f"  {source.name} {status} — max {source.capabilities.max_results} results")
```

### Get LLM Tool Definitions

```python
# For OpenAI function calling
openai_tools = client.get_tools(format="openai")

# For MCP server integration
mcp_manifest = client.get_tools(format="mcp")

# For LangChain
langchain_tools = client.get_tools(format="langchain")
```

### Check Usage Stats

```python
usage = client.get_usage()
print(f"Scans today: {usage.data['scans_today']}")
print(f"Signals cached: {usage.data['signals_cached']}")
```

### Browse Cached Signals

```python
signals = client.get_signals(
    source="reddit",
    min_score=0.8,
    category="buying",
    limit=20,
)

print(f"{signals.data['total']} total buying signals from Reddit")
```

## Error Handling

```python
from aias_intelligence_signal import (
    AiASClient,
    AiASError,
    AuthenticationError,
    RateLimitError,
    ValidationError,
    ServerError,
)

try:
    result = client.scan(...)
except AuthenticationError as e:
    print(f"Invalid API key: {e.message}")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after}s")
except ValidationError as e:
    print(f"Bad request: {e.message}")
    print(f"Details: {e.details}")
except ServerError as e:
    print(f"Server error [{e.status_code}]: {e.message}")
except AiASError as e:
    print(f"API Error [{e.code}]: {e.message}")
    print(f"Request ID: {e.request_id}")
```

## Configuration

```python
client = AiASClient(
    api_key="aai_your_key",
    base_url="https://saas-signal.com",  # default
    timeout=30.0,                         # seconds, default
    stream_timeout=120.0,                 # seconds, default
    max_retries=3,                        # default, set 0 to disable
)
```

## Context Manager

```python
# Sync
with AiASClient(api_key="aai_your_key") as client:
    result = client.scan(...)

# Async
async with AsyncAiASClient(api_key="aai_your_key") as client:
    result = await client.scan(...)
```

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `scan()` | `POST /v1/scan` | Multi-source signal scan with AI scoring |
| `scan_stream()` | `POST /v1/scan/stream` | Real-time SSE streaming scan |
| `get_sources()` | `GET /v1/sources` | List 22+ available signal sources |
| `get_signals()` | `GET /v1/signals` | Browse cached signals with filters |
| `score()` | `POST /v1/score` | Score arbitrary text for intent |
| `enrich()` | `POST /v1/enrich` | AI outreach, analysis, lead packets |
| `get_usage()` | `GET /v1/usage` | Organization usage statistics |
| `get_tools()` | `GET /v1/tools` | LLM tool definitions (OpenAI/MCP/LangChain) |

## 22+ Signal Sources

**Tier 1 (no configuration needed):** Reddit, Hacker News, Product Hunt, IndieHackers, Dev.to, Lobsters, Hashnode, BetaList, EchoJS, WIP, LaunchingNext, HackerNoon, Makerlog, AlternativeTo, SaaSHub, TLDR, Changelog

**Tier 2 (requires API keys):** Twitter/X, LinkedIn Jobs, LinkedIn People, Telegram, Google News, Indeed

## Intent Categories

`buying` | `evaluating` | `frustrated` | `hiring` | `building` | `asking` | `announcing` | `discussing`

## License

MIT - [AiAssist Secure](https://aiassist.net)
