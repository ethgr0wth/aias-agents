# Signal Source Tools Overhaul

## What & Why
The current public tool catalog has ~13 tools that duplicate what LLMs already do natively. Replace them with 24 real external data tools. SaaS-Signal service files are extracted into `aias_production_clone/api/saas/` as a self-contained module — no cross-project imports. Services are adapted to work within the AiAS codebase (fix imports, stub StorageService references, use AiAS Redis).

## Done looks like
- New `api/saas/` module inside AiAS containing all SaaS-Signal source services
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
1. **Extract SaaS-Signal services into api/saas/ module** — Copy ~20 service files from `saas-signal/api/services/` into `aias_production_clone/api/saas/`. Fix imports: replace `from services.storage_service import StorageService` with AiAS Redis equivalents. Add `__init__.py` and a `sources.py` registry that maps source names to service classes with a unified `async search_source(source, keywords, limit)` dispatcher.

2. **Remove LLM-native tools + add signal source tools to catalog** — In redis_storage.py, drop 13 LLM-native entries, add 24 source tool entries (builtin_action "signal_scan", category "intelligence"), bump PUBLIC_TOOLS_VERSION.

3. **Implement signal_scan builtin handler** — In tool_executor.py, add `_builtin_signal_scan` that imports from `api.saas.sources`, calls the unified dispatcher, returns results trimmed for LLM consumption. Add to dispatch table.

4. **ToolsHub UI: intelligence category + SaaS-Signal branding** — Add "intelligence" category with radar icon. Each source tool card shows a subtle "Powered by SaaS-Signal" label.

## Relevant files
- `saas-signal/api/services/reddit_rss_service.py`
- `saas-signal/api/services/hackernews_service.py`
- `saas-signal/api/services/devto_service.py`
- `saas-signal/api/services/lobsters_service.py`
- `saas-signal/api/services/hashnode_service.py`
- `saas-signal/api/services/producthunt_service.py`
- `saas-signal/api/services/indiehackers_service.py`
- `saas-signal/api/services/betalist_service.py`
- `saas-signal/api/services/echojs_service.py`
- `saas-signal/api/services/wip_service.py`
- `saas-signal/api/services/launchingnext_service.py`
- `saas-signal/api/services/hackernoon_service.py`
- `saas-signal/api/services/makerlog_service.py`
- `saas-signal/api/services/alternativeto_service.py`
- `saas-signal/api/services/saashub_service.py`
- `saas-signal/api/services/tldr_service.py`
- `saas-signal/api/services/changelog_service.py`
- `saas-signal/api/services/telegram_service.py`
- `saas-signal/api/services/scrapingdog_service.py`
- `saas-signal/api/services/netrows_service.py`
- `aias_production_clone/api/services/redis_storage.py:10067-10095`
- `aias_production_clone/api/services/tool_executor.py:400-436`
- `aias_production_clone/client/src/pages/ToolsHub.tsx`
