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

## Implementation Plan

### Phase 1: Foundation (Week 1-2)

#### 1.1 KMS Service Module
```python
# api/services/kms_service.py

class KMSService:
    """Key Management Service for Secure tier encryption."""
    
    def provision_tenant_master_key(org_id: str) -> str:
        """Create TMK for new Secure tier organization."""
        
    def generate_workspace_dek(workspace_id: str, tmk_id: str) -> WrappedKey:
        """Generate and wrap a new DEK for a workspace."""
        
    def unwrap_dek(wrapped_dek: WrappedKey, tmk_id: str) -> bytes:
        """Unwrap DEK for encryption/decryption operations."""
        
    def rotate_dek(workspace_id: str) -> WrappedKey:
        """Generate new DEK, re-encrypt all messages."""
```

#### 1.2 Encrypted Message Codec
```python
# api/services/message_crypto.py

class MessageCrypto:
    """Encrypt/decrypt message content using workspace DEK."""
    
    def encrypt(plaintext: str, dek: bytes) -> EncryptedPayload:
        """AES-256-GCM encrypt with random nonce."""
        
    def decrypt(payload: EncryptedPayload, dek: bytes) -> str:
        """Verify auth tag and decrypt."""
```

### Phase 2: Integration (Week 2-3)

#### 2.1 Storage Layer Updates
- Modify `add_message()` to encrypt if workspace is Secure tier
- Modify `get_messages()` to decrypt before returning
- Add `encrypted` flag to Message schema
- Cache unwrapped DEKs with short TTL (5 min)

#### 2.2 AI Orchestrator Updates
- Decrypt message history before building LLM prompt
- Encrypt AI response before storage
- Ensure plaintext never logged or traced

### Phase 3: Subscription Integration (Week 3)

#### 3.1 Plan Enforcement
- Add `secure_storage_enabled` field to Organization
- Check subscription tier before enabling encryption
- Auto-provision TMK on Secure tier activation

#### 3.2 Upgrade Path
- Existing Pro → Secure: Encrypt all historical messages
- Background job with progress tracking
- Workspace-by-workspace migration

### Phase 4: Compliance & Operations (Week 4)

#### 4.1 Audit Logging
- Log every DEK unwrap operation
- Log key rotation events
- Tamper-proof audit trail

#### 4.2 Key Recovery & Escrow

**Important: Escrow is opt-in only. Default is no recovery capability.**

- **Default behavior**: No key escrow - if customer loses access, data is unrecoverable
- **Opt-in escrow**: Customer explicitly requests and accepts recovery capability
- **Risk acknowledgment**: Customer signs off that escrow introduces additional access vectors
- Split-knowledge recovery process (requires M-of-N admin quorum)
- Documented incident response procedures

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

## API Changes

### New Endpoints

```
POST /api/admin/organizations/{org_id}/enable-secure
  → Provision TMK, migrate existing messages

GET /api/admin/organizations/{org_id}/encryption-status
  → Return encryption stats, key versions, last rotation

POST /api/admin/organizations/{org_id}/rotate-keys
  → Trigger DEK rotation for all workspaces

POST /api/admin/organizations/{org_id}/export-escrow
  → Generate escrow package for customer
```

### Schema Updates

```python
# Organization model additions
class Organization:
    secure_storage_enabled: bool = False
    tmk_id: Optional[str] = None
    encryption_migrated_at: Optional[datetime] = None

# Workspace model additions  
class Workspace:
    dek_version: int = 0
    encrypted: bool = False

# Message model additions
class Message:
    encrypted: bool = False
    key_version: int = 0
    nonce: Optional[str] = None
    tag: Optional[str] = None
```

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

---

## Success Criteria

1. **Zero Plaintext in Redis**: Verified via Redis dump inspection
2. **Transparent to Users**: No UX changes, same chat experience
3. **< 5% Latency Impact**: Encryption overhead minimal
4. **Audit Trail Complete**: Every key operation logged
5. **Key Rotation Works**: Re-encrypt without downtime
6. **Compliance Ready**: Documentation for SOC2/GDPR audits

---

## Dependencies

- **Cloud KMS**: AWS KMS, Google Cloud KMS, or Azure Key Vault
- **Cryptography Library**: Python `cryptography` package (already installed)
- **Background Jobs**: For migration and key rotation tasks

---

## Open Questions

1. **Cloud KMS Provider**: Which cloud provider for HSM-backed keys?
2. **Self-Hosted Option**: Should customers be able to bring their own KMS?
3. **Retention Policy**: How long to keep encrypted messages before purge?
4. **Geographic Restrictions**: Should keys be region-locked for compliance?

---

## Next Steps

1. [ ] Review and approve this architecture
2. [ ] Select cloud KMS provider
3. [ ] Implement KMS service module (feature-flagged)
4. [ ] Build encrypted message codec
5. [ ] Integrate with storage layer
6. [ ] Build migration tooling
7. [ ] Security review and penetration testing
8. [ ] Documentation and compliance package

---

*Document Version: 1.0*  
*Created: December 2025*  
*Status: DRAFT - Pending Review*
