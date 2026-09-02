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

try:
    from aias_intelligence import AiASIntelligence
    HAS_INTEL = True
except ImportError:
    HAS_INTEL = False

try:
    from fpdf import FPDF
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

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

SESSION = requests.Session()
SESSION.headers.update(HEADERS)

intel = AiASIntelligence(api_key=API_KEY) if HAS_INTEL else None

COMPANY_FIELDS = [
    "name", "website", "linkedin_url", "x_url", "category", "description",
    "products_services", "icp", "locations", "stage", "hiring_signals",
    "launch_signals", "product_velocity", "ecosystem", "partnerships",
    "event_sponsor_relevance", "messaging_style", "momentum_summary",
    "outreach_angle", "confidence", "source_coverage", "source_urls",
]

TEAM_FIELDS = [
    "company_name", "person_name", "role_title", "team_category",
    "linkedin_url", "x_url", "website_profile_url", "github_url",
    "other_public_profile_urls", "location_if_public", "bio_summary",
    "activity_status", "likely_decision_area", "outreach_relevance",
    "public_preferences_or_signals", "notable_public_posts_or_topics",
    "confidence_level", "notes",
]

USE_CASES = ["sponsorship", "partnerships", "sales", "general"]


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


def company_slug(name):
    slug = re.sub(r"[^a-z0-9]+", "_", (name or "").lower()).strip("_")
    return slug[:50] or "company"


def clean_company(c):
    out = {}
    for f in COMPANY_FIELDS:
        val = c.get(f)
        if isinstance(val, list):
            out[f] = "; ".join(str(v) for v in val)
        else:
            out[f] = str(val or "").strip()
    return out


def clean_team_member(m):
    out = {}
    for f in TEAM_FIELDS:
        val = m.get(f)
        if isinstance(val, list):
            out[f] = "; ".join(str(v) for v in val)
        else:
            out[f] = str(val or "").strip()
    return out


def dedupe_companies(companies):
    seen = set()
    unique = []
    for c in companies:
        c = clean_company(c)
        key = normalize_name(c["name"])
        if key and key not in seen:
            seen.add(key)
            unique.append(c)
    return unique


def dedupe_team(members):
    seen = set()
    unique = []
    for m in members:
        m = clean_team_member(m)
        key = (normalize_name(m["person_name"]), normalize_name(m["company_name"]))
        if key[0] and key not in seen:
            seen.add(key)
            unique.append(m)
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
        lines.append(f"- [{source}] @{author}: {title} -- {body}")
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


def chat(messages, max_tokens=8192):
    try:
        data = post_json(
            "/v1/chat/completions",
            {"model": MODEL, "messages": messages, "max_tokens": max_tokens},
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
    if not intel:
        return []
    if sources_list is None:
        sources_list = ["reddit", "hackernews", "twitter"]
    try:
        subreddits = None
        if "reddit" in sources_list:
            subreddits = ["startups", "SaaS", "Entrepreneur", "technology", "business"]
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


def load_csv(filepath):
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_csv(filepath, rows, fieldnames):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def save_json(filepath, data):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_run_dir(topic, output_dir=None):
    base = output_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), "runs")
    slug = safe_topic_slug(topic)
    run_dir = os.path.join(base, slug)
    os.makedirs(run_dir, exist_ok=True)
    os.makedirs(os.path.join(run_dir, "company_profiles"), exist_ok=True)
    return run_dir


def get_paths(run_dir):
    return {
        "companies_csv": os.path.join(run_dir, "companies_summary.csv"),
        "team_csv": os.path.join(run_dir, "team_profiles.csv"),
        "summary_json": os.path.join(run_dir, "summary.json"),
        "profiles_dir": os.path.join(run_dir, "company_profiles"),
    }


def progress_report(paths):
    companies = load_csv(paths["companies_csv"])
    team = load_csv(paths["team_csv"])

    total_c = len(companies)
    strong = sum(1 for c in companies if c.get("confidence") != "low")
    partial = total_c - strong
    total_t = len(team)
    with_linkedin = sum(1 for t in team if t.get("linkedin_url"))
    with_x = sum(1 for t in team if t.get("x_url"))
    with_any = sum(1 for t in team if t.get("linkedin_url") or t.get("x_url") or t.get("github_url"))

    profiled_companies = set(t.get("company_name", "") for t in team)

    print(f"\n{'='*60}")
    print(f"PROGRESS REPORT")
    print(f"{'='*60}")
    print(f"  Companies:       {total_c} total ({strong} strong, {partial} partial)")
    print(f"  Profiled:        {len(profiled_companies)} companies with team data")
    print(f"  Team members:    {total_t} total")
    print(f"  With LinkedIn:   {with_linkedin}")
    print(f"  With X/Twitter:  {with_x}")
    print(f"  Has any profile: {with_any}")
    print(f"{'='*60}\n")


