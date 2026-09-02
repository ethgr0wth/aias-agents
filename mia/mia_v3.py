import os
import sys
import json
import csv
import re
import time
import uuid
import requests
from dotenv import load_dotenv
from enum import Enum
from dataclasses import dataclass, field, asdict
from datetime import datetime
from urllib.parse import urlparse
from typing import Optional

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
    "confidence_level", "enrichment_status", "notes",
]

USE_CASES = ["sponsorship", "partnerships", "sales", "general"]


class Phase(str, Enum):
    INIT = "init"
    DISCOVER = "discover"
    VALIDATE = "validate"
    PROFILE = "profile"
    COMPLETE = "complete"
    FAILED = "failed"

ALLOWED_TRANSITIONS = {
    Phase.INIT: [Phase.DISCOVER, Phase.VALIDATE, Phase.PROFILE, Phase.COMPLETE],
    Phase.DISCOVER: [Phase.VALIDATE, Phase.COMPLETE, Phase.FAILED],
    Phase.VALIDATE: [Phase.PROFILE, Phase.DISCOVER, Phase.COMPLETE, Phase.FAILED],
    Phase.PROFILE: [Phase.PROFILE, Phase.COMPLETE, Phase.FAILED],
    Phase.COMPLETE: [],
    Phase.FAILED: [Phase.INIT],
}


class EventType(str, Enum):
    PHASE_ENTER = "phase_enter"
    PHASE_EXIT = "phase_exit"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    EVIDENCE = "evidence"
    CONFIDENCE_SHIFT = "confidence_shift"
    STATUS = "status"
    MUTATION = "mutation"
    GUARD_REJECT = "guard_reject"
    BRAIN_DECISION = "brain_decision"
    RESOLUTION = "resolution"
    ERROR = "error"


@dataclass
class Event:
    run_id: str
    id: str
    ts: str
    phase: str
    type: str
    source: str
    payload: dict
    company: Optional[str] = None
    accepted: bool = True
    reject_reason: Optional[str] = None


@dataclass
class GuardrailConfig:
    min_sources_for_validation: int = 2
    min_confidence_for_extraction: str = "partial"
    max_brain_iterations: int = 8
    max_evidence_per_company: int = 50
    reject_markers: list = field(default_factory=lambda: [
        "I don't have", "I cannot verify", "hypothetical",
        "I'm making this up", "placeholder",
    ])


class Ledger:
    def __init__(self, path):
        self.path = path
        os.makedirs(os.path.dirname(path), exist_ok=True)

    def append(self, event: Event):
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(event), ensure_ascii=False) + "\n")

    def read_all(self):
        if not os.path.exists(self.path):
            return []
        events = []
        with open(self.path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return events

    def evidence_for(self, company):
        norm = normalize_name(company)
        return [e for e in self.read_all()
                if e.get("type") == EventType.EVIDENCE.value
                and normalize_name(e.get("company", "")) == norm]

    def stats(self):
        events = self.read_all()
        total = len(events)
        accepted = sum(1 for e in events if e.get("accepted", True))
        return {
            "total": total,
            "accepted": accepted,
            "rejected": total - accepted,
            "evidence": sum(1 for e in events if e.get("type") == EventType.EVIDENCE.value),
            "brain_decisions": sum(1 for e in events if e.get("type") == EventType.BRAIN_DECISION.value),
            "tool_calls": sum(1 for e in events if e.get("type") == EventType.TOOL_CALL.value),
            "guard_rejects": sum(1 for e in events if e.get("type") == EventType.GUARD_REJECT.value),
        }


class Runtime:
    def __init__(self, run_id, ledger, guardrails):
        self.run_id = run_id
        self.ledger = ledger
        self.guardrails = guardrails
        self.phase = Phase.INIT
        self.phase_history = []
        self.companies = []
        self.team = []
        self.syntheses = {}
        self.evidence_counts = {}
        self.confidence_scores = {}
        self.tool_calls = 0
        self.current_company = None

    def emit(self, etype, payload, source="runtime", company=None):
        event = Event(
            run_id=self.run_id,
            id=str(uuid.uuid4())[:12],
            ts=datetime.utcnow().isoformat() + "Z",
            phase=self.phase.value,
            type=etype.value,
            source=source,
            payload=payload,
            company=company or self.current_company,
        )
        event = self._resolve(event)
        self.ledger.append(event)
        if not event.accepted and event.type == EventType.GUARD_REJECT.value:
            print(f"    ⚠ GUARD: {event.reject_reason}")
        return event

    def _resolve(self, event):
        if event.type == EventType.EVIDENCE.value:
            claim = event.payload.get("claim", "")
            if not claim.strip():
                event.accepted = False
                event.reject_reason = "Empty evidence"
                return event
            for marker in self.guardrails.reject_markers:
                if marker.lower() in claim.lower():
                    event.accepted = False
                    event.reject_reason = f"Fabrication marker: '{marker}'"
                    self.emit(EventType.GUARD_REJECT, {
                        "reason": event.reject_reason, "claim": claim[:200]
                    }, source="guardrail")
                    return event
            norm = normalize_name(event.company or "")
            count = self.evidence_counts.get(norm, 0)
            if count >= self.guardrails.max_evidence_per_company:
                event.accepted = False
                event.reject_reason = "Evidence cap reached"
                return event
            self.evidence_counts[norm] = count + 1

        elif event.type == EventType.PHASE_ENTER.value:
            target = Phase(event.payload.get("target"))
            if target not in ALLOWED_TRANSITIONS.get(self.phase, []):
                event.accepted = False
                event.reject_reason = f"Invalid: {self.phase.value} → {target.value}"
                return event

        elif event.type == EventType.CONFIDENCE_SHIFT.value:
            conf = event.payload.get("confidence", "")
            if conf not in ("high", "partial", "low"):
                event.accepted = False
                event.reject_reason = f"Invalid confidence: {conf}"
                return event
            norm = normalize_name(event.company or "")
            self.confidence_scores[norm] = conf

        return event

    def transition(self, target):
        entry = self.emit(EventType.PHASE_ENTER, {"target": target.value, "from": self.phase.value})
        if not entry.accepted:
            print(f"  !! Transition REJECTED: {self.phase.value} → {target.value}")
            return False
        self.emit(EventType.PHASE_EXIT, {"phase": self.phase.value})
        self.phase_history.append({"from": self.phase.value, "to": target.value})
        self.phase = target
        labels = {
            Phase.DISCOVER: "Discovering", Phase.VALIDATE: "Validating",
            Phase.PROFILE: "Profiling", Phase.COMPLETE: "Complete", Phase.FAILED: "Failed",
        }
        label = labels.get(target, target.value)
        ctx = f" — {self.current_company}" if self.current_company else ""
        print(f"\n  ▸ {label}{ctx}")
        return True

    def confidence_gate(self, company_name):
        norm = normalize_name(company_name)
        conf = self.confidence_scores.get(norm, "low")
        hierarchy = {"low": 0, "partial": 1, "high": 2}
        min_conf = self.guardrails.min_confidence_for_extraction
        if hierarchy.get(conf, 0) < hierarchy.get(min_conf, 0):
            self.emit(EventType.GUARD_REJECT, {
                "reason": f"Confidence gate: {conf} < {min_conf}"
            }, source="guardrail", company=company_name)
            return False
        return True

    def save_state(self, path):
        save_json(path, {
            "run_id": self.run_id, "phase": self.phase.value,
            "companies": len(self.companies), "team": len(self.team),
            "tool_calls": self.tool_calls, "evidence_counts": self.evidence_counts,
            "confidence_scores": self.confidence_scores,
            "phase_history": self.phase_history,
        })


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


def web_search(query, max_results=10, rt=None):
    if rt:
        rt.emit(EventType.TOOL_CALL, {"tool": "web_search", "query": query}, source="tool")
    try:
        data = post_json("/v1/search", {"query": query, "search_depth": "advanced", "max_results": max_results}, timeout=30)
        if not data.get("success"):
            return []
        results = data.get("results", [])
        if rt:
            rt.emit(EventType.TOOL_RESULT, {"tool": "web_search", "count": len(results)}, source="tool")
            rt.tool_calls += 1
        return results
    except Exception as e:
        print(f"  Search failed for '{query}': {e}")
        if rt:
            rt.emit(EventType.ERROR, {"tool": "web_search", "error": str(e)}, source="tool")
        return []


def extract_url(url, rt=None):
    if rt:
        rt.emit(EventType.TOOL_CALL, {"tool": "extract_url", "url": url}, source="tool")
    try:
        data = post_json("/v1/web/extract", {"url": url, "extract_links": True, "max_content_length": 15000}, timeout=30)
        if data.get("success"):
            content = data.get("content", "")
            if rt:
                rt.emit(EventType.TOOL_RESULT, {"tool": "extract_url", "chars": len(content)}, source="tool")
                rt.tool_calls += 1
            return content
    except Exception as e:
        print(f"  Extract error for {url}: {e}")
        if rt:
            rt.emit(EventType.ERROR, {"tool": "extract_url", "error": str(e)}, source="tool")
    return ""


def chat_stream(messages, max_tokens=8192, rt=None, company=None):
    if rt:
        rt.emit(EventType.TOOL_CALL, {"tool": "chat", "msgs": len(messages)}, source="model", company=company)

    try:
        url = f"{BASE_URL}/v1/chat/completions"
        r = SESSION.post(url, json={
            "model": MODEL, "messages": messages, "max_tokens": max_tokens, "stream": True
        }, timeout=120, stream=True)
        r.raise_for_status()
    except Exception as e:
        print(f"    Stream open error: {e}, falling back to sync")
        return _chat_sync(messages, max_tokens, rt, company)

    accumulated = []
    tokens = 0
    try:
        for line in r.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data: "):
                continue
            data_str = line[6:].strip()
            if data_str == "[DONE]":
                break
            try:
                chunk = json.loads(data_str)
            except json.JSONDecodeError:
                continue
            choices = chunk.get("choices", [])
            if not choices:
                continue
            content = choices[0].get("delta", {}).get("content", "")
            if content:
                accumulated.append(content)
                tokens += 1
    except Exception as e:
        print(f"    Stream read error: {e}")
        if not accumulated:
            return _chat_sync(messages, max_tokens, rt, company)

    result = "".join(accumulated)
    if rt:
        rt.emit(EventType.TOOL_RESULT, {"tool": "chat", "tokens": tokens, "chars": len(result)}, source="model", company=company)
        rt.tool_calls += 1
    return result if result else "[]"


def _chat_sync(messages, max_tokens=8192, rt=None, company=None):
    try:
        data = post_json("/v1/chat/completions", {"model": MODEL, "messages": messages, "max_tokens": max_tokens}, timeout=120)
        result = data["choices"][0]["message"]["content"]
        if rt:
            rt.emit(EventType.TOOL_RESULT, {"tool": "chat_sync", "chars": len(result)}, source="model", company=company)
            rt.tool_calls += 1
        return result
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
        data = intel.scan(sources=sources_list, keywords=keywords, limit=25, category="recent", subreddits=subreddits)
        return data.get("data", {}).get("results", [])
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
        "ledger": os.path.join(run_dir, "event_ledger.jsonl"),
        "state": os.path.join(run_dir, "runtime_state.json"),
    }

