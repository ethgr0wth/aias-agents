# AiAS License Server API Specification

## Overview

The license server (`api.aiassist.net`) handles Envato purchase code verification, license activation, and proprietary core package delivery. This is a separate service you host to protect your intellectual property.

## Base URL

```
https://api.aiassist.net/v1
```

## Authentication

All requests from installers include:
- `X-Installer-Version`: Installer version (e.g., "1.0.0")
- Request body includes HMAC signature for verification

---

## Endpoints

### POST /license/verify

Validates an Envato purchase code and returns a download token.

**Request:**
```json
{
  "purchase_code": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
  "email": "buyer@example.com",
  "domain": "client-site.com",
  "timestamp": 1705420800,
  "nonce": "random32charhex",
  "signature": "hmac-sha256-signature"
}
```

**Response (Success):**
```json
{
  "valid": true,
  "license_key": "AIAS-XXXX-XXXX-XXXX",
  "download_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "features": ["quests", "blog", "pin", "memory", "shadow_mode"],
  "support_until": "2027-01-16",
  "allowed_domains": 1,
  "activations_used": 1,
  "activations_limit": 1
}
```

**Response (Failure):**
```json
{
  "valid": false,
  "message": "Purchase code already activated on another domain"
}
```

**Error Codes:**
| Code | Message |
|------|---------|
| `invalid_code` | Purchase code not found |
| `already_activated` | Code already used on another domain |
| `expired_support` | Support period expired, cannot download updates |
| `invalid_email` | Email doesn't match purchase record |
| `rate_limited` | Too many attempts, try again later |

---

### GET /license/download/:package

Downloads a proprietary core package. Requires valid download token.

**Headers:**
```
Authorization: Bearer <download_token>
Accept: application/zip
```

**Packages:**
- `core-services` - AI orchestrator, memory, storage
- `core-routes` - Workspaces, quests, PIN, webhooks
- `core-providers` - LLM provider adapters

**Response:**
- Content-Type: `application/zip`
- X-Checksum-SHA256: `<sha256-hash-of-content>`
- Body: ZIP file binary

**Errors:**
```json
{
  "error": "token_expired",
  "message": "Download token has expired. Please re-verify license."
}
```

---

### POST /license/deactivate

Deactivates a license from a domain (allows re-activation elsewhere).

**Request:**
```json
{
  "license_key": "AIAS-XXXX-XXXX-XXXX",
  "domain": "old-site.com",
  "email": "buyer@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "activations_remaining": 1
}
```

---

### GET /license/status

Checks current license status (for dashboard display).

**Headers:**
```
Authorization: Bearer <license_key>
```

**Response:**
```json
{
  "license_key": "AIAS-XXXX-XXXX-XXXX",
  "status": "active",
  "features": ["quests", "blog", "pin", "memory"],
  "support_until": "2027-01-16",
  "activated_domains": ["client-site.com"],
  "activations_used": 1,
  "activations_limit": 1
}
```

---

## Server Implementation

### Envato API Integration

To verify purchase codes with Envato:

```python
import httpx

ENVATO_TOKEN = "your-envato-personal-token"

async def verify_envato_purchase(code: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://api.envato.com/v3/market/author/sale",
            params={"code": code},
            headers={"Authorization": f"Bearer {ENVATO_TOKEN}"}
        )
        
        if response.status_code == 404:
            return {"valid": False, "error": "invalid_code"}
        
        if response.status_code != 200:
            return {"valid": False, "error": "envato_api_error"}
        
        data = response.json()
        return {
            "valid": True,
            "item_id": data["item"]["id"],
            "item_name": data["item"]["name"],
            "buyer": data["buyer"],
            "purchase_date": data["sold_at"],
            "support_until": data.get("supported_until"),
            "license": data["license"]
        }
```

### Database Schema (PostgreSQL)

```sql
CREATE TABLE licenses (
    id SERIAL PRIMARY KEY,
    purchase_code VARCHAR(36) UNIQUE NOT NULL,
    license_key VARCHAR(20) UNIQUE NOT NULL,
    buyer_email VARCHAR(255) NOT NULL,
    envato_item_id INTEGER NOT NULL,
    envato_buyer VARCHAR(100),
    purchase_date TIMESTAMP NOT NULL,
    support_until TIMESTAMP,
    features JSONB DEFAULT '[]',
    activations_limit INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE activations (
    id SERIAL PRIMARY KEY,
    license_id INTEGER REFERENCES licenses(id),
    domain VARCHAR(255) NOT NULL,
    activated_at TIMESTAMP DEFAULT NOW(),
    deactivated_at TIMESTAMP,
    ip_address INET,
    UNIQUE(license_id, domain)
);

CREATE TABLE download_tokens (
    id SERIAL PRIMARY KEY,
    license_id INTEGER REFERENCES licenses(id),
    token VARCHAR(500) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### Security Considerations

1. **Rate Limiting**: Max 5 verification attempts per IP per hour
2. **Token Expiry**: Download tokens expire after 1 hour
3. **Domain Validation**: Store and validate activation domains
4. **Signature Verification**: Validate HMAC signatures on requests
5. **HTTPS Only**: Reject non-HTTPS connections
6. **Audit Logging**: Log all license operations

---

## License Tiers (Optional)

You can offer different license tiers:

| Tier | Features | Activations | Support |
|------|----------|-------------|---------|
| Regular | Core features | 1 domain | 6 months |
| Extended | + Blog, PIN | 3 domains | 12 months |
| Enterprise | All features | Unlimited | Lifetime |

---

## Webhook Events (Optional)

Send webhooks to customer endpoints:

```json
{
  "event": "license.activated",
  "license_key": "AIAS-XXXX-XXXX-XXXX",
  "domain": "client-site.com",
  "timestamp": "2025-01-16T12:00:00Z"
}
```

Events: `license.activated`, `license.deactivated`, `support.expiring`, `support.expired`
