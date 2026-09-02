# AiAS P2P Inference Network (PIN)
## Comprehensive Workplan & Technical Blueprint
### Version 1.0 | Status: Active Development

---

# PART I: VISION

## The Next Wave Is Here

The GPU gold rush of 2024-2025 created millions of idle inference machines. Miners who once chased Bitcoin now sit on powerful hardware with no purpose. Data centers overflow with underutilized compute. Hobbyists run 4090s that sleep 23 hours a day.

**PIN changes everything.**

We're not building another AI API. We're building the **inference layer of the internet** — a decentralized network where anyone with a GPU can become an AI provider, and anyone with credits can access distributed intelligence.

```
┌─────────────────────────────────────────────────────────────────────┐
│                                                                     │
│   "Turn your GPU into a money printer. Join the inference economy." │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Why Now?

1. **Hardware Surplus** — Millions of GPUs sit idle post-crypto
2. **Inference Demand** — AI API costs are exploding
3. **Decentralization Need** — Single points of failure are unacceptable
4. **Economic Alignment** — Operators earn, users save, everyone wins

## The PIN Promise

| For Operators | For Users |
|---------------|-----------|
| Monetize idle compute | Access distributed AI |
| No contracts, no commitment | Lower costs than centralized APIs |
| Real-time earnings dashboard | Redundant, fault-tolerant inference |
| Reputation builds value | OpenAI-compatible, drop-in replacement |

---

# PART II: SYSTEM ARCHITECTURE

## Core Components

```
┌────────────────────────────────────────────────────────────────────────────┐
│                           AiAS PIN ARCHITECTURE                            │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                  │
│  │   USER      │────▶│  AiAS       │────▶│  OPERATOR   │                  │
│  │   REQUEST   │     │  ROUTER     │     │  NODE       │                  │
│  └─────────────┘     └──────┬──────┘     └─────────────┘                  │
│                             │                                              │
│                     ┌───────▼───────┐                                      │
│                     │    REDIS      │                                      │
│                     │  COORDINATION │                                      │
│                     │    LAYER      │                                      │
│                     └───────────────┘                                      │
│                             │                                              │
│         ┌───────────────────┼───────────────────┐                          │
│         ▼                   ▼                   ▼                          │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                  │
│  │  HEARTBEAT  │     │  REPUTATION │     │   BILLING   │                  │
│  │   MONITOR   │     │   ENGINE    │     │   LEDGER    │                  │
│  └─────────────┘     └─────────────┘     └─────────────┘                  │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

### 1. AiAS Router
The intelligent traffic controller that receives inference requests and routes them to optimal operators.

- Receives OpenAI-compatible requests at `/v1/pin/chat/completions`
- Queries Redis for available operators matching requested model
- Applies deterministic routing algorithm (reputation + latency weighted)
- Handles failover on timeout or error
- Records metrics for reputation updates

### 2. Operator Nodes
Independent inference servers run by operators worldwide.

- Expose OpenAI-compatible `/v1/chat/completions` endpoint
- Run models via llama.cpp, vLLM, TensorRT-LLM, or Ollama
- Execute lightweight agent for registration and heartbeats
- Report capacity, supported models, and pricing

### 3. Redis Coordination Layer
The single source of truth for all network state.

- Operator registry and metadata
- Real-time heartbeat tracking
- Job queue and assignment state
- Reputation scores and history
- Billing ledgers and payouts

### 4. Heartbeat Monitor
Background worker ensuring network health.

- Polls operator heartbeat timestamps
- Marks stale operators offline (>30s no heartbeat)
- Triggers reputation penalties for prolonged outages
- Manages cooldown periods for returning operators

### 5. Reputation Engine
Trust scoring system based on performance.

- Success rate (completed / attempted requests)
- Average response latency
- Uptime percentage
- Quality score (future: user ratings)

### 6. Billing Ledger
Token-based economics engine.

- User credit consumption tracking
- Operator earnings accumulation
- Protocol fee extraction (10% default)
- Payout queue management

### 7. PIN Client
Cross-platform desktop application that operators run locally to securely connect their Ollama instances to the network.

- Secure credential storage (OS keychain)
- Automatic heartbeat management
- Health monitoring and error reporting
- Mutual TLS for secure communication
- Auto-updates and version management

---

# PART II-B: PIN CLIENT SPECIFICATION

## Overview

