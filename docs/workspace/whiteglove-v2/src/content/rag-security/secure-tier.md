---
title: Secure Tier Encryption
description: End-to-end encrypted messaging architecture for the Secure tier.
category: Security
icon: Shield
order: 1
---

# Secure Tier: End-to-End Encrypted Messaging

## Overview

The **Secure** subscription tier extends Pro with enterprise-grade message encryption. **Secure Tier protects customer conversations from internal access, database compromise, and unauthorized inspection by encrypting all message content at rest using per-organization keys protected by hardware security modules.**

This provides a key differentiator for privacy-conscious organizations while maintaining full AI functionality.

**Tier Positioning:**
- **Free**: Basic AI chat, rate-limited
- **Pro**: Full AI features, BYOK, conversation memory
- **Secure** (NEW): Everything in Pro + encrypted message storage (admin-blind)
- **Enterprise**: Secure + SSO, dedicated support, custom SLAs, compliance packages

---

## Problem Statement

Currently, all workspace messages are stored as plaintext in Redis. Platform administrators with database access can read any customer's conversations. For security-conscious organizations (legal, healthcare, finance), this is a dealbreaker.

**Goals:**
1. Messages encrypted at rest - Redis only stores ciphertext
2. Platform admins cannot decrypt customer data
3. AI orchestrator can still process messages (decrypt → LLM → re-encrypt)
4. Zero changes to end-user experience
5. Compliance-ready (GDPR, SOC2, HIPAA considerations)

---

## Architecture

### Key Hierarchy (Double-Envelope Encryption)

```
┌─────────────────────────────────────────────────────────────┐
│                    KEY MANAGEMENT SERVICE                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐                                        │
│  │  Platform Root  │  (HSM-backed, never exported)          │
│  │      Key        │                                        │
│  └────────┬────────┘                                        │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────┐                                        │
│  │  Tenant Master  │  One per organization (Secure tier)    │
│  │   Key (TMK)     │  Wrapped with Platform Root Key        │
│  └────────┬────────┘                                        │
│           │                                                 │
│           ▼                                                 │
│  ┌─────────────────┐                                        │
│  │  Data Encrypt   │  One per workspace                     │
│  │   Key (DEK)     │  Wrapped with TMK                      │
│  └─────────────────┘                                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Encryption Flow

```
                    ┌──────────────┐
                    │   Client     │
                    │  (Browser)   │
                    └──────┬───────┘
                           │ TLS (plaintext in transit)
                           ▼
                    ┌──────────────┐
                    │   FastAPI    │
                    │   Backend    │
                    └──────┬───────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
    ┌──────────────────┐      ┌──────────────────┐
    │  KMS Service     │      │  AI Orchestrator │
    │  (Unwrap DEK)    │      │  (Decrypt → LLM) │
    └────────┬─────────┘      └────────┬─────────┘
             │                         │
             ▼                         ▼
    ┌──────────────────┐      ┌──────────────────┐
    │  Redis Storage   │      │  LLM Provider    │
    │  (Ciphertext)    │      │  (Plaintext)     │
    └──────────────────┘      └──────────────────┘
```

### Message Storage Format

**Current (Plaintext):**
```json
{
  "id": "msg_abc123",
  "workspace_id": "ws_xyz",
  "content": "What's my favorite color?",
  "role": "user",
  "created_at": "2025-12-24T22:00:00Z"
}
```

**Secure Tier (Encrypted):**
```json
{
  "id": "msg_abc123",
  "workspace_id": "ws_xyz",
  "encrypted": true,
  "key_version": 1,
  "nonce": "base64-encoded-96-bit-nonce",
  "tag": "base64-encoded-128-bit-auth-tag",
  "ciphertext": "base64-encoded-aes-256-gcm-encrypted-content",
  "role": "user",
  "created_at": "2025-12-24T22:00:00Z"
}
```

---

## Cryptographic Specifications

| Component | Algorithm | Key Size | Notes |
|-----------|-----------|----------|-------|
| Message Encryption | AES-256-GCM | 256-bit | Authenticated encryption |
| DEK Wrapping | AES-256-KW or RSA-OAEP | 256-bit | Key wrap for storage |
| TMK Storage | Cloud KMS / HSM | 256-bit | Never exported |
| Nonce | Random | 96-bit | Unique per message |
| Auth Tag | GCM | 128-bit | Integrity verification |

**Key Generation:**
- TMKs are randomly generated and managed by Cloud KMS; organization identifiers are used for lookup only (not derivation)
- DEKs are randomly generated per workspace, wrapped with TMK

---

## Security Considerations

### What Platform Admins CAN See:
- Message metadata (timestamps, workspace IDs, message counts)
- Encrypted ciphertext blobs
- Key usage audit logs
- User activity patterns

### What Platform Admins CANNOT See:
- Message content (plaintext)
- DEKs (wrapped, only unwrapped in memory)
- TMKs (stored in HSM/cloud KMS)

### Threat Model

| Threat | Mitigation |
|--------|------------|
| Admin reads Redis directly | Only ciphertext stored |
| Admin dumps database | Keys not in database |
| Admin modifies code | Audit logs + code review |
| Key compromise | Key rotation + versioning |
| Insider threat | Split-knowledge escrow |

---

## Pricing Considerations

**Secure Tier Pricing (Suggested):**
- Base: Pro price + $10/seat/month
- Includes: Encrypted storage, audit logs, key management
- Add-on: Custom key escrow setup (+$500 one-time)

**Cost Factors:**
- Cloud KMS API calls (~$0.03 per 10,000 operations)
- Increased storage (base64 ciphertext ~33% larger)
- CPU overhead for encryption (~5% latency increase)
