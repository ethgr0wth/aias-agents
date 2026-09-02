# AiAS License Server

Production-ready license verification and core package delivery service.

## Features

- Envato purchase code verification
- License activation/deactivation per domain
- Secure package downloads with checksums
- Rate limiting
- Download logging
- Health checks

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `REDIS_URL` | Yes | redis://localhost:6379 | Redis connection string |
| `ENVATO_PERSONAL_TOKEN` | Yes | - | Your Envato API token |
| `SESSION_SECRET` | No | random | Secret for token signing |
| `PACKAGES_DIR` | No | ./packages | Path to package ZIPs |
| `LICENSE_SERVER_PORT` | No | 8001 | Server port |
| `RATE_LIMIT_REQUESTS` | No | 10 | Max requests per window |
| `RATE_LIMIT_WINDOW` | No | 3600 | Rate limit window (seconds) |

## Getting Your Envato Token

1. Go to https://build.envato.com/create-token/
2. Select permissions: `View Your Envato Account Username`, `View the user's items' sales history`
3. Create token and save it securely

## Package Directory Structure

```
packages/
├── core-services.zip    # AI orchestrator, memory, storage
├── core-routes.zip      # Workspaces, quests, PIN routes
└── core-providers.zip   # LLM provider adapters
```

## Running Locally

```bash
cd license-server
pip install -r requirements.txt
export REDIS_URL="redis://localhost:6379"
export ENVATO_PERSONAL_TOKEN="your-token"
python main.py
```

## Running in Replit

1. Set environment variables in Secrets
2. Create a workflow: `cd license-server && python main.py`
3. Or use the main workflow with port 8001

## API Endpoints

### POST /v1/license/verify
Verify purchase code and get download token.

### GET /v1/license/download/{package}
Download core package (requires Bearer token).

### POST /v1/license/deactivate
Deactivate license from a domain.

### GET /v1/license/status/{license_key}
Check license status and activations.

### GET /health
Health check endpoint.

## Redis Keys

Data stored in Redis:
- `license:code:{purchase_code}` - License by purchase code
- `license:key:{license_key}` - License by license key
- `license:downloads` - Download log (last 10k entries)
- `license:ratelimit:{ip}` - Rate limiting counters

## Security Notes

- Rate limited to prevent abuse
- Download tokens expire after 2 hours
- All downloads logged
- HTTPS required in production
