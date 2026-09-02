import os
import sys
import json
import csv
import re
import time
import requests
from dotenv import load_dotenv
from datetime import datetime
from urllib.parse import urlparse
from aias_intelligence import AiASIntelligence

BASE_URL = "https://api.aiassist.net"
load_dotenv()
API_KEY = os.environ.get("AIASSIST_API_KEY", "")

if not API_KEY:
    print("Error: AIASSIST_API_KEY environment variable is not set.")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
    "X-AiAssist-Provider": "openai",
}

MODEL = "gpt-5.4"

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

FUND_FIELDS = [
    "name", "type", "url", "thesis", "stage_focus",
    "check_size", "notable_portfolio", "relevance", "source_url",
]
INVESTOR_FIELDS = [
    "name", "title", "fund", "fund_url", "type",
    "thesis", "portfolio_overlap", "signal_source",
    "email", "twitter", "linkedin", "source_url",
]

SESSION = requests.Session()
SESSION.headers.update(HEADERS)

intel = AiASIntelligence(api_key=API_KEY)


def truncate(text, max_len=500):
    return (text or "")[:max_len].strip()


def get_domain(url):
    try:
        return urlparse(url).netloc.replace("www.", "").strip().lower()
    except Exception:
        return ""


def normalize_name(name):
    name = (name or "").strip().lower()
    name = re.sub(r"[^a-z0-9\s]", "", name)
    name = re.sub(r"\s+", " ", name)
    return name


def safe_topic_slug(topic):
    slug = re.sub(r"[^a-z0-9]+", "_", topic.lower()).strip("_")
    return slug[:40] or "topic"


def clean_fund(f):
    return {
        "name": str(f.get("name", "")).strip(),
        "type": str(f.get("type", "")).strip(),
        "url": str(f.get("url", "")).strip(),
        "thesis": str(f.get("thesis", "")).strip(),
        "stage_focus": str(f.get("stage_focus", "")).strip(),
        "check_size": str(f.get("check_size", "")).strip(),
        "notable_portfolio": str(f.get("notable_portfolio", "")).strip(),
        "relevance": str(f.get("relevance", "")).strip(),
        "source_url": str(f.get("source_url", "")).strip(),
    }


def clean_investor(inv):
    return {
        "name": str(inv.get("name", "")).strip(),
        "title": str(inv.get("title", "")).strip(),
        "fund": str(inv.get("fund", "")).strip(),
        "fund_url": str(inv.get("fund_url", "")).strip(),
        "type": str(inv.get("type", "")).strip(),
        "thesis": str(inv.get("thesis", "")).strip(),
        "portfolio_overlap": str(inv.get("portfolio_overlap", "")).strip(),
        "signal_source": str(inv.get("signal_source", "")).strip(),
        "email": str(inv.get("email") or "").strip(),
        "twitter": str(inv.get("twitter") or "").strip(),
        "linkedin": str(inv.get("linkedin") or "").strip(),
        "source_url": str(inv.get("source_url", "")).strip(),
    }


def dedupe_funds(funds):
    seen = set()
    unique = []
    for f in funds:
        f = clean_fund(f)
        key = (f["name"].lower(), get_domain(f["url"]))
        if key not in seen:
            seen.add(key)
            unique.append(f)
    return unique


def dedupe_investors(investors):
    seen = set()
    unique = []
    for inv in investors:
        inv = clean_investor(inv)
        key = (normalize_name(inv["name"]), inv["fund"].lower())
        if key not in seen:
            seen.add(key)
            unique.append(inv)
    return unique


def format_search_context(results, max_items=20, max_content_len=500):
    lines = []
    for r in results[:max_items]:
        title = truncate(r.get("title", ""), 150)
        url = r.get("url", "")
        content = truncate(r.get("content", ""), max_content_len)
        lines.append(f"- {title} ({url}): {content}")
    return "\n".join(lines)


