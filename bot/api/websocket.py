"""
WebSocket Support Module
========================
Real-time communication for the dashboard:
- Live threat alerts
- Security event streaming
- Bot status updates
- Guild activity monitoring
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Set, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect
from collections import defaultdict
import hashlib

logger = logging.getLogger('Offcialx.WebSocket')

class ConnectionManager:
    """Manages WebSocket connections and broadcasts"""

    def __init__(self):
        # Active connections: guild_id -> set of websockets
        self.guild_connections: Dict[int, Set[WebSocket]] = defaultdict(set)

        # Global connections (receive all events)
        self.global_connections: Set[WebSocket] = set()

        # Connection metadata
        self.connection_info: Dict[WebSocket, Dict] = {}

        # Event queue for offline clients
        self.event_queue: Dict[int, list] = defaultdict(list)
        self.max_queue_size = 100

        # Stats
        self.total_connections = 0
        self.total_messages_sent = 0

    async def connect(self, websocket: WebSocket, guild_id: int = None,
                     token: str = None, is_global: bool = False):
        """Accept a new WebSocket connection"""
        await websocket.accept()

        self.connection_info[websocket] = {
            'guild_id': guild_id,
            'token': token,
            'connected_at': datetime.utcnow(),
            'is_global': is_global
        }

        if is_global:
            self.global_connections.add(websocket)
        elif guild_id:
            self.guild_connections[guild_id].add(websocket)

        self.total_connections += 1

        logger.info(f'WebSocket connected: guild={guild_id}, global={is_global}')

        # Send queued events
        if guild_id and guild_id in self.event_queue:
            for event in self.event_queue[guild_id][-50:]:
                await self.send_personal(websocket, event)
            self.event_queue[guild_id].clear()

        # Send connection confirmation
        await self.send_personal(websocket, {
            'type': 'connected',
            'guild_id': guild_id,
            'timestamp': datetime.utcnow().isoformat()
        })

    def disconnect(self, websocket: WebSocket):
        """Handle WebSocket disconnection"""
        info = self.connection_info.get(websocket, {})
        guild_id = info.get('guild_id')

        if info.get('is_global'):
            self.global_connections.discard(websocket)
        elif guild_id:
            self.guild_connections[guild_id].discard(websocket)

        if websocket in self.connection_info:
            del self.connection_info[websocket]

        logger.info(f'WebSocket disconnected: guild={guild_id}')

    async def send_personal(self, websocket: WebSocket, data: Dict):
        """Send message to a specific connection"""
        try:
            await websocket.send_json(data)
            self.total_messages_sent += 1
        except Exception as e:
            logger.error(f'Failed to send WebSocket message: {e}')

    async def broadcast_to_guild(self, guild_id: int, data: Dict):
        """Broadcast message to all connections for a guild"""
        data['guild_id'] = guild_id
        data['timestamp'] = datetime.utcnow().isoformat()

        # Send to guild connections
        dead_connections = set()
        for connection in self.guild_connections[guild_id]:
            try:
                await connection.send_json(data)
                self.total_messages_sent += 1
            except:
                dead_connections.add(connection)

        # Clean up dead connections
        for conn in dead_connections:
            self.disconnect(conn)

        # Send to global connections
        for connection in self.global_connections:
            try:
                await connection.send_json(data)
                self.total_messages_sent += 1
            except:
                pass

        # Queue for offline clients
        self.event_queue[guild_id].append(data)
        if len(self.event_queue[guild_id]) > self.max_queue_size:
            self.event_queue[guild_id] = self.event_queue[guild_id][-self.max_queue_size:]

    async def broadcast_global(self, data: Dict):
        """Broadcast to all global connections"""
        data['timestamp'] = datetime.utcnow().isoformat()

        dead_connections = set()
        for connection in self.global_connections:
            try:
                await connection.send_json(data)
                self.total_messages_sent += 1
            except:
                dead_connections.add(connection)

        for conn in dead_connections:
            self.disconnect(conn)

    def get_stats(self) -> Dict:
        """Get connection statistics"""
        return {
            'total_connections': self.total_connections,
            'active_guild_connections': sum(len(c) for c in self.guild_connections.values()),
            'active_global_connections': len(self.global_connections),
            'total_messages_sent': self.total_messages_sent,
            'guilds_with_connections': len(self.guild_connections)
        }

# Global connection manager
manager = ConnectionManager()

# Event types
class EventTypes:
    # Threat events
    THREAT_DETECTED = 'threat_detected'
    THREAT_BLOCKED = 'threat_blocked'
    USER_FLAGGED = 'user_flagged'

    # Security events
    NUKE_ATTEMPT = 'nuke_attempt'
    RAID_DETECTED = 'raid_detected'
    SPAM_DETECTED = 'spam_detected'

    # Moderation events
    USER_BANNED = 'user_banned'
    USER_KICKED = 'user_kicked'
    USER_MUTED = 'user_muted'
    USER_WARNED = 'user_warned'

    # Lockdown events
    LOCKDOWN_STARTED = 'lockdown_started'
    LOCKDOWN_ENDED = 'lockdown_ended'

    # System events
    BOT_STATUS = 'bot_status'
    SETTINGS_CHANGED = 'settings_changed'
    WHITELIST_UPDATED = 'whitelist_updated'

async def emit_threat_alert(guild_id: int, threat_data: Dict):
    """Emit a threat detection alert"""
    await manager.broadcast_to_guild(guild_id, {
        'type': EventTypes.THREAT_DETECTED,
        'data': threat_data
    })

async def emit_security_event(guild_id: int, event_type: str, data: Dict):
    """Emit a security event"""
    await manager.broadcast_to_guild(guild_id, {
        'type': event_type,
        'data': data
    })

async def emit_moderation_event(guild_id: int, action: str, user_id: int,
                                moderator_id: int, reason: str = None):
    """Emit a moderation action event"""
    event_map = {
        'ban': EventTypes.USER_BANNED,
        'kick': EventTypes.USER_KICKED,
        'mute': EventTypes.USER_MUTED,
        'warn': EventTypes.USER_WARNED
    }

    await manager.broadcast_to_guild(guild_id, {
        'type': event_map.get(action, 'moderation_action'),
        'data': {
            'action': action,
            'user_id': str(user_id),
            'moderator_id': str(moderator_id),
            'reason': reason
        }
    })

async def emit_lockdown_event(guild_id: int, is_locked: bool,
                              channels_affected: int, reason: str = None):
    """Emit a lockdown event"""
    event_type = EventTypes.LOCKDOWN_STARTED if is_locked else EventTypes.LOCKDOWN_ENDED

    await manager.broadcast_to_guild(guild_id, {
        'type': event_type,
        'data': {
            'locked': is_locked,
            'channels_affected': channels_affected,
            'reason': reason
        }
    })

async def emit_bot_status(status: Dict):
    """Emit bot status update to all global connections"""
    await manager.broadcast_global({
        'type': EventTypes.BOT_STATUS,
        'data': status
    })

# WebSocket route handler
async def websocket_endpoint(websocket: WebSocket, guild_id: int = None):
    """WebSocket endpoint handler"""
    await manager.connect(websocket, guild_id)

    try:
        while True:
            # Receive and process messages from client
            data = await websocket.receive_json()

            if data.get('type') == 'ping':
                await manager.send_personal(websocket, {
                    'type': 'pong',
                    'timestamp': datetime.utcnow().isoformat()
                })

            elif data.get('type') == 'subscribe':
                # Subscribe to a guild
                new_guild_id = data.get('guild_id')
                if new_guild_id:
                    info = manager.connection_info.get(websocket, {})
                    old_guild_id = info.get('guild_id')

                    if old_guild_id:
                        manager.guild_connections[old_guild_id].discard(websocket)

                    manager.guild_connections[new_guild_id].add(websocket)
                    info['guild_id'] = new_guild_id

                    await manager.send_personal(websocket, {
                        'type': 'subscribed',
                        'guild_id': new_guild_id
                    })

            elif data.get('type') == 'get_stats':
                await manager.send_personal(websocket, {
                    'type': 'stats',
                    'data': manager.get_stats()
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f'WebSocket error: {e}')
        manager.disconnect(websocket)

# Integration functions for bot cogs
def get_manager() -> ConnectionManager:
    """Get the global connection manager"""
    return manager