def discover_companies(topic, max_companies):
    print(f"\n{'='*60}")
    print(f"Phase 1: Discovering companies for: {topic}")
    print(f"{'='*60}\n")

    search_queries = [
        f"top companies {topic} 2025 2026",
        f"best {topic} startups companies",
        f"leading {topic} platforms tools products",
        f"{topic} companies funding growth",
        f"emerging {topic} companies market leaders",
    ]

    all_results = []
    for query in search_queries:
        print(f"  Searching: {query}")
        all_results.extend(web_search(query))
        time.sleep(0.5)

    signal_context = ""
    if intel:
        print(f"\n  Scanning signals across Reddit, Hacker News, Twitter...")
        signal_keywords = topic.split()[:5]
        signal_keywords.extend(["company", "startup", "product", "launch"])
        signals = scan_signals(signal_keywords)
        if signals:
            print(f"  Found {len(signals)} signal(s) from intelligence scan.")
            signal_context = format_signal_context(signals)
        else:
            print(f"  No signals found (continuing with web search results).")

    search_context = format_search_context(all_results)
    print(f"\n  Found {len(all_results)} search results. Analyzing with AI...\n")

    prompt = f"""Based on the following search results and signals about "{topic}", identify the most relevant companies operating in this space.

Include diverse company types:
- Established market leaders
- High-growth startups
- Emerging players with recent launches or funding
- Tools/platforms serving this market
- Companies with strong public presence (website, LinkedIn, X/Twitter)

Search results:
{search_context}

{"Social signals (Reddit, HN, Twitter):" + chr(10) + signal_context if signal_context else "No social signals available."}

Return a JSON array of {max_companies * 2} candidate companies. Each should have:
- "name": company name
- "website": likely website URL
- "relevance": why this company is relevant to "{topic}" (1 sentence)
- "category": industry category or sub-sector
- "source_snippets": 1-2 key facts from search results

Return ONLY the JSON array, no other text. Do NOT make up companies -- only include those visible in the search results."""

    response = chat([
        {"role": "system", "content": "You are a market research analyst. Identify real companies from search results. Always respond with valid JSON. Never fabricate companies or details."},
        {"role": "user", "content": prompt},
    ])

    try:
        candidates = parse_json_response(response)
    except json.JSONDecodeError:
        retry_response = chat([
            {"role": "system", "content": "You must respond with ONLY a valid JSON array. No markdown, no explanation."},
            {"role": "user", "content": f"Convert this into a valid JSON array of companies:\n\n{response}"},
        ])
        try:
            candidates = parse_json_response(retry_response)
        except json.JSONDecodeError:
            print("  Error: Could not parse companies. Using empty list.")
            candidates = []

    if not isinstance(candidates, list):
        candidates = []

    seen_names = set()
    unique = []
    for c in candidates:
        if not isinstance(c, dict):
            continue
        name = normalize_name(c.get("name", ""))
        if name and name not in seen_names:
            seen_names.add(name)
            unique.append(c)

    print(f"  Identified {len(unique)} candidate companies.\n")
    for c in unique[:max_companies * 2]:
        print(f"    - {c.get('name', 'Unknown')}")

    return unique


def validate_company(candidate, topic):
    name = candidate.get("name", "Unknown")
    likely_website = candidate.get("website", "")

    print(f"\n  Validating: {name}...")

    website = ""
    linkedin_url = ""
    x_url = ""
    sources_found = []

    if likely_website:
        content = extract_url(likely_website)
        if content and len(content) > 100:
            website = likely_website
            sources_found.append("website")
            print(f"    Website confirmed: {website}")
        time.sleep(0.3)

    if not website:
        results = web_search(f"{name} official website", max_results=3)
        for r in results:
            url = r.get("url", "")
            if url and "linkedin" not in url and "twitter" not in url and "x.com" not in url:
                content = extract_url(url)
                if content and len(content) > 100:
                    website = url
                    sources_found.append("website")
                    print(f"    Website found: {website}")
                    break
                time.sleep(0.3)

    search_results = web_search(f"{name} LinkedIn company page", max_results=5)
    for r in search_results:
        url = r.get("url", "")
        if "linkedin.com/company" in url.lower():
            linkedin_url = url
            sources_found.append("linkedin")
            print(f"    LinkedIn found: {linkedin_url}")
            break
    time.sleep(0.3)

    search_results = web_search(f"{name} X Twitter company official", max_results=5)
    for r in search_results:
        url = r.get("url", "")
        if "x.com/" in url.lower() or "twitter.com/" in url.lower():
            x_url = url
            sources_found.append("x")
            print(f"    X/Twitter found: {x_url}")
            break
    time.sleep(0.3)

    coverage = len(sources_found)
    if coverage == 3:
        confidence = "high"
    elif coverage == 2:
        confidence = "partial"
    else:
        confidence = "low"

    print(f"    Source coverage: {coverage}/3 ({', '.join(sources_found) if sources_found else 'none'}) -> {confidence}")

    all_source_urls = [u for u in [website, linkedin_url, x_url] if u]

    return {
        "name": name,
        "website": website,
        "linkedin_url": linkedin_url,
        "x_url": x_url,
        "source_coverage": f"{coverage}/3: {', '.join(sources_found) if sources_found else 'none'}",
        "confidence": confidence,
        "relevance": candidate.get("relevance", ""),
        "category": candidate.get("category", ""),
        "source_urls": "; ".join(all_source_urls),
    }


