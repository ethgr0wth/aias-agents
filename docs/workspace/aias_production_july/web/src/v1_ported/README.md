# v1 Ported Feature Layer

This directory is a **mechanical, behavior-preserving port** of the existing
`client/src` feature implementation into the Portal `web/` application.

## Contract

- `client/` remains untouched and can continue to be built/served as static v1.
- Portal `web/` is the v1.1 product shell.
- Core collaboration (rooms/messages/roster/inbox) is native v1.1 under
  `web/src/v1_1` and `/api/v1.1`.
- Specialist capabilities are lazy-mounted from this directory so v1.1 retains
  every feature v1 shipped while those large pages are incrementally extracted.
- Existing backend endpoints are reused. No business logic is duplicated.

## Runtime integration

- `FeatureHost.tsx`: lazy `import.meta.glob` registry; each feature gets its own
  chunk and is available at `/app/v1/:feature`.
- `LegacyMount.tsx`: supplies v1 ThemeProvider, TooltipProvider and Toaster.
- `compat/wouter.tsx`: maps legacy Wouter calls onto Portal navigation.
- `lib/queryClient.ts`: routes v1 API calls through the shared Portal API base,
  session header and single TanStack QueryClient.
- `@v1/*`: Vite/TypeScript alias for this tree.

## Source directories copied

`pages`, `components`, `hooks`, `lib`, `themes`, `data`, `assets`, plus
`shared/schema.ts` and `client/public` assets.

The copied source is marked `@ts-nocheck` during the parity migration because
v1 itself contains pre-existing type drift. Portal adapters and native v1.1
code remain strict. This preserves working behavior without weakening the new
core architecture.

## Sync policy

This is now a ported v1 snapshot. New v1.1 work belongs in `web/src/v1_1` or
Portal-native features, not in `client/`. If a critical v1 bug must be fixed in
both clients before cutover, apply it to both trees explicitly and record it in
this file.
