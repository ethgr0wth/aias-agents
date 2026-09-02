# NEDB Migration — Slice 6 Triage (per-domain verdicts)

Criteria: **native** when a domain has entity hashes with secondary-access
patterns (field lookups, derived index sets, N+1 hydration) — the engine's
indexes earn their keep. **verbatim-forever** when it's honest KV/config
accessed only by exact key: a value blob's native shape IS a value doc;
reshaping it buys nothing. **native-later** when it earns native but has
structure that deserves a focused PR (ordered sub-collections, mixed shapes).

| Domain | Verdict | Rationale |
|---|---|---|
| envs (entity + slug ptr) | **native (this PR)** | Entity hash; compound lookup `envs:slug:{license}:{slug}` → WHERE license_id AND slug; members/workspaces sets already died (slice 5) |
| drafts | **native (this PR)** | Entity + two sets, both fully derived: approved/rejected drafts are DELETED, so existence == pending; ws set == workspace_id field |
| playground | **native-later** | Earns it (session entity + user set) but carries FOUR ordered sub-collections per session (:messages/:attachments/:directives/:knowledge) — ordered content deserves its own read + PR, not a drive-by |
| tools / tool_secrets / tool_invocations / tool_policy | **native-later** | Mixed shapes (public catalog set, org sets, per-workspace hashes); tool_secrets is ciphertext-at-rest — moves verbatim inside whatever shape lands |
| api_keys_ext + org/user sets + api_key_usage | **native-later** | Classic entity+derived-sets; usage counters need the counter decision (in-memory vs docs) made with the rate-limit domain |
| provider_credentials + org set / user_providers | **native-later** | Entity+derived; BYOK Fernet ciphertext rides verbatim regardless of shape |
| training_contexts / deployed_agents / directives | **native-later** | Entity+org/owner sets; mechanical once read |
| resellers / reseller_leads / conversions / ref_links / payout_claims / leads / contacts | **native-later** | CRM cluster; entity hashes with list/set indexes; low heat, batch into one PR |
| blogs cluster (blog_posts, blog_domains, widgets, slugs, posts, generations…) | **native-later** | Publishing entities with slug pointers; self-contained domain, one PR |
| subscriptions / subscription / plans / quotas / batches | **native-later** | Billing-adjacent entities; migrate with care alongside the divergent user pointers consolidation |
| user_settings / model_prefs | **verbatim-forever** | Per-user config blobs, exact-key access only |
| pin:config / pin:metrics / pin:models / pin:operators / pin:nodes / pin:jobs | **pin operational cluster — native-later** | Money already native (slice 2); ops/registry cluster is heartbeat+TTL heavy, own PR |
| usage / usage_log / groq_usage / api_key_ip / api_key_ip_block / rate_limit | **verbatim-forever (rate_limit: in-memory candidate)** | Counters + logs, exact-key; rate limits may leave storage entirely post-cutover (middleware counters) |
| invite_used_ips / org_smtp / workspace_customization / worker / templates / template / model / provider / post_slug / domain_hostname | **verbatim-forever** | Exact-key config/flags; no secondary access found |
| user (singular) / org (singular) / organizations | **verbatim until consolidation** | Codebase inconsistencies (duplicate prefixes); merging is the post-cutover consolidation pass, not migration |
| users:{id}:subscription/license/organization pointers | **verbatim until consolidation** | Written on separate code paths; can diverge from hash fields (slice 4 finding) |

Every verbatim domain remains fully migrated (lossless fallback shape) and
reachable through the adapter's `_vget/_vhset/_vkv` helpers — "verbatim" is a
shape verdict, never a data-loss verdict.

---

## §4 closure — the client seam (2026-07-11, post-handoff)

The handoff's one cutover blocker (direct-Redis callers bypassing the storage
singleton — the source of the dry run's "unknown prefixes") is CLOSED at the
client factory, not per call site:

- `api/config.py:get_redis()` now honors `AIAS_STORAGE_BACKEND` exactly like
  the storage seam: `nedb` returns a process-wide `RedisOnNedb` singleton, so
  all ~110 direct call sites (routes/services/workers) ride the same backend.
  Future direct callers inherit the seam for free.
- `api/routes/tts.py` no longer builds its own `redis.from_url` client — its
  `get_redis_client()` delegates to the config factory (tts keys are
  unnamespaced; `_norm` passes them through unchanged).
