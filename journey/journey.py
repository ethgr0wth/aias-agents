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

PUB_FIELDS = ["name", "url", "type", "relevance", "editorial_page_url"]
JOURNALIST_FIELDS = [
    "name", "title", "publication", "publication_url",
    "beat", "email", "twitter", "linkedin", "source_url",
]

SESSION = requests.Session()
SESSION.headers.update(HEADERS)


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


def clean_publication(pub):
    return {
        "name": str(pub.get("name", "")).strip(),
        "url": str(pub.get("url", "")).strip(),
        "type": str(pub.get("type", "")).strip(),
        "relevance": str(pub.get("relevance", "")).strip(),
        "editorial_page_url": str(pub.get("editorial_page_url") or "").strip(),
    }


def clean_journalist(j):
    return {
        "name": str(j.get("name", "")).strip(),
        "title": str(j.get("title", "")).strip(),
        "publication": str(j.get("publication", "")).strip(),
        "publication_url": str(j.get("publication_url", "")).strip(),
        "beat": str(j.get("beat", "")).strip(),
        "email": str(j.get("email") or "").strip(),
        "twitter": str(j.get("twitter") or "").strip(),
        "linkedin": str(j.get("linkedin") or "").strip(),
        "source_url": str(j.get("source_url", "")).strip(),
    }


def dedupe_publications(publications):
    seen = set()
    unique = []
    for pub in publications:
        pub = clean_publication(pub)
        key = (pub["name"].lower(), get_domain(pub["url"]))
        if key not in seen:
            seen.add(key)
            unique.append(pub)
    return unique


def dedupe_journalists(journalists):
    seen = set()
    unique = []
    for j in journalists:
        j = clean_journalist(j)
        key = (normalize_name(j["name"]), j["publication"].lower())
        if key not in seen:
            seen.add(key)
            unique.append(j)
    return unique


def format_search_context(results, max_items=20, max_content_len=500):
    lines = []
    for r in results[:max_items]:
        title = truncate(r.get("title", ""), 150)
        url = r.get("url", "")
        content = truncate(r.get("content", ""), max_content_len)
        lines.append(f"- {title} ({url}): {content}")
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


def get_csv_paths(topic):
    slug = safe_topic_slug(topic)
    pub_path = os.path.join(OUTPUT_DIR, f"pubs_{slug}.csv")
    jour_path = os.path.join(OUTPUT_DIR, f"contacts_{slug}.csv")
    return pub_path, jour_path


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


def progress_report(pub_path, jour_path):
    pubs = load_csv(pub_path)
    journalists = load_csv(jour_path)

    total_j = len(journalists)
    with_email = sum(1 for j in journalists if j.get("email"))
    with_twitter = sum(1 for j in journalists if j.get("twitter"))
    with_linkedin = sum(1 for j in journalists if j.get("linkedin"))
    with_any = sum(1 for j in journalists if j.get("email") or j.get("twitter") or j.get("linkedin"))
    needs_enrich = total_j - with_any

    scanned_pubs = set(j.get("publication", "") for j in journalists)
    pubs_pending = len(pubs) - len(scanned_pubs)

    print(f"\n{'='*60}")
    print(f"PROGRESS REPORT")
    print(f"{'='*60}")
    print(f"  Publications:    {len(pubs)} total, {len(scanned_pubs)} scanned, {pubs_pending} pending")
    print(f"  Journalists:     {total_j} total")
    print(f"  With email:      {with_email}")
    print(f"  With Twitter:    {with_twitter}")
    print(f"  With LinkedIn:   {with_linkedin}")
    print(f"  Has any contact: {with_any}")
    print(f"  Needs enriching: {needs_enrich}")
    print(f"{'='*60}\n")


