# Journey — Journalist & Publication Finder Agent

> Find the right journalists, at the right publications, with the right contact info — automatically.

An AI-powered Python agent that discovers publications covering your topic, identifies the journalists and editors who write about it, extracts their contact information (email, Twitter/X, LinkedIn), and saves everything to clean, deduplicated CSV files.

Built for founders, PR teams, and anyone who wants to get published. Point it at a topic, and it does the research for you.

# Journey

Journey is an AI agent that turns what you're building into targeted media opportunities.

It finds journalists already writing about your space — so you can pitch with relevance, not guesswork.

## Why Journey?

Builders ship.
Most never get seen.

Journey fixes distribution.

## Use cases
- SaaS launches
- Open source releases
- Product updates
- Founder stories

## Philosophy
Don't spray 1,000 emails.

Find the 10 people already writing about you.

---

## What It Does

```
$ python journey.py "AI startups SaaS" --max-pubs 10

============================================================
Searching for publications covering: AI startups SaaS
============================================================

  Identified 12 relevant publications.

    - TechCrunch (online media)
    - The Information (online media)
    - Bloomberg (news outlet)
    - The Wall Street Journal (newspaper)
    - Forbes (magazine)
    - PitchBook News (trade publication)
    ...

  [1/10] Looking up journalists at TechCrunch...
    Found 8 journalist(s):
      - Russell Brandom (AI Editor)
      - Rebecca Bellan (Senior Reporter)
      - Julie Bort (Venture Editor)
      ...

  [2/10] Looking up journalists at The Information...
    Found 10 journalist(s):
      - Amir Efrati (Co-Executive Editor)
      - Katie Roof (Deputy Bureau Chief, VC)
      ...

============================================================
Enriching contact information...
============================================================

============================================================
PROGRESS REPORT
============================================================
  Publications:    10 total, 8 scanned, 2 pending
  Journalists:     39 total
  With email:      16
  With Twitter:    10
  With LinkedIn:   5
  Has any contact: 22
  Needs enriching: 17
============================================================
```

**Real results from a single run** — 10 publications, 39 journalists, 22 with verified contact info, in under 2 minutes.

---

## Example Output

### Publications Found

| Publication | Type | Journalists Found |
|---|---|---|
| TechCrunch | online media | 8 |
| The Information | online media | 10 |
| Bloomberg | news outlet | 5 |
| Forbes | magazine | 5 |
| PitchBook News | trade publication | 4 |
| Andreessen Horowitz (a16z) | blog | 4 |
| The Wall Street Journal | newspaper | 2 |
| AI Magazine | magazine | 1 |

### Sample Contacts

| Name | Title | Publication | Contact Found |
|---|---|---|---|
| Russell Brandom | AI Editor | TechCrunch | email |
| Julie Bort | Venture Editor | TechCrunch | email, twitter |
| Amir Efrati | Co-Executive Editor | The Information | email, twitter |
| Katie Roof | Deputy Bureau Chief, VC | The Information | twitter |
| Rachel Metz | AI Reporter | Bloomberg | email, twitter |
| Alex Konrad | Senior Editor | Forbes | twitter, linkedin |
| Rosie Bradbury | Senior Reporter | PitchBook News | email, linkedin |
| Kate Clark | Reporter | The Wall Street Journal | twitter |

---

## Features

- **Publication Discovery** — Searches the web and uses AI to identify the most relevant newspapers, magazines, online media, blogs, and trade publications covering your topic.
- **Journalist Lookup** — For each publication, finds journalists, editors, reporters, and writers who cover your beat. Extracts editorial/team pages and cross-references with web search results.
- **Contact Enrichment** — Searches for email addresses, Twitter/X handles, and LinkedIn profiles. Batched in groups of 5 per publication for speed.
- **Resumable Runs** — Saves progress after every publication. If a run is interrupted, re-run the same command and it picks up exactly where it left off. No duplicate work, no wasted API calls.
- **Enrich-Only Mode** — Already have journalists but need more contact info? Run `--enrich-only` to skip discovery and just fill in missing contacts.
- **Persistent CSVs** — Each topic gets a single pair of CSV files that grow over time. New publications and journalists are appended; existing data is never overwritten.
- **Progress Reports** — See at a glance how many publications are scanned, how many journalists are found, and how many still need contact enrichment.
- **Retry with Backoff** — API calls automatically retry on transient errors (429, 5xx) with exponential backoff.
- **Smart Deduplication** — Publications deduped by name + domain, journalists by normalized name + publication. Handles punctuation, casing, and whitespace.
- **Data Sanitization** — All data is cleaned and normalized before saving. No nulls, no stray whitespace, no garbage in your CSV.

---

## Quick Start 
### (linux, windows is slightly different venv)

```bash
git clone https://github.com/aiassistsecure/journey.git
cd journey
python3 -m venv venv
source venv/bin/activate   # different on Windows depending on which shell
pip install -r requirements.txt
cp .env.example .env        # Add your AiAssist.net API key
python3 journey.py "your topic here"
```

### Requirements