def progress_report(paths):
    companies = load_csv(paths["companies_csv"])
    team = load_csv(paths["team_csv"])
    total_c = len(companies)
    strong = sum(1 for c in companies if c.get("confidence") != "low")
    partial = total_c - strong
    total_t = len(team)
    with_any = sum(1 for t in team if t.get("linkedin_url") or t.get("x_url") or t.get("github_url"))
    profiled = set(t.get("company_name", "") for t in team)
    print(f"\n{'='*60}")
    print(f"PROGRESS REPORT")
    print(f"{'='*60}")
    print(f"  Companies:       {total_c} total ({strong} strong, {partial} partial)")
    print(f"  Profiled:        {len(profiled)} companies with team data")
    print(f"  Team members:    {total_t} total")
    print(f"  With profiles:   {with_any}")
    print(f"{'='*60}\n")


def discover_companies(topic, max_companies, rt):
    rt.transition(Phase.DISCOVER)

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
        all_results.extend(web_search(query, rt=rt))
        time.sleep(0.5)

    signal_context = ""
    if intel:
        print(f"\n  Scanning signals...")
        signal_keywords = topic.split()[:5] + ["company", "startup", "product", "launch"]
        signals = scan_signals(signal_keywords)
        if signals:
            signal_context = format_signal_context(signals)

    search_context = format_search_context(all_results)
    print(f"\n  Found {len(all_results)} results. Analyzing...\n")

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

    response = chat_stream([
        {"role": "system", "content": "You are a market research analyst. Identify real companies from search results. Always respond with valid JSON. Never fabricate companies or details."},
        {"role": "user", "content": prompt},
    ], rt=rt)

    try:
        candidates = parse_json_response(response)
    except json.JSONDecodeError:
        retry = chat_stream([
            {"role": "system", "content": "Respond with ONLY a valid JSON array."},
            {"role": "user", "content": f"Convert into a valid JSON array:\n\n{response}"},
        ], rt=rt)
        try:
            candidates = parse_json_response(retry)
        except json.JSONDecodeError:
            candidates = []

    if not isinstance(candidates, list):
        candidates = []

    seen = set()
    unique = []
    for c in candidates:
        if not isinstance(c, dict):
            continue
        name = normalize_name(c.get("name", ""))
        if name and name not in seen:
            seen.add(name)
            unique.append(c)

    rt.emit(EventType.RESOLUTION, {"phase": "discover", "found": len(unique)})
    print(f"  Identified {len(unique)} candidates.\n")
    for c in unique[:max_companies * 2]:
        print(f"    - {c.get('name', 'Unknown')}")
    return unique


def validate_company(candidate, topic, rt):
    name = candidate.get("name", "Unknown")
    likely_website = candidate.get("website", "")
    rt.current_company = name

    print(f"\n  Validating: {name}...")
    website = ""
    linkedin_url = ""
    x_url = ""
    sources_found = []

    if likely_website:
        content = extract_url(likely_website, rt=rt)
        if content and len(content) > 100:
            website = likely_website
            sources_found.append("website")
            print(f"    Website confirmed: {website}")
            rt.emit(EventType.EVIDENCE, {"claim": f"Website confirmed: {website}", "confidence": 0.9, "source": "website"}, source="tool")
        time.sleep(0.3)

    if not website:
        results = web_search(f"{name} official website", max_results=3, rt=rt)
        for r in results:
            url = r.get("url", "")
            if url and "linkedin" not in url and "twitter" not in url and "x.com" not in url:
                content = extract_url(url, rt=rt)
                if content and len(content) > 100:
                    website = url
                    sources_found.append("website")
                    print(f"    Website found: {website}")
                    rt.emit(EventType.EVIDENCE, {"claim": f"Website found: {website}", "confidence": 0.7, "source": "search"}, source="tool")
                    break
                time.sleep(0.3)

    results = web_search(f"{name} LinkedIn company page", max_results=5, rt=rt)
    for r in results:
        url = r.get("url", "")
        if "linkedin.com/company" in url.lower():
            linkedin_url = url
            sources_found.append("linkedin")
            print(f"    LinkedIn found: {linkedin_url}")
            rt.emit(EventType.EVIDENCE, {"claim": f"LinkedIn: {linkedin_url}", "confidence": 0.85}, source="tool")
            break
    time.sleep(0.3)

    results = web_search(f"{name} X Twitter company official", max_results=5, rt=rt)
    for r in results:
        url = r.get("url", "")
        if "x.com/" in url.lower() or "twitter.com/" in url.lower():
            x_url = url
            sources_found.append("x")
            print(f"    X/Twitter found: {x_url}")
            rt.emit(EventType.EVIDENCE, {"claim": f"X/Twitter: {x_url}", "confidence": 0.8}, source="tool")
            break
    time.sleep(0.3)

    coverage = len(sources_found)
    if coverage == 3:
        confidence = "high"
    elif coverage == 2:
        confidence = "partial"
    else:
        confidence = "low"

    rt.emit(EventType.CONFIDENCE_SHIFT, {"confidence": confidence, "coverage": f"{coverage}/3", "sources": sources_found}, company=name)
    print(f"    Source coverage: {coverage}/3 ({', '.join(sources_found) if sources_found else 'none'}) -> {confidence}")

    return {
        "name": name, "website": website, "linkedin_url": linkedin_url, "x_url": x_url,
        "source_coverage": f"{coverage}/3: {', '.join(sources_found) if sources_found else 'none'}",
        "confidence": confidence, "relevance": candidate.get("relevance", ""),
        "category": candidate.get("category", ""),
        "source_urls": "; ".join([u for u in [website, linkedin_url, x_url] if u]),
    }