The PIN Client is a lightweight desktop application that operators install on the same machine (or network) as their Ollama instance. It handles all communication with the PIN Router, eliminating the need for operators to expose their endpoints directly to the internet.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         OPERATOR MACHINE                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐     ┌─────────────────────────────────────────────┐   │
│  │   OLLAMA    │◀────│              PIN CLIENT                      │   │
│  │  (Localhost)│     │                                              │   │
│  │  :11434     │     │  ┌─────────────────────────────────────────┐ │   │
│  └─────────────┘     │  │ • Credential Manager (OS Keychain)      │ │   │
│                      │  │ • Heartbeat Scheduler (30s interval)    │ │   │
│                      │  │ • Health Monitor (GPU, Memory, Ollama)  │ │   │
│                      │  │ • WebSocket Client (to PIN Router)      │ │   │
│                      │  │ • Request Proxy (Router → Ollama)       │ │   │
│                      │  │ • Response Streamer (SSE handling)      │ │   │
│                      │  └─────────────────────────────────────────┘ │   │
│                      └─────────────────────────────────────────────┘   │
│                                      │                                  │
│                                      │ mTLS                             │
│                                      ▼                                  │
└──────────────────────────────────────┼──────────────────────────────────┘
                                       │
                           ┌───────────▼───────────┐
                           │      PIN ROUTER       │
                           │   (AiAS Backend)      │
                           └───────────────────────┘
```

## Core Components

### 1. Credential Manager
Securely stores and retrieves operator credentials.

```
Storage Location:
  - Windows: Windows Credential Manager
  - macOS: Keychain Access
  - Linux: libsecret / GNOME Keyring

Stored Credentials:
  - client_id: "pin_cid_abc123..."
  - api_secret: "pin_sk_xyz789..."
  - operator_id: "op_123abc..."
  - ollama_endpoint: "http://localhost:11434"
```

### 2. Heartbeat Scheduler
Maintains operator online status.

```rust
struct HeartbeatPayload {
    client_id: String,
    timestamp: u64,
    signature: String,  // HMAC-SHA256(timestamp, api_secret)
    health: HealthReport,
}

struct HealthReport {
    ollama_status: "online" | "offline" | "degraded",
    models_loaded: Vec<String>,
    current_load: u32,
    capacity: u32,
    gpu_memory_used: u64,
    gpu_memory_total: u64,
    uptime_seconds: u64,
}

Interval: 30 seconds
Timeout: 5 seconds
Retry: 3 attempts with exponential backoff
```

### 3. WebSocket Connection
Persistent connection to receive inference requests.

```
Endpoint: wss://api.aiassist.app/v1/pin/ws
Authentication: client_id + HMAC signature

Message Types (Inbound):
  - INFERENCE_REQUEST: Route inference to local Ollama
  - PING: Keep-alive check
  - MODEL_REFRESH: Re-fetch available models
  - SHUTDOWN: Graceful disconnect command

Message Types (Outbound):
  - INFERENCE_RESPONSE: Streaming tokens from Ollama
  - INFERENCE_COMPLETE: Final response with usage stats
  - INFERENCE_ERROR: Error during processing
  - PONG: Keep-alive response
  - MODEL_LIST: Current models from Ollama /api/tags
```

### 4. Request Proxy
Routes inference requests from PIN Router to local Ollama.

```
Flow:
  1. Receive INFERENCE_REQUEST via WebSocket
  2. Transform to Ollama /api/chat format
  3. Stream response back through WebSocket
  4. Report token usage for billing

Supported Operations:
  - /api/chat (streaming)
  - /api/generate (streaming)
  - /api/tags (model list)
```

## Security Model

### Authentication Flow
```
1. Operator enters client_id + api_secret during setup
2. Client stores credentials in OS keychain (encrypted)
3. For each request:
   a. Generate timestamp
   b. Create signature: HMAC-SHA256(client_id + timestamp, api_secret)
   c. Send: { client_id, timestamp, signature }
4. Router verifies signature against stored hash
5. If valid, request proceeds; if invalid, 401 Unauthorized
```

### Credential Security
- API secret never transmitted after initial setup
- Only HMAC signatures sent over wire
- Credentials stored in OS-native secure storage
- No plaintext credential files

### Transport Security
- All connections use TLS 1.3
- Certificate pinning for PIN Router endpoints
- WebSocket connection uses WSS (encrypted)

## User Interface

### System Tray Application
Minimal UI that lives in the system tray.

```
Tray Menu:
  ┌─────────────────────────────────┐
  │ PIN Client v1.0.0               │
  ├─────────────────────────────────┤
  │ ● Status: Connected             │
  │   Uptime: 3h 42m                │
  │   Requests: 1,247 today         │
  ├─────────────────────────────────┤
  │ ○ Models: 3 loaded              │
  │   - llama3.1:8b                 │
  │   - mistral:7b                  │
  │   - codellama:13b               │
  ├─────────────────────────────────┤
  │ [View Dashboard]                │
  │ [Settings]                      │
  │ [Quit]                          │
  └─────────────────────────────────┘
