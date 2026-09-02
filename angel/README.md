# Angel — Investor & Fund Finder Agent

> Find the investors already interested in what you're building.

An AI-powered Python agent that discovers angel investors, micro funds, seed funds, family offices, and operator-investors who back companies in your category. Scans the web, extracts portfolio pages, monitors social signals across Reddit, Hacker News, and Twitter, and enriches every investor with verified Twitter and LinkedIn contacts.

Built for founders raising pre-seed or seed rounds who need to find the right investors — not just any investors.

---

## What It Does

```
$ python angel.py "AI SaaS artificial intelligence" --max-funds 10

============================================================
Discovering investors & funds for: AI SaaS artificial intelligence
============================================================

  Searching: top angel investors AI SaaS artificial intelligence startups
  Searching: seed funds micro VCs investing in AI SaaS artificial intelligence
  Searching: family offices venture capital AI SaaS artificial intelligence portfolio
  ...

  Scanning signals across Reddit, Hacker News, Twitter...
  Found 22 signal(s) from intelligence scan.

  Identified 18 relevant funds/investors.

    - Ben Lang (angel investor)
    - Stella Garber (angel investor)
    - Forum Ventures (seed fund)
    - Y Combinator (venture fund)
    - Andreessen Horowitz (a16z) (venture fund)
    - Lightspeed Venture Partners (venture fund)
    - NFX (venture fund)
    - Carib Ventures, LLC (family office)
    ...

  [1/10] Looking up investors at Forum Ventures...
    Found 14 investor(s):
      - Michael Cardamone (CEO & Managing Partner)
      - Jonah Midanik (General Partner)
      - James Murphy (Managing Partner)
      ...

  [2/10] Looking up investors at Andreessen Horowitz (a16z)...
    Found 10 investor(s):
      - Martin Casado (General Partner)
      - Anjney Midha (General Partner)
      - Marc Andreessen (Co-Founder and General Partner)
      ...

============================================================
PROGRESS REPORT
============================================================
  Funds/Orgs:      10 total, 8 scanned, 2 pending
  Investors:       91 total
  With Twitter:    37
  With LinkedIn:   71
  Has any contact: 77 (84%)
  Needs enriching: 14
============================================================
```

**Real results from a single topic** — 10 funds, 91 investors, 84% with verified contact info.

---

## Example Output

### Funds & Investors Discovered

| Fund | Type | Investors Found | With Contact |
|---|---|---|---|
| Lightspeed Venture Partners | venture fund | 46 | 44 |
| Forum Ventures | seed fund | 14 | 12 |
| NFX | venture fund | 13 | 8 |
| Andreessen Horowitz (a16z) | venture fund | 10 | 8 |
| ScOp Venture Capital | venture fund | 4 | 1 |
| Y Combinator | venture fund | 2 | 2 |
| Ben Lang | angel investor | 1 | 1 |
| Stella Garber | angel investor | 1 | 1 |

### Sample Investor Contacts

| Name | Title | Fund | Twitter | LinkedIn |
|---|---|---|---|---|
| Marc Andreessen | Co-Founder, GP | a16z | — | yes |
| Ben Horowitz | Co-Founder, GP | a16z | yes | yes |
| Justine Moore | Partner | a16z | yes | yes |
| Pete Flint | General Partner | NFX | yes | yes |
| Morgan Beller | General Partner | NFX | yes | yes |
| Semil Shah | Venture Partner | Lightspeed | yes | yes |
| Michael Mignano | Partner | Lightspeed | yes | yes |
| Nnamdi Iregbulem | Partner | Lightspeed | yes | yes |
| Brad Flora | Group Partner | Y Combinator | yes | yes |
| Stella Garber | Angel / CEO, Hoop | — | yes | yes |
| Bocar Dia | Partner | Forum Ventures | yes | yes |
| Guru Chahal | Partner | Lightspeed | yes | yes |

---

## Features

