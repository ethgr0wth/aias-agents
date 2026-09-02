# Enterprise Tier: True End-to-End Encryption (E2EE)

## Overview

The **Enterprise** tier provides **true end-to-end encryption** where the AiAssist Secure platform **never** sees plaintext message content - not at rest, not in transit, not in memory. This is achieved through a **client-mediated architecture** where encryption/decryption and AI processing happen entirely on the client side.

**Key Differentiator:** Unlike the Secure tier (where the server decrypts for AI processing), Enterprise E2EE ensures the platform is cryptographically blind to customer data.

---

## Tier Comparison

| Capability | Pro | Secure | Enterprise E2EE |
|------------|-----|--------|-----------------|
| Encrypted at rest | ❌ | ✅ | ✅ |
| Platform can decrypt | Yes | Yes (for AI) | **Never** |
| AI processing location | Server | Server | **Client** |
| LLM API keys | Platform or BYOK | Platform or BYOK | **BYOK only** |
| Admin visibility | Full | Metadata only | **Metadata only** |
| Multi-device support | Server-mediated | Server-mediated | Device enrollment |
| Key management | Platform | Platform KMS | **Customer-controlled** |
| Compliance level | Basic | SOC2-ready | **HIPAA/FedRAMP-ready** |

---

## The Core Truth

**True E2EE with server-side AI processing is impossible by definition.**

If the server decrypts data to process it, it's not end-to-end encrypted. Enterprise customers who require true E2EE must accept one of two models:

1. **Client Direct**: Client handles all AI calls using customer's BYOK API keys
2. **Secure Enclaves**: Server processes in attested TEE (Trusted Execution Environment)

This document focuses on **Client Direct** as the primary architecture, with Secure Enclaves as a Phase 2 option.

---

## Architecture: Client Direct Model

### Data Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        ENTERPRISE E2EE FLOW                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                     CLIENT (Browser/App)                         │   │
│   │                                                                  │   │
│   │   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐      │   │
│   │   │ 1. Fetch     │    │ 2. Decrypt   │    │ 3. Build     │      │   │
│   │   │ Ciphertext   │───►│ Locally      │───►│ Prompt       │      │   │
│   │   │ from Platform│    │ (WS-CS key)  │    │              │      │   │
│   │   └──────────────┘    └──────────────┘    └──────┬───────┘      │   │
│   │                                                   │              │   │
│   │   ┌──────────────┐    ┌──────────────┐    ┌──────▼───────┐      │   │
│   │   │ 6. Store     │    │ 5. Encrypt   │    │ 4. Call LLM  │      │   │
│   │   │ Ciphertext   │◄───│ Response     │◄───│ Directly     │──────┼───┼──► LLM Provider
│   │   │ on Platform  │    │ (WS-CS key)  │    │ (BYOK key)   │      │   │    (OpenAI, etc)
│   │   └──────────────┘    └──────────────┘    └──────────────┘      │   │
│   │                                                                  │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                    │                                     │
│                                    │ Ciphertext only                     │
│                                    ▼                                     │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                  PLATFORM (AiAssist Secure)                      │   │
│   │                                                                  │   │
│   │   • Stores encrypted message blobs                               │   │
│   │   • Manages workspace metadata (IDs, timestamps, member lists)   │   │
│   │   • Routes encrypted payloads                                    │   │
│   │   • NEVER decrypts, NEVER sees plaintext                        │   │
│   │                                                                  │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### What the Platform Sees

**CAN see (metadata):**
- Workspace IDs, user IDs, timestamps
- Message counts and sizes
- Device enrollment records
- Encrypted key material blobs

**CANNOT see (cryptographically protected):**
- Message content
- AI prompts and responses
- Customer LLM API keys
- Workspace conversation secrets

---

## Key Management

### Key Hierarchy

