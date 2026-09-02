---
title: Python SDK
icon: Code
category: Developers
order: 3
description: Documentation for the official Python server SDK.
---

# Python Server SDK Documentation

> `aiassist` - Self-host the AiAssist backend with FastAPI, Flask, or Django

Run your own AI chat infrastructure with full control over data, models, and scaling.

## Installation

```bash
pip install aiassist
```

### Requirements

- Python 3.9+
- Redis 6.0+
- Groq API key (or compatible LLM provider)

---

## Quick Start

### FastAPI

```python
from fastapi import FastAPI
from aiassist import AiAssistRouter, AiAssistConfig

app = FastAPI()

config = AiAssistConfig(
    groq_api_key="gsk_...",
    redis_url="redis://localhost:6379/0"
)

app.include_router(AiAssistRouter(config), prefix="/api")

# Run with: uvicorn main:app --reload
```

### Flask

```python
from flask import Flask
from aiassist.flask import AiAssistBlueprint, AiAssistConfig

app = Flask(__name__)

config = AiAssistConfig(
    groq_api_key="gsk_...",
    redis_url="redis://localhost:6379/0"
)

app.register_blueprint(AiAssistBlueprint(config), url_prefix="/api")

# Run with: flask run
```

### Django

```python
# settings.py
INSTALLED_APPS = [
    ...
    'aiassist.django',
]

AIASSIST_CONFIG = {
    'groq_api_key': 'gsk_...',
    'redis_url': 'redis://localhost:6379/0',
}

# urls.py
from django.urls import path, include

urlpatterns = [
    path('api/', include('aiassist.django.urls')),
]
```

---

## Configuration

### `AiAssistConfig`

```python
from aiassist import AiAssistConfig

config = AiAssistConfig(
    # Required
    groq_api_key="gsk_...",
    redis_url="redis://localhost:6379/0",
    
    # Optional - AI Settings
    default_model="llama-3.3-70b-versatile",
    fallback_model="llama-3.1-8b-instant",
    max_tokens=2048,
    temperature=0.7,
    
    # Optional - System Prompt
    system_prompt="""You are a helpful AI assistant. 
    Be concise, friendly, and professional.""",
    
    # Optional - Rate Limiting
    rate_limit_requests=100,      # per minute
    rate_limit_tokens=50000,      # per minute
    
    # Optional - Session Management
    session_ttl=86400,            # 24 hours
    workspace_ttl=604800,         # 7 days
    
    # Optional - Security
    allowed_origins=["https://yoursite.com"],
    require_auth=False,
    
    # Optional - Callbacks
    on_message=lambda ws_id, msg: print(f"New message in {ws_id}"),
    on_takeover=lambda ws_id, admin_id: notify_admin(admin_id),
    on_error=lambda error: log_error(error)
)
```

### Environment Variables

```bash
# .env file
AIASSIST_GROQ_API_KEY=gsk_...
AIASSIST_REDIS_URL=redis://localhost:6379/0
AIASSIST_DEFAULT_MODEL=llama-3.3-70b-versatile
AIASSIST_SESSION_SECRET=your-secret-key
```

```python
from aiassist import AiAssistConfig

config = AiAssistConfig.from_env()  # Loads from environment
```

---

## Core Components

### `AiAssistRouter` (FastAPI)

The main router that handles all chat endpoints.

```python
from aiassist import AiAssistRouter, AiAssistConfig

config = AiAssistConfig(...)
router = AiAssistRouter(config)

# Includes these endpoints:
# POST /workspaces              - Create workspace
# GET  /workspaces              - List workspaces (admin)
# GET  /workspaces/{id}         - Get workspace
# PATCH /workspaces/{id}        - Update workspace (mode change)
# POST /workspaces/{id}/messages - Send message
# GET  /workspaces/{id}/messages - Get messages
# GET  /workspaces/{id}/typing   - Get typing preview (admin)
# POST /workspaces/{id}/typing   - Update typing preview
# POST /workspaces/{id}/directives - Add directive (admin)
```

### `AiOrchestrator`

The AI engine that handles response generation.

```python
from aiassist import AiOrchestrator, AiOrchestratorConfig

orchestrator = AiOrchestrator(
    groq_api_key="gsk_...",
    default_model="llama-3.3-70b-versatile"
)

# Generate a response
response = await orchestrator.generate(
    workspace_id="ws_123",
    user_message="How do I reset my password?",
    conversation_history=messages,
    directives=active_directives
)
```

### `RedisStorage`

Handles all data persistence.

```python
from aiassist import RedisStorage

storage = RedisStorage("redis://localhost:6379/0")

# Workspace operations
workspace = storage.create_workspace(title="Support Chat")
workspace = storage.get_workspace("ws_123")
workspaces = storage.list_workspaces(active_only=True)

# Message operations
message = storage.add_message(
    workspace_id="ws_123",
    content="Hello!",
    role="user"
)
messages = storage.get_messages("ws_123")

# Directive operations
directive = storage.add_directive(
    workspace_id="ws_123",
    content="Be extra helpful about pricing",
    directive_type="guidance"
)
```

---

## Human Takeover

### Switching Modes

```python
from aiassist import WorkspaceMode

# Switch to human control
storage.update_workspace(
    workspace_id="ws_123",
    mode=WorkspaceMode.TAKEOVER
)

# Switch back to AI
storage.update_workspace(
    workspace_id="ws_123",
    mode=WorkspaceMode.AI
)
```

### Sending as AI (Human Impersonation)

```python
# Admin sends message that appears as AI to customer
message = storage.add_message(
    workspace_id="ws_123",
    content="I've processed your refund. You should see it in 3-5 days.",
    role="manager",
    visible_to_client=True,
    metadata={"sent_by": "admin_456", "display_as": "ai"}
)
```

### Internal Notes (Hidden from Customer)

```python
# Add note only visible to admins
note = storage.add_message(
    workspace_id="ws_123",
    content="Customer is frustrated. Handle with care.",
    role="system",
    visible_to_client=False
)
```