def brain_gather_context(company, topic, rt):
    name = company.get("name", "Unknown")
    website = company.get("website", "")
    linkedin_url = company.get("linkedin_url", "")
    x_url = company.get("x_url", "")

    gathered = {"website": "", "linkedin": "", "x": "", "news": "", "news_urls": []}

    if website:
        content = extract_url(website, rt=rt)
        if content and len(content) > 200:
            gathered["website"] = content
            print(f"    Extracted website ({len(content)} chars)")
        for suffix in ["/about", "/about-us", "/team", "/pricing", "/products", "/solutions"]:
            sub_url = website.rstrip("/") + suffix
            sub = extract_url(sub_url, rt=rt)
            if sub and len(sub) > 200:
                gathered["website"] += f"\n\n--- {suffix} ---\n" + truncate(sub, 4000)
                print(f"    Extracted: {sub_url}")
                break
            time.sleep(0.3)

    if linkedin_url:
        content = extract_url(linkedin_url, rt=rt)
        if content:
            gathered["linkedin"] = content
            print(f"    Extracted LinkedIn ({len(content)} chars)")

    if x_url:
        content = extract_url(x_url, rt=rt)
        if content:
            gathered["x"] = content
            print(f"    Extracted X/Twitter ({len(content)} chars)")

    team_search = web_search(f"{name} leadership team executives VP director", max_results=5, rt=rt)
    team_context = format_search_context(team_search, max_items=5, max_content_len=400)
    if team_context:
        gathered["website"] += f"\n\n--- Leadership/Team Search Results ---\n{team_context}"
        print(f"    Team search: {len(team_search)} results")
    for r in team_search:
        url = r.get("url", "")
        if website and get_domain(url) == get_domain(website):
            if any(kw in url.lower() for kw in ["team", "about", "leadership", "people"]):
                sub = extract_url(url, rt=rt)
                if sub and len(sub) > 200:
                    gathered["website"] += f"\n\n--- Team Page: {url} ---\n{truncate(sub, 4000)}"
                    print(f"    Extracted team page: {url}")
                    break

    news = web_search(f"{name} {topic} news funding launch 2025 2026", max_results=5, rt=rt)
    gathered["news"] = format_search_context(news, max_items=5, max_content_len=300)
    gathered["news_urls"] = [r.get("url", "") for r in news if r.get("url")]

    return gathered


def brain_profile_company(company, gathered, topic, use_case, rt):
    name = company.get("name", "Unknown")
    rt.current_company = name

    rt.transition(Phase.PROFILE)

    if not rt.confidence_gate(name):
        print(f"    !! Confidence gate blocked {name}")
        return company, [], {}

    print(f"\n  Phase 3-5: Brain profiling {name}...")
    print(f"    LLM is in control — deciding what to extract, how deep to go, and when evidence is sufficient.")

    use_case_note = {
        "sponsorship": "The goal is sponsorship outreach. Focus on event presence, community, brand partnerships, marketing leads.",
        "partnerships": "The goal is partnership outreach. Focus on integration ecosystem, API, partner programs, BD/CTO contacts.",
        "sales": "The goal is sales outreach. Focus on buying signals, budget, tech stack, decision-makers.",
        "general": "General research. Cover all angles.",
    }.get(use_case, "")

    brain_prompt = f"""You are MIA, a Market Intelligence Analyst. You are profiling "{name}" for {use_case} outreach.

YOUR MISSION: Analyze all available data about this company, extract intelligence, identify the team, and synthesize outreach recommendations. You are the second brain — you decide what matters, what to trust, and what to discard.

{use_case_note}

AVAILABLE DATA:
{"Website content:" + chr(10) + truncate(gathered["website"], 6000) if gathered["website"] else "No website content."}

{"LinkedIn content:" + chr(10) + truncate(gathered["linkedin"], 3000) if gathered["linkedin"] else "No LinkedIn content."}

{"X/Twitter content:" + chr(10) + truncate(gathered["x"], 2000) if gathered["x"] else "No X/Twitter content."}

Recent news:
{gathered["news"] if gathered["news"] else "No recent news found."}

Company website: {company.get("website", "N/A")}
Company LinkedIn: {company.get("linkedin_url", "N/A")}
Company X/Twitter: {company.get("x_url", "N/A")}

RESPOND WITH A SINGLE JSON OBJECT containing three sections:

1. "company_intel" — a JSON object with these fields (tag each with [Observed], [Inferred], or [Uncertain]):
   - "description", "products_services", "icp", "locations", "stage"
   - "hiring_signals", "launch_signals", "product_velocity"
   - "ecosystem", "partnerships", "event_sponsor_relevance"
   - "messaging_style", "momentum_summary", "outreach_angle"

2. "team" — a JSON array of up to 10 REAL NAMED people, each with:
   CRITICAL RULES FOR TEAM EXTRACTION:
   - Every entry MUST have a real human name (first + last). Never create placeholder entries like "Unknown named leader" or "Partnerships leadership" or "Google Cloud partner organization contact".
   - Include people whose names appear in the data AND well-known public figures at the company (e.g. CEO, CTO) even if not explicitly in the text — mark those as confidence "Inferred".
   - Do NOT stop at executives. Go DEEPER: find VPs, Directors, Heads of, team leads — especially in BD, partnerships, developer relations, product, engineering.
   - Prioritize people you'd actually email for {use_case} outreach — operators and middle management matter more than the CEO.
   - If the data mentions team pages, about pages, or leadership pages, note them in investigation_notes for further enrichment.

   Fields per person:
   - "person_name" (MUST be a real first+last name, never a title or department placeholder), "role_title"
   - "team_category": founder / executive / operator / technical_lead / partnerships / marketing / sales / community / other
   - "linkedin_url" (or null), "x_url" (or null), "github_url" (or null)
   - "website_profile_url" (or null), "other_public_profile_urls" (or null)
   - "location_if_public" (or null), "bio_summary", "activity_status"
   - "likely_decision_area", "outreach_relevance"
   - "public_preferences_or_signals", "notable_public_posts_or_topics"
   - "confidence_level": "Observed" / "Inferred" / "Uncertain"
   - "notes"

3. "synthesis" — a JSON object with:
   - "what_they_do", "public_voice", "apparent_stage", "momentum_indicators"
   - "best_sponsor_contact", "best_sales_contact", "best_partnership_contact", "best_technical_contact"
   - "strongest_outreach_angle" (2-3 sentences for {use_case})
   - "observed_facts" (list), "inferred_conclusions" (list), "uncertain_areas" (list)
   - "investigation_notes": what you noticed, what's missing, what you'd investigate further with more time

Return ONLY the JSON object. Do NOT fabricate people, URLs, or facts. If unsure, mark confidence accordingly. You are the analyst — be honest and precise."""

    rt.emit(EventType.BRAIN_DECISION, {
        "action": "unified_profile",
        "company": name,
        "data_sources": [k for k, v in gathered.items() if v and k != "news_urls"],
        "rationale": "Single comprehensive analysis — LLM sees all data and produces intel + team + synthesis in one pass",
    }, source="brain", company=name)

    response = chat_stream([
        {"role": "system", "content": "You are MIA, a market intelligence analyst. You are the second brain — autonomous, precise, honest. Extract real intelligence, identify real people, synthesize actionable outreach. Never fabricate. Tag all conclusions with confidence. Respond with valid JSON only."},
        {"role": "user", "content": brain_prompt},
    ], max_tokens=12288, rt=rt, company=name)

    try:
        result = parse_json_response(response)
    except json.JSONDecodeError:
        print(f"    !! Brain response parse failed, retrying...")
        retry = chat_stream([
            {"role": "system", "content": "Respond with ONLY valid JSON. No markdown."},
            {"role": "user", "content": f"Fix this into valid JSON:\n\n{response[:4000]}"},
        ], rt=rt, company=name)
        try:
            result = parse_json_response(retry)
        except json.JSONDecodeError:
            result = {}

    if not isinstance(result, dict):
        result = {}

    intel_data = result.get("company_intel", {})
    if isinstance(intel_data, dict):
        for field_name, value in intel_data.items():
            if field_name in COMPANY_FIELDS and value:
                val_str = str(value)
                conf = 0.8
                if "[Observed]" in val_str:
                    conf = 0.95
                elif "[Uncertain]" in val_str:
                    conf = 0.4
                elif "[Inferred]" in val_str:
                    conf = 0.65
                rt.emit(EventType.EVIDENCE, {
                    "claim": f"{field_name}: {truncate(val_str, 200)}", "confidence": conf, "field": field_name,
                }, source="brain", company=name)
        company.update({k: str(v or "").strip() for k, v in intel_data.items() if k in COMPANY_FIELDS})

    extra_urls = gathered.get("news_urls", [])
    existing = company.get("source_urls", "")
    all_sources = [u for u in existing.split("; ") if u] + extra_urls
    company["source_urls"] = "; ".join(list(dict.fromkeys(u for u in all_sources if u)))

    team_data = result.get("team", [])
    team_members = []
    if isinstance(team_data, list):
        for m in team_data:
            if not isinstance(m, dict):
                continue
            m["company_name"] = name
            cleaned = clean_team_member(m)
            team_members.append(cleaned)
            rt.emit(EventType.EVIDENCE, {
                "claim": f"Team: {m.get('person_name', '?')} — {m.get('role_title', '?')}",
                "confidence": 0.7 if m.get("confidence_level") == "Observed" else 0.4,
                "entity": "team_member",
            }, source="brain", company=name)
        team_members = dedupe_team(team_members)

    if team_members:
        print(f"    Found {len(team_members)} team member(s):")
        for m in team_members:
            print(f"      - {m.get('person_name', '?')} ({m.get('role_title', 'N/A')})")
    else:
        print(f"    No team members identified.")

    synthesis = result.get("synthesis", {})
    if not isinstance(synthesis, dict):
        synthesis = {}

    if synthesis.get("investigation_notes"):
        rt.emit(EventType.BRAIN_DECISION, {
            "action": "investigation_notes",
            "notes": synthesis["investigation_notes"],
        }, source="brain", company=name)
        print(f"    Brain notes: {truncate(str(synthesis['investigation_notes']), 200)}")

    for key in ["observed_facts", "inferred_conclusions", "uncertain_areas"]:
        items = synthesis.get(key, [])
        if isinstance(items, list):
            tag = key.split("_")[0]
            for item in items:
                rt.emit(EventType.EVIDENCE, {
                    "claim": str(item),
                    "confidence": {"observed": 0.95, "inferred": 0.6, "uncertain": 0.3}.get(tag, 0.5),
                    "category": key,
                }, source="brain", company=name)

    rt.emit(EventType.MUTATION, {
        "entity": "company", "company": name,
        "intel_fields": len([k for k in intel_data if k in COMPANY_FIELDS]),
        "team_members": len(team_members),
        "has_synthesis": bool(synthesis),
    }, source="runtime", company=name)

    rt.emit(EventType.RESOLUTION, {
        "phase": "profile", "company": name,
        "intel_fields": len([k for k in intel_data if k in COMPANY_FIELDS]),
        "team_count": len(team_members),
        "contacts_identified": sum(1 for k in ["best_sponsor_contact", "best_sales_contact", "best_partnership_contact", "best_technical_contact"]
                                    if synthesis.get(k) and synthesis[k] != "Not identified"),
    }, source="runtime", company=name)

    return company, team_members, synthesis


