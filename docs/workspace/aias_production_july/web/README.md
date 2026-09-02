# AiAssist — Web Client (Portal-based)

A new, lean web client for the AiAssist platform, built on the
[Portal](https://github.com/interchained/portal) framework. Replaces the
legacy `client/` Vite app.

## Why a new client

The legacy client bundled three.js, monaco, puppeteer, and three dashboard
versions into a heavy SPA. This client is a clean rebuild:

- **Portal framework** — file-based routing, living app contract
  (`app.contract.ts`), `PortalProvider`, server-renderable.
- **Lean by default** — only the surfaces we need, code-split per route,
  no heavyweight editors or 3D unless a feature demands it.
- **Consumes the backend as-is** — no server-side state in the client. Auth
  is FastAPI session cookies; the public integration API uses Bearer `aai_`
  keys. Socket.IO powers realtime.

## Surfaces

| Surface | Routes | Plane |
|---------|--------|-------|
| Public marketing | `/`, `/pricing`, `/docs`, `/blog`, `/blog/:slug`, `/login`, `/register`, `/recover` | Portal SSR-able |
| End-user app | `/app/*` (dashboard, workspaces, playground, agents, templates, code, keystone, runtime, flashcards, image, voice, pin, tools, providers, api-keys, settings, directives) | Authenticated SPA |
| Admin / operator | `/admin/*` (dashboard, users, organizations, licenses, seats, subscriptions, pricing, resellers, payouts, control-center, operator console) | Admin-gated SPA |

## Stack

- React 18 + TypeScript
- Vite 5
- Tailwind CSS
- `@tanstack/react-query` for server state
- `socket.io-client` for realtime (`/client` + `/admin` namespaces)
- Vendored Portal packages (`@interchained/portal-*`) under `vendor/portal/`

## Getting started

```bash
cd web
npm install
npm run dev        # Vite dev server on :5173, proxies /api + /socket.io to :5000
```

The dev server proxies `/api`, `/v1`, `/invite`, `/socket.io`, `/docs`,
`/redoc`, `/openapi.json` to `http://localhost:5000` (the Express host),
which itself proxies to FastAPI on `:8000`. Override with
`AIAS_API_TARGET=http://host:port`.

## Build

```bash
npm run build      # tsc typecheck + vite build -> dist/
npm run preview    # preview the production build
npm run typecheck  # tsc --noEmit
```

## Vendored Portal packages

`@interchained/portal-*` is not yet published to npm. The three runtime
packages are vendored under `vendor/portal/` with their built `dist/`:

- `portal-contract` — `defineApp`, `AppContract` types
- `portal-core` — Vite plugin (`@portal/routes`, `@portal/contract` virtual modules)
- `portal-react` — `PortalProvider`, `Router`, `Link`, `Head`, hooks

Vite aliases resolve these to the vendored `dist/`. To upgrade Portal,
re-copy from `github.com/interchained/portal` and rebuild the packages.

## Auth model

- **Session cookie** (default) — `credentials: "include"` on every request.
  `/api/auth/me` checks state; `/api/auth/login`, `/api/auth/verify-2fa`,
  `/api/auth/logout` manage the cycle.
- **Bearer `aai_` key** — for `/v1/*` integration calls. Pass via
  `api.post(..., { bearerToken })`.
- **Admin** — session cookie + `role: admin|super_admin`. `AdminLayout`
  guards `/admin/*`.

## Socket.IO realtime

`src/lib/realtime.ts` wraps two namespaces, both snake_case:

- `/client` — `join_workspace`, `send_message`, `typing_start/stop`,
  `typing_preview`; receives `message_new`, `typing_indicator`,
  `awaiting_approval`.
- `/admin` — `subscribe_dashboard`, `subscribe_workspace`, `send_as_ai`,
  `change_mode` (`ai|shadow|takeover`), `inject_directive`; receives
  `workspace_list`, `message_new`, `client_presence`, `draft_created`,
  `client_typing`, `typing_preview`.

## Runtime contract

The runtime page honors the PR #34 fail-closed contract: every `run_code`
call carries `environment_id`; a 409 is treated as
destroy-session-recreate-retry.

## Deploy

The built `dist/` is served same-origin by the existing Express host
(`server/index.ts`), which proxies `/api`, `/v1`, `/socket.io` to FastAPI.
No separate process needed — point the Express static handler at `web/dist`
in production.
