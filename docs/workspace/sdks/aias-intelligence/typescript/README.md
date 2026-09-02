# @aiassist-secure/intelligence

Official TypeScript/JavaScript SDK for the AiAS Intelligence API.

Scan 22+ online platforms for raw signal data — Reddit, Twitter/X, Hacker News, LinkedIn, Product Hunt, and more.

## Install

```bash
npm install @aiassist-secure/intelligence
```

## Quick Start

```typescript
import { AiASIntelligence } from "@aiassist-secure/intelligence";

const client = new AiASIntelligence({ apiKey: "aai_your_key_here" });

// List available sources
const { data, meta } = await client.sources();
console.log(data.sources); // [{name: "reddit", premium: false, provider: "free"}, ...]

// Scan sources for raw data
const results = await client.scan({
  sources: ["reddit", "hackernews", "devto"],
  keywords: ["saas", "ai tools"],
  limit: 20,
});

console.log(`Found ${results.data.total} results in ${results.meta.processing_ms}ms`);
for (const item of results.data.results) {
  console.log(`[${item.source}] ${item.title} — ${item.url}`);
}
```

## API

### `new AiASIntelligence(config)`

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `apiKey` | `string` | required | Your AiAS API key (`aai_...`) |
| `baseUrl` | `string` | `https://aiassist.net` | API base URL |
| `timeout` | `number` | `60000` | Request timeout in ms |

### `client.sources()`

Returns all available signal sources with premium/free status.

### `client.scan(options)`

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `sources` | `ValidSource[]` | required | Platforms to scan (max 10) |
| `keywords` | `string[]` | `[]` | Search keywords |
| `limit` | `number` | `25` | Results per source (1-50) |
| `category` | `string` | `"recent"` | Sort category |
| `subreddits` | `string[]` | `[]` | Filter specific subreddits |

### Available Sources

**Free:** reddit, hackernews, devto, lobsters, hashnode, betalist, echojs, wip, launchingnext, hackernoon, makerlog, alternativeto, saashub, tldr, changelog, indiehackers, producthunt, telegram

**Premium (requires Netrows key):** twitter, linkedin_jobs, linkedin_people, google_news

## Requirements

- Node.js 18+
- AiAS Pro or Enterprise plan
- Zero dependencies

## License

MIT
