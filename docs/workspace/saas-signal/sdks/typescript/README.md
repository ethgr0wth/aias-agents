# @aiassist-secure/intelligence-signal

Official TypeScript/JavaScript SDK for the **AiAS Intelligence Signal API** — real-time signal intelligence across 22+ online platforms with AI-powered intent scoring.

Built by [AiAssist Secure](https://aiassist.net) | API: [saas-signal.com](https://saas-signal.com)

## Features

- Full TypeScript types for all API requests and responses
- 8 endpoint methods: `scan`, `scanStream`, `sources`, `signals`, `score`, `enrich`, `usage`, `tools`
- SSE streaming via async iterator for real-time scan results
- Auto-retry with exponential backoff (configurable)
- AbortController/timeout support
- Zero runtime dependencies (native `fetch`)
- Node.js 18+ and modern browsers

## Installation

```bash
npm install @aiassist-secure/intelligence-signal
```

## Quick Start

```typescript
import { AiASClient } from '@aiassist-secure/intelligence-signal';

const client = new AiASClient({
  apiKey: 'aai_your_api_key_here',
});

// Scan Reddit and Hacker News for buying signals
const result = await client.scan({
  sources: ['reddit', 'hackernews'],
  keywords: { include: ['CRM', 'project management'] },
  mode: 'LEAD',
  min_intent_score: 0.6,
  limit: 25,
});

for (const signal of result.data.signals) {
  console.log(`[${signal.intent.category}] ${signal.title}`);
  console.log(`  Score: ${signal.intent.score} | Source: ${signal.source}`);
  console.log(`  URL: ${signal.url}`);
}
```

## Usage Examples

### Multi-Source Scan with Campaign Context

```typescript
const result = await client.scan({
  sources: ['reddit', 'hackernews', 'devto', 'producthunt'],
  keywords: {
    include: ['workflow automation', 'no-code', 'zapier alternative'],
    exclude: ['free', 'open source'],
    subreddits: ['SaaS', 'startups', 'Entrepreneur'],
  },
  mode: 'LEAD',
  context: {
    company_name: 'FlowBot',
    campaign_intent: 'Find users frustrated with existing automation tools',
    campaign_goal: 'Generate qualified leads for enterprise plan',
  },
  min_intent_score: 0.5,
  limit: 50,
});

console.log(`Found ${result.data.scan_summary.total_returned} high-intent signals`);
console.log(`Scanned ${result.data.scan_summary.total_fetched} posts across ${result.data.scan_summary.sources_scanned.length} sources`);
```

### Real-Time Streaming Scan

```typescript
for await (const event of client.scanStream({
  sources: ['reddit', 'twitter', 'hackernews'],
  keywords: { include: ['AI agent', 'LLM framework'] },
})) {
  switch (event.type) {
    case 'scan_started':
      console.log(`Scanning ${event.data.total_sources} sources...`);
      break;
    case 'source_started':
      console.log(`  Scanning ${event.data.source}...`);
      break;
    case 'signal':
      console.log(`  Found: ${event.data.title} (score: ${event.data.intent.score})`);
      break;
    case 'source_completed':
      console.log(`  ${event.data.source}: ${event.data.signals_found} signals`);
      break;
    case 'scan_completed':
      console.log(`Done! ${event.data.total_signals} signals in ${event.data.processing_ms}ms`);
      break;
  }
}
```

### Score Your Own Content

```typescript
const result = await client.score({
  items: [
    { id: '1', text: 'Looking for a CRM that integrates with Slack and has good API docs' },
    { id: '2', text: 'Just launched my new side project for todo lists!' },
    { id: '3', text: 'We need to migrate off Salesforce ASAP, budget approved' },
  ],
  keywords: { include: ['CRM', 'Slack integration'] },
  mode: 'LEAD',
});

for (const scored of result.data.scores) {
  console.log(`${scored.id}: ${scored.category} (${scored.score}) — ${scored.reasoning}`);
}
```

### Enrich a Signal with AI Outreach

```typescript
const scanResult = await client.scan({
  sources: ['reddit'],
  keywords: { include: ['need help with analytics'] },
  min_intent_score: 0.7,
  limit: 5,
});

if (scanResult.data.signals.length > 0) {
  const topSignal = scanResult.data.signals[0];

  const enriched = await client.enrich({
    signal: topSignal,
    generate: ['outreach', 'analysis', 'lead_packet'],
    outreach_style: 'helpful',
    custom_directives: 'Focus on our free tier and migration assistance',
  });

  console.log(enriched.data.enrichment);
}
```

### List Available Sources

```typescript
const sources = await client.sources();

console.log(`${sources.data.total_sources} sources available:`);
console.log(`  Tier 1 (no config needed): ${sources.data.tier_1_count}`);
console.log(`  Tier 2 (requires API keys): ${sources.data.tier_2_count}`);

for (const source of sources.data.sources) {
  const status = source.requires_config ? '(requires config)' : '(ready)';
  console.log(`  ${source.name} ${status} — max ${source.capabilities.max_results} results`);
}
```

### Get LLM Tool Definitions

```typescript
// For OpenAI function calling
const openaiTools = await client.tools('openai');
// Pass openaiTools.data.tools to chat.completions.create()

// For MCP server integration
const mcpManifest = await client.tools('mcp');

// For LangChain
const langchainTools = await client.tools('langchain');
```

### Check Usage Stats

```typescript
const usage = await client.usage();
console.log(`Scans today: ${usage.data.scans_today}`);
console.log(`Signals cached: ${usage.data.signals_cached}`);
```

### Browse Cached Signals

```typescript
const signals = await client.signals({
  source: 'reddit',
  min_score: 0.8,
  category: 'buying',
  limit: 20,
});

console.log(`${signals.data.total} total buying signals from Reddit`);
```

## Error Handling

```typescript
import { AiASClient, AiASError } from '@aiassist-secure/intelligence-signal';

try {
  const result = await client.scan({ ... });
} catch (err) {
  if (err instanceof AiASError) {
    console.error(`API Error [${err.errorCode}]: ${err.message}`);
    console.error(`Status: ${err.statusCode}`);
    console.error(`Request ID: ${err.requestId}`);
    if (err.details) console.error('Details:', err.details);
  }
}
```

## Configuration

```typescript
const client = new AiASClient({
  apiKey: 'aai_your_key',
  baseUrl: 'https://saas-signal.com',  // default
  maxRetries: 3,                        // default, set 0 to disable
  retryBaseDelay: 500,                  // ms, default
  timeout: 60_000,                      // ms, default
});
```

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `scan(request)` | `POST /v1/scan` | Multi-source signal scan with AI scoring |
| `scanStream(request)` | `POST /v1/scan/stream` | Real-time SSE streaming scan |
| `sources()` | `GET /v1/sources` | List 22+ available signal sources |
| `signals(query?)` | `GET /v1/signals` | Browse cached signals with filters |
| `score(request)` | `POST /v1/score` | Score arbitrary text for intent |
| `enrich(request)` | `POST /v1/enrich` | AI outreach, analysis, lead packets |
| `usage()` | `GET /v1/usage` | Organization usage statistics |
| `tools(format?)` | `GET /v1/tools` | LLM tool definitions (OpenAI/MCP/LangChain) |

## 22+ Signal Sources

**Tier 1 (no configuration needed):** Reddit, Hacker News, Product Hunt, IndieHackers, Dev.to, Lobsters, Hashnode, BetaList, EchoJS, WIP, LaunchingNext, HackerNoon, Makerlog, AlternativeTo, SaaSHub, TLDR, Changelog

**Tier 2 (requires API keys):** Twitter/X, LinkedIn Jobs, LinkedIn People, Telegram, Google News, Indeed

## Intent Categories

`buying` | `evaluating` | `frustrated` | `hiring` | `building` | `asking` | `announcing` | `discussing`

## License

MIT - [AiAssist Secure](https://aiassist.net)