def extract_company_intel(company, topic, use_case):
    name = company.get("name", "Unknown")
    website = company.get("website", "")
    linkedin_url = company.get("linkedin_url", "")
    x_url = company.get("x_url", "")

    print(f"\n  Phase 3: Extracting intelligence for {name}...")

    page_content = ""
    if website:
        content = extract_url(website)
        if content and len(content) > 200:
            page_content = content
            print(f"    Extracted website content ({len(content)} chars)")

        for suffix in ["/about", "/about-us", "/team", "/pricing", "/products", "/solutions"]:
            sub_url = website.rstrip("/") + suffix
            sub_content = extract_url(sub_url)
            if sub_content and len(sub_content) > 200:
                page_content += f"\n\n--- {suffix} ---\n" + truncate(sub_content, 4000)
                print(f"    Extracted: {sub_url}")
                break
            time.sleep(0.3)

    linkedin_content = ""
    if linkedin_url:
        linkedin_content = extract_url(linkedin_url)
        if linkedin_content:
            print(f"    Extracted LinkedIn page ({len(linkedin_content)} chars)")

    x_content = ""
    if x_url:
        x_content = extract_url(x_url)
        if x_content:
            print(f"    Extracted X/Twitter page ({len(x_content)} chars)")

    news_results = web_search(f"{name} {topic} news funding launch 2025 2026", max_results=5)
    news_context = format_search_context(news_results, max_items=5, max_content_len=300)

    extra_source_urls = [r.get("url", "") for r in news_results if r.get("url")]
    existing_sources = company.get("source_urls", "")
    all_sources = [u for u in existing_sources.split("; ") if u] + extra_source_urls
    company["source_urls"] = "; ".join(list(dict.fromkeys(u for u in all_sources if u)))

    use_case_instruction = ""
    if use_case == "sponsorship":
        use_case_instruction = "Pay special attention to event involvement, community engagement, brand partnerships, and sponsorship history."
    elif use_case == "partnerships":
        use_case_instruction = "Pay special attention to integration ecosystem, partner programs, API availability, and co-marketing signals."
    elif use_case == "sales":
        use_case_instruction = "Pay special attention to buying signals, budget indicators, tech stack clues, and decision-maker accessibility."

    prompt = f"""Analyze this company for a {use_case} research use case.

Company: {name}
Website: {website}
LinkedIn: {linkedin_url}
X/Twitter: {x_url}

{"Website content:" + chr(10) + truncate(page_content, 6000) if page_content else "No website content."}

{"LinkedIn content:" + chr(10) + truncate(linkedin_content, 3000) if linkedin_content else "No LinkedIn content."}

{"X/Twitter content:" + chr(10) + truncate(x_content, 2000) if x_content else "No X/Twitter content."}

Recent news/mentions:
{news_context if news_context else "No recent news found."}

{use_case_instruction}

Extract and return a JSON object with these fields:
- "description": what the company does (2-3 sentences)
- "products_services": main products or services offered
- "icp": likely ideal customer profile / target customer types
- "locations": geographic locations if visible
- "stage": apparent company stage (startup, growth, enterprise, etc.)
- "hiring_signals": any hiring activity visible
- "launch_signals": recent launches, updates, or announcements
- "product_velocity": signs of active development
- "ecosystem": technology ecosystem, integrations, platforms
- "partnerships": visible partnership or alliance references
- "event_sponsor_relevance": event participation, sponsorships, conference presence
- "messaging_style": how the company positions itself publicly
- "momentum_summary": overall momentum assessment (1-2 sentences)
- "outreach_angle": recommended angle for {use_case} outreach (1-2 sentences)

For each field, tag confidence as:
- Add " [Observed]" if directly stated in source material
- Add " [Inferred]" if likely true from repeated signals
- Add " [Uncertain]" if weak or conflicting evidence

Return ONLY the JSON object. Do NOT fabricate information."""

    response = chat([
        {"role": "system", "content": "You are a company intelligence analyst. Extract verified public information. Tag each conclusion with confidence level. Never fabricate details. Respond with valid JSON only."},
        {"role": "user", "content": prompt},
    ])

    try:
        intel_data = parse_json_response(response)
    except json.JSONDecodeError:
        intel_data = {}

    if not isinstance(intel_data, dict):
        intel_data = {}

    company.update({k: str(v or "").strip() for k, v in intel_data.items() if k in COMPANY_FIELDS})
    return company


