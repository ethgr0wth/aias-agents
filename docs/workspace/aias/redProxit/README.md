# redProxit

**AI-powered Reddit poster using AiAssist Secure**

Generate subreddit-appropriate posts with AI and publish them to Reddit. Built for scale with proxy support.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set your API keys (never hardcode these!)
export AIAS_API_KEY="aai_your_key_here"
export REDDIT_CLIENT_ID="your_client_id"
export REDDIT_CLIENT_SECRET="your_client_secret"
export REDDIT_USERNAME="your_username"
export REDDIT_PASSWORD="your_password"

# Generate and preview (dry run)
python redProxit.py --subreddit selfhosted --context "Launching our new AI tool" --dry-run

# Generate and post
python redProxit.py --subreddit selfhosted --context "Launching our new AI tool"
```

## Features

- **AI Content Generation**: Uses AiAssist Secure to generate subreddit-appropriate titles and body text
- **Subreddit Tone Matching**: AI adapts writing style to match community culture
- **Dry Run Mode**: Preview generated content without posting
- **Proxy Support**: SOCKS5/HTTP proxies for scale operations
- **Scheduling**: Delay posting with `--schedule`
- **Context from File**: Use `--context-file` or default `context.txt`

## Usage

### Basic

```bash
# From inline context
python redProxit.py -s python -c "Announcing a new async library for Redis"

# From file
echo "Our new tool helps developers..." > context.txt
python redProxit.py -s selfhosted --dry-run

# With specific context file
python redProxit.py -s homelab -f announcement.txt
```

### With Proxy (for Tor or rotating proxies)

```bash
# Single proxy (Tor)
python redProxit.py -s selfhosted -c "..." --proxy socks5://127.0.0.1:9050

# Multiple proxies (rotates)
python redProxit.py -s selfhosted -c "..." --proxy-file proxies.txt
```

### Scheduling

```bash
# Post after delay
python redProxit.py -s python -c "..." --schedule 30m
python redProxit.py -s python -c "..." --schedule 2h
```

### Skip Confirmation

```bash
python redProxit.py -s selfhosted -c "..." --yes
```

## Configuration

Copy `config.example.yaml` to `config.yaml`:

```bash
cp config.example.yaml config.yaml
```

### Environment Variables (Recommended)

Never hardcode credentials. Use environment variables:

| Variable | Description |
|----------|-------------|
| `AIAS_API_KEY` | AiAssist Secure API key |
| `AIAS_BASE_URL` | AiAS server URL (default: http://localhost:8000) |
| `REDDIT_CLIENT_ID` | Reddit OAuth app client ID |
| `REDDIT_CLIENT_SECRET` | Reddit OAuth app client secret |
| `REDDIT_USERNAME` | Reddit account username |
| `REDDIT_PASSWORD` | Reddit account password |

### Reddit App Setup

1. Go to https://www.reddit.com/prefs/apps
2. Click "create another app..."
3. Select "script" type
4. Note the client ID (under app name) and secret

## Proxy Support

### Tor (Local SOCKS5)

```bash
# Start Tor service
sudo systemctl start tor

# Use with redProxit
python redProxit.py -s privacy -c "..." --proxy socks5://127.0.0.1:9050
```

### Rotating Proxies

Create `proxies.txt`:

```
socks5://127.0.0.1:9050
socks5://127.0.0.1:9051
http://user:pass@proxy.example.com:8080
```

```bash
python redProxit.py -s selfhosted -c "..." --proxy-file proxies.txt
```

## Output Example

```
$ python redProxit.py -s selfhosted -c "We built an AI chat platform with shadow mode" --dry-run

2024-01-15 10:30:00 - INFO - Context loaded (52 chars)
2024-01-15 10:30:00 - INFO - Generating content for r/selfhosted...

============================================================
📍 Subreddit: r/selfhosted
============================================================

📝 TITLE:
Built a self-hosted AI chat with human approval workflow - here's what I learned

📄 BODY:
Hey r/selfhosted,

After months of running various AI chat solutions, I got frustrated with...

[AI-generated content continues]

============================================================

🔍 DRY RUN - Post not submitted
```

## Security Notes

- **Never commit credentials** - Use environment variables
- **config.yaml is gitignored** - Keep it that way
- **Proxy your identity** - If posting at scale, use Tor or VPN
- **Respect rate limits** - Reddit will ban aggressive posters

## License

MIT - Part of the AiAssist Secure ecosystem.
