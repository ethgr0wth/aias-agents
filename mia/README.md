# MIA — Market Intelligence Analyst

> Discover companies, build dossiers, surface the strongest outreach contacts — in one pass.

An AI-powered Python agent that discovers relevant companies from keywords, validates their public footprint, extracts company and team intelligence, and generates polished batch outputs including per-company PDF dossiers, combined CSV exports, and a summary index.

Built as a fork of [Angel](../angel/) — evolved from investor discovery into company intelligence and outreach preparation.

---

## What It Does

```
$ python mia.py "AI coding agents" --max-companies 10 --use-case sponsorship

  MIA — Market Intelligence Analyst
  Topic: AI coding agents
  Use case: sponsorship
  Max companies: 10
  Output: runs/ai_coding_agents/

============================================================
Phase 1: Discovering companies for: AI coding agents
============================================================

  Searching: top companies AI coding agents 2025 2026
  Searching: best AI coding agents startups companies
  Searching: leading AI coding agents platforms tools products
  ...

  Identified 18 candidate companies.

============================================================
Phase 2: Validating company identities
============================================================

  [1/18] Validating: Cursor...
    Website confirmed: https://cursor.com
    LinkedIn found: https://linkedin.com/company/cursor-ai
    X/Twitter found: https://x.com/cursor_ai
    Source coverage: 3/3 (website, linkedin, x) -> high

  [2/18] Validating: Replit...
    Website confirmed: https://replit.com
    LinkedIn found: https://linkedin.com/company/replit
    X/Twitter found: https://x.com/replit
    Source coverage: 3/3 (website, linkedin, x) -> high

  ...

  Validated 10 companies (10 total).

============================================================
  [1/10] Processing: Cursor
============================================================

  Phase 3: Extracting intelligence for Cursor...
    Extracted website content (8432 chars)
    Extracted LinkedIn page (2100 chars)

  Phase 4: Extracting team profiles for Cursor...
    Found 6 team member(s):
      - Michael Truell (CEO & Co-Founder)
      - Sualeh Asif (CTO & Co-Founder)
      ...

  Phase 5: Synthesizing analysis for Cursor...
    PDF saved: runs/ai_coding_agents/company_profiles/cursor.pdf

============================================================
PROGRESS REPORT
============================================================
  Companies:       10 total (8 strong, 2 partial)
  Profiled:        10 companies with team data
  Team members:    47 total
  With LinkedIn:   38
  With X/Twitter:  22
  Has any profile: 42
============================================================
```

---

## Features

- **Company Discovery** — Searches the web for companies matching your keywords across multiple angles (market leaders, startups, emerging players, funded companies).
- **3-Source Validation** — Every company must pass a public footprint check: official website, LinkedIn company page, and X/Twitter. Companies with fewer than 2 sources are dropped or flagged as partial.
- **Company Intelligence Extraction** — Extracts description, products, ICP, locations, hiring signals, launch signals, product velocity, ecosystem, partnerships, event/sponsor relevance, and messaging style.
- **Team Profile Extraction** — Finds founders, executives, operators, and department leads with public LinkedIn, X, GitHub profiles. Prioritizes contacts based on your use case.
- **Confidence Model** — Every conclusion is tagged as Observed (verified), Inferred (likely), or Uncertain (weak evidence).
- **Per-Company PDF Dossiers** — Polished 14-section intelligence reports with cover page, executive summary, team overview, outreach angle, confidence notes, and source appendix.
- **Best Contact Logic** — Identifies the best sponsor, sales, partnership, and technical contacts per company.
- **Use-Case Aware** — Tailors extraction and recommendations for sponsorship, partnerships, sales, or general research.
- **Social Signal Scanning** — Uses the AiAS Intelligence SDK to scan Reddit, Hacker News, and Twitter for company activity (optional).
- **Resumable Runs** — Saves progress after every company. Interrupt and resume at will.
- **Enrich-Only Mode** — Already have companies? Run `--enrich-only` to fill in missing intelligence without rediscovering.
- **Retry with Backoff** — API calls retry on transient errors with exponential backoff.
- **Smart Deduplication** — Companies deduped by normalized name. Team members deduped by name + company.

---

## Quick Start

```bash
git clone https://github.com/aiassistsecure/mia.git
cd mia
pip install -r requirements.txt
cp .env.example .env        # Add your AiAssist.net API key
python mia.py "your market keywords here"
```

### Requirements

