# AiAssist.net — Full API Reference

> **Injection-ready reference.** All routes are live on the FastAPI backend (port 8000, proxied via Express on 5000).
> Legacy versioned files (`public_api_v1`–`v11`, `_stable_*`, `_broken`) are archived — not mounted.

---

## Base URL & Auth

```
Base URL:  https://aiassist.net          (production)
           http://localhost:5000         (local dev, Express proxy)
           http://localhost:8000         (direct FastAPI)
```

### Authentication modes

| Mode | How | Applies to |
|---|---|---|
| **Session cookie** | `session_id=<value>` HTTP-only cookie set after login | All `/api/*` private routes |
| **Bearer API key** | `Authorization: Bearer aai_<key>` | `/v1/*` public integration API |
| **Bearer API key (proxy)** | Same header, routed via `/api/v1/*` | `/api/v1/*` proxy mirror of `/v1/*` |
| **Admin role** | Session cookie + `role: admin` or `super_admin` | All `/api/admin/*` routes |
| **PIN operator key** | `Authorization: Bearer <operator-api-key>` | PIN daemon/heartbeat endpoints |

---

## 1. Public Integration API — `/v1`

> Bearer `aai_<key>` required. Also mirrored at `/api/v1` for same-origin calls.

| Method | Path | Description |
|---|---|---|
| `POST` | `/v1/chat/completions` | OpenAI-compatible chat completions (BYOK multi-provider) |
| `GET` | `/v1/models` | List available models for the authenticated key |
| `GET` | `/v1/providers` | List configured providers for the key |
| `GET` | `/v1/usage` | Token/request usage for the API key |
| `GET` | `/v1/health` | Public health check (no auth) |
| `GET` | `/v1/organization` | Organization info tied to the key |
| `GET` | `/v1/provider` | Active provider details |
| `GET` | `/v1/availability` | Provider availability / rate-limit status |
| `POST` | `/v1/search` | Web search (BYOK) |
| `POST` | `/v1/web/extract` | Extract content from a URL |
| `GET` | `/v1/intelligence/sources` | SaaS-Signal: list 22+ signal sources |
| `POST` | `/v1/intelligence/scan` | SaaS-Signal: scan for buying/hiring/eval signals |
| `POST` | `/v1/intelligence/extract-keywords` | SaaS-Signal: extract intent keywords from text |

**Chat completions — key headers**

```
Authorization: Bearer aai_<key>
X-AiAssist-Provider: groq | openai | anthropic | gemini | mistral | openrouter | ...
X-AiAssist-Byok: <raw-api-key>        (optional, use your own key for this request)
X-Agent-Id: <deployed-agent-id>       (optional, target a specific deployed agent)
Content-Type: application/json
```

> Model is specified in the request body (`"model": "llama-3.3-70b-versatile"`), not a header.

---

## 2. Authentication — `/api/auth`

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/auth/login` | Password login → sets session cookie |
| `POST` | `/api/auth/verify-2fa` | Complete TOTP 2FA challenge |
| `POST` | `/api/auth/logout` | Destroy session |
| `GET` | `/api/auth/me` | Current session user (quick check) |
| `POST` | `/api/auth/register` | Create new account (requires `super_admin` session — not public signup) |
| `POST` | `/api/auth/setup` | First-run platform setup |
| `POST` | `/api/auth/recovery/check` | Check recovery code eligibility |
| `POST` | `/api/auth/recovery/verify` | Verify recovery code |

---

## 3. Users — `/api/user`

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/user/register` | Register user (alternative to auth/register) |
| `GET` | `/api/user/me` | Full current user profile |
| `PUT` | `/api/user/profile` | Update profile (name, avatar, etc.) |
| `PUT` | `/api/user/password` | Change password |
| `PUT` | `/api/user/social` | Update social links |
| `GET` | `/api/user/usage` | Personal usage stats |
| `GET` | `/api/user/models` | Models available to user |
| `GET` | `/api/user/workspaces` | List own workspaces |
| `GET` | `/api/user/workspaces/{workspace_id}` | Single workspace detail |
| `GET` | `/api/user/workspaces/{workspace_id}/customization` | Workspace customization settings |
| `PUT` | `/api/user/workspaces/{workspace_id}/customization` | Update workspace customization |
| **API Keys (basic)** | | |
| `GET` | `/api/user/api-keys` | List API keys |
| `POST` | `/api/user/api-keys` | Create API key |
| `DELETE` | `/api/user/api-keys/{key_id}` | Delete API key |
| **API Keys (extended)** | | |
| `GET` | `/api/user/api-keys-extended` | List extended API keys |
| `POST` | `/api/user/api-keys-extended` | Create extended key |
| `DELETE` | `/api/user/api-keys-extended/{key_id}` | Delete extended key |
| `GET` | `/api/user/api-keys-extended/{key_id}/usage` | Key usage log |
| `GET` | `/api/user/api-keys-extended/{key_id}/usage-stats` | Aggregated usage stats |
| `GET` | `/api/user/api-keys-extended/{key_id}/usage-limits` | Rate limits |
| `PUT` | `/api/user/api-keys-extended/{key_id}/usage-limits` | Set rate limits |
| `DELETE` | `/api/user/api-keys-extended/{key_id}/usage-limits` | Remove rate limits |
| **Providers** | | |
| `GET` | `/api/user/providers/groq` | Get Groq provider config |
| `POST` | `/api/user/providers/groq` | Save Groq API key |
| `DELETE` | `/api/user/providers/groq` | Remove Groq key |
| `GET` | `/api/user/groq-usage` | Groq usage |
| **TOTP** | | |
| `POST` | `/api/user/totp/setup` | Initialize TOTP setup |
| `POST` | `/api/user/totp/verify` | Verify + enable TOTP |
| `GET` | `/api/user/totp/status` | TOTP enabled status |
| `POST` | `/api/user/totp/disable` | Disable TOTP |
| **Training / Templates** | | |
| `GET` | `/api/user/training-contexts` | List training contexts |
| `POST` | `/api/user/training-contexts` | Create training context |
| `GET` | `/api/user/training-contexts/{ctx_id}` | Get training context |
| `PUT` | `/api/user/training-contexts/{ctx_id}` | Update training context |
| `DELETE` | `/api/user/training-contexts/{ctx_id}` | Delete training context |
| `GET` | `/api/user/response-templates` | List response templates |
| `POST` | `/api/user/response-templates` | Create response template |
| `GET` | `/api/user/response-templates/{tpl_id}` | Get template |
| `PUT` | `/api/user/response-templates/{tpl_id}` | Update template |
| `DELETE` | `/api/user/response-templates/{tpl_id}` | Delete template |
| **Layout** | | |
| `GET` | `/api/user/aios-layout` | Get AiOS dashboard layout config |
| `PUT` | `/api/user/aios-layout` | Save AiOS layout config |
| `GET` | `/api/user/onboarding` | Get onboarding state |
| `PUT` | `/api/user/onboarding` | Update onboarding state |
| `POST` | `/api/user/sync-organization` | Sync user into organization |

