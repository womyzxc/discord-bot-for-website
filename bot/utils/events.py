"""
Event Utilities
===============
Helper functions for emitting WebSocket events from bot cogs.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger('Offcialx.Events')

# Reference to WebSocket manager (set by main.py)
_ws_manager = None
_api_enabled = False

def set_ws_manager(manager):
    """Set the WebSocket manager reference"""
    global _ws_manager, _api_enabled
    _ws_manager = manager
    _api_enabled = True
    logger.info('WebSocket event system initialized')

def is_api_enabled() -> bool:
    """Check if API/WebSocket is enabled"""
    return _api_enabled

async def emit_event(guild_id: int, event_type: str, data: Dict[str, Any]):
    """Emit an event to WebSocket clients"""
    if not _api_enabled or not _ws_manager:
        return

    try:
        await _ws_manager.broadcast_to_guild(guild_id, {
            'type': event_type,
            'data': data
        })
    except Exception as e:
        logger.error(f'Failed to emit event: {e}')

async def emit_global_event(event_type: str, data: Dict[str, Any]):
    """Emit an event to all global WebSocket clients"""
    if not _api_enabled or not _ws_manager:
        return

    try:
        await _ws_manager.broadcast_global({
            'type': event_type,
            'data': data
        })
    except Exception as e:
        logger.error(f'Failed to emit global event: {e}')

# Convenience functions for common events

async def emit_threat_detected(guild_id: int, user_id: int, threat_type: str,
                               threat_score: float, details: str = None):
    """Emit a threat detection event"""
    await emit_event(guild_id, 'threat_detected', {
        'user_id': str(user_id),
        'threat_type': threat_type,
        'threat_score': threat_score,
        'details': details,
        'detected_at': datetime.utcnow().isoformat()
    })

async def emit_user_punished(guild_id: int, user_id: int, action: str,
                             moderator_id: int = None, reason: str = None,
                             duration: int = None):
    """Emit a user punishment event"""
    await emit_event(guild_id, f'user_{action}', {
        'user_id': str(user_id),
        'action': action,
        'moderator_id': str(moderator_id) if moderator_id else None,
        'reason': reason,
        'duration': duration,
        'timestamp': datetime.utcnow().isoformat()
    })

async def emit_lockdown_status(guild_id: int, is_locked: bool,
                               channels: int, reason: str = None):
    """Emit lockdown status change event"""
    event_type = 'lockdown_started' if is_locked else 'lockdown_ended'
    await emit_event(guild_id, event_type, {
        'locked': is_locked,
        'channels_affected': channels,
        'reason': reason,
        'timestamp': datetime.utcnow().isoformat()
    })

async def emit_raid_mode(guild_id: int, is_active: bool, reason: str = None):
    """Emit raid mode status change event"""
    event_type = 'raid_mode_enabled' if is_active else 'raid_mode_disabled'
    await emit_event(guild_id, event_type, {
        'active': is_active,
        'reason': reason,
        'timestamp': datetime.utcnow().isoformat()
    })

async def emit_settings_changed(guild_id: int, module: str,
                                changes: Dict[str, Any]):
    """Emit settings change event"""
    await emit_event(guild_id, 'settings_changed', {
        'module': module,
        'changes': changes,
        'timestamp': datetime.utcnow().isoformat()
    })

async def emit_backup_created(guild_id: int, version: int,
                              roles: int, channels: int):
    """Emit backup creation event"""
    await emit_event(guild_id, 'backup_created', {
        'version': version,
        'roles': roles,
        'channels': channels,
        'timestamp': datetime.utcnow().isoformat()
    })

async def emit_bot_status(guilds: int, users: int, latency: float,
                          status: str = 'online'):
    """Emit bot status to all global connections"""
    await emit_global_event('bot_status', {
        'guilds': guilds,
        'users': users,
        'latency_ms': round(latency * 1000),
        'status': status,
        'timestamp': datetime.utcnow().isoformat()
    })