- Python 3.10+
- `requests` library
- `fpdf2` library (for PDF generation)
- `aiassist-secure-intelligence` SDK (optional, for social signal scanning)
- An [AiAssist.net](https://aiassist.net) API key with access to:
  - `/v1/chat/completions` — AI analysis (GPT-5.4 via OpenAI provider)
  - `/v1/search` — Web search
  - `/v1/web/extract` — Web page extraction
  - Intelligence API — Reddit, Hacker News, Twitter signal scanning (optional)

---

## Usage

### Full Scan

Discover companies, validate, extract intel, build dossiers — the full pipeline:

```bash
python mia.py "AI coding agents"
```

### Use-Case Specific

Tailor outreach recommendations for a specific goal:

```bash
python mia.py "AI coding agents" --use-case sponsorship
python mia.py "developer tools" --use-case partnerships
python mia.py "enterprise SaaS" --use-case sales
```

### Limit Companies

Focus on the top N most relevant companies:

```bash
python mia.py "AI coding agents" --max-companies 5
```

### Custom Branding

Brand the PDF dossiers with your company name:

```bash
python mia.py "AI coding agents" --brand-name "Interchained LLC"
```

### Enrich Only

Already ran a scan but want to fill in missing data? Skip discovery entirely:

```bash
python mia.py "AI coding agents" --enrich-only
```

### Resume

Interrupted mid-run? Just run the same command again:

```bash
# Run 1 — profiles 4 of 10 companies, then times out
python mia.py "AI coding agents" --max-companies 10

# Run 2 — resumes at company 5, skips the first 4
python mia.py "AI coding agents" --max-companies 10
```

---

## Output Schema

All output is saved to `runs/<topic>/`. Each topic gets a persistent directory.

### Directory Structure

```
runs/ai_coding_agents/
├── companies_summary.csv          Combined company data
├── team_profiles.csv              Combined team/contact data
├── summary.json                   Quick-reference index
└── company_profiles/
    ├── cursor.pdf                 Per-company PDF dossier
    ├── replit.pdf
    ├── github_copilot.pdf
    └── ...
```

### Companies — `companies_summary.csv`

| Column | Description |
|---|---|
| `name` | Company name |
| `website` | Official website URL |
| `linkedin_url` | LinkedIn company page URL |
| `x_url` | X/Twitter company page URL |
| `category` | Industry category |
| `description` | What the company does |
| `products_services` | Main products or services |
| `icp` | Ideal customer profile |
| `locations` | Geographic locations |
| `stage` | Company stage (startup, growth, enterprise) |
| `hiring_signals` | Visible hiring activity |
| `launch_signals` | Recent launches or announcements |
| `product_velocity` | Signs of active development |
| `ecosystem` | Technology ecosystem |
| `partnerships` | Partnership references |
| `event_sponsor_relevance` | Event/sponsor participation |
| `messaging_style` | Public positioning |
| `momentum_summary` | Overall momentum assessment |
| `outreach_angle` | Recommended outreach angle |
| `confidence` | high, partial, or low |
| `source_coverage` | Source validation results (e.g., 3/3) |
| `source_urls` | Source URLs used |

### Team Profiles — `team_profiles.csv`

| Column | Description |
|---|---|
| `company_name` | Which company they're at |
| `person_name` | Full name |
| `role_title` | Role/title |
| `team_category` | founder, executive, operator, technical_lead, etc. |
| `linkedin_url` | LinkedIn profile URL |
| `x_url` | X/Twitter URL |
| `website_profile_url` | Company bio/profile URL |
| `github_url` | GitHub profile URL |
| `other_public_profile_urls` | Other profile URLs |
| `location_if_public` | Location if publicly visible |
| `bio_summary` | Brief public bio |
| `activity_status` | active, inactive, or unknown |
| `likely_decision_area` | What they decide on |
| `outreach_relevance` | Why they matter for outreach |
| `public_preferences_or_signals` | Visible preferences |
| `notable_public_posts_or_topics` | Recent public topics |
| `confidence_level` | Observed, Inferred, or Uncertain |
| `notes` | Additional context |

### Summary — `summary.json`

Quick-reference index with:
- Topic and use case
- Per-company: best sponsor/sales/partnership/technical contacts
- Strongest outreach angle per company
- Team member counts and confidence levels

### PDF Dossier (per company)

14-section intelligence report:
1. Cover page
2. Executive summary
3. Company snapshot
4. Official positioning
5. Public market voice
6. Products & services
7. Customer / ICP inference
8. Market signals
9. Team & decision-maker overview
10. Best contacts by use case
11. Outreach angle
12. Confidence notes (Observed / Inferred / Uncertain)
13. Source appendix
14. Coverage limitations (if applicable)

---

## How It Works

```
┌───────────────┐     ┌────────────────┐     ┌──────────────────┐
│  1. Discover   │────>│  2. Validate   │────>│  3. Extract      │
│                │     │                │     │     Intel         │
│ Web search     │     │ Website check  │     │                  │
│ for companies  │     │ LinkedIn check │     │ Company data,    │
│ matching       │     │ X/Twitter      │     │ products, ICP,   │
│ keywords       │     │ check          │     │ hiring, launches │
│                │     │                │     │ partnerships,    │
│ + signal scan  │     │ 3-source gate  │     │ messaging style  │
└───────────────┘     └────────────────┘     └──────────────────┘
                                                      │
                      ┌───────────────────────────────┘
                      v
         ┌──────────────────┐     ┌──────────────────┐
         │  4. Extract      │────>│  5. Synthesize   │
         │     Team         │     │                  │
         │                  │     │ Best contacts,   │
         │ Founders,        │     │ outreach angle,  │
         │ executives,      │     │ confidence tags, │
         │ operators,       │     │ observed vs      │
         │ department leads │     │ inferred vs      │
         │ + social profiles│     │ uncertain        │
         └──────────────────┘     └──────────────────┘
                                          │
                                          v
                               ┌──────────────────┐
                               │  6. Generate      │
                               │     Artifacts     │
                               │                   │
                               │ PDF dossier,      │
                               │ CSV export,       │
                               │ summary JSON      │
                               │ (incremental +    │
                               │  resumable)       │
                               └──────────────────┘
```

1. **Discover** — Runs 5 targeted web searches plus optional social signal scanning to identify candidate companies.
2. **Validate** — For each candidate, verifies 3 mandatory sources (website, LinkedIn, X). Companies with <2 sources are dropped.
3. **Extract Intel** — Extracts company-level intelligence from website, LinkedIn, X, and news using the tiered source hierarchy.
4. **Extract Team** — Finds founders, executives, and key team members with public profiles, prioritized by use case.
5. **Synthesize** — Generates outreach recommendations, identifies best contacts per use case, and tags all conclusions with confidence levels.
6. **Generate** — Creates PDF dossiers, combined CSV exports, and a summary JSON index. All saves are incremental.

---

## Source Hierarchy

| Tier | Sources | Used For |
|---|---|---|
| **Tier 1** | Official website, LinkedIn company page | Identity, positioning, business profile |
| **Tier 2** | X/Twitter, founder profiles, docs/GitHub | Tone, recency, momentum, public narrative |
| **Tier 3** | News, app directories, events, reviews | Validation, enrichment, ecosystem context |

---

## File Structure

```
mia/
├── mia.py              Main entry point — the agent
├── requirements.txt    Python dependencies
├── .env.example        Template for API key setup
├── .gitignore          Excludes runs/, .env, __pycache__/
├── runs/               Output directory (gitignored)
│   └── <topic>/
│       ├── companies_summary.csv
│       ├── team_profiles.csv
│       ├── summary.json
│       └── company_profiles/
│           ├── <company>.pdf
│           └── ...
├── README.md
└── LICENSE
```

---

## Technical Details

| Detail | Value |
|---|---|
| AI Model | GPT-5.4 (via AiAssist.net OpenAI proxy) |
| Intelligence SDK | `aiassist-secure-intelligence` v1.1.0 (optional) |
| Signal Sources | Reddit, Hacker News, Twitter (optional) |
| Search Depth | `advanced` (full page analysis) |
| Max Content Extraction | 15,000 characters per page |
| Validation Gate | 3-source (website + LinkedIn + X), minimum 2 required |
| Team Profile Limit | Up to 10 per company |
| Retry Policy | 3 attempts, exponential backoff (1.5x) |
| Retryable Status Codes | 408, 409, 429, 500, 502, 503, 504 |
| Connection Pooling | `requests.Session` reused across all calls |
| Deduplication | Companies by normalized name, team by name + company |
| Incremental Saves | After every company profiled |
| Confidence Model | Observed / Inferred / Uncertain |
| Fabrication Policy | Never — only includes details verified from public sources |
| PDF Engine | fpdf2 |

---

## Use Cases

- **Sponsorship Prospecting** — Find companies in your space, identify marketing/BD contacts, and surface the best sponsorship angle.
- **Partnership Research** — Map potential partners, their integration ecosystems, and the right person to reach.
- **Sales Intelligence** — Build target company profiles with buying signals, tech stack clues, and decision-maker contacts.
- **Competitive Landscaping** — Understand who's in the market, what they're doing, and how they position themselves.
- **Event Planning** — Identify companies active in your space for speaker invitations, sponsor pitches, or booth neighbors.

---

## Related Projects

- **[Angel](../angel/)** — The original. Finds angel investors, micro funds, and seed funds for founders raising capital.
- **[Journey](../journey/)** — Same architecture, finds journalists and publications for PR outreach.

---

## License

MIT — see [LICENSE](LICENSE) for details.

Copyright (c) 2026 Interchained LLC