def _scan_linkedin_people(person_name, company_name, rt=None):
    keywords = [f"{person_name} {company_name}"]
    if rt:
        rt.emit(EventType.TOOL_CALL, {"tool": "intel_scan", "source": "linkedin_people", "keywords": keywords}, source="enrichment")
    try:
        data = intel.scan(sources=["linkedin_people"], keywords=keywords, limit=10, category="recent")
        results = data.get("data", {}).get("results", [])
        if rt:
            rt.emit(EventType.TOOL_RESULT, {"tool": "intel_scan", "source": "linkedin_people", "count": len(results)}, source="enrichment")
            rt.tool_calls += 1
        return results
    except Exception as e:
        if rt:
            rt.emit(EventType.ERROR, {"tool": "intel_scan", "source": "linkedin_people", "error": str(e)}, source="enrichment")
        return []


def _scan_twitter(person_name, company_name, rt=None):
    keywords = [f"{person_name} {company_name}"]
    if rt:
        rt.emit(EventType.TOOL_CALL, {"tool": "intel_scan", "source": "twitter", "keywords": keywords}, source="enrichment")
    try:
        data = intel.scan(sources=["twitter"], keywords=keywords, limit=10, category="recent")
        results = data.get("data", {}).get("results", [])
        if rt:
            rt.emit(EventType.TOOL_RESULT, {"tool": "intel_scan", "source": "twitter", "count": len(results)}, source="enrichment")
            rt.tool_calls += 1
        return results
    except Exception as e:
        if rt:
            rt.emit(EventType.ERROR, {"tool": "intel_scan", "source": "twitter", "error": str(e)}, source="enrichment")
        return []


def _serp_fallback_linkedin(person_name, company_name, rt=None):
    results = web_search(f'"{person_name}" "{company_name}" site:linkedin.com/in/', max_results=5, rt=rt)
    if not results:
        results = web_search(f'{person_name} {company_name} LinkedIn profile', max_results=5, rt=rt)
    candidates = []
    for r in results:
        url = (r.get("url") or "").lower()
        if "linkedin.com/in/" in url:
            candidates.append({
                "url": r.get("url", ""),
                "title": r.get("title", ""),
                "snippet": r.get("content", ""),
                "source": "serp_fallback",
            })
    return candidates


def _serp_fallback_twitter(person_name, company_name, rt=None):
    results = web_search(f'"{person_name}" "{company_name}" site:x.com', max_results=5, rt=rt)
    if not results:
        results = web_search(f'{person_name} {company_name} Twitter', max_results=5, rt=rt)
    candidates = []
    for r in results:
        url = (r.get("url") or "").lower()
        if "x.com/" in url or "twitter.com/" in url:
            if "/status/" not in url:
                candidates.append({
                    "url": r.get("url", ""),
                    "title": r.get("title", ""),
                    "snippet": r.get("content", ""),
                    "source": "serp_fallback",
                })
    return candidates


def _format_candidates_for_verification(candidates, platform):
    lines = []
    for i, c in enumerate(candidates[:5], 1):
        lines.append(f"Candidate {i}:")
        if c.get("url"):
            lines.append(f"  URL: {c['url']}")
        if c.get("title"):
            lines.append(f"  Title: {c['title']}")
        if c.get("snippet"):
            lines.append(f"  Snippet: {truncate(c['snippet'], 300)}")
        if c.get("headline"):
            lines.append(f"  Headline: {c['headline']}")
        if c.get("company"):
            lines.append(f"  Company: {c['company']}")
        if c.get("author"):
            lines.append(f"  Author: {c['author']}")
        if c.get("body"):
            lines.append(f"  Content: {truncate(c['body'], 300)}")
        lines.append("")
    return "\n".join(lines)


