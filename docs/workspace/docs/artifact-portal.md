# Artifact Portal — Conversational Agent Builder

## What & Why
Replace the Dashboard "Get Started" section with an epic workstation-style **Artifact Portal** — a conversational interface where users talk to their BYOK LLM to build fully functional AI agents (not code suggestions, but deployable working products). This ties together onboarding, agent creation, knowledge base population, document scanning, and HITL support into one unified experience.

The portal serves three audiences:
- **New users**: Guided onboarding that helps them understand the platform and get started building their first agent
- **Power users**: A streamlined agent-building workstation that auto-populates knowledge bases, scans corporate docs, and deploys production agents
- **Admin/support**: Direct integration with admin workspaces for HITL support via Shadow/Takeover modes

## Done looks like
- Dashboard shows an epic "Artifact Generator" workstation UI in the Get Started area with a polished, immersive design
- Users can select their BYOK provider/model and start a conversation to build an agent
- The portal conversation guides users through: naming their agent, setting a persona, adding directives, scanning documents (URLs), and populating the knowledge base
- Corporate document URLs are scanned via the existing web extraction service and facts are automatically extracted and stored as training contexts
- Users can deploy their built agent directly from the portal (leveraging existing playground → deployed agent flow)
- New users see a guided onboarding flow that explains the platform and walks them through creating their first agent
- The portal creates a workspace tied to admin support — admins can monitor and intervene via existing HITL tools (Shadow mode, Takeover, admin messaging)
- Provider/model selector uses the existing `useAvailableModels` hook and sends `X-AiAssist-Provider` header

## Out of scope
- AI agent template marketplace or store
- AppSumo-specific template modifications (per user's instructions)
- Voice action integration within the portal
- Mobile-specific layout (desktop-first, responsive later)
- Custom domain or white-label for the portal

## Tasks
1. **Artifact Portal backend endpoints** — Create a new router (`api/routes/artifact_portal.py`) with endpoints for portal sessions: create portal session (wraps playground session creation with agent-builder persona), scan document URL (calls web extraction → fact extraction → creates training contexts), list extracted facts, and deploy agent from portal session. Reuse existing services — no new AI logic.

2. **Agent-builder system persona** — Define a specialized system prompt/persona for the portal AI that knows how to guide users through agent creation. It should ask about use case, suggest a persona, help craft directives, offer to scan documents, and walk through deployment — all conversationally.

3. **Artifact Portal frontend component** — Build the main `ArtifactPortal.tsx` page component with the epic workstation UI. Dark theme, gradient accents, animated elements (Framer Motion). Includes: chat interface, provider/model selector, document scanner panel, knowledge base preview, and deploy button. Integrate with existing `useAvailableModels` hook.

4. **Dashboard integration** — Replace the current "Get Started" / Quick Start section on `Dashboard.tsx` with a prominent Artifact Portal entry point. Epic card design with a "Launch Workstation" CTA that navigates to the portal.

5. **Onboarding flow for new users** — When a user has no sessions/agents, the portal starts in onboarding mode with a welcome message and guided conversation. Detects first-time users and adapts the agent-builder persona to be more explanatory.

6. **HITL support workspace binding** — When a portal session is created, automatically create or bind to an admin-visible workspace in Shadow mode so support staff can monitor and intervene. Connect to existing draft approval and admin messaging systems.

7. **Document scanning and fact extraction integration** — Wire up the document scanner panel to call the web extraction service, then pipe extracted content through the fact extraction pipeline from conversation memory. Store results as training contexts attached to the portal session's knowledge base.

## Relevant files
- `aias_production_clone/client/src/pages/Dashboard.tsx`
- `aias_production_clone/client/src/pages/OraclePlayground.tsx`
- `aias_production_clone/client/src/components/chat/ImmersiveChat.tsx`
- `aias_production_clone/client/src/hooks/use-available-models.ts`
- `aias_production_clone/api/routes/playground.py`
- `aias_production_clone/api/routes/deployed_agents.py`
- `aias_production_clone/api/routes/templates.py`
- `aias_production_clone/api/routes/workspaces.py`
- `aias_production_clone/api/services/ai_orchestrator.py`
- `aias_production_clone/api/services/web_extraction.py`
- `aias_production_clone/api/services/conversation_memory.py`
- `aias_production_clone/api/services/redis_storage.py`
- `aias_production_clone/api/models/schemas.py`
