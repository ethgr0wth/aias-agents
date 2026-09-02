# AiO — AI Orchestrator v2: Complete Walkthrough

## What is AiO?

AiO (AI Orchestrator) is a visual, low-code automation platform built into AiAssist Secure. It lets you design, test, and deploy complex AI-powered workflows using a drag-and-drop canvas editor — no coding required for most use cases, but fully extensible with Python and JavaScript when you need it.

Think of it as a workflow builder where every step can be an AI agent, a code block, an API call, a human approval gate, or any combination. You wire them together visually, hit Test, and watch it run.

---

## Getting Started

### Accessing AiO

- **Desktop**: Navigate to `/aio` from the main app, or open it from the AI OS dashboard (`/aios`) where it runs as a windowed application.
- **Mobile**: The interface is fully responsive — the same `/aio/new` route works on phones with touch-optimized controls, bottom-sheet panels, and safe-area padding for notched devices.

### Creating Your First Workflow

1. Go to `/aio/new` — you'll land on a blank canvas.
2. Tap the **+** button (top-left) to open the **Node Palette**.
3. Browse categories and add nodes by dragging (desktop) or tapping (mobile).
4. Connect nodes by dragging from one node's output handle to another's input handle.
5. Select any node to configure it in the **Config Panel**.
6. Hit **Test** to execute, then **Publish** when you're satisfied.

---

## The Canvas Editor

The canvas is where everything happens. It's built on React Flow and provides a full graph-editing experience.

### TopBar

The toolbar at the top of the canvas with two rows:

- **Row 1 (Primary Actions)**: Back button, AiAS logo, editable workflow name, Save, Test (execute), and Publish buttons. A status indicator shows the current run state (running, completed, failed).
- **Row 2 (Panel Tabs)**: Quick toggles for Versions, Runs, Ledger, and Approvals panels. On mobile, these are horizontally scrollable with labels always visible.

### Node Palette

The node library, organized by category. On desktop it's a left sidebar; on mobile it opens as a bottom sheet covering 60% of the screen. Tap any node to add it at the center of your viewport, or drag-and-drop on desktop.

### Config Panel

When you select a node, this panel slides in from the right (desktop) or rises from the bottom (mobile). Every node type has its own configuration form — system prompts for AI nodes, code editors for runtime nodes, condition builders for logic nodes, and so on.

### Zoom Controls

Standard zoom in/out, fit-to-view, and lock controls. On mobile these are sized for comfortable tapping and positioned above the browser chrome.

### MiniMap

A birds-eye overview of your entire workflow graph. Hidden on mobile to save screen space; visible on desktop at the bottom-right corner.

---

## Node Types

AiO provides 27 node types across 7 categories:

### Triggers
The entry points for your workflow.

| Node | Description |
|------|-------------|
| **Manual Trigger** | Start a workflow by hand — hit Test or trigger via API |
| **Webhook** | HTTP endpoint that fires the workflow when called |
| **Schedule** | Cron-based scheduling (e.g., every hour, daily at 9am) |

### AI / Agents
The intelligence layer.

| Node | Description |
|------|-------------|
| **Agent** | Full AI agent with tool access — can call functions, search, analyze |
| **LLM Prompt** | Single-shot call to any LLM (OpenAI, Anthropic, Gemini, Groq, Mistral) |

### Runtime (Code Execution)
Sandboxed code execution via the AiOS Runtime.

| Node | Description |
|------|-------------|
| **Run Python** | Execute Python code with package support |
| **Run JavaScript** | Execute Node.js code with npm packages |
| **Install Package** | Install pip or npm packages into the runtime |
| **Read File** | Read a file from the runtime filesystem |
| **Write File** | Write content to a file |
| **List Directory** | List files and folders in a directory |

### Tools
External integrations and actions.

| Node | Description |
|------|-------------|
| **Custom Tool** | User-defined tools from the Custom Tools system |
| **HTTP Request** | Make REST API calls to any endpoint |
| **Built-in Action** | Pre-built actions (calculate, translate, summarize, send email, etc.) |

### Artifacts
Persistent outputs that live beyond the workflow run.

| Node | Description |
|------|-------------|
| **Create Artifact** | Save a file, document, or data object |
| **Read Artifact** | Load a previously saved artifact |
| **Update Artifact** | Modify an existing artifact |
| **Generate Image** | AI image generation (DALL-E, Gemini, etc.) |

### Logic
Control flow and data manipulation.

| Node | Description |
|------|-------------|
| **If / Condition** | Branch based on a boolean condition |
| **Switch** | Multi-way routing (like a switch/case) |
| **Loop / ForEach** | Iterate over a list of items |
| **Transform** | Map and extract data fields |
| **Filter** | Filter array items by criteria |
| **Merge** | Combine multiple branches back together |

### Approval (Human-in-the-Loop)
Pause execution for human review.

| Node | Description |
|------|-------------|
| **Approval Gate** | Require human approval before continuing |
| **Review Content** | Present content for review before proceeding |
| **Manual Decision** | Let a human choose which path to take |

