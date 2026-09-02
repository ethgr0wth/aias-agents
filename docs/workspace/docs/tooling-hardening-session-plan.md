# Objective
Fix Redis delete bug, wire policy enforcement, add send_email BYOM, batch encryption backfill

# Tasks

### T001: Fix Redis wildcard delete bug in delete_custom_tool
- **Blocked By**: []
- **Details**:
  - Replace `self.r.delete(key(f"tool_secrets:{tool_id}:*"))` with SCAN-based deletion
  - Also fix delete_org_tool if it has the same bug
  - Files: `api/services/redis_storage.py`

### T002: Wire policy enforcement into tool execution
- **Blocked By**: []
- **Details**:
  - Call check_execution_policy + check_rate_limit in _handle_custom_tool_call
  - Set max 3-5 tool calls per turn (conservative default)
  - Track calls_this_turn in orchestrator loop
  - Apply to playground manual fallback path too
  - Files: `api/services/ai_orchestrator.py`, `api/services/tool_executor.py`

### T003: Add send_email built-in with BYOM SMTP
- **Blocked By**: []
- **Details**:
  - Add org-level SMTP config storage (host, port, user, pass, from_email)
  - Add API endpoint to configure SMTP credentials
  - Implement _builtin_send_email that uses org SMTP config
  - Add send_email to dispatcher and public catalog
  - Files: `api/services/tool_executor.py`, `api/routes/custom_tools.py`, `api/services/redis_storage.py`

### T004: Batch encryption backfill
- **Blocked By**: []
- **Details**:
  - Use Redis pipeline for bulk operations
  - Process messages in batches of 100
  - Add progress logging
  - Files: `api/services/kms_service.py`
