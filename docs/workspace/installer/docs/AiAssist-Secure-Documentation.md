# AiAssist Secure

## Enterprise AI Platform - Installation & Configuration Guide

**Version 1.0.0**

---

## Table of Contents

1. [Introduction](#introduction)
2. [System Requirements](#system-requirements)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [BYOK API Keys](#byok-api-keys)
6. [Features Overview](#features-overview)
7. [Support](#support)

---

## Introduction

AiAssist Secure is an enterprise-grade AI chat platform that puts you in complete control of your AI infrastructure. With Bring-Your-Own-Key (BYOK) support, you use your own API keys from providers like OpenAI, Anthropic, Groq, Gemini, and Mistral.

**Key Benefits:**
- Full data ownership - your keys, your data
- Multi-provider AI support
- Shadow Mode for human oversight
- Keystone app builder
- Self-hosted on your own VPS

---

## System Requirements

### Minimum Server Requirements

| Component | Requirement |
|-----------|-------------|
| OS | Ubuntu 20.04+ / Debian 11+ |
| CPU | 2 cores |
| RAM | 4 GB |
| Storage | 20 GB SSD |
| PHP | 8.1+ with curl, json, zip extensions |
| Python | 3.10+ |
| Node.js | 18+ |
| Redis | 6.0+ |

### Optional
- PostgreSQL 14+ (for analytics)
- Nginx (recommended for production)
- SSL certificate (Let's Encrypt recommended)

---

## Installation

### Step 1: Upload Files

Upload the AiAssist Secure package to your VPS:

```bash
scp aiassist-secure-v1.0.0.zip user@your-server:/var/www/
```

### Step 2: Extract Package

```bash
cd /var/www
unzip aiassist-secure-v1.0.0.zip
cd aiassist-secure
```

### Step 3: Run Web Installer

1. Point your browser to: `https://yourdomain.com/installer/`
2. Enter your Envato purchase code
3. The installer will verify your license and download core components
4. Follow the on-screen prompts to complete setup

### Step 4: Configure Environment

The installer creates a `.env` file. Review and update:

```ini
REDIS_URL=redis://localhost:6379
SESSION_SECRET=your-generated-secret
```

### Step 5: Build for Production

```bash
cd /var/www/aiassist

# Install dependencies
npm install

# Build the frontend (creates optimized dist/)
npm run build
```

### Step 6: Test Manually (Optional)

Before setting up services, you can test manually:

```bash
# Terminal 1: Start backend
./start_back.sh

# Terminal 2: Start frontend
./start_front.sh
```

Visit `http://your-server-ip:5000` to verify everything works.

---

## Production Setup

For production, run services as systemd daemons so they start automatically on boot.

### Step 1: Install Redis

```bash
sudo apt update
sudo apt install redis-server -y
sudo systemctl enable redis-server
sudo systemctl start redis-server
```

### Step 2: Create Python Virtual Environment

```bash
cd /var/www/aiassist/api
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 3: Create API Service

Create `/etc/systemd/system/aiassist-api.service`:

```ini
[Unit]
Description=AiAssist Secure API
After=network.target redis-server.service
Wants=redis-server.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/aiassist
EnvironmentFile=/var/www/aiassist/.env
ExecStart=/bin/bash /var/www/aiassist/start_back.sh
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Step 4: Create Frontend Service

Create `/etc/systemd/system/aiassist-frontend.service`:

```ini
[Unit]
Description=AiAssist Secure Frontend
After=network.target aiassist-api.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/var/www/aiassist
EnvironmentFile=/var/www/aiassist/.env
ExecStart=/bin/bash /var/www/aiassist/start_front.sh
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Step 5: Enable and Start Services

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services to start on boot
sudo systemctl enable aiassist-api
sudo systemctl enable aiassist-frontend

# Start services now
sudo systemctl start aiassist-api
sudo systemctl start aiassist-frontend

# Check status
sudo systemctl status aiassist-api
sudo systemctl status aiassist-frontend
```

### Step 6: Configure Nginx

Create `/etc/nginx/sites-available/aiassist`:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    # Frontend (React app)
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # API routes
    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket for real-time chat
    location /socket.io/ {
        proxy_pass http://127.0.0.1:8000/socket.io/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/aiassist /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default  # Optional: remove default site
sudo nginx -t
sudo systemctl restart nginx
```

### SSL with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

---

## Environment Variables

The installer configures core variables automatically. Additional variables may be set in `.env` for advanced configurations.

### Core Variables (Set by Installer)

| Variable | Required | Description |
|----------|----------|-------------|
| `REDIS_URL` | Yes | Redis connection string (e.g., `redis://localhost:6379`) |
| `DATABASE_URL` | Optional | PostgreSQL for analytics/reporting |
| `SESSION_SECRET` | Yes | 64-character hex string for session encryption |

### Runtime Variables (Set After Installation)

| Variable | Required | Description |
|----------|----------|-------------|
| `REDIS_NAMESPACE` | No | Prefix for Redis keys (default: `aiassist`) |
| `BACKEND_URL` | No | Backend API URL for split deployments (default: `http://localhost:8000`) |
| `PORT` | No | Frontend port (default: `5000`) |
| `BACKEND_PORT` | No | Backend API port (default: `8000`) |

### API Integration Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `LANDING_PAGE_API_KEY` | No | API key for public landing page chat widget |
| `VITE_LANDING_PAGE_API_KEY` | No | Same key, exposed to frontend (requires rebuild) |
| `STRIPE_SECRET_KEY` | No | Stripe API key for subscriptions |
| `STRIPE_PUBLISHABLE_KEY` | No | Stripe public key |
| `STRIPE_WEBHOOK_SECRET` | No | Stripe webhook verification |
| `GOOGLE_TTS_CREDENTIALS` | No | Google TTS service account JSON |

### PIN Network Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `PIN_ENCRYPTION_KEY` | No | Encryption key for PIN operator credentials |

### Example .env File

```bash
# Core (set by installer)
REDIS_URL=redis://localhost:6379
SESSION_SECRET=your-64-char-hex-secret

# Runtime configuration
REDIS_NAMESPACE=aiassist
BACKEND_URL=http://localhost:8000

# Optional integrations
STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_PUBLISHABLE_KEY=pk_live_xxx
```

**Note:** API keys for AI providers (OpenAI, Anthropic, etc.) are managed in the dashboard, not environment variables.

---

## BYOK API Keys

AiAssist Secure supports multiple AI providers. Add your API keys in the dashboard under Settings > API Keys.

### Supported Providers (11 + PIN)

| Provider | Models | Get API Key |
|----------|--------|-------------|
| OpenAI | GPT-4o, GPT-4 Turbo, o1, o3 | https://platform.openai.com |
| Anthropic | Claude 4, Claude 3.5 Sonnet | https://console.anthropic.com |
| Google | Gemini 2.0, Gemini Pro | https://ai.google.dev |
| Groq | Llama 3.3, Mixtral, Gemma 2 | https://console.groq.com |
| Mistral | Mistral Large, Codestral | https://console.mistral.ai |
| xAI | Grok-2, Grok-3 | https://x.ai |
| Cohere | Command R+, Command R | https://cohere.com |
| DeepSeek | DeepSeek-V3, DeepSeek-R1 | https://deepseek.com |
| Perplexity | Sonar Pro, Sonar | https://perplexity.ai |
| Together AI | Llama, Qwen, DBRX | https://together.ai |
| Fireworks AI | Llama, Mixtral | https://fireworks.ai |

### PIN - P2P Inference Network

Connect to decentralized Ollama nodes for local LLM inference:
- No API keys required - uses community-operated nodes
- Credit-based billing with USDT payouts
- Quality-verified operators with speed tiers
- Models: Llama 3, Mistral, Qwen, Gemma, and more

Your API keys are stored securely and never leave your server.

---

## Features Overview

### Multi-Provider AI
Switch between AI providers seamlessly. Use different models for different workspaces.

### Shadow Mode (Enterprise)
AI drafts responses that require human approval before sending. Perfect for customer-facing communications.

### Keystone App Builder
Build custom AI-powered applications with our visual builder. Create chatbots, assistants, and automation workflows.

### Workspace Management
Organize conversations into workspaces. Assign team members and set permissions.

### Contact Management
Track leads and customers. AI remembers context from previous conversations.

### Memory System
Configurable conversation memory with PII filtering and safety features.

---

## Support

### Documentation
Visit https://aiassist.net/docs for full documentation.

### Email Support
Contact dev@interchained.org for technical assistance.

### Response Times
- Critical issues: 24 hours
- General questions: 48-72 hours

### What's Included
- 6 months of support from purchase date
- Bug fixes and security updates
- Installation assistance

---

## License

This software is licensed under the Envato Regular or Extended License.

**Regular License:** One end product, free or paid for end users
**Extended License:** One end product where end users are charged

See https://codecanyon.net/licenses for full terms.

---

© 2026 AiAssist.net - All Rights Reserved
