# ServerBuddy

ServerBuddy is a web-based server operations assistant. It combines a
restricted command console, operational tool cards, audit history, and an
AiAssist-powered chat interface behind password, API-key, JWT, rate-limit, and
optional IP-allowlist controls.

## Security warning

ServerBuddy can execute a restricted set of commands on its host. Do not expose
it directly to the public internet. Run it behind TLS, set an IP allowlist,
use a strong unique password and JWT secret, and give the process access only
to directories and tools it actually needs.

## Requirements

- Python 3.11+
- Node.js 20+ and npm
- Redis
- An AiAssist API key for each user

## Quick start

```bash
cp .env.example .env
# Fill SERVERBUDDY_PASSWORD and SERVERBUDDY_JWT_SECRET.

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cd client
npm ci
cd ..

./start.sh
```

Open `http://localhost:8099`.

Generate a JWT secret with:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

## Configuration

| Variable | Required | Purpose |
|---|---:|---|
| `SERVERBUDDY_PASSWORD` | Yes | Shared login password |
| `SERVERBUDDY_JWT_SECRET` | Yes | Signs browser sessions |
| `AIAS_BASE_URL` | Yes | AiAssist-compatible API endpoint |
| `REDIS_URL` | Yes | Authentication cache |
| `SERVERBUDDY_ALLOWED_IPS` | Recommended | Comma-separated source IP allowlist |
| `SERVERBUDDY_SHELL_CWD` | Recommended | Root directory for restricted shell commands |
| `INTERCHAINED_NODE_PATH` | No | Optional node executable |
| `INTERCHAINED_CLI_PATH` | No | Optional CLI executable |
| `INTERCHAINED_WALLETS` | No | JSON array or comma-separated wallet names |

Never commit `.env`. The repository contains no default password or signing
secret and refuses to start without both.

## Architecture

```text
serverBuddy/
├── client/              # React + Vite dashboard
├── server/              # FastAPI API, auth, tools, shell, and audit logic
├── start.sh             # Builds the client and starts Uvicorn
├── Dockerfile
└── .env.example
```

The backend serves the built SPA from `client/dist`.

## Docker

```bash
docker build -t serverbuddy .
docker run --rm --env-file .env -p 8099:8099 serverbuddy
```

Mount only the host paths ServerBuddy must inspect. Avoid mounting the host
root or a Docker socket.

## License

MIT. See [LICENSE](./LICENSE).