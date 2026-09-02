# AiAssist SDK Publishing Guide

This document provides instructions for building and publishing all AiAssist SDK packages.

## Prerequisites

- Node.js 18+ 
- Python 3.9+
- npm account (for npm packages)
- PyPI account (for Python package)
- Access to CDN hosting (for vanilla widget)

## Automated Release

Use the release script to publish all packages at once:

```bash
# Dry run (build only, no publish)
./scripts/release-sdk.sh 1.0.0 --dry-run

# Publish all packages
./scripts/release-sdk.sh 1.0.0
```

The script handles version bumping, building, and publishing for all packages.

---

## Package Overview

| Package | Registry | Install Command |
|---------|----------|-----------------|
| `@aiassist-secure/core` | npm | `npm install @aiassist-secure/core` |
| `@aiassist-secure/react` | npm | `npm install @aiassist-secure/react` |
| `@aiassist-secure/vanilla` | npm + CDN | `npm install @aiassist-secure/vanilla` or CDN |
| `aiassist-secure` | PyPI | `pip install aiassist-secure` (v1 client only) |

---

## 1. TypeScript Core SDK (@aiassist-secure/core)

Framework-agnostic client that works in Node.js and browsers.

### Build

```bash
cd packages/typescript

npm install
npm run build
```

This creates:
- `dist/index.js` (CommonJS)
- `dist/index.mjs` (ESM)
- `dist/index.d.ts` (TypeScript definitions)

### Publish

```bash
npm login
npm pack --dry-run
npm publish --access public
```

---

## 2. React Package (@aiassist-secure/react)

### Build

```bash
cd packages/react

# Install dependencies
npm install

# Build for production
npm run build
```

This creates:
- `dist/index.js` (CommonJS)
- `dist/index.mjs` (ESM)
- `dist/index.d.ts` (TypeScript definitions)

### Publish to npm

```bash
# Login to npm (first time only)
npm login

# Dry run to verify package contents
npm pack --dry-run

# Publish
npm publish --access public
```

### Version Bump

```bash
# Patch version (1.0.0 -> 1.0.1)
npm version patch

# Minor version (1.0.0 -> 1.1.0)
npm version minor

# Major version (1.0.0 -> 2.0.0)
npm version major
```

---

## 3. Vanilla Widget (@aiassist-secure/vanilla)

### Build

```bash
cd packages/vanilla

# Build for distribution
node build.js
```

This creates:
- `dist/widget.js` (Full version with banner)
- `dist/widget.min.js` (Minified for production)
- `dist/widget.esm.js` (ES Module version)
- `dist/widget.d.ts` (TypeScript definitions)

### Publish to npm

```bash
npm login
npm pack --dry-run
npm publish --access public
```

### CDN Deployment

After building, deploy to your CDN:

```bash
# Upload to CDN (example using AWS S3)
aws s3 cp dist/widget.min.js s3://cdn.aiassist.net/widget.js --acl public-read
aws s3 cp dist/widget.min.js s3://cdn.aiassist.net/v1.0.0/widget.js --acl public-read

# Or using rsync to VPS
rsync -avz dist/ user@cdn.aiassist.net:/var/www/cdn/
```

#### CDN File Structure

```
cdn.aiassist.net/
├── widget.js          # Latest version (always updated)
├── widget.min.js      # Latest minified
├── v1.0.0/
│   ├── widget.js
│   └── widget.min.js
├── v1.0.1/
│   └── ...
```

#### CDN Headers

Set these headers on your CDN:

```
Content-Type: application/javascript
Cache-Control: public, max-age=31536000  # For versioned files
Cache-Control: public, max-age=3600      # For latest version
Access-Control-Allow-Origin: *
```

### Usage from CDN

```html
<!-- Latest version (auto-updates) -->
<script src="https://cdn.aiassist.net/widget.js"></script>

<!-- Specific version (recommended for production) -->
<script src="https://cdn.aiassist.net/v1.0.0/widget.js"></script>

<script>
  AiAssist.init({
    apiKey: 'your-api-key',
    position: 'bottom-right'
  });
</script>
```

---

## 4. Python Package (aiassist-secure)

**v1 - Client Only** (public distribution)

Located at: `packages/python-client/`

```bash
pip install aiassist-secure
```

Only dependency: `httpx` - No Redis, no server components, no proprietary code.

### Build

```bash
cd packages/python-client

# Install build tools
pip install build twine

# Build package
python -m build
```

This creates:
- `dist/aiassist_secure-x.x.x-py3-none-any.whl` (Wheel)
- `dist/aiassist_secure-x.x.x.tar.gz` (Source distribution)

### Publish to PyPI

```bash
# Upload to TestPyPI first (recommended)
twine upload --repository testpypi dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ aiassist-secure

# Upload to production PyPI
twine upload dist/*
```

### Version Bump

Edit `pyproject.toml` to increment the version:
```toml
[project]
version = "0.1.1"  # Increment from current version
```

Use semantic versioning:
- **Patch** (0.1.0 → 0.1.1): Bug fixes, no API changes
- **Minor** (0.1.0 → 0.2.0): New features, backwards compatible
- **Major** (0.1.0 → 1.0.0): Breaking changes

---

## Automated Release Script

Create a release script for convenience:

```bash
#!/bin/bash
# scripts/release.sh

set -e

VERSION=$1

if [ -z "$VERSION" ]; then
  echo "Usage: ./scripts/release.sh <version>"
  exit 1
fi

echo "Releasing version $VERSION..."

# React package
echo "Building React package..."
cd packages/react
npm version $VERSION --no-git-tag-version
npm run build
npm publish --access public
cd ../..

# Vanilla package
echo "Building Vanilla package..."
cd packages/vanilla
npm version $VERSION --no-git-tag-version
node build.js
npm publish --access public

# Deploy to CDN
echo "Deploying to CDN..."
scp -r dist/* user@cdn.aiassist.net:/var/www/cdn.aiassist.net/
ssh user@cdn.aiassist.net "mkdir -p /var/www/cdn.aiassist.net/v$VERSION && cp /var/www/cdn.aiassist.net/widget.* /var/www/cdn.aiassist.net/v$VERSION/"
cd ../..

# Python package (update version manually in pyproject.toml)
echo "Building Python package..."
cd packages/python
# Update version in pyproject.toml
sed -i "s/version = \".*\"/version = \"$VERSION\"/" pyproject.toml
python -m build
twine upload dist/*
cd ../..

# Git tag
git add .
git commit -m "Release v$VERSION"
git tag -a "v$VERSION" -m "Release v$VERSION"
git push origin main --tags

echo "Released v$VERSION successfully!"
```

---

## Pre-publish Checklist

Before publishing any package:

- [ ] Update version number
- [ ] Update CHANGELOG.md
- [ ] Run tests (if available)
- [ ] Build successfully
- [ ] Verify package contents with `npm pack --dry-run` or `python -m build`
- [ ] Test installation locally
- [ ] Update documentation
- [ ] Tag release in git

---

## NPM Package Scopes

All npm packages use the `@aiassist-secure` scope. To publish:

1. Create organization on npmjs.com: `aiassist-secure`
2. Add yourself as maintainer
3. Publish with `--access public` flag

---

## Troubleshooting

### npm ERR! 403 Forbidden

- Ensure you're logged in: `npm whoami`
- Verify package name isn't taken
- Use `--access public` for scoped packages

### PyPI Upload Failed

- Check credentials in `~/.pypirc`
- Verify package name isn't taken on PyPI
- Ensure version number is unique

### CDN Not Updating

- Clear CDN cache: `aws cloudfront create-invalidation --distribution-id XXX --paths "/*"`
- Check file permissions
- Verify Content-Type headers

---

## Support

- Documentation: https://aiassist.net/docs
- Developer Docs: https://aiassist.net/developer-docs
- Email: support@aiassist.net
