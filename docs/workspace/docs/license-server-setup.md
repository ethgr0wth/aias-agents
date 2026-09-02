# AiAS License Server Setup

## Overview

The license server verifies Envato purchase codes and delivers protected core packages to licensed customers.

## Production Deployment

### Required Environment Variables

```bash
# Required
REDIS_URL=redis://your-redis-host:6379
ENVATO_PERSONAL_TOKEN=your-envato-personal-access-token

# Optional
LICENSE_SERVER_PORT=8001          # Default: 8001
SESSION_SECRET=your-session-key   # Auto-generated if not set
PACKAGES_DIR=./packages           # Where core packages are stored
RATE_LIMIT_REQUESTS=10            # Max requests per window
RATE_LIMIT_WINDOW=3600            # Window in seconds (1 hour)
```

### Getting Your Envato Personal Token

1. Go to https://build.envato.com/my-apps/
2. Click "Create Token"
3. Enable these permissions:
   - View your Envato Account username
   - View the user's email address
   - **View the item buyer's purchases** (required for license verification)
4. Copy the token and set as `ENVATO_PERSONAL_TOKEN`

### Running in Production

```bash
# Install dependencies
pip install fastapi uvicorn redis httpx pydantic

# Start server
python license-server/main.py
```

Or with uvicorn directly:

```bash
uvicorn license-server.main:app --host 0.0.0.0 --port 8001
```

### Building Core Packages

Before the server can deliver packages, build them:

```bash
python scripts/build-core-packages.py
```

This creates:
- `license-server/packages/core-services.zip` (10 files)
- `license-server/packages/core-routes.zip` (33 files)
- `license-server/packages/core-providers.zip` (3 files)

---

## Development/Testing Mode

Dev mode bypasses Envato verification for local testing. It requires **triple authentication** to prevent accidental exposure.

### Required Environment Variables (Dev)

```bash
# All production variables PLUS:
DEV_MODE=true                    # Enable dev endpoints
DEV_SECRET=your-secret-pin       # Required secret (you choose this)
```

### How Triple Lock Works

| Layer | What's Checked | Failure Response |
|-------|----------------|------------------|
| 1 | Server `DEV_MODE=true` | 403 "Dev mode not enabled" |
| 2 | Server `DEV_SECRET` configured | 403 "Dev secret not configured" |
| 3 | Request `X-Dev-Secret` header matches | 403 "Invalid dev secret" |

### Installer Configuration (Dev)

The installer also needs these environment variables:

```bash
# Point to local license server
LICENSE_SERVER_URL=http://localhost:8001/v1

# Enable dev mode in installer
DEV_MODE=true
DEV_SECRET=your-secret-pin       # Must match server's DEV_SECRET
```

### Running Locally for Development

**Terminal 1 - License Server:**
```bash
export REDIS_URL=redis://localhost:6379
export DEV_MODE=true
export DEV_SECRET=test123
export PACKAGES_DIR=./license-server/packages

python license-server/main.py
```

**Terminal 2 - PHP Installer:**
```bash
export LICENSE_SERVER_URL=http://localhost:8001/v1
export DEV_MODE=true
export DEV_SECRET=test123

php -S localhost:8080 -t installer
```

### Test Purchase Codes (Dev Only)

In dev mode, any UUID-formatted code works:
```
12345678-1234-1234-1234-123456789012
aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee
```

---

## API Endpoints

### Health Check
```
GET /health
```

### Verify License (Production)
```
POST /v1/license/verify
Content-Type: application/json

{
  "purchase_code": "uuid-from-envato",
  "email": "buyer@example.com",
  "domain": "customer-site.com",
  "timestamp": 1234567890,
  "nonce": "random-string",
  "signature": "hmac-signature"
}
```

### Verify License (Dev Only)
```
POST /v1/license/dev-verify
Content-Type: application/json
X-Dev-Secret: your-secret-pin

{
  "purchase_code": "any-uuid-format",
  "email": "test@test.com",
  "domain": "localhost",
  "timestamp": 1234567890,
  "nonce": "random-string",
  "signature": "hmac-signature"
}
```

### Download Package
```
GET /v1/packages/{package_name}?token={download_token}
```

---

## Security Checklist

Before going live:

- [ ] `ENVATO_PERSONAL_TOKEN` is set and valid
- [ ] `DEV_MODE` is NOT set (or set to `false`)
- [ ] `DEV_SECRET` is NOT set in production
- [ ] Redis is secured and not publicly accessible
- [ ] HTTPS is enabled (use a reverse proxy like nginx)
- [ ] Rate limiting is configured appropriately

---

## Troubleshooting

### "License server not configured"
- Missing `ENVATO_PERSONAL_TOKEN`

### "Purchase code not found"
- Customer entered wrong code
- Code doesn't belong to your Envato account

### "Dev mode not enabled" (403)
- Trying to use `/dev-verify` without `DEV_MODE=true` on server

### "Invalid dev secret" (403)
- `X-Dev-Secret` header doesn't match server's `DEV_SECRET`

### "Storage not available"
- Redis connection failed - check `REDIS_URL`
