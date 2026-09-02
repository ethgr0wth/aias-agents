---
title: Mobile App Config
description: Capacitor-based mobile application wrapper for Quests.
category: Mobile
icon: Smartphone
order: 4
---

# Quests Mobile App - Capacitor WebView Wrapper

## Overview

The Quests mobile app is designed as a lightweight Capacitor-based webview wrapper that provides native iOS and Android access to the AiAssist Secure Quests Builder platform. This approach maximizes code reuse while providing a native app experience.

## Architecture

### Web-First Approach
- The core Quests Builder UI is built with React and designed mobile-responsive
- The mobile app wraps the web application in a native container
- All business logic, AI chat, and file operations run on the server
- The mobile app is essentially a "protocol scope client" for AiAS

### Technology Stack
- **Capacitor 5.x** - Native runtime for iOS and Android
- **React** - Same codebase as web application
- **Native Features** - Camera, file system access, push notifications

## Implementation Plan

### Phase 1: Basic WebView Wrapper
```bash
# Initialize Capacitor in the client directory
npx cap init "AiAssist Quests" "com.aiassist.quests"
npx cap add ios
npx cap add android
```

**Capacitor Config** (`capacitor.config.ts`):
```typescript
import { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.aiassist.quests',
  appName: 'AiAssist Quests',
  webDir: 'dist',
  server: {
    url: 'https://app.aiassist.net/quests',
    cleartext: false
  },
  plugins: {
    SplashScreen: {
      launchAutoHide: false,
      showSpinner: false
    },
    Keyboard: {
      resize: 'native'
    }
  }
};

export default config;
```

### Phase 2: Native Plugin Integration

**Required Plugins:**
- `@capacitor/keyboard` - Handle keyboard events for code editing
- `@capacitor/status-bar` - Native status bar control
- `@capacitor/splash-screen` - App launch experience
- `@capacitor/push-notifications` - Build status notifications (optional)
- `@capacitor/filesystem` - Local file caching (optional)

### Phase 3: Offline Support (Future)

**Local SQLite Cache:**
- Cache environment metadata for offline viewing
- Queue file changes for sync when online
- Store chat history locally

## UI Considerations

### Responsive Design
The Quests workspace uses `ResizablePanelGroup` which adapts to screen size:
- **Desktop**: Three-pane layout (file tree, editor, chat)
- **Tablet**: Collapsible file tree, two-pane layout
- **Mobile**: Single-pane with tab navigation between views

### Mobile-Specific Adjustments
1. **Touch-friendly file tree** - Larger touch targets for folder/file selection
2. **Keyboard handling** - Proper handling of soft keyboard for code editing
3. **Swipe gestures** - Swipe between editor and chat panels
4. **Pull-to-refresh** - Refresh file tree and chat history

## Authentication

The mobile app uses the same session-based authentication as the web:
1. Initial login via webview OAuth/credential form
2. Session cookie stored securely in native keychain
3. Auto-refresh on app resume

## Deep Linking

URL scheme for opening specific environments:
```
aiassist://quests/env/{environment_id}
aiassist://quests/env/{environment_id}/file/{path}
```

## Build & Deploy

### iOS
```bash
npx cap sync ios
npx cap open ios
# Build in Xcode, submit to App Store Connect
```

### Android
```bash
npx cap sync android
npx cap open android
# Build in Android Studio, submit to Google Play Console
```

## Scope of Work

### MVP Features (WebView Only)
- [x] Capacitor project initialization
- [ ] Basic webview configuration
- [ ] Splash screen and app icon
- [ ] iOS and Android builds
- [ ] TestFlight/Internal testing deployment

### Enhanced Features (Future)
- [ ] Push notifications for build completion
- [ ] Native file picker for uploads
- [ ] Offline environment metadata caching
- [ ] Biometric authentication

## Security Considerations

1. **Certificate Pinning** - Optional SSL pinning for production
2. **Secure Storage** - Use native keychain for session tokens
3. **No Sensitive Data Caching** - API keys never stored locally
4. **WebView Hardening** - Disable JavaScript execution from untrusted sources

## Estimated Timeline

| Phase | Duration | Description |
|-------|----------|-------------|
| Setup | 1 day | Capacitor init, basic config |
| iOS Build | 1 day | Xcode setup, TestFlight deployment |
| Android Build | 1 day | Android Studio setup, internal testing |
| Polish | 2 days | Icons, splash screen, edge cases |
| **Total** | **5 days** | MVP ready for internal testing |

## Notes

- The mobile app is intentionally thin - a webview wrapper
- All heavy lifting (AI, file ops, builds) happens server-side
- This approach allows rapid iteration on the web UI without app store updates
- Consider using Capacitor Live Update for OTA web bundle updates