- Python 3.10+
- `requests` library
- An [AiAssist.net](https://aiassist.net) API key (any plan, start free 7 days) with access to:
  - `/v1/chat/completions` — AI analysis (GPT-5.4 via OpenAI provider)
  - `/v1/search` — Web search
  - `/v1/web/extract` — Web page extraction

---

## Usage

### Full Scan

Discover publications, find journalists, enrich contacts — the full pipeline:

```bash
python journey.py "AI startups SaaS artificial intelligence"
```

### Limit Publications

Focus on the top N most relevant publications:

```bash
python journey.py "AI startups SaaS" --max-pubs 10
```

### Enrich Only

Already ran a scan but want to fill in more contacts? Skip discovery entirely:

```bash
python journey.py "AI startups SaaS" --enrich-only
```

### Resume

Interrupted mid-run? Just run the same command again. It picks up where it left off:

```bash
# Run 1 — gets through 5 of 10 publications, then times out
python journey.py "AI startups SaaS" --max-pubs 10

# Run 2 — resumes at publication 6, skips the first 5
python journey.py "AI startups SaaS" --max-pubs 10

# Run 3 — all 10 done, just enriches any remaining contacts
python journey.py "AI startups SaaS" --max-pubs 10
```

---

## Output Schema

All output is saved to the `output/` directory (gitignored). Each topic gets two persistent CSV files.

### Publications — `output/pubs_<topic>.csv`

| Column | Description |
|---|---|
| `name` | Publication name |
| `url` | Main website URL |
| `type` | newspaper, magazine, online media, blog, trade publication |
| `relevance` | Why this publication covers your topic |
| `editorial_page_url` | URL of their about/team/staff page |

### Contacts — `output/contacts_<topic>.csv`

| Column | Description |
|---|---|
| `name` | Journalist's full name |
| `title` | Role — Senior Reporter, Editor-in-Chief, Staff Writer, etc. |
| `publication` | Which publication they work at |
| `publication_url` | Publication's website |
| `beat` | Topics they cover |
| `email` | Email address (verified from web sources) |
| `twitter` | Twitter/X handle |
| `linkedin` | LinkedIn profile URL |
| `source_url` | Where the journalist info was found |

---

## How It Works

```
┌─────────────┐     ┌──────────────┐     ┌────────────────┐     ┌─────────────┐
│   Search     │────>│   Analyze    │────>│    Extract     │────>│   Enrich    │
│              │     │              │     │                │     │             │
│ Web search   │     │ GPT-5.4      │     │ Editorial      │     │ Batch web   │
│ for pubs     │     │ ranks &      │     │ pages, staff   │     │ search for  │
│ covering     │     │ identifies   │     │ directories,   │     │ email,      │
│ your topic   │     │ relevant     │     │ bylines →      │     │ Twitter,    │
│              │     │ publications │     │ journalists    │     │ LinkedIn    │
└─────────────┘     └──────────────┘     └────────────────┘     └─────────────┘
                                                                       │
                                                                       v
                                                              ┌─────────────┐
                                                              │    Save     │
                                                              │             │
                                                              │ Dedupe,     │
                                                              │ sanitize,   │
                                                              │ write CSV   │
                                                              │ (resumable) │
                                                              └─────────────┘
```

1. **Search** — Runs 3 parallel web searches with different query angles to cast a wide net.
2. **Analyze** — GPT-5.4 analyzes all search results to identify and rank the most relevant publications.
3. **Extract** — For each publication, searches for journalists by name, extracts editorial/team pages, and cross-references to build a verified list.
4. **Enrich** — For journalists missing contact info, runs batched web searches (5 per batch) and uses AI to extract verified contact details.
5. **Save** — Results are deduplicated, sanitized, and saved to CSV after each publication. Nothing is lost if the process is interrupted.

---

## File Structure

```
journey/
├── journey.py          Main entry point — the agent
├── requirements.txt    Python dependencies
├── .env.example        Template for API key setup
├── .gitignore          Excludes output/, .env, __pycache__/
├── output/             CSV output directory (gitignored)
│   ├── pubs_<topic>.csv
│   └── contacts_<topic>.csv
├── README.md
└── LICENSE             MIT
```

---

## Technical Details

| Detail | Value |
|---|---|
| AI Model | GPT-5.4 (via AiAssist.net OpenAI proxy) |
| Search Depth | `advanced` (full page analysis) |
| Max Content Extraction | 15,000 characters per page |
| Enrichment Batch Size | 5 journalists per API call |
| Retry Policy | 3 attempts, exponential backoff (1.5x) |
| Retryable Status Codes | 408, 409, 429, 500, 502, 503, 504 |
| Connection Pooling | `requests.Session` reused across all calls |
| Deduplication | Publications by name + domain, journalists by normalized name + publication |
| Data Integrity | All fields sanitized, nulls converted to empty strings, whitespace stripped |
| Fabrication Policy | Never — only includes details verified from web sources |

---

## Use Cases

- **Founders** — Find journalists who cover your space to pitch your startup story.
- **PR Teams** — Build targeted media lists for press releases and product launches.
- **Content Marketers** — Identify publications accepting guest posts or contributed articles.
- **Researchers** — Map the media landscape covering a specific industry or topic.
- **Job Seekers** — Find editors and hiring managers at publications you want to write for.

---

## License

MIT — see [LICENSE](LICENSE) for details.
