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

---

## Directives System

Inject context, instructions, or constraints into the AI's behavior.

### Directive Types

```python
from aiassist import DirectiveType

# SYSTEM - Core behavior (highest priority)
storage.add_directive(
    workspace_id="ws_123",
    content="Never discuss competitor products.",
    directive_type=DirectiveType.SYSTEM,
    priority=100
)

# CONTEXT - Background information
storage.add_directive(
    workspace_id="ws_123",
    content="This customer is a VIP enterprise client.",
    directive_type=DirectiveType.CONTEXT,
    priority=50
)

# GUIDANCE - Soft suggestions
storage.add_directive(
    workspace_id="ws_123",
    content="Try to upsell the premium plan if relevant.",
    directive_type=DirectiveType.GUIDANCE,
    priority=10
)

# TONE - Communication style
storage.add_directive(
    workspace_id="ws_123",
    content="Use a formal, professional tone.",
    directive_type=DirectiveType.TONE,
    priority=30
)
```

### Managing Directives

```python
# List active directives
directives = storage.get_directives("ws_123", active_only=True)

# Deactivate a directive
storage.update_directive("dir_123", active=False)

# Delete a directive
storage.delete_directive("dir_123")
```

---

## WebSocket Support

For real-time features like typing preview.

### FastAPI with Socket.IO

```python
from fastapi import FastAPI
import socketio
from aiassist import AiAssistRouter, create_socket_handlers

app = FastAPI()
sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')

# Register socket handlers
create_socket_handlers(sio, storage, orchestrator)

# Mount both
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)

# Endpoints handled:
# Client namespace (/client):
#   - join_workspace
#   - send_message
#   - typing_preview
#
# Admin namespace (/admin):
#   - subscribe_workspace
#   - send_as_ai
#   - change_mode
```

---

## Authentication & Authorization

### API Key Authentication

```python
from aiassist import AiAssistConfig, require_api_key

config = AiAssistConfig(
    require_auth=True,
    api_key_header="X-API-Key"
)

# Clients must include: X-API-Key: aai_xxx
```

### Role-Based Access

```python
from aiassist import UserRole

# Define roles
class UserRole:
    CLIENT = "client"      # End users chatting
    MANAGER = "manager"    # Can monitor and takeover
    ADMIN = "admin"        # Full access

# Protect admin routes
@router.get("/workspaces")
async def list_workspaces(user: User = Depends(require_role(UserRole.MANAGER))):
    return storage.list_workspaces()
```

### Custom Auth Integration

```python
from aiassist import AiAssistRouter

router = AiAssistRouter(
    config,
    auth_dependency=your_auth_dependency,  # Your existing auth
    get_user_id=lambda request: request.state.user.id
)
```

---

## Webhooks

Get notified of events in real-time.

```python
config = AiAssistConfig(
    webhook_url="https://yoursite.com/webhooks/aiassist",
    webhook_secret="whsec_...",
    webhook_events=[
        "conversation.started",
        "conversation.ended",
        "message.created",
        "mode.changed",
        "takeover.requested"
    ]
)
```

### Webhook Payload

```json
{
  "event": "message.created",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "workspace_id": "ws_123",
    "message": {
      "id": "msg_456",
      "role": "user",
      "content": "I need help with billing",
      "created_at": "2024-01-15T10:30:00Z"
    }
  },
  "signature": "sha256=..."
}
```

### Verifying Webhooks

```python
from aiassist import verify_webhook_signature

@app.post("/webhooks/aiassist")
async def handle_webhook(request: Request):
    payload = await request.body()
    signature = request.headers.get("X-AiAssist-Signature")
    
    if not verify_webhook_signature(payload, signature, webhook_secret):
        raise HTTPException(401, "Invalid signature")
    
    data = json.loads(payload)
    
    if data["event"] == "takeover.requested":
        notify_team_on_slack(data["data"]["workspace_id"])
    
    return {"ok": True}
```

---

## Custom LLM Providers

Use providers other than Groq.

### OpenAI

```python
from aiassist import AiAssistConfig, LLMProvider

config = AiAssistConfig(
    llm_provider=LLMProvider.OPENAI,
    openai_api_key="sk-...",
    default_model="gpt-4-turbo"
)
```

### Anthropic

```python
config = AiAssistConfig(
    llm_provider=LLMProvider.ANTHROPIC,
    anthropic_api_key="sk-ant-...",
    default_model="claude-3-opus"
)
```

### Custom Provider

```python
from aiassist import BaseLLMProvider

class MyCustomProvider(BaseLLMProvider):
    async def generate(self, messages, **kwargs):
        # Your implementation
        response = await my_llm_api.chat(messages)
        return response.content

config = AiAssistConfig(
    llm_provider=MyCustomProvider(api_key="...")
)
```

---

## Scaling & Production

### Redis Cluster

```python
config = AiAssistConfig(
    redis_url="redis://cluster-host:6379",
    redis_cluster=True
)
```

### Multiple Workers

```python
# Use with gunicorn/uvicorn workers
# Sessions and state are shared via Redis

# gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

### Health Checks

```python
from aiassist import health_check

@app.get("/health")
async def health():
    return await health_check(config)
    # Returns: {"redis": "ok", "llm": "ok", "status": "healthy"}
```

---

## Examples

### Complete FastAPI App

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from aiassist import AiAssistRouter, AiAssistConfig

app = FastAPI(title="My Chat API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://mysite.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

config = AiAssistConfig.from_env()
app.include_router(AiAssistRouter(config), prefix="/api")

@app.get("/")
async def root():
    return {"message": "Chat API is running"}
```

### With Custom Business Logic

```python
from aiassist import AiAssistRouter, AiAssistConfig
from aiassist.hooks import before_ai_response, after_message

config = AiAssistConfig(...)

@before_ai_response
async def inject_user_context(workspace_id, user_message, context):
    # Fetch user data from your database
    user = await get_user_from_workspace(workspace_id)
    if user:
        context["user_name"] = user.name
        context["subscription"] = user.plan
    return context

@after_message
async def sync_to_crm(workspace_id, message):
    if message.role == "user":
        await update_hubspot_contact(workspace_id, message)

router = AiAssistRouter(config)
```

---

## API Reference

See [API Reference](./api-reference.md) for complete endpoint documentation.

---

## Next Steps

- [React SDK](./react-sdk.md) - Frontend integration
- [Vanilla JS SDK](./vanilla-sdk.md) - No-framework widget
- [API Reference](./api-reference.md) - Full API documentation
- [Human Takeover Guide](./human-takeover.md) - Admin features
