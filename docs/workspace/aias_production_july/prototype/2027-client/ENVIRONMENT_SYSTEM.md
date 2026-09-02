# Environment System — 2027 Client (Environment-Bound)

> Environments are not a setting. They are where you live.

---

## 1. The Leak We Fix

march_2026:

- `file_root = data/quests/{org_id}/{env_id}/` on disk but never shown — users don't know where code lives
- `ENV_LIMITS = {free:0, basic:1, pro:5, enterprise:100}` hits as surprise 403 Environment limit reached
- `.quests/project-state.json {selectedAgentName, selectedModelURI, promptDraft, migration via migrateModelURI}` — exists but not surfaced
- `preview_port` optional, assigned via PortManager random but no health indicator
- Sync: `QuestsFileService.sync_workspace tar.gz exclude .git node_modules __pycache__ .venv venv` → secure extract skip symlinks/dev absolute/.. ensures target.startswith workspace+sep counting files — invisible to user, no progress bar
- Commit manager debounce 10s `threading.Timer mark_dirty → _fire_commit proxy POST sessions/{id}/commit_workspace` — auto-commits but no timeline
- PR #34 gating: sessions carry `environment_id` binding set at create_session; omit or mismatch → 409 runtime environment does not match session binding / has no environment binding; missing workspace → 409 sync the environment before execution — client previously crashed, fixed in Keystone Lite e42637a via destroy-recreate-retry but not in main web
- Bare repos `runtime_root/git/<sid>/repo.git` never GC — leak forever disk growth no cleanup path — prod risk
- Stack detection `package.json requirements.txt pyproject.toml Pipfile Dockerfile` → auto `npm ci if frozen_lockfile && package-lock else install --cache <shared> --prefer-offline fcntl lock 180s` — runs but no UI
- Venv cascade `python3 -m venv → --without-pip → ensurepip --upgrade → bootstrap urllib get-pip.py fallback checks python3/python bin existence` — fragile but invisible
- File root isolation org-scoped via Redis `quests:org:{org}:envs` + `quests:user:{user}:envs`

2027: Environment Deck

---

## 2. EnvironmentDeck Model

```ts
interface EnvironmentRecord {
  id: string
  org_id: string
  user_id: string
  name: string
  description: string
  template_id: "react-vite" | "next-app" | "node-express" | "python-fastapi" | "blank" | string // + registry templates basic angular astro htmx nextjs nuxt micro-chatbot ai-chess chat-with-files prompt-library empty
  status: "active" | "paused" | "expired"
  llm_provider?: string
  llm_model?: string
  preview_port?: number
  preview_health: "unknown" | "healthy" | "unhealthy" | "starting"
  file_root: string // data/quests/{org}/{env}
  project_state: {
    selectedAgentName: "app-builder" | "chat"
    selectedModelURI: string // migrateModelURI handles old URIs
    promptDraft: string // 50k max
  }
  created_at: string
  updated_at: string
  file_count: number // max 1000 per QuestsSecurityPolicy.MAX_FILES_PER_ENV
  total_bytes: number
  git_head?: string
  git_branch: string // default main
  sync: {
    status: "idle" | "packing" | "uploading" | "extracting" | "committing" | "error"
    progress: number // 0-100
    exclude: [".git", "node_modules", "__pycache__", ".git", "venv", ".venv"] // QuestsFileService + zip exclude
    debounce_ms: 10000 // workspace_commit_manager
    last_sync: string
    last_commit: string
    commit_message?: string
    diff_stats?: { added: number, modified: number, deleted: number }
    timeline: Array<{ commit: string, message: string, time: string, author: "AiAS", files: string[] }>
    fast_path_used: boolean // checkout_from_previous_bare git clone --bare prev→new checkout first branch or HEAD for same org:user:env
  }
  stack: {
    detected: Array<"package.json" | "requirements.txt" | "pyproject.toml" | "Pipfile" | "Dockerfile">
    node: { lock: "package-lock.json" | null, frozen: boolean, cache: "shared/npm-cache", fcntl_lock: ".cache.lock", status: "idle" | "installing" | "installed" | "error" }
    python: { requirements: string, cache: "shared/pip-cache", venv_cascade: ["python3 -m venv", "--without-pip", "ensurepip --upgrade", "urllib get-pip.py"], status: "idle" | "creating-venv" | "installing" | "installed" | "error" }
  }
  limits: {
    max_files: 1000
    max_file_size: 50 * 1024 * 1024
    max_content: 5 * 1024 * 1024
    current_files: number
    meter: number // 0-100
  }
  binding: {
    session_id: string
    environment_id: string // mandatory PR #34
    runtime_root: "/tmp/runtime_b"
    zones: ["workspaces", "tmp", "output", "cache", "readonly-base", "artifacts", "git"]
    ttl: 3600
    grace: 1800
    cleanup_interval: 120
    bare_leak_warning: boolean // git/<sid>/repo.git never GC
  }
}

interface EnvLimitMeter {
  plan: "free" | "basic" | "pro" | "enterprise"
  limits: { free: 0, basic: 1, pro: 5, enterprise: 100 }
  current: number
  meter: number // current/limit *100 or Infinity if free 0
  upgrade_target: "basic" | "pro" | "enterprise"
  message: string // "Environment limit reached (1). Upgrade your plan for more."
}
```

---

## 3. UX — Env Deck