def _verify_candidates(candidates, person_name, company_name, role, platform, rt=None):
    if not candidates:
        return None, False

    candidate_text = _format_candidates_for_verification(candidates, platform)

    verify_prompt = f"""I am looking for the {platform} profile of "{person_name}" who works at "{company_name}" as "{role}".

Here are the candidate profiles found:

{candidate_text}

QUESTION: Which candidate (if any) is the correct {platform} profile for {person_name} at {company_name}?

Respond with ONLY a JSON object:
{{
  "match_found": true or false,
  "candidate_number": 1-5 or null,
  "profile_url": "the URL of the matched profile" or null,
  "confidence": "high" / "medium" / "low",
  "reason": "brief explanation of why this is or isn't a match"
}}"""

    verify_resp = chat_stream([
        {"role": "system", "content": "You verify identity matches between a target person and candidate profiles. Be strict — only confirm if name and company clearly match. Never guess. Respond with valid JSON only."},
        {"role": "user", "content": verify_prompt},
    ], max_tokens=512, rt=rt, company=company_name)

    try:
        verdict = parse_json_response(verify_resp)
        if verdict.get("match_found") and verdict.get("confidence") in ("high", "medium"):
            url = verdict.get("profile_url", "")
            if not url and verdict.get("candidate_number"):
                idx = int(verdict["candidate_number"]) - 1
                if 0 <= idx < len(candidates):
                    url = candidates[idx].get("url", "")
            return url, True, verdict
        return None, False, verdict
    except (json.JSONDecodeError, TypeError, KeyError):
        return None, False, None


def enrich_contacts(team_members, company, rt=None):
    name = company.get("name", "Unknown")
    to_enrich = [
        m for m in team_members
        if m.get("person_name", "").strip()
        and m.get("person_name", "").strip().lower() not in ("unknown", "n/a", "none", "")
        and not (m.get("linkedin_url") and "linkedin.com/in/" in (m.get("linkedin_url") or ""))
    ]
    if not to_enrich:
        return team_members

    print(f"\n  ▸ Enriching {len(to_enrich)} contacts for {name}")
    has_intel = intel is not None

    for member in to_enrich:
        pname = member.get("person_name", "")
        role = member.get("role_title", "")
        if not pname or pname.lower() in ("unknown", "n/a"):
            continue

        print(f"    [{pname}] ({role})")

        linkedin_url = ""
        x_url = ""
        linkedin_verified = False
        x_verified = False

        li_candidates = []
        if has_intel:
            print(f"      Netrows linkedin_people scan...")
            netrows_results = _scan_linkedin_people(pname, name, rt)
            for r in netrows_results:
                li_candidates.append({
                    "url": r.get("url", ""),
                    "title": r.get("title", ""),
                    "headline": r.get("content", r.get("body", "")),
                    "company": (r.get("metadata", {}) or {}).get("company", ""),
                    "author": r.get("author", ""),
                    "snippet": r.get("body", ""),
                    "source": "netrows",
                })
            if li_candidates:
                print(f"      Netrows returned {len(li_candidates)} candidate(s)")

        if not li_candidates:
            print(f"      SERP fallback for LinkedIn...")
            li_candidates = _serp_fallback_linkedin(pname, name, rt)
            if li_candidates:
                print(f"      SERP returned {len(li_candidates)} candidate(s)")

        if li_candidates:
            url, verified, verdict = _verify_candidates(li_candidates, pname, name, role, "LinkedIn", rt)
            if verified and url:
                linkedin_url = url
                linkedin_verified = True
                conf = verdict.get("confidence", "?") if verdict else "?"
                if rt:
                    rt.emit(EventType.EVIDENCE, {
                        "claim": f"LinkedIn VERIFIED: {pname} -> {url} ({conf})",
                        "confidence": 0.9 if conf == "high" else 0.7,
                        "entity": "contact_enrichment",
                    }, source="enrichment", company=name)
                print(f"      LinkedIn VERIFIED: {url} ({conf})")
            else:
                reason = verdict.get("reason", "no match") if verdict else "no candidates"
                print(f"      LinkedIn: no match ({reason})")

        x_candidates = []
        if has_intel:
            print(f"      Netrows twitter scan...")
            tw_results = _scan_twitter(pname, name, rt)
            for r in tw_results:
                author = r.get("author", "")
                tweet_url = r.get("url", "")
                profile_url = f"https://x.com/{author}" if author and author != "unknown" else ""
                x_candidates.append({
                    "url": profile_url,
                    "title": f"@{author}" if author else "",
                    "body": r.get("body", r.get("content", "")),
                    "author": author,
                    "snippet": r.get("body", ""),
                    "source": "netrows",
                })
            seen_authors = set()
            deduped = []
            for c in x_candidates:
                a = (c.get("author") or "").lower()
                if a and a not in seen_authors:
                    seen_authors.add(a)
                    deduped.append(c)
            x_candidates = deduped
            if x_candidates:
                print(f"      Netrows returned {len(x_candidates)} candidate(s)")

        if not x_candidates:
            print(f"      SERP fallback for X/Twitter...")
            x_candidates = _serp_fallback_twitter(pname, name, rt)
            if x_candidates:
                print(f"      SERP returned {len(x_candidates)} candidate(s)")

        if x_candidates:
            url, verified, verdict = _verify_candidates(x_candidates, pname, name, role, "X/Twitter", rt)
            if verified and url:
                x_url = url
                x_verified = True
                conf = verdict.get("confidence", "?") if verdict else "?"
                if rt:
                    rt.emit(EventType.EVIDENCE, {
                        "claim": f"X/Twitter VERIFIED: {pname} -> {url} ({conf})",
                        "confidence": 0.85 if conf == "high" else 0.65,
                        "entity": "contact_enrichment",
                    }, source="enrichment", company=name)
                print(f"      X/Twitter VERIFIED: {url} ({conf})")
            else:
                reason = verdict.get("reason", "no match") if verdict else "no candidates"
                print(f"      X/Twitter: no match ({reason})")

        if linkedin_verified and linkedin_url:
            member["linkedin_url"] = linkedin_url
        if x_verified and x_url:
            member["x_url"] = x_url

        status_parts = []
        if linkedin_verified:
            status_parts.append("LinkedIn")
        if x_verified:
            status_parts.append("X")
        if status_parts:
            member["enrichment_status"] = f"Verified: {', '.join(status_parts)}"
        else:
            member["enrichment_status"] = "No verified profiles found"

        time.sleep(0.3)

    verified_count = sum(1 for m in team_members if "Verified" in (m.get("enrichment_status") or ""))
    print(f"    Enrichment complete: {verified_count}/{len(to_enrich)} contacts verified")
    if rt:
        rt.emit(EventType.RESOLUTION, {
            "phase": "enrich", "company": name,
            "enriched": verified_count, "attempted": len(to_enrich),
        }, source="runtime", company=name)

    return team_members


