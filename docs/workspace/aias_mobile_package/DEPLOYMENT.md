# AiAssist Secure Mobile - Deployment Guide

> Step-by-step instructions for deploying to iOS App Store and Google Play Store

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [iOS Deployment](#ios-deployment)
3. [Android Deployment](#android-deployment)
4. [App Store Assets](#app-store-assets)
5. [Version Management](#version-management)
6. [Post-Release](#post-release)

---

## Prerequisites

### Development Machine

| Platform | Requirements |
|----------|--------------|
| iOS | macOS 13+, Xcode 15+, Apple Developer Account ($99/year) |
| Android | Any OS, Android Studio, Google Play Developer Account ($25 one-time) |

### Project Setup

```bash
# Install dependencies
npm install

# Add platforms (first time only)
npm run cap:add:ios
npm run cap:add:android

# Sync web assets
npm run cap:sync
```

---

## iOS Deployment

### Step 1: Apple Developer Setup

1. **Create App ID**
   - Go to [Apple Developer Portal](https://developer.apple.com/account)
   - Navigate to Certificates, Identifiers & Profiles → Identifiers
   - Click (+) to create new App ID
   - Select "App IDs" and continue
   - Enter:
     - Description: `AiAssist Secure`
     - Bundle ID: `net.aiassist.secure` (Explicit)
   - Enable capabilities:
     - [x] Push Notifications
     - [x] Associated Domains (for deep links)
   - Click Register

2. **Create Provisioning Profiles**
   - Development Profile (for testing)
   - Distribution Profile (for App Store)

3. **Configure Push Notifications**
   - Create APNs Key in Apple Developer Portal
   - Download and save securely
   - Provide to backend team for server integration

### Step 2: Xcode Configuration

```bash
# Open project in Xcode
npm run build:ios
```

In Xcode:

1. **Select Target** → AiAssist Secure (under TARGETS)

2. **General Tab**
   - Display Name: `AiAssist Secure`
   - Bundle Identifier: `net.aiassist.secure`
   - Version: `1.0.0`
   - Build: `1`

3. **Signing & Capabilities Tab**
   - Team: Select your Apple Developer Team
   - Signing Certificate: Distribution
   - Provisioning Profile: Select App Store profile
   - Add Capabilities:
     - Push Notifications
     - Associated Domains → `applinks:aiassist.net`

4. **Info Tab (Info.plist)**
   
   Add URL Scheme for deep links:
   ```xml
   <key>CFBundleURLTypes</key>
   <array>
     <dict>
       <key>CFBundleURLSchemes</key>
       <array>
         <string>aiassist</string>
       </array>
       <key>CFBundleURLName</key>
       <string>net.aiassist.secure</string>
     </dict>
   </array>
   ```

   Add Associated Domains entitlement for Universal Links:
   ```xml
   <key>com.apple.developer.associated-domains</key>
   <array>
     <string>applinks:aiassist.net</string>
   </array>
   ```

### Step 3: App Icons

Place app icons in `ios/App/App/Assets.xcassets/AppIcon.appiconset/`:

| Size | Filename | Usage |
|------|----------|-------|
| 20x20 | icon-20.png | iPad Notifications |
| 29x29 | icon-29.png | Settings |
| 40x40 | icon-40.png | Spotlight |
| 60x60 | icon-60.png | iPhone App |
| 76x76 | icon-76.png | iPad App |
| 83.5x83.5 | icon-83.5.png | iPad Pro |
| 1024x1024 | icon-1024.png | App Store |

### Step 4: Build Archive

1. Select "Any iOS Device" as build target
2. Menu: Product → Archive
3. Wait for build to complete
4. Organizer window opens automatically

### Step 5: Upload to App Store Connect

1. In Organizer, select the archive
2. Click "Distribute App"
3. Select "App Store Connect" → Next
4. Select "Upload" → Next
5. Select signing options → Next
6. Review and click "Upload"

### Step 6: App Store Connect Configuration

Go to [App Store Connect](https://appstoreconnect.apple.com):

1. **Create New App**
   - Platform: iOS
   - Name: AiAssist Secure
   - Primary Language: English (US)
   - Bundle ID: net.aiassist.secure
   - SKU: aiassist-secure-ios

2. **App Information**
   - Category: Productivity
   - Content Rights: Does not contain third-party content
   - Age Rating: Complete questionnaire

3. **Prepare for Submission**
   - Add screenshots (see [App Store Assets](#app-store-assets))
   - Write description and keywords
   - Set pricing (Free)
   - Add privacy policy URL
   - Select build version

4. **Submit for Review**
   - Click "Submit for Review"
   - Review time: 24-48 hours typically

---

## Android Deployment

### Step 1: Google Play Console Setup

1. **Create Developer Account**
   - Go to [Google Play Console](https://play.google.com/console)
   - Pay $25 registration fee
   - Complete account details

2. **Create App**
   - Click "Create app"
   - Enter app details:
     - App name: AiAssist Secure
     - Default language: English (US)
     - App type: App
     - Category: Productivity
     - Free or paid: Free

### Step 2: Generate Signing Key

```bash
# Create keystore (keep this file secure!)
keytool -genkey -v \
  -keystore aiassist-release.keystore \
  -alias aiassist \
  -keyalg RSA \
  -keysize 2048 \
  -validity 10000

# You'll be prompted for:
# - Keystore password
# - Key password  
# - Name, Organization, Location details
```

**IMPORTANT:** Back up `aiassist-release.keystore` securely. If lost, you cannot update the app.

### Step 3: Configure Signing in Gradle

Edit `android/app/build.gradle`:

```gradle
android {
    ...
    
    signingConfigs {
        release {
            storeFile file('aiassist-release.keystore')
            storePassword System.getenv("KEYSTORE_PASSWORD") ?: 'your_keystore_password'
            keyAlias 'aiassist'
            keyPassword System.getenv("KEY_PASSWORD") ?: 'your_key_password'
        }
    }
    
    buildTypes {
        release {
            signingConfig signingConfigs.release
            minifyEnabled true
            proguardFiles getDefaultProguardFile('proguard-android.txt'), 'proguard-rules.pro'
        }
    }
}
```

### Step 4: Configure Deep Links

Edit `android/app/src/main/AndroidManifest.xml`:

```xml
<activity
    android:name=".MainActivity"
    android:exported="true">
    
    <!-- Deep Link Intent Filter -->
    <intent-filter>
        <action android:name="android.intent.action.VIEW" />
        <category android:name="android.intent.category.DEFAULT" />
        <category android:name="android.intent.category.BROWSABLE" />
        <data android:scheme="aiassist" />
    </intent-filter>
    
    <!-- App Links (HTTPS) -->
    <intent-filter android:autoVerify="true">
        <action android:name="android.intent.action.VIEW" />
        <category android:name="android.intent.category.DEFAULT" />
        <category android:name="android.intent.category.BROWSABLE" />
        <data android:scheme="https" android:host="aiassist.net" />
    </intent-filter>
    
</activity>
```

### Step 5: Build Release APK/AAB

```bash
# Open in Android Studio
npm run build:android
```

In Android Studio:

1. Menu: Build → Generate Signed Bundle / APK
2. Select "Android App Bundle" (recommended) or APK
3. Select keystore and enter passwords
4. Select "release" build variant
5. Click "Create"

Output location: `android/app/release/app-release.aab`

### Step 6: Upload to Google Play

1. **Go to Production Track**
   - Open your app in Google Play Console
   - Navigate to Release → Production

2. **Create New Release**
   - Click "Create new release"
   - Upload the `.aab` file
   - Add release notes

3. **Complete Store Listing**
   - Short description (80 chars)
   - Full description (4000 chars)
   - Screenshots (see [App Store Assets](#app-store-assets))
   - Feature graphic (1024x500)
   - App icon (512x512)

4. **Content Rating**
   - Complete the questionnaire
   - Get rating certificate

5. **App Content**
   - Privacy Policy URL
   - Ads declaration
   - Target audience

6. **Review and Rollout**
   - Review all sections
   - Click "Start rollout to Production"
   - Confirm release

---

## App Store Assets

### Screenshots Required

#### iOS Screenshots

| Device | Size | Required |
|--------|------|----------|
| iPhone 6.7" | 1290 x 2796 | Yes |
| iPhone 6.5" | 1284 x 2778 | Yes |
| iPhone 5.5" | 1242 x 2208 | Yes |
| iPad Pro 12.9" | 2048 x 2732 | If supporting iPad |

#### Android Screenshots

| Type | Size | Required |
|------|------|----------|
| Phone | 1080 x 1920 (min) | Yes (2-8 images) |
| 7" Tablet | 1200 x 1920 | Optional |
| 10" Tablet | 1800 x 2560 | Optional |

### Recommended Screenshots

1. **Login/Welcome Screen** - Show the secure login
2. **Chat Interface** - Demonstrate AI conversation
3. **Workspace View** - Show workspace management
4. **Agent Selection** - Display deployed agents
5. **Knowledge Base** - Show training contexts
6. **Settings/Profile** - User account features

### App Icon Specifications

| Platform | Size | Format |
|----------|------|--------|
| iOS App Store | 1024 x 1024 | PNG (no transparency) |
| Google Play | 512 x 512 | PNG (32-bit with alpha) |

### Feature Graphic (Android)

- Size: 1024 x 500 pixels
- Format: PNG or JPEG
- No text in upper/lower 15% (for overlays)

---

## Version Management

### Semantic Versioning

Format: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes, major new features
- **MINOR**: New features, backwards compatible
- **PATCH**: Bug fixes, minor improvements

### Updating Version

1. **Update package.json**
   ```json
   {
     "version": "1.1.0"
   }
   ```

2. **Sync to native projects**
   ```bash
   npm run cap:sync
   ```

3. **iOS**: Update in Xcode (General → Version)

4. **Android**: Update in `android/app/build.gradle`
   ```gradle
   versionCode 2
   versionName "1.1.0"
   ```

### Build Numbers

- iOS: Increment `Build` number for each upload
- Android: Increment `versionCode` for each upload

---

## Post-Release

### Monitoring

1. **Crash Reporting**
   - iOS: Use Xcode Organizer or integrate Crashlytics
   - Android: Use Play Console → Android Vitals or Crashlytics

2. **User Reviews**
   - Monitor and respond to reviews
   - Address common issues in updates

3. **Usage Analytics**
   - Use the AiAssist.net dashboard for API usage
   - Consider adding Firebase Analytics for app-specific metrics

### Updating the App

```bash
# 1. Make changes to web assets or config
# 2. Sync changes
npm run cap:sync

# 3. Build and upload new version
npm run build:ios    # Then archive in Xcode
npm run build:android  # Then build signed AAB
```

### Hotfixes

Since the app loads from https://aiassist.net, most fixes can be deployed server-side without an app update. Only update the app for:

- Native configuration changes
- New native capabilities
- Deep link scheme changes
- Push notification updates

---

## Checklist

### Pre-Submission

- [ ] App icons generated for all sizes
- [ ] Screenshots captured for all device sizes
- [ ] Privacy policy URL live and accessible
- [ ] App description written
- [ ] Keywords selected (iOS)
- [ ] Category selected
- [ ] Content rating completed
- [ ] Test on physical devices
- [ ] Deep links tested
- [ ] Push notifications tested

### iOS Specific

- [ ] Apple Developer account active
- [ ] App ID created
- [ ] Provisioning profiles generated
- [ ] APNs key created
- [ ] Archive built successfully
- [ ] Uploaded to App Store Connect

### Android Specific

- [ ] Google Play Developer account active
- [ ] Keystore created and backed up
- [ ] Signing configured in Gradle
- [ ] AAB generated and signed
- [ ] Uploaded to Google Play Console
- [ ] Content rating obtained

---

## Support

For deployment issues:

- **Capacitor**: [capacitorjs.com/docs](https://capacitorjs.com/docs)
- **iOS**: [developer.apple.com](https://developer.apple.com)
- **Android**: [developer.android.com](https://developer.android.com)
- **AiAssist API**: [aiassist.net/docs](https://aiassist.net/docs)
