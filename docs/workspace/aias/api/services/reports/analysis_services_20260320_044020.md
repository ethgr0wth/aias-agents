# Code Analysis Report
**Repo**: `services`
**Date**: 2026-03-20 04:40:20
**Model**: `openai/gpt-5.4`
**Files Scanned**: 1
**Focus**: security audit
**File Filter**: kms_service.py

---

# Codebase Analysis: `kms_service.py`

## Architecture Overview

### File structure
This codebase currently consists of a single service module:

- `kms_service.py`

### What this module does
`kms_service.py` implements a lightweight key-management layer backed by Redis:

- Loads a **root key** from `MESSAGE_ROOT_KEY` environment variable
- Uses that root key to wrap/unwrap an **organization TMK** (tenant/master key)
- Uses the TMK to wrap/unwrap **workspace DEKs** (data encryption keys)
- Stores wrapped keys in Redis hashes
- Caches unwrapped DEKs in process memory
- Writes audit events to a Redis stream

### Main components

#### 1. `WrappedKey` dataclass
Defined near the top of `kms_service.py`.

Purpose:
- Represents a wrapped key payload
- Serializes/deserializes wrapped key metadata to/from JSON

Fields:
- `algorithm`
- `nonce`
- `ciphertext`
- `tag`
- `key_version`
- `key_id`

#### 2. Root key handling
Functions:
- `kms_service.py:_get_root_key`

Purpose:
- Reads `MESSAGE_ROOT_KEY` from environment
- Base64-decodes it
- Validates it is exactly 32 bytes

This is the top-level wrapping key for TMKs.

#### 3. Key wrapping primitives
Functions:
- `kms_service.py:_wrap_key`
- `kms_service.py:_unwrap_key`

Purpose:
- Wrap plaintext keys using AES-GCM
- Use `key_id` as associated authenticated data (AAD)

This is a reasonable envelope-encryption design.

#### 4. DEK cache
Globals/functions:
- `kms_service.py:_dek_cache`
- `kms_service.py:_cache_get`
- `kms_service.py:_cache_set`

Purpose:
- Cache unwrapped workspace DEKs in memory for `DEK_CACHE_TTL = 300`

#### 5. Audit logging
Function:
- `kms_service.py:_audit_log`

Purpose:
- Writes audit events to Redis stream `encryption:audit`

#### 6. Provisioning and retrieval APIs
Functions:
- `kms_service.py:provision_tmk`
- `kms_service.py:_get_tmk`
- `kms_service.py:provision_dek`
- `kms_service.py:get_workspace_dek`

Purpose:
- Provision org-level TMKs
- Provision workspace-level DEKs
- Retrieve and unwrap DEKs

#### 7. Encryption feature toggles/status
Functions:
- `kms_service.py:is_org_encryption_enabled`
- `kms_service.py:enable_org_encryption`
- `kms_service.py:disable_org_encryption`
- `kms_service.py:get_encryption_status`

Purpose:
- Enable/disable encryption per org
- Report org encryption status and counts

---

# Security Audit Findings

Security is the main concern here, and there are several important issues.

---

## 1. **Critical: DEKs are returned even when org encryption is disabled**
**File:** `kms_service.py`  
**Lines:** around `get_workspace_dek` and `provision_dek`

### Problem
`get_workspace_dek(workspace_id, org_id)` does not check `is_org_encryption_enabled(org_id)` before provisioning or returning a DEK.

That means:
- even if `secure_storage_enabled` is `"false"`
- callers can still retrieve or provision DEKs
- disabling encryption is effectively only a metadata flag, not an enforcement control

### Why this matters
This is a security policy bypass. If the application expects disabled encryption to prevent key usage, it currently does not.

### Evidence
- `disable_org_encryption()` only sets `"secure_storage_enabled"` to `"false"`
- `get_workspace_dek()` directly calls `provision_dek()`
- `provision_dek()` directly unwraps/provisions DEKs if TMK exists

### Suggested fix
Add an enforcement check in `get_workspace_dek()` and ideally in `provision_dek()` too.

