# Puppeteer/Chrome Setup for VPS Deployment

This guide covers installing the required system dependencies for running Puppeteer (headless Chrome) on your VPS.

## Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install -y \
    libnspr4 \
    libnss3 \
    libx11-6 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxtst6 \
    libcups2 \
    libdbus-1-3 \
    libexpat1 \
    libdrm2 \
    libxkbcommon0 \
    libgbm1 \
    libasound2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libatspi2.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    libglib2.0-0 \
    libgtk-3-0 \
    libpango-1.0-0 \
    fonts-liberation \
    xdg-utils \
    wget
```

## CentOS/RHEL/Amazon Linux

```bash
sudo yum install -y \
    nspr \
    nss \
    libX11 \
    libXcomposite \
    libXcursor \
    libXdamage \
    libXext \
    libXi \
    libXrandr \
    libXrender \
    libXtst \
    cups-libs \
    dbus-libs \
    expat \
    libdrm \
    libxkbcommon \
    mesa-libgbm \
    alsa-lib \
    atk \
    at-spi2-atk \
    at-spi2-core \
    cairo \
    gdk-pixbuf2 \
    glib2 \
    gtk3 \
    pango \
    liberation-fonts \
    wget
```

## Alpine Linux

```bash
apk add --no-cache \
    chromium \
    nss \
    freetype \
    harfbuzz \
    ca-certificates \
    ttf-freefont
```

For Alpine, set the environment variable to use the system Chromium:
```bash
export PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true
export PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser
```

## After Installing Dependencies

Install Puppeteer's Chrome:
```bash
npx puppeteer browsers install chrome
```

## Troubleshooting

### Missing Library Errors

If you see errors like `error while loading shared libraries: libXXX.so`, install the missing package:

| Missing Library | Ubuntu Package | CentOS Package |
|----------------|----------------|----------------|
| libnspr4.so | libnspr4 | nspr |
| libnss3.so | libnss3 | nss |
| libX11.so | libx11-6 | libX11 |
| libgbm.so | libgbm1 | mesa-libgbm |

### Sandbox Errors

If you get sandbox-related errors, Puppeteer is launched with these flags:
```javascript
puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
});
```

### Docker

For Docker deployments, use a base image with Chrome pre-installed or add the dependencies to your Dockerfile:

```dockerfile
FROM node:20-slim

RUN apt-get update && apt-get install -y \
    libnspr4 libnss3 libx11-6 libxcomposite1 libxcursor1 \
    libxdamage1 libxext6 libxi6 libxrandr2 libxrender1 \
    libxtst6 libcups2 libdbus-1-3 libexpat1 libdrm2 \
    libxkbcommon0 libgbm1 libasound2 libatk1.0-0 \
    libatk-bridge2.0-0 libatspi2.0-0 libcairo2 \
    libgdk-pixbuf2.0-0 libglib2.0-0 libgtk-3-0 \
    libpango-1.0-0 fonts-liberation wget \
    && rm -rf /var/lib/apt/lists/*

RUN npx puppeteer browsers install chrome
```