def extract_team_profiles(company, topic, use_case):
    name = company.get("name", "Unknown")
    website = company.get("website", "")

    print(f"\n  Phase 4: Extracting team profiles for {name}...")

    search_queries = [
        f"{name} founders CEO executives team",
        f"{name} leadership team about us",
        f"{name} {topic} team LinkedIn",
    ]

    all_results = []
    for query in search_queries:
        all_results.extend(web_search(query, max_results=5))
        time.sleep(0.3)

    page_content = ""
    if website:
        for suffix in ["/team", "/about", "/about-us", "/people", "/leadership"]:
            test_url = website.rstrip("/") + suffix
            content = extract_url(test_url)
            if content and len(content) > 300:
                page_content = content
                print(f"    Extracted team page: {test_url}")
                break
            time.sleep(0.3)

    search_context = format_search_context(all_results, max_items=15, max_content_len=400)
    page_content_trimmed = truncate(page_content, 6000)

    role_priority = ""
    if use_case == "sponsorship":
        role_priority = "Prioritize: marketing leads, community managers, partnerships/BD leads, CMO, CEO."
    elif use_case == "partnerships":
        role_priority = "Prioritize: partnerships/BD leads, CTO, product leads, CEO, integration engineers."
    elif use_case == "sales":
        role_priority = "Prioritize: CTO, VP Engineering, product leads, procurement, IT decision-makers."
    else:
        role_priority = "Prioritize: founders, C-suite, then department heads."

    prompt = f"""Find key team members at "{name}" for a {use_case} outreach use case.

{role_priority}

Search results:
{search_context}

{"Team/about page content:" + chr(10) + page_content_trimmed if page_content_trimmed else "No team page content found."}

For each person, return a JSON object with:
- "person_name": full name
- "role_title": their role/title
- "team_category": one of: founder, executive, operator, technical_lead, partnerships, marketing, sales, community, other
- "linkedin_url": LinkedIn profile URL if found, null otherwise
- "x_url": X/Twitter handle or URL if found, null otherwise
- "website_profile_url": company team page or personal site URL if found, null otherwise
- "github_url": GitHub profile URL if found, null otherwise
- "other_public_profile_urls": any other public profile URLs (comma-separated) if found, null otherwise
- "location_if_public": location if publicly visible, null otherwise
- "bio_summary": brief public bio (1-2 sentences)
- "activity_status": active, inactive, or unknown based on public signals
- "likely_decision_area": what they likely decide on (budget, tech stack, partnerships, etc.)
- "outreach_relevance": why they matter for {use_case} (1 sentence)
- "public_preferences_or_signals": any visible preferences, interests, or repeated themes
- "notable_public_posts_or_topics": recent public posts or topics if visible
- "confidence_level": "Observed", "Inferred", or "Uncertain"
- "notes": any additional context

Return a JSON array of up to 10 team members. Return ONLY the JSON array. Do NOT fabricate people or details."""

    response = chat([
        {"role": "system", "content": "You are a team intelligence analyst. Find real people and their public profiles. Never fabricate information. If uncertain, mark confidence accordingly. Respond with valid JSON only."},
        {"role": "user", "content": prompt},
    ], max_tokens=8192)

    try:
        members = parse_json_response(response)
    except json.JSONDecodeError:
        members = []

    if not isinstance(members, list):
        members = []

    cleaned = []
    for m in members:
        if not isinstance(m, dict):
            continue
        m["company_name"] = name
        cleaned.append(clean_team_member(m))

    cleaned = dedupe_team(cleaned)

    if cleaned:
        print(f"    Found {len(cleaned)} team member(s):")
        for m in cleaned:
            print(f"      - {m.get('person_name', 'Unknown')} ({m.get('role_title', 'N/A')})")
    else:
        print(f"    No team members found.")

    return cleaned


def synthesize_company(company, team_members, use_case):
    name = company.get("name", "Unknown")
    print(f"\n  Phase 5: Synthesizing analysis for {name}...")

    team_summary = ""
    if team_members:
        lines = []
        for m in team_members[:10]:
            lines.append(f"- {m.get('person_name', '?')}: {m.get('role_title', '?')} ({m.get('team_category', '?')}) - {m.get('outreach_relevance', 'N/A')}")
        team_summary = "\n".join(lines)

    prompt = f"""Provide a final synthesis for {use_case} outreach to "{name}".

Company data:
{json.dumps({k: company.get(k, '') for k in ['description', 'products_services', 'icp', 'stage', 'momentum_summary', 'messaging_style', 'ecosystem', 'partnerships', 'event_sponsor_relevance']}, indent=2)}

Team members:
{team_summary if team_summary else "No team data available."}

Answer these questions in a JSON object:
- "what_they_do": concise description of the company (2 sentences)
- "public_voice": what their public messaging signals right now (1-2 sentences)
- "apparent_stage": startup / growth / enterprise / mature
- "momentum_indicators": key signals of momentum, launches, hiring, or ecosystem movement
- "best_sponsor_contact": name and role of best person for sponsorship outreach, or "Not identified"
- "best_sales_contact": name and role of best person for sales outreach, or "Not identified"
- "best_partnership_contact": name and role of best person for partnership outreach, or "Not identified"
- "best_technical_contact": name and role of best person for technical/product discussions, or "Not identified"
- "strongest_outreach_angle": the single best angle for {use_case} outreach to this company (2-3 sentences)
- "observed_facts": list of key facts that are directly observed from sources
- "inferred_conclusions": list of conclusions that are likely but not directly stated
- "uncertain_areas": list of areas where evidence is weak or conflicting

Return ONLY the JSON object. Be honest about what is observed vs inferred vs uncertain."""

    response = chat([
        {"role": "system", "content": "You are a strategic outreach analyst. Synthesize company intelligence into actionable outreach recommendations. Be precise about confidence levels. Respond with valid JSON only."},
        {"role": "user", "content": prompt},
    ])

    try:
        synthesis = parse_json_response(response)
    except json.JSONDecodeError:
        synthesis = {}

    if not isinstance(synthesis, dict):
        synthesis = {}

    return synthesis