- Shim gaps used by direct callers were added to `RedisOnNedb`: `hsetnx`
  (create-once via `_rmw` CAS — KMS TMK/DEK wrap; race-tested, exactly one
  winner), `lrem` (full count 0/+N/−N semantics), `zrangebyscore`
  (−inf/+inf/exclusive `(x` bounds), `zrange(desc=True)` (inherited
  `get_subscription_events` calls it — was a TypeError on flip), `xlen`
  (kms encryption-status audit count — silently reported 0 before), and
  `pipeline(transaction=...)` accepts the kwarg kms_service passes (was a
  TypeError on flip). `ping()` fixed to hit nedbd `/health` via
  `NedbdClient._req` (NedbdClient never had `health()`; main.py's health
  check would have crashed on flip). `incrby`/`hincrby`/`hincrbyfloat` now
  return the committed (last-attempt) value under CAS retry, not the first.
- Pipeline semantics documented honestly: redis-py pipelines ARE MULTI/EXEC
  by default; the shim replays op-by-op with per-op CAS. Callers are
  idempotent batch writers (webhooks, subscription sweeps) that self-heal on
  the next pass — no lost updates, no split brain.
- Suites: shim now 42 checks (P9 gap primitives + P10 the client seam);
  board 13/23/25/33/18/15/6/42 = 175 green. Coverage unchanged:
  native 38 · inherited 361 · missing 0.

Stale copies (`redis_storage_broken/_stable/_stable_march/_v11`,
`*_stable` route/service files) are NOT imported anywhere and were left
untouched — they still reference `register_script` but never load.

### Dry-run inventory closed (2026-07-11, same day)

Mark's prod dry-run flagged 15 "unknown prefixes" — exactly the direct-writer
keys traced above. `nedb_backfill.py` now knows them:

- `DIRECT_WRITER_PREFIXES` (14 prefixes: aai, ai_change_log, ai_templates,
  audit_events, encryption, fc, platform, pricing, quests, snapshot,
  user_generations, user_snapshots, user_templates, web_search_usage) is
  unioned into `KNOWN_PREFIXES`, each documented at the definition site.
  They migrate verbatim (first segment = collection) — correct for
  exact-key config/log/entity blobs; a re-run of --dry-run reports them
  as expected collections, not surprises.
- `_unrouted` stays flagged on purpose, and dry-run now PRINTS the actual
  keys (first 20). These are colonless global keys (`usage_users`,
  `reserved_blog_slugs`, `audit`, ...). Parity verified: backfill
  `route()` and shim `_coll_of()` both map colonless keys to the
  `_unrouted` collection, so they migrate losslessly AND remain readable
  through the shim post-flip.
- Backfill suite still 13/13 after the change.

### The six _unrouted keys, verified one by one (prod dry-run 2026-07-11)

Mark's re-run flagged exactly 6 `_unrouted` keys: `audit`,
`system_templates`, `reseller_program_config`, `invite_used_ips`,
`reserved_blog_slugs`, `usage_users`. All colonless global singletons;
each one is traced and safe:

- **Read-path parity is exact**: verbatim backfill writes
  `(coll=_unrouted, id=key_s, doc.key=key_s)`; shim `_get` does
  `get_doc(_coll_of(key_s), key_s)` — same coll, same id. Proven live
  with a colonless set/get/delete round-trip against nedbd.
- `audit` (colonless) is a **write-only** stream: xadd'd by
  `record_audit_event` (redis_storage:1615), read by nothing — grep of
  all xrange/xrevrange/xlen callers confirms. The REAL audit log is
  `audit:stream` (colon key → coll `audit`), and nedb_atomic's native
  `_audit()` writes the identical shape (coll `audit`, key
  `audit:stream`, id `audit:stream:{eid}`) as the shim's inherited
  xadd — the two audit writers already agree; no split brain.
- `system_templates` (templates route), `reseller_program_config`
  (hash), `invite_used_ips` (set — the colonless twin of the known
  prefixed variant), `reserved_blog_slugs` (set), `usage_users` (set):
  exact-key access via inherited RedisStorage bodies → shim → the same
  `_unrouted` docs the backfill creates.

Verdict: the dry-run report is CLEAN. `_unrouted 6` is informational,
not a blocker — proceed with the runbook (real run, --verify, boot
smoke, freeze-window flip).