def format_signal_context(results, max_items=15):
    lines = []
    for r in results[:max_items]:
        title = truncate(r.get("title", ""), 150)
        body = truncate(r.get("body", "") or r.get("content", ""), 300)
        author = r.get("author", "unknown")
        source = r.get("source", "")
        lines.append(f"- [{source}] @{author}: {title} — {body}")
    return "\n".join(lines)


def post_json(endpoint, payload, timeout=30, retries=3, backoff=1.5):
    url = f"{BASE_URL}{endpoint}"
    last_exc = None
    for attempt in range(1, retries + 1):
        try:
            r = SESSION.post(url, json=payload, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.HTTPError as e:
            last_exc = e
            resp = getattr(e, "response", None)
            status = resp.status_code if resp is not None else "unknown"
            body = resp.text[:500] if resp is not None else "no response body"
            print(f"  HTTP error ({status}) on {endpoint}: {body}")
            if resp is not None and resp.status_code not in (408, 409, 429, 500, 502, 503, 504):
                break
        except Exception as e:
            last_exc = e
            print(f"  Request error on {endpoint}: {e}")
        if attempt < retries:
            sleep_for = backoff ** attempt
            print(f"  Retrying in {sleep_for:.1f}s... ({attempt}/{retries})")
            time.sleep(sleep_for)
    raise last_exc


def web_search(query, max_results=10):
    try:
        data = post_json(
            "/v1/search",
            {"query": query, "search_depth": "advanced", "max_results": max_results},
            timeout=30,
        )
        if not data.get("success"):
            print(f"  Search warning: {data.get('error', 'unknown error')}")
            return []
        return data.get("results", [])
    except Exception as e:
        print(f"  Search failed for '{query}': {e}")
        return []


def extract_url(url):
    try:
        data = post_json(
            "/v1/web/extract",
            {"url": url, "extract_links": True, "max_content_length": 15000},
            timeout=30,
        )
        if data.get("success"):
            return data.get("content", "")
    except Exception as e:
        print(f"  Extract error for {url}: {e}")
    return ""


def chat(messages):
    try:
        data = post_json(
            "/v1/chat/completions",
            {"model": MODEL, "messages": messages, "max_tokens": 8192},
            timeout=120,
        )
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"    Chat error: {e}")
        return "[]"


def parse_json_response(response):
    response = (response or "").strip()
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass
    if response.startswith("```"):
        lines = response.splitlines()
        if lines:
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        stripped = "\n".join(lines).strip()
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            response = stripped
    start = response.find("[")
    end = response.rfind("]")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(response[start:end + 1])
        except json.JSONDecodeError:
            pass
    start = response.find("{")
    end = response.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(response[start:end + 1])
        except json.JSONDecodeError:
            pass
    raise json.JSONDecodeError("Could not extract JSON", response, 0)


def scan_signals(keywords, sources_list=None):
    if sources_list is None:
        sources_list = ["reddit", "hackernews", "twitter"]
    try:
        subreddits = None
        if "reddit" in sources_list:
            subreddits = ["startups", "venturecapital", "SaaS", "Entrepreneur", "algotrading", "artificial"]

        data = intel.scan(
            sources=sources_list,
            keywords=keywords,
            limit=25,
            category="recent",
            subreddits=subreddits,
        )
        results = data.get("data", {}).get("results", [])
        return results
    except Exception as e:
        print(f"  Intelligence scan error: {e}")
        return []


def get_csv_paths(topic):
    slug = safe_topic_slug(topic)
    fund_path = os.path.join(OUTPUT_DIR, f"funds_{slug}.csv")
    inv_path = os.path.join(OUTPUT_DIR, f"investors_{slug}.csv")
    return fund_path, inv_path