def generate_pdf_dossier(company, team_members, synthesis, profiles_dir, brand_name="MIA", rt=None):
    if not HAS_PDF:
        print(f"    Skipping PDF (fpdf2 not installed)")
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
            safe = content.encode("latin-1", errors="replace").decode("latin-1")
            pdf.multi_cell(0, 5, safe)
        pdf.ln(4)

    def sep():
        pdf.set_draw_color(200, 200, 200)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(4)

    evidence_count = len(rt.ledger.evidence_for(name)) if rt else 0

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
    pdf.cell(0, 8, f"Generated by {brand_name} v3 | {datetime.now().strftime('%B %d, %Y')}", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 10)
    pdf.cell(0, 8, f"Confidence: {company.get('confidence', '?')} | Coverage: {company.get('source_coverage', 'N/A')}", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 6, f"Evidence claims: {evidence_count} | Runtime: deterministic v3", new_x="LMARGIN", new_y="NEXT", align="C")

    pdf.add_page()
    add_section("Executive Summary", synthesis.get("what_they_do", company.get("description", "N/A")), is_header=True)
    sep()

    snapshot = [f"Website: {company.get('website', 'N/A')}", f"LinkedIn: {company.get('linkedin_url', 'N/A')}",
                f"X/Twitter: {company.get('x_url', 'N/A')}", f"Category: {company.get('category', 'N/A')}",
                f"Stage: {synthesis.get('apparent_stage', company.get('stage', 'N/A'))}",
                f"Locations: {company.get('locations', 'N/A')}"]
    add_section("Company Snapshot", "\n".join(snapshot))
    sep()

    add_section("Official Positioning", company.get("messaging_style", "N/A"))
    sep()
    add_section("Public Market Voice", synthesis.get("public_voice", "N/A"))
    sep()
    add_section("Products & Services", company.get("products_services", "N/A"))
    sep()
    add_section("Customer / ICP Inference", company.get("icp", "N/A"))
    sep()

    market = [f"Momentum: {synthesis.get('momentum_indicators', company.get('momentum_summary', 'N/A'))}",
              f"Hiring: {company.get('hiring_signals', 'N/A')}", f"Launches: {company.get('launch_signals', 'N/A')}",
              f"Product Velocity: {company.get('product_velocity', 'N/A')}", f"Ecosystem: {company.get('ecosystem', 'N/A')}",
              f"Partnerships: {company.get('partnerships', 'N/A')}", f"Events: {company.get('event_sponsor_relevance', 'N/A')}"]
    add_section("Market Signals", "\n".join(market))
    sep()

    pdf.add_page()
    add_section("Team & Decision-Maker Overview", "", is_header=True)
    if team_members:
        for m in team_members[:10]:
            lines = [f"Name: {m.get('person_name', 'N/A')}", f"Role: {m.get('role_title', 'N/A')}",
                     f"Category: {m.get('team_category', 'N/A')}"]
            if m.get("linkedin_url"):
                lines.append(f"LinkedIn: {m['linkedin_url']}")
            if m.get("x_url"):
                lines.append(f"X/Twitter: {m['x_url']}")
            if m.get("bio_summary"):
                lines.append(f"Bio: {m['bio_summary']}")
            lines.extend([f"Decision Area: {m.get('likely_decision_area', 'N/A')}",
                          f"Outreach Relevance: {m.get('outreach_relevance', 'N/A')}",
                          f"Confidence: {m.get('confidence_level', 'N/A')}"])
            pdf.set_font("Helvetica", "B", 10)
            safe_p = m.get("person_name", "?").encode("latin-1", errors="replace").decode("latin-1")
            pdf.cell(0, 6, safe_p, new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 9)
            safe_l = "\n".join(lines).encode("latin-1", errors="replace").decode("latin-1")
            pdf.multi_cell(0, 4, safe_l)
            pdf.ln(3)
    else:
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 8, "No team members identified.", new_x="LMARGIN", new_y="NEXT")
    sep()

    contacts = [f"Sponsor: {synthesis.get('best_sponsor_contact', 'Not identified')}",
                f"Sales: {synthesis.get('best_sales_contact', 'Not identified')}",
                f"Partnership: {synthesis.get('best_partnership_contact', 'Not identified')}",
                f"Technical: {synthesis.get('best_technical_contact', 'Not identified')}"]
    add_section("Best Contacts by Use Case", "\n".join(contacts))
    sep()

    add_section("Outreach Angle", synthesis.get("strongest_outreach_angle", company.get("outreach_angle", "N/A")))
    sep()

    pdf.add_page()
    add_section("Confidence Notes", "", is_header=True)
    for key, label in [("observed_facts", "Observed (verified)"), ("inferred_conclusions", "Inferred (likely)"), ("uncertain_areas", "Uncertain (weak)")]:
        items = synthesis.get(key, [])
        if items:
            content = "\n".join(f"- {f}" for f in (items if isinstance(items, list) else [str(items)]))
            add_section(label, content)
    sep()

    if synthesis.get("investigation_notes"):
        notes = synthesis["investigation_notes"]
        if isinstance(notes, list):
            notes = "\n".join(f"- {n}" for n in notes)
        add_section("Brain Investigation Notes", str(notes))
        sep()

    source_lines = [f"Website: {company.get('website', 'N/A')}", f"LinkedIn: {company.get('linkedin_url', 'N/A')}",
                    f"X/Twitter: {company.get('x_url', 'N/A')}"]
    source_urls = company.get("source_urls", "")
    if source_urls:
        for u in source_urls.split(";"):
            u = u.strip()
            if u:
                source_lines.append(f"Source: {u}")
    add_section("Source Appendix", "\n".join(source_lines))

    try:
        pdf.output(pdf_path)
        print(f"    PDF saved: {pdf_path}")
        if rt:
            rt.emit(EventType.MUTATION, {"entity": "artifact", "type": "pdf", "path": pdf_path}, company=name)
        return pdf_path
    except Exception as e:
        print(f"    PDF error: {e}")
        return None


