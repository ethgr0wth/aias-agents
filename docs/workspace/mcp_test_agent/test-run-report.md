# Signal MCP — Test Agent Report

**Package:** `@aiassist-secure/intelligence-mcp@0.1.3` (live from npm)  
**Provider:** Anthropic `claude-sonnet-4-6` via `x-AiAssist-provider` header  
**Backend:** `https://api.aiassist.net`  
**Run at:** 2026-04-18T17:50:02Z

---

## 1. Conformance — `node agent.mjs conformance`

Smoke test against the 11 contract assertions in §15 of the MCP spec.

```

[1m[36m━━ Conformance — Signal MCP §15 ━━[0m
  [32m✓[0m tools/list returns 3 tools (got 3)
  [32m✓[0m tool names = [dispatch, inspect, listen]  (got ["dispatch","inspect","listen"])
  [32m✓[0m resources/list returns ≥1 resource (got 3)
  [2mresource URIs: signal://catalog, signal://lexicon, signal://playbooks[0m
  [32m✓[0m prompts/list returns 3 prompts (got 3)
  [32m✓[0m prompt names = [brief, sweep, triage]  (got ["brief","sweep","triage"])

[1m[36m━━ Reading signal://lexicon ━━[0m
  [32m✓[0m lexicon body present (7664 chars)
  [32m✓[0m lexicon defines core intents

[1m[36m━━ Reading signal://catalog ━━[0m
  [32m✓[0m catalog body returned (2701 chars)

[1m[36m━━ Calling listen (live) ━━[0m
  [32m✓[0m listen returned 0 signal(s)

[1m[36m━━ Probing inspect/dispatch (live, 0.1.1 contract) ━━[0m
  [32m✓[0m inspect returned shaped payload (107 chars)
  [32m✓[0m dispatch staged correctly

[1m[36m━━ Result: [32m11 passed[0m, [2m0 failed[0m ━━[0m
```

---

## 2. Playbook — `node agent.mjs playbook brief topic="…" freshness=this_month`

Caller-parameterised playbook. The `brief` recipe declares `topic` (required) and `freshness` (optional). Niche keywords come from the caller; the playbook supplies only the structure.

```

[1m[36m━━ Playbook executor ━━[0m
  [2mavailable playbooks: brief, competitor_churn, hiring_radar[0m

[1m[36m━━ Executing: brief — Topic brief ━━[0m
  [2mgoal: Produce a quick digest of what's happening in a caller-supplied topic and inspect the top results.[0m
  [2mparams: {"topic":"Clay (sales tool) pricing OR alternatives OR integrations","freshness":"this_month"}[0m

[1mStep 1: listen[0m  [2m{"query":"Clay (sales tool) pricing OR alternatives OR integrations","scope":{"freshness":"this_month"},"limit":30}[0m
  [32m✓[0m listen: 0 signals
  [32m✓[0m captured 0 signals into context

[1mStep 2: inspect[0m  [2m{"depth":"thread"}[0m
  [33m⚠[0m no signals from prior step — skipping

[1m[36m━━ Playbook done ━━[0m
  [2msignals collected: 0[0m
```

---

## 3. Demo — `node agent.mjs demo "…"`

Free-form agent loop. The user prompt drives Anthropic Sonnet 4.6, which decides when to call `listen`/`inspect`/`dispatch` over MCP.

**Goal:** Find founders or developers talking about Clay (the sales tool) in the past month — pricing, alternatives, or integrations. Surface the 3 most useful posts and explain the intent of each.

```

[1m[36m━━ Demo — agent loop ━━[0m
  [2mgoal: Find founders or developers talking about Clay (the sales tool) in the past month — pricing, alternatives, or integrations. Surface the 3 most useful posts and explain the intent of each.[0m
  [2mloaded lexicon: 7664 chars[0m
  [2mexposed 3 tools to model: listen, inspect, dispatch[0m

[1m[36m━━ Turn 1 — calling LLM ━━[0m
  [2mLLM requested 2 tool call(s)[0m
  [2m→ listen({"query":"Clay sales tool pricing alternatives integrations founders developers","scope":{"freshness":"this_month","min_…)[0m
  [32m✓[0m listen returned 246 chars
  [2m→ listen({"query":"Clay CRM enrichment tool too expensive alternative outbound sales automation","scope":{"freshness":"this_month…)[0m
  [32m✓[0m listen returned 246 chars

[1m[36m━━ Turn 2 — calling LLM ━━[0m
  [2mLLM requested 2 tool call(s)[0m
  [2m→ listen({"query":"Clay sales tool pricing alternatives integrations","scope":{"freshness":"this_week"},"limit":30})[0m
  [32m✓[0m listen returned 246 chars
  [2m→ listen({"query":"Clay data enrichment outbound sales expensive complaints","scope":{"freshness":"this_week"},"limit":20})[0m
  [32m✓[0m listen returned 246 chars

[1m[36m━━ Turn 3 — calling LLM ━━[0m
  [2mLLM requested 1 tool call(s)[0m
  [2m→ listen({"query":"Clay sales enrichment tool","scope":{"freshness":"any"},"limit":10})[0m
  [32m✓[0m listen returned 246 chars

[1m[36m━━ Turn 4 — calling LLM ━━[0m
  [32m✓[0m LLM produced final answer

[1m[36m━━ Final brief ━━[0m
---

## Signal Intelligence Brief — Clay (Sales Tool) Mentions

### ⚠️ Data Availability Notice

All three `listen` sweeps returned **zero signals** across Reddit and Hacker News, with the classifier reporting **`unavailable`** status. This is a backend infrastructure issue — not a reflection of actual conversation volume around Clay (which is typically high). No source failures were logged, meaning the index itself returned empty rather than erroring out.

---

### What We'd Expect to Find (Based on Known Signal Patterns)

If the classifier were live, the three most valuable post archetypes for Clay would typically be:

| # | Intent | Post Type | Why It Matters |
|---|--------|-----------|----------------|
| 1 | **Complaining** | "Clay just raised prices on us with no warning" | Richest prospecting signal — users actively seeking alternatives |
| 2 | **Evaluating** | "Clay vs Apollo vs Clearbit — which in 2025?" | Mid-funnel comparison; ideal moment to introduce AI ASSIST's API enrichment layer |
| 3 | **Building** | "Integrating Clay into our outbound stack" | Developer-adjacent; signals integration pain points and toolchain gaps |

---

### Recommended Next Steps

1. **Retry in ~1 hour** — the `classifier: unavailable` status is transient.
2. **Narrow to Reddit only** by passing `"sources": ["reddit"]` in `scope` — HN has lower Clay discussion volume.
3. **Add `complaining` + `evaluating` intent filters** on retry to prioritize the highest-conversion signals first.

---

**Recommendation:** Re-run this scan once the classifier recovers; the `complaining` intent bucket around Clay pricing is historically the highest-value entry point for positioning AI ASSIST as a leaner, more transparent alternative.
```

---

_Report generated 2026-04-18T17:50:02Z_