def generate_pdf_dossier(company, team_members, synthesis, profiles_dir, brand_name="MIA"):
    if not HAS_PDF:
        print(f"    Skipping PDF (fpdf2 not installed). Install with: pip install fpdf2")
        return None

    name = company.get("name", "Unknown")
    slug = company_slug(name)
    pdf_path = os.path.join(profiles_dir, f"{slug}.pdf")

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)

    def add_section(title, content, is_header=False):
        if is_header:
            pdf.set_font("Helvetica", "B", 16)
            pdf.set_text_color(30, 30, 80)
        else:
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(40, 40, 100)
        pdf.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(30, 30, 30)
        if content:
            safe_content = content.encode("latin-1", errors="replace").decode("latin-1")
            pdf.multi_cell(0, 5, safe_content)
        pdf.ln(4)

    def add_separator():
        pdf.set_draw_color(200, 200, 200)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(4)

    pdf.add_page()
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(30, 30, 80)
    pdf.ln(40)
    safe_name = name.encode("latin-1", errors="replace").decode("latin-1")
    pdf.cell(0, 15, safe_name, new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(8)
    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 10, "Company Intelligence Profile", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(6)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 8, f"Generated by {brand_name} | {datetime.now().strftime('%B %d, %Y')}", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(4)
    confidence = company.get("confidence", "unknown")
    pdf.set_font("Helvetica", "I", 10)
    pdf.cell(0, 8, f"Confidence: {confidence} | Coverage: {company.get('source_coverage', 'N/A')}", new_x="LMARGIN", new_y="NEXT", align="C")

    pdf.add_page()
    add_section("Executive Summary", synthesis.get("what_they_do", company.get("description", "No description available.")), is_header=True)
    add_separator()

    snapshot_lines = []
    snapshot_lines.append(f"Website: {company.get('website', 'N/A')}")
    snapshot_lines.append(f"LinkedIn: {company.get('linkedin_url', 'N/A')}")
    snapshot_lines.append(f"X/Twitter: {company.get('x_url', 'N/A')}")
    snapshot_lines.append(f"Category: {company.get('category', 'N/A')}")
    snapshot_lines.append(f"Stage: {synthesis.get('apparent_stage', company.get('stage', 'N/A'))}")
    snapshot_lines.append(f"Locations: {company.get('locations', 'N/A')}")
    add_section("Company Snapshot", "\n".join(snapshot_lines))
    add_separator()

    add_section("Official Positioning", company.get("messaging_style", "No positioning data available."))
    add_separator()

    add_section("Public Market Voice", synthesis.get("public_voice", "No public voice data available."))
    add_separator()

    add_section("Products & Services", company.get("products_services", "No product data available."))
    add_separator()

    add_section("Customer / ICP Inference", company.get("icp", "No ICP data available."))
    add_separator()

    market_lines = []
    market_lines.append(f"Momentum: {synthesis.get('momentum_indicators', company.get('momentum_summary', 'N/A'))}")
    market_lines.append(f"Hiring: {company.get('hiring_signals', 'N/A')}")
    market_lines.append(f"Launches: {company.get('launch_signals', 'N/A')}")
    market_lines.append(f"Product Velocity: {company.get('product_velocity', 'N/A')}")
    market_lines.append(f"Ecosystem: {company.get('ecosystem', 'N/A')}")
    market_lines.append(f"Partnerships: {company.get('partnerships', 'N/A')}")
    market_lines.append(f"Events/Sponsorship: {company.get('event_sponsor_relevance', 'N/A')}")
    add_section("Market Signals", "\n".join(market_lines))
    add_separator()

    pdf.add_page()
    add_section("Team & Decision-Maker Overview", "", is_header=True)
    if team_members:
        for m in team_members[:10]:
            member_lines = []
            member_lines.append(f"Name: {m.get('person_name', 'N/A')}")
            member_lines.append(f"Role: {m.get('role_title', 'N/A')}")
            member_lines.append(f"Category: {m.get('team_category', 'N/A')}")
            if m.get("linkedin_url"):
                member_lines.append(f"LinkedIn: {m['linkedin_url']}")
            if m.get("x_url"):
                member_lines.append(f"X/Twitter: {m['x_url']}")
            if m.get("bio_summary"):
                member_lines.append(f"Bio: {m['bio_summary']}")
            member_lines.append(f"Decision Area: {m.get('likely_decision_area', 'N/A')}")
            member_lines.append(f"Outreach Relevance: {m.get('outreach_relevance', 'N/A')}")
            member_lines.append(f"Confidence: {m.get('confidence_level', 'N/A')}")
            pdf.set_font("Helvetica", "B", 10)
            safe_pname = m.get("person_name", "Unknown").encode("latin-1", errors="replace").decode("latin-1")
            pdf.cell(0, 6, safe_pname, new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 9)
            safe_mlines = "\n".join(member_lines).encode("latin-1", errors="replace").decode("latin-1")
            pdf.multi_cell(0, 4, safe_mlines)
            pdf.ln(3)
    else:
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 8, "No team members identified with sufficient confidence.", new_x="LMARGIN", new_y="NEXT")
    add_separator()

    best_contacts = []
    best_contacts.append(f"Best Sponsor Contact: {synthesis.get('best_sponsor_contact', 'Not identified')}")
    best_contacts.append(f"Best Sales Contact: {synthesis.get('best_sales_contact', 'Not identified')}")
    best_contacts.append(f"Best Partnership Contact: {synthesis.get('best_partnership_contact', 'Not identified')}")
    best_contacts.append(f"Best Technical Contact: {synthesis.get('best_technical_contact', 'Not identified')}")
    add_section("Best Contacts by Use Case", "\n".join(best_contacts))
    add_separator()

    add_section("Outreach Angle", synthesis.get("strongest_outreach_angle", company.get("outreach_angle", "No outreach angle determined.")))
    add_separator()

    pdf.add_page()
    add_section("Confidence Notes", "", is_header=True)
    observed = synthesis.get("observed_facts", [])
    inferred = synthesis.get("inferred_conclusions", [])
    uncertain = synthesis.get("uncertain_areas", [])

    if observed:
        add_section("Observed (directly verified)", "\n".join(f"- {f}" for f in (observed if isinstance(observed, list) else [str(observed)])))
    if inferred:
        add_section("Inferred (likely from signals)", "\n".join(f"- {f}" for f in (inferred if isinstance(inferred, list) else [str(inferred)])))
    if uncertain:
        add_section("Uncertain (weak evidence)", "\n".join(f"- {f}" for f in (uncertain if isinstance(uncertain, list) else [str(uncertain)])))
    add_separator()

    source_lines = []
    source_lines.append(f"Website: {company.get('website', 'N/A')}")
    source_lines.append(f"LinkedIn: {company.get('linkedin_url', 'N/A')}")
    source_lines.append(f"X/Twitter: {company.get('x_url', 'N/A')}")
    source_urls = company.get("source_urls", "")
    if source_urls:
        for url in source_urls.split(";"):
            url = url.strip()
            if url:
                source_lines.append(f"Source: {url}")
    add_section("Source Appendix", "\n".join(source_lines))

    coverage = company.get("source_coverage", "")
    if "1/" in coverage or "0/" in coverage or company.get("confidence") == "partial":
        add_separator()
        limitations = []
        if not company.get("website"):
            limitations.append("- Official website could not be confirmed")
        if not company.get("linkedin_url"):
            limitations.append("- LinkedIn company page not found")
        if not company.get("x_url"):
            limitations.append("- X/Twitter company page not found")
        if not team_members:
            limitations.append("- No team members could be verified")
        if limitations:
            add_section("Coverage Limitations", "\n".join(limitations))

    try:
        pdf.output(pdf_path)
        print(f"    PDF saved: {pdf_path}")
        return pdf_path
    except Exception as e:
        print(f"    PDF generation error: {e}")
        return None