#### Surgical diff
```diff
--- a/kms_service.py
+++ b/kms_service.py
@@
 def provision_dek(workspace_id: str, org_id: str, request_id: str = "") -> tuple:
+    if not is_org_encryption_enabled(org_id):
+        raise RuntimeError(f"Encryption is not enabled for org {org_id}")
     r = get_redis()
@@
 def get_workspace_dek(workspace_id: str, org_id: str) -> tuple:
+    if not is_org_encryption_enabled(org_id):
+        raise RuntimeError(f"Encryption is not enabled for org {org_id}")
     cached = _cache_get(workspace_id)
     if cached:
         return cached
```

---

## 2. **Critical: Cache key is only `workspace_id`, causing cross-org key confusion**
**File:** `kms_service.py`  
**Lines:** around `_dek_cache`, `_cache_get`, `_cache_set`, `get_workspace_dek`

### Problem
The in-memory cache is keyed only by `workspace_id`:

```python
_dek_cache: Dict[str, tuple] = {}
```

and:

```python
entry = _dek_cache.get(workspace_id)
```

If `workspace_id` is not globally unique across orgs, or if callers can pass mismatched `workspace_id`/`org_id`, one org could receive another org’s cached DEK.

### Why this matters
This is a serious confidentiality risk. Even if workspace IDs are intended to be globally unique, the code does not enforce that assumption.

### Suggested fix
Key the cache by both `org_id` and `workspace_id`.

#### Surgical diff
```diff
--- a/kms_service.py
+++ b/kms_service.py
@@
-_dek_cache: Dict[str, tuple] = {}
+_dek_cache: Dict[str, tuple] = {}
@@
-def _cache_get(workspace_id: str) -> Optional[tuple]:
-    entry = _dek_cache.get(workspace_id)
+def _cache_key(org_id: str, workspace_id: str) -> str:
+    return f"{org_id}:{workspace_id}"
+
+
+def _cache_get(org_id: str, workspace_id: str) -> Optional[tuple]:
+    entry = _dek_cache.get(_cache_key(org_id, workspace_id))
@@
-        _dek_cache.pop(workspace_id, None)
+        _dek_cache.pop(_cache_key(org_id, workspace_id), None)
         return None
     return (dek_bytes, dek_id, key_version)
@@
-def _cache_set(workspace_id: str, dek_bytes: bytes, dek_id: str, key_version: int):
-    _dek_cache[workspace_id] = (dek_bytes, dek_id, key_version, time.time())
+def _cache_set(org_id: str, workspace_id: str, dek_bytes: bytes, dek_id: str, key_version: int):
+    _dek_cache[_cache_key(org_id, workspace_id)] = (dek_bytes, dek_id, key_version, time.time())
```

And update call sites:

```diff
--- a/kms_service.py
+++ b/kms_service.py
@@
-        _cache_set(workspace_id, dek_bytes, wrapped.key_id, wrapped.key_version)
+        _cache_set(org_id, workspace_id, dek_bytes, wrapped.key_id, wrapped.key_version)
@@
-        _cache_set(workspace_id, dek_bytes, wrapped.key_id, wrapped.key_version)
+        _cache_set(org_id, workspace_id, dek_bytes, wrapped.key_id, wrapped.key_version)
@@
-    _cache_set(workspace_id, dek_bytes, dek_id, 1)
+    _cache_set(org_id, workspace_id, dek_bytes, dek_id, 1)
@@
-    cached = _cache_get(workspace_id)
+    cached = _cache_get(org_id, workspace_id)
```

---

## 3. **Critical: No binding between workspace and org when unwrapping DEKs**
**File:** `kms_service.py`  
**Lines:** around `provision_dek`

### Problem
`provision_dek(workspace_id, org_id)` fetches:

```python
existing = r.hget(key(f"workspaces:{workspace_id}"), "dek_wrapped")
```

and unwraps it using the TMK for the supplied `org_id`.

There is no validation that:
- the workspace actually belongs to `org_id`
- the stored DEK metadata was created for that org

### Why this matters
If a caller supplies a workspace ID from another org, behavior depends on whether the wrong TMK can decrypt it. Usually AES-GCM will fail, which is good cryptographically, but:
- this still creates an authorization gap
- it relies on decryption failure rather than ownership validation
- it may leak existence/oracle behavior
- if IDs or metadata are corrupted/migrated incorrectly, this becomes dangerous

