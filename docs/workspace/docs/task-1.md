---
title: AiAS AppSumo Launch Readiness — Provider Router Dogfooding + Dashboard + Onboarding
---
# AiAS AppSumo Launch Readiness

## What & Why
Prepare AiAS for AppSumo launch by addressing all beta test feedback (27/100 score). The core architectural fix: dogfood the existing `ProviderRouter` (`v1/providers`) for ALL internal AI endpoints — playground, blog generator, quests chat, code generator, and workspace chat. Currently each feature rolls its own provider selection with scattered `get_client_for_user`, `get_provider_with_fallbacks`, and manual client creation, causing model/provider mismatches that break chats. The `ProviderRouter` already handles resolve → get key → call adapter → error normalization cleanly; every internal feature should use it. Additionally: redesign the dashboard, add onboarding, and fix error messages.

Working directory: `aias_production_clone` (fresh clone of production code).

## Done looks like
- All internal AI features (playground, blog, quests, code gen, workspace chat) route through `ProviderRouter.route_completion()` / `route_completion_stream()` — no more scattered provider selection code
- `X-AiAssist-Provider` header respected on all AI endpoints, not just the public API
- Model selection always uses the correct provider's API key — selecting GPT-4o uses the OpenAI key, selecting Claude uses the Anthropic key
- If a user selects a model but doesn't have that provider's key, they get a clear actionable error ("Add your OpenAI key in Settings") instead of a crash or silent fallback to wrong provider
- Dashboard is reorganized from a 2,500-line scroll wall into clear tabbed sections
- First-time users see a guided onboarding wizard that walks them through creating their first workspace
- All error messages shown to users are friendly and actionable — no raw stack traces or technical details
- Templates trimmed to 5-7 business-relevant examples (remove pet care, parenting, immigration, etc.)

## Out of scope
- PIN Network changes
- Stripe/billing changes
- New provider integrations
- Public API (`/v1/chat/completions`) — already uses the router correctly
- Voice actions — intentionally uses hardcoded fast models per provider

## Tasks
1. **Provider Router dogfooding** — Refactor `playground_completion`, `AIOrchestrator.generate_response`, `blog_generator._call_llm`, quests chat/stream endpoints, and code generator endpoints to call `ProviderRouter.route_completion()` instead of building their own clients. Remove `resolve_provider_and_key_for_model()` from config.py (the router already does this). Accept `X-AiAssist-Provider` header on all these endpoints.

2. **Error message cleanup** — Replace all raw `err.message`, `technicalDetails`, and stack trace exposures in Dashboard.tsx, BlogPostEditor.tsx, OraclePlayground.tsx, and ProviderSettings.tsx with user-friendly copy. Ensure provider router errors ("No API key configured for openai") surface as clear UI messages.

3. **Dashboard redesign** — Break the single-scroll dashboard into tabbed sections: Overview/Home, Workspaces, API Keys, Provider Settings, Templates. Each section is focused and navigable.

4. **Onboarding wizard** — First-time user flow: welcome screen → pick a use case → configure one provider key → auto-create a sample workspace → guided first chat. Stores completion state so it only shows once.

5. **Template curation** — Remove off-brand templates (pet care, parenting, immigration, astrology, etc.). Keep 5-7 SaaS-relevant examples: support deflection, lead qualification, FAQ automation, sales assistant, onboarding helper.

## Relevant files
- `aias_production_clone/api/providers/router.py`
- `aias_production_clone/api/providers/config.py`
- `aias_production_clone/api/services/ai_orchestrator.py`
- `aias_production_clone/api/services/blog_generator.py`
- `aias_production_clone/api/routes/quests.py`
- `aias_production_clone/api/routes/code_generator.py`
- `aias_production_clone/api/routes/public_api.py`
- `aias_production_clone/client/src/pages/Dashboard.tsx`
- `aias_production_clone/client/src/components/ProviderSettings.tsx`
- `aias_production_clone/client/src/components/BlogPostEditor.tsx`
- `aias_production_clone/client/src/components/OraclePlayground.tsx`
- `aias_production_clone/script/seed_ai_templates.py`