def find_publications(topic):
    print(f"\n{'='*60}")
    print(f"Searching for publications covering: {topic}")
    print(f"{'='*60}\n")

    search_queries = [
        f"top publications covering {topic}",
        f"best media outlets journalists {topic}",
        f"leading news publications {topic} industry",
    ]

    all_results = []
    for query in search_queries:
        print(f"  Searching: {query}")
        all_results.extend(web_search(query))
        time.sleep(0.5)

    search_context = format_search_context(all_results)
    print(f"\n  Found {len(all_results)} search results. Analyzing with AI...\n")

    prompt = f"""Based on the following search results about "{topic}", identify the most relevant publications (newspapers, magazines, online media outlets, blogs, trade publications) that actively cover this topic.

Search results:
{search_context}

Return a JSON array of publications. Each publication should have:
- "name": publication name
- "url": main website URL
- "type": type of publication (newspaper, magazine, online media, blog, trade publication, etc.)
- "relevance": why it's relevant to the topic (1 sentence)
- "editorial_page_url": URL of their about/team/staff/editorial page if you can determine it, otherwise null

Return ONLY the JSON array, no other text. Include 10-15 most relevant publications."""

    response = chat([
        {"role": "system", "content": "You are a media research analyst. You help find publications and media outlets relevant to specific topics. Always respond with valid JSON."},
        {"role": "user", "content": prompt},
    ])

    try:
        publications = parse_json_response(response)
    except json.JSONDecodeError:
        retry_response = chat([
            {"role": "system", "content": "You must respond with ONLY a valid JSON array. No markdown, no explanation."},
            {"role": "user", "content": f"Convert this into a valid JSON array of publications:\n\n{response}"},
        ])
        try:
            publications = parse_json_response(retry_response)
        except json.JSONDecodeError:
            print("  Error: Could not parse publications. Using empty list.")
            publications = []

    if not isinstance(publications, list):
        publications = []

    publications = dedupe_publications(publications)

    print(f"  Identified {len(publications)} relevant publications.\n")
    for pub in publications:
        print(f"    - {pub.get('name', 'Unknown')} ({pub.get('type', 'N/A')})")

    return publications


def find_journalists(publication, topic):
    pub_name = publication.get("name", "Unknown")
    pub_url = publication.get("url", "")
    domain = get_domain(pub_url)

    print(f"\n  Looking up journalists at {pub_name}...")

    search_queries = [
        f"{pub_name} journalists editors {topic}",
        f"site:{domain} staff editorial team about" if domain else f"{pub_name} staff editorial team about",
        f"{pub_name} reporter writer {topic} contact",
    ]

    all_results = []
    for query in search_queries:
        all_results.extend(web_search(query, max_results=5))
        time.sleep(0.3)

    editorial_url = publication.get("editorial_page_url")
    page_content = ""
    if editorial_url:
        print(f"    Extracting editorial page: {editorial_url}")
        page_content = extract_url(editorial_url)

    if not page_content and pub_url:
        for suffix in ["/about", "/team", "/staff", "/editorial-staff", "/contact", "/about-us"]:
            test_url = pub_url.rstrip("/") + suffix
            content = extract_url(test_url)
            if content and len(content) > 200:
                page_content = content
                print(f"    Found team page at: {test_url}")
                break
            time.sleep(0.3)

    search_context = format_search_context(all_results, max_items=15, max_content_len=400)
    page_content_trimmed = truncate(page_content, 6000)
    editorial_context = (
        "Editorial/team page content:\n" + page_content_trimmed
        if page_content_trimmed
        else "No editorial page content found."
    )

    prompt = f"""I'm researching journalists and editors at "{pub_name}" ({pub_url}) who cover "{topic}".

Search results:
{search_context}

{editorial_context}

Find journalists, editors, reporters, and writers at this publication who cover or are likely to cover topics related to "{topic}".

Return a JSON array of journalist objects. Each should have:
- "name": full name
- "title": their role/title (e.g., "Senior Reporter", "Editor-in-Chief", "Staff Writer")
- "beat": what topics they cover
- "email": email address if found, otherwise null
- "twitter": Twitter/X handle if found, otherwise null
- "linkedin": LinkedIn URL if found, otherwise null
- "source_url": URL where you found info about them

Return ONLY the JSON array, no other text. If you cannot find specific journalists, return an empty array []. Do NOT make up information - only include details you can verify from the search results and page content."""

    response = chat([
        {"role": "system", "content": "You are a media research analyst. Find real journalists and their contact details. Never fabricate information. If you cannot verify a detail, set it to null. Always respond with valid JSON."},
        {"role": "user", "content": prompt},
    ])

    try:
        journalists = parse_json_response(response)
    except json.JSONDecodeError:
        journalists = []

    if not isinstance(journalists, list):
        journalists = []

    cleaned = []
    for j in journalists:
        if not isinstance(j, dict):
            continue
        j["publication"] = pub_name
        j["publication_url"] = pub_url
        cleaned.append(clean_journalist(j))

    cleaned = dedupe_journalists(cleaned)

    if cleaned:
        print(f"    Found {len(cleaned)} journalist(s):")
        for j in cleaned:
            print(f"      - {j.get('name', 'Unknown')} ({j.get('title', 'N/A')})")
    else:
        print(f"    No journalists found for this publication.")

    return cleaned


def enrich_contacts(journalists, topic):
    needs_enrichment = [
        j for j in journalists
        if not (j.get("email") or j.get("twitter") or j.get("linkedin"))
    ]
    if not needs_enrichment:
        print("  All journalists already have contact info.")
        return journalists

    by_pub = {}
    for j in needs_enrichment:
        pub = j.get("publication", "Unknown")
        by_pub.setdefault(pub, []).append(j)

    for pub, group in by_pub.items():
        names = [j.get("name", "") for j in group if j.get("name")]
        if not names:
            continue

        batch_size = 5
        for i in range(0, len(names), batch_size):
            batch = names[i:i + batch_size]
            names_str = ", ".join(batch)
            print(f"    Enriching {len(batch)} contacts at {pub} (batch {i // batch_size + 1})...")

            results = web_search(f"{pub} journalists {names_str} email twitter contact", max_results=10)
            if not results:
                continue

            context = format_search_context(results, max_items=10, max_content_len=350)

            prompt = f"""Find contact information for these journalists at {pub} who cover {topic}:
{names_str}

Search results:
{context}

Return a JSON array of objects, one per journalist. Each object should have:
- "name": the journalist's name
- "email": email if found, null otherwise
- "twitter": Twitter/X handle if found, null otherwise
- "linkedin": LinkedIn URL if found, null otherwise

Return ONLY the JSON array, no other text. Do NOT make up information. Only include contacts you can verify from the search results."""

            response = chat([
                {"role": "system", "content": "Extract real contact information. Never fabricate data. Respond with valid JSON only."},
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
                    for j in group:
                        key = normalize_name(j.get("name", ""))
                        c = contact_map.get(key)
                        if not c:
                            continue
                        if c.get("email"):
                            j["email"] = str(c["email"]).strip()
                        if c.get("twitter"):
                            j["twitter"] = str(c["twitter"]).strip()
                        if c.get("linkedin"):
                            j["linkedin"] = str(c["linkedin"]).strip()
            except (json.JSONDecodeError, IndexError, KeyError, TypeError):
                pass

            time.sleep(0.3)

    return dedupe_journalists(journalists)


def run(topic, max_pubs=None, enrich_only=False):
    start_time = time.time()
    pub_path, jour_path = get_csv_paths(topic)

    existing_pubs = load_csv(pub_path)
    existing_journalists = load_csv(jour_path)

    existing_pub_keys = set(
        (p.get("name", "").lower(), get_domain(p.get("url", "")))
        for p in existing_pubs
    )
    existing_journalist_keys = set(
        (normalize_name(j.get("name", "")), j.get("publication", "").lower())
        for j in existing_journalists
    )
    scanned_pubs = set(j.get("publication", "").lower() for j in existing_journalists)

    if existing_pubs or existing_journalists:
        print(f"\n  Resuming from existing data:")
        print(f"    {len(existing_pubs)} publications on file")
        print(f"    {len(existing_journalists)} journalists on file")
        print(f"    {len(scanned_pubs)} publications already scanned for journalists")
        progress_report(pub_path, jour_path)

    if enrich_only:
        print(f"\n{'='*60}")
        print(f"ENRICH-ONLY MODE")
        print(f"{'='*60}")
        if not existing_journalists:
            print("  No journalists to enrich. Run a full scan first.")
            return pub_path, jour_path
        existing_journalists = enrich_contacts(existing_journalists, topic)
        save_csv(jour_path, existing_journalists, JOURNALIST_FIELDS)
        print(f"\n  Updated: {jour_path}")
        progress_report(pub_path, jour_path)
        elapsed = time.time() - start_time
        print(f"  Time elapsed: {elapsed:.1f}s\n")
        return pub_path, jour_path

    if not existing_pubs:
        publications = find_publications(topic)
    else:
        print(f"\n  Using {len(existing_pubs)} existing publications. Searching for new ones...")
        new_pubs = find_publications(topic)
        added = 0
        for pub in new_pubs:
            pub = clean_publication(pub)
            key = (pub["name"].lower(), get_domain(pub["url"]))
            if key not in existing_pub_keys:
                existing_pubs.append(pub)
                existing_pub_keys.add(key)
                added += 1
        if added:
            print(f"  Added {added} new publications.")
        else:
            print(f"  No new publications found.")
        publications = existing_pubs

    publications = dedupe_publications(publications)

    if max_pubs and len(publications) > max_pubs:
        print(f"\n  Limiting to top {max_pubs} publications (of {len(publications)} found).")
        publications = publications[:max_pubs]

    save_csv(pub_path, publications, PUB_FIELDS)
    print(f"\n  Publications saved to: {pub_path}")

    pubs_to_scan = [p for p in publications if p.get("name", "").lower() not in scanned_pubs]

    if not pubs_to_scan:
        print(f"\n  All {len(publications)} publications already scanned. Skipping journalist lookup.")
    else:
        print(f"\n  {len(pubs_to_scan)} publications to scan ({len(publications) - len(pubs_to_scan)} already done).")

    all_journalists = list(existing_journalists)

    for i, pub in enumerate(pubs_to_scan, 1):
        print(f"\n  [{i}/{len(pubs_to_scan)}]", end="")
        journalists = find_journalists(pub, topic)

        new_count = 0
        for j in journalists:
            key = (normalize_name(j.get("name", "")), j.get("publication", "").lower())
            if key not in existing_journalist_keys:
                all_journalists.append(j)
                existing_journalist_keys.add(key)
                new_count += 1

        if new_count:
            print(f"    Added {new_count} new journalist(s).")

        save_csv(jour_path, all_journalists, JOURNALIST_FIELDS)
        time.sleep(0.5)

    print(f"\n{'='*60}")
    print(f"Enriching contact information...")
    print(f"{'='*60}")
    all_journalists = enrich_contacts(all_journalists, topic)

    save_csv(jour_path, all_journalists, JOURNALIST_FIELDS)

    elapsed = time.time() - start_time
    progress_report(pub_path, jour_path)
    print(f"  Time elapsed: {elapsed:.1f}s")
    print(f"\n  Output files:")
    print(f"    - {pub_path}")
    print(f"    - {jour_path}")
    print(f"{'='*60}\n")

    return pub_path, jour_path


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Find publications and journalists covering a topic (resumable, v3)")
    parser.add_argument("topic", nargs="+", help="The topic to research")
    parser.add_argument("--max-pubs", type=int, default=None, help="Max number of publications to scan")
    parser.add_argument("--enrich-only", action="store_true", help="Only enrich existing contacts, skip discovery")
    args = parser.parse_args()

    topic = " ".join(args.topic)
    run(topic, max_pubs=args.max_pubs, enrich_only=args.enrich_only)