```

### Settings Window
Configuration panel for advanced options.

```
┌─────────────────────────────────────────────────────┐
│  PIN Client Settings                                │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Ollama Endpoint:  [ http://localhost:11434 ]       │
│                                                     │
│  Concurrent Requests: [ 4 ▼ ]                       │
│                                                     │
│  ☑ Start on system boot                             │
│  ☑ Show notifications                               │
│  ☐ Debug logging                                    │
│                                                     │
│  [Test Connection]  [Reset Credentials]  [Save]     │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## Technical Stack (Recommended)

```
Framework: Tauri v2
  - Rust backend for performance and security
  - Minimal resource footprint (~15MB)
  - Native OS integration
  - Cross-platform: Windows, macOS, Linux

Frontend: React + Tailwind
  - Consistent with AiAS web interface
  - Simple settings and status UI

Keychain Access:
  - keyring-rs (Rust crate)
  - Native OS credential storage

WebSocket:
  - tokio-tungstenite (async WebSocket)
  - Auto-reconnect with backoff

HTTP Client:
  - reqwest (for Ollama communication)
  - Streaming response support
```

## Installation Flow

```
1. User downloads PIN Client for their OS
2. Runs installer/opens DMG/extracts archive
3. On first launch:
   a. Prompt for credentials (client_id, api_secret)
   b. Auto-detect Ollama endpoint (localhost:11434)
   c. Test connection to both Ollama and PIN Router
   d. Store credentials in OS keychain
   e. Start heartbeat scheduler
   f. Minimize to system tray
4. Client runs in background, ready for requests
```

## Error Handling

### Common Issues
```
| Issue                    | Detection           | Resolution            |
|--------------------------|---------------------|-----------------------|
| Ollama not running       | /api/tags timeout   | Show "Start Ollama"   |
| Invalid credentials      | 401 from Router     | Prompt re-entry       |
| Network disconnected     | WebSocket close     | Reconnect with backoff|
| GPU OOM                  | Ollama error        | Report degraded status|
| Model not found          | Ollama 404          | Refresh model list    |
```

### Retry Strategy
```rust
let retry_delays = [1, 2, 4, 8, 16, 30, 60]; // seconds
// After exhausting retries, show user notification
// Manual reconnect button available in tray menu
```

## Future Enhancements

1. **Multi-Endpoint Support**: Connect multiple Ollama instances
2. **GPU Metrics Dashboard**: Detailed GPU utilization graphs
3. **Earnings Tracker**: Show real-time earnings in tray
4. **Auto-Model Download**: Download models directly from UI
5. **Remote Management**: Control client from web dashboard

---

# PART III: REDIS NAMESPACE SPECIFICATION

## Namespace: `pin:`

All PIN-related data lives under the `pin:` prefix, cleanly separated from existing AiAS data.

### Operator Registry
```
pin:operators:{operator_id}          → Hash
  - id: string (UUID)
  - user_id: string (AiAS user reference)
  - name: string
  - endpoint: string (https://operator-url.com)
  - api_key_hash: string (for auth with operator)
  - status: "pending" | "active" | "suspended" | "offline"
  - models: JSON array ["llama-3.1-70b", "mistral-7b"]
  - capacity: number (concurrent requests)
  - pricing_per_1k_tokens: number (in credits)
  - region: string (us-east, eu-west, asia)
  - created_at: timestamp
  - updated_at: timestamp
```

### Heartbeat Tracking
```
pin:heartbeats:{operator_id}         → String (timestamp)
  - TTL: 60 seconds (auto-expire marks offline)

pin:operators:online                 → Set
  - Contains operator_ids with valid heartbeats
```

### Reputation Scores
```
pin:reputation:{operator_id}         → Hash
  - total_requests: number
  - successful_requests: number
  - failed_requests: number
  - total_latency_ms: number
  - avg_latency_ms: number
  - success_rate: float (0.0 - 1.0)
  - score: float (computed reputation)
  - last_updated: timestamp
```

### Job Queue & Status
```
pin:jobs:pending                     → List
  - Job IDs awaiting assignment

pin:jobs:{job_id}                    → Hash
  - id: string (UUID)
  - user_id: string
  - operator_id: string (assigned)
  - model: string
  - status: "pending" | "assigned" | "processing" | "completed" | "failed"
  - input_tokens: number
  - output_tokens: number
  - created_at: timestamp
  - started_at: timestamp
  - completed_at: timestamp
  - error: string (if failed)
```

### Model Index
```
pin:models:{model_name}              → Set
  - Contains operator_ids that support this model

pin:models:available                 → Set
  - All unique model names across network
```

### Billing Ledger
```
pin:billing:user:{user_id}           → Hash
  - credits_balance: number
  - total_spent: number
  - last_transaction: timestamp

pin:billing:operator:{operator_id}   → Hash
  - earnings_balance: number (pending payout)
  - total_earned: number
  - total_paid_out: number
  - last_payout: timestamp

pin:billing:transactions             → Stream
  - Event log of all credit movements
```

### Network Metrics
```
pin:metrics:global                   → Hash
  - total_operators: number
  - online_operators: number
  - total_requests_24h: number
  - total_tokens_24h: number
  - avg_latency_24h: number

pin:metrics:hourly:{hour}            → Hash
  - requests: number
  - tokens: number
  - unique_users: number
  - unique_operators: number
```

---

# PART IV: API SPECIFICATION

## Operator Agent Routes

### POST `/v1/pin/operators/register`
Register a new operator node.

```json
Request:
{
  "name": "GPU Farm Alpha",
  "endpoint": "https://my-inference.example.com",
  "models": ["llama-3.1-70b-instruct", "mistral-7b-instruct"],
  "capacity": 10,
  "pricing_per_1k_tokens": 0.5,
  "region": "us-east"
}

Response:
{
  "operator_id": "op_abc123",
  "api_key": "pin_sk_...",
  "status": "pending",
  "message": "Registration received. Awaiting activation."
}
```

### POST `/v1/pin/operators/heartbeat`
Keep operator marked as online.

```json
Request:
{
  "operator_id": "op_abc123",
  "current_load": 3,
  "capacity": 10,
  "models_available": ["llama-3.1-70b-instruct"]
}

Response:
{
  "acknowledged": true,
  "next_heartbeat_due": 30
}
```

### GET `/v1/pin/operators/{operator_id}/status`
Get operator status and metrics.

```json
Response:
{
  "operator_id": "op_abc123",
  "status": "active",
  "online": true,
  "reputation_score": 0.94,
  "total_requests": 15234,
  "success_rate": 0.97,
  "avg_latency_ms": 1240,
  "earnings_balance": 1523.50,
  "total_earned": 8432.00
}
```

### GET `/v1/pin/operators/{operator_id}/earnings`
Get detailed earnings breakdown.

```json
Response:
{
  "balance": 1523.50,
  "pending_payout": 0,
  "total_earned": 8432.00,
  "total_paid_out": 6908.50,
  "earnings_24h": 142.30,
  "earnings_7d": 892.10,
  "earnings_30d": 3201.00,
  "transactions": [...]
}
```

### POST `/v1/pin/operators/{operator_id}/withdraw`
Request earnings withdrawal.

```json
Request:
{
  "amount": 500.00,
  "method": "stripe" | "crypto"
}

Response:
{
  "withdrawal_id": "wd_xyz789",
  "amount": 500.00,
  "status": "processing",
  "estimated_arrival": "2026-01-07T12:00:00Z"
}
```

## Inference Routes

### POST `/v1/pin/chat/completions`
OpenAI-compatible inference via PIN network.

```json
Request:
{
  "model": "llama-3.1-70b-instruct",
  "messages": [
    {"role": "user", "content": "Hello, world!"}
  ],
  "temperature": 0.7,
  "max_tokens": 1000,
  "stream": false
}

Response:
{
  "id": "pin-abc123",
  "object": "chat.completion",
  "created": 1704480000,
  "model": "llama-3.1-70b-instruct",
  "choices": [...],
  "usage": {
    "prompt_tokens": 12,
    "completion_tokens": 145,
    "total_tokens": 157
  },
  "pin_metadata": {
    "operator_id": "op_xyz",
    "latency_ms": 1150,
    "credits_charged": 0.08
  }
}
```

## Network Routes

### GET `/v1/pin/network/status`
Global network health and metrics.

```json
Response:
{
  "status": "healthy",
  "operators": {
    "total": 142,
    "online": 127,
    "capacity": 1850
  },
  "models": ["llama-3.1-70b", "mistral-7b", "codellama-34b", ...],
  "metrics_24h": {
    "requests": 1234567,
    "tokens": 89012345,
    "avg_latency_ms": 980
  }
}
```

### GET `/v1/pin/network/operators`
List all operators (public directory).

```json
Response:
{
  "operators": [
    {
      "id": "op_abc123",
      "name": "GPU Farm Alpha",
      "region": "us-east",
      "models": ["llama-3.1-70b-instruct"],
      "status": "online",
      "reputation_score": 0.94,
      "pricing_per_1k_tokens": 0.5
    },
    ...
  ]
}
```

---

# PART V: ROUTING ALGORITHM

## Deterministic Selection

No ML, no randomness — pure math-based routing.

```python
def select_operator(model: str, exclude: list[str] = []) -> Operator | None:
    """
    Deterministic operator selection algorithm.
    
    1. Filter by model support
    2. Filter by online status (valid heartbeat)
    3. Exclude previously failed operators
    4. Rank by composite score
    5. Return top operator
    """
    
    # Step 1: Get operators supporting this model
    candidates = redis.smembers(f"pin:models:{model}")
    
    # Step 2: Filter to online operators only
    online = redis.smembers("pin:operators:online")
    candidates = candidates.intersection(online)
    
    # Step 3: Exclude failed operators from this request
    candidates = candidates - set(exclude)
    
    if not candidates:
        return None
    
    # Step 4: Score and rank
    scored = []
    for op_id in candidates:
        rep = redis.hgetall(f"pin:reputation:{op_id}")
        op = redis.hgetall(f"pin:operators:{op_id}")
        
        # Composite score: 70% reputation, 30% inverse latency
        reputation_score = float(rep.get("score", 0.5))
        avg_latency = float(rep.get("avg_latency_ms", 5000))
        latency_score = max(0, 1 - (avg_latency / 10000))  # 10s = 0 score
        
        composite = (0.7 * reputation_score) + (0.3 * latency_score)
        scored.append((op_id, composite))
    
    # Step 5: Return highest scored operator
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[0][0]
```

## Failover Logic

```python
async def route_with_failover(request: ChatRequest, max_attempts: int = 3):
    """
    Route request with automatic failover on failure.
    """
    excluded = []
    
    for attempt in range(max_attempts):
        operator_id = select_operator(request.model, exclude=excluded)
        
        if not operator_id:
            raise NoOperatorsAvailable(f"No operators for {request.model}")
        
        try:
            response = await forward_to_operator(operator_id, request)
            
            # Success - update reputation positively
            await update_reputation(operator_id, success=True, latency=response.latency)
            
            return response
            
        except (Timeout, ConnectionError, OperatorError) as e:
            # Failure - update reputation negatively
            await update_reputation(operator_id, success=False)
            excluded.append(operator_id)
            
            if attempt == max_attempts - 1:
                raise AllOperatorsFailed()
    
    raise AllOperatorsFailed()
```

---

# PART VI: PROOF-OF-RESPONSE (PoR)

## Philosophy

Bitcoin uses Proof-of-Work: waste energy to prove commitment.
PIN uses **Proof-of-Response**: prove value by delivering results.

No mining, no hashing, no energy waste. Just:
1. Receive request
2. Respond correctly
3. Respond quickly
4. Get paid

## Validation Criteria

| Criterion | Threshold | Consequence |
|-----------|-----------|-------------|
| Response received | Required | No pay if timeout |
| Valid JSON format | Required | Reputation penalty |
| Latency | <10s default | Score reduction |
| Token count match | ±5% | Audit flag |

## Health Check Protocol

```python
async def health_check(operator_id: str) -> HealthResult:
    """
    Periodic health check sent to all operators.
    """
    operator = await get_operator(operator_id)
    
    # Send minimal inference request
    probe = {
        "model": operator.models[0],
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 5
    }
    
    start = time.time()
    try:
        response = await http_client.post(
            f"{operator.endpoint}/v1/chat/completions",
            json=probe,
            timeout=10.0
        )
        latency = (time.time() - start) * 1000
        
        if response.status_code == 200:
            return HealthResult(healthy=True, latency_ms=latency)
        else:
            return HealthResult(healthy=False, error="bad_status")
            
    except Timeout:
        return HealthResult(healthy=False, error="timeout")
    except Exception as e:
        return HealthResult(healthy=False, error=str(e))
```

---

# PART VII: ECONOMICS

## Token Flow

```
┌────────────────────────────────────────────────────────────────┐
│                      TOKEN ECONOMICS                           │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│   USER                                                         │
│    │                                                           │
│    │ Spends Credits                                            │
│    ▼                                                           │
│  ┌─────────────────┐                                           │
│  │  INFERENCE      │                                           │
│  │  REQUEST        │                                           │
│  └────────┬────────┘                                           │
│           │                                                    │
│           │ On Success Only                                    │
│           ▼                                                    │
│  ┌─────────────────┐      ┌─────────────────┐                 │
│  │  OPERATOR       │◀────▶│  AiAS           │                 │
│  │  (90%)          │      │  PROTOCOL FEE   │                 │
│  │                 │      │  (10%)          │                 │
│  └─────────────────┘      └─────────────────┘                 │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

## Pricing Model

- **User pays**: Credits per 1K tokens (set by operator, minimum floor)
- **Operator receives**: 90% of user payment
- **Protocol fee**: 10% to AiAS treasury
- **Failed requests**: No charge, no payout

## Example Transaction

```
User requests: llama-3.1-70b-instruct
Operator rate: $0.50 / 1K tokens
Response: 2,340 tokens

User charged:   $0.50 × 2.34 = $1.17
Operator earns: $1.17 × 0.90 = $1.05
Protocol fee:   $1.17 × 0.10 = $0.12
```

## Payout Schedule

- Earnings accumulate in operator balance
- Minimum withdrawal: $50
- Payout methods: Stripe, Crypto (Phase 2)
- Processing time: 1-3 business days

---

# PART VIII: UI/UX DESIGN LANGUAGE

## The Aesthetic: "Transmission from 2035"

The PIN interface should feel like you're accessing technology from the future — clean, holographic, data-rich. Think:
- Bloomberg Terminal meets Cyberpunk
- Minority Report data visualization
- NASA mission control precision

### Color Palette

```css
/* PIN UI Colors */
--pin-void: #0a0a0f;           /* Deep space black */
--pin-grid: #1a1a2e;           /* Grid background */
--pin-glow: #00ff88;           /* Primary accent - matrix green */
--pin-pulse: #00d4ff;          /* Secondary accent - cyan */
--pin-earn: #ffd700;           /* Earnings/gold */
--pin-warn: #ff4444;           /* Warnings/offline */
--pin-text: #e0e0e0;           /* Primary text */
--pin-muted: #666680;          /* Muted text */
```

### Typography

- **Headlines**: Space Grotesk or similar geometric sans
- **Data**: JetBrains Mono or similar monospace
- **Body**: Inter or system sans-serif

### Visual Elements

1. **Glowing Borders** — Subtle neon outlines on cards
2. **Grid Backgrounds** — Faint perspective grids suggesting infinite depth
3. **Pulse Animations** — Heartbeat-like pulses for live data
4. **Data Streams** — Flowing numbers/tokens visualization
5. **Holographic Cards** — Glass-morphism with rainbow refractions

## Page Designs

### 1. PIN Landing Page (`/pin`)

**Hero Section**
```
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│              ◆ P2P INFERENCE NETWORK ◆                        │
│                                                                │
│     "The future of AI is distributed. Join the network."      │
│                                                                │
│          [ BECOME AN OPERATOR ]    [ ACCESS THE NETWORK ]     │
│                                                                │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│   │    142       │  │   1.2M       │  │   980ms      │        │
│   │  OPERATORS   │  │  REQUESTS/DAY│  │  AVG LATENCY │        │
│   └──────────────┘  └──────────────┘  └──────────────┘        │
│                                                                │
│         ╔══════════════════════════════════════╗               │
│         ║  LIVE INFERENCE FEED                 ║               │
│         ║  ▸ op_alpha → 2.3K tokens → $1.17    ║               │
│         ║  ▸ op_beta  → 890 tokens  → $0.44    ║               │
│         ║  ▸ op_gamma → 1.1K tokens → $0.55    ║               │
│         ╚══════════════════════════════════════╝               │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

**Value Props Section**
- "Turn Idle GPUs Into Revenue"
- "Access Distributed Intelligence"
- "No Contracts. No Commitments."
- "OpenAI-Compatible. Drop-in Ready."

**Live Network Visualization**
- 3D globe with operator nodes as glowing points
- Real-time connection lines showing inference routes
- Pulsing activity indicators

### 2. Operator Dashboard (`/pin/operator`)

```
┌────────────────────────────────────────────────────────────────┐
│  ◆ OPERATOR COMMAND CENTER                    [op_alpha]  ● LIVE │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                    EARNINGS                              │  │
│  │     $1,523.50              +$142.30 (24h)               │  │
│  │     ████████████████░░░░░░░░ ← earnings chart            │  │
│  │     [ WITHDRAW ]                                         │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   15,234    │  │   97.2%     │  │   1.24s     │            │
│  │  REQUESTS   │  │  SUCCESS    │  │  AVG RESP   │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  REPUTATION SCORE                                        │  │
│  │  ████████████████████████░░░░  0.94 / 1.00              │  │
│  │  ↑ Top 8% of operators                                   │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │  RECENT JOBS                                             │  │
│  │  ▸ llama-3.1-70b │ 2,340 tok │ 1.2s │ $1.17 │ ✓        │  │
│  │  ▸ mistral-7b    │ 890 tok   │ 0.4s │ $0.44 │ ✓        │  │
│  │  ▸ llama-3.1-70b │ 3,100 tok │ 1.8s │ $1.55 │ ✓        │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### 3. Network Explorer (`/pin/network`)

```
┌────────────────────────────────────────────────────────────────┐
│  ◆ PIN NETWORK EXPLORER                              LIVE ●    │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                    3D GLOBE VISUALIZATION               │  │
│  │                                                          │  │
│  │                         ╭──○──╮                         │  │
│  │                    ○───○      ○───○                     │  │
│  │                   /    ╲      ╱    \                    │  │
│  │                  ○      ○────○      ○                   │  │
│  │                   \    /      \    /                    │  │
│  │                    ○──○        ○──○                     │  │
│  │                                                          │  │
│  │              [ US-EAST ]  [ EU-WEST ]  [ ASIA ]         │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                                │
│  OPERATOR DIRECTORY                                            │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ RANK │ OPERATOR      │ REGION  │ MODELS │ SCORE │ RATE  │ │
│  │──────┼───────────────┼─────────┼────────┼───────┼───────│ │
│  │  #1  │ GPU Farm Alpha│ us-east │ 3      │ 0.98  │ $0.45 │ │
│  │  #2  │ Neural Node   │ eu-west │ 2      │ 0.96  │ $0.50 │ │
│  │  #3  │ Compute Co    │ asia    │ 4      │ 0.94  │ $0.40 │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  LIVE THROUGHPUT                                               │
│  ██████████████████████████████░░░░░░░░  1.2M req/24h         │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### 4. Operator Registration (`/pin/join`)

```
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│               ◆ JOIN THE INFERENCE NETWORK ◆                  │
│                                                                │
│     "Your GPU. Your rules. Your earnings."                    │
│                                                                │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  STEP 1: CONFIGURE YOUR NODE                                   │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Node Name          [ GPU Farm Alpha______________ ]     │ │
│  │  Endpoint URL       [ https://my-gpu.example.com__ ]     │ │
│  │  Region             [ US-EAST ▼ ]                        │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  STEP 2: DECLARE YOUR MODELS                                   │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  ☑ llama-3.1-70b-instruct                               │ │
│  │  ☑ mistral-7b-instruct                                  │ │
│  │  ☐ codellama-34b                                        │ │
│  │  ☐ mixtral-8x7b                                         │ │
│  │  + Add custom model                                      │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  STEP 3: SET YOUR PRICING                                      │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Rate per 1K tokens  [ $0.50 ]                          │ │
│  │  Capacity            [ 10 concurrent requests ]          │ │
│  │                                                          │ │
│  │  Estimated monthly: $2,400 - $8,000 based on network    │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│              [ ◆ REGISTER & START EARNING ◆ ]                 │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

# PART IX: PHASED BUILD PLAN

## Phase 0: Trusted Mesh (MVP)
**Duration: 2-3 weeks**
**Goal: Prove the inference routing loop works**
**Status: ✅ COMPLETE (2026-01-05)**

### Week 1: Foundation
- [x] Redis schema implementation (all `pin:` namespaces) ✅
- [x] Operator model and storage layer ✅
- [x] Basic FastAPI routes: register, heartbeat, status ✅
- [x] Atomic LUA scripts for financial operations ✅
- [x] Heartbeat background worker (stale operator eviction) ✅

### Week 2: Routing
- [x] `/v1/pin/chat/completions` endpoint ✅
- [x] Operator selection algorithm (reputation-weighted) ✅
- [x] Failover logic (3 attempts with operator exclusion) ✅
- [x] Basic reputation tracking ✅
- [x] Token metering integration with atomic billing ✅
- [x] Proof-of-Response achieved (remote test node) ✅

### Week 3: UI & Polish
- [x] PIN landing page `/pin` (futuristic aesthetic) ✅
- [x] Operator registration flow `/pin/join` ✅
- [x] Operator dashboard `/pin/operator` (earnings, withdrawals, wallet) ✅
- [x] Network explorer `/pin/network` ✅
- [x] Manual operator onboarding (Interchained shared node) ✅

### Week 4: Operator Onboarding (2026-01-05)
- [x] Ollama endpoint verification API (`/v1/pin/operators/verify-endpoint`) ✅
- [x] Auto-discovery of models from Ollama `/api/tags` ✅
- [x] Client ID + API Secret generation for PIN Client auth ✅
- [x] PIN Client technical specification document ✅
- [x] BSC wallet management for USDT payouts ✅
- [x] Withdrawal request system with admin approval ✅
- [x] Auth-gated registration (redirect to login if unauthenticated) ✅

### Exit Criteria - ALL MET ✅
- ✅ Route inference request to operator and back (28s latency, 7 models)
- ✅ Track tokens and credits atomically (LUA scripts)
- ✅ 90/10 fee split with adjustable protocol fee
- ✅ Transaction recording and audit trail

---

## Phase 1: Open Operators
**Duration: 4-6 weeks**
**Goal: Incentivized participation at scale**
**Status: 🚧 IN PROGRESS**

### Completed
- [x] Self-serve operator registration (with input validation) ✅
- [x] Pricing floors ($0.0001) and ceilings ($100) ✅
- [x] Configurable protocol fee (admin-adjustable 0-50%) ✅
- [x] Network explorer with live visualization ✅
- [x] BSC USDT withdrawal system (replaces Stripe) ✅
- [x] Ollama-only operator flow (simplified onboarding) ✅
- [x] Endpoint verification + model auto-discovery ✅
- [x] PIN Client architecture specification ✅

### In Progress - Go Live Checklist
- [ ] **Fix online status detection** (heartbeat → PIN Client connection)
- [ ] **PIN Client WebSocket endpoint** (`/v1/pin/ws`) for persistent connections
- [ ] **WebSocket-based inference routing** (client pulls jobs, not push-based)
- [ ] **Operator dashboard real-time status** (WebSocket connection indicator)
- [ ] **PIN Client MVP** (Tauri-based, credential storage, heartbeat, inference proxy)

### Remaining
- [ ] Advanced reputation algorithm (success rate weighting)
- [ ] Operator dashboard v2 (charts, history, alerts)
- [ ] User dashboard (usage, costs, preferences)
- [ ] Documentation and operator onboarding guide
- [ ] PIN Client auto-updater

### Exit Criteria
- 20+ independent operators
- 10K+ requests/day
- Self-sustaining economics

---

## Phase 2: Protocol
**Duration: 8-12 weeks**
**Goal: Establish moat and protocolization**

- [ ] Slashing mechanism for bad actors
- [ ] Cooldown periods for returning operators
- [ ] Regional routing (latency-optimized)
- [ ] SLA tiers (guaranteed latency, priority routing)
- [ ] Optional on-chain settlement layer
- [ ] Public whitepaper release
- [ ] SDK for operator integration
- [ ] Enterprise features (dedicated capacity, private mesh)

### Exit Criteria
- 100+ operators
- 1M+ requests/day
- Revenue positive
- Whitepaper published

---

# PART X: INTEGRATION WITH EXISTING AIAS

## Leverage Points

| Existing System | PIN Integration |
|-----------------|-----------------|
| Redis storage | Add `pin:` namespace |
| AI Orchestrator | Extend for P2P routing |
| User auth | Operator role + API keys |
| Subscription billing | Credit system for PIN |
| FastAPI backend | New `/v1/pin/*` routes |
| React frontend | New PIN pages |
| Theme system | PIN-specific theme |

## New Files Required

```
api/
  routes/
    pin.py                 # All PIN API routes
  services/
    pin_router.py          # Routing engine
    pin_reputation.py      # Reputation calculations
    pin_billing.py         # Token metering
  workers/
    pin_heartbeat.py       # Background health monitor

client/src/
  pages/
    pin/
      Landing.tsx          # /pin
      Join.tsx             # /pin/join
      Dashboard.tsx        # /pin/operator
      Network.tsx          # /pin/network
  components/
    pin/
      LiveFeed.tsx
      OperatorCard.tsx
      NetworkGlobe.tsx
      EarningsChart.tsx
  themes/
    backgrounds/
      PinBackground.tsx    # Futuristic grid aesthetic
```

---

# PART XI: SUCCESS METRICS

## Phase 0 KPIs
- Time to first inference: <5 seconds
- Routing success rate: >99%
- Operator uptime: >95%
- User satisfaction: Qualitative feedback

## Phase 1 KPIs
- Operators registered: 20+
- Daily requests: 10K+
- Average response time: <2 seconds
- Operator earnings: $100+/operator/month

## Phase 2 KPIs
- Operators registered: 100+
- Daily requests: 1M+
- Revenue: $10K+/month
- Network uptime: 99.9%

---

# APPENDIX A: OPERATOR AGENT REFERENCE

## Minimal Agent Implementation

Operators run a lightweight agent alongside their inference server:

```python
# pin_agent.py - Minimal operator agent

import asyncio
import httpx
from datetime import datetime

AIAS_URL = "https://aiassist.app"
OPERATOR_ID = "op_abc123"
API_KEY = "pin_sk_..."

async def heartbeat_loop():
    """Send heartbeat every 30 seconds."""
    async with httpx.AsyncClient() as client:
        while True:
            try:
                await client.post(
                    f"{AIAS_URL}/v1/pin/operators/heartbeat",
                    json={
                        "operator_id": OPERATOR_ID,
                        "current_load": get_current_load(),
                        "capacity": 10,
                        "models_available": ["llama-3.1-70b"]
                    },
                    headers={"Authorization": f"Bearer {API_KEY}"}
                )
                print(f"[{datetime.now()}] Heartbeat sent")
            except Exception as e:
                print(f"[{datetime.now()}] Heartbeat failed: {e}")
            
            await asyncio.sleep(30)

if __name__ == "__main__":
    asyncio.run(heartbeat_loop())
```

---

# APPENDIX B: GLOSSARY

| Term | Definition |
|------|------------|
| **PIN** | P2P Inference Network |
| **Operator** | GPU/NPU owner providing inference services |
| **Node** | Operator's inference server |
| **PoR** | Proof-of-Response — validation via successful inference |
| **Heartbeat** | Periodic health signal from operator |
| **Reputation** | Score based on performance history |
| **Credits** | Internal currency for inference consumption |
| **Routing** | Algorithm selecting optimal operator |
| **Failover** | Automatic retry with different operator |
| **Slashing** | Penalty for bad behavior (Phase 2) |

---

# APPENDIX C: REVISION HISTORY

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-05 | AiAS Team | Initial specification |

---

**END OF WORKPLAN**

```
┌────────────────────────────────────────────────────────────────┐
│                                                                │
│                    ◆ THE FUTURE IS DISTRIBUTED ◆              │
│                                                                │
│                      Let's build it together.                  │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```
