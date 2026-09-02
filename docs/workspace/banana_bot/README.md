# 🍌 Banny Banana's (Ban Bot)

**Intelligent anti-spam moderation for Discord and Telegram.**

Banny detects raid links, scam invites, and NSFW spam — issues a one-shot warning... deletes the offensive content, then permanently bans repeat offenders. It scans live messages **and** historical channel content, never touches your admins, and respects role hierarchy by design.

---

## Features

### Live moderation
- **Hardcoded invite-link detection** — Discord, Telegram, WhatsApp, Facebook groups, Signal, Instagram, and common spam shortlinks (bit.ly, tinyurl, etc.) — always enforced
- **Optional keyword list** — fully configurable, defaults to a sensible NSFW pack (porn, onlyfans, escort, etc.) — disable anytime by emptying the list
- **2-strike system** — first offense = silent delete + private warning that auto-expires in 30s; second offense = permanent ban + history purge
- **Strike memory** — strikes expire after 30 days by default (configurable)

### Safety guarantees — the bot will *never* moderate:
- The server owner
- Anyone with the Administrator permission
- Anyone whose top role is equal to or above Banny's own role
- Anyone in your configured `exempt_roles` list
- Anyone whose username/display name contains a string from `exempt_name_contains`
- Group admins on Telegram (checked live per message)

### `/sentinel` — historical deep-scan slash command
- Scans every watched channel for matching content
- **Animated live progress bar** with spinner and per-channel scan status
- **Resumable** — saves per-channel cursors to SQLite, so you can run it again and only check new messages since the last scan
- **Rate-limit smart** — bulk-deletes recent messages (≤14d), individually deletes older ones, with exponential backoff on 429s
- **Dry-run mode** — preview deletions without touching anything
- Single-channel or full-server scope

### Operational
- **`#banny-log` channel** — all bans, strikes, and startup events post here only; public channels stay quiet
- **SQLite persistence** — strike history, ban list, tracked messages, sentinel progress
- **Channel scoping** — whitelist (`watch`) or blacklist (`ignore`) channels by name or ID
- **Edit detection** — re-checks edited messages for evasion attempts
- **Clean restart** — `start.sh` hard-kills any stale Banny processes before launching

---

## Quick start

### 1. Get your bot tokens

