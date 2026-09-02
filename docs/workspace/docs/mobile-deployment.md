# AiAS Mobile Deployment — Capacitor Polish

  ## What & Why
  Ship AiAssist Secure to the Google Play Store using the existing Capacitor shell (`aias_mobile_package/`). The app wraps the existing React web UI that already connects to the production cloud backend — no backend changes needed. The focus is making three core screens (Home, Login/Register, Dashboard) feel native on mobile rather than "website in a wrapper."

  This is the distribution play — get AiAS into the hands of solo founders via the app store, with the full platform behind it.

  ## Done looks like
  - The Capacitor app loads `aiassist.net` with a polished mobile experience
  - **Home page**: Lightweight mobile variant — no heavy 3D backgrounds in WebView, clean hero with clear CTA to login/register, fast load
  - **Login/Register**: Native-feeling auth screens with proper touch targets, keyboard handling, no 3D entrance scene on mobile (performance), clean form layout
  - **Dashboard**: Mobile-first layout with bottom tab navigation, collapsible sections, card-based UI, proper spacing and touch targets, swipe-friendly tab navigation between dashboard sections (Settings, API Keys, Usage, Agents, etc.)
  - Bottom navigation bar with key tabs (Dashboard, Workspaces, Agents, Settings)
  - Capacitor native features active: splash screen with branded assets, status bar styling, haptic feedback on key actions, proper safe area insets
  - Loading/error states feel native (shimmer skeletons, not bare spinners)
  - The app is buildable via `npx cap sync && npx cap open android`

  ## Out of scope
  - Playground / Keystone / Artifact Factory mobile polish (follow-up phases)
  - Push notifications and biometric auth (Phase 2)
  - iOS build (Android first)
  - Offline SQLite caching (Phase 2)
  - App store listing, screenshots, store assets (separate task)
  - New backend endpoints or API changes

  ## Tasks
  1. **Mobile detection utility** — Add a shared utility that detects Capacitor WebView context vs regular browser, so components can conditionally render lighter mobile variants.

  2. **Bottom navigation shell** — Add a persistent bottom tab bar for mobile viewports (Dashboard, Workspaces, Agents, Settings) with proper safe area handling and active state indicators. This replaces the current desktop sidebar/header nav on mobile.

  3. **Home page mobile variant** — Conditionally skip 3D backgrounds (MalachiBackground, AthenaBackground, etc.) and heavy animations in Capacitor/mobile context. Render a clean, fast-loading hero section with login/register CTAs. Keep the core messaging but strip the performance-heavy elements.

  4. **Login/Register mobile polish** — Remove PremiumEntranceScene lazy load on mobile. Ensure form inputs have proper touch targets (min 44px), auto-focus behavior, and keyboard-aware scroll. Clean spacing for mobile viewport. Register flow should work smoothly without modals overlapping on small screens.

  5. **Dashboard mobile redesign** — Refactor the 2700-line Dashboard into a mobile-friendly layout: collapsible card sections, horizontal scroll for sub-navigation tabs, proper spacing/padding for touch, swipe-friendly interaction. License activation, API keys, usage stats, and provider settings should all be accessible but not cramped.

  6. **Capacitor shell update** — Update `aias_mobile_package/` splash screen and loading page with proper branded assets. Ensure `capacitor.config.ts` has correct settings for Android build. Verify the Capacitor bridge script loads correctly when serving from the remote URL.

  7. **Integration test** — Verify the full flow: app launch → splash → home → login → dashboard → navigation between tabs. Ensure WebSocket chat works, API calls succeed, and no CORS/mixed-content issues in the WebView.

  ## Relevant files
  - `aias_mobile_package/capacitor.config.ts`
  - `aias_mobile_package/www/index.html`
  - `aias_mobile_package/www/js/app.js`
  - `aias_mobile_package/package.json`
  - `aias_production_clone/client/src/App.tsx`
  - `aias_production_clone/client/src/pages/Home.tsx`
  - `aias_production_clone/client/src/pages/Register.tsx`
  - `aias_production_clone/client/src/pages/admin/Login.tsx`
  - `aias_production_clone/client/src/pages/Dashboard.tsx`
  - `aias_production_clone/client/src/components/Shimmer.tsx`
  - `aias_production_clone/client/src/themes/ThemeProvider.tsx`
  - `aias_production_clone/client/src/themes/backgrounds/MalachiBackground.tsx`
  