### Suggested fix
Persist and validate org ownership in workspace metadata before unwrap/provision.

#### Surgical diff
```diff
--- a/kms_service.py
+++ b/kms_service.py
@@
 def provision_dek(workspace_id: str, org_id: str, request_id: str = "") -> tuple:
     r = get_redis()
+    workspace_key = key(f"workspaces:{workspace_id}")
+    stored_org_id = r.hget(workspace_key, "org_id")
+    if stored_org_id and stored_org_id != org_id:
+        raise RuntimeError(f"Workspace {workspace_id} does not belong to org {org_id}")
-    existing = r.hget(key(f"workspaces:{workspace_id}"), "dek_wrapped")
+    existing = r.hget(workspace_key, "dek_wrapped")
@@
-    was_set = r.hsetnx(key(f"workspaces:{workspace_id}"), "dek_wrapped", wrapped.to_json())
+    was_set = r.hsetnx(workspace_key, "dek_wrapped", wrapped.to_json())
@@
-        existing = r.hget(key(f"workspaces:{workspace_id}"), "dek_wrapped")
+        existing = r.hget(workspace_key, "dek_wrapped")
@@
-    r.hset(key(f"workspaces:{workspace_id}"), mapping={
+    r.hset(workspace_key, mapping={
+        "org_id": org_id,
         "dek_id": dek_id,
         "dek_version": "1",
     })
```

If `org_id` is already stored elsewhere under a different field name, validate against that instead of introducing a new field.

---

## 4. **High: Disabling encryption does not invalidate in-memory DEK cache**
**File:** `kms_service.py`  
**Lines:** around `disable_org_encryption`, `_dek_cache`

### Problem
When encryption is disabled, cached DEKs remain in memory until TTL expiry.

### Why this matters
Even after an admin disables encryption, previously unwrapped DEKs may still be served from cache for up to 300 seconds.

### Suggested fix
Invalidate cached DEKs for the org on disable.

#### Surgical diff
```diff
--- a/kms_service.py
+++ b/kms_service.py
@@
 def disable_org_encryption(org_id: str, actor_id: str = "", request_id: str = ""):
     r = get_redis()
     r.hset(key(f"orgs:{org_id}"), "secure_storage_enabled", "false")
+    for cache_key in list(_dek_cache.keys()):
+        if cache_key.startswith(f"{org_id}:"):
+            _dek_cache.pop(cache_key, None)
     _audit_log("encryption_disabled", org_id, actor_type="admin",
                actor_id=actor_id, request_id=request_id)
```

---

## 5. **High: No integrity validation of `algorithm` field during unwrap**
**File:** `kms_service.py`  
**Lines:** around `_unwrap_key`

### Problem
`WrappedKey` stores `algorithm`, but `_unwrap_key()` ignores it completely.

### Why this matters
Today only AES-GCM is used, so this is not an immediate break. But it creates downgrade/confusion risk if formats evolve. A malformed or tampered record with unexpected algorithm metadata is not rejected explicitly.

### Suggested fix
Validate the algorithm before decrypting.

#### Surgical diff
```diff
--- a/kms_service.py
+++ b/kms_service.py
@@
 def _unwrap_key(wrapped: WrappedKey, wrapping_key: bytes) -> bytes:
+    if wrapped.algorithm != WRAP_ALGORITHM:
+        raise RuntimeError(f"Unsupported wrap algorithm: {wrapped.algorithm}")
     nonce = base64.b64decode(wrapped.nonce)
```

---

## 6. **High: Root key decoding is permissive**
**File:** `kms_service.py`  
**Lines:** around `_get_root_key`

### Problem
This line:

```python
decoded = base64.b64decode(raw)
```

uses non-strict base64 decoding by default.

### Why this matters
Malformed environment values may be accepted unexpectedly, depending on content. This is more robustness than direct exploit, but for key material you want strict parsing.

### Suggested fix
Use strict validation and clearer error handling.

