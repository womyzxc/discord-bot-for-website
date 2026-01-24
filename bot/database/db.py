"""
Database Module
===============
SQLite/PostgreSQL database for persistent storage of:
- Guild settings
- Whitelist entries
- Backups metadata
- Security logs
- User warnings
- Threat intelligence data
"""

import aiosqlite
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import os

logger = logging.getLogger('Offcialx.Database')

# Database path
DB_PATH = os.getenv('DATABASE_PATH', 'data/offcialx.db')

class Database:
    """Async SQLite database handler"""

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.connection: Optional[aiosqlite.Connection] = None
        self._lock = asyncio.Lock()

    async def connect(self):
        """Connect to the database"""
        # Ensure data directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        self.connection = await aiosqlite.connect(self.db_path)
        self.connection.row_factory = aiosqlite.Row

        # Enable foreign keys
        await self.connection.execute("PRAGMA foreign_keys = ON")

        # Create tables
        await self._create_tables()

        logger.info(f'Connected to database: {self.db_path}')

    async def close(self):
        """Close the database connection"""
        if self.connection:
            await self.connection.close()
            logger.info('Database connection closed')

    async def _create_tables(self):
        """Create all required tables"""

        # Guild settings table
        await self.connection.execute('''
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id INTEGER PRIMARY KEY,
                module TEXT NOT NULL,
                settings TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create unique index on guild_id + module
        await self.connection.execute('''
            CREATE UNIQUE INDEX IF NOT EXISTS idx_guild_module
            ON guild_settings(guild_id, module)
        ''')

        # Whitelist table
        await self.connection.execute('''
            CREATE TABLE IF NOT EXISTS whitelist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                level TEXT NOT NULL,
                added_by INTEGER NOT NULL,
                reason TEXT,
                added_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(guild_id, user_id)
            )
        ''')

        # Warnings table
        await self.connection.execute('''
            CREATE TABLE IF NOT EXISTS warnings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                moderator_id INTEGER NOT NULL,
                reason TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Security logs table
        await self.connection.execute('''
            CREATE TABLE IF NOT EXISTS security_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                user_id INTEGER,
                target_id INTEGER,
                action TEXT,
                details TEXT,
                severity TEXT DEFAULT 'info',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Threat intelligence table
        await self.connection.execute('''
            CREATE TABLE IF NOT EXISTS threat_intel (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                threat_type TEXT NOT NULL,
                threat_score INTEGER DEFAULT 0,
                evidence TEXT,
                guild_ids TEXT,
                first_seen TEXT DEFAULT CURRENT_TIMESTAMP,
                last_seen TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, threat_type)
            )
        ''')

        # Action patterns table (for AI analysis)
        await self.connection.execute('''
            CREATE TABLE IF NOT EXISTS action_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                action_type TEXT NOT NULL,
                action_count INTEGER DEFAULT 1,
                timeframe INTEGER NOT NULL,
                pattern_hash TEXT,
                is_suspicious INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Backups metadata table
        await self.connection.execute('''
            CREATE TABLE IF NOT EXISTS backups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                version INTEGER NOT NULL,
                backup_data TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(guild_id, version)
            )
        ''')

        # Quarantine table
        await self.connection.execute('''
            CREATE TABLE IF NOT EXISTS quarantine (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                original_roles TEXT,
                reason TEXT,
                quarantined_at TEXT DEFAULT CURRENT_TIMESTAMP,
                expires_at TEXT,
                UNIQUE(guild_id, user_id)
            )
        ''')

        # Trusted users table (for antinuke trust command)
        await self.connection.execute('''
            CREATE TABLE IF NOT EXISTS trusted_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                added_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(guild_id, user_id)
            )
        ''')

        # Trusted bots table (for antinuke trustbot command)
        await self.connection.execute('''
            CREATE TABLE IF NOT EXISTS trusted_bots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                bot_id INTEGER NOT NULL,
                added_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(guild_id, bot_id)
            )
        ''')

        # Whitelisted roles table (for wlist role command)
        await self.connection.execute('''
            CREATE TABLE IF NOT EXISTS whitelisted_roles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                role_id INTEGER NOT NULL,
                added_by INTEGER NOT NULL,
                reason TEXT,
                added_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(guild_id, role_id)
            )
        ''')

        # Channel backups table (for anti-nuke restore)
        await self.connection.execute('''
            CREATE TABLE IF NOT EXISTS channel_backups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                channel_data TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(guild_id, channel_id)
            )
        ''')

        await self.connection.commit()
        logger.info('Database tables created/verified')

    # ==================== GUILD SETTINGS ====================

    async def get_guild_settings(self, guild_id: int, module: str) -> Optional[Dict]:
        """Get settings for a guild module"""
        async with self._lock:
            cursor = await self.connection.execute(
                'SELECT settings FROM guild_settings WHERE guild_id = ? AND module = ?',
                (guild_id, module)
            )
            row = await cursor.fetchone()

            if row:
                return json.loads(row['settings'])
            return None

    async def save_guild_settings(self, guild_id: int, module: str, settings: Dict):
        """Save settings for a guild module"""
        async with self._lock:
            await self.connection.execute('''
                INSERT INTO guild_settings (guild_id, module, settings, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(guild_id, module) DO UPDATE SET
                    settings = excluded.settings,
                    updated_at = excluded.updated_at
            ''', (guild_id, module, json.dumps(settings), datetime.utcnow().isoformat()))
            await self.connection.commit()

    async def delete_guild_settings(self, guild_id: int, module: str = None):
        """Delete settings for a guild (optionally specific module)"""
        async with self._lock:
            if module:
                await self.connection.execute(
                    'DELETE FROM guild_settings WHERE guild_id = ? AND module = ?',
                    (guild_id, module)
                )
            else:
                await self.connection.execute(
                    'DELETE FROM guild_settings WHERE guild_id = ?',
                    (guild_id,)
                )
            await self.connection.commit()

    # ==================== WHITELIST ====================

    async def get_whitelist(self, guild_id: int) -> List[Dict]:
        """Get all whitelist entries for a guild"""
        async with self._lock:
            cursor = await self.connection.execute(
                'SELECT * FROM whitelist WHERE guild_id = ?',
                (guild_id,)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_whitelist_entry(self, guild_id: int, user_id: int) -> Optional[Dict]:
        """Get a specific whitelist entry"""
        async with self._lock:
            cursor = await self.connection.execute(
                'SELECT * FROM whitelist WHERE guild_id = ? AND user_id = ?',
                (guild_id, user_id)
            )
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def add_to_whitelist(self, guild_id: int, user_id: int, level: str,
                               added_by: int, reason: str = None):
        """Add user to whitelist"""
        async with self._lock:
            await self.connection.execute('''
                INSERT INTO whitelist (guild_id, user_id, level, added_by, reason)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(guild_id, user_id) DO UPDATE SET
                    level = excluded.level,
                    added_by = excluded.added_by,
                    reason = excluded.reason,
                    added_at = CURRENT_TIMESTAMP
            ''', (guild_id, user_id, level, added_by, reason))
            await self.connection.commit()

    async def remove_from_whitelist(self, guild_id: int, user_id: int):
        """Remove user from whitelist"""
        async with self._lock:
            await self.connection.execute(
                'DELETE FROM whitelist WHERE guild_id = ? AND user_id = ?',
                (guild_id, user_id)
            )
            await self.connection.commit()

    async def clear_whitelist(self, guild_id: int, level: str = None):
        """Clear whitelist for a guild"""
        async with self._lock:
            if level:
                await self.connection.execute(
                    'DELETE FROM whitelist WHERE guild_id = ? AND level = ?',
                    (guild_id, level)
                )
            else:
                await self.connection.execute(
                    'DELETE FROM whitelist WHERE guild_id = ?',
                    (guild_id,)
                )
            await self.connection.commit()

    # ==================== WARNINGS ====================

    async def get_warnings(self, guild_id: int, user_id: int) -> List[Dict]:
        """Get warnings for a user"""
        async with self._lock:
            cursor = await self.connection.execute(
                'SELECT * FROM warnings WHERE guild_id = ? AND user_id = ? ORDER BY created_at DESC',
                (guild_id, user_id)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def add_warning(self, guild_id: int, user_id: int, moderator_id: int, reason: str):
        """Add a warning"""
        async with self._lock:
            await self.connection.execute('''
                INSERT INTO warnings (guild_id, user_id, moderator_id, reason)
                VALUES (?, ?, ?, ?)
            ''', (guild_id, user_id, moderator_id, reason))
            await self.connection.commit()

    async def clear_warnings(self, guild_id: int, user_id: int):
        """Clear warnings for a user"""
        async with self._lock:
            await self.connection.execute(
                'DELETE FROM warnings WHERE guild_id = ? AND user_id = ?',
                (guild_id, user_id)
            )
            await self.connection.commit()

    async def get_warning_count(self, guild_id: int, user_id: int) -> int:
        """Get warning count for a user"""
        async with self._lock:
            cursor = await self.connection.execute(
                'SELECT COUNT(*) as count FROM warnings WHERE guild_id = ? AND user_id = ?',
                (guild_id, user_id)
            )
            row = await cursor.fetchone()
            return row['count'] if row else 0

    # ==================== SECURITY LOGS ====================

    async def log_security_event(self, guild_id: int, event_type: str,
                                 user_id: int = None, target_id: int = None,
                                 action: str = None, details: str = None,
                                 severity: str = 'info'):
        """Log a security event"""
        async with self._lock:
            await self.connection.execute('''
                INSERT INTO security_logs (guild_id, event_type, user_id, target_id, action, details, severity)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (guild_id, event_type, user_id, target_id, action, details, severity))
            await self.connection.commit()

    async def get_security_logs(self, guild_id: int, limit: int = 100,
                                event_type: str = None) -> List[Dict]:
        """Get security logs for a guild"""
        async with self._lock:
            if event_type:
                cursor = await self.connection.execute('''
                    SELECT * FROM security_logs
                    WHERE guild_id = ? AND event_type = ?
                    ORDER BY created_at DESC LIMIT ?
                ''', (guild_id, event_type, limit))
            else:
                cursor = await self.connection.execute('''
                    SELECT * FROM security_logs
                    WHERE guild_id = ?
                    ORDER BY created_at DESC LIMIT ?
                ''', (guild_id, limit))

            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    # ==================== THREAT INTELLIGENCE ====================

    async def add_threat_intel(self, user_id: int, threat_type: str,
                               threat_score: int, evidence: str = None,
                               guild_id: int = None):
        """Add or update threat intelligence"""
        async with self._lock:
            # Get existing entry
            cursor = await self.connection.execute(
                'SELECT * FROM threat_intel WHERE user_id = ? AND threat_type = ?',
                (user_id, threat_type)
            )
            existing = await cursor.fetchone()

            if existing:
                # Update existing
                existing_guilds = json.loads(existing['guild_ids'] or '[]')
                if guild_id and guild_id not in existing_guilds:
                    existing_guilds.append(guild_id)

                new_score = min(existing['threat_score'] + threat_score, 1000)

                await self.connection.execute('''
                    UPDATE threat_intel
                    SET threat_score = ?, evidence = ?, guild_ids = ?, last_seen = ?
                    WHERE user_id = ? AND threat_type = ?
                ''', (new_score, evidence, json.dumps(existing_guilds),
                      datetime.utcnow().isoformat(), user_id, threat_type))
            else:
                # Insert new
                guild_ids = json.dumps([guild_id] if guild_id else [])
                await self.connection.execute('''
                    INSERT INTO threat_intel (user_id, threat_type, threat_score, evidence, guild_ids)
                    VALUES (?, ?, ?, ?, ?)
                ''', (user_id, threat_type, threat_score, evidence, guild_ids))

            await self.connection.commit()

    async def get_threat_intel(self, user_id: int) -> List[Dict]:
        """Get threat intelligence for a user"""
        async with self._lock:
            cursor = await self.connection.execute(
                'SELECT * FROM threat_intel WHERE user_id = ?',
                (user_id,)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_threat_score(self, user_id: int) -> int:
        """Get total threat score for a user"""
        async with self._lock:
            cursor = await self.connection.execute(
                'SELECT SUM(threat_score) as total FROM threat_intel WHERE user_id = ?',
                (user_id,)
            )
            row = await cursor.fetchone()
            return row['total'] or 0

    async def get_known_threats(self, min_score: int = 50) -> List[Dict]:
        """Get all known threats above a minimum score"""
        async with self._lock:
            cursor = await self.connection.execute('''
                SELECT user_id, SUM(threat_score) as total_score,
                       GROUP_CONCAT(threat_type) as threat_types
                FROM threat_intel
                GROUP BY user_id
                HAVING total_score >= ?
                ORDER BY total_score DESC
            ''', (min_score,))
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    # ==================== ACTION PATTERNS ====================

    async def record_action_pattern(self, guild_id: int, user_id: int,
                                    action_type: str, timeframe: int,
                                    pattern_hash: str = None, is_suspicious: bool = False):
        """Record an action pattern for analysis"""
        async with self._lock:
            await self.connection.execute('''
                INSERT INTO action_patterns (guild_id, user_id, action_type, timeframe, pattern_hash, is_suspicious)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (guild_id, user_id, action_type, timeframe, pattern_hash, int(is_suspicious)))
            await self.connection.commit()

    async def get_action_patterns(self, guild_id: int = None, user_id: int = None,
                                  suspicious_only: bool = False) -> List[Dict]:
        """Get action patterns"""
        async with self._lock:
            query = 'SELECT * FROM action_patterns WHERE 1=1'
            params = []

            if guild_id:
                query += ' AND guild_id = ?'
                params.append(guild_id)
            if user_id:
                query += ' AND user_id = ?'
                params.append(user_id)
            if suspicious_only:
                query += ' AND is_suspicious = 1'

            query += ' ORDER BY created_at DESC LIMIT 1000'

            cursor = await self.connection.execute(query, params)
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    # ==================== BACKUPS ====================

    async def save_backup(self, guild_id: int, backup_data: Dict):
        """Save a backup to the database"""
        version = backup_data.get('version', 1)
        async with self._lock:
            await self.connection.execute('''
                INSERT INTO backups (guild_id, version, backup_data)
                VALUES (?, ?, ?)
                ON CONFLICT(guild_id, version) DO UPDATE SET
                    backup_data = excluded.backup_data,
                    created_at = CURRENT_TIMESTAMP
            ''', (guild_id, version, json.dumps(backup_data)))
            await self.connection.commit()

    async def get_backups(self, guild_id: int) -> List[Dict]:
        """Get all backups for a guild with full data"""
        async with self._lock:
            cursor = await self.connection.execute(
                'SELECT * FROM backups WHERE guild_id = ? ORDER BY version ASC',
                (guild_id,)
            )
            rows = await cursor.fetchall()
            result = []
            for row in rows:
                data = dict(row)
                if 'backup_data' in data and data['backup_data']:
                    try:
                        backup = json.loads(data['backup_data'])
                        backup['backup_id'] = data.get('id')
                        result.append(backup)
                    except json.JSONDecodeError:
                        pass
            return result

    async def get_backup(self, guild_id: int, version: int) -> Optional[Dict]:
        """Get a specific backup"""
        async with self._lock:
            cursor = await self.connection.execute(
                'SELECT * FROM backups WHERE guild_id = ? AND version = ?',
                (guild_id, version)
            )
            row = await cursor.fetchone()
            if row:
                data = dict(row)
                if 'backup_data' in data and data['backup_data']:
                    try:
                        backup = json.loads(data['backup_data'])
                        backup['backup_id'] = data.get('id')
                        return backup
                    except json.JSONDecodeError:
                        pass
            return None

    async def delete_backup(self, guild_id: int, version: int):
        """Delete a backup"""
        async with self._lock:
            await self.connection.execute(
                'DELETE FROM backups WHERE guild_id = ? AND version = ?',
                (guild_id, version)
            )
            await self.connection.commit()

    async def clear_backups(self, guild_id: int):
        """Clear all backups for a guild"""
        async with self._lock:
            await self.connection.execute(
                'DELETE FROM backups WHERE guild_id = ?',
                (guild_id,)
            )
            await self.connection.commit()

    # ==================== QUARANTINE ====================

    async def quarantine_user(self, guild_id: int, user_id: int,
                              original_roles: List[int], reason: str = None,
                              expires_at: str = None):
        """Add user to quarantine"""
        async with self._lock:
            await self.connection.execute('''
                INSERT INTO quarantine (guild_id, user_id, original_roles, reason, expires_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(guild_id, user_id) DO UPDATE SET
                    original_roles = excluded.original_roles,
                    reason = excluded.reason,
                    expires_at = excluded.expires_at,
                    quarantined_at = CURRENT_TIMESTAMP
            ''', (guild_id, user_id, json.dumps(original_roles), reason, expires_at))
            await self.connection.commit()

    async def get_quarantined_user(self, guild_id: int, user_id: int) -> Optional[Dict]:
        """Get quarantine info for a user"""
        async with self._lock:
            cursor = await self.connection.execute(
                'SELECT * FROM quarantine WHERE guild_id = ? AND user_id = ?',
                (guild_id, user_id)
            )
            row = await cursor.fetchone()
            if row:
                data = dict(row)
                data['original_roles'] = json.loads(data['original_roles'])
                return data
            return None

    async def release_from_quarantine(self, guild_id: int, user_id: int):
        """Remove user from quarantine"""
        async with self._lock:
            await self.connection.execute(
                'DELETE FROM quarantine WHERE guild_id = ? AND user_id = ?',
                (guild_id, user_id)
            )
            await self.connection.commit()

    # ==================== TRUSTED USERS ====================

    async def get_trusted_users(self, guild_id: int) -> List[int]:
        """Get all trusted user IDs for a guild"""
        async with self._lock:
            cursor = await self.connection.execute(
                'SELECT user_id FROM trusted_users WHERE guild_id = ?',
                (guild_id,)
            )
            rows = await cursor.fetchall()
            return [row['user_id'] for row in rows]

    async def add_trusted_user(self, guild_id: int, user_id: int):
        """Add a user to trusted list"""
        async with self._lock:
            await self.connection.execute('''
                INSERT INTO trusted_users (guild_id, user_id)
                VALUES (?, ?)
                ON CONFLICT(guild_id, user_id) DO NOTHING
            ''', (guild_id, user_id))
            await self.connection.commit()

    async def remove_trusted_user(self, guild_id: int, user_id: int):
        """Remove a user from trusted list"""
        async with self._lock:
            await self.connection.execute(
                'DELETE FROM trusted_users WHERE guild_id = ? AND user_id = ?',
                (guild_id, user_id)
            )
            await self.connection.commit()

    # ==================== TRUSTED BOTS ====================

    async def get_trusted_bots(self, guild_id: int) -> List[int]:
        """Get all trusted bot IDs for a guild"""
        async with self._lock:
            cursor = await self.connection.execute(
                'SELECT bot_id FROM trusted_bots WHERE guild_id = ?',
                (guild_id,)
            )
            rows = await cursor.fetchall()
            return [row['bot_id'] for row in rows]

    async def add_trusted_bot(self, guild_id: int, bot_id: int):
        """Add a bot to trusted list"""
        async with self._lock:
            await self.connection.execute('''
                INSERT INTO trusted_bots (guild_id, bot_id)
                VALUES (?, ?)
                ON CONFLICT(guild_id, bot_id) DO NOTHING
            ''', (guild_id, bot_id))
            await self.connection.commit()

    async def remove_trusted_bot(self, guild_id: int, bot_id: int):
        """Remove a bot from trusted list"""
        async with self._lock:
            await self.connection.execute(
                'DELETE FROM trusted_bots WHERE guild_id = ? AND bot_id = ?',
                (guild_id, bot_id)
            )
            await self.connection.commit()

    # ==================== WHITELISTED ROLES ====================

    async def get_whitelisted_roles(self, guild_id: int) -> List[Dict]:
        """Get all whitelisted roles for a guild"""
        async with self._lock:
            cursor = await self.connection.execute(
                'SELECT * FROM whitelisted_roles WHERE guild_id = ?',
                (guild_id,)
            )
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def add_whitelisted_role(self, guild_id: int, role_id: int, added_by: int, reason: str = None):
        """Add a role to whitelisted roles"""
        async with self._lock:
            await self.connection.execute('''
                INSERT INTO whitelisted_roles (guild_id, role_id, added_by, reason)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(guild_id, role_id) DO UPDATE SET
                    added_by = excluded.added_by,
                    reason = excluded.reason,
                    added_at = CURRENT_TIMESTAMP
            ''', (guild_id, role_id, added_by, reason))
            await self.connection.commit()

    async def remove_whitelisted_role(self, guild_id: int, role_id: int):
        """Remove a role from whitelisted roles"""
        async with self._lock:
            await self.connection.execute(
                'DELETE FROM whitelisted_roles WHERE guild_id = ? AND role_id = ?',
                (guild_id, role_id)
            )
            await self.connection.commit()

    async def clear_whitelisted_roles(self, guild_id: int):
        """Clear all whitelisted roles for a guild"""
        async with self._lock:
            await self.connection.execute(
                'DELETE FROM whitelisted_roles WHERE guild_id = ?',
                (guild_id,)
            )
            await self.connection.commit()

    # ==================== CHANNEL BACKUPS ====================

    async def get_channel_backups(self, guild_id: int) -> Dict[int, Dict]:
        """Get all channel backups for a guild"""
        async with self._lock:
            cursor = await self.connection.execute(
                'SELECT channel_id, channel_data FROM channel_backups WHERE guild_id = ?',
                (guild_id,)
            )
            rows = await cursor.fetchall()
            result = {}
            for row in rows:
                channel_id = row['channel_id']
                try:
                    result[channel_id] = json.loads(row['channel_data'])
                except:
                    pass
            return result

    async def save_channel_backup(self, guild_id: int, channel_id: int, channel_data: Dict):
        """Save a channel backup"""
        async with self._lock:
            await self.connection.execute('''
                INSERT INTO channel_backups (guild_id, channel_id, channel_data, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(guild_id, channel_id) DO UPDATE SET
                    channel_data = excluded.channel_data,
                    updated_at = excluded.updated_at
            ''', (guild_id, channel_id, json.dumps(channel_data), datetime.utcnow().isoformat()))
            await self.connection.commit()

    async def save_channel_backups_bulk(self, guild_id: int, backups: Dict[int, Dict]):
        """Save multiple channel backups at once"""
        async with self._lock:
            for channel_id, channel_data in backups.items():
                await self.connection.execute('''
                    INSERT INTO channel_backups (guild_id, channel_id, channel_data, updated_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(guild_id, channel_id) DO UPDATE SET
                        channel_data = excluded.channel_data,
                        updated_at = excluded.updated_at
                ''', (guild_id, channel_id, json.dumps(channel_data), datetime.utcnow().isoformat()))
            await self.connection.commit()

    async def delete_channel_backup(self, guild_id: int, channel_id: int):
        """Delete a channel backup"""
        async with self._lock:
            await self.connection.execute(
                'DELETE FROM channel_backups WHERE guild_id = ? AND channel_id = ?',
                (guild_id, channel_id)
            )
            await self.connection.commit()

    async def clear_channel_backups(self, guild_id: int):
        """Clear all channel backups for a guild"""
        async with self._lock:
            await self.connection.execute(
                'DELETE FROM channel_backups WHERE guild_id = ?',
                (guild_id,)
            )
            await self.connection.commit()


# Global database instance
db: Optional[Database] = None

async def init_database():
    """Initialize the global database instance"""
    global db
    db = Database()
    await db.connect()
    return db

async def get_database() -> Database:
    """Get the global database instance"""
    global db
    if db is None:
        db = await init_database()
    return db
