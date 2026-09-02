# Signal Command Intelligence Workstation

## What & Why
Build a standalone marketing intelligence workstation that scans Reddit for leads using the published `aiassist-secure-intelligence-signal` PyPI package. Sci-fi command-center aesthetic meets professional data workstation. Follows the same standalone app pattern as `image-workstation/`. Signals stored in localStorage, exportable to CSV. API key passed per-request from frontend (no server-side storage).

## Done looks like
- `signal-command/` directory with FastAPI backend (port 5003) and Vite + React + TypeScript + Tailwind v3 frontend (port 5004)
- Backend is a thin proxy: `POST /api/scan` accepts API key + config, calls the SDK, returns signals. `GET /api/sources` returns available sources.
- Dashboard with sci-fi aesthetic: deep black base (#06060c), electric cyan (#00e5ff) accent, magenta (#ff2d7b) for high-intent alerts
- Layout: Top Command Bar, Scan Control Panel (left sidebar), Signal Feed (center), Intel Summary Panel (right sidebar), Action Bar (bottom)
- Scan controls: API key input, keywords, exclude keywords, subreddit tags, mode toggle (LEAD/SEO), intent score slider, scan limit, auto-poll interval
- Signal cards with intent score badges, category pills, color-coded border glow, expand for full content
- Stats panel: total signals, average intent score, intent category breakdown, top subreddits, scan history
- CSV export (selected or all), localStorage persistence for signals and config
- Auto-polling at configurable intervals
- Replit workflow "Signal Command" starts both backend and frontend

## Out of scope
- Database persistence (localStorage only)
- User authentication (API key per-request)
- Server-side signal caching
- Mobile-first layout (desktop-first, responsive to tablet)

## Tasks
1. **Scaffold backend** — Create `signal-command/api/main.py` FastAPI server on port 5003. Install `aiassist-secure-intelligence-signal` pip package. Implement `POST /api/scan` and `GET /api/sources` endpoints.

2. **Scaffold frontend** — Create Vite + React + TypeScript + Tailwind v3 app matching `image-workstation/` pattern. Port 5004, proxy `/api` to localhost:5003.

3. **Build the dashboard UI** — Full sci-fi command center layout with all five sections (command bar, scan panel, signal feed, intel summary, action bar). Framer Motion animations, CSS glow effects, scan-line overlay.

4. **Wire frontend to backend + localStorage** — Connect scan controls to API, store signals in localStorage with deduplication, auto-polling, stats calculation, CSV export, config persistence.

5. **Add workflow and finalize** — Create Replit workflow, update replit.md, end-to-end verification.

## Relevant files
- `image-workstation/` (reference pattern for standalone app structure)
- `image-workstation/vite.config.ts`
- `image-workstation/package.json`
- `image-workstation/tailwind.config.js`