**Discord**
1. Visit [discord.com/developers/applications](https://discord.com/developers/applications) → New Application → Bot
2. Copy the token
3. Enable Privileged Gateway Intents: `Message Content`, `Server Members`
4. Invite the bot with: `Manage Messages`, `Ban Members`, `Read Message History`, `Use Slash Commands`

**Telegram**
1. Message [@BotFather](https://t.me/BotFather) → `/newbot` → copy the token
2. Add the bot to your group(s) as an **admin** with: Delete Messages, Ban Users

### 2. Set environment variables

Keep bot tokens out of configuration files and source control. For local
development, copy `.env.example` to `.env` and fill in the values, or export
the variables in your shell:

```bash
export DISCORD_BOT_TOKEN="your_discord_token"
export TELEGRAM_BOT_TOKEN="your_telegram_token"
```

The token environment variables override any token values in `config.yaml`.
Never commit `.env`, `config.yaml`, or the SQLite database.

### 3. Configure

```bash
cp config.example.yaml config.yaml
# edit config.yaml — set exempt_roles, log_channel, keywords, etc.
```

### 4. Create the log channel

In your Discord server, create a text channel named `banny-log` (or whatever you set in `log_channel`). Banny will auto-discover it on startup.

### 5. Run

```bash
bash start.sh
```

That's it. Banny is live.

---

## Configuration reference

### Discord
| Setting | Default | Description |
|---|---|---|
| `discord.enabled` | `false` | Master switch for Discord platform |
| `discord.exempt_roles` | `[Admin, Moderator, Staff]` | Role names that are immune |
| `discord.exempt_name_contains` | `[]` | Username substrings that grant immunity (case-insensitive) |
| `discord.respect_hierarchy` | `true` | Never moderate anyone at or above Banny's role |
| `discord.ban_delete_days` | `7` | Days of history Discord deletes on ban (0–7) |
| `discord.channels.watch` | `[]` | If non-empty, only these channels are moderated |
| `discord.channels.ignore` | `[]` | Channels to never touch (overrides watch) |
| `discord.log_channel` | `banny-log` | Channel name or ID for bans/strikes/startup |

### Telegram
| Setting | Default | Description |
|---|---|---|
| `telegram.enabled` | `false` | Master switch for Telegram platform |
| `telegram.exempt_user_ids` | `[]` | Telegram user IDs that are immune |
| `telegram.exempt_name_contains` | `[]` | Username/first-name substrings for immunity |

### Moderation
| Setting | Default | Description |
|---|---|---|
| `moderation.strikes_before_ban` | `2` | Strikes until permanent ban |
| `moderation.strike_memory_days` | `30` | How long strikes count (0 = forever) |
| `moderation.keywords` | NSFW pack | Optional words/phrases that trigger strikes |
| `moderation.block_all_links` | `false` | Aggressive mode: block every external URL |
| `moderation.allowed_domains` | `[github.com, ...]` | Whitelist for `block_all_links` mode |

### Cleanup
| Setting | Default | Description |
|---|---|---|
| `cleanup.enabled` | `true` | Purge a banned user's recent history |
| `cleanup.scan_days` | `30` | How many days back to clean on ban |

---

## Commands

### Slash commands (Discord)

```
/sentinel days:<int> channel:<#channel> dry_run:<bool> resume:<bool> reset_progress:<bool>
```

| Option | Default | Meaning |
|---|---|---|
| `days` | `0` | How many days back to scan. `0` = all time |
| `channel` | unset | Target a single channel. Leave blank for all watched channels |
| `dry_run` | `false` | Preview deletions only, don't actually delete |
| `resume` | `true` | Pick up from saved cursor (recommended). `false` = full re-scan |
| `reset_progress` | `false` | Wipe saved cursors before starting |

### Prefix commands (Discord)

```
!strikes @user      — check a user's strike count
!channels           — list watched vs ignored channels
```

---

## Strike flow

```
Message arrives
   └─ Author is exempt (owner/admin/high-role)?  → ignore
   └─ Channel is in ignore list?                  → ignore
   └─ Contains invite link OR keyword?
            ├─ NO  → allow
            └─ YES → delete message
                       ├─ Strike 1 → warn (auto-deletes in 30s) + log to #banny-log
                       └─ Strike 2 → ban + purge history + log to #banny-log
```

---

## Hardcoded link patterns

These are **always** flagged regardless of your keyword list:

- **Discord** — `discord.gg/…`, `discord.com/invite/…`
- **Telegram** — `t.me/…`, `telegram.me/…`, `telegram.org/…`
- **WhatsApp** — `chat.whatsapp.com/…`, `wa.me/…`
- **Facebook** — `facebook.com/groups/…`, `fb.com/groups/…`
- **Signal** — `signal.group/#…`
- **Instagram** — `instagram.com/…?igsh=…` (DM spam pattern)
- **Shortlinks** — `bit.ly`, `tinyurl.com`, `rb.gy`, `t.ly`, `is.gd`

---

## Architecture

```
banana_bot/
├── main.py               # entry point (click CLI)
├── start.sh              # bootstrap script (pkill old + launch)
├── config.yaml           # your runtime config (gitignored; copy the example)
├── config.example.yaml   # template
├── .env.example          # token variable template
├── .github/workflows/    # CI checks for supported Python versions
├── requirements.txt
├── data/                 # runtime state (gitignored)
└── src/
    ├── config.py         # Pydantic config models
    ├── engine.py         # orchestrates both platforms
    ├── models.py         # data classes
    ├── moderator.py      # link patterns + keyword scanner
    ├── storage.py        # SQLite layer
    └── platforms/
        ├── discord_mod.py
        └── telegram_mod.py
```

---

## Deploying

See **[DEPLOY.md](./DEPLOY.md)** for production deployment on Replit, Docker, systemd, or bare metal.

---

## License

MIT. Build cool stuff with it.