```
┌─────────────────────────────────────────────────────────────────────┐
│                      CUSTOMER-CONTROLLED KEYS                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Device Key Pair (per device)                                │   │
│  │  • X25519 key pair                                           │   │
│  │  • Private key: Device-local (IndexedDB/Keychain)            │   │
│  │  • Public key: Registered with platform                      │   │
│  └──────────────────────────┬──────────────────────────────────┘   │
│                              │ Unwraps                              │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Workspace Conversation Secret (WS-CS)                       │   │
│  │  • 256-bit symmetric key (XChaCha20-Poly1305)                │   │
│  │  • One per workspace                                          │   │
│  │  • Wrapped for each authorized device's public key           │   │
│  │  • Stored on platform as encrypted blob                      │   │
│  └──────────────────────────┬──────────────────────────────────┘   │
│                              │ Encrypts                             │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Message Content + BYOK API Tokens                           │   │
│  │  • AES-256-GCM encrypted payloads                            │   │
│  │  • Unique nonce per message                                   │   │
│  │  • Customer LLM API keys encrypted under WS-CS               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Cryptographic Specifications

| Component | Algorithm | Key Size | Library |
|-----------|-----------|----------|---------|
| Device key pair | X25519 | 256-bit | libsodium |
| Key wrapping | Sealed boxes (X25519 + XSalsa20-Poly1305) | 256-bit | libsodium |
| Message encryption | AES-256-GCM | 256-bit | Web Crypto API |
| Key derivation | HKDF-SHA256 | - | Web Crypto API |
| Nonce | Random | 96-bit (GCM) / 192-bit (XChaCha) | - |

---

## Multi-User & Multi-Device Support

### Device Enrollment Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    NEW DEVICE ENROLLMENT                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. User logs in on new device                                      │
│     └─► Device generates new X25519 key pair                        │
│     └─► Public key sent to platform                                 │
│                                                                     │
│  2. Platform notifies existing devices                              │
│     └─► "New device requesting access"                              │
│                                                                     │
│  3. User approves on existing device                                │
│     └─► Existing device fetches new device's public key             │
│     └─► Wraps WS-CS with new device's public key                    │
│     └─► Uploads wrapped key to platform                             │
│                                                                     │
│  4. New device downloads wrapped WS-CS                              │
│     └─► Unwraps with private key                                    │
│     └─► Can now decrypt workspace history                           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Member Invitation Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    NEW MEMBER INVITATION                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. Admin invites new member to workspace                           │
│     └─► Platform sends invitation (no key material yet)             │
│                                                                     │
│  2. New member accepts, enrolls device                              │
│     └─► Device generates X25519 key pair                            │
│     └─► Public key registered with platform                         │
│                                                                     │
│  3. Admin approves new member                                       │
│     └─► Admin's device wraps WS-CS with new member's public key     │
│     └─► Wrapped key uploaded to platform                            │
│                                                                     │
│  4. New member's device downloads wrapped WS-CS                     │
│     └─► Full workspace access granted                               │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Member Revocation Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MEMBER REVOCATION                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. Admin revokes member access                                     │
│     └─► Platform removes member's wrapped key entries               │
│                                                                     │
│  2. Key rotation triggered                                          │
│     └─► Remaining admin generates new WS-CS                         │
│     └─► Re-wraps for all remaining members/devices                  │
│     └─► Old WS-CS marked deprecated                                 │
│                                                                     │
│  3. Background re-encryption (optional)                             │
│     └─► Client-side job re-encrypts history with new WS-CS          │
│     └─► Progress tracked, old ciphertext purged                     │
│                                                                     │
│  Note: Revoked member may retain old messages if they cached them.  │
│  Forward secrecy is preserved for new messages.                     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## BYOK LLM Integration

### API Key Storage

Customer LLM API keys are encrypted under the workspace WS-CS and stored on the platform. Only clients with WS-CS access can decrypt and use them.

```json
{
  "workspace_id": "ws_xyz",
  "provider": "openai",
  "encrypted_api_key": {
    "nonce": "base64...",
    "ciphertext": "base64...",
    "tag": "base64..."
  }
}
```

### Client-Side LLM Calls

```javascript
// Pseudocode for client-side AI call

