# License Server VPS Deployment Guide

Deploy the AiAS License Server on a VPS with nginx reverse proxy and SSL.

## Prerequisites

- Ubuntu 22.04+ VPS (DigitalOcean, Linode, Vultr, etc.)
- Domain pointed to VPS IP (`license.aiassist.net` → your VPS IP)
- SSH access to the server

## 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip python3-venv nginx certbot python3-certbot-nginx redis-server git

# Enable and start Redis
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Verify Redis is running
redis-cli ping  # Should return PONG
```

## 2. Deploy License Server

```bash
# Create directory structure
mkdir -p /opt/aias/license-server/packages

# Upload these files to /opt/aias/license-server/:
# - main.py
# - packages/core-services.zip
# - packages/core-routes.zip
# - packages/core-providers.zip

# Create virtual environment
cd /opt/aias/license-server
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install fastapi uvicorn redis httpx pydantic
```

## 3. Create Environment File

```bash
nano /opt/aias/.env
```

Add:
```bash
REDIS_URL=redis://localhost:6379/2
ENVATO_PERSONAL_TOKEN=QJ6GluMCwLKMUjv1kU4EE7Ie7RZ1RjIg
SESSION_SECRET=d3f5805d9aabf838417ddbe146cfa6bf409c4944b176d0bbe868389a319c3bd753df02d57751632ae0582882a78bc5b8822d605aacdfcd46c4a96e92aa61c22d
LICENSE_SERVER_PORT=4488
PACKAGES_DIR=/opt/aias/license-server/packages

# DO NOT SET THESE IN PRODUCTION
# DEV_MODE=false
# DEV_SECRET=
```

Secure the file:
```bash
chmod 600 /opt/aias/.env
```

## 4. Create Systemd Service

```bash
nano /etc/systemd/system/aias-license.service
```

Add:
```ini
[Unit]
Description=AiAS License Server
After=network.target redis-server.service
Wants=redis-server.service

[Service]
Type=simple
User=root
Group=root
WorkingDirectory=/opt/aias/license-server
EnvironmentFile=/opt/aias/.env
ExecStart=/opt/aias/license-server/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8001
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable aias-license
sudo systemctl start aias-license

# Check status
sudo systemctl status aias-license

# View logs
sudo journalctl -u aias-license -f
```

## 5. Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/license.aiassist.net
```

Add:
```nginx
server {
    listen 80;
    server_name license.aiassist.net;

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for package downloads
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Allow larger package uploads if needed
        client_max_body_size 50M;
    }

    # Health check endpoint (no logging)
    location /health {
        proxy_pass http://127.0.0.1:8001/health;
        access_log off;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/license.aiassist.net /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 6. Install SSL Certificate

```bash
sudo certbot --nginx -d license.aiassist.net
```

Follow prompts. Certbot will:
- Obtain Let's Encrypt certificate
- Configure nginx for HTTPS
- Set up auto-renewal

Verify auto-renewal:
```bash
sudo certbot renew --dry-run
```

## 7. Configure Firewall

```bash
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

## 8. Test Deployment

```bash
# Health check
curl https://license.aiassist.net/health

# Should return:
# {"status":"healthy","redis":"connected","timestamp":"..."}
```

## 9. Upload Core Packages

From your local machine:
```bash
# Build packages first
python scripts/build-core-packages.py

# Upload to VPS
scp license-server/packages/*.zip user@your-vps:/tmp/

# On VPS, move to correct location
sudo -u aias mv /tmp/*.zip /opt/aias/license-server/packages/
```

---

## Maintenance

### View Logs
```bash
# Live logs
sudo journalctl -u aias-license -f

# Last 100 lines
sudo journalctl -u aias-license -n 100
```

### Restart Service
```bash
sudo systemctl restart aias-license
```

### Update License Server
```bash
# Upload new main.py
sudo -u aias cp /path/to/new/main.py /opt/aias/license-server/

# Restart
sudo systemctl restart aias-license
```

### Update Core Packages
```bash
# Build locally
python scripts/build-core-packages.py

# Upload
scp license-server/packages/*.zip user@your-vps:/tmp/
sudo -u aias mv /tmp/*.zip /opt/aias/license-server/packages/

# No restart needed - packages served directly
```

### Check Redis Data
```bash
redis-cli
> KEYS license:*
> GET license:code:some-purchase-code
```

---

## Security Hardening

### Fail2Ban (Block Brute Force)
```bash
sudo apt install fail2ban
sudo systemctl enable fail2ban
```

### SSH Key-Only Access
```bash
# Disable password auth
sudo nano /etc/ssh/sshd_config
# Set: PasswordAuthentication no
sudo systemctl restart sshd
```

### Secure Redis
```bash
sudo nano /etc/redis/redis.conf
# Set: bind 127.0.0.1
# Set: requirepass your-redis-password
sudo systemctl restart redis-server
```

Update `.env`:
```bash
REDIS_URL=redis://:your-redis-password@localhost:6379
```

---

## Monitoring

### Simple Uptime Check
```bash
# Add to crontab
crontab -e

# Check every 5 minutes
*/5 * * * * curl -sf https://license.aiassist.net/health || echo "License server down" | mail -s "ALERT" you@email.com
```

### Resource Usage
```bash
# Memory/CPU
htop

# Disk
df -h
```

---

## Troubleshooting

### "502 Bad Gateway"
- License server not running: `sudo systemctl status aias-license`
- Check logs: `sudo journalctl -u aias-license -n 50`

### "Connection refused" on health check
- Firewall blocking: `sudo ufw status`
- Nginx not running: `sudo systemctl status nginx`

### Redis connection failed
- Redis not running: `sudo systemctl status redis-server`
- Wrong password in REDIS_URL

### SSL certificate errors
- Renew certificate: `sudo certbot renew`
- Check nginx config: `sudo nginx -t`