def run(topic, max_companies=10, use_case="general", output_dir=None, brand_name="MIA",
        enrich_only=False, resume_only=False, targets=None, guardrails=None):
    run_id = str(uuid.uuid4())[:8]
    start_time = time.time()
    run_dir = get_run_dir(topic, output_dir)
    paths = get_paths(run_dir)

    if guardrails is None:
        guardrails = GuardrailConfig()

    ledger = Ledger(paths["ledger"])
    rt = Runtime(run_id, ledger, guardrails)

    print(f"\n  MIA v3 — Deterministic Runtime over Streamed Cognition")
    print(f"  Run ID: {run_id}")
    print(f"  Topic: {topic}")
    print(f"  Use case: {use_case}")
    print(f"  Max companies: {max_companies}")
    print(f"  Output: {run_dir}")
    print(f"  Guardrails: min_sources={guardrails.min_sources_for_validation}, "
          f"min_confidence={guardrails.min_confidence_for_extraction}, "
          f"max_brain_iters={guardrails.max_brain_iterations}")
    print()

    rt.emit(EventType.STATUS, {"message": "Runtime initialized", "version": "v3", "run_id": run_id})

    existing_companies = load_csv(paths["companies_csv"])
    existing_team = load_csv(paths["team_csv"])
    rt.companies = existing_companies
    rt.team = existing_team

    existing_keys = set(normalize_name(c.get("name", "")) for c in existing_companies)
    profiled = set(normalize_name(c.get("name", "")) for c in existing_companies if c.get("description"))

    for c in existing_companies:
        rt.confidence_scores[normalize_name(c.get("name", ""))] = c.get("confidence", "low")

    if existing_companies or existing_team:
        print(f"  Resuming: {len(existing_companies)} companies, {len(existing_team)} team, {len(profiled)} profiled")
        progress_report(paths)

    if enrich_only:
        print(f"\n  ENRICH-ONLY MODE")
        if not existing_companies:
            print("  No companies to enrich.")
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
            gathered = brain_gather_context(company, topic, rt)
            company, new_team, synthesis = brain_profile_company(company, gathered, topic, use_case, rt)
            existing_companies[i] = clean_company(company)
            if new_team:
                existing_team.extend(new_team)
                company_team = new_team
            if needs_pdf or needs_intel:
                generate_pdf_dossier(company, company_team or new_team, synthesis, paths["profiles_dir"], brand_name, rt)
            save_csv(paths["companies_csv"], existing_companies, COMPANY_FIELDS)
            save_csv(paths["team_csv"], dedupe_team(existing_team), TEAM_FIELDS)
        progress_report(paths)
        _finish_run(rt, paths, existing_companies, existing_team, {}, start_time, topic, use_case, brand_name, run_id)
        return paths

    targeted = []
    if targets:
        print(f"\n  Targeted companies: {', '.join(targets)}")
        for t in targets:
            if normalize_name(t) not in existing_keys:
                targeted.append({"name": t})
            else:
                print(f"    {t} — already on file.")

    if resume_only and existing_companies:
        print(f"\n  Resume mode: skipping discovery.")
        candidates = targeted
    elif targets and not targeted and existing_companies:
        candidates = []
    elif targets:
        remaining = max(0, max_companies - len(targeted))
        if remaining > 0:
            discovered = discover_companies(topic, remaining, rt)
            discovered = [c for c in discovered if normalize_name(c.get("name", "")) not in existing_keys
                          and normalize_name(c.get("name", "")) not in set(normalize_name(t) for t in targets)]
            candidates = targeted + discovered
        else:
            candidates = targeted
    elif not existing_companies:
        candidates = discover_companies(topic, max_companies, rt)
    else:
        print(f"\n  Searching for new candidates...")
        new_cands = discover_companies(topic, max_companies, rt)
        candidates = [c for c in new_cands if normalize_name(c.get("name", "")) not in existing_keys]
        if candidates:
            print(f"  {len(candidates)} new candidates.")
        else:
            print(f"  No new candidates.")
            candidates = []

    if candidates:
        rt.transition(Phase.VALIDATE)
        validated = []
        for i, candidate in enumerate(candidates):
            if len(validated) >= max_companies:
                break
            name_key = normalize_name(candidate.get("name", ""))
            if name_key in existing_keys:
                continue
            print(f"\n  [{i+1}/{len(candidates)}]", end="")
            result = validate_company(candidate, topic, rt)
            if result["confidence"] == "low":
                print(f"    DROPPED: {result['name']} (insufficient coverage)")
                continue
            validated.append(result)
            existing_keys.add(name_key)
        existing_companies.extend(validated)
        rt.companies = existing_companies
        print(f"\n  Validated {len(validated)} ({len(existing_companies)} total).")

    if len(existing_companies) > max_companies:
        strong = [c for c in existing_companies if c.get("confidence") != "low"]
        weak = [c for c in existing_companies if c.get("confidence") == "low"]
        existing_companies = (strong + weak)[:max_companies]

    save_csv(paths["companies_csv"], existing_companies, COMPANY_FIELDS)
    print(f"\n  Companies saved: {paths['companies_csv']}")

    to_profile = [c for c in existing_companies if normalize_name(c.get("name", "")) not in profiled]
    if not to_profile:
        print(f"\n  All {len(existing_companies)} companies already profiled.")
    else:
        print(f"\n  {len(to_profile)} to profile ({len(existing_companies) - len(to_profile)} done).")

    all_team = list(existing_team)
    all_syntheses = {}

    for i, company in enumerate(to_profile, 1):
        print(f"\n{'='*60}")
        print(f"  [{i}/{len(to_profile)}] Processing: {company.get('name', 'Unknown')}")
        print(f"{'='*60}")

        gathered = brain_gather_context(company, topic, rt)
        company, team_members, synthesis = brain_profile_company(company, gathered, topic, use_case, rt)
        all_syntheses[company.get("name", "")] = synthesis

        team_members = enrich_contacts(team_members, company, rt)

        idx = next((j for j, c in enumerate(existing_companies) if normalize_name(c.get("name", "")) == normalize_name(company.get("name", ""))), None)
        if idx is not None:
            existing_companies[idx] = clean_company(company)

        all_team.extend(team_members)

        if company.get("outreach_angle", "") == "" and synthesis.get("strongest_outreach_angle"):
            company["outreach_angle"] = synthesis["strongest_outreach_angle"]
            if idx is not None:
                existing_companies[idx] = clean_company(company)

        generate_pdf_dossier(company, team_members, synthesis, paths["profiles_dir"], brand_name, rt)

        save_csv(paths["companies_csv"], existing_companies, COMPANY_FIELDS)
        save_csv(paths["team_csv"], dedupe_team(all_team), TEAM_FIELDS)
        rt.save_state(paths["state"])
        time.sleep(0.5)

    all_team = dedupe_team(all_team)
    save_csv(paths["team_csv"], all_team, TEAM_FIELDS)

    for company in existing_companies:
        name = company.get("name", "")
        if name in all_syntheses:
            continue
        name_key = normalize_name(name)
        company_team = [t for t in all_team if normalize_name(t.get("company_name", "")) == name_key]
        if company.get("description") and not os.path.exists(os.path.join(paths["profiles_dir"], f"{company_slug(name)}.pdf")):
            gathered = brain_gather_context(company, topic, rt)
            _, _, synthesis = brain_profile_company(company, gathered, topic, use_case, rt)
            all_syntheses[name] = synthesis
            generate_pdf_dossier(company, company_team, synthesis, paths["profiles_dir"], brand_name, rt)

    _finish_run(rt, paths, existing_companies, all_team, all_syntheses, start_time, topic, use_case, brand_name, run_id)
    return paths


def _finish_run(rt, paths, companies, team, syntheses, start_time, topic, use_case, brand_name, run_id):
    summary = {
        "topic": topic, "use_case": use_case, "generated_at": datetime.now().isoformat(),
        "brand": brand_name, "runtime_version": "v3", "run_id": run_id,
        "total_companies": len(companies), "total_team_members": len(team),
        "runtime_stats": rt.ledger.stats(),
        "companies": [],
    }

    for company in companies:
        name = company.get("name", "")
        syn = syntheses.get(name, {})
        name_key = normalize_name(name)
        ct = [t for t in team if normalize_name(t.get("company_name", "")) == name_key]
        evidence = rt.ledger.evidence_for(name)

        summary["companies"].append({
            "name": name, "website": company.get("website", ""),
            "linkedin": company.get("linkedin_url", ""), "x": company.get("x_url", ""),
            "confidence": company.get("confidence", ""),
            "evidence_claims": len(evidence),
            "best_sponsor_contact": syn.get("best_sponsor_contact", "Not identified"),
            "best_sales_contact": syn.get("best_sales_contact", "Not identified"),
            "best_partnership_contact": syn.get("best_partnership_contact", "Not identified"),
            "best_technical_contact": syn.get("best_technical_contact", "Not identified"),
            "strongest_outreach_angle": syn.get("strongest_outreach_angle", company.get("outreach_angle", "")),
            "team_count": len(ct),
        })

    save_json(paths["summary_json"], summary)
    rt.transition(Phase.COMPLETE)
    rt.save_state(paths["state"])

    elapsed = time.time() - start_time
    progress_report(paths)

    stats = rt.ledger.stats()
    print(f"\n{'='*60}")
    print(f"RUNTIME SUMMARY (v3)")
    print(f"{'='*60}")
    print(f"  Run ID:          {rt.run_id}")
    print(f"  Events:          {stats['total']} ({stats['accepted']} accepted, {stats['rejected']} rejected)")
    print(f"  Evidence claims: {stats['evidence']}")
    print(f"  Brain decisions: {stats['brain_decisions']}")
    print(f"  Tool calls:      {stats['tool_calls']}")
    print(f"  Guard rejects:   {stats['guard_rejects']}")
    print(f"  Phases:          {len(rt.phase_history)}")
    print(f"  Ledger:          {paths['ledger']}")
    print(f"{'='*60}")

    print(f"\n  Time: {elapsed:.1f}s")
    print(f"\n  Output files:")
    print(f"    - {paths['companies_csv']}")
    print(f"    - {paths['team_csv']}")
    print(f"    - {paths['summary_json']}")
    print(f"    - {paths['ledger']}")
    print(f"    - {paths['state']}")
    pdf_count = len([f for f in os.listdir(paths["profiles_dir"]) if f.endswith(".pdf")])
    print(f"    - {paths['profiles_dir']}/ ({pdf_count} PDFs)")
    print(f"{'='*60}\n")


def _daemon_ask(question):
    try:
        return input(f"\n  MIA > {question}\n  You > ").strip()
    except (EOFError, KeyboardInterrupt):
        return ""


def _daemon_llm_parse(user_input, parse_task):
    prompt = f"""The user said: "{user_input}"

{parse_task}

Respond with ONLY a JSON object. No explanation."""
    try:
        resp = _chat_sync([
            {"role": "system", "content": "You parse user input into structured data for a market intelligence tool. Respond with valid JSON only."},
            {"role": "user", "content": prompt},
        ], max_tokens=512)
        return parse_json_response(resp)
    except Exception:
        return None


MIA_BANNER = r"""

    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║    ███╗   ███╗ ██╗  █████╗         ██                        ║
    ║    ████╗ ████║ ██║ ██╔══██╗       ████                       ║
    ║    ██╔████╔██║ ██║ ███████║      ██  ██                      ║
    ║    ██║╚██╔╝██║ ██║ ██╔══██║      ██  ██                      ║
    ║    ██║ ╚═╝ ██║ ██║ ██║  ██║     ██    ██                     ║
    ║    ╚═╝     ╚═╝ ╚═╝ ╚═╝  ╚═╝    ████████                     ║
    ║                                 ██ /\ ██                     ║
    ║    Market Intelligence          ██/  \██                     ║
    ║    Analyst · v3                 █/ () \█                     ║
    ║                                 / \__/ \                     ║
    ║    the girl in the             /   ||   \                    ║
    ║    red dress                  /    ||    \                   ║
    ║                              ██    ||    ██                  ║
    ║    by Interchained LLC        ██   ||   ██                   ║
    ║    powered by AiAS SDK         ██  /\  ██                    ║
    ║                                 ████████                     ║
    ║                                  ██  ██                      ║
    ║                                  ██  ██                      ║
    ║                                 ███  ███                     ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
"""

