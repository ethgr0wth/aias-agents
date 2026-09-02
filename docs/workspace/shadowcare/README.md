# ShadowCare

ShadowCare is a privacy-conscious mental-health support platform with
deployment management, guided intake, moderated AI companion sessions, and
human review of generated replies.

It is built as a FastAPI application with Redis-backed state and a small
TypeScript/Tailwind frontend.

## Important safety note

ShadowCare is a software project, not a medical device or emergency service.
It does not diagnose, prescribe, or replace a licensed clinician. Any
deployment that uses AI-generated replies should include appropriate human
oversight, crisis escalation procedures, privacy notices, and a review of the
laws and regulations that apply to its users.

## Features

- Practitioner/admin deployment management
- Configurable rooms, questionnaires, matchmaking, and companion agents
- Access-code based patient entry
- Live sessions over WebSockets
- Human review workflow for AI-generated drafts
- Signal tracking and session summaries
- Groups, posts, reactions, notifications, and bot APIs
- Redis-backed persistence with no committed application database
- Optional image uploads through ImgBB

## Requirements

- Python 3.11+
- Node.js 22+ and npm
- Redis 6+
- An AiAssist-compatible API key for AI-generated replies (optional for
  development, required for live AI responses)

## Quick start

```bash
cp .env.example .env
# Edit .env and set AUTH_SALT plus the services you plan to use.

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

npm ci
npm run build

python -m uvicorn src.main:app --host 0.0.0.0 --port 5000
```

Or use the production helper:

```bash
./production.sh 5000
```

The app is then available at `http://localhost:5000`.

## Configuration

The application reads `.env` automatically when it starts. Never commit that
file or any production credentials.

| Variable | Required | Purpose |
|---|---:|---|
| `AUTH_SALT` | Yes | Unique random secret used for privacy-preserving identity hashes |
| `DEVNET_REDIS_HOST` | Yes | Redis hostname |
| `DEVNET_REDIS_PORT` | No | Redis port, defaults to `6379` |
| `DEVNET_REDIS_DB` | No | Redis database number, defaults to `12` |
| `AIASSIST_API_KEY` | For AI | Enables AI companion replies |
| `IMGBB_API_KEY` | For uploads | Enables image uploads |
| `HOST` | No | Bind host for `production.sh` |
| `PORT` | No | Bind port for `production.sh` |
| `WORKERS` | No | Uvicorn worker count for `production.sh` |

Generate a salt instead of reusing the example value:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Frontend development

Source files are in `src/frontend`. Rebuild generated browser assets after
editing them:

```bash
npm run build
```

The generated files are served from `src/static`.

## Project layout

```text
shadowcare/
├── src/main.py                 # FastAPI application and core platform routes
├── src/routes_sc.py            # ShadowCare deployment/session API
├── src/services/               # Sessions, agents, signals, and deployment logic
├── src/frontend/               # TypeScript and Tailwind source
├── src/static/                 # Browser assets and media
├── src/templates/              # HTML templates
├── scripts/                    # Administrative utilities
├── production.sh               # Build frontend and run Uvicorn
├── Dockerfile                  # Multi-stage production image
└── .env.example                # Safe configuration template
```

`src_gex/` is retained as an alternate historical runtime snapshot. The
supported entry point for this repository is `src.main:app`.

## Docker

Build and run with a Redis instance available to the container:

```bash
docker build -t shadowcare .
docker run --rm \
  --env-file .env \
  -p 5000:5000 \
  shadowcare
```

Use a managed Redis service or a private Docker network in production. Do not
expose Redis publicly.

## Security and privacy

- Treat Redis as sensitive production data: it may contain profiles,
  conversations, access codes, activity logs, and generated content.
- Use a unique `AUTH_SALT` per environment and rotate it only with a planned
  migration because changing it invalidates identity hashes.
- Keep API keys in the hosting provider's secret store.
- Put the application behind TLS and an access-controlled network.
- Review retention, deletion, consent, and incident-response policies before
  handling real patient data.

Please report security issues privately rather than opening a public issue
with exploit details.

## License

MIT. See [LICENSE](./LICENSE).