```
┌─ Environments (2/5) [████▒▒] pro — 3 more before upgrade ───┐
│ [+ New] [Import GitHub] [Template Gallery registry/]          │
├───────────────────────────────────────────────────────────────┤
│ ● my-react-app [react-vite] ● active | file_root data/quests/o123/e456 | files 87/1000 12MB/50MB
│   preview :5173 ● healthy [Open preview /quests-preview/e456]
│   stack: package.json ✓ node deps installing --cache shared ▼
│   venv: idle                                                  │
│   sync: ● idle last 2m ago [Timeline 3 commits] commit_msg Add nav + apply EditFile surgical
│                               diff +12 -3 files src/App.tsx src/components/Nav.tsx
│   project_state: app-builder | claude-3.5-sonnet | draft 12/50000 chars
│   binding: session abc123 ↔ env e456 ✓ env_id present (PR#34) ttl 3600 grace 1800 cleanup 120s
│   bare: git/abc123/repo.git 241MB ⚠ leak — GC cron scheduled nightly
│   actions: [Open IDE] [Sync now] [Diff] [Download zip exclude node_modules] [Delete]
│ ───────────────────────────────────────────────────────────── │
│ ○ my-python-api [python-fastapi] ○ paused | file_root data/quests/o123/e789 | stack requirements.txt
│   python cascade: python3 -m venv → ensurepip → get-pip.py ✓ venv ready
│   etc...
└───────────────────────────────────────────────────────────────┘
```

- **New env**: dialog name desc template_id select from 5 builtins + registry submodule live copy `quests-engine/registry` (basic angular astro etc) — `_create_builtin_template writes index.html/js/etc`. Plan gated check `count_environments_by_org(org) >= limit` → 403 with meter.
- **Import GitHub**: url validation `GITHUB_URL_PATTERN ^https?://github.com/{owner}/{repo}(?:.git)?`, branch default main, subdir target — clones via `QuestsFileService.github_clone`.
- **Sync status live**: packing → uploading (tar.gz size) → extracting secure reject symlinks/dev → committing diff stats — uses SSE or WS, not silent.
- **Commit timeline**: `workspace_diff git add -A diff --cached --quiet commit AiAS author` — list with files added/modified/deleted, click to view diff, diff preview unified via `generate_diff_preview`.
- **Fast path indicator**: when `env_last_session org:user:env TTL7d` hit, shows 🚀 `checkout_from_previous_bare git clone --bare prev→new checkout first branch or HEAD` — bootstrap 10x faster.
- **Stack indicator**: detect `package.json` → show `npm ci if frozen_lockfile && package-lock else install --cache <shared> --prefer-offline fcntl lock 180s` progress; `requirements.txt` → venv cascade progress; Dockerfile → not yet auto build warning.
- **409 recovery**: toast `Environment binding mismatch (409) — destroying stale session {sid} + recreating + re-syncing` auto, no data loss file_root persists, session ephemeral lost on restart note shown.
- **Limit meter**: bar with free 0 (no envs) → upgrade CTA basic 1 (1 env) etc.

---

## 4. Runtime Binding (PR #34) — How 2027 Client Handles

```ts
async function run_code_with_binding(session_id, env_id, code, cwd): Promise<Result> {
  // every run_code must include environment_id per PR #34
  try {
    return await proxy.POST("/api/runtime/run_code", { session_id, environment_id: env_id, code, cwd })
  } catch (e) {
    if (e.status === 409 && e.message.includes("does not match session binding")) {
      // stale session from previous env
      toast.warning(`Env binding mismatch (session ${session_id} ↔ env ${env_id}). Recreating...`)
      await proxy.DELETE(`/api/runtime/sessions/${session_id}`)
      const newSession = await proxy.POST(`/api/runtime/sessions`, { policy, environment_id: env_id })
      // re-sync workspace tar from file_root via QuestsFileService sync
      await sync_workspace_from_tar(file_root, newSession.session_id)
      // retry once
      return await proxy.POST("/api/runtime/run_code", { session_id: newSession.session_id, environment_id: env_id, code, cwd })
    }
    if (e.status === 409 && e.message.includes("has no environment binding")) {
      // unbound session + env-bearing request
      await proxy.POST(`/api/runtime/sessions/${session_id}/bind`, { environment_id: env_id }) // or destroy/recreate pattern
      throw e
    }
    if (e.status === 409 && e.message.includes("sync the environment before execution")) {
      await sync_workspace_from_tar(file_root, session_id)
      return await proxy.POST("/api/runtime/run_code", { session_id, environment_id: env_id, code, cwd })
    }
    throw e
  }
}
```

- Header `environment_id` also in `X-Runtime-Context JSON{user_id, org_id}` HMAC payload `METHOD:PATH:BODY+TIMESTAMP+NONCE[:CONTEXT]` — must be included in signing.

---

## 5. GC Admin

- Bare leak `git/<sid>/repo.git` never GC → disk growth linear with sessions — prod needs cron `find $RUNTIME_ROOT/git -type d -name "*.git" -mtime +7 -size +100M` → archive S3 + delete + alert
- 2027 shows warning when `runtime.cache.status()` sizes MB via rglob file counts > threshold
- Cleanup loop visualization: session_meta TTL 3600 expiry → get_expired_sessions still in active set but meta missing → cleanup preserve bare + set_grace TTL grace_seconds → later grace expires → get_grace_expired_sessions → cleanup_disk + remove from active set — diagram in UI as timeline

---

See ARCHITECTURE.md §2.2 + README env awareness
