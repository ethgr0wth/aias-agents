# Gex — AI Code Surgeon

Gex scans your source code, clones the repo to a parallel directory, asks an LLM for surgical fixes, applies them to the clone, and posts a detailed summary to an AiAS workspace.

Your original code is never touched. All changes go to the `_gex` clone.

## Quick Start

```bash
# Single file (primary mode)
python3 gex.py --scan ./myproject --file src/auth.py

# Single file with focus
python3 gex.py --scan ./myproject --file src/auth.py --focus "fix the login bug"

# Full repo scan
python3 gex.py --scan ./myproject

# Dry run (analyze without applying)
python3 gex.py --scan ./myproject --file src/auth.py --dry-run

# List AiAS workspaces
python3 gex.py --list-workspaces
```

## How It Works

```
Source Code ──> Scan ──> Clone to _gex/ ──> LLM Analysis ──> Parse Patches ──> Apply to Clone ──> Workspace Summary
```

1. **Scan** — Reads source files with line numbers so the LLM has exact references
2. **Clone** — Copies the repo to `<repo>_gex/` (skips node_modules, .git, etc.)
3. **LLM Analysis** — Sends code to the AI with instructions to return surgical edits
4. **Parse** — Extracts `<<<WRITE>>>` and `<<<PATCH>>>` blocks from the LLM response
5. **Apply** — Writes changes to the clone directory only
6. **Report** — Saves a markdown report locally and posts the full summary to an AiAS workspace

## Surgical Edit Patterns

Gex uses Keystone-lite patterns for precise code changes:

### WRITE — Full file create/overwrite

```
<<<WRITE:src/utils/helper.py>>>
def helper():
    return "fixed"
<<<END>>>
```

Use for new files or when >50% of the file changes.

### PATCH — Line-based surgical edits

```
<<<PATCH:src/auth.py>>>
[
  {"action": "replace", "start_line": 15, "end_line": 20, "content": "    return validate(token)"},
  {"action": "insert", "start_line": 5, "content": "import hashlib"},
  {"action": "delete", "start_line": 42, "end_line": 45}
]
<<<END>>>
```

| Action    | Description                                         |
|-----------|-----------------------------------------------------|
| `replace` | Replace lines `start_line` through `end_line`       |
| `insert`  | Insert content before `start_line`                  |
| `delete`  | Remove lines `start_line` through `end_line`        |

## Configuration

All configuration is via environment variables:

| Variable         | Default                        | Description                  |
|------------------|--------------------------------|------------------------------|
| `AIAS_API_URL`   | `https://api.aiassist.net`     | AiAS API endpoint            |
| `AIAS_API_KEY`   | —                              | Your `aai_` prefixed API key |
| `AIAS_MODEL`     | `moonshotai/kimi-k2-instruct`  | LLM model to use             |
| `AIAS_PROVIDER`  | `groq`                         | LLM provider                 |

## CLI Options

```
python3 gex.py [OPTIONS]

Options:
  --scan PATH          Path to repo or directory to scan
  --file PATH          Focus on a specific file (filters scan results)
  --focus TEXT          Tell the LLM what to prioritize (e.g. "security", "performance")
  --dry-run            Show patches without applying them
  --list-workspaces    List your AiAS workspaces
```

## Output

Each run produces:

- **Clone directory** — `<repo>_gex/` with patches applied
- **Markdown report** — Saved to `<repo>/reports/gex_<name>_<timestamp>.md`
- **AiAS workspace** — Full summary posted for cloud access

## Safety

- **Clone-only** — Original source is never modified
- **Path traversal protection** — LLM-suggested paths are validated to stay within the clone
- **Resilient parser** — 3-tier JSON parsing handles malformed LLM output (strict parse, newline fix, regex fallback)
- **Chunked uploads** — Large reports are split into chunks for reliable workspace delivery

## Self-Test

The ultimate test — run Gex on itself:

```bash
python3 gex.py --scan . --file gex.py --focus "bugs, edge cases, and robustness"
```

## Requirements

- Python 3.10+
- `httpx` (`pip install httpx`)
- A valid AiAS API key

## Related

- **Analyzer** (`analyzer.py`) — The original code analysis tool. Scans and reports but doesn't apply fixes.
- **Gex** (`gex.py`) — Analyzer's evolution. Scans, clones, patches, and reports.
