# Offcialx - Discord Security Bot Website

A modern, feature-rich website for the Offcialx Discord security bot built with Next.js 16, TypeScript, and Tailwind CSS.

![Offcialx](https://img.shields.io/badge/Offcialx-Discord%20Security-purple)
![Next.js](https://img.shields.io/badge/Next.js-16-black)
![TypeScript](https://img.shields.io/badge/TypeScript-5-blue)
![Tailwind CSS](https://img.shields.io/badge/Tailwind-3-38bdf8)

## Features

- **Modern UI** - Sleek dark theme with purple accents and animations
- **Discord & Google OAuth** - Secure authentication via NextAuth.js
- **Admin Panel** - User management, analytics, activity logs, ban/unban users
- **Bot Status Page** - Real-time Discord bot statistics and service health
- **Anti-Nuke Configuration** - Comprehensive bot command documentation
- **Responsive Design** - Fully mobile-friendly

## Quick Start

### Prerequisites

- Node.js 20+ or Bun
- Discord Developer Application
- Google Cloud OAuth credentials (optional)

### Installation

```bash
# Clone the repository
git clone https://github.com/womyzxc/offcialx-website.git
cd offcialx-website

# Install dependencies
npm install
# or
bun install

# Copy environment variables
cp .env.example .env.local

# Start development server
npm run dev
```

### Environment Variables

Create a `.env.local` file with the following variables:

```env
# NextAuth
AUTH_SECRET=your-super-secret-key

# Discord OAuth (https://discord.com/developers/applications)
DISCORD_CLIENT_ID=your-client-id
DISCORD_CLIENT_SECRET=your-client-secret

# Discord Bot Token (for real-time stats)
DISCORD_BOT_TOKEN=your-bot-token

# Google OAuth (https://console.cloud.google.com/apis/credentials)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# App URL
NEXTAUTH_URL=http://localhost:3000
```

## Deployment

### Deploy to Railway

1. **Connect GitHub Repository:**
   - Go to [Railway](https://railway.app)
   - Click "New Project" → "Deploy from GitHub repo"
   - Select `offcialx-website`

2. **Add Environment Variables:**
   In Railway dashboard → Variables, add:
   - `AUTH_SECRET`
   - `DISCORD_CLIENT_ID`
   - `DISCORD_CLIENT_SECRET`
   - `DISCORD_BOT_TOKEN`
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
   - `NEXTAUTH_URL` (your Railway domain, e.g., `https://your-app.up.railway.app`)

3. **Deploy:**
   Railway will automatically build and deploy using the Dockerfile.

### Deploy to Netlify

1. **Connect GitHub Repository:**
   - Go to [Netlify](https://netlify.com)
   - "Add new site" → "Import an existing project"
   - Connect to GitHub and select `offcialx-website`

2. **Configure Build Settings:**
   - Build command: `npm run build`
   - Publish directory: `.next`

3. **Add Environment Variables:**
   Site settings → Environment variables → Add all required variables.

## GitHub Actions (CI/CD)

This project includes automated workflows:

### CI Pipeline (`.github/workflows/ci.yml`)
- Runs on every push and pull request
- Linting, type checking, and build verification
- Security audit

### Railway Deployment (`.github/workflows/deploy-railway.yml`)
Automatic deployment to Railway on push to main.

**Required Secrets:**
1. Go to your GitHub repo → Settings → Secrets and variables → Actions
2. Add:
   - `RAILWAY_TOKEN`: Get from [Railway Account Settings](https://railway.app/account/tokens)

### Netlify Deployment (`.github/workflows/deploy-netlify.yml`)
Automatic deployment to Netlify on push to main.

**Required Secrets:**
- `NETLIFY_AUTH_TOKEN`: Get from [Netlify User Settings](https://app.netlify.com/user/applications#personal-access-tokens)
- `NETLIFY_SITE_ID`: Found in Site settings → General → Site ID
- All environment variables (AUTH_SECRET, DISCORD_*, GOOGLE_*, NEXTAUTH_URL)

## Project Structure

```
src/
├── app/
│   ├── admin/           # Admin panel pages
│   ├── api/             # API routes
│   │   ├── admin/       # Admin API endpoints
│   │   ├── auth/        # NextAuth endpoints
│   │   └── bot/         # Bot stats API
│   ├── auth/            # Authentication pages
│   ├── dashboard/       # User dashboard
│   ├── documentation/   # Docs page
│   ├── status/          # Bot status page
│   └── themes/          # Themes page
├── components/          # React components
└── lib/                 # Utilities and configs
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/bot/stats` | GET | Fetch Discord bot statistics |
| `/api/bot/health` | GET | Check service health status |
| `/api/bot/incidents` | GET/POST/PATCH | Manage status incidents |
| `/api/admin/users` | GET | List all users (admin) |
| `/api/admin/admins` | GET/POST | Manage admin accounts |
| `/api/admin/stats` | GET | Dashboard analytics |
| `/api/admin/logs` | GET | Activity logs |

## Admin Access

Default admin credentials:
- **Username:** `womy1621`
- **Password:** `womy1621`

Access the admin panel at `/admin/login`

## Tech Stack

- **Framework:** Next.js 16 (App Router, Turbopack)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **Authentication:** NextAuth.js v5
- **Charts:** Recharts
- **Fonts:** Orbitron, Poppins

## Security Notes

⚠️ **Important:**
- Never commit `.env.local` to git (already in `.gitignore`)
- Reset your Discord bot token if exposed
- Use strong `AUTH_SECRET` in production
- Enable 2FA on your Discord Developer account

## License

MIT License - feel free to use this project for your own Discord bot website.

---

**Built with [Same](https://same.new)** 🤖