---

## 4. Workspaces — `/api/workspaces`

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/workspaces` | Create workspace |
| `GET` | `/api/workspaces` | List workspaces |
| `GET` | `/api/workspaces/by-client/{client_id}` | Look up workspace by client ID |
| `PATCH` | `/api/workspaces/bulk-mode` | Bulk update workspace modes |
| `GET` | `/api/workspaces/mode-summary` | Mode summary across all workspaces |
| `GET` | `/api/workspaces/drafts/pending` | All pending draft messages |
| `GET` | `/api/workspaces/{workspace_id}` | Get workspace |
| `PATCH` | `/api/workspaces/{workspace_id}` | Update workspace |
| `POST` | `/api/workspaces/{workspace_id}/clear-attention` | Clear attention flag |
| `GET` | `/api/workspaces/{workspace_id}/messages` | Get message history |
| `DELETE` | `/api/workspaces/{workspace_id}/messages` | Clear message history |
| `POST` | `/api/workspaces/{workspace_id}/messages` | Send message (chat) |
| `POST` | `/api/workspaces/{workspace_id}/admin-message` | Send admin-injected message |
| `GET` | `/api/workspaces/{workspace_id}/contact` | Get linked contact |
| `GET` | `/api/workspaces/{workspace_id}/directives` | Workspace-level directives |
| `POST` | `/api/workspaces/{workspace_id}/directives` | Add directive to workspace |
| `GET` | `/api/workspaces/{workspace_id}/typing` | Typing indicator state |
| `POST` | `/api/workspaces/{workspace_id}/typing` | Update typing indicator |
| **Memory / Facts** | | |
| `GET` | `/api/workspaces/{workspace_id}/memory/facts` | List memory facts |
| `POST` | `/api/workspaces/{workspace_id}/memory/facts` | Add memory fact |
| `PATCH` | `/api/workspaces/{workspace_id}/memory/facts/{content_hash}` | Update fact |
| `DELETE` | `/api/workspaces/{workspace_id}/memory/facts/{content_hash}` | Delete fact |
| `DELETE` | `/api/workspaces/{workspace_id}/memory/facts` | Clear all facts |
| **Shadow / Drafts** | | |
| `GET` | `/api/workspaces/{workspace_id}/drafts` | Pending drafts for workspace |
| `POST` | `/api/workspaces/drafts/{draft_id}/approve` | Approve draft → send |
| `POST` | `/api/workspaces/drafts/{draft_id}/reject` | Reject draft |
| `POST` | `/api/workspaces/drafts/{draft_id}/regenerate` | Regenerate draft |

---

## 5. Memory & Settings — `/api/*`

> All mounted at `/api` prefix. Covers conversation memory, web-search toggles, GDPR session export, and Tavily BYOK.

**Workspace memory**

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/workspaces/{workspace_id}/settings/memory` | Get memory config |
| `PATCH` | `/api/workspaces/{workspace_id}/settings/memory` | Update memory config |
| `GET` | `/api/workspaces/{workspace_id}/settings/web-search` | Get web-search toggle |
| `PATCH` | `/api/workspaces/{workspace_id}/settings/web-search` | Update web-search toggle |

**Organization memory defaults**

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/organization/defaults` | Org memory defaults |
| `PATCH` | `/api/organization/defaults` | Update org memory defaults |
| `GET` | `/api/organization/web-search-defaults` | Org web-search defaults |
| `PATCH` | `/api/organization/web-search-defaults` | Update org web-search defaults |
| `PATCH` | `/api/admin/organizations/{org_id}/memory-settings` | Override org memory settings (admin) |

**GDPR session export**

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/user/sessions/{session_id}/export` | Export session data (GDPR portability) |
| `DELETE` | `/api/user/sessions/{session_id}` | Delete session data (GDPR erasure) |

**Admin kill-switch**

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/admin/memory/kill-switch` | Enable/disable fact extraction globally |
| `GET` | `/api/admin/memory/status` | Memory system status + circuit-breaker state |
| `GET` | `/api/admin/memory/stats/{workspace_id}` | Memory stats for a workspace |

**Tavily BYOK (web search)**

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/byok/tavily` | Tavily key status |
| `POST` | `/api/byok/tavily` | Save Tavily API key |
| `DELETE` | `/api/byok/tavily` | Remove Tavily key |

---

## 6. Contacts — `/api/contacts`

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/contacts` | List contacts |
| `POST` | `/api/contacts` | Create contact |
| `GET` | `/api/contacts/{contact_id}` | Get contact |
| `PATCH` | `/api/contacts/{contact_id}` | Update contact |
| `PATCH` | `/api/contacts/{contact_id}/lifecycle` | Update lifecycle stage |

---

## 7. Directives — `/api/directives`

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/directives` | List directives |
| `POST` | `/api/directives` | Create directive |
| `GET` | `/api/directives/{directive_id}` | Get directive |
| `PATCH` | `/api/directives/{directive_id}` | Update directive |
| `DELETE` | `/api/directives/{directive_id}` | Delete directive |

---

## 8. Organizations — `/api/organizations`

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/organizations/me` | Get current user's organization |
| `POST` | `/api/organizations/` | Create organization |
| `GET` | `/api/organizations/{org_id}` | Get organization |
| `GET` | `/api/organizations/{org_id}/members` | List members |
| `GET` | `/api/organizations/{org_id}/seats` | List license seats |
| `GET` | `/api/organizations/my/members` | Members of own org |
| `GET` | `/api/organizations/my/seats` | Seats in own org |
| `GET` | `/api/organizations/my/availability` | Staff availability |
| `PUT` | `/api/organizations/my/availability` | Update staff availability |

---

## 9. Encryption (Secure Tier) — `/api/admin/organizations`

> Admin only. Double-envelope AES-256-GCM per-org encryption.

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/admin/organizations/{org_id}/enable-secure` | Enable Secure Tier (generates TMK) |
| `POST` | `/api/admin/organizations/{org_id}/disable-secure` | Disable Secure Tier |
| `GET` | `/api/admin/organizations/{org_id}/encryption-status` | Check encryption status |

---

## 10. Providers (BYOK) — `/api/providers`

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/providers` | Platform-level provider list |
| `GET` | `/api/providers/models` | Dynamic model list across providers |
| `GET` | `/api/providers/all` | All providers (admin view) |
| `GET` | `/api/providers/user` | User's configured providers |
| `GET` | `/api/providers/user/{provider}/keys` | Keys for a provider |
| `POST` | `/api/providers/user/{provider}` | Add/update provider key |
| `DELETE` | `/api/providers/user/{provider}` | Remove provider |
| `GET` | `/api/providers/user/default` | Get default provider |
| `PUT` | `/api/providers/user/default` | Set default provider |
| `GET` | `/api/providers/user/priority` | Provider priority order |
| `PUT` | `/api/providers/user/priority` | Update provider priority |
| `GET` | `/api/providers/user/pin/enabled` | PIN provider enabled flag |
| `PUT` | `/api/providers/user/pin/enabled` | Toggle PIN provider |
| `PUT` | `/api/providers/user/credentials/{cred_id}/role` | Update credential role |
| `DELETE` | `/api/providers/user/credentials/{cred_id}` | Delete credential |
| `GET` | `/api/providers/user/{provider}/active` | Check if provider is active |
| `GET` | `/api/providers/user/models/preferences` | Model preferences (all providers) |
| `GET` | `/api/providers/user/{provider}/models/preferences` | Model preferences per provider |
| `PUT` | `/api/providers/user/models/preferences` | Save model preferences |

---

## 11. Licenses — `/api/licenses` + `/api/admin/licenses`

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/licenses/activate` | Activate a license key |
| `GET` | `/api/licenses/me` | Current user's license |
| `GET` | `/api/licenses/v2/my-license` | Enhanced current license |
| `POST` | `/api/licenses/v2/activate` | Activate v2 license |
| `POST` | `/api/licenses/v2/claim` | Claim a distributed seat |
| `GET` | `/api/licenses/v2/plans` | List subscription plans |
| `GET` | `/api/licenses/v2/plans/{plan_code}` | Get plan by code |
| `GET` | `/api/licenses/v2/validate/{license_key}` | Validate a key |
| `GET` | `/api/licenses/v2/all` | All licenses (admin scope) |
| `POST` | `/api/licenses/v2/batches` | Create license batch |
| `GET` | `/api/licenses/v2/batches` | List batches |
| `GET` | `/api/licenses/v2/batches/{batch_id}` | Get batch |
| `GET` | `/api/licenses/v2/enhanced/{license_id}` | Enhanced license detail |
| `GET` | `/api/licenses/v2/audit-logs` | License audit log |
| `GET` | `/api/licenses/v2/hierarchy` | Full license hierarchy |
| `GET` | `/api/licenses/v2/hierarchy/{parent_license_id}` | Hierarchy from parent |
| `POST` | `/api/licenses/v2/hierarchy/repair` | Repair hierarchy |
| `POST` | `/api/licenses/v2/distribute` | Distribute child licenses |
| `POST` | `/api/licenses/v2/child/{license_id}/revoke` | Revoke child license |
| `POST` | `/api/licenses/v2/child/{license_id}/regenerate` | Regenerate child license |
| **Admin** | | |
| `GET` | `/api/admin/licenses` | List all licenses |
| `GET` | `/api/admin/licenses/{license_id}` | Get license |
| `POST` | `/api/admin/licenses/{license_id}/revoke` | Revoke |
| `POST` | `/api/admin/licenses/{license_id}/reactivate` | Reactivate |
| `PATCH` | `/api/admin/licenses/{license_id}/adjust` | Adjust license |

> Note: `generate`, `generate-batch` are on the user-facing `/api/licenses` router (lines 192/205), not the admin router.

---

## 12. Seats — `/api/seats`

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/seats/invite` | Invite user to a seat |
| `POST` | `/api/seats/claim` | Claim seat invite |
| `POST` | `/api/seats/revoke` | Revoke seat |
| `GET` | `/api/seats/my` | Current user's seat info |
| `GET` | `/api/seats/validate/{token}` | Validate invite token |
| `GET` | `/api/seats/{seat_id}` | Get seat |

---

## 13. Subscription — `/api/subscription` + `/api/admin/subscriptions`

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/subscription/status` | Current subscription status |
| `POST` | `/api/subscription/activate` | Activate subscription |
| `POST` | `/api/subscription/cancel` | Cancel subscription |
| `POST` | `/api/subscription/reactivate` | Reactivate subscription |
| `GET` | `/api/subscription/history` | Subscription history |
| **Admin** | | |
| `GET` | `/api/admin/subscriptions` | List all subscriptions |
| `GET` | `/api/admin/subscriptions/expiring` | Expiring soon |
| `POST` | `/api/admin/subscriptions/{sub_id}/extend` | Extend subscription |
| `POST` | `/api/admin/subscriptions/{sub_id}/revoke` | Revoke subscription |

---

## 14. Billing — `/api/billing`

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/billing/seat-pricing` | Seat pricing info |
| `POST` | `/api/billing/checkout` | Create Stripe checkout session |
| `GET` | `/api/billing/my-subscription` | Current user subscription + Stripe data |
| `POST` | `/api/billing/upgrade-seats` | Add seats via Stripe |
| `POST` | `/api/billing/upgrade-to-team` | Upgrade to team plan |
| `GET` | `/api/billing/pin/credit-packs` | PIN credit pack options |
| `POST` | `/api/billing/pin/purchase-credits` | Purchase PIN credits |
| `GET` | `/api/billing/pin/balance` | PIN credit balance |

---

## 15. Pricing — `/api/pricing` + `/api/admin/pricing`

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/pricing/config` | Public pricing config (phases, tiers) |
| **Admin** | | |
| `GET` | `/api/admin/pricing/config` | Full pricing config |
| `PUT` | `/api/admin/pricing/phase` | Update active phase |
| `POST` | `/api/admin/pricing/phase` | Create phase |
| `DELETE` | `/api/admin/pricing/phase/{phase_id}` | Delete phase |
| `PUT` | `/api/admin/pricing/countdown` | Update countdown |
| `PUT` | `/api/admin/pricing/tier` | Update tier |
| `POST` | `/api/admin/pricing/reset` | Reset pricing config |

---

## 16. Templates — `/api/templates`

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/templates` | List templates |
| `GET` | `/api/templates/categories` | Template categories |
| `GET` | `/api/templates/{template_id}` | Get template |
| `POST` | `/api/templates` | Create template |
| `PUT` | `/api/templates/{template_id}` | Update template |
| `DELETE` | `/api/templates/{template_id}` | Delete template |
| `POST` | `/api/templates/{template_id}/deploy` | Deploy template to workspace |
| `POST` | `/api/templates/{template_id}/clone` | Clone template |
| `DELETE` | `/api/templates/deployments/global` | Remove all global deployments |
| `DELETE` | `/api/templates/deployments/workspace/{workspace_id}` | Remove workspace deployments |

---

## 17. Deployed Agents — `/api/deployed-agents`

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/deployed-agents` | Deploy an agent |
| `GET` | `/api/deployed-agents` | List deployed agents |
| `GET` | `/api/deployed-agents/active` | Currently active agent |
| `GET` | `/api/deployed-agents/{agent_id}` | Get agent |
| `GET` | `/api/deployed-agents/{agent_id}/integration` | Integration code snippets |
| `PATCH` | `/api/deployed-agents/{agent_id}` | Update agent |
| `POST` | `/api/deployed-agents/{agent_id}/activate` | Activate agent |
| `POST` | `/api/deployed-agents/deactivate` | Deactivate active agent |
| `POST` | `/api/deployed-agents/{agent_id}/redeploy` | Redeploy agent |
| `DELETE` | `/api/deployed-agents/{agent_id}` | Delete agent |
| `POST` | `/api/deployed-agents/{agent_id}/archive` | Archive agent |

---

## 18. Playground — `/api/playground`

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/playground/sessions` | Create playground session |
| `GET` | `/api/playground/sessions` | List sessions |
| `GET` | `/api/playground/sessions/{session_id}` | Get session |
| `PATCH` | `/api/playground/sessions/{session_id}` | Update session |
| `DELETE` | `/api/playground/sessions/{session_id}` | Delete session |
| `POST` | `/api/playground/sessions/{session_id}/chat` | Send message (sync) |
| `POST` | `/api/playground/sessions/{session_id}/chat/stream` | Send message (SSE stream) |
| `DELETE` | `/api/playground/sessions/{session_id}/messages` | Clear history |
| `POST` | `/api/playground/sessions/{session_id}/directives` | Add directive |
| `DELETE` | `/api/playground/sessions/{session_id}/directives/{index}` | Remove directive |
| `POST` | `/api/playground/sessions/{session_id}/knowledge` | Add knowledge item |
| `DELETE` | `/api/playground/sessions/{session_id}/knowledge/{item_id}` | Remove knowledge |
| `POST` | `/api/playground/sessions/{session_id}/attachments` | Upload attachment |
| `DELETE` | `/api/playground/sessions/{session_id}/attachments/{attachment_id}` | Remove attachment |
| `POST` | `/api/playground/sessions/{session_id}/apply-template` | Apply template |

---

## 19. Code Generator — `/api/code-generator`

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/code-generator/models` | Models available for code generation |
| `POST` | `/api/code-generator/generate` | Generate code from prompt |
| `POST` | `/api/code-generator/regenerate` | Regenerate with updated prompt |
| `POST` | `/api/code-generator/quick-edit` | Quick in-line edit |
| `GET` | `/api/code-generator/history` | Generation history |
| `GET` | `/api/code-generator/{generation_id}` | Get generation |
| `GET` | `/api/code-generator/{generation_id}/download` | Download generated file |
| `DELETE` | `/api/code-generator/{generation_id}` | Delete generation |

---

## 20. Keystone IDE — `/api/keystone`

> Full IDE workspace with file system, chat, terminal, git, and deploy tabs.

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/keystone/status` | Keystone service status |
| **Environments (Keystone workspaces)** | | |
| `GET` | `/api/keystone/environments` | List environments |
| `POST` | `/api/keystone/environments` | Create environment |
| `GET` | `/api/keystone/environments/{env_id}` | Get environment |
| `PATCH` | `/api/keystone/environments/{env_id}` | Update environment |
| `DELETE` | `/api/keystone/environments/{env_id}` | Delete environment |
| **File System** | | |
| `GET` | `/api/keystone/environments/{env_id}/files/tree` | Directory tree |
| `GET` | `/api/keystone/environments/{env_id}/files/read` | Read file |
| `POST` | `/api/keystone/environments/{env_id}/files/write` | Write file |
| `POST` | `/api/keystone/environments/{env_id}/files/edit` | Edit file (patch) |
| `POST` | `/api/keystone/environments/{env_id}/files/edit/preview` | Preview edit diff |
| `GET` | `/api/keystone/environments/{env_id}/files/hash` | File hash |
| `GET` | `/api/keystone/environments/{env_id}/files/download` | Download file |
| `GET` | `/api/keystone/environments/{env_id}/files/download-all` | Download all as zip |
| `POST` | `/api/keystone/environments/{env_id}/files/mkdir` | Create directory |
| `DELETE` | `/api/keystone/environments/{env_id}/files/delete` | Delete file/dir |
| `POST` | `/api/keystone/environments/{env_id}/files/rename` | Rename file |
| `GET` | `/api/keystone/environments/{env_id}/files/glob` | Glob file search |
| `GET` | `/api/keystone/environments/{env_id}/files/grep` | Grep in files |
| **Code Analysis** | | |
| `GET` | `/api/keystone/environments/{env_id}/files/analyze/functions` | Function map |
| `GET` | `/api/keystone/environments/{env_id}/files/analyze/brackets` | Bracket tracker |
| `GET` | `/api/keystone/environments/{env_id}/files/function` | Get single function |
| `GET` | `/api/keystone/environments/{env_id}/files/functions` | All functions |
| **Chat (AI Assistant)** | | |
| `GET` | `/api/keystone/environments/{env_id}/chat/history` | Chat history |
| `DELETE` | `/api/keystone/environments/{env_id}/chat/history` | Clear history |
| `POST` | `/api/keystone/environments/{env_id}/chat/reset-context` | Reset context |
| `POST` | `/api/keystone/environments/{env_id}/chat` | Chat (sync) |
| `POST` | `/api/keystone/environments/{env_id}/chat/stream` | Chat (SSE stream) |
| **Processes / Terminal** | | |
| `POST` | `/api/keystone/environments/{env_id}/run` | Start process |
| `POST` | `/api/keystone/environments/{env_id}/stop` | Stop process |
| `GET` | `/api/keystone/environments/{env_id}/process` | Get process status |
| `GET` | `/api/keystone/environments/{env_id}/logs` | Stream/get logs |
| `POST` | `/api/keystone/environments/{env_id}/restart` | Restart process |
| **Git** | | |
| `POST` | `/api/keystone/environments/{env_id}/git/init` | Init git repo |
| `GET` | `/api/keystone/environments/{env_id}/git/status` | Git status |
| `POST` | `/api/keystone/environments/{env_id}/git/add` | Stage files |
| `POST` | `/api/keystone/environments/{env_id}/git/commit` | Commit |
| `GET` | `/api/keystone/environments/{env_id}/git/log` | Commit log |
| **GitHub** | | |
| `POST` | `/api/keystone/environments/{env_id}/github/clone` | Clone from GitHub |
| **Templates** | | |
| `GET` | `/api/keystone/templates` | List deploy templates |
| `GET` | `/api/keystone/templates/{template_id}` | Get deploy template |

---

## 21. Environments (License/Team) — `/api/environments`

> Separate from Keystone. Manages team environments and member access.

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/environments/` | List environments |
| `POST` | `/api/environments/` | Create environment |
| `POST` | `/api/environments/initialize` | Initialize environment |
| `GET` | `/api/environments/overview` | License overview |
| `GET` | `/api/environments/members` | List members |
| `PATCH` | `/api/environments/members/{target_user_id}` | Update member role |
| `DELETE` | `/api/environments/members/{target_user_id}` | Remove member |
| `POST` | `/api/environments/switch` | Switch active environment |
| `GET` | `/api/environments/{env_id}` | Get environment |
| `PATCH` | `/api/environments/{env_id}` | Update environment |
| `DELETE` | `/api/environments/{env_id}` | Delete environment |
| `GET` | `/api/environments/{env_id}/members` | List env members |
| `POST` | `/api/environments/{env_id}/members/{target_user_id}` | Add member |
| `DELETE` | `/api/environments/{env_id}/members/{target_user_id}` | Remove member |

---

## 22. Runtime (AiOS Server A) — `/api/runtime`

> Proxies to Server B (port 8099). Requires session cookie or `Bearer aai_<key>`.
> Returns `503` if `RUNTIME_REMOTE_URL` is not configured.

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/runtime/health` | Runtime health |
| `POST` | `/api/runtime/handshake` | HMAC handshake with Server B |
| `POST` | `/api/runtime/sessions` | Create session |
| `GET` | `/api/runtime/sessions` | List sessions |
| `POST` | `/api/runtime/sessions/{session_id}/reset` | Reset session |
| `DELETE` | `/api/runtime/sessions/{session_id}` | Destroy session |
| `POST` | `/api/runtime/sessions/{session_id}/cleanup` | Cleanup workspace files |
| `POST` | `/api/runtime/sessions/{session_id}/respawn` | Respawn from bare repo |
| `POST` | `/api/runtime/sessions/{session_id}/commit_message` | Generate commit message |
| `POST` | `/api/runtime/sessions/{session_id}/flush_commit` | Flush and commit |
| `POST` | `/api/runtime/sync_workspace` | Sync Keystone env → Server B |
| **Deployment tools** | | |
| `POST` | `/api/runtime/clone_repo` | Clone repository |
| `POST` | `/api/runtime/checkout_ref` | Checkout git ref |
| `POST` | `/api/runtime/detect_stack` | Detect stack (Node/Python/etc) |
| `POST` | `/api/runtime/install_node_deps` | npm/pnpm/yarn install |
| `POST` | `/api/runtime/install_python_deps` | pip install |
| `POST` | `/api/runtime/write_env_file` | Write .env file |
| `POST` | `/api/runtime/list_processes` | List running processes |
| `POST` | `/api/runtime/start_process` | Start process |
| `POST` | `/api/runtime/stop_process` | Stop process |
| `POST` | `/api/runtime/check_port` | Check if port is open |
| `POST` | `/api/runtime/http_health_check` | HTTP health check |
| `POST` | `/api/runtime/stream_logs` | Stream process logs |
| `POST` | `/api/runtime/capture_preview_metadata` | Capture preview metadata |
| `POST` | `/api/runtime/export_artifacts` | Export build artifacts |
| `POST` | `/api/runtime/export_artifact` | Export single artifact |
| **Code execution** | | |
| `POST` | `/api/runtime/run_code` | Execute Python or Node code |
| `POST` | `/api/runtime/install_package` | Install package at runtime |
| `POST` | `/api/runtime/list_directory` | List directory |
| `POST` | `/api/runtime/read_file` | Read file |
| `POST` | `/api/runtime/write_file` | Write file |
| `POST` | `/api/runtime/search_in_files` | Search in files |
| `POST` | `/api/runtime/functions_mapping` | Python function map |
| `POST` | `/api/runtime/bracket_tracker` | Bracket analysis |
| **Ledger** | | |
| `GET` | `/api/runtime/ledger` | Session tool invocation ledger |
| `GET` | `/api/runtime/ledger/all` | Full ledger (all sessions) |
| **Git HTTP (smart HTTP server)** | | |
| `GET` | `/api/runtime/git/{session_id}/info/refs` | Git info/refs |
| `POST` | `/api/runtime/git/{session_id}/git-upload-pack` | Git fetch/clone |
| `POST` | `/api/runtime/git/{session_id}/git-receive-pack` | Git push |
| **Activity tracking** | | |
| `POST` | `/api/runtime/activity/{session_id}` | Record activity event |
| `GET` | `/api/runtime/activity/{session_id}` | Get activity log |
| `GET` | `/api/runtime/activity/{session_id}/summary` | Activity summary |
| **Admin** | | |
| `GET` | `/api/runtime/admin/sessions` | List all sessions |
| `DELETE` | `/api/runtime/admin/sessions/{session_id}` | Force destroy session |
| `GET` | `/api/runtime/admin/sessions/stats` | Session aggregates |
| `GET` | `/api/runtime/admin/sessions/{session_id}/activity` | Full activity stream |
| `GET` | `/api/runtime/admin/activity/user/{user_id}` | Activity by user |

---

## 23. Custom Tools — `/api/workspaces` + `/api/org`

**Private (workspace-scoped) tools**

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/workspaces/{workspace_id}/tools` | List workspace tools |
| `POST` | `/api/workspaces/{workspace_id}/tools` | Create tool |
| `GET` | `/api/workspaces/{workspace_id}/tools/{tool_id}` | Get tool |
| `PUT` | `/api/workspaces/{workspace_id}/tools/{tool_id}` | Update tool |
| `DELETE` | `/api/workspaces/{workspace_id}/tools/{tool_id}` | Delete tool |
| `POST` | `/api/workspaces/{workspace_id}/tools/{tool_id}/test` | Test tool |
| `GET` | `/api/workspaces/{workspace_id}/tools/{tool_id}/invocations` | Invocation log |
| `POST` | `/api/workspaces/{workspace_id}/tools/{tool_id}/replay/{invocation_id}` | Replay invocation |
| `GET` | `/api/workspaces/{workspace_id}/tools-policy` | Get tool policy |
| `PUT` | `/api/workspaces/{workspace_id}/tools-policy` | Update tool policy |
| `DELETE` | `/api/workspaces/{workspace_id}/tools-policy` | Remove tool policy |

**Org-level tools + public catalog**

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/org/tools` | List org tools |
| `POST` | `/api/org/tools` | Create org tool |
| `POST` | `/api/org/tools/test-webhook` | Test webhook tool |
| `GET` | `/api/org/tools/public/catalog` | Public platform tool catalog |
| `POST` | `/api/org/tools/public/{tool_id}/enable` | Enable public tool for org |
| `POST` | `/api/org/tools/public/{tool_id}/disable` | Disable public tool |
| `POST` | `/api/org/tools/public/{tool_id}/test` | Test public tool |
| `GET` | `/api/org/tools/{tool_id}` | Get org tool |
| `PUT` | `/api/org/tools/{tool_id}` | Update org tool |
| `DELETE` | `/api/org/tools/{tool_id}` | Delete org tool |
| `POST` | `/api/org/tools/{tool_id}/test` | Test org tool |
| `GET` | `/api/org/tools/{tool_id}/invocations` | Invocation log |
| `POST` | `/api/org/tools/{tool_id}/replay/{invocation_id}` | Replay |
| **SMTP config** | | |
| `GET` | `/api/org/smtp` | Get SMTP config |
| `PUT` | `/api/org/smtp` | Set SMTP config |
| `DELETE` | `/api/org/smtp` | Remove SMTP config |
| `POST` | `/api/org/smtp/test` | Send test email |
| **NetRows integration** | | |
| `GET` | `/api/org/netrows` | Get NetRows config |
| `PUT` | `/api/org/netrows` | Set NetRows API key + config |
| `DELETE` | `/api/org/netrows` | Remove NetRows config |
| `GET` | `/api/org/netrows/usage` | NetRows usage stats |

---

## 24. Blog — `/api/blog`

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/blog/blogs` | List blogs |
| `POST` | `/api/blog/blogs` | Create blog |
| `GET` | `/api/blog/blogs/by-slug/{slug}` | Get blog by slug |
| `GET` | `/api/blog/blogs/by-slug/{slug}/posts` | Get posts by blog slug |
| `GET` | `/api/blog/blogs/{blog_id}` | Get blog |
| `PATCH` | `/api/blog/blogs/{blog_id}` | Update blog |
| `DELETE` | `/api/blog/blogs/{blog_id}` | Delete blog |
| `GET` | `/api/blog/blogs/{blog_id}/posts` | List posts |
| `POST` | `/api/blog/blogs/{blog_id}/posts` | Create post |
| `GET` | `/api/blog/posts/{post_id}` | Get post |
| `PATCH` | `/api/blog/posts/{post_id}` | Update post |
| `DELETE` | `/api/blog/posts/{post_id}` | Delete post |
| `GET` | `/api/blog/blogs/{blog_id}/domains` | List custom domains |
| `POST` | `/api/blog/blogs/{blog_id}/domains` | Add custom domain |
| `DELETE` | `/api/blog/domains/{domain_id}` | Remove domain |
| `GET` | `/api/blog/blogs/{blog_id}/widgets` | List widgets |
| `POST` | `/api/blog/blogs/{blog_id}/widgets` | Create widget |
| `PATCH` | `/api/blog/widgets/{widget_id}` | Update widget |
| `DELETE` | `/api/blog/widgets/{widget_id}` | Delete widget |
| **AI generation** | | |
| `POST` | `/api/blog/blogs/{blog_id}/generate/post` | AI-generate full post |
| `POST` | `/api/blog/blogs/{blog_id}/generate/outline` | Generate outline |
| `POST` | `/api/blog/blogs/{blog_id}/generate/expand` | Expand section |
| `POST` | `/api/blog/blogs/{blog_id}/generate/rewrite` | Rewrite section |
| `POST` | `/api/blog/blogs/{blog_id}/generate/seo` | Generate SEO metadata |

---

## 25. Embed — `/api/embed` + `/api/public`

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/embed/{embed_token}` | Get embed config |
| `GET` | `/api/embed/{embed_token}/posts/{post_slug}` | Get embeddable post |
| `GET` | `/api/embed/{embed_token}/config` | Embed display config |
| `GET` | `/api/public/blog/{blog_slug}` | Public blog view (no auth) |

---

## 26. Text-to-Speech — `/api/tts`

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/tts/synthesize` | Synthesize speech (Google TTS) |
| `POST` | `/api/tts/byok/google-tts` | Save user's Google TTS credentials |
| `GET` | `/api/tts/byok/google-tts` | Get BYOK TTS config |
| `DELETE` | `/api/tts/byok/google-tts` | Remove BYOK TTS config |
| `GET` | `/api/tts/usage` | TTS usage stats |
| `GET` | `/api/tts/voices` | Available voices |
| **Admin** | | |
| `GET` | `/api/tts/admin/config` | Platform TTS config |
| `POST` | `/api/tts/admin/config` | Update TTS config |
| `POST` | `/api/tts/admin/reset-usage` | Reset usage counters |

---

## 27. Voice Actions — `/api/voice/actions`

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/voice/actions/explain` | AI-explain a voice input |
| `POST` | `/api/voice/actions/summarize` | Summarize voice input |
| `POST` | `/api/voice/actions/extract-actions` | Extract action items |
| `POST` | `/api/voice/actions/decision` | Decision support from voice |

---

## 28. Documents — `/api/documents`

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/documents/extract` | Extract text/structure from uploaded doc |

---

## 29. Web Extraction — `/api/web-extraction`

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/web-extraction/extract` | Extract content from URL |
| `POST` | `/api/web-extraction/batch` | Batch URL extraction |
| `GET` | `/api/web-extraction/usage` | Extraction usage |

---

## 30. Image Generation — `/api/image`

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/image/generate` | Generate image (BYOK provider) |

---

## 31. Flashcards — `/api/flashcards`

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/flashcards/decks` | List decks |
| `GET` | `/api/flashcards/providers` | Supported providers |
| `POST` | `/api/flashcards/decks/manual` | Create deck (manual cards) |
| `POST` | `/api/flashcards/decks/generate` | AI-generate deck from prompt/text/doc |
| `GET` | `/api/flashcards/decks/{deck_id}` | Get deck + cards |
| `PATCH` | `/api/flashcards/decks/{deck_id}` | Update deck |
| `DELETE` | `/api/flashcards/decks/{deck_id}` | Delete deck |
| `POST` | `/api/flashcards/decks/{deck_id}/cards` | Add card to deck |
| `PATCH` | `/api/flashcards/cards/{card_id}` | Edit card |
| `DELETE` | `/api/flashcards/cards/{card_id}` | Delete card |
| `POST` | `/api/flashcards/cards/{card_id}/regenerate-distractors` | Regen multiple-choice distractors |
| `GET` | `/api/flashcards/decks/{deck_id}/study/next` | Get next card (SM-2 spaced repetition) |
| `POST` | `/api/flashcards/cards/{card_id}/review` | Submit review rating (again/hard/good/easy) |

**Required headers for AI calls:**
```
X-AiAssist-Provider: groq | openai | anthropic | ...
X-AiAssist-Model: <model-id>
```

---

## 32. P2P Inference Network (PIN) — `/api/v1/pin` + `/api/admin/pin`

> Decentralized Ollama inference marketplace.

**Operator (self-service)**

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/pin/operator/me` | Get own operator profile |
| `GET` | `/api/v1/pin/operator/me/nodes` | List own nodes |
| `POST` | `/api/v1/pin/operator/me/nodes` | Register node |
| `GET` | `/api/v1/pin/operator/me/health` | Node health status |
| `GET` | `/api/v1/pin/operator/me/status` | Operator status / tier |
| `GET` | `/api/v1/pin/operator/me/earnings` | Earnings summary |
| `GET` | `/api/v1/pin/operator/me/interview` | Interview status + results |
| `POST` | `/api/v1/pin/operator/me/interview/request` | Request interview |
| `POST` | `/api/v1/pin/operator/me/reputation/reset` | Reset reputation |
| `GET` | `/api/v1/pin/operator/me/wallet` | Wallet info |
| `PUT` | `/api/v1/pin/operator/me/wallet` | Update wallet |
| `GET` | `/api/v1/pin/operator/me/pricing` | Custom pricing |
| `PUT` | `/api/v1/pin/operator/me/pricing` | Set custom pricing |
| `GET` | `/api/v1/pin/operator/me/withdrawals` | Withdrawal history |
| `POST` | `/api/v1/pin/operator/me/withdrawals` | Request withdrawal |
| `GET` | `/api/v1/pin/operator/me/api-key` | Get operator API key |
| `POST` | `/api/v1/pin/operator/me/regenerate-api-key` | Regenerate API key |
| `PATCH` | `/api/v1/pin/operator/me/nodes/{node_id}` | Update node |
| `DELETE` | `/api/v1/pin/operator/me/nodes/{node_id}` | Remove node |
| `POST` | `/api/v1/pin/operator/me/nodes/{node_id}/regenerate-credentials` | Rotate node credentials |

**Network (public/shared)**

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/pin/network/status` | Network status |
| `GET` | `/api/v1/pin/network/stats` | Network stats |
| `GET` | `/api/v1/pin/network/operators` | Public operator list |
| `GET` | `/api/v1/pin/network/models` | Available models on network |
| `GET` | `/api/v1/pin/network/health` | Network health |
| `GET` | `/api/v1/pin/pricing/summary` | Network pricing |
| `GET` | `/api/v1/pin/config/operator-share` | Operator revenue share config |

**Multi-operator**

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/pin/operators/{operator_id}/nodes` | List nodes for operator |
| `POST` | `/api/v1/pin/operators/{operator_id}/nodes` | Add node for operator |
| `GET` | `/api/v1/pin/operators/{operator_id}/status` | Operator status |
| `GET` | `/api/v1/pin/operators/{operator_id}/earnings` | Earnings |
| `GET` | `/api/v1/pin/operators/{operator_id}/wallet` | Wallet |
| `PUT` | `/api/v1/pin/operators/{operator_id}/wallet` | Update wallet |
| `POST` | `/api/v1/pin/operators/{operator_id}/withdraw` | Withdraw |
| `GET` | `/api/v1/pin/operators/{operator_id}/withdrawals` | Withdrawal history |

**Node management**

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/pin/nodes/{node_id}` | Get node |
| `PATCH` | `/api/v1/pin/nodes/{node_id}` | Update node |
| `DELETE` | `/api/v1/pin/nodes/{node_id}` | Delete node |
| `POST` | `/api/v1/pin/nodes/{node_id}/regenerate-credentials` | Rotate credentials |
| `POST` | `/api/v1/pin/nodes/{node_id}/set-primary` | Set primary node |

**Registration / Daemon**

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/pin/operators/register` | Register as operator |
| `POST` | `/api/v1/pin/daemon/register` | Daemon auto-register |
| `POST` | `/api/v1/pin/operators/heartbeat` | Operator heartbeat |
| `POST` | `/api/v1/pin/operators/verify-endpoint` | Verify inference endpoint |
| `POST` | `/api/v1/pin/test-credentials` | Test node credentials |

**Inference**

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/v1/pin/chat/completions` | OpenAI-compatible inference via PIN |
| `WS` | `/api/v1/pin/ws` | WebSocket inference stream |

**Credits**

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/v1/pin/credits/balance` | Credit balance |
| `POST` | `/api/v1/pin/credits/add` | Add credits |

**Admin**

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/admin/pin/operators` | List all operators |
| `PATCH` | `/api/admin/pin/operators/{operator_id}/status` | Override operator status |
| `POST` | `/api/admin/pin/seed-test-operator` | Seed test operator |
| `GET` | `/api/admin/pin/config/protocol-fee` | Protocol fee config |
| `PATCH` | `/api/admin/pin/config/protocol-fee` | Update protocol fee |
| `GET` | `/api/admin/pin/withdrawals` | All withdrawal requests |
| `PATCH` | `/api/admin/pin/withdrawals/{withdrawal_id}/process` | Process withdrawal |
| `PATCH` | `/api/admin/pin/withdrawals/{withdrawal_id}/reject` | Reject withdrawal |
| `GET` | `/api/v1/pin/admin/thresholds` | Interview quality thresholds |
| `PUT` | `/api/v1/pin/admin/thresholds` | Update thresholds |
| `POST` | `/api/v1/pin/admin/thresholds/reset` | Reset to defaults |

---

## 33. Artifacts — `/api/artifacts`

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/artifacts` | Create artifact |
| `GET` | `/api/artifacts` | List artifacts |
| `GET` | `/api/artifacts/{artifact_id}` | Get artifact |
| `PATCH` | `/api/artifacts/{artifact_id}` | Update artifact |
| `DELETE` | `/api/artifacts/{artifact_id}` | Delete artifact |

---

## 34. Change Log — `/api/change-log`

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/change-log` | List change log entries |
| `GET` | `/api/change-log/entity-types` | Available entity types |
| `GET` | `/api/change-log/stats` | Change log stats |

---

## 35. Policy Snapshots — `/api/policy-snapshots`

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/policy-snapshots` | List snapshots |
| `GET` | `/api/policy-snapshots/{snapshot_id}` | Get snapshot |
| `POST` | `/api/policy-snapshots` | Create snapshot |
| `POST` | `/api/policy-snapshots/{snapshot_id}/restore` | Restore from snapshot |
| `DELETE` | `/api/policy-snapshots/{snapshot_id}` | Delete snapshot |
| `GET` | `/api/policy-snapshots/compare/{snapshot_a_id}/{snapshot_b_id}` | Diff two snapshots |

---

## 36. Control Center — `/api/control-center`

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/control-center` | Get control center config (all operator switches) |
| `POST` | `/api/control-center/audit-event` | Log audit event |

---

## 37. Leads — `/api/leads`

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/leads/capture` | Capture email lead |
| `GET` | `/api/leads/check/{client_id}` | Check if client has lead |
| `GET` | `/api/leads` | List leads |
| `GET` | `/api/leads/{lead_id}` | Get lead |
| `PATCH` | `/api/leads/{lead_id}` | Update lead |
| `PATCH` | `/api/leads/{lead_id}/workspace` | Link lead to workspace |

---

## 38. Reseller — `/api/reseller` + `/invite` + `/api/admin/resellers` + `/api/admin/payout-claims`

**Reseller (self-service)**

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/reseller/config` | Get reseller config |
| `GET` | `/api/reseller/profile` | Get reseller profile |
| `PUT` | `/api/reseller/profile` | Update profile |
| `GET` | `/api/reseller/links` | List referral links |
| `POST` | `/api/reseller/links` | Create referral link |
| `GET` | `/api/reseller/leads` | Referred leads |
| `GET` | `/api/reseller/conversions` | Conversions |
| `GET` | `/api/reseller/earnings` | Earnings |
| `GET` | `/api/reseller/quota` | Quota usage |
| `GET` | `/api/reseller/payouts` | Payout history |
| `POST` | `/api/reseller/payouts/claim` | Claim payout |

**Public (invite links)**

| Method | Path | Description |
|---|---|---|
| `GET` | `/invite/{link_code}` | Resolve referral link |
| `POST` | `/invite/leads/capture` | Capture referred lead |

**Admin**

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/admin/resellers/config` | Set reseller program config |
| `GET` | `/api/admin/resellers/config` | Get reseller program config |
| `GET` | `/api/admin/resellers` | List resellers |
| `GET` | `/api/admin/resellers/stats` | Program stats |
| `GET` | `/api/admin/resellers/leads` | All referred leads |
| `GET` | `/api/admin/resellers/conversions/pending` | Pending conversions |
| `GET` | `/api/admin/resellers/{reseller_id}` | Get reseller |
| `PUT` | `/api/admin/resellers/{reseller_id}` | Update reseller |
| `POST` | `/api/admin/resellers/create` | Create reseller account |
| `POST` | `/api/admin/resellers/run-quota-check` | Run quota enforcement |
| **Payout claims** | | |
| `GET` | `/api/admin/payout-claims` | List payout claims |
| `PUT` | `/api/admin/payout-claims/{claim_id}/review` | Review claim |
| `POST` | `/api/admin/payout-claims/{claim_id}/complete` | Mark complete |

---

## 39. Webhooks — `/api/webhooks`

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/webhooks/stripe` | Stripe webhook receiver |

---

## 40. Admin & Stats (direct routes on main app)

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Frontend shell (HTML) |
| `GET` | `/api/health` | Overall API health |
| `GET` | `/api/stats` | Platform stats (public) |
| `GET` | `/api/admin/stats` | Admin stats |
| `GET` | `/api/admin/usage` | Aggregate usage |
| `GET` | `/api/admin/usage/logs` | Usage logs |
| `GET` | `/api/admin/users` | List all users |
| `GET` | `/api/admin/users/{user_id}` | Get user by ID |

---

## 41. Real-time — Socket.IO

> Two namespaces on the same Socket.IO server (Express, port 5000). All payloads use `snake_case`.

```
WS   ws://aiassist.net/socket.io/?EIO=4&transport=websocket
```

### Namespace `/client` — end-user chat

| Event (emit to server) | Payload | Description |
|---|---|---|
| `join_workspace` | `{ workspace_id }` | Join workspace room |
| `send_message` | `{ workspace_id, content }` | Send chat message |
| `typing_start` | `{ workspace_id }` | Signal typing started |
| `typing_stop` | `{ workspace_id }` | Signal typing stopped |
| `typing_preview` | `{ workspace_id, text }` | Live keystroke preview (visible to admins) |

| Event (receive from server) | Payload | Description |
|---|---|---|
| `message_new` | `{ message }` | New AI or user message |
| `typing_indicator` | `{ is_typing }` | AI typing state |
| `awaiting_approval` | `{ workspace_id, status }` | Shadow mode: draft pending approval |

### Namespace `/admin` — operator dashboard

| Event (emit to server) | Payload | Description |
|---|---|---|
| `subscribe_dashboard` | `{}` | Subscribe to all workspace activity |
| `subscribe_workspace` | `{ workspace_id }` | Subscribe to single workspace |
| `unsubscribe_workspace` | `{ workspace_id }` | Unsubscribe |
| `send_as_ai` | `{ workspace_id, content, user_id }` | Inject AI-role message |
| `change_mode` | `{ workspace_id, mode }` | Change workspace mode (`ai`/`shadow`/`takeover`) |
| `inject_directive` | `{ workspace_id, content, type, user_id }` | Inject directive live |

| Event (receive from server) | Payload | Description |
|---|---|---|
| `workspace_list` | `{ workspaces }` | All active workspaces on dashboard subscribe |
| `message_new` | `{ workspace_id, message }` | New message in any workspace |
| `client_presence` | `{ workspace_id, online }` | Client connect/disconnect |
| `workspace_update` | `{ workspace }` | Mode or status changed |
| `draft_created` | `{ workspace_id, draft }` | Shadow mode draft ready |
| `client_typing` | `{ workspace_id, is_typing }` | Client typing indicator |
| `typing_preview` | `{ workspace_id, text, is_typing }` | Live keystroke preview |

---

## 42. Quick-reference — Auth per area

| Area | Auth required |
|---|---|
| `/v1/*` | `Authorization: Bearer aai_<key>` |
| `/api/auth/login`, `/register`, `/health` | None |
| `/api/pricing/config`, `/invite/*`, `/api/public/*` | None |
| `/api/v1/pin/network/*`, `/api/v1/pin/pricing/*` | None (read-only public) |
| All other `/api/*` | Session cookie |
| `/api/admin/*` | Session cookie + admin/super_admin role |
| PIN daemon (`/daemon/register`, `/heartbeat`) | `Authorization: Bearer <operator-api-key>` |

---

*Generated from live source — `aias_production_april/api/routes/`. Legacy versioned files excluded.*
