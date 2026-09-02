# Quests Builder: Surgical Code Editing

## Overview

The Quests Builder now supports **surgical code editing** to prevent the common problem of AI truncating code with placeholders like `// existing code here`. Instead of rewriting entire files, the AI uses line-based edit operations that precisely target specific sections.

## How It Works

### Two File Operation Formats

| Format | Use Case | Example |
|--------|----------|---------|
| `filepath:` | Create new files | Full file content for new files |
| `edit:` | Modify existing files | JSON operations targeting specific lines |

### Edit Operations

The `edit:` format supports three actions:

```json
{
  "operations": [
    {"action": "replace", "start_line": 10, "end_line": 15, "content": "new code"},
    {"action": "insert", "start_line": 25, "content": "code to insert"},
    {"action": "delete", "start_line": 30, "end_line": 35}
  ]
}
```

| Action | Description |
|--------|-------------|
| `replace` | Replace lines start_line through end_line with new content |
| `insert` | Insert content before start_line (existing code shifts down) |
| `delete` | Remove lines start_line through end_line |

## API Endpoints

### Apply Edits
```
POST /api/quests/environments/{env_id}/files/edit
```

Request body:
```json
{
  "path": "src/components/Button.tsx",
  "base_hash": "abc123...",
  "operations": [
    {"action": "replace", "start_line": 15, "end_line": 20, "content": "// new implementation"}
  ]
}
```

### Preview Edits
```
POST /api/quests/environments/{env_id}/files/edit/preview
```

Returns the resulting file content without saving, useful for diff views.

### Get File Hash
```
GET /api/quests/environments/{env_id}/files/hash?path=src/file.ts
```

Returns the current content hash for conflict detection.

## Conflict Detection

The system uses SHA-256 content hashing to detect conflicts:

1. Before editing, the AI receives the file's current hash
2. Edit requests include `base_hash` to verify the file hasn't changed
3. If hashes don't match, the edit is rejected with a conflict error
4. Users can choose to force the edit or view the current file first

## Frontend Integration

### Visual Indicators

Files modified in chat messages show different badges:
- **Green badge with + icon**: New file created
- **Blue badge with edit icon**: Existing file edited

### Click Actions

Clicking a file badge:
- Opens the file in the code editor
- On mobile, switches to the code tab automatically

## Streaming Events

The chat stream emits these events for file operations:

| Event | Description |
|-------|-------------|
| `files_written` | List of newly created files |
| `file_edited` | Single file that was edited |
| `files_edited` | List of all edited files |
| `file_error` | Error writing a new file |
| `edit_error` | Error applying an edit (e.g., conflict) |

## Function Boundary Detection

The system includes brace-matching helpers to detect exact function boundaries, preventing partial replacements that leave duplicate code.

### Get Function Boundaries
```
GET /api/quests/environments/{env_id}/files/function?path=src/file.cpp&function_name=TransferToken
```

Returns:
```json
{
  "path": "src/file.cpp",
  "function_name": "TransferToken",
  "start_line": 15,
  "end_line": 42,
  "line_count": 28,
  "content_preview": "bool CTokenManager::TransferToken(..."
}
```

### List All Functions
```
GET /api/quests/environments/{env_id}/files/functions?path=src/file.cpp
```

Returns all functions in a file with their line ranges.

### Supported Languages
- C/C++ (including class methods with `::`)
- JavaScript/TypeScript (functions, methods, arrow functions)
- Go (`func` keyword)
- Rust (`fn` keyword)
- Python (`def` keyword with indent-based detection)

## Best Practices for LLM Prompting

The system prompt instructs the AI to:
1. Use `edit:` blocks for small changes (1-20 lines)
2. Use `filepath:` for new files or major rewrites (>50% change)
3. Never use placeholder comments like `// rest of code here`
4. Always preserve code that isn't being changed
5. **Always use the full line range** when replacing functions (start to closing brace)
6. Count lines in provided file content to determine exact `end_line`

## Common Mistakes to Avoid

### Incomplete Replace Operations
**Problem**: LLM uses `end_line` that stops before the function's closing brace.
**Result**: Old function tail remains, causing duplicate code.

**Wrong**:
```json
{"action": "replace", "start_line": 10, "end_line": 18, "content": "new code"}
```
(If function ends at line 25, lines 19-25 remain as orphan code!)

**Correct**:
```json
{"action": "replace", "start_line": 10, "end_line": 25, "content": "new code"}
```

## Implementation Files

- **Schema**: `api/services/quests_service.py` - `FileEditOperation`, `FileEditRequest`, `FileEditResult`
- **Service**: `api/services/quests_service.py` - `QuestsFileService.apply_edits()`, `find_function_boundaries()`, `list_functions()`
- **Routes**: `api/routes/quests.py` - `/files/edit`, `/files/edit/preview`, `/files/hash`, `/files/function`, `/files/functions`
- **Frontend**: `client/src/pages/QuestsWorkspace.tsx` - Edit event handling and badges