async function sendMessage(userMessage) {
  // 1. Fetch encrypted history from platform
  const encryptedHistory = await api.getMessages(workspaceId);
  
  // 2. Decrypt locally using WS-CS
  const history = await crypto.decryptMessages(encryptedHistory, wscs);
  
  // 3. Decrypt BYOK API key
  const apiKey = await crypto.decrypt(encryptedApiKey, wscs);
  
  // 4. Build prompt and call LLM directly
  const response = await fetch('https://api.openai.com/v1/chat/completions', {
    headers: { 'Authorization': `Bearer ${apiKey}` },
    body: JSON.stringify({
      model: 'gpt-4o',
      messages: [...history, { role: 'user', content: userMessage }]
    })
  });
  
  // 5. Encrypt response
  const encryptedResponse = await crypto.encrypt(response.content, wscs);
  
  // 6. Store on platform (ciphertext only)
  await api.storeMessage(workspaceId, encryptedResponse);
}
```

### Supported Providers

All BYOK providers work with client-direct calls:
- OpenAI (GPT-4o, GPT-4, etc.)
- Anthropic (Claude 3.5, etc.)
- Google (Gemini)
- Groq (Llama, Mixtral)
- Mistral
- Any provider with a REST API

---

## Key Recovery & Escrow

### Default: No Recovery

**By default, Enterprise E2EE workspaces have NO key recovery.**

If all devices with access are lost, the data is unrecoverable. This is the most secure configuration.

### Opt-In: Customer-Controlled Escrow

For compliance requirements (legal hold, regulatory access), customers may opt into escrow:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ESCROW ARCHITECTURE                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Customer's HSM/KMS (Azure, AWS, on-prem)                           │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Escrow Master Key (EMK)                                     │   │
│  │  • Generated and stored in customer's infrastructure         │   │
│  │  • Never leaves customer's control                           │   │
│  │  • Optional: M-of-N sharding (e.g., 3-of-5 executives)       │   │
│  └──────────────────────────┬──────────────────────────────────┘   │
│                              │                                      │
│                              ▼                                      │
│  Platform stores:                                                   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  WS-CS encrypted with customer's EMK public key              │   │
│  │  • Platform cannot decrypt (no EMK access)                   │   │
│  │  • Customer can recover by decrypting with EMK               │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Escrow Requirements

1. **Explicit opt-in**: Customer must request and configure escrow
2. **Risk acknowledgment**: Signed acceptance that escrow weakens security
3. **Customer-controlled**: EMK lives in customer's infrastructure only
4. **Audit trail**: All escrow operations logged
5. **Revocable**: Customer can rotate EMK and remove escrow

---

## Storage Format

### Encrypted Message Schema

```json
{
  "id": "msg_abc123",
  "workspace_id": "ws_xyz",
  "e2ee": true,
  "sender_device_id": "dev_123",
  "envelope": {
    "version": 1,
    "algorithm": "AES-256-GCM",
    "nonce": "base64-encoded-96-bit-nonce",
    "tag": "base64-encoded-128-bit-auth-tag",
    "ciphertext": "base64-encoded-encrypted-content"
  },
  "metadata": {
    "role": "user",
    "created_at": "2025-12-25T10:00:00Z",
    "content_length": 256
  }
}
```

### Wrapped Key Schema

```json
{
  "workspace_id": "ws_xyz",
  "key_version": 3,
  "wrapped_keys": [
    {
      "device_id": "dev_abc",
      "user_id": "user_123",
      "wrapped_wscs": "base64-sealed-box...",
      "created_at": "2025-12-01T00:00:00Z"
    },
    {
      "device_id": "dev_def",
      "user_id": "user_456",
      "wrapped_wscs": "base64-sealed-box...",
      "created_at": "2025-12-15T00:00:00Z"
    }
  ],
  "escrow": null
}
```

---

## Implementation Plan

### Phase 1: Foundation (Weeks 1-3)

#### 1.1 Client Crypto SDK
- Device key generation and secure storage
- WS-CS encryption/decryption
- Message envelope handling
- BYOK API key vault

#### 1.2 Device Management
- Device enrollment API
- Public key registry
- Device approval workflow UI

### Phase 2: Workspace Key Management (Weeks 3-5)

#### 2.1 Key Distribution
- WS-CS generation
- Sealed box wrapping for members
- Key rotation machinery

#### 2.2 Member Management
- Invitation flow
- Approval workflow
- Revocation and re-keying

### Phase 3: Client-Direct AI (Weeks 5-7)

#### 3.1 BYOK Integration
- Encrypted API key storage
- Client-side LLM calls
- Provider-agnostic abstraction

#### 3.2 UI Updates
- E2EE indicator in workspace
- Device management settings
- Key recovery options

### Phase 4: Compliance & Operations (Weeks 7-9)

#### 4.1 Escrow System
- Customer EMK integration
- Recovery workflow
- Audit logging

#### 4.2 Migration Tools
- Secure → Enterprise upgrade path
- History re-encryption tool
- Mixed-mode workspace support

---

## Phase 2 Option: Secure Enclaves (TEE)

For customers who cannot use client-direct (e.g., regulated call centers, shared terminals):

### Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SECURE ENCLAVE (TEE) MODEL                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  AWS Nitro Enclave / Azure Confidential VM                          │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Attested Enclave                                            │   │
│  │  • Customer verifies attestation before sending keys         │   │
│  │  • WS-CS decrypted inside enclave only                       │   │
│  │  • Plaintext exists only in enclave memory                   │   │
│  │  • LLM calls made from enclave                               │   │
│  │  • Response re-encrypted before leaving                      │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  Platform control plane sees: ciphertext only                       │
│  Enclave sees: ephemeral plaintext (never persisted)                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### TEE Benefits
- Server-side processing (familiar UX)
- Customer attestation verification
- Ephemeral plaintext (never persisted)

### TEE Tradeoffs
- More complex infrastructure
- Cloud provider dependency
- Higher operational cost
- Trust in TEE implementation

**Recommendation:** Offer TEE as optional add-on for specific compliance requirements.

---

## Security Considerations

### Threat Model

| Threat | Mitigation |
|--------|------------|
| Platform admin reads database | Only ciphertext stored |
| Platform admin modifies server code | Client-side crypto, can't fake keys |
| Compromised platform server | No plaintext ever on server |
| Device theft | Device key protected by OS keychain |
| Lost all devices | Data unrecoverable (by design) OR escrow recovery |
| Revoked member retains data | Forward secrecy for new messages |
| Man-in-the-middle | TLS + client-side encryption |

### What We're NOT Protecting Against

- Compromised client device (malware on user's machine)
- LLM provider data retention (customer's BYOK responsibility)
- Metadata analysis (timestamps, message sizes visible)
- Social engineering of key holders

### Compliance Positioning

| Framework | E2EE Support |
|-----------|--------------|
| SOC 2 | ✅ Audit logs, access controls |
| HIPAA | ✅ Encryption at rest and in transit |
| FedRAMP | ⚠️ Requires enclave option |
| GDPR | ✅ Data minimization, encryption |
| PCI-DSS | ⚠️ Not applicable (no cardholder data) |

---

## Pricing Considerations

**Enterprise E2EE Tier (Suggested):**
- Base: Secure price + $25/seat/month
- Minimum seats: 5
- Includes: Client crypto SDK, device management, BYOK integration
- Add-ons:
  - Custom escrow setup: +$2,000 one-time
  - TEE enclave option: +$10/seat/month
  - Dedicated support: Custom pricing

**Cost Factors:**
- No cloud KMS costs (customer-controlled)
- Client-side compute (customer's devices)
- Increased support complexity

---

## Open Questions

1. **SDK Distribution**: How do we ship the client crypto SDK? (npm package, bundled, CDN?)
2. **Mobile Support**: Native iOS/Android apps or PWA with WebCrypto?
3. **Offline Mode**: Should clients cache decrypted history? Security implications?
4. **Key Backup**: Should we offer cloud backup of device keys? (weakens security)
5. **Attestation UX**: How do customers verify TEE attestation in practice?
6. **Mixed Workspaces**: Can a workspace have both E2EE and non-E2EE members?

---

## Success Criteria

1. **Zero Plaintext on Platform**: Verified via memory dumps and storage inspection
2. **Client-Direct LLM Calls Work**: All BYOK providers functional
3. **Multi-Device Seamless**: Device enrollment < 60 seconds
4. **Key Rotation Complete**: Under 5 minutes for typical workspace
5. **Attestation Verified**: Customers can verify enclave identity
6. **Compliance Certified**: SOC 2 Type II audit passed

---

## Relationship to Secure Tier

Enterprise E2EE builds on Secure tier infrastructure:

| Component | Secure | Enterprise E2EE |
|-----------|--------|-----------------|
| Tenant provisioning | Reused | Reused |
| Metadata storage | Reused | Reused |
| Audit logging | Reused | Extended |
| Key storage | Platform KMS | Customer-controlled |
| Encryption location | Server | Client |
| AI processing | Server | Client or TEE |

**Migration Path:**
- Secure → Enterprise: Re-encrypt history client-side
- Can run mixed mode during transition
- Workspace-level setting: `encryption_mode = 'secure' | 'e2ee'`

---

*Document Version: 1.0*  
*Created: December 2025*  
*Status: DRAFT - Pending Review*