def load_csv(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_csv(filepath, rows, fieldnames):
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def progress_report(fund_path, inv_path):
    funds = load_csv(fund_path)
    investors = load_csv(inv_path)

    total_inv = len(investors)
    with_email = sum(1 for i in investors if i.get("email"))
    with_twitter = sum(1 for i in investors if i.get("twitter"))
    with_linkedin = sum(1 for i in investors if i.get("linkedin"))
    with_any = sum(1 for i in investors if i.get("email") or i.get("twitter") or i.get("linkedin"))
    needs_enrich = total_inv - with_any

    scanned_funds = set(i.get("fund", "") for i in investors)
    funds_pending = len(funds) - len(scanned_funds)

    print(f"\n{'='*60}")
    print(f"PROGRESS REPORT")
    print(f"{'='*60}")
    print(f"  Funds/Orgs:      {len(funds)} total, {len(scanned_funds)} scanned, {funds_pending} pending")
    print(f"  Investors:       {total_inv} total")
    print(f"  With email:      {with_email}")
    print(f"  With Twitter:    {with_twitter}")
    print(f"  With LinkedIn:   {with_linkedin}")
    print(f"  Has any contact: {with_any}")
    print(f"  Needs enriching: {needs_enrich}")
    print(f"{'='*60}\n")


def discover_funds(topic):
    print(f"\n{'='*60}")
    print(f"Discovering investors & funds for: {topic}")
    print(f"{'='*60}\n")

    search_queries = [
        f"top angel investors {topic} startups",
        f"seed funds micro VCs investing in {topic}",
        f"family offices venture capital {topic} portfolio",
        f"best investors backing {topic} companies 2025 2026",
        f"syndicates angel groups {topic} early stage",
    ]

    all_results = []
    for query in search_queries:
        print(f"  Searching: {query}")
        all_results.extend(web_search(query))
        time.sleep(0.5)

    print(f"\n  Scanning signals across Reddit, Hacker News, Twitter...")
    signal_keywords = topic.split()[:5]
    signal_keywords.extend(["investor", "funding", "seed", "angel"])
    signals = scan_signals(signal_keywords)
    signal_context = ""
    if signals:
        print(f"  Found {len(signals)} signal(s) from intelligence scan.")
        signal_context = format_signal_context(signals)
    else:
        print(f"  No signals found (continuing with web search results).")

    search_context = format_search_context(all_results)
    print(f"\n  Found {len(all_results)} search results. Analyzing with AI...\n")

    prompt = f"""Based on the following search results and social signals about "{topic}", identify investors, funds, syndicates, and angel groups that actively invest in this space.

Include these types:
- Angel investors (individuals investing their own money)
- Micro funds / micro VCs ($1M-$50M fund size)
- Seed-stage venture funds
- Family offices known to invest in this space
- Operator-investors (founders/execs who also angel invest in this niche)
- Syndicates and angel groups

Search results:
{search_context}

{"Social signals (Reddit, HN, Twitter):" + chr(10) + signal_context if signal_context else "No social signals available."}

Return a JSON array of funds/investors. Each should have:
- "name": fund or investor name
- "type": "angel investor", "micro fund", "seed fund", "family office", "syndicate", "operator-investor", or "venture fund"
- "url": website URL if known
- "thesis": their investment thesis or focus area (1-2 sentences)
- "stage_focus": what stage they invest at (pre-seed, seed, Series A, etc.)
- "check_size": typical check size if known, otherwise null
- "notable_portfolio": 2-3 notable portfolio companies if known
- "relevance": why they're relevant to "{topic}" (1 sentence)
- "source_url": URL where you found this information

Return ONLY the JSON array, no other text. Include 15-25 most relevant results. Do NOT make up information."""

    response = chat([
        {"role": "system", "content": "You are a venture capital research analyst. You help find investors, funds, and angels relevant to specific sectors. Always respond with valid JSON. Never fabricate information."},
        {"role": "user", "content": prompt},
    ])

    try:
        funds = parse_json_response(response)
    except json.JSONDecodeError:
        retry_response = chat([
            {"role": "system", "content": "You must respond with ONLY a valid JSON array. No markdown, no explanation."},
            {"role": "user", "content": f"Convert this into a valid JSON array of investors/funds:\n\n{response}"},
        ])
        try:
            funds = parse_json_response(retry_response)
        except json.JSONDecodeError:
            print("  Error: Could not parse funds. Using empty list.")
            funds = []

    if not isinstance(funds, list):
        funds = []

    funds = dedupe_funds(funds)

    print(f"  Identified {len(funds)} relevant funds/investors.\n")
    for f in funds:
        print(f"    - {f.get('name', 'Unknown')} ({f.get('type', 'N/A')})")

    return funds


def find_investors_at_fund(fund, topic):
    fund_name = fund.get("name", "Unknown")
    fund_url = fund.get("url", "")
    fund_type = fund.get("type", "")

    print(f"\n  Looking up investors at {fund_name}...")

    search_queries = [
        f"{fund_name} partners investors team {topic}",
        f"{fund_name} portfolio {topic} investments",
        f"{fund_name} angel investor partner managing director",
    ]

    all_results = []
    for query in search_queries:
        all_results.extend(web_search(query, max_results=5))
        time.sleep(0.3)

    page_content = ""
    if fund_url:
        for suffix in ["/team", "/about", "/people", "/partners", "/portfolio", ""]:
            test_url = fund_url.rstrip("/") + suffix
            content = extract_url(test_url)
            if content and len(content) > 200:
                page_content = content
                print(f"    Extracted: {test_url}")
                break
            time.sleep(0.3)

    search_context = format_search_context(all_results, max_items=15, max_content_len=400)
    page_content_trimmed = truncate(page_content, 6000)

    prompt = f"""I'm researching investors at "{fund_name}" ({fund_url}) — a {fund_type} that invests in "{topic}".

Search results:
{search_context}

{"Website content:" + chr(10) + page_content_trimmed if page_content_trimmed else "No website content available."}

Find the individual investors, partners, principals, and operators at this fund/group who make investment decisions, especially those focused on or interested in "{topic}".

Return a JSON array of investor objects. Each should have:
- "name": full name
- "title": their role (Partner, Managing Director, Angel Investor, Operator, etc.)
- "thesis": their personal investment focus if different from the fund's
- "portfolio_overlap": any portfolio companies relevant to "{topic}" they've backed
- "email": email if found, otherwise null
- "twitter": Twitter/X handle if found, otherwise null
- "linkedin": LinkedIn URL if found, otherwise null
- "source_url": URL where you found info about them

Return ONLY the JSON array. If this is a solo angel investor, return them as a single-element array. Do NOT make up information."""

    response = chat([
        {"role": "system", "content": "You are a venture capital research analyst. Find real investors and their details. Never fabricate information. If you cannot verify a detail, set it to null. Always respond with valid JSON."},
        {"role": "user", "content": prompt},
    ])

    try:
        investors = parse_json_response(response)
    except json.JSONDecodeError:
        investors = []

    if not isinstance(investors, list):
        investors = []

    cleaned = []
    for inv in investors:
        if not isinstance(inv, dict):
            continue
        inv["fund"] = fund_name
        inv["fund_url"] = fund_url
        inv["type"] = fund_type
        cleaned.append(clean_investor(inv))

    cleaned = dedupe_investors(cleaned)

    if cleaned:
        print(f"    Found {len(cleaned)} investor(s):")
        for inv in cleaned:
            print(f"      - {inv.get('name', 'Unknown')} ({inv.get('title', 'N/A')})")
    else:
        print(f"    No individual investors found.")

    return cleaned


def enrich_with_signals(investors, topic):
    names = [i.get("name", "") for i in investors if i.get("name") and not i.get("signal_source")]
    if not names:
        return investors

    print(f"\n  Scanning social signals for {len(names)} investor(s)...")

    name_keywords = []
    for n in names[:10]:
        parts = n.split()
        if len(parts) >= 2:
            name_keywords.append(parts[-1])

    scan_keywords = list(set(name_keywords + topic.split()[:3]))

    signals = scan_signals(scan_keywords, sources_list=["reddit", "hackernews", "twitter"])

    if not signals:
        print(f"    No social signals found.")
        return investors

    print(f"    Found {len(signals)} signal(s). Matching to investors...")

    signal_text = format_signal_context(signals, max_items=20)

    investor_names = ", ".join(names[:15])
    prompt = f"""I have a list of investors and social media signals. Match any signals to the investors.

Investors: {investor_names}

Signals:
{signal_text}

For each investor that has a matching signal, return a JSON object with:
- "name": the investor's name
- "signal_source": brief description of the signal (e.g., "Reddit post about AI investing", "Tweet about seed-stage SaaS")
- "twitter": their Twitter handle if visible in the signal, otherwise null

Return a JSON array. Only include investors with matching signals. Return empty array [] if no matches."""

    response = chat([
        {"role": "system", "content": "Match social signals to investors. Never fabricate connections. Respond with valid JSON only."},
        {"role": "user", "content": prompt},
    ])

    try:
        matches = parse_json_response(response)
        if isinstance(matches, dict):
            matches = [matches]
        if isinstance(matches, list):
            match_map = {}
            for m in matches:
                if isinstance(m, dict) and m.get("name"):
                    match_map[normalize_name(m["name"])] = m
            for inv in investors:
                key = normalize_name(inv.get("name", ""))
                m = match_map.get(key)
                if m:
                    if m.get("signal_source"):
                        inv["signal_source"] = str(m["signal_source"]).strip()
                    if m.get("twitter") and not inv.get("twitter"):
                        inv["twitter"] = str(m["twitter"]).strip()
    except (json.JSONDecodeError, TypeError):
        pass

    return investors


def enrich_from_team_page(investors, fund_name, fund_url):
    if not fund_url:
        return investors

    for suffix in ["/team", "/people", "/partners", "/about"]:
        url = fund_url.rstrip("/") + suffix
        content = extract_url(url)
        if content and len(content) > 500:
            print(f"    Scanning team page for contact links: {url}")

            prompt = f"""From this team page content for {fund_name}, extract Twitter/X handles and LinkedIn URLs for each person listed.

Page content:
{truncate(content, 8000)}

Known team members: {', '.join(i.get('name','') for i in investors if i.get('name'))}

Return a JSON array of objects. Each object should have:
- "name": person's name
- "twitter": their Twitter/X handle if found on the page, null otherwise
- "linkedin": their LinkedIn URL if found on the page, null otherwise

Return ONLY the JSON array. Only include people whose links you can see in the page content."""

            response = chat([
                {"role": "system", "content": "Extract social links from team pages. Only include links actually present in the content. Respond with valid JSON only."},
                {"role": "user", "content": prompt},
            ])

            try:
                contacts = parse_json_response(response)
                if isinstance(contacts, dict):
                    contacts = [contacts]
                if isinstance(contacts, list):
                    contact_map = {}
                    for c in contacts:
                        if isinstance(c, dict) and c.get("name"):
                            contact_map[normalize_name(c["name"])] = c
                    matched = 0
                    for inv in investors:
                        key = normalize_name(inv.get("name", ""))
                        c = contact_map.get(key)
                        if not c:
                            continue
                        if c.get("twitter") and not inv.get("twitter"):
                            inv["twitter"] = str(c["twitter"]).strip()
                            matched += 1
                        if c.get("linkedin") and not inv.get("linkedin"):
                            inv["linkedin"] = str(c["linkedin"]).strip()
                            matched += 1
                    if matched:
                        print(f"    Extracted {matched} contact link(s) from team page.")
            except (json.JSONDecodeError, TypeError):
                pass
            break
        time.sleep(0.3)

    return investors


def enrich_contacts_individual(investors, topic, save_path=None):
    needs_enrichment = [
        i for i in investors
        if not (i.get("twitter") or i.get("linkedin"))
    ]
    if not needs_enrichment:
        print("  All investors already have contact info.")
        return investors

    print(f"    {len(needs_enrichment)} investor(s) need contact enrichment.")

    batch_size = 3
    for i in range(0, len(needs_enrichment), batch_size):
        batch = needs_enrichment[i:i + batch_size]
        all_search_results = []

        for inv in batch:
            name = inv.get("name", "")
            fund = inv.get("fund", "")
            if not name:
                continue
            query = f'"{name}" {fund} investor twitter linkedin'
            results = web_search(query, max_results=5)
            for r in results:
                r["_target_name"] = name
            all_search_results.extend(results)
            time.sleep(0.2)

        if not all_search_results:
            continue

        names_str = ", ".join(inv.get("name", "") for inv in batch)
        context = format_search_context(all_search_results, max_items=15, max_content_len=300)
        print(f"    Enriching: {names_str}")

        prompt = f"""Find Twitter/X handles and LinkedIn URLs for these investors:

{chr(10).join(f'- {inv.get("name","")} ({inv.get("fund","")}, {inv.get("title","")})' for inv in batch)}

Search results:
{context}

Return a JSON array with one object per investor:
- "name": investor name
- "twitter": Twitter/X handle (e.g., @handle) if found, null otherwise
- "linkedin": LinkedIn profile URL if found, null otherwise
- "email": email if found, null otherwise

Return ONLY the JSON array. Do NOT fabricate — only include what you find in the search results."""

        response = chat([
            {"role": "system", "content": "Extract real contact info from search results. Never fabricate. Respond with valid JSON only."},
            {"role": "user", "content": prompt},
        ])

        try:
            contacts = parse_json_response(response)
            if isinstance(contacts, dict):
                contacts = [contacts]
            if isinstance(contacts, list):
                contact_map = {}
                for c in contacts:
                    if isinstance(c, dict) and c.get("name"):
                        contact_map[normalize_name(c["name"])] = c
                for inv in batch:
                    key = normalize_name(inv.get("name", ""))
                    c = contact_map.get(key)
                    if not c:
                        continue
                    if c.get("email") and not inv.get("email"):
                        inv["email"] = str(c["email"]).strip()
                    if c.get("twitter") and not inv.get("twitter"):
                        inv["twitter"] = str(c["twitter"]).strip()
                    if c.get("linkedin") and not inv.get("linkedin"):
                        inv["linkedin"] = str(c["linkedin"]).strip()
        except (json.JSONDecodeError, IndexError, KeyError, TypeError):
            pass

        if save_path:
            save_csv(save_path, investors, INVESTOR_FIELDS)

        time.sleep(0.3)

    return dedupe_investors(investors)


def enrich_contacts(investors, topic, save_path=None):
    by_fund = {}
    for inv in investors:
        fund = inv.get("fund", "Unknown")
        by_fund.setdefault(fund, []).append(inv)

    for fund_name, group in by_fund.items():
        needs = [i for i in group if not (i.get("twitter") or i.get("linkedin"))]
        if not needs:
            continue

        fund_url = group[0].get("fund_url", "") if group else ""
        if fund_url and len(needs) >= 3:
            print(f"\n  Enriching {fund_name} ({len(needs)} need contacts)...")
            enrich_from_team_page(group, fund_name, fund_url)
            if save_path:
                save_csv(save_path, investors, INVESTOR_FIELDS)

    still_need = [i for i in investors if not (i.get("twitter") or i.get("linkedin"))]
    if still_need:
        print(f"\n  Individual enrichment for {len(still_need)} remaining investor(s)...")
        investors = enrich_contacts_individual(investors, topic, save_path=save_path)

    return investors


def run(topic, max_funds=None, enrich_only=False):
    start_time = time.time()
    fund_path, inv_path = get_csv_paths(topic)

    existing_funds = load_csv(fund_path)
    existing_investors = load_csv(inv_path)

    existing_fund_keys = set(
        (f.get("name", "").lower(), get_domain(f.get("url", "")))
        for f in existing_funds
    )
    existing_investor_keys = set(
        (normalize_name(i.get("name", "")), i.get("fund", "").lower())
        for i in existing_investors
    )
    scanned_funds = set(i.get("fund", "").lower() for i in existing_investors)

    if existing_funds or existing_investors:
        print(f"\n  Resuming from existing data:")
        print(f"    {len(existing_funds)} funds/orgs on file")
        print(f"    {len(existing_investors)} investors on file")
        print(f"    {len(scanned_funds)} funds already scanned")
        progress_report(fund_path, inv_path)

    if enrich_only:
        print(f"\n{'='*60}")
        print(f"ENRICH-ONLY MODE")
        print(f"{'='*60}")
        if not existing_investors:
            print("  No investors to enrich. Run a full scan first.")
            return fund_path, inv_path
        existing_investors = enrich_with_signals(existing_investors, topic)
        save_csv(inv_path, existing_investors, INVESTOR_FIELDS)
        existing_investors = enrich_contacts(existing_investors, topic, save_path=inv_path)
        save_csv(inv_path, existing_investors, INVESTOR_FIELDS)
        print(f"\n  Updated: {inv_path}")
        progress_report(fund_path, inv_path)
        elapsed = time.time() - start_time
        print(f"  Time elapsed: {elapsed:.1f}s\n")
        return fund_path, inv_path

    if not existing_funds:
        funds = discover_funds(topic)
    else:
        print(f"\n  Using {len(existing_funds)} existing funds. Searching for new ones...")
        new_funds = discover_funds(topic)
        added = 0
        for f in new_funds:
            f = clean_fund(f)
            key = (f["name"].lower(), get_domain(f["url"]))
            if key not in existing_fund_keys:
                existing_funds.append(f)
                existing_fund_keys.add(key)
                added += 1
        if added:
            print(f"  Added {added} new funds/orgs.")
        else:
            print(f"  No new funds found.")
        funds = existing_funds

    funds = dedupe_funds(funds)

    if max_funds and len(funds) > max_funds:
        print(f"\n  Limiting to top {max_funds} funds (of {len(funds)} found).")
        funds = funds[:max_funds]

    save_csv(fund_path, funds, FUND_FIELDS)
    print(f"\n  Funds saved to: {fund_path}")

    funds_to_scan = [f for f in funds if f.get("name", "").lower() not in scanned_funds]

    if not funds_to_scan:
        print(f"\n  All {len(funds)} funds already scanned. Skipping investor lookup.")
    else:
        print(f"\n  {len(funds_to_scan)} funds to scan ({len(funds) - len(funds_to_scan)} already done).")

    all_investors = list(existing_investors)

    for i, fund in enumerate(funds_to_scan, 1):
        print(f"\n  [{i}/{len(funds_to_scan)}]", end="")
        investors = find_investors_at_fund(fund, topic)

        new_count = 0
        for inv in investors:
            key = (normalize_name(inv.get("name", "")), inv.get("fund", "").lower())
            if key not in existing_investor_keys:
                all_investors.append(inv)
                existing_investor_keys.add(key)
                new_count += 1

        if new_count:
            print(f"    Added {new_count} new investor(s).")

        save_csv(inv_path, all_investors, INVESTOR_FIELDS)
        time.sleep(0.5)

    print(f"\n{'='*60}")
    print(f"Scanning social signals...")
    print(f"{'='*60}")
    all_investors = enrich_with_signals(all_investors, topic)

    print(f"\n{'='*60}")
    print(f"Enriching contact information...")
    print(f"{'='*60}")
    all_investors = enrich_contacts(all_investors, topic, save_path=inv_path)

    save_csv(inv_path, all_investors, INVESTOR_FIELDS)

    elapsed = time.time() - start_time
    progress_report(fund_path, inv_path)
    print(f"  Time elapsed: {elapsed:.1f}s")
    print(f"\n  Output files:")
    print(f"    - {fund_path}")
    print(f"    - {inv_path}")
    print(f"{'='*60}\n")

    return fund_path, inv_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Find investors, funds, and angels backing a given category (resumable)")
    parser.add_argument("topic", nargs="+", help="The investment category to research")
    parser.add_argument("--max-funds", type=int, default=None, help="Max number of funds to scan")
    parser.add_argument("--enrich-only", action="store_true", help="Only enrich existing contacts, skip discovery")
    args = parser.parse_args()

    topic = " ".join(args.topic)
    run(topic, max_funds=args.max_funds, enrich_only=args.enrich_only)