#### Surgical diff
```diff
--- a/kms_service.py
+++ b/kms_service.py
@@
 def _get_root_key() -> bytes:
@@
-        decoded = base64.b64decode(raw)
+        try:
+            decoded = base64.b64decode(raw, validate=True)
+        except Exception as exc:
+            raise RuntimeError("MESSAGE_ROOT_KEY must be valid base64") from exc
```

---

## 7. **Medium: Unbounded in-process DEK cache can grow indefinitely**
**File:** `kms_service.py`  
**Lines:** around `_dek_cache`, `_cache_set`

### Problem
Expired entries are only removed on access. There is no max size and no periodic cleanup.

### Why this matters
An attacker or heavy workload can force many unique workspace IDs through the service and grow memory usage indefinitely.

### Suggested fix
Add a simple size cap or opportunistic cleanup.

#### Surgical diff
```diff
--- a/kms_service.py
+++ b/kms_service.py
@@
 DEK_CACHE_TTL = 300
+DEK_CACHE_MAX_ENTRIES = 10000
@@
 def _cache_set(org_id: str, workspace_id: str, dek_bytes: bytes, dek_id: str, key_version: int):
+    if len(_dek_cache) >= DEK_CACHE_MAX_ENTRIES:
+        now = time.time()
+        expired = [k for k, v in _dek_cache.items() if now - v[3] > DEK_CACHE_TTL]
+        for k in expired:
+            _dek_cache.pop(k, None)
+        if len(_dek_cache) >= DEK_CACHE_MAX_ENTRIES:
+            _dek_cache.pop(next(iter(_dek_cache)), None)
     _dek_cache[_cache_key(org_id, workspace_id)] = (dek_bytes, dek_id, key_version, time.time())
```

---

## 8. **Medium: Sensitive key material is cached in plaintext in process memory**
**File:** `kms_service.py`  
**Lines:** around `_dek_cache`, `provision_dek`, `get_workspace_dek`

### Problem
Unwrapped DEKs are stored in plaintext in a global Python dictionary.

### Why this matters
This may be acceptable in some application architectures, but it increases exposure:
- memory dumps
- debug tooling
- accidental object retention
- multi-tenant worker processes

Python does not provide reliable zeroization, so minimizing retention matters.

### Recommendation
If performance allows:
- reduce TTL
- cache only when necessary
- consider storing only wrapped DEKs and re-unwrapping on demand
- isolate this service process if handling high-sensitivity data

This is more architectural than a surgical code fix.

---

## 9. **Medium: Audit logging swallows exceptions too broadly**
**File:** `kms_service.py`  
**Lines:** around `_audit_log`

### Problem
```python
except Exception:
    logger.error("Failed to write encryption audit log: %s", operation)
```

This suppresses all failures and loses exception context.

### Why this matters
For a security-sensitive service, audit failures should be observable. Right now:
- stack trace is lost
- root cause is hidden
- security monitoring may silently degrade

### Suggested fix
Log exception details.

#### Surgical diff
```diff
--- a/kms_service.py
+++ b/kms_service.py
@@
-    except Exception:
-        logger.error("Failed to write encryption audit log: %s", operation)
+    except Exception:
+        logger.exception("Failed to write encryption audit log: %s", operation)
```

If audit logging is mandatory for compliance, you may want to fail closed for certain operations instead of swallowing errors.

---

## 10. **Medium: `get_encryption_status` leaks global audit stream length, not org-specific count**
**File:** `kms_service.py`  
**Lines:** around `get_encryption_status`

### Problem
```python
audit_count = r.xlen(key("encryption:audit"))
```

This returns the total number of audit entries across all orgs, but the function returns it as part of one org’s status.

### Why this matters
This is an information disclosure issue:
- one org can infer total encryption activity volume
- the field name suggests org-specific relevance

### Suggested fix
Either:
- rename the field to indicate global count, or
- maintain per-org audit streams/counters

Minimal safe fix:

```diff
--- a/kms_service.py
+++ b/kms_service.py
@@
-        "audit_log_entries": audit_count,
+        "global_audit_log_entries": audit_count,
```

Better fix: write audit entries to `encryption:audit:{org_id}` in addition to or instead of the global stream.

