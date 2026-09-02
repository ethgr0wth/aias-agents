# AiAssist Secure Mobile Application - WORKPLAN

> Capacitor-based mobile shell for the AiAssist Secure AI platform

## Project Overview

This project creates a native iOS and Android mobile application that wraps the AiAssist Secure web platform (https://aiassist.net) using Capacitor. The app provides native mobile capabilities while leveraging the existing web application for the UI.

## Architecture

> **Note:** This is a **Remote Shell Architecture** - the app loads the external
> AiAssist.net website directly in a WebView. Native features like splash screen
> and status bar work via native configuration. For JavaScript-based native features
> (haptics, share, etc.), the remote site would need to include the Capacitor bridge.

```
┌─────────────────────────────────────────────────────────────┐
│                    AiAssist Secure Mobile                    │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   iOS App   │  │ Android App │  │   Web Preview       │  │
│  │  (Xcode)    │  │  (Android   │  │   (Development)     │  │
│  │             │  │   Studio)   │  │                     │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
│         │                │                     │             │
│         └────────────────┼─────────────────────┘             │
│                          │                                   │
│  ┌───────────────────────▼───────────────────────────────┐  │
│  │         Native Layer (via capacitor.config.ts)         │  │
│  │  • SplashScreen (native)  • StatusBar (native)         │  │
│  │  • Deep Links (native via URL schemes)                 │  │
│  │  • Push Notifications (native registration)            │  │
│  └───────────────────────┬───────────────────────────────┘  │
│                          │                                   │
│  ┌───────────────────────▼───────────────────────────────┐  │
│  │                  WebView Container                     │  │
│  │           Loads: https://aiassist.net                  │  │
│  │     (Remote site handles all UI and app logic)         │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   AiAssist Secure Platform                   │
│                   https://aiassist.net                       │
├─────────────────────────────────────────────────────────────┤
│  • Chat Completions API (OpenAI-compatible)                  │
│  • Workspaces & Conversations                                │
│  • Deployed Agents                                           │
│  • Knowledge Base (Training Contexts)                        │
│  • Shadow Mode (Draft Approval)                              │
│  • App Builder (Quests)                                      │
│  • WebSocket Real-time Chat                                  │
│  • Voice Actions                                             │
│  • CRM (Contacts, Leads)                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## MVP Features (Phase 1)

### Completed

- [x] Capacitor project structure for iOS and Android
- [x] WebView configuration pointing to AiAssist web app
- [x] Native splash screen configuration
- [x] Status bar styling (dark theme)
- [x] Basic app configuration (app ID, name, permissions)
- [x] Deep linking setup for workspaces and agents
- [x] Secure storage integration via Preferences plugin
- [x] Network status monitoring
- [x] Keyboard handling for mobile UI
- [x] Share service for content sharing
- [x] Express server for local development preview

### Pending

- [ ] Add iOS and Android platform directories (`npx cap add ios/android`)
- [ ] Configure app icons and splash screen images
- [ ] Test deep links on native platforms
- [ ] Configure push notification credentials (APNs/FCM)
- [ ] Build and test on physical devices

---

## Architecture Notes

### Remote Shell vs Embedded Shell

This project uses a **Remote Shell** architecture:

| Feature | How It Works |
|---------|--------------|
| Splash Screen | Native (configured in capacitor.config.ts) |
| Status Bar | Native (configured in capacitor.config.ts) |
| Deep Links | Native (via iOS URL schemes / Android App Links) |
| Push Notifications | Native registration, but requires backend integration |
| UI/App Logic | Handled by remote https://aiassist.net |

### For Full Native JavaScript Features

If you want JavaScript-based native features (haptics, share sheets, etc.) to work
from within the remote app, you have two options:

**Option A: Add Capacitor to AiAssist.net**
1. Install `@capacitor/core` and plugins on the remote site
2. Include the Capacitor bridge script
3. Call native APIs directly from the remote app

**Option B: Use Local Shell with Iframe**
1. Remove `server.url` from capacitor.config.ts
2. Use an iframe in www/index.html to load the remote app
3. Use postMessage for communication between shell and iframe

For this initial setup, Option A is recommended if you want rich native features.

---

## Phase 2 Features (Optional Enhancements)

### Push Notifications
- Draft approval notifications (Shadow Mode)
- New message alerts for workspaces
- Usage limit warnings
- Agent status updates

### Biometric Authentication
- Face ID / Touch ID for iOS
- Fingerprint / Face unlock for Android
- Secure session management

### Offline Mode
- Cache recent conversations
- Queue messages for sending when online
- Offline workspace browsing

### Native Enhancements
- Haptic feedback on key interactions
- Share sheet for AI responses
- App shortcuts for quick access
- Background sync for conversations

---

## Project Structure

```
aiassist-secure-mobile/
├── capacitor.config.ts      # Capacitor configuration
├── package.json             # Dependencies and scripts
├── .gitignore              # Git ignore rules
├── WORKPLAN.md             # This file
├── replit.md               # Project documentation
│
├── www/                    # Web assets (splash/loading screen)
│   ├── index.html          # Loading screen HTML
│   └── js/
│       └── app.js          # Native bridge JavaScript
│
├── src/
│   └── server.js           # Express dev server
│
├── resources/              # App icons and splash screens
│   ├── icon/               # App icons (various sizes)
│   └── splash/             # Splash screen images
│
├── ios/                    # iOS platform (after `cap add ios`)
│   └── App/
│       ├── App/
│       └── Podfile
│
└── android/                # Android platform (after `cap add android`)
    └── app/
        ├── build.gradle
        └── src/
```

---

## Configuration

### Capacitor Config (`capacitor.config.ts`)

| Setting | Value | Description |
|---------|-------|-------------|
| `appId` | `net.aiassist.secure` | Bundle/Package identifier |
| `appName` | `AiAssist Secure` | Display name |
| `webDir` | `www` | Web assets directory |
| `server.url` | `https://aiassist.net` | Remote web app URL |

### Deep Link Schemes

| Platform | Scheme | Example |
|----------|--------|---------|
| iOS | `aiassist://` | `aiassist://workspace/123` |
| Android | `aiassist://` | `aiassist://agent/456` |

### Supported Deep Link Paths

- `/workspace/{id}` - Open specific workspace
- `/agent/{id}` - Open deployed agent
- `/chat` - Open chat interface
- `/dashboard` - Open main dashboard

---

## Build Commands

### Development

```bash
# Start local preview server
npm run dev

# Preview runs on http://localhost:5000
```

### iOS Build

```bash
# Add iOS platform (first time only)
npm run cap:add:ios

# Sync changes and open Xcode
npm run build:ios

# In Xcode: Select target device → Build & Run
```

### Android Build

```bash
# Add Android platform (first time only)
npm run cap:add:android

# Sync changes and open Android Studio
npm run build:android

# In Android Studio: Select device → Run
```

### Sync Changes

```bash
# After web asset changes
npm run cap:sync

# Copy web assets only
npm run cap:copy
```

---

## API Integration

The mobile app accesses all AiAssist Secure APIs through the WebView. Key endpoints:

### Public API (`/v1`)
- `POST /v1/chat/completions` - AI chat completions
- `GET /v1/models` - List available models
- `GET /v1/usage` - Usage statistics
- `GET /v1/health` - Health check

### Private API (`/api`)
- Authentication (login, register, 2FA)
- Workspaces (CRUD, messages, drafts)
- Deployed Agents
- Knowledge Base (Training Contexts)
- Contacts & Leads (CRM)
- App Builder (Quests)
- Voice Actions

### WebSocket
- Real-time chat via Socket.IO
- Typing indicators
- Draft notifications

---

## Native Plugin Usage

### Secure Storage (Preferences)

```javascript
// Store API key securely
await SecureStorage.set('apiKey', 'aai_xxx');

// Retrieve stored value
const key = await SecureStorage.get('apiKey');

// Clear all storage
await SecureStorage.clear();
```

### Share Content

```javascript
// Share AI response
await ShareService.share(
  'AI Response',
  'Here is what the AI said...',
  'https://aiassist.net/chat'
);
```

### Deep Link Handling

Deep links are automatically handled by the app:
- `aiassist://workspace/123` → Opens workspace 123
- `aiassist://agent/456` → Opens agent 456

---

## Requirements

### Development
- Node.js 18+
- npm or yarn

### iOS Builds
- macOS with Xcode 15+
- CocoaPods installed
- Apple Developer account

### Android Builds
- Android Studio (latest)
- Android SDK 33+
- JDK 17+

---

## Environment Setup

### iOS Certificates

1. Create App ID in Apple Developer Portal
2. Configure push notification capability
3. Generate provisioning profiles
4. Configure in Xcode

### Android Signing

1. Generate keystore: `keytool -genkey -v -keystore aiassist.keystore`
2. Configure in `android/app/build.gradle`
3. Set up Firebase for push notifications

### Push Notifications

1. **iOS (APNs)**
   - Generate APNs key in Apple Developer Portal
   - Configure in app backend

2. **Android (FCM)**
   - Create Firebase project
   - Download `google-services.json`
   - Place in `android/app/`

---

## Testing Checklist

### Pre-Release Testing

- [ ] App launches and shows splash screen
- [ ] Web app loads correctly in WebView
- [ ] Login/logout flow works
- [ ] Chat functionality works
- [ ] Deep links open correct screens
- [ ] Share functionality works
- [ ] Network offline handling
- [ ] Push notifications received
- [ ] Keyboard appears/dismisses correctly
- [ ] Status bar styled correctly
- [ ] Safe area insets respected

### Device Testing

- [ ] iPhone (various sizes)
- [ ] iPad
- [ ] Android phones (various sizes)
- [ ] Android tablets

---

## Deployment

### iOS App Store

1. Archive in Xcode
2. Upload to App Store Connect
3. Complete app listing
4. Submit for review

### Google Play Store

1. Generate signed APK/AAB
2. Upload to Google Play Console
3. Complete store listing
4. Submit for review

---

## Troubleshooting

### WebView Not Loading

- Check `server.url` in capacitor config
- Verify `allowNavigation` includes the domain
- Check network connectivity

### Deep Links Not Working

- Verify URL scheme in platform configs
- Check Associated Domains (iOS)
- Verify App Links (Android)

### Push Notifications Not Received

- Verify APNs/FCM credentials
- Check notification permissions
- Verify backend integration

---

## Resources

- [Capacitor Documentation](https://capacitorjs.com/docs)
- [AiAssist Secure API Docs](https://aiassist.net/docs)
- [iOS Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/)
- [Material Design Guidelines](https://material.io/design)

---

## Contact

For questions about the AiAssist Secure API:
- Documentation: https://aiassist.net/docs
- Support: Through the AiAssist Secure dashboard
