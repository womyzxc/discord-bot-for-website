"""
Offcialx Dashboard API
======================
FastAPI-based REST API for web dashboard integration.

Features:
- REST API endpoints
- WebSocket for real-time updates
- Rate limiting and IP blocking
"""

from .dashboard import app, create_api_app, set_bot_instance, set_db_instance, get_websocket_manager
from .websocket import manager as ws_manager, emit_threat_alert, emit_security_event, emit_moderation_event
from .security import rate_limiter, ip_blocker, SecurityMiddleware

__all__ = [
    'app',
    'create_api_app',
    'set_bot_instance',
    'set_db_instance',
    'get_websocket_manager',
    'ws_manager',
    'emit_threat_alert',
    'emit_security_event',
    'emit_moderation_event',
    'rate_limiter',
    'ip_blocker',
    'SecurityMiddleware'
]
