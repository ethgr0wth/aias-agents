---
title: Public Tool Catalog Overhaul — Replace LLM-Native Tools with Signal Source Tools
---
# Signal Source Tools Overhaul

  ## What & Why
  The current public tool catalog has ~13 tools that duplicate what LLMs already do natively. Replace them with 24 real external data tools. SaaS-Signal service files are extracted into aias_production_clone/api/saas/ as a self-contained module — no cross-project imports. Services are adapted to work within the AiAS codebase (fix imports, stub StorageService references, use AiAS Redis).

  ## Done looks like
  - New api/saas/ module inside AiAS containing all SaaS-Signal source services
  - ToolsHub shows ~35 tools: 11 kept action tools + 24 new intelligence/source tools
  - LLM-native tools (calculator, translator, summarizer, etc.) removed from catalog
  - Each source available as its own tool with subtle "Powered by SaaS-Signal" branding
  - Multi-source "Signal Scanner" tool for searching across platforms
  - Raw search results (titles, text, URLs, dates) — no scoring pipeline
  - "intelligence" category in ToolsHub

  ## Out of scope
  - Removing builtin handler code for removed tools (backward compat)
  - SaaS-Signal v1 API changes
  - Intent scoring or enrichment on results
  - ScrapingDog-dependent sources return clear message if API key not configured

  ## Tasks
  1. Extract SaaS-Signal services into api/saas/ module — Copy ~20 service files, fix imports, add __init__.py and sources.py registry with unified async search_source(source, keywords, limit) dispatcher.
  2. Remove LLM-native tools + add signal source tools to catalog — Drop 13 entries, add 24 source tools, bump PUBLIC_TOOLS_VERSION.
  3. Implement signal_scan builtin handler — Add _builtin_signal_scan to tool_executor.py dispatch, import from api.saas.sources.
  4. ToolsHub UI: intelligence category + SaaS-Signal branding — New category with radar icon, subtle "Powered by SaaS-Signal" label on source tool cards.

  ## Relevant files
  - saas-signal/api/services/ (all 20+ service files)
  - aias_production_clone/api/services/redis_storage.py:10067-10095
  - aias_production_clone/api/services/tool_executor.py:400-436
  - aias_production_clone/client/src/pages/ToolsHub.tsx