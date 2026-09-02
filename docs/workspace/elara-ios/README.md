# Elara Wallet — iOS Release Repo

Premium cryptocurrency wallet for Bitcoin and Interchained (ITC).
This repository is the iOS build source used with Codemagic CI/CD.

## Stack
- Svelte 4 + TypeScript + Vite 5
- Capacitor 7 (iOS target)
- Custom ElectrumX TCP plugin with native Swift implementation

## Local iOS development

```bash
npm install
npx vite build
npx cap sync ios
npx cap open ios
```

## Codemagic CI/CD

Builds and uploads to TestFlight automatically on every push.
See `codemagic.yaml` for workflow configuration.

Required secrets (set in Codemagic dashboard):
- `APP_STORE_CONNECT_KEY_IDENTIFIER`
- `APP_STORE_CONNECT_ISSUER_ID`
- `APP_STORE_CONNECT_PRIVATE_KEY`
- `CERTIFICATE_PRIVATE_KEY`
- `VITE_REVENUECAT_IOS_KEY`

## Bundle ID
`org.interchained.elara`
