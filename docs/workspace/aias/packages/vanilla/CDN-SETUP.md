# CDN Setup for AiAssist Vanilla Widget

This guide helps you set up CDN hosting for the AiAssist vanilla widget on your VPS.

## Prerequisites

- VPS with nginx or similar web server
- SSL certificate (Let's Encrypt recommended)
- Domain: `cdn.aiassist.net` (or your preferred subdomain)

## Directory Structure

```
/var/www/cdn.aiassist.net/
├── index.html              # CDN info page (optional)
├── widget.js               # Latest full version
├── widget.min.js           # Latest minified (recommended for production)
├── widget.esm.js           # Latest ESM version
├── widget.d.ts             # TypeScript definitions
├── v1.0.0/
│   ├── widget.js
│   ├── widget.min.js
│   ├── widget.esm.js
│   └── widget.d.ts
├── v1.0.1/
│   └── ...
└── v1.1.0/
    └── ...
```

## Nginx Configuration

Create `/etc/nginx/sites-available/cdn.aiassist.net`:

```nginx
server {
    listen 80;
    server_name cdn.aiassist.net;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name cdn.aiassist.net;

    # SSL certificates (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/cdn.aiassist.net/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/cdn.aiassist.net/privkey.pem;

    root /var/www/cdn.aiassist.net;
    index index.html;

    # CORS headers for widget
    add_header Access-Control-Allow-Origin "*" always;
    add_header Access-Control-Allow-Methods "GET, OPTIONS" always;
    add_header Access-Control-Allow-Headers "Origin, X-Requested-With, Content-Type, Accept" always;

    # Security headers
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # JavaScript files
    location ~* \.js$ {
        add_header Content-Type "application/javascript; charset=utf-8";
        add_header Access-Control-Allow-Origin "*";
        
        # Cache versioned files for 1 year
        if ($uri ~* "^/v\d+\.\d+\.\d+/") {
            add_header Cache-Control "public, max-age=31536000, immutable";
        }
        
        # Cache latest files for 1 hour
        if ($uri !~* "^/v\d+\.\d+\.\d+/") {
            add_header Cache-Control "public, max-age=3600";
        }
    }

    # Gzip compression
    gzip on;
    gzip_types application/javascript text/javascript;
    gzip_min_length 1000;

    location / {
        try_files $uri $uri/ =404;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/cdn.aiassist.net /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## SSL with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d cdn.aiassist.net
```

## Deployment Script

Create `/home/deploy/deploy-widget.sh`:

```bash
#!/bin/bash
# Deploy AiAssist widget to CDN

set -e

VERSION=$1
SOURCE_DIR=$2

if [ -z "$VERSION" ] || [ -z "$SOURCE_DIR" ]; then
    echo "Usage: ./deploy-widget.sh <version> <source-dir>"
    echo "Example: ./deploy-widget.sh 1.0.0 /path/to/packages/vanilla/dist"
    exit 1
fi

CDN_ROOT="/var/www/cdn.aiassist.net"

# Create version directory
mkdir -p "$CDN_ROOT/v$VERSION"

# Copy versioned files (all artifacts)
cp "$SOURCE_DIR/widget.js" "$CDN_ROOT/v$VERSION/"
cp "$SOURCE_DIR/widget.min.js" "$CDN_ROOT/v$VERSION/"
cp "$SOURCE_DIR/widget.esm.js" "$CDN_ROOT/v$VERSION/"
cp "$SOURCE_DIR/widget.d.ts" "$CDN_ROOT/v$VERSION/"

# Update latest version (all artifacts)
cp "$SOURCE_DIR/widget.js" "$CDN_ROOT/"
cp "$SOURCE_DIR/widget.min.js" "$CDN_ROOT/"
cp "$SOURCE_DIR/widget.esm.js" "$CDN_ROOT/"
cp "$SOURCE_DIR/widget.d.ts" "$CDN_ROOT/"

# Set permissions
chown -R www-data:www-data "$CDN_ROOT"
chmod -R 755 "$CDN_ROOT"

echo "Deployed v$VERSION to CDN"
echo ""
echo "URLs:"
echo "  Latest:    https://cdn.aiassist.net/widget.js"
echo "  Versioned: https://cdn.aiassist.net/v$VERSION/widget.js"
```

## Remote Deployment

From your local machine after building:

```bash
# Build the widget
cd packages/vanilla
node build.js

# Deploy to VPS
scp -r dist/* user@cdn.aiassist.net:/var/www/cdn.aiassist.net/

# Or use rsync for incremental updates
rsync -avz --progress dist/ user@cdn.aiassist.net:/var/www/cdn.aiassist.net/
```

## CDN Landing Page (Optional)

Create `/var/www/cdn.aiassist.net/index.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>AiAssist CDN</title>
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background: #0a0a0b;
            color: #fff;
        }
        h1 { color: #00d4ff; }
        code {
            background: #1a1a1b;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 14px;
        }
        pre {
            background: #1a1a1b;
            padding: 20px;
            border-radius: 8px;
            overflow-x: auto;
        }
        a { color: #00d4ff; }
    </style>
</head>
<body>
    <h1>AiAssist Widget CDN</h1>
    <p>Drop-in AI chat for any website.</p>
    
    <h2>Quick Start</h2>
    <pre><code>&lt;script src="https://cdn.aiassist.net/widget.js"&gt;&lt;/script&gt;
&lt;script&gt;
  AiAssist.init({
    apiKey: 'your-api-key',
    position: 'bottom-right'
  });
&lt;/script&gt;</code></pre>
    
    <h2>Available Files</h2>
    <ul>
        <li><a href="/widget.js">widget.js</a> - Latest full version</li>
        <li><a href="/widget.min.js">widget.min.js</a> - Latest minified</li>
        <li><a href="/widget.esm.js">widget.esm.js</a> - ES Module version</li>
    </ul>
    
    <h2>Documentation</h2>
    <p><a href="https://aiassist.net/developer-docs">Developer Docs</a></p>
</body>
</html>
```

## Testing

After deployment, verify:

```bash
# Check file accessibility
curl -I https://cdn.aiassist.net/widget.js
curl -I https://cdn.aiassist.net/widget.d.ts

# Check CORS headers
curl -I -H "Origin: https://example.com" https://cdn.aiassist.net/widget.js

# Test in browser console
# Should load without CORS errors
const script = document.createElement('script');
script.src = 'https://cdn.aiassist.net/widget.js';
document.head.appendChild(script);
```

## TypeScript Support

TypeScript definitions are available at `https://cdn.aiassist.net/widget.d.ts`. 

For npm users, types are bundled automatically. For CDN users who want TypeScript:

```typescript
// Download and place in your project, or reference directly
// Option 1: Download widget.d.ts locally
// Option 2: Use npm package for types only: npm install @aiassist/vanilla
```

## Cache Strategy

**Versioned URLs (recommended for production):**
- URLs like `/v1.0.0/widget.js` are immutable
- Cached for 1 year with `immutable` directive
- Update by changing version in your script tag

**Latest URLs:**
- URLs like `/widget.js` point to newest version
- Cached for 1 hour (3600 seconds)
- May not update immediately due to edge caching

**Best Practice:** Use versioned URLs in production for reliability:
```html
<script src="https://cdn.aiassist.net/v1.0.0/widget.js"></script>
```

## Cache Invalidation

If you need to force refresh the latest URLs:

```bash
# After updating latest files, wait up to 1 hour for cache expiry
# OR manually purge if using Cloudflare:
curl -X POST "https://api.cloudflare.com/client/v4/zones/ZONE_ID/purge_cache" \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  --data '{"files":["https://cdn.aiassist.net/widget.js","https://cdn.aiassist.net/widget.min.js","https://cdn.aiassist.net/widget.esm.js"]}'

# For nginx (if using as origin):
# No built-in invalidation - rely on cache TTL or restart nginx
```

## Monitoring

Set up uptime monitoring for:
- `https://cdn.aiassist.net/widget.js` 
- Check Content-Type header is `application/javascript`
- Check response size > 10KB

Recommended tools:
- UptimeRobot (free)
- Pingdom
- Better Uptime