- **Fund & Investor Discovery** — Searches the web for angel investors, micro funds, seed funds, family offices, syndicates, and operator-investors who back companies in your category.
- **Portfolio Analysis** — Extracts team pages, portfolio pages, and thesis statements from fund websites to identify who's making bets in your space.
- **Social Signal Scanning** — Uses the AiAS Intelligence SDK to scan Reddit, Hacker News, and Twitter for real-time investor activity and mentions.
- **Multi-Layer Enrichment** — Three enrichment strategies stacked:
  1. **Team page extraction** — Pulls Twitter/LinkedIn links directly from fund websites
  2. **Individual web search** — Searches each investor by name + fund for social profiles
  3. **Signal matching** — Cross-references social signals with investor names
- **Resumable Runs** — Saves progress after every fund and every enrichment batch. Interrupt and resume at will.
- **Enrich-Only Mode** — Already have investors? Run `--enrich-only` to fill in missing contacts without rediscovering.
- **Persistent CSVs** — Each topic gets stable CSV files that grow over time. No duplicates, no overwrites.
- **Progress Reports** — See exactly how many funds are scanned, how many investors are found, and how many still need contacts.
- **Retry with Backoff** — API calls retry on transient errors with exponential backoff.
- **Smart Deduplication** — Investors deduped by normalized name + fund. Funds deduped by name + domain.

---

## Quick Start

```bash
git clone https://github.com/youruser/angel.git
cd angel
pip install -r requirements.txt
cp .env.example .env        # Add your AiAssist.net API key
python angel.py "your investment category here"
```

### Requirements

