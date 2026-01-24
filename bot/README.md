# Offcialx Anti-Nuke Security Bot v3.5.1

Military-grade Discord server protection with 27 protection layers, AI-powered threat detection, and real-time monitoring.

## Features

### Core Protection (27 Layers)
- **Anti-Nuke**: Mass ban/kick/channel/role deletion detection
- **Anti-Raid**: Coordinated attack prevention with VPN detection
- **Anti-Selfbot**: Automated account detection
- **Anti-Spam**: Message flood prevention
- **Behavioral Fingerprinting**: AI-powered user analysis
- **Cross-Server Ban Sync**: Share bans between servers
- **Recovery System**: Undo attacker actions

### Commands
- Beautiful interactive `!help` menu with buttons
- Professional slash commands with ANSI styling
- 12 customizable color themes
- Step-by-step setup wizard

---

## 🚀 Deploy to Railway (Recommended)

Railway provides 24/7 uptime with automatic restarts and easy configuration.

### Quick Deploy

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template)

### Manual Deployment

1. **Create Railway Account**
   - Go to [railway.app](https://railway.app)
   - Sign in with GitHub

2. **Create New Project**
   - Click "New Project" → "Deploy from GitHub repo"
   - Select your repository
   - Choose the `bot` directory as the root

3. **Add Environment Variables**
   In Railway Dashboard → Variables tab, add:

   ```env
   # Required
   DISCORD_BOT_TOKEN=your_bot_token_here

   # Optional but recommended
   BOT_PREFIX=!
   OWNER_IDS=your_discord_id
   ENABLE_API=true
   API_SECRET_KEY=your_secret_key

   # For PostgreSQL (Railway provides this automatically)
   DATABASE_URL=${{Postgres.DATABASE_URL}}

   # For Discord webhook alerts
   WEBHOOK_URL=https://discord.com/api/webhooks/...
   ```

4. **Deploy**
   - Railway will automatically detect the Dockerfile
   - Wait for the build to complete
   - Bot will be online 24/7!

### Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `DISCORD_BOT_TOKEN` | ✅ Yes | Your Discord bot token from [Discord Developer Portal](https://discord.com/developers/applications) |
| `BOT_PREFIX` | No | Command prefix (default: `!`) |
| `OWNER_IDS` | No | Comma-separated Discord user IDs for bot owners |
| `ENABLE_API` | No | Enable REST API for dashboard (default: `true`) |
| `API_SECRET_KEY` | No | Secret key for API authentication |
| `DATABASE_URL` | No | PostgreSQL connection string |
| `WEBHOOK_URL` | No | Discord webhook for security alerts |
| `PORT` | No | API server port (Railway sets this automatically) |

---

## 💻 Local Development

### Prerequisites
- Python 3.11+
- Discord Bot Token

### Installation

```bash
# Clone the repository
git clone https://github.com/womyzxc/discord-bot-for-website.git
cd discord-bot-for-website/bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env and add your DISCORD_BOT_TOKEN

# Run the bot
python main.py

# Or run with API server
python run_with_api.py
```

---

## 🐳 Docker Deployment

```bash
# Build the image
docker build -t offcialx-bot .

# Run the container
docker run -d \
  --name offcialx \
  -e DISCORD_BOT_TOKEN=your_token \
  -e ENABLE_API=true \
  -p 8080:8080 \
  offcialx-bot
```

---

## 📁 Project Structure

```
bot/
├── main.py              # Bot entry point
├── run_with_api.py      # Bot + API server launcher
├── requirements.txt     # Python dependencies
├── Dockerfile          # Docker configuration
├── Procfile            # Railway/Heroku process file
├── railway.toml        # Railway configuration
├── cogs/               # Bot commands and features
│   ├── antinuke.py     # Anti-nuke protection
│   ├── antiraid.py     # Anti-raid protection
│   ├── ban_sync.py     # Cross-server ban sync
│   ├── vpn_detection.py # VPN/Proxy detection
│   ├── themes.py       # Custom theme system
│   ├── help.py         # Help command
│   ├── slash_commands.py # Slash commands
│   └── ...
├── api/                # REST API for dashboard
│   ├── dashboard.py    # Main API routes
│   ├── websocket.py    # WebSocket for real-time
│   └── security.py     # Rate limiting
├── database/           # Database handlers
│   ├── db.py          # SQLite handler
│   └── postgres.py    # PostgreSQL handler
└── utils/              # Utilities
    ├── embeds.py      # Embed builder
    ├── webhooks.py    # Webhook notifications
    └── scheduler.py   # Background tasks
```

---

## 🔧 Configuration

### Anti-Nuke Thresholds (ULTRA STRICT by default)
All thresholds are set to 1 for maximum protection:
- Mass ban/kick: 1 action triggers
- Channel delete/create: 1 action triggers
- Role modifications: 1 action triggers
- Detection timeframe: 3 seconds

### Trust Levels
- **Level 3 (Owner)**: Full immunity
- **Level 2 (Admin)**: High bypass permissions
- **Level 1 (Mod)**: Limited bypass permissions
- **Level 0 (User)**: No bypass

---

## 🎨 Custom Themes

12 preset themes available:
- 💜 Default (Purple)
- 🌙 Midnight (Dark Blue)
- 🔴 Crimson (Red)
- 💚 Emerald (Green)
- 🌊 Ocean (Blue)
- 🌅 Sunset (Orange)
- ✨ Gold
- 💫 Neon (Cyberpunk)
- 🌹 Rose (Pink)
- ❄️ Arctic (Cyan)
- 🖤 Shadow (Dark)
- 🍃 Mint (Light Green)

Plus custom hex color support!

---

## 📞 Support

- **Discord Server**: [Join Support](https://discord.gg/NXK5sFEJSy)
- **Website**: [offcialx.xyz](https://offcialx.xyz)
- **GitHub Issues**: [Report Bug](https://github.com/womyzxc/discord-bot-for-website/issues)

---

## 📜 License

MIT License - See [LICENSE](../LICENSE) for details.

---

Made with ❤️ by the Offcialx Team