---

## Template Variables

Nodes can reference outputs from previous nodes using template syntax:

- `{{input.field}}` — Access workflow input data
- `{{node_id.output}}` — Access a specific node's output
- `{{node_id.field_name}}` — Access a specific field from a node's output

The Config Panel shows available template variables based on the nodes connected upstream.

---

## Side Panels

### Versions Panel
Every time you hit **Publish**, AiO creates an immutable snapshot of your workflow. The Versions panel shows your publication history with:
- Version numbers and timestamps
- Change descriptions
- Ability to compare any two versions (visual diff)
- One-click rollback to any previous version

### Run History Panel
A complete audit trail of every workflow execution:
- Status (running, completed, failed)
- Trigger type (manual, webhook, schedule, API)
- Duration
- Click any run to inspect it node-by-node

### Ledger Panel
A real-time event stream during execution. As your workflow runs, the ledger shows:
- Which node is currently executing
- Status updates for each step
- Timing information
- Error details if something fails

### Approvals Inbox
Lists all pending human-in-the-loop tasks across your workflows:
- Filter by pending or all approvals
- Expandable cards showing the approval context and payload
- Comment field for providing feedback
- Approve or Reject buttons

---

## Execution Engine

### How It Works

When you hit **Test** or a trigger fires:

1. **Graph Analysis**: The engine performs a topological sort on your nodes and edges to determine execution order.
2. **Template Resolution**: Dynamic references like `{{llm_prompt_1.output}}` are resolved in real-time as each node completes.
3. **Node Execution**: Each node runs in sequence (or parallel where the graph allows), with results stored in Redis.
4. **Branching**: Condition and Switch nodes evaluate their logic and skip nodes on non-matching paths.
5. **Loops**: Loop nodes iterate over lists, executing downstream nodes once per item.
6. **Approvals**: When an approval node is reached, execution pauses. A checkpoint is saved. Once a human approves or rejects, execution resumes or cancels.
7. **Artifacts**: Any artifacts created during execution are persisted and accessible from the Artifacts Hub.

### State Management

Node execution states flow through: `pending` → `running` → `completed` / `failed` / `skipped`

Run-level states: `queued` → `running` → `completed` / `failed` / `waiting_for_approval`

---

## Artifacts Hub

Accessible at `/aio/artifacts`, the Artifacts Hub is a central repository for all outputs generated by your workflows:

- **Browse & Search**: View all artifacts with sorting (newest, oldest, A-Z)
- **Detail View**: Preview artifact content with source workflow links
- **Actions**: Delete, clone, and manage artifacts
- **Integration**: Artifacts created by one workflow can be read or updated by another

---

## API Access

### REST API

Every workflow is accessible programmatically:

- `POST /api/aio/workflows/{id}/execute` — Trigger a run
- `POST /api/aio/workflows/{id}/trigger` — Public API trigger (Bearer token auth)
- `GET /api/aio/workflows/{id}/runs` — List run history
- `GET /api/aio/runs/{run_id}/detail` — Get detailed execution results

### Webhook Triggers

Enable webhooks on any workflow to receive HTTP POST requests that automatically start a run. The request body is passed as workflow input.

### Scheduled Triggers

Set cron expressions to run workflows on a schedule — hourly, daily, weekly, or any custom interval.

---

## BYOK (Bring Your Own Key)

AiO uses the platform's BYOK system. AI nodes use whichever LLM provider you've configured in your account settings:

- **Supported Providers**: OpenAI, Anthropic, Gemini, Groq, Mistral
- **Per-Node Override**: You can specify a different model on individual LLM nodes
- **No Lock-in**: Switch providers anytime without rebuilding workflows

---

## Mobile Experience

The entire canvas editor is mobile-friendly:

- **Touch-Optimized Controls**: All buttons are minimum 44px tap targets
- **Bottom Sheet Panels**: Side panels become bottom sheets on mobile, covering 70% of the viewport
- **Node Palette as Bottom Sheet**: Opens from the bottom with tap-to-add support (no drag required)
- **Safe Area Support**: Proper padding for notched phones and home indicators
- **Hidden MiniMap**: Removed on mobile to maximize canvas space
- **Responsive TopBar**: Two-row layout with scrollable panel tabs
- **Mobile Approvals**: Dedicated approval view with expandable cards and quick actions

---

## Architecture Summary

| Component | Technology |
|-----------|-----------|
| Frontend | React, TypeScript, Vite, Tailwind CSS |
| Canvas | @xyflow/react (React Flow) |
| Backend | FastAPI (Python) |
| Storage | Redis (primary persistence) |
| Code Execution | AiOS Runtime (Server B) — sandboxed Python/Node.js |
| AI Providers | BYOK — OpenAI, Anthropic, Gemini, Groq, Mistral |
| Authentication | Session-based + API key (`aai_` prefix) |

---

*AiO v2 — Built as part of AiAssist Secure by Interchained LLC.*