---

## 11. **Medium: No validation of decoded nonce/tag lengths on unwrap**
**File:** `kms_service.py`  
**Lines:** around `_unwrap_key`

### Problem
The code base64-decodes nonce/ciphertext/tag and passes them to AESGCM without explicit length checks.

### Why this matters
Cryptography library will reject invalid inputs, so this is not a direct break, but explicit validation improves:
- tamper detection clarity
- error quality
- defensive hardening

### Suggested fix
```diff
--- a/kms_service.py
+++ b/kms_service.py
@@
 def _unwrap_key(wrapped: WrappedKey, wrapping_key: bytes) -> bytes:
     if wrapped.algorithm != WRAP_ALGORITHM:
         raise RuntimeError(f"Unsupported wrap algorithm: {wrapped.algorithm}")
     nonce = base64.b64decode(wrapped.nonce)
     ciphertext = base64.b64decode(wrapped.ciphertext)
     tag = base64.b64decode(wrapped.tag)
+    if len(nonce) != 12:
+        raise RuntimeError("Invalid wrapped key nonce length")
+    if len(tag) != 16:
+        raise RuntimeError("Invalid wrapped key tag length")
     aesgcm = AESGCM(wrapping_key)
```

---

## 12. **Low/Medium: No concurrency protection around global cache**
**File:** `kms_service.py`  
**Lines:** around `_dek_cache`, `_cache_get`, `_cache_set`

### Problem
The global dict is mutated without locking.

### Why this matters
In CPython, individual dict operations are atomic enough to avoid many crashes, but compound operations are not synchronized. In threaded deployments this can lead to subtle races.

### Suggested fix
Use a `threading.Lock` around cache access if this service runs in a multi-threaded app server.

---

# Potential Bugs

## 1. `is_org_encryption_enabled` may fail depending on Redis client return type
**File:** `kms_service.py`  
**Lines:** around `is_org_encryption_enabled`

### Problem
```python
val = r.hget(key(f"orgs:{org_id}"), "secure_storage_enabled")
return val == "true"
```

If Redis returns `bytes` instead of `str`, this will always be `False`.

Same issue may affect:
- `get_encryption_status` with `org_data.get("secure_storage_enabled")`
- `tmk_wrapped` / `dek_wrapped` JSON parsing if values are bytes

### Suggested fix
Normalize Redis values.

#### Surgical diff
```diff
--- a/kms_service.py
+++ b/kms_service.py
@@
 logger = logging.getLogger(__name__)
@@
+def _to_str(value):
+    if isinstance(value, bytes):
+        return value.decode("utf-8")
+    return value
+
@@
 def is_org_encryption_enabled(org_id: str) -> bool:
@@
-    val = r.hget(key(f"orgs:{org_id}"), "secure_storage_enabled")
+    val = _to_str(r.hget(key(f"orgs:{org_id}"), "secure_storage_enabled"))
     return val == "true"
```

And similarly at other Redis read sites.

---

## 2. `WrappedKey.from_json` may break if Redis returns bytes
**File:** `kms_service.py`  
**Lines:** around `WrappedKey.from_json`, callers in `provision_tmk`, `_get_tmk`, `provision_dek`

### Problem
`json.loads(raw)` accepts `str`, `bytes`, or `bytearray` in modern Python, so this may be fine depending on runtime. But downstream dataclass field types assume strings. Mixed bytes/str behavior can become inconsistent.

### Recommendation
Normalize Redis values before parsing, especially for consistency.

---

## 3. `get_encryption_status` may perform expensive full workspace scan
**File:** `kms_service.py`  
**Lines:** around `get_encryption_status`

### Problem
```python
workspaces = storage.list_workspaces(active_only=True)
for ws in workspaces:
    if ws.organization_id == org_id:
```

This appears to fetch all active workspaces, then filter in Python.

### Why this matters
This is a performance issue and can become a bug under scale.

### Suggested fix
Prefer a storage API that filters by org at source, e.g. `list_workspaces(org_id=org_id, active_only=True)` if available.

---

## 4. `provision_tmk` can leave partially initialized org metadata
**File:** `kms_service.py`  
**Lines:** around `provision_tmk`

