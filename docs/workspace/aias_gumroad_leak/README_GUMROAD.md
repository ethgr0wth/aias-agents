# AiAssist Secure — Gumroad Edition

Thanks for buying. This is the full source for AiAssist Secure, the
security-first AI orchestration platform that powers https://aiassist.net.

You can run it, modify it, white-label it, and sell access to it.
You cannot resell the source itself. Full terms are in `LICENSE`.

────────────────────────────────────────────────────────────────────
## What's in the box

- `api/`            — FastAPI backend (auth, workspaces, AI orchestrator, BYOK,
                      Stripe billing, custom tooling, Quests/KeyStone IDE,
                      flashcards, runtime proxy)
- `client/`         — React + TypeScript + Vite + Tailwind frontend
- `server/`         — Express reverse-proxy / static-file shim
- `shared/`         — Shared TypeScript types and Drizzle ORM schema
- `packages/`       — TypeScript, Python, React, and Vanilla JS SDKs
- `quests-engine/`  — Quests / KeyStone IDE engine (Monaco-based workspace)
- `pin-client/`,
  `pin-clientd/`,
  `pin-proxy/`      — P2P Inference Network (decentralized Ollama marketplace)
- `redProxit/`      — Lightweight redis proxy
- `tools/`          — Code analysis and debugging utilities
- `wordpress-plugin/` — WordPress integration plugin
- `sdk-docs/`,
  `docs/`           — Public developer docs
- `nginx*.conf.example`, `maintenance.html`, `maintenance.cjs`
                    — Production deployment helpers
- `.env.example`    — Template for the environment variables you need to set

What is intentionally NOT in the box (you supply your own):
- `.env` with real keys
- Production databases (Postgres dump, Redis `dump.rdb`, `appendonlydir/`)
- Build outputs (`dist*`, `node_modules`, `venv`)
- Internal git history

────────────────────────────────────────────────────────────────────
## Requirements

- Node.js 20+
- Python 3.11+
- Redis 7+
- PostgreSQL 14+ (optional today; required if you want the Drizzle path)
- A Stripe account (for the subscription system)
- At least one LLM provider key (Groq, OpenAI, Anthropic, Gemini, or Mistral)

────────────────────────────────────────────────────────────────────
## Quick start

1. Copy the env template and fill in real values:

       cp .env.example .env
       # then edit .env

2. Install dependencies:

       npm install
       pip install -r requirements.txt
       # or: pip install -e .   (uses pyproject.toml)

3. Start Redis locally (or point `REDIS_URL` at a managed instance):

       redis-server

4. Boot the stack:

       bash start.sh

   This launches the FastAPI backend (`run_api.py`) and the Vite frontend.

5. Open the app and create the first admin user via the signup flow.

────────────────────────────────────────────────────────────────────
## Environment variables

See `.env.example` for the full list. The critical ones:

| Key                          | What it does                                   |
| ---------------------------- | ---------------------------------------------- |
| `SESSION_SECRET`             | Cookie signing — generate a random 64-char hex |
| `MESSAGE_ROOT_KEY`           | Root key for admin-blind message encryption    |
| `REDIS_NAMESPACE`            | Prefix for all Redis keys (use one per env)    |
| `STRIPE_SECRET_KEY`          | Stripe server-side key                         |
| `STRIPE_PUBLISHABLE_KEY`     | Stripe client-side key                         |
| `STRIPE_WEBHOOK_SECRET`      | `whsec_...` from the Stripe CLI / dashboard    |
| `GROQ_API_KEY`               | Default BYOK fallback provider                 |
| `GOOGLE_TTS_API_KEY`         | Optional — only if you enable voice           |
| `RUNTIME_REMOTE_URL`         | URL of the Server B runtime sandbox            |
| `RUNTIME_SHARED_SECRET`      | HMAC secret shared with Server B               |
| `AIAS_API_KEY`               | Default API key used by some internal tools    |

────────────────────────────────────────────────────────────────────
## White-labeling

You are allowed to rebrand. Things to change:

- `client/index.html`                 — title, meta tags, favicon
- `client/src/` brand strings, logos  — search for "AiAssist" and replace
- `client/public/`                    — replace logo/icon assets
- `LICENSE`                           — leave intact (this is required)

────────────────────────────────────────────────────────────────────
## What the license allows

- Run it for yourself or your customers
- Modify, fork, extend it
- White-label and sell access / subscriptions to it
- Build paid upsells, add-ons, integrations on top

## What it does NOT allow

- Reselling, mirroring, or redistributing the source code itself
- Repackaging it as a "starter kit" / "boilerplate" / source bundle
- Reselling AiAssist as a competing source product

Full terms: `LICENSE`. Questions: dev@interchained.org

────────────────────────────────────────────────────────────────────
## Support

This is a source-code product, not a managed service. Support is
best-effort by email at dev@interchained.org. For implementation
help, custom deployment, or OEM terms, reach out for a quote.