def run(topic, max_companies=10, use_case="general", output_dir=None, brand_name="MIA", enrich_only=False, resume_only=False, targets=None):
    start_time = time.time()
    run_dir = get_run_dir(topic, output_dir)
    paths = get_paths(run_dir)

    print(f"\n  MIA — Market Intelligence Analyst")
    print(f"  Topic: {topic}")
    print(f"  Use case: {use_case}")
    print(f"  Max companies: {max_companies}")
    print(f"  Output: {run_dir}\n")

    existing_companies = load_csv(paths["companies_csv"])
    existing_team = load_csv(paths["team_csv"])

    existing_company_keys = set(normalize_name(c.get("name", "")) for c in existing_companies)
    profiled_companies = set(normalize_name(c.get("name", "")) for c in existing_companies if c.get("description"))

    if existing_companies or existing_team:
        print(f"  Resuming from existing data:")
        print(f"    {len(existing_companies)} companies on file")
        print(f"    {len(existing_team)} team members on file")
        print(f"    {len(profiled_companies)} companies fully profiled")
        progress_report(paths)

    if enrich_only:
        print(f"\n{'='*60}")
        print(f"ENRICH-ONLY MODE")
        print(f"{'='*60}")
        if not existing_companies:
            print("  No companies to enrich. Run a full scan first.")
            return paths

        for i, company in enumerate(existing_companies):
            name_key = normalize_name(company.get("name", ""))

            needs_intel = not company.get("description")
            company_team = [t for t in existing_team if normalize_name(t.get("company_name", "")) == name_key]
            needs_team = len(company_team) == 0
            slug = company_slug(company.get("name", ""))
            needs_pdf = not os.path.exists(os.path.join(paths["profiles_dir"], f"{slug}.pdf"))

            if not needs_intel and not needs_team and not needs_pdf:
                continue

            print(f"\n  [{i+1}/{len(existing_companies)}] Enriching: {company.get('name', 'Unknown')}")

            if needs_intel:
                company = extract_company_intel(company, topic, use_case)
                existing_companies[i] = clean_company(company)

            if needs_team:
                new_team = extract_team_profiles(company, topic, use_case)
                existing_team.extend(new_team)
                company_team = new_team

            if needs_pdf or needs_intel:
                synthesis = synthesize_company(company, company_team, use_case)
                generate_pdf_dossier(company, company_team, synthesis, paths["profiles_dir"], brand_name)

            save_csv(paths["companies_csv"], existing_companies, COMPANY_FIELDS)
            save_csv(paths["team_csv"], dedupe_team(existing_team), TEAM_FIELDS)

        progress_report(paths)
        elapsed = time.time() - start_time
        print(f"  Time elapsed: {elapsed:.1f}s\n")
        return paths

    targeted_candidates = []
    if targets:
        print(f"\n  Targeted companies: {', '.join(targets)}")
        for t in targets:
            if normalize_name(t) not in existing_company_keys:
                targeted_candidates.append({"name": t})
            else:
                print(f"    {t} — already on file, will be profiled if incomplete.")

    if resume_only and existing_companies:
        print(f"\n  Resume mode: skipping discovery, profiling {len(existing_companies)} existing companies.")
        candidates = targeted_candidates
    elif targets and not targeted_candidates and existing_companies:
        candidates = []
    elif targets:
        remaining_slots = max(0, max_companies - len(targeted_candidates))
        if remaining_slots > 0:
            discovered = discover_companies(topic, remaining_slots)
            discovered = [c for c in discovered if normalize_name(c.get("name", "")) not in existing_company_keys
                          and normalize_name(c.get("name", "")) not in set(normalize_name(t) for t in targets)]
            candidates = targeted_candidates + discovered
        else:
            candidates = targeted_candidates
    elif not existing_companies:
        candidates = discover_companies(topic, max_companies)
    else:
        print(f"\n  Using {len(existing_companies)} existing companies. Searching for new candidates...")
        new_candidates = discover_companies(topic, max_companies)
        candidates = [c for c in new_candidates if normalize_name(c.get("name", "")) not in existing_company_keys]
        if candidates:
            print(f"  {len(candidates)} new candidates to validate.")
        else:
            print(f"  No new candidates found.")
            candidates = []

    if candidates:
        print(f"\n{'='*60}")
        print(f"Phase 2: Validating company identities")
        print(f"{'='*60}")

        validated = []
        for i, candidate in enumerate(candidates):
            if len(validated) >= max_companies:
                break

            name_key = normalize_name(candidate.get("name", ""))
            if name_key in existing_company_keys:
                continue

            print(f"\n  [{i+1}/{len(candidates)}]", end="")
            result = validate_company(candidate, topic)

            if result["confidence"] == "low":
                print(f"    DROPPED: {result['name']} (insufficient source coverage)")
                continue

            validated.append(result)
            existing_company_keys.add(name_key)

        existing_companies.extend(validated)
        print(f"\n  Validated {len(validated)} companies ({len(existing_companies)} total).")

    if len(existing_companies) > max_companies:
        strong = [c for c in existing_companies if c.get("confidence") != "low"]
        partial = [c for c in existing_companies if c.get("confidence") == "low"]
        existing_companies = (strong + partial)[:max_companies]

    save_csv(paths["companies_csv"], existing_companies, COMPANY_FIELDS)
    print(f"\n  Companies saved to: {paths['companies_csv']}")

    companies_to_profile = [
        c for c in existing_companies
        if normalize_name(c.get("name", "")) not in profiled_companies
    ]

    if not companies_to_profile:
        print(f"\n  All {len(existing_companies)} companies already profiled.")
    else:
        print(f"\n  {len(companies_to_profile)} companies to profile ({len(existing_companies) - len(companies_to_profile)} already done).")

    all_team = list(existing_team)
    all_syntheses = {}

    for i, company in enumerate(companies_to_profile, 1):
        print(f"\n{'='*60}")
        print(f"  [{i}/{len(companies_to_profile)}] Processing: {company.get('name', 'Unknown')}")
        print(f"{'='*60}")

        company = extract_company_intel(company, topic, use_case)

        idx = next((j for j, c in enumerate(existing_companies) if normalize_name(c.get("name", "")) == normalize_name(company.get("name", ""))), None)
        if idx is not None:
            existing_companies[idx] = clean_company(company)

        team_members = extract_team_profiles(company, topic, use_case)
        all_team.extend(team_members)

        synthesis = synthesize_company(company, team_members, use_case)
        all_syntheses[company.get("name", "")] = synthesis

        if company.get("outreach_angle", "") == "" and synthesis.get("strongest_outreach_angle"):
            company["outreach_angle"] = synthesis["strongest_outreach_angle"]
            if idx is not None:
                existing_companies[idx] = clean_company(company)

        generate_pdf_dossier(company, team_members, synthesis, paths["profiles_dir"], brand_name)

        save_csv(paths["companies_csv"], existing_companies, COMPANY_FIELDS)
        save_csv(paths["team_csv"], dedupe_team(all_team), TEAM_FIELDS)
        time.sleep(0.5)

    all_team = dedupe_team(all_team)
    save_csv(paths["team_csv"], all_team, TEAM_FIELDS)

    for company in existing_companies:
        name = company.get("name", "")
        if name in all_syntheses:
            continue
        name_key = normalize_name(name)
        company_team = [t for t in all_team if normalize_name(t.get("company_name", "")) == name_key]
        if company.get("description"):
            synthesis = synthesize_company(company, company_team, use_case)
            all_syntheses[name] = synthesis
            if not os.path.exists(os.path.join(paths["profiles_dir"], f"{company_slug(name)}.pdf")):
                generate_pdf_dossier(company, company_team, synthesis, paths["profiles_dir"], brand_name)

    summary = {
        "topic": topic,
        "use_case": use_case,
        "generated_at": datetime.now().isoformat(),
        "brand": brand_name,
        "total_companies": len(existing_companies),
        "total_team_members": len(all_team),
        "companies": [],
    }

    for company in existing_companies:
        name = company.get("name", "")
        syn = all_syntheses.get(name, {})
        name_key = normalize_name(name)
        company_team = [t for t in all_team if normalize_name(t.get("company_name", "")) == name_key]

        summary["companies"].append({
            "name": name,
            "website": company.get("website", ""),
            "linkedin": company.get("linkedin_url", ""),
            "x": company.get("x_url", ""),
            "confidence": company.get("confidence", ""),
            "best_sponsor_contact": syn.get("best_sponsor_contact", "Not identified"),
            "best_sales_contact": syn.get("best_sales_contact", "Not identified"),
            "best_partnership_contact": syn.get("best_partnership_contact", "Not identified"),
            "best_technical_contact": syn.get("best_technical_contact", "Not identified"),
            "strongest_outreach_angle": syn.get("strongest_outreach_angle", company.get("outreach_angle", "")),
            "team_count": len(company_team),
        })

    save_json(paths["summary_json"], summary)

    elapsed = time.time() - start_time
    progress_report(paths)

    print(f"  Time elapsed: {elapsed:.1f}s")
    print(f"\n  Output files:")
    print(f"    - {paths['companies_csv']}")
    print(f"    - {paths['team_csv']}")
    print(f"    - {paths['summary_json']}")

    pdf_count = len([f for f in os.listdir(paths["profiles_dir"]) if f.endswith(".pdf")])
    print(f"    - {paths['profiles_dir']}/ ({pdf_count} PDF dossiers)")
    print(f"{'='*60}\n")

    return paths


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="MIA — Market Intelligence Analyst. Discover companies, build dossiers, surface outreach contacts."
    )
    parser.add_argument("keywords", nargs="+", help="Keywords describing the market/topic to research")
    parser.add_argument("--max-companies", type=int, default=10, help="Maximum number of companies to profile (default: 10)")
    parser.add_argument("--use-case", choices=USE_CASES, default="general", help="Outreach use case: sponsorship, partnerships, sales, or general (default: general)")
    parser.add_argument("--output-dir", type=str, default=None, help="Custom output directory (default: runs/<topic>/)")
    parser.add_argument("--brand-name", type=str, default="MIA", help="Brand name for PDF dossiers (default: MIA)")
    parser.add_argument("--enrich-only", action="store_true", help="Only enrich existing company data, skip discovery")
    parser.add_argument("--resume-run", action="store_true", help="Resume a previous run — skip discovery, only profile unfinished companies")
    parser.add_argument("--targets", type=str, default=None, help="Comma-separated list of specific company names to target (e.g. 'Cursor,Lovable,Stripe')")

    args = parser.parse_args()

    topic = " ".join(args.keywords)
    targets = [t.strip() for t in args.targets.split(",") if t.strip()] if args.targets else None
    run(
        topic,
        max_companies=args.max_companies,
        use_case=args.use_case,
        output_dir=args.output_dir,
        brand_name=args.brand_name,
        enrich_only=args.enrich_only,
        resume_only=args.resume_run,
        targets=targets,
    )