MIA_INTRO = """
  Hey. I'm MIA — the girl in the red dress.

  While everyone else is distracted, I'm the one who
  already knows who to talk to, what they care about,
  and how to get in the room.

  I find companies. I profile their teams. I verify
  real profiles — LinkedIn, X, the works. I build you
  a dossier with outreach angles that actually land.

  Every claim backed by evidence.
  If I can't verify it, I'll tell you straight.

  So — who are we going after?
"""


def daemon_mode():
    print(MIA_BANNER)
    print(MIA_INTRO)
    print("  Type 'quit' or 'exit' at any time to stop.\n")

    while True:
        raw = _daemon_ask("What market or industry would you like me to research?\n         (e.g. 'AI developer tools', 'fintech payments', 'cloud infrastructure')")
        if raw.lower() in ("quit", "exit", "q"):
            print("\n  Goodbye.\n")
            return
        if not raw:
            print("  I need a topic to research. Try again.")
            continue

        parsed = _daemon_llm_parse(raw, """Extract the research topic/keywords from what the user said.
Return: {"topic": "the core topic keywords", "understood_as": "one-sentence description of what they want to research"}""")

        if parsed and parsed.get("topic"):
            topic = parsed["topic"]
            understood = parsed.get("understood_as", topic)
            print(f"\n  Got it — I'll research: {understood}")
        else:
            topic = raw
            print(f"\n  Got it — researching: {topic}")

        confirm = _daemon_ask(f"Does that sound right? (yes/no)")
        if confirm.lower() in ("no", "n", "nah", "nope"):
            topic = _daemon_ask("OK, what should the topic be?")
            if not topic:
                continue

        raw_uc = _daemon_ask("What's this research for?\n         1. Partnerships (integration, BD, ecosystem)\n         2. Sponsorship (events, brand, community)\n         3. Sales (buying signals, decision-makers)\n         4. General (broad research)")
        uc_map = {"1": "partnerships", "2": "sponsorship", "3": "sales", "4": "general",
                  "partnerships": "partnerships", "sponsorship": "sponsorship",
                  "sales": "sales", "general": "general", "partner": "partnerships",
                  "sponsor": "sponsorship", "bd": "partnerships"}
        use_case = uc_map.get(raw_uc.lower().strip(), "")
        if not use_case:
            parsed_uc = _daemon_llm_parse(raw_uc, """The user described their use case for market research.
Classify it into exactly one of: partnerships, sponsorship, sales, general.
Return: {"use_case": "one of the four options"}""")
            use_case = (parsed_uc or {}).get("use_case", "general")
        print(f"  Use case: {use_case}")

        raw_targets = _daemon_ask("Any specific companies you want me to target?\n         (comma-separated names, or 'no' to let me discover)")
        targets = None
        if raw_targets.lower() not in ("no", "n", "none", "nah", "nope", "skip", ""):
            parsed_t = _daemon_llm_parse(raw_targets, """Extract company names from what the user said.
Return: {"companies": ["Company1", "Company2", ...]}""")
            if parsed_t and parsed_t.get("companies"):
                targets = parsed_t["companies"]
                print(f"  Targeting: {', '.join(targets)}")
            else:
                targets = [t.strip() for t in raw_targets.split(",") if t.strip()]
                if targets:
                    print(f"  Targeting: {', '.join(targets)}")

        raw_max = _daemon_ask("How many companies should I profile? (default: 5)")
        if raw_max.lower() in ("", "default", "skip"):
            max_companies = 5
        else:
            try:
                max_companies = int(raw_max)
                max_companies = max(1, min(max_companies, 50))
            except ValueError:
                parsed_max = _daemon_llm_parse(raw_max, """The user said how many companies they want.
Return: {"count": <integer>}""")
                max_companies = (parsed_max or {}).get("count", 5)
                try:
                    max_companies = int(max_companies)
                except (ValueError, TypeError):
                    max_companies = 5
        print(f"  Max companies: {max_companies}")

        raw_brand = _daemon_ask("What's your brand/company name? (for the PDF dossiers, default: MIA)")
        brand_name = raw_brand if raw_brand and raw_brand.lower() not in ("default", "skip", "") else "MIA"
        print(f"  Brand: {brand_name}")

        raw_dir = _daemon_ask("Output directory? (press Enter for default)")
        output_dir = raw_dir if raw_dir and raw_dir.lower() not in ("default", "skip", "") else None

        print(f"\n  {'='*50}")
        print(f"  READY TO RUN")
        print(f"  {'='*50}")
        print(f"  Topic:         {topic}")
        print(f"  Use case:      {use_case}")
        print(f"  Targets:       {', '.join(targets) if targets else 'Auto-discover'}")
        print(f"  Max companies: {max_companies}")
        print(f"  Brand:         {brand_name}")
        print(f"  Output:        {output_dir or 'default (./runs/)'}")
        print(f"  {'='*50}")

        go = _daemon_ask("Launch the scan? (yes/no)")
        if go.lower() in ("no", "n", "nah", "nope"):
            print("  Skipped. Let's start over.\n")
            continue

        print("\n  Launching...\n")
        run(
            topic=topic,
            max_companies=max_companies,
            use_case=use_case,
            output_dir=output_dir,
            brand_name=brand_name,
            enrich_only=False,
            resume_only=False,
            targets=targets,
        )

        again = _daemon_ask("Run complete! Want to do another scan? (yes/no)")
        if again.lower() in ("no", "n", "nah", "nope", "quit", "exit", "q"):
            print("\n  Thanks for using MIA. Goodbye.\n")
            return
        print("  Let's go again.\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="MIA v3 — Deterministic Runtime over Streamed Cognition. LLM-as-second-brain market intelligence."
    )
    parser.add_argument("keywords", nargs="*", help="Keywords describing the market/topic to research")
    parser.add_argument("--daemon", action="store_true", help="Interactive mode — MIA guides you through setup")
    parser.add_argument("--max-companies", type=int, default=10, help="Max companies to profile (default: 10)")
    parser.add_argument("--use-case", choices=USE_CASES, default="general", help="Outreach use case (default: general)")
    parser.add_argument("--output-dir", type=str, default=None, help="Custom output directory")
    parser.add_argument("--brand-name", type=str, default="MIA", help="Brand name for PDFs (default: MIA)")
    parser.add_argument("--enrich-only", action="store_true", help="Only enrich existing data")
    parser.add_argument("--resume-run", action="store_true", help="Resume previous run, skip discovery")
    parser.add_argument("--targets", type=str, default=None, help="Comma-separated company names to target")
    parser.add_argument("--min-sources", type=int, default=2, help="Min source coverage for validation (default: 2)")
    parser.add_argument("--min-confidence", choices=["low", "partial", "high"], default="partial", help="Min confidence for extraction (default: partial)")
    parser.add_argument("--max-brain-iters", type=int, default=8, help="Max brain iterations per company (default: 8)")

    args = parser.parse_args()

    if args.daemon:
        daemon_mode()
    else:
        if not args.keywords:
            parser.error("keywords are required unless using --daemon mode")

        topic = " ".join(args.keywords)
        targets_list = [t.strip() for t in args.targets.split(",") if t.strip()] if args.targets else None

        gc = GuardrailConfig(
            min_sources_for_validation=args.min_sources,
            min_confidence_for_extraction=args.min_confidence,
            max_brain_iterations=args.max_brain_iters,
        )

        run(topic, max_companies=args.max_companies, use_case=args.use_case,
            output_dir=args.output_dir, brand_name=args.brand_name,
            enrich_only=args.enrich_only, resume_only=args.resume_run,
            targets=targets_list, guardrails=gc)
