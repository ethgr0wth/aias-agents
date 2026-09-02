# Artifact Portal — Smart Agent Metadata & Auto-Population

  ## What & Why
  When deploying agents from the Artifact Portal, the deployed agent shows:
  - A bad name derived from the user's raw prompt words (e.g., "A-Python-Web-Scraper-That-v1.0")
  - The LLM's preamble as the description ("Below is a complete, production-ready Python agent that...")
  - 0 directives and 0 KB items — completely empty agent configuration

  The fix: fire a **second parallel LLM call** during generation that produces structured metadata — a clean agent name, a purpose-driven description, initial directives, and knowledge base items. This metadata populates the playground session before deploy, so the agent ships ready to use.

  ## Done looks like
  - Agent names are short and descriptive (e.g., "Code-Review-Agent" not "A-Python-Web-Scraper-That-v1.0")
  - Agent description is a clean one-liner explaining what it does, not raw LLM prose
  - Deployed agents have 3-5 directives (tone, guidance, constraints) auto-generated
  - Deployed agents have 2-3 knowledge base items describing the agent's capabilities
  - Both LLM calls run in parallel so generation time stays the same
  - The metadata call uses the same provider/model the user selected

  ## Out of scope
  - Changing the deploy API endpoints or storage layer
  - Modifying the Deployed Agents management page
  - Template system integration

  ## Tasks
  1. **Add parallel metadata LLM call** — During generation, fire a second chat call to the same session asking the LLM to return a JSON object with: a short agent name (2-4 words, kebab-case), a one-line description, 3-5 directives (with type and content), and 2-3 knowledge base items (with title, content, category). Use Promise.all to run both calls concurrently with the existing code generation call.

  2. **Parse metadata and update artifact state** — Parse the JSON response from the metadata call, extract the agent name, description, directives, and KB items. Update the artifact state with the clean name and description instead of deriving them from the prompt.

  3. **Populate session with directives and KB** — After parsing, call POST /api/playground/sessions/{session_id}/directives for each directive and POST /api/playground/sessions/{session_id}/knowledge for each KB item to populate the session before deploy.

  4. **Graceful fallback** — If the metadata call fails (rate limit, parse error), fall back to the current behavior (prompt-derived name, first-sentence description, no directives/KB). The primary code generation should never be blocked by a metadata failure.

  ## Relevant files
  - `aias_production_clone/client/src/pages/ArtifactPortal.tsx:101-168`
  - `aias_production_clone/api/routes/playground.py:158-257`
  - `aias_production_clone/api/models/schemas.py:1398-1413,1497-1510`
  