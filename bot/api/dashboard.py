"""
Web Dashboard API
=================
FastAPI-based REST API for web dashboard integration.
Allows controlling the bot from the Offcialx website.

Features:
- REST API endpoints for bot control
- WebSocket for real-time updates
- Rate limiting and IP blocking
- Token-based authentication
"""

from fastapi import FastAPI, HTTPException, Depends, Header, Query, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import hashlib
import secrets
import asyncio
import logging
import os

# Import security and websocket modules
from .security import SecurityMiddleware, ip_blocker, rate_limiter, get_security_stats
from .websocket import manager as ws_manager, websocket_endpoint, EventTypes

logger = logging.getLogger('Offcialx.API')

# API Models
class GuildSettings(BaseModel):
    enabled: bool = True
    punishment: str = "ban"
    thresholds: Dict[str, int] = {}

class WhitelistEntry(BaseModel):
    user_id: int
    level: str = "trusted"
    reason: Optional[str] = None

class ModAction(BaseModel):
    user_id: int
    action: str  # ban, kick, mute, warn
    reason: Optional[str] = None
    duration: Optional[int] = None  # For mute, in minutes

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class ThreatScanResult(BaseModel):
    user_id: int
    threat_score: float
    risk_level: str
    indicators: List[str]
    patterns: List[Dict]

# Create FastAPI app
app = FastAPI(
    title="Offcialx Dashboard API",
    description="REST API for controlling the Offcialx security bot",
    version="1.0.0"
)

# Security middleware (rate limiting, IP blocking)
app.add_middleware(SecurityMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://offcialx.xyz",
        "https://*.netlify.app",
        "https://*.railway.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Bot instance (will be set by main.py)
bot = None
db = None

def set_bot_instance(bot_instance):
    """Set the bot instance for API access"""
    global bot
    bot = bot_instance

def set_db_instance(db_instance):
    """Set the database instance"""
    global db
    db = db_instance

# Authentication
async def verify_api_key(x_api_key: str = Header(...)):
    """Verify API key from header"""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="API key required")

    # Check against environment variable or database
    valid_key = os.getenv('API_SECRET_KEY', '')

    if x_api_key == valid_key:
        return {"admin": True}

    # Check database for user tokens
    if db:
        token_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
        token_data = await db.validate_api_token(token_hash)
        if token_data:
            return token_data

    raise HTTPException(status_code=401, detail="Invalid API key")

async def get_guild_or_404(guild_id: int):
    """Get a guild or raise 404"""
    if not bot:
        raise HTTPException(status_code=503, detail="Bot not connected")

    guild = bot.get_guild(guild_id)
    if not guild:
        raise HTTPException(status_code=404, detail="Guild not found")

    return guild

# ==================== HEALTH & STATUS ====================