### Problem
`tmk_wrapped` is written with `hsetnx`, then `tmk_id` is written separately:

```python
was_set = r.hsetnx(..., "tmk_wrapped", ...)
...
r.hset(..., "tmk_id", tmk_id)
```

If the process crashes between these calls, the org may have `tmk_wrapped` but no `tmk_id`.

### Suggested fix
Use a Redis transaction/pipeline or derive `tmk_id` from wrapped payload when needed.

---

# Performance Issues

## 1. Full workspace scan in `get_encryption_status`
**File:** `kms_service.py`

As noted above, this is likely O(all active workspaces), not O(org workspaces).

### Fix
Push filtering into storage layer.

---

## 2. Repeated Redis key construction and multiple round trips
**File:** `kms_service.py`

Examples:
- `provision_tmk`
- `provision_dek`

There are several repeated `hget`/`hset` calls on the same Redis hash. This is not terrible, but could be reduced with pipelines in hot paths.

### Example
In `provision_dek`, the code:
- gets `dek_wrapped`
- gets TMK
- may `hsetnx`
- may `hget` again
- may `hset` mapping

This is acceptable for low volume, but not optimized.

---

## 3. Cache cleanup only on access
**File:** `kms_service.py`

Expired cache entries remain forever if never re-accessed.

### Fix
Covered above with max-size/cleanup logic.

---

# Code Quality Review

## What looks good
There are several solid choices here:

- `AESGCM` is used correctly with a random 12-byte nonce
- Key sizes are appropriate at 32 bytes
- AAD includes `key_id`, which helps bind metadata to ciphertext
- `WrappedKey` serialization is clean and readable
- `hsetnx` is used to reduce duplicate provisioning races
- Root key length is validated
- Audit logging exists, which is good for a KMS-like service

## Areas to improve

### 1. Missing explicit authorization/ownership checks
This is the biggest design weakness in the module.

### 2. Mixed policy and mechanism
Encryption enable/disable is treated as metadata, but key retrieval ignores it. Policy enforcement should happen at the service boundary.

### 3. Inconsistent error handling
Some functions fail loudly (`RuntimeError`), others swallow errors (`_audit_log`, `get_encryption_status` audit count).

### 4. Type annotations are too loose
Several functions return `tuple` instead of a typed tuple or named structure:
- `provision_dek`
- `get_workspace_dek`

This makes misuse easier.

### 5. No helper for Redis value normalization
Given likely Redis byte/string ambiguity, a small helper would improve reliability.

---

# Suggested Fixes Summary

## Highest priority
1. Enforce `secure_storage_enabled` in:
   - `kms_service.py:provision_dek`
   - `kms_service.py:get_workspace_dek`

2. Bind cache entries to both org and workspace:
   - `kms_service.py:_cache_get`
   - `kms_service.py:_cache_set`

3. Validate workspace ownership before DEK unwrap/provision:
   - `kms_service.py:provision_dek`

4. Invalidate org cache entries on disable:
   - `kms_service.py:disable_org_encryption`

## Next priority
5. Validate `wrapped.algorithm` in `_unwrap_key`
6. Use strict base64 decoding in `_get_root_key`
7. Add cache size control
8. Improve audit failure logging
9. Normalize Redis bytes/strings consistently

---

# Overall Assessment

## Security posture
This module has a decent cryptographic core, but the **security model around authorization and policy enforcement is incomplete**.

### Strong points
- AES-GCM envelope encryption design is sound
- Root/TMK/DEK hierarchy is sensible
- Random key generation is correct

### Main risks
- encryption disable flag is not enforced
- workspace/org ownership is not validated
- cache keying can cause cross-tenant confusion
- plaintext DEKs remain in memory
- org status leaks global audit volume

## Bottom line
The cryptography itself is mostly fine. The biggest issues are **access control, tenant isolation, and operational hardening**, not cipher misuse.

If you want, I can next provide:
1. a **prioritized remediation plan**, or
2. a **patched version of `kms_service.py` with only minimal surgical changes**.

---
*Generated by AiAS Code Analysis Buddy*
