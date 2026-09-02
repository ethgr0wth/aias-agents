---
title: Secure Tier Encryption (Admin-Blind Messages)
---
# Secure Tier Encryption (Admin-Blind)

## What & Why
Implement admin-blind encrypted message storage for the Secure subscription tier. Medical, legal, and finance clients need assurance that platform administrators cannot read their conversation data. This uses AES-256-GCM with a double-envelope key hierarchy (DEK per workspace, TMK per org, root key from env secret) so Redis only stores ciphertext.

## Done looks like
- Messages for Secure-tier orgs are AES-256-GCM encrypted at rest in Redis — inspecting Redis shows only ciphertext
- Platform admins cannot decrypt customer message content
- AI orchestrator still works normally (decrypt → LLM → re-encrypt happens transparently)
- No change to end-user experience — chat works identically
- Admin endpoint to enable/disable encryption per org
- Admin endpoint to check encryption status per org
- Encryption status visible in admin dashboard

## Out of scope
- Cloud KMS / HSM integration (using env-var root key for now, upgradeable later)
- M-of-N quorum key escrow
- Automated key rotation with re-encryption job
- Background migration of historical plaintext messages (manual script later if needed)
- SOC2/HIPAA certification paperwork (just the technical controls)

## Tasks
1. **Message crypto service** — Create `api/services/message_crypto.py` with AES-256-GCM encrypt/decrypt using the `cryptography` library. Each call generates a random 96-bit nonce and returns ciphertext + nonce + auth tag.

2. **KMS service (lean)** — Create `api/services/kms_service.py` that manages the key hierarchy: root key from `PIN_ENCRYPTION_KEY` env var, TMK per org (generated randomly, wrapped/unwrapped with root key), DEK per workspace (generated randomly, wrapped/unwrapped with TMK). Store wrapped keys in Redis. Cache unwrapped DEKs in memory with 5-min TTL.

3. **Schema updates** — Add `encrypted`, `nonce`, `tag`, `key_version` fields to Message model. Add `secure_storage_enabled` and `tmk_id` fields to Organization/OrganizationSettings. All fields have safe defaults so existing data is unaffected.

4. **Storage layer integration** — Modify `add_message()` to encrypt content when the workspace's org has `secure_storage_enabled=true`. Modify `get_messages()` to transparently decrypt before returning. DEK is fetched per workspace via KMS service. The `encrypted` flag on each message determines whether decryption is needed (backward compatible with existing plaintext).

5. **Admin API endpoints** — Add `POST /api/admin/organizations/{org_id}/enable-secure` (provision TMK, set flag), `GET /api/admin/organizations/{org_id}/encryption-status` (return encryption stats), and `POST /api/admin/organizations/{org_id}/disable-secure` (flag off, new messages stored plaintext).

6. **Audit logging** — Log every DEK unwrap and TMK provision event to a Redis stream (`encryption:audit`) with timestamp, org_id, workspace_id, operation type. This provides a tamper-evident trail for compliance reviews.

## Relevant files
- `aias_production/api/services/redis_storage.py:1112-1169`
- `aias_production/api/services/redis_storage.py:1199-1230`
- `aias_production/api/services/redis_storage.py:3083-3170`
- `aias_production/api/models/schemas.py:636-651`
- `aias_production/api/models/schemas.py:897-927`
- `aias_production/api/routes/organizations.py`
- `aias_production/docs/secure-tier-encryption.md`