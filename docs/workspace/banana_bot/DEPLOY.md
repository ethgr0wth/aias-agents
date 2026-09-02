# Deploying Banana Bot

Banny is a single Python process. No web server, no database server, no message broker — just Python + SQLite. Deployment options below, from easiest to most production-hardened.

---

## Prerequisites (all deployments)

1. **Python 3.10+**
2. **Discord bot token** and/or **Telegram bot token** (see [README.md § Quick start](./README.md#1-get-your-bot-tokens))
3. The bot must be invited to your Discord server / added to your Telegram group as admin
4. On Discord: create a `#banny-log` channel for centralized event logs

---

## Option 1 — Replit (zero config)

The fastest way. Replit handles the runtime, secrets, and process supervision for you.

1. Fork or import this folder into a Replit project
2. In **Tools → Secrets**, add:
   - `DISCORD_BOT_TOKEN`
   - `TELEGRAM_BOT_TOKEN`
3. Copy `config.example.yaml` to `config.yaml` and edit it
4. Set the workflow command to: `cd banana_bot && bash start.sh`
5. Click **Run**

For 24/7 uptime, **Deploy** the workflow as a Reserved VM (Replit handles auto-restart).

---

## Option 2 — Bare metal / VPS

For an Ubuntu / Debian server:

```bash
# 1. Clone the repo
git clone <your-repo-url> banana_bot
cd banana_bot

# 2. Install Python deps system-wide (or in a venv if you prefer)
pip install -r requirements.txt

# 3. Configure
cp config.example.yaml config.yaml
nano config.yaml   # set enabled: true, exempt_roles, log_channel, etc.

# 4. Export tokens
export DISCORD_BOT_TOKEN="your_token"
export TELEGRAM_BOT_TOKEN="your_token"

# 5. Run
bash start.sh
```

Banny logs to stdout. Pipe to a file or use `journalctl` if running under systemd.

---

## Option 3 — systemd service (recommended for VPS)

Create `/etc/systemd/system/banana-bot.service`:

```ini
[Unit]
Description=Banana Bot — Discord & Telegram anti-spam
After=network.target

[Service]
Type=simple
User=banana
WorkingDirectory=/opt/banana_bot
EnvironmentFile=/etc/banana_bot.env
ExecStart=/usr/bin/python3 main.py --config config.yaml
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Create `/etc/banana_bot.env` (mode `600`, owned by root):

```
DISCORD_BOT_TOKEN=your_token
TELEGRAM_BOT_TOKEN=your_token
```

Enable and start:

```bash
sudo useradd -r -s /bin/false banana
sudo chown -R banana:banana /opt/banana_bot
sudo chmod 600 /etc/banana_bot.env
sudo systemctl daemon-reload
sudo systemctl enable --now banana-bot
sudo journalctl -u banana-bot -f   # follow logs
```

---

## Option 4 — Docker

Create `Dockerfile` in the project root:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

RUN mkdir -p data
VOLUME ["/app/data"]

CMD ["python", "main.py", "--config", "config.yaml"]
```

Build and run:

```bash
docker build -t banana-bot .

docker run -d \
  --name banana-bot \
  --restart unless-stopped \
  -e DISCORD_BOT_TOKEN="your_token" \
  -e TELEGRAM_BOT_TOKEN="your_token" \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  -v banana-data:/app/data \
  banana-bot
```

The `banana-data` named volume persists the SQLite database (strikes, sentinel cursors) across restarts.

### docker-compose alternative

```yaml
services:
  banana-bot:
    build: .
    container_name: banana-bot
    restart: unless-stopped
    environment:
      DISCORD_BOT_TOKEN: ${DISCORD_BOT_TOKEN}
      TELEGRAM_BOT_TOKEN: ${TELEGRAM_BOT_TOKEN}
    volumes:
      - ./config.yaml:/app/config.yaml:ro
      - banana-data:/app/data

volumes:
  banana-data:
```

Put your tokens in a `.env` file next to `docker-compose.yml` and run `docker compose up -d`.

---

## Persistence & backups

Banny's only persistent state is `data/banana.db` — a single SQLite file containing:

- User strike records
- Ban list
- Tracked messages (for history purges)
- Sentinel scan cursors (per channel)

**Back it up** if you care about strike continuity across reinstalls:

```bash
# Online backup (safe while bot is running)
sqlite3 data/banana.db ".backup data/banana.backup.db"
```

To migrate to a new host, just copy `config.yaml` and `data/banana.db`.

---

## Operating Banny

### Updating
```bash
git pull
pip install -r requirements.txt --upgrade
# restart the service
sudo systemctl restart banana-bot
```

### Health check
```bash
# look for "[Discord] Banana Bot logged in" in the logs
sudo journalctl -u banana-bot -n 50 --no-pager
```

### Running `/sentinel` for the first time
On a busy server, the first historical scan can take a while. Recommendations:

1. Run a **dry run** first to estimate scope: `/sentinel dry_run:True`
2. Then run for real: `/sentinel`
3. After the first scan completes, subsequent runs are fast (resume mode is on by default — only new messages are checked)

### Resetting sentinel progress
If you want a full fresh re-scan:
```
/sentinel reset_progress:True
```

### Resetting strike history
Stop the bot, delete `data/banana.db`, restart. (Or use `sqlite3` to surgically remove specific users.)

---

## Permissions checklist

**Discord bot needs:**
- ✅ Manage Messages (delete spam)
- ✅ Ban Members (issue bans)
- ✅ Read Message History (sentinel scan)
- ✅ Use Slash Commands (`/sentinel`)
- ✅ Send Messages (warnings + log channel)
- ✅ View Channel (every channel you want monitored)

**Discord bot role placement:** drag Banny's role **above** any roles you want it to be able to moderate. Banny will never moderate users with roles at or above its own.

**Telegram bot needs:**
- ✅ Admin status in every group it should moderate
- ✅ Delete Messages permission
- ✅ Ban Users permission

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Bot starts but no slash commands appear | Wait ~1 min for Discord guild sync. If still missing, kick & re-invite with `applications.commands` scope |
| Bot deletes nothing in `/sentinel` | Check that the channel is not in `channels.ignore` and that the bot has `Read Message History` |
| Two Banny instances running | `bash start.sh` includes `pkill` — but if you launched manually, run `pkill -9 -f "python main.py"` |
| Rate-limit warnings during big scans | Normal — Banny auto-backs-off. Reduce scan scope or let it finish at its own pace |
| `discord.errors.PrivilegedIntentsRequired` | Enable `Message Content` and `Server Members` intents in the Discord Developer Portal |
| Telegram bot ignores messages | Make sure the bot is an **admin** in the group, not just a member |

---

## Security notes

- Tokens should be supplied through **environment variables** — environment values
  override any token fields in `config.yaml`, and tokens must never be committed
- The SQLite file (`data/banana.db`) contains message content snippets for strike audit logs — keep it on disk Banny owns, mode `600`
- Banny does not phone home, does not collect telemetry, and has no remote update mechanism

---

## Resource footprint

For a server with ~5000 members across ~30 channels:
- **RAM**: ~80–150 MB resident
- **CPU**: < 1% idle, brief spikes during `/sentinel`
- **Disk**: SQLite grows ~1 KB per strike, ~50 bytes per tracked message

Banny will run happily on a $5/month VPS or a Replit free hobby account.
