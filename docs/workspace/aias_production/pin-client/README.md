# PIN Client v2.1.0

P2P Inference Network Operator Client - A Tauri-based desktop application that connects your local LLM instances to the PIN network.

## Overview

The PIN Client allows GPU/NPU operators to offer inference services through the P2P Inference Network. It:

1. **Securely stores credentials** in your OS keychain (macOS Keychain, Windows Credential Manager, Linux Secret Service)
2. **Maintains a persistent WebSocket connection** with auto-reconnect to the PIN server
3. **Supports multi-node configuration** - connect multiple inference endpoints from one client
4. **Dual API mode** - works with both Ollama and OpenAI-compatible APIs (vLLM, TGI, LocalAI, etc.)
5. **Quality interviews** - nodes are tested and assigned quality tiers (verified, standard, slow)
6. **Reports health metrics** (load, capacity, models) to the network
7. **Wallet management** - set your BSC payout address for USDT earnings

## What's New in v2.1.0

- **Multi-node support**: Configure multiple inference endpoints with different settings
- **OpenAI API mode**: Connect vLLM, text-generation-inference, or any OpenAI-compatible server
- **Interview system**: Automated quality testing for tier assignment
- **Wallet updates**: Configure payout address directly from the GUI
- **Auto-reconnect**: Resilient connection handling with automatic retry

## Prerequisites

- [Ollama](https://ollama.ai) or an OpenAI-compatible inference server running
- At least one model available
- PIN operator credentials (operator_id and api_secret from registration)

## Installation

### Pre-built Binaries

Download the latest release for your platform from the [Releases](https://github.com/aiassistsecure/pin-client/releases) page.

### Build from Source

1. Install Rust and Tauri prerequisites:
   ```bash
   # Install Rust
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   
   # macOS
   xcode-select --install
   
   # Ubuntu/Debian
   sudo apt update
   sudo apt install libwebkit2gtk-4.1-dev build-essential curl wget libssl-dev libgtk-3-dev libayatana-appindicator3-dev librsvg2-dev
   
   # Windows
   # Install Visual Studio Build Tools
   ```

2. Clone and build:
   ```bash
   cd pin-client
   cargo tauri build
   ```

## Configuration

### Credentials Tab

1. **Operator ID**: Your `op_xxxx` identifier from registration
2. **API Secret**: Your secret key (stored securely in OS keychain)
3. **Server URL**: Leave blank for production, or enter custom server URL

### Nodes Tab

Configure one or more inference endpoints:

| Field | Description | Example |
|-------|-------------|---------|
| Alias | Friendly name for the node | `GPU-1`, `vLLM-Server` |
| Inference URI | URL to your inference server | `http://localhost:11434` |
| API Mode | `ollama` or `openai` | See table below |
| Region | Geographic region code | `us-east`, `eu-west`, `ap-south` |
| Capacity | Max concurrent requests | `10` |

#### API Mode Selection

| Mode | Use For | Model Endpoint | Chat Endpoint |
|------|---------|----------------|---------------|
| `ollama` | Ollama instances | `/api/tags` | `/api/chat` |
| `openai` | vLLM, TGI, LocalAI, LMStudio | `/v1/models` | `/v1/chat/completions` |

### Wallet Tab

Enter your BSC (Binance Smart Chain) wallet address to receive USDT payouts for completed inference requests.

## Quality Tiers

After connecting, each node undergoes an interview process where the server sends test prompts to evaluate:

- **Accuracy**: Correctness of responses
- **Speed**: Tokens per second throughput

| Tier | Requirements (Ollama) | Requirements (OpenAI) | Priority |
|------|----------------------|----------------------|----------|
| `verified` | >90% accuracy, >20 tok/s | >95% accuracy, >30 tok/s | Highest |
| `standard` | >70% accuracy, >10 tok/s | >85% accuracy, >20 tok/s | Normal |
| `slow` | >70% accuracy, <10 tok/s | >85% accuracy, <20 tok/s | Low (budget) |
| `failed` | <70% accuracy | <85% accuracy | Blocked |

## Message Protocol

### Authentication
```json
{
  "type": "AUTH",
  "client_id": "op_xxxx",
  "timestamp": "1704499200",
  "signature": "sha256(client_id + timestamp + sha256(api_secret))"
}
```

### Register Node
```json
{
  "type": "REGISTER_NODE",
  "alias": "GPU-1",
  "models": ["llama3:8b", "mistral:7b"],
  "capacity": 10,
  "region": "us-east"
}
```

### Update Wallet
```json
{
  "type": "UPDATE_WALLET",
  "payout_address": "0x..."
}
```

### Interview Request (from server)
```json
{
  "type": "INTERVIEW_REQUEST",
  "interview_id": "interview_xxx",
  "node_id": "node_xxx",
  "model": "qwen2:7b",
  "prompts": [
    {"id": "fact_planets", "prompt": "How many planets?", "max_tokens": 50}
  ],
  "timeout_ms": 120000
}
```

### Interview Result
```json
{
  "type": "INTERVIEW_RESULT",
  "interview_id": "interview_xxx",
  "model": "qwen2:7b",
  "results": [
    {
      "prompt_id": "fact_planets",
      "response": "There are 8 planets.",
      "ttft_ms": 150,
      "total_ms": 2500,
      "tokens_generated": 12
    }
  ]
}
```

### Inference Request (from server)
```json
{
  "type": "INFERENCE_REQUEST",
  "request_id": "req_abc123",
  "payload": {
    "model": "llama3:8b",
    "messages": [{"role": "user", "content": "Hello"}]
  }
}
```

### Inference Response
```json
{
  "type": "INFERENCE_RESPONSE",
  "request_id": "req_abc123",
  "result": {
    "model": "llama3:8b",
    "choices": [{"index": 0, "message": {"role": "assistant", "content": "Hi!"}}],
    "usage": {"prompt_tokens": 5, "completion_tokens": 10, "total_tokens": 15}
  }
}
```

## System Tray

The PIN Client runs in your system tray with the following options:
- **Show Window**: Open the main window
- **Connect**: Connect to PIN network
- **Disconnect**: Disconnect from network
- **Quit**: Exit the application

## Security

- API secrets are stored in your OS's secure credential storage (never in config files)
- WebSocket connections use TLS encryption
- Authentication uses HMAC-SHA256 signatures with timestamp replay protection
- Payout addresses are validated before acceptance

## Troubleshooting

### "Failed to connect to Ollama/OpenAI"
- Ensure your inference server is running
- Check the URL is correct and accessible
- Verify the API mode matches your server type

### "Invalid credentials"
- Verify your operator_id and api_secret from the operator dashboard
- Re-register if credentials were regenerated

### "Interview failed"
- Ensure you have the required benchmark models (for Ollama: llama3:8b, mistral:7b, qwen2:7b, or gemma2:7b)
- Check that your server can respond within the timeout period
- Slow hardware may result in "slow" tier instead of "verified"

### "Connection keeps dropping during interview"
- Long response times may cause timeout disconnects
- Consider using faster models or hardware
- The client will auto-reconnect and retry

### "No models found"
- For Ollama: Run `ollama list` to verify models are pulled
- For OpenAI-compatible: Check the `/v1/models` endpoint returns model data

## License

MIT License - See LICENSE file for details.