- Python 3.10+
- `requests` and `httpx` libraries
- `aiassist-secure-intelligence` SDK (for social signal scanning)
- An [AiAssist.net](https://aiassist.net) API key (enterprise plan) with access to:
  - `/v1/chat/completions` — AI analysis (GPT-5.4 via OpenAI provider)
  - `/v1/search` — Web search
  - `/v1/web/extract` — Web page extraction
  - Intelligence API — Reddit, Hacker News, Twitter signal scanning

---

## Usage

### Full Scan

Discover funds, find investors, scan signals, enrich contacts — the full pipeline:

```bash
python angel.py "AI SaaS artificial intelligence"
```

### Limit Funds

Focus on the top N most relevant funds:

```bash
python angel.py "AI SaaS" --max-funds 10
```

### Enrich Only

Already ran a scan but want more contacts? Skip discovery entirely:

```bash
python angel.py "AI SaaS" --enrich-only
```

### Resume

Interrupted mid-run? Just run the same command again:

```bash
# Run 1 — scans 4 of 10 funds, then times out
python angel.py "AI SaaS" --max-funds 10

# Run 2 — resumes at fund 5, skips the first 4
python angel.py "AI SaaS" --max-funds 10

# Run 3 — all 10 done, enriches remaining contacts
python angel.py "AI SaaS" --max-funds 10
```

---

## Output Schema

All output is saved to the `output/` directory (gitignored). Each topic gets two persistent CSV files.

### Funds — `output/funds_<topic>.csv`

| Column | Description |
|---|---|
| `name` | Fund or investor name |
| `type` | angel investor, micro fund, seed fund, family office, syndicate, venture fund |
| `url` | Website URL |
| `thesis` | Investment thesis / focus area |
| `stage_focus` | Pre-seed, seed, Series A, growth, etc. |
| `check_size` | Typical check size if known |
| `notable_portfolio` | Notable portfolio companies in the space |
| `relevance` | Why they're relevant to your category |
| `source_url` | Where the information was found |

### Investors — `output/investors_<topic>.csv`

| Column | Description |
|---|---|
| `name` | Investor's full name |
| `title` | Role — Partner, GP, Managing Director, Angel, etc. |
| `fund` | Which fund or org they're with |
| `fund_url` | Fund's website |
| `type` | Fund type (angel, seed, venture, family office) |
| `thesis` | Personal investment focus |
| `portfolio_overlap` | Companies they've backed in your space |
| `signal_source` | Social signal matched (Reddit post, tweet, etc.) |
| `email` | Email address (if found) |
| `twitter` | Twitter/X handle |
| `linkedin` | LinkedIn profile URL |
| `source_url` | Where the investor info was found |

---

## How It Works

```
┌─────────────┐     ┌──────────────┐     ┌────────────────┐
│  Discover    │────>│   Extract    │────>│  Scan Signals  │
│              │     │              │     │                │
│ Web search   │     │ Team pages,  │     │ Intelligence   │
│ for funds,   │     │ portfolio    │     │ SDK scans      │
│ angels,      │     │ pages,       │     │ Reddit, HN,    │
│ syndicates   │     │ thesis →     │     │ Twitter for    │
│ in your      │     │ individual   │     │ investor       │
│ category     │     │ investors    │     │ activity       │
└─────────────┘     └──────────────┘     └────────────────┘
                                                │
                          ┌─────────────────────┘
                          v
              ┌────────────────────┐     ┌─────────────┐
              │  Enrich Contacts   │────>│    Save      │
              │                    │     │              │
              │ 1. Team page links │     │ Dedupe,      │
              │ 2. Individual      │     │ sanitize,    │
              │    web search      │     │ write CSV    │
              │ 3. Signal matching │     │ (incremental │
              │                    │     │  + resumable)│
              └────────────────────┘     └─────────────┘
```

1. **Discover** — Runs 5 targeted web searches across different angles (angels, micro VCs, syndicates, family offices, operators) plus social signal scanning.
2. **Extract** — For each fund, searches for partners/team members and extracts their team pages to build a verified investor list.
3. **Scan Signals** — Uses the Intelligence SDK to scan Reddit, Hacker News, and Twitter for real-time investor activity relevant to your category.
4. **Enrich** — Three-layer enrichment: team page link extraction, individual web searches for each investor, and signal matching.
5. **Save** — Results saved incrementally after every fund and every enrichment batch. Nothing is lost on interruption.

---

## File Structure

```
angel/
├── angel.py            Main entry point — the agent
├── requirements.txt    Python dependencies
├── .env.example        Template for API key setup
├── .gitignore          Excludes output/, .env, __pycache__/
├── output/             CSV output directory (gitignored)
│   ├── funds_<topic>.csv
│   └── investors_<topic>.csv
├── README.md
└── LICENSE
```

---

## Technical Details

| Detail | Value |
|---|---|
| AI Model | GPT-5.4 (via AiAssist.net OpenAI proxy) |
| Intelligence SDK | `aiassist-secure-intelligence` v1.1.1 |
| Signal Sources | Reddit, Hacker News, Twitter (22 sources available) |
| Search Depth | `advanced` (full page analysis) |
| Max Content Extraction | 15,000 characters per page |
| Enrichment Batch Size | 3 investors per individual search |
| Team Page Scan | Extracts Twitter/LinkedIn links from /team, /people, /partners pages |
| Retry Policy | 3 attempts, exponential backoff (1.5x) |
| Retryable Status Codes | 408, 409, 429, 500, 502, 503, 504 |
| Connection Pooling | `requests.Session` reused across all calls |
| Deduplication | Funds by name + domain, investors by normalized name + fund |
| Incremental Saves | After every fund scan and every enrichment batch |
| Fabrication Policy | Never — only includes details verified from web sources |

---

## Use Cases

- **Founders Raising** — Find angels and seed funds already investing in your space before you start cold outreach.
- **Startup Accelerators** — Build investor databases for your portfolio companies by category.
- **PR & Comms** — Identify investor-influencers who are active on Twitter talking about your market.
- **Fund of Funds** — Map the micro VC and angel landscape in specific verticals.
- **Market Research** — Understand who's backing what in emerging categories like AI, climate, bio, etc.

---

## Related Projects

- **[Journey](../journalist-finder/)** — Same architecture, but finds journalists and publications instead of investors. Built for getting press coverage.

---

## License

MIT — see [LICENSE](LICENSE) for details.
