# AiAssist SDK Examples

This directory contains working examples demonstrating how to integrate AiAssist into different environments.

## Examples Overview

### 1. HTML Demo (`html-demo/`)

A vanilla JavaScript example showing how to embed the chat widget in any HTML page.

**Features:**
- Drop-in widget integration
- API key configuration
- Control methods (open, close, toggle)
- Event callbacks

**Usage:**
1. Get an API key from the AiAssist dashboard
2. Open `html-demo/index.html` in a browser
3. Enter your API key and click "Initialize Widget"
4. Click the chat bubble to start chatting

### 2. React Demo (`react-demo/`)

React components for building AI chat interfaces with TypeScript support.

**Features:**
- Embedded chat component
- Floating widget component
- Theme customization
- Hooks for custom implementations

**Files:**
- `App.tsx` - Main demo application
- `index.html` - Demo page structure

**Usage:**
```tsx
import { AiAssistChat, AiAssistChatWidget } from '@aiassist/react';

function MyApp() {
  return (
    <AiAssistChat
      apiKey="your-api-key"
      apiUrl="http://localhost:5000"
      height="400px"
      placeholder="Ask me anything..."
    />
  );
}
```

### 3. Python Demo (`python-demo/`)

Python examples showing backend integration with the AiAssist API.

**Files:**
- `server.py` - Full FastAPI server using the SDK
- `simple_example.py` - Simple API client example

**Simple Example Usage:**
```bash
# Set environment variables
export AIASSIST_API_URL=http://localhost:5000
export AIASSIST_API_KEY=aai_your_key_here

# Run the example
pip install httpx
python simple_example.py
```

**Full Server Usage:**
```bash
# Set environment variables
export REDIS_URL=redis://localhost:6379/12
export GROQ_API_KEY=your_groq_key

# Run the server
uvicorn server:app --reload --port 8001
```

## API Endpoints

All examples connect to these core API endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/workspaces` | POST | Create new workspace with initial message |
| `/api/workspaces/:id/messages` | POST | Send message to existing workspace |
| `/v1/chat/completions` | POST | OpenAI-compatible chat API |
| `/api/auth/register` | POST | Register new user |
| `/api/auth/login` | POST | User login |
| `/api/user/api-keys` | POST | Generate API key |

## Getting an API Key

1. Register at the AiAssist dashboard (`/register`)
2. Log in to your account (`/login`)
3. Go to the Dashboard page
4. Click "Generate New API Key"
5. Copy the key (it starts with `aai_`)

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AIASSIST_API_URL` | API server URL | `http://localhost:5000` |
| `AIASSIST_API_KEY` | Your API key | Required |
| `REDIS_URL` | Redis connection (server only) | `redis://localhost:6379/12` |
| `GROQ_API_KEY` | Groq API key (server only) | Required for AI |

### Widget Options

```javascript
AiAssist.init({
  apiKey: 'aai_...',           // Your API key
  endpoint: 'http://localhost:5000',  // API URL
  position: 'bottom-right',     // Widget position
  title: 'AI Assistant',        // Header title
  subtitle: 'Ask me anything',  // Header subtitle
  placeholder: 'Type here...',  // Input placeholder
  theme: 'dark',                // Theme: 'light' | 'dark'
  poweredBy: true,              // Show powered by link
  autoOpen: false,              // Auto-open on load
  autoOpenDelay: 3000,          // Delay before auto-open
  
  // Callbacks
  onReady: () => {},            // Widget initialized
  onOpen: () => {},             // Chat opened
  onClose: () => {},            // Chat closed
  onMessage: (msg) => {},       // Message received
  onError: (err) => {},         // Error occurred
});
```

## Troubleshooting

### "API error: 401"
- Check that your API key is correct
- Ensure the key hasn't expired or been revoked

### "API error: 500"
- Check that the server is running
- Verify GROQ_API_KEY is set correctly

### Widget not appearing
- Check browser console for errors
- Ensure the widget.js script is loaded
- Verify the API endpoint is accessible

## License

MIT License - See the main project LICENSE file.