@app.get("/api/health")
async def health_check():
    """Check API health"""
    return {
        "status": "healthy",
        "bot_connected": bot is not None and bot.is_ready(),
        "database_connected": db is not None,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/stats")
async def get_bot_stats(auth: dict = Depends(verify_api_key)):
    """Get bot statistics"""
    if not bot:
        raise HTTPException(status_code=503, detail="Bot not connected")

    uptime = datetime.utcnow() - bot.start_time

    return {
        "guilds": len(bot.guilds),
        "users": sum(g.member_count or 0 for g in bot.guilds),
        "latency_ms": round(bot.latency * 1000),
        "uptime_seconds": int(uptime.total_seconds()),
        "shards": bot.shard_count or 1,
        "version": "3.0.0"
    }

# ==================== GUILD MANAGEMENT ====================

@app.get("/api/guilds")
async def list_guilds(auth: dict = Depends(verify_api_key)):
    """List all guilds the bot is in"""
    if not bot:
        raise HTTPException(status_code=503, detail="Bot not connected")

    guilds = []
    for guild in bot.guilds:
        guilds.append({
            "id": str(guild.id),
            "name": guild.name,
            "icon": str(guild.icon.url) if guild.icon else None,
            "member_count": guild.member_count or 0,
            "owner_id": str(guild.owner_id)
        })

    return {"guilds": guilds}

@app.get("/api/guilds/{guild_id}")
async def get_guild(guild_id: int, auth: dict = Depends(verify_api_key)):
    """Get guild details"""
    guild = await get_guild_or_404(guild_id)

    return {
        "id": str(guild.id),
        "name": guild.name,
        "icon": str(guild.icon.url) if guild.icon else None,
        "banner": str(guild.banner.url) if guild.banner else None,
        "member_count": guild.member_count or 0,
        "owner_id": str(guild.owner_id),
        "created_at": guild.created_at.isoformat(),
        "roles": len(guild.roles),
        "channels": len(guild.channels),
        "emojis": len(guild.emojis)
    }

# ==================== SETTINGS ====================

@app.get("/api/guilds/{guild_id}/settings")
async def get_all_settings(guild_id: int, auth: dict = Depends(verify_api_key)):
    """Get all settings for a guild"""
    guild = await get_guild_or_404(guild_id)

    settings = {}

    # Get settings from each cog
    cog_names = ['AntiNuke', 'AntiRaid', 'AntiSpam', 'AntiSelfbot', 'ThreatIntelligence']

    for cog_name in cog_names:
        cog = bot.get_cog(cog_name)
        if cog:
            if cog_name == 'AntiNuke':
                settings[cog_name.lower()] = await cog.get_guild_settings(guild_id)
            else:
                settings[cog_name.lower()] = await cog.get_settings(guild_id)

    return {"guild_id": str(guild_id), "settings": settings}

@app.get("/api/guilds/{guild_id}/settings/{module}")
async def get_module_settings(guild_id: int, module: str, auth: dict = Depends(verify_api_key)):
    """Get settings for a specific module"""
    guild = await get_guild_or_404(guild_id)

    cog_map = {
        'antinuke': 'AntiNuke',
        'antiraid': 'AntiRaid',
        'antispam': 'AntiSpam',
        'antiselfbot': 'AntiSelfbot',
        'threatintel': 'ThreatIntelligence'
    }

    cog_name = cog_map.get(module.lower())
    if not cog_name:
        raise HTTPException(status_code=404, detail="Module not found")

    cog = bot.get_cog(cog_name)
    if not cog:
        raise HTTPException(status_code=404, detail="Module not loaded")

    if cog_name == 'AntiNuke':
        settings = await cog.get_guild_settings(guild_id)
    else:
        settings = await cog.get_settings(guild_id)

    return {"module": module, "settings": settings}

@app.put("/api/guilds/{guild_id}/settings/{module}")
async def update_module_settings(guild_id: int, module: str,
                                  settings: Dict[str, Any],
                                  auth: dict = Depends(verify_api_key)):
    """Update settings for a specific module"""
    guild = await get_guild_or_404(guild_id)

    cog_map = {
        'antinuke': 'AntiNuke',
        'antiraid': 'AntiRaid',
        'antispam': 'AntiSpam',
        'antiselfbot': 'AntiSelfbot',
        'threatintel': 'ThreatIntelligence'
    }

    cog_name = cog_map.get(module.lower())
    if not cog_name:
        raise HTTPException(status_code=404, detail="Module not found")

    cog = bot.get_cog(cog_name)
    if not cog:
        raise HTTPException(status_code=404, detail="Module not loaded")

    # Get current settings and update
    if cog_name == 'AntiNuke':
        current = await cog.get_guild_settings(guild_id)
    else:
        current = await cog.get_settings(guild_id)

    # Update only provided fields
    for key, value in settings.items():
        if key in current:
            current[key] = value

    return {"success": True, "settings": current}

# ==================== WHITELIST ====================

@app.get("/api/guilds/{guild_id}/whitelist")
async def get_whitelist(guild_id: int, auth: dict = Depends(verify_api_key)):
    """Get whitelist for a guild"""
    guild = await get_guild_or_404(guild_id)

    cog = bot.get_cog('Whitelist')
    if not cog:
        raise HTTPException(status_code=503, detail="Whitelist module not loaded")

    entries = cog.get_all_whitelisted(guild_id)

    whitelist = []
    for user_id, entry in entries.items():
        member = guild.get_member(user_id)
        whitelist.append({
            "user_id": str(user_id),
            "username": str(member) if member else "Unknown",
            "level": entry.level,
            "added_by": str(entry.added_by),
            "added_at": entry.added_at.isoformat(),
            "reason": entry.reason
        })

    return {"whitelist": whitelist}

@app.post("/api/guilds/{guild_id}/whitelist")
async def add_to_whitelist(guild_id: int, entry: WhitelistEntry,
                           auth: dict = Depends(verify_api_key)):
    """Add user to whitelist"""
    guild = await get_guild_or_404(guild_id)

    cog = bot.get_cog('Whitelist')
    if not cog:
        raise HTTPException(status_code=503, detail="Whitelist module not loaded")

    cog.add_to_whitelist(guild_id, entry.user_id, entry.level, 0, entry.reason or "")

    return {"success": True, "message": f"Added user {entry.user_id} to whitelist"}

@app.delete("/api/guilds/{guild_id}/whitelist/{user_id}")
async def remove_from_whitelist(guild_id: int, user_id: int,
                                 auth: dict = Depends(verify_api_key)):
    """Remove user from whitelist"""
    guild = await get_guild_or_404(guild_id)

    cog = bot.get_cog('Whitelist')
    if not cog:
        raise HTTPException(status_code=503, detail="Whitelist module not loaded")

    if cog.remove_from_whitelist(guild_id, user_id):
        return {"success": True, "message": f"Removed user {user_id} from whitelist"}
    else:
        raise HTTPException(status_code=404, detail="User not in whitelist")

# ==================== MODERATION ====================

@app.post("/api/guilds/{guild_id}/moderation")
async def mod_action(guild_id: int, action: ModAction,
                     auth: dict = Depends(verify_api_key)):
    """Perform a moderation action"""
    guild = await get_guild_or_404(guild_id)

    member = guild.get_member(action.user_id)
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    try:
        if action.action == "ban":
            await member.ban(reason=action.reason or "API action")
        elif action.action == "kick":
            await member.kick(reason=action.reason or "API action")
        elif action.action == "mute":
            duration = timedelta(minutes=action.duration or 60)
            await member.timeout(duration, reason=action.reason or "API action")
        elif action.action == "unmute":
            await member.timeout(None)
        else:
            raise HTTPException(status_code=400, detail="Invalid action")

        return {"success": True, "message": f"{action.action} applied to user {action.user_id}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/guilds/{guild_id}/warnings/{user_id}")
async def get_user_warnings(guild_id: int, user_id: int,
                            auth: dict = Depends(verify_api_key)):
    """Get warnings for a user"""
    guild = await get_guild_or_404(guild_id)

    cog = bot.get_cog('Moderation')
    if not cog:
        raise HTTPException(status_code=503, detail="Moderation module not loaded")

    warnings = cog.warnings[guild_id].get(user_id, [])

    return {
        "user_id": str(user_id),
        "warning_count": len(warnings),
        "warnings": warnings[-10:]  # Last 10
    }

# ==================== THREAT INTELLIGENCE ====================

@app.get("/api/guilds/{guild_id}/threats/scan/{user_id}")
async def scan_user(guild_id: int, user_id: int,
                    auth: dict = Depends(verify_api_key)):
    """Scan a user for threats"""
    guild = await get_guild_or_404(guild_id)

    cog = bot.get_cog('ThreatIntelligence')
    if not cog:
        raise HTTPException(status_code=503, detail="Threat Intelligence module not loaded")

    analysis = await cog.analyze_behavior(guild_id, user_id)
    global_threat = await cog.check_global_threat(user_id)

    risk_level = "HIGH" if analysis['threat_score'] >= 75 else \
                 "MEDIUM" if analysis['threat_score'] >= 50 else \
                 "LOW" if analysis['threat_score'] >= 25 else "MINIMAL"

    return {
        "user_id": str(user_id),
        "threat_score": analysis['threat_score'],
        "risk_level": risk_level,
        "indicators": analysis['indicators'],
        "patterns": analysis['patterns'],
        "global_threat": global_threat
    }

@app.get("/api/threats/known")
async def get_known_threats(min_score: int = Query(50, ge=0, le=1000),
                            auth: dict = Depends(verify_api_key)):
    """Get known global threats"""
    cog = bot.get_cog('ThreatIntelligence') if bot else None

    if cog:
        threats = []
        for user_id, data in cog.global_threats.items():
            if data.get('total_score', 0) >= min_score:
                threats.append({
                    "user_id": str(user_id),
                    "total_score": data.get('total_score', 0),
                    "threat_types": data.get('threat_types', []),
                    "server_count": len(data.get('guild_ids', []))
                })

        return {"threats": sorted(threats, key=lambda x: x['total_score'], reverse=True)}

    return {"threats": []}

@app.post("/api/guilds/{guild_id}/threats/report")
async def report_threat(guild_id: int, user_id: int, threat_type: str,
                        evidence: Optional[str] = None,
                        auth: dict = Depends(verify_api_key)):
    """Report a threat"""
    guild = await get_guild_or_404(guild_id)

    cog = bot.get_cog('ThreatIntelligence')
    if not cog:
        raise HTTPException(status_code=503, detail="Threat Intelligence module not loaded")

    await cog.report_threat(guild, user_id, threat_type, evidence)

    return {"success": True, "message": f"Threat reported for user {user_id}"}

# ==================== SECURITY LOGS ====================

@app.get("/api/guilds/{guild_id}/logs")
async def get_security_logs(guild_id: int,
                            limit: int = Query(100, ge=1, le=1000),
                            event_type: Optional[str] = None,
                            auth: dict = Depends(verify_api_key)):
    """Get security logs for a guild"""
    guild = await get_guild_or_404(guild_id)

    if db:
        logs = await db.get_security_logs(guild_id, limit, event_type)
        return {"logs": logs}

    return {"logs": []}

# ==================== LOCKDOWN ====================

@app.post("/api/guilds/{guild_id}/lockdown")
async def lockdown_guild(guild_id: int,
                         duration: int = Query(5, ge=1, le=60),
                         reason: str = "API lockdown",
                         auth: dict = Depends(verify_api_key)):
    """Lock down a guild"""
    guild = await get_guild_or_404(guild_id)

    cog = bot.get_cog('Lockdown')
    if not cog:
        raise HTTPException(status_code=503, detail="Lockdown module not loaded")

    # Create a fake member for the API
    locked = await cog.lockdown_server(guild, reason, duration * 60, guild.me)

    return {
        "success": True,
        "message": f"Locked {locked} channels",
        "duration_minutes": duration
    }

@app.delete("/api/guilds/{guild_id}/lockdown")
async def unlock_guild(guild_id: int, auth: dict = Depends(verify_api_key)):
    """Unlock a guild"""
    guild = await get_guild_or_404(guild_id)

    cog = bot.get_cog('Lockdown')
    if not cog:
        raise HTTPException(status_code=503, detail="Lockdown module not loaded")

    unlocked = await cog.unlock_server(guild, "API unlock")

    return {"success": True, "message": f"Unlocked {unlocked} channels"}

# ==================== BACKUP ====================

@app.get("/api/guilds/{guild_id}/backups")
async def list_backups(guild_id: int, auth: dict = Depends(verify_api_key)):
    """List backups for a guild"""
    guild = await get_guild_or_404(guild_id)

    cog = bot.get_cog('Backup')
    if not cog:
        raise HTTPException(status_code=503, detail="Backup module not loaded")

    backups = cog.backups.get(guild_id, [])

    return {
        "backups": [
            {
                "version": b.version,
                "created_at": b.created_at.isoformat(),
                "roles": len(b.roles),
                "channels": len(b.text_channels) + len(b.voice_channels)
            }
            for b in backups
        ]
    }

@app.post("/api/guilds/{guild_id}/backups")
async def create_backup(guild_id: int, auth: dict = Depends(verify_api_key)):
    """Create a backup"""
    guild = await get_guild_or_404(guild_id)

    cog = bot.get_cog('Backup')
    if not cog:
        raise HTTPException(status_code=503, detail="Backup module not loaded")

    backup = await cog.create_backup(guild)

    return {
        "success": True,
        "version": backup.version,
        "roles": len(backup.roles),
        "channels": len(backup.text_channels) + len(backup.voice_channels)
    }


# ==================== WEBSOCKET ====================

@app.websocket("/ws")
async def websocket_global(websocket: WebSocket):
    """Global WebSocket endpoint for all events"""
    await ws_manager.connect(websocket, is_global=True)
    try:
        while True:
            data = await websocket.receive_json()
            if data.get('type') == 'ping':
                await ws_manager.send_personal(websocket, {'type': 'pong'})
    except:
        ws_manager.disconnect(websocket)

@app.websocket("/ws/{guild_id}")
async def websocket_guild(websocket: WebSocket, guild_id: int):
    """Guild-specific WebSocket endpoint"""
    await ws_manager.connect(websocket, guild_id=guild_id)
    try:
        while True:
            data = await websocket.receive_json()
            if data.get('type') == 'ping':
                await ws_manager.send_personal(websocket, {'type': 'pong'})
    except:
        ws_manager.disconnect(websocket)

@app.get("/api/websocket/stats")
async def get_ws_stats(auth: dict = Depends(verify_api_key)):
    """Get WebSocket connection statistics"""
    return ws_manager.get_stats()

# ==================== SECURITY ADMIN ====================

@app.get("/api/security/stats")
async def security_stats(auth: dict = Depends(verify_api_key)):
    """Get security statistics"""
    return await get_security_stats()

@app.post("/api/security/block/{ip}")
async def block_ip(ip: str, auth: dict = Depends(verify_api_key)):
    """Block an IP address"""
    ip_blocker.block_ip(ip)
    return {"success": True, "message": f"IP {ip} blocked"}

@app.delete("/api/security/block/{ip}")
async def unblock_ip(ip: str, auth: dict = Depends(verify_api_key)):
    """Unblock an IP address"""
    ip_blocker.unblock_ip(ip)
    return {"success": True, "message": f"IP {ip} unblocked"}

@app.post("/api/security/whitelist/{ip}")
async def whitelist_ip(ip: str, auth: dict = Depends(verify_api_key)):
    """Whitelist an IP address"""
    ip_blocker.whitelist_ip(ip)
    return {"success": True, "message": f"IP {ip} whitelisted"}

@app.get("/api/security/blocked")
async def get_blocked_ips(auth: dict = Depends(verify_api_key)):
    """Get list of blocked IPs"""
    return {
        "blocked_ips": list(ip_blocker.blocked_ips),
        "temp_blocked": {ip: exp.isoformat() for ip, exp in ip_blocker.temp_blocks.items()}
    }


def create_api_app(bot_instance, db_instance=None):
    """Create and configure the API app"""
    set_bot_instance(bot_instance)
    if db_instance:
        set_db_instance(db_instance)
    return app


# Export WebSocket manager for use in bot cogs
def get_websocket_manager():
    """Get the WebSocket connection manager"""
    return ws_manager
