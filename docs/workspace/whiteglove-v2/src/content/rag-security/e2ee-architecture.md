---
title: Enterprise E2E Encryption
icon: Lock
category: Security
order: 3
description: Client-side encryption architecture for zero-trust security.
---

# Enterprise E2E Encryption

> True End-to-End Encryption (E2EE) where the platform never sees plaintext.

**Tier:** Enterprise Only  
**Status:** Architecture Specification

---

## Overview

The **Enterprise** tier provides **true end-to-end encryption** where the AiAssist Secure platform **never** sees plaintext message content - not at rest, not in transit, not in memory. This is achieved through a **client-mediated architecture** where encryption/decryption and AI processing happen entirely on the client side.

**Key Differentiator:** Unlike the Secure tier (where the server decrypts for AI processing), Enterprise E2EE ensures the platform is cryptographically blind to customer data.

---

## The Core Truth

**True E2EE with server-side AI processing is impossible by definition.**

If the server decrypts data to process it, it's not end-to-end encrypted. Enterprise customers who require true E2EE must accept one of two models:

1. **Client Direct**: Client handles all AI calls using customer's BYOK API keys
2. **Secure Enclaves**: Server processes in attested TEE (Trusted Execution Environment)

This document focuses on **Client Direct** as the primary architecture.

---

## Architecture: Client Direct Model

### Data Flow

1. **Client**: Fetches ciphertext from platform.
2. **Client**: Decrypts locally using Workspace Conversation Secret (WS-CS).
3. **Client**: Decrypts BYOK API key locally.
4. **Client**: Sends prompt directly to LLM provider (OpenAI, etc.).
5. **Client**: Encrypts response locally.
6. **Platform**: Stores ciphertext only.

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

1. **Device Key Pair**: X25519 per device, stored in IndexedDB/Keychain.
2. **Workspace Conversation Secret (WS-CS)**: AES-256 key, wrapped for each device, stored encrypted on platform.
3. **Message Encryption**: AES-256-GCM, unique nonce per message.

### Device Enrollment

- **New Device**: Generates key pair, registers public key.
- **Approval**: Existing device wraps WS-CS with new device's public key.
- **Revocation**: Admin revokes device, rotates WS-CS, re-encrypts history (optional).

---

## BYOK LLM Integration

### API Key Storage

Customer LLM API keys are encrypted under the workspace WS-CS and stored on the platform. Only clients with WS-CS access can decrypt and use them.

### Client-Side LLM Calls

Clients fetch encrypted history, decrypt locally, call the LLM provider directly using the decrypted BYOK key, and then encrypt the response before sending it to the platform for storage.

**Supported Providers:**
- OpenAI, Anthropic, Google, Groq, Mistral, and any REST-compatible provider.

---

## Key Recovery & Escrow

**Default: No Recovery.** If all devices are lost, data is unrecoverable.

**Opt-In Escrow:**
- Customer manages an **Escrow Master Key (EMK)** in their own HSM/KMS.
- Platform stores WS-CS encrypted with EMK public key.
- Recovery acts as a "break glass" procedure fully controlled by the customer.

---

## Security Considerations

| Threat | Mitigation |
|--------|------------|
| Platform admin reads database | Only ciphertext stored |
| Platform admin modifies server code | Client-side crypto, can't fake keys |
| Compromised platform server | No plaintext ever on server |
| Device theft | Device key protected by OS keychain |
| Lost all devices | Data unrecoverable (by design) OR escrow recovery |

**Compliance:**
- **SOC 2**: Audit logs, access controls.
- **HIPAA**: Encryption at rest and in transit.
- **GDPR**: Data minimization, encryption.
