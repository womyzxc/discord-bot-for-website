"""
PostgreSQL Database Module
==========================
Production-ready PostgreSQL database handler with:
- Connection pooling
- Async operations
- All the same functionality as SQLite
"""

import asyncpg
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
import os

logger = logging.getLogger('Offcialx.PostgreSQL')

class PostgresDatabase:
    """Async PostgreSQL database handler with connection pooling"""

    def __init__(self, database_url: str = None):
        self.database_url = database_url or os.getenv('DATABASE_URL', '')
        self.pool: Optional[asyncpg.Pool] = None
        self._lock = asyncio.Lock()

        # Connection pool settings
        self.MIN_POOL_SIZE = 5   # Minimum connections to keep open
        self.MAX_POOL_SIZE = 20  # Maximum connections during high load
        self.COMMAND_TIMEOUT = 30  # Timeout for queries (seconds)
        self.MAX_RETRIES = 3     # Retry failed operations

    async def connect(self):
        """Connect to the database with connection pooling"""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=self.MIN_POOL_SIZE,
                max_size=self.MAX_POOL_SIZE,
                command_timeout=self.COMMAND_TIMEOUT,
                max_inactive_connection_lifetime=300,  # Close idle connections after 5 min
            )

            # Create tables
            await self._create_tables()

            logger.info(f'Connected to PostgreSQL (pool: {self.MIN_POOL_SIZE}-{self.MAX_POOL_SIZE} connections)')
        except Exception as e:
            logger.error(f'Failed to connect to PostgreSQL: {e}')
            raise

    async def close(self):
        """Close the connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info('PostgreSQL connection pool closed')

    async def health_check(self) -> bool:
        """Check if database connection is healthy"""
        try:
            async with self.pool.acquire() as conn:
                await conn.fetchval('SELECT 1')
            return True
        except Exception as e:
            logger.error(f'Database health check failed: {e}')
            return False

    def get_pool_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        if not self.pool:
            return {'status': 'disconnected'}
        return {
            'status': 'connected',
            'size': self.pool.get_size(),
            'free_size': self.pool.get_idle_size(),
            'min_size': self.pool.get_min_size(),
            'max_size': self.pool.get_max_size(),
        }

    async def _execute_with_retry(self, operation, *args, **kwargs):
        """Execute a database operation with retry logic"""
        last_error = None
        for attempt in range(self.MAX_RETRIES):
            try:
                return await operation(*args, **kwargs)
            except asyncpg.InterfaceError as e:
                # Connection issues - wait and retry
                last_error = e
                logger.warning(f'Database connection error (attempt {attempt+1}): {e}')
                await asyncio.sleep(0.5 * (attempt + 1))
            except asyncpg.PostgresError as e:
                # PostgreSQL errors - log and retry for transient issues
                last_error = e
                if 'deadlock' in str(e).lower() or 'serialization' in str(e).lower():
                    logger.warning(f'Database contention (attempt {attempt+1}): {e}')
                    await asyncio.sleep(0.1 * (attempt + 1))
                else:
                    raise  # Non-transient error, don't retry
            except Exception as e:
                logger.error(f'Unexpected database error: {e}')
                raise

        # All retries failed
        raise last_error

    async def _create_tables(self):
        """Create all required tables"""
        async with self.pool.acquire() as conn:
            # Guild settings table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS guild_settings (
                    id SERIAL PRIMARY KEY,
                    guild_id BIGINT NOT NULL,
                    module VARCHAR(50) NOT NULL,
                    settings JSONB NOT NULL DEFAULT '{}',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(guild_id, module)
                )
            ''')

            # Create index
            await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_guild_settings_guild
                ON guild_settings(guild_id)
            ''')

            # Whitelist table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS whitelist (
                    id SERIAL PRIMARY KEY,
                    guild_id BIGINT NOT NULL,
                    user_id BIGINT NOT NULL,
                    level VARCHAR(20) NOT NULL,
                    added_by BIGINT NOT NULL,
                    reason TEXT,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(guild_id, user_id)
                )
            ''')

            # Warnings table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS warnings (
                    id SERIAL PRIMARY KEY,
                    guild_id BIGINT NOT NULL,
                    user_id BIGINT NOT NULL,
                    moderator_id BIGINT NOT NULL,
                    reason TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_warnings_user
                ON warnings(guild_id, user_id)
            ''')

            # Security logs table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS security_logs (
                    id SERIAL PRIMARY KEY,
                    guild_id BIGINT NOT NULL,
                    event_type VARCHAR(50) NOT NULL,
                    user_id BIGINT,
                    target_id BIGINT,
                    action VARCHAR(50),
                    details TEXT,
                    severity VARCHAR(20) DEFAULT 'info',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_security_logs_guild
                ON security_logs(guild_id, created_at DESC)
            ''')

            # Threat intelligence table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS threat_intel (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    threat_type VARCHAR(50) NOT NULL,
                    threat_score INTEGER DEFAULT 0,
                    evidence TEXT,
                    guild_ids JSONB DEFAULT '[]',
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, threat_type)
                )
            ''')

            await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_threat_intel_user
                ON threat_intel(user_id)
            ''')

            await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_threat_intel_score
                ON threat_intel(threat_score DESC)
            ''')

            # Action patterns table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS action_patterns (
                    id SERIAL PRIMARY KEY,
                    guild_id BIGINT NOT NULL,
                    user_id BIGINT NOT NULL,
                    action_type VARCHAR(50) NOT NULL,
                    action_count INTEGER DEFAULT 1,
                    timeframe INTEGER NOT NULL,
                    pattern_hash VARCHAR(64),
                    is_suspicious BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Backups table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS backups (
                    id SERIAL PRIMARY KEY,
                    guild_id BIGINT NOT NULL,
                    version INTEGER NOT NULL,
                    backup_data JSONB NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(guild_id, version)
                )
            ''')

            # Quarantine table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS quarantine (
                    id SERIAL PRIMARY KEY,
                    guild_id BIGINT NOT NULL,
                    user_id BIGINT NOT NULL,
                    original_roles JSONB,
                    reason TEXT,
                    quarantined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    UNIQUE(guild_id, user_id)
                )
            ''')

            # API tokens table (for web dashboard)
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS api_tokens (
                    id SERIAL PRIMARY KEY,
                    guild_id BIGINT NOT NULL,
                    user_id BIGINT NOT NULL,
                    token_hash VARCHAR(64) NOT NULL UNIQUE,
                    permissions JSONB DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    last_used TIMESTAMP
                )
            ''')

            # Trusted users table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS trusted_users (
                    id SERIAL PRIMARY KEY,
                    guild_id BIGINT NOT NULL,
                    user_id BIGINT NOT NULL,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(guild_id, user_id)
                )
            ''')

            # Trusted bots table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS trusted_bots (
                    id SERIAL PRIMARY KEY,
                    guild_id BIGINT NOT NULL,
                    bot_id BIGINT NOT NULL,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(guild_id, bot_id)
                )
            ''')

            # Whitelisted roles table
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS whitelisted_roles (
                    id SERIAL PRIMARY KEY,
                    guild_id BIGINT NOT NULL,
                    role_id BIGINT NOT NULL,
                    added_by BIGINT NOT NULL DEFAULT 0,
                    reason TEXT,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(guild_id, role_id)
                )
            ''')

            # Channel backups table (for anti-nuke restore)
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS channel_backups (
                    id SERIAL PRIMARY KEY,
                    guild_id BIGINT NOT NULL,
                    channel_id BIGINT NOT NULL,
                    channel_data JSONB NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(guild_id, channel_id)
                )
            ''')

            await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_channel_backups_guild
                ON channel_backups(guild_id)
            ''')

            # Bot global settings (status, activity, log channels)
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS bot_settings (
                    key VARCHAR(100) PRIMARY KEY,
                    value JSONB NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Server settings backup (name, icon, banner, etc.)
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS server_settings_backup (
                    guild_id BIGINT PRIMARY KEY,
                    settings_data JSONB NOT NULL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Trusted roles (bypass anti-nuke checks)
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS trusted_roles (
                    id SERIAL PRIMARY KEY,
                    guild_id BIGINT NOT NULL,
                    role_id BIGINT NOT NULL,
                    added_by BIGINT,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(guild_id, role_id)
                )
            ''')

            # Honeypots table (trap channels/roles for attackers)
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS honeypots (
                    id SERIAL PRIMARY KEY,
                    guild_id BIGINT NOT NULL,
                    item_id BIGINT NOT NULL,
                    item_type VARCHAR(20) NOT NULL,
                    created_by BIGINT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(guild_id, item_id, item_type)
                )
            ''')

            await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_honeypots_guild
                ON honeypots(guild_id)
            ''')

            # Honeypot triggers (log who triggered honeypots)
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS honeypot_triggers (
                    id SERIAL PRIMARY KEY,
                    guild_id BIGINT NOT NULL,
                    user_id BIGINT NOT NULL,
                    honeypot_id BIGINT NOT NULL,
                    action_taken VARCHAR(50),
                    triggered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Selfbot detection tracking
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS selfbot_tracking (
                    id SERIAL PRIMARY KEY,
                    guild_id BIGINT NOT NULL,
                    user_id BIGINT NOT NULL,
                    suspicion_score INTEGER DEFAULT 0,
                    fast_reactions INTEGER DEFAULT 0,
                    nitro_attempts INTEGER DEFAULT 0,
                    selfbot_commands INTEGER DEFAULT 0,
                    flagged BOOLEAN DEFAULT FALSE,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(guild_id, user_id)
                )
            ''')

            # Ban velocity tracking (for mass ban detection)
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS ban_velocity (
                    id SERIAL PRIMARY KEY,
                    guild_id BIGINT NOT NULL,
                    actor_id BIGINT NOT NULL,
                    target_id BIGINT NOT NULL,
                    action_type VARCHAR(20) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            await conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_ban_velocity_guild_actor
                ON ban_velocity(guild_id, actor_id, created_at DESC)
            ''')

            logger.info('PostgreSQL tables created/verified')

    # ==================== GUILD SETTINGS ====================

    def _parse_json_settings(self, data) -> Optional[Dict]:
        """Safely parse JSON settings from database"""
        if data is None:
            return None
        if isinstance(data, dict):
            return data
        if isinstance(data, str):
            try:
                return json.loads(data)
            except (json.JSONDecodeError, TypeError):
                return None
        # asyncpg might return as Record or other types
        try:
            return dict(data)
        except (TypeError, ValueError):
            return None

    async def get_guild_settings(self, guild_id: int, module: str) -> Optional[Dict]:
        """Get settings for a guild module"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                'SELECT settings FROM guild_settings WHERE guild_id = $1 AND module = $2',
                guild_id, module
            )
            if not row:
                return None
            return self._parse_json_settings(row['settings'])

    async def save_guild_settings(self, guild_id: int, module: str, settings: Dict):
        """Save settings for a guild module"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO guild_settings (guild_id, module, settings, updated_at)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (guild_id, module) DO UPDATE SET
                    settings = $3,
                    updated_at = $4
            ''', guild_id, module, json.dumps(settings), datetime.utcnow())

    async def get_all_guild_settings(self, guild_id: int) -> Dict[str, Dict]:
        """Get all settings for a guild"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                'SELECT module, settings FROM guild_settings WHERE guild_id = $1',
                guild_id
            )
            result = {}
            for row in rows:
                parsed = self._parse_json_settings(row['settings'])
                if parsed:
                    result[row['module']] = parsed
            return result

    async def delete_guild_settings(self, guild_id: int, module: str = None):
        """Delete settings for a guild"""
        async with self.pool.acquire() as conn:
            if module:
                await conn.execute(
                    'DELETE FROM guild_settings WHERE guild_id = $1 AND module = $2',
                    guild_id, module
                )
            else:
                await conn.execute(
                    'DELETE FROM guild_settings WHERE guild_id = $1',
                    guild_id
                )

    # ==================== WHITELIST ====================

    async def get_whitelist(self, guild_id: int) -> List[Dict]:
        """Get all whitelist entries for a guild"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                'SELECT * FROM whitelist WHERE guild_id = $1',
                guild_id
            )
            return [dict(row) for row in rows]

    async def get_whitelist_entry(self, guild_id: int, user_id: int) -> Optional[Dict]:
        """Get a specific whitelist entry"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                'SELECT * FROM whitelist WHERE guild_id = $1 AND user_id = $2',
                guild_id, user_id
            )
            return dict(row) if row else None

    async def add_to_whitelist(self, guild_id: int, user_id: int, level: str,
                               added_by: int, reason: str = None):
        """Add user to whitelist"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO whitelist (guild_id, user_id, level, added_by, reason)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (guild_id, user_id) DO UPDATE SET
                    level = $3,
                    added_by = $4,
                    reason = $5,
                    added_at = CURRENT_TIMESTAMP
            ''', guild_id, user_id, level, added_by, reason)

    async def remove_from_whitelist(self, guild_id: int, user_id: int):
        """Remove user from whitelist"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                'DELETE FROM whitelist WHERE guild_id = $1 AND user_id = $2',
                guild_id, user_id
            )

    # ==================== WARNINGS ====================

    async def get_warnings(self, guild_id: int, user_id: int) -> List[Dict]:
        """Get warnings for a user"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                '''SELECT * FROM warnings
                   WHERE guild_id = $1 AND user_id = $2
                   ORDER BY created_at DESC''',
                guild_id, user_id
            )
            return [dict(row) for row in rows]

    async def add_warning(self, guild_id: int, user_id: int, moderator_id: int, reason: str):
        """Add a warning"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO warnings (guild_id, user_id, moderator_id, reason)
                VALUES ($1, $2, $3, $4)
            ''', guild_id, user_id, moderator_id, reason)

    async def clear_warnings(self, guild_id: int, user_id: int):
        """Clear warnings for a user"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                'DELETE FROM warnings WHERE guild_id = $1 AND user_id = $2',
                guild_id, user_id
            )

    async def get_warning_count(self, guild_id: int, user_id: int) -> int:
        """Get warning count for a user"""
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(
                'SELECT COUNT(*) FROM warnings WHERE guild_id = $1 AND user_id = $2',
                guild_id, user_id
            )
            return result or 0

    # ==================== SECURITY LOGS ====================

    async def log_security_event(self, guild_id: int, event_type: str,
                                 user_id: int = None, target_id: int = None,
                                 action: str = None, details: str = None,
                                 severity: str = 'info'):
        """Log a security event"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO security_logs
                (guild_id, event_type, user_id, target_id, action, details, severity)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            ''', guild_id, event_type, user_id, target_id, action, details, severity)

    async def get_security_logs(self, guild_id: int, limit: int = 100,
                                event_type: str = None) -> List[Dict]:
        """Get security logs for a guild"""
        async with self.pool.acquire() as conn:
            if event_type:
                rows = await conn.fetch('''
                    SELECT * FROM security_logs
                    WHERE guild_id = $1 AND event_type = $2
                    ORDER BY created_at DESC LIMIT $3
                ''', guild_id, event_type, limit)
            else:
                rows = await conn.fetch('''
                    SELECT * FROM security_logs
                    WHERE guild_id = $1
                    ORDER BY created_at DESC LIMIT $2
                ''', guild_id, limit)

            return [dict(row) for row in rows]

    # ==================== THREAT INTELLIGENCE ====================

    async def add_threat_intel(self, user_id: int, threat_type: str,
                               threat_score: int, evidence: str = None,
                               guild_id: int = None):
        """Add or update threat intelligence"""
        async with self.pool.acquire() as conn:
            # Get existing entry
            existing = await conn.fetchrow(
                'SELECT * FROM threat_intel WHERE user_id = $1 AND threat_type = $2',
                user_id, threat_type
            )

            if existing:
                existing_guilds = list(existing['guild_ids']) if existing['guild_ids'] else []
                if guild_id and guild_id not in existing_guilds:
                    existing_guilds.append(guild_id)

                new_score = min(existing['threat_score'] + threat_score, 1000)

                await conn.execute('''
                    UPDATE threat_intel
                    SET threat_score = $1, evidence = $2, guild_ids = $3, last_seen = $4
                    WHERE user_id = $5 AND threat_type = $6
                ''', new_score, evidence, json.dumps(existing_guilds),
                   datetime.utcnow(), user_id, threat_type)
            else:
                guild_ids = json.dumps([guild_id] if guild_id else [])
                await conn.execute('''
                    INSERT INTO threat_intel
                    (user_id, threat_type, threat_score, evidence, guild_ids)
                    VALUES ($1, $2, $3, $4, $5)
                ''', user_id, threat_type, threat_score, evidence, guild_ids)

    async def get_threat_intel(self, user_id: int) -> List[Dict]:
        """Get threat intelligence for a user"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                'SELECT * FROM threat_intel WHERE user_id = $1',
                user_id
            )
            return [dict(row) for row in rows]

    async def get_threat_score(self, user_id: int) -> int:
        """Get total threat score for a user"""
        async with self.pool.acquire() as conn:
            result = await conn.fetchval(
                'SELECT COALESCE(SUM(threat_score), 0) FROM threat_intel WHERE user_id = $1',
                user_id
            )
            return result or 0

    async def get_known_threats(self, min_score: int = 50) -> List[Dict]:
        """Get all known threats above a minimum score"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT user_id, SUM(threat_score) as total_score,
                       array_agg(threat_type) as threat_types
                FROM threat_intel
                GROUP BY user_id
                HAVING SUM(threat_score) >= $1
                ORDER BY total_score DESC
            ''', min_score)
            return [dict(row) for row in rows]

    # ==================== API TOKENS ====================

    async def create_api_token(self, guild_id: int, user_id: int,
                               token_hash: str, permissions: List[str],
                               expires_at: datetime = None):
        """Create an API token for web dashboard"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO api_tokens
                (guild_id, user_id, token_hash, permissions, expires_at)
                VALUES ($1, $2, $3, $4, $5)
            ''', guild_id, user_id, token_hash, json.dumps(permissions), expires_at)

    async def validate_api_token(self, token_hash: str) -> Optional[Dict]:
        """Validate an API token"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('''
                SELECT * FROM api_tokens
                WHERE token_hash = $1
                AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
            ''', token_hash)

            if row:
                # Update last used
                await conn.execute(
                    'UPDATE api_tokens SET last_used = CURRENT_TIMESTAMP WHERE id = $1',
                    row['id']
                )
                return dict(row)
            return None

    async def revoke_api_token(self, token_hash: str):
        """Revoke an API token"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                'DELETE FROM api_tokens WHERE token_hash = $1',
                token_hash
            )

    # ==================== TRUSTED USERS ====================

    async def get_trusted_users(self, guild_id: int) -> List[int]:
        """Get all trusted user IDs for a guild"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                'SELECT user_id FROM trusted_users WHERE guild_id = $1',
                guild_id
            )
            return [row['user_id'] for row in rows]

    async def add_trusted_user(self, guild_id: int, user_id: int):
        """Add a user to trusted users"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO trusted_users (guild_id, user_id)
                VALUES ($1, $2)
                ON CONFLICT (guild_id, user_id) DO NOTHING
            ''', guild_id, user_id)

    async def remove_trusted_user(self, guild_id: int, user_id: int):
        """Remove a user from trusted users"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                'DELETE FROM trusted_users WHERE guild_id = $1 AND user_id = $2',
                guild_id, user_id
            )

    # ==================== TRUSTED BOTS ====================

    async def get_trusted_bots(self, guild_id: int) -> List[int]:
        """Get all trusted bot IDs for a guild"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                'SELECT bot_id FROM trusted_bots WHERE guild_id = $1',
                guild_id
            )
            return [row['bot_id'] for row in rows]

    async def add_trusted_bot(self, guild_id: int, bot_id: int):
        """Add a bot to trusted bots"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO trusted_bots (guild_id, bot_id)
                VALUES ($1, $2)
                ON CONFLICT (guild_id, bot_id) DO NOTHING
            ''', guild_id, bot_id)

    async def remove_trusted_bot(self, guild_id: int, bot_id: int):
        """Remove a bot from trusted bots"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                'DELETE FROM trusted_bots WHERE guild_id = $1 AND bot_id = $2',
                guild_id, bot_id
            )

    # ==================== WHITELISTED ROLES ====================

    async def get_whitelisted_roles(self, guild_id: int) -> List[Dict]:
        """Get all whitelisted roles for a guild"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                'SELECT * FROM whitelisted_roles WHERE guild_id = $1',
                guild_id
            )
            return [dict(row) for row in rows]

    async def add_whitelisted_role(self, guild_id: int, role_id: int, added_by: int = 0, reason: str = None):
        """Add a role to whitelisted roles"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO whitelisted_roles (guild_id, role_id, added_by, reason)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (guild_id, role_id) DO UPDATE SET
                    added_by = $3,
                    reason = $4,
                    added_at = CURRENT_TIMESTAMP
            ''', guild_id, role_id, added_by, reason)

    async def remove_whitelisted_role(self, guild_id: int, role_id: int):
        """Remove a role from whitelisted roles"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                'DELETE FROM whitelisted_roles WHERE guild_id = $1 AND role_id = $2',
                guild_id, role_id
            )

    # ==================== TRUSTED ROLES ====================

    async def get_trusted_roles(self, guild_id: int) -> List[int]:
        """Get all trusted role IDs for a guild"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                'SELECT role_id FROM trusted_roles WHERE guild_id = $1',
                guild_id
            )
            return [row['role_id'] for row in rows]

    async def add_trusted_role(self, guild_id: int, role_id: int, added_by: int = 0):
        """Add a role to trusted roles"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO trusted_roles (guild_id, role_id, added_by)
                VALUES ($1, $2, $3)
                ON CONFLICT (guild_id, role_id) DO NOTHING
            ''', guild_id, role_id, added_by)

    async def remove_trusted_role(self, guild_id: int, role_id: int):
        """Remove a role from trusted roles"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                'DELETE FROM trusted_roles WHERE guild_id = $1 AND role_id = $2',
                guild_id, role_id
            )

    # ==================== CHANNEL BACKUPS ====================

    async def get_channel_backups(self, guild_id: int) -> Dict[int, Dict]:
        """Get all channel backups for a guild"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                'SELECT channel_id, channel_data FROM channel_backups WHERE guild_id = $1',
                guild_id
            )
            result = {}
            for row in rows:
                channel_id = row['channel_id']
                data = row['channel_data']
                if isinstance(data, dict):
                    result[channel_id] = data
                elif isinstance(data, str):
                    try:
                        result[channel_id] = json.loads(data)
                    except json.JSONDecodeError as e:
                        logger.warning(f'Failed to parse channel backup JSON for {channel_id}: {e}')
                    except Exception as e:
                        logger.error(f'Unexpected error parsing channel backup for {channel_id}: {e}')
            return result

    async def save_channel_backup(self, guild_id: int, channel_id: int, channel_data: Dict):
        """Save a channel backup"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO channel_backups (guild_id, channel_id, channel_data, updated_at)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (guild_id, channel_id) DO UPDATE SET
                    channel_data = $3,
                    updated_at = $4
            ''', guild_id, channel_id, json.dumps(channel_data), datetime.utcnow())

    async def save_channel_backups_bulk(self, guild_id: int, backups: Dict[int, Dict]):
        """Save multiple channel backups at once"""
        async with self.pool.acquire() as conn:
            for channel_id, channel_data in backups.items():
                await conn.execute('''
                    INSERT INTO channel_backups (guild_id, channel_id, channel_data, updated_at)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (guild_id, channel_id) DO UPDATE SET
                        channel_data = $3,
                        updated_at = $4
                ''', guild_id, channel_id, json.dumps(channel_data), datetime.utcnow())

    async def delete_channel_backup(self, guild_id: int, channel_id: int):
        """Delete a channel backup"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                'DELETE FROM channel_backups WHERE guild_id = $1 AND channel_id = $2',
                guild_id, channel_id
            )

    async def clear_channel_backups(self, guild_id: int):
        """Clear all channel backups for a guild"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                'DELETE FROM channel_backups WHERE guild_id = $1',
                guild_id
            )

    # ==================== BOT SETTINGS ====================

    async def get_bot_setting(self, key: str) -> Optional[Dict]:
        """Get a bot setting by key"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                'SELECT value FROM bot_settings WHERE key = $1',
                key
            )
            if row:
                return self._parse_json_settings(row['value'])
            return None

    async def save_bot_setting(self, key: str, value: Dict):
        """Save a bot setting"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO bot_settings (key, value, updated_at)
                VALUES ($1, $2, $3)
                ON CONFLICT (key) DO UPDATE SET
                    value = $2,
                    updated_at = $3
            ''', key, json.dumps(value), datetime.utcnow())

    async def delete_bot_setting(self, key: str):
        """Delete a bot setting"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                'DELETE FROM bot_settings WHERE key = $1',
                key
            )

    async def get_all_bot_settings(self) -> Dict[str, Dict]:
        """Get all bot settings"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('SELECT key, value FROM bot_settings')
            result = {}
            for row in rows:
                parsed = self._parse_json_settings(row['value'])
                if parsed:
                    result[row['key']] = parsed
            return result

    # ==================== SERVER SETTINGS BACKUP ====================

    async def get_server_settings_backup(self, guild_id: int) -> Optional[Dict]:
        """Get server settings backup for a guild"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                'SELECT settings_data FROM server_settings_backup WHERE guild_id = $1',
                guild_id
            )
            if row:
                return self._parse_json_settings(row['settings_data'])
            return None

    async def save_server_settings_backup(self, guild_id: int, settings_data: Dict):
        """Save server settings backup"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO server_settings_backup (guild_id, settings_data, updated_at)
                VALUES ($1, $2, $3)
                ON CONFLICT (guild_id) DO UPDATE SET
                    settings_data = $2,
                    updated_at = $3
            ''', guild_id, json.dumps(settings_data), datetime.utcnow())

    async def delete_server_settings_backup(self, guild_id: int):
        """Delete server settings backup for a guild"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                'DELETE FROM server_settings_backup WHERE guild_id = $1',
                guild_id
            )

    async def get_all_server_settings_backups(self) -> Dict[int, Dict]:
        """Get all server settings backups"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('SELECT guild_id, settings_data FROM server_settings_backup')
            result = {}
            for row in rows:
                parsed = self._parse_json_settings(row['settings_data'])
                if parsed:
                    result[row['guild_id']] = parsed
            return result


    # ==================== HONEYPOTS ====================

    async def get_honeypots(self, guild_id: int, item_type: str = None) -> List[Dict]:
        """Get all honeypots for a guild"""
        async with self.pool.acquire() as conn:
            if item_type:
                rows = await conn.fetch(
                    'SELECT * FROM honeypots WHERE guild_id = $1 AND item_type = $2',
                    guild_id, item_type
                )
            else:
                rows = await conn.fetch(
                    'SELECT * FROM honeypots WHERE guild_id = $1',
                    guild_id
                )
            return [dict(row) for row in rows]

    async def add_honeypot(self, guild_id: int, item_id: int, item_type: str, created_by: int = None):
        """Add a honeypot channel or role"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO honeypots (guild_id, item_id, item_type, created_by)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (guild_id, item_id, item_type) DO NOTHING
            ''', guild_id, item_id, item_type, created_by)

    async def remove_honeypot(self, guild_id: int, item_id: int, item_type: str = None):
        """Remove a honeypot"""
        async with self.pool.acquire() as conn:
            if item_type:
                await conn.execute(
                    'DELETE FROM honeypots WHERE guild_id = $1 AND item_id = $2 AND item_type = $3',
                    guild_id, item_id, item_type
                )
            else:
                await conn.execute(
                    'DELETE FROM honeypots WHERE guild_id = $1 AND item_id = $2',
                    guild_id, item_id
                )

    async def log_honeypot_trigger(self, guild_id: int, user_id: int, honeypot_id: int, action_taken: str):
        """Log when a user triggers a honeypot"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO honeypot_triggers (guild_id, user_id, honeypot_id, action_taken)
                VALUES ($1, $2, $3, $4)
            ''', guild_id, user_id, honeypot_id, action_taken)

    async def get_honeypot_triggers(self, guild_id: int, limit: int = 50) -> List[Dict]:
        """Get honeypot trigger history"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT * FROM honeypot_triggers
                WHERE guild_id = $1
                ORDER BY triggered_at DESC
                LIMIT $2
            ''', guild_id, limit)
            return [dict(row) for row in rows]

    # ==================== SELFBOT TRACKING ====================

    async def get_selfbot_tracking(self, guild_id: int, user_id: int) -> Optional[Dict]:
        """Get selfbot tracking data for a user"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                'SELECT * FROM selfbot_tracking WHERE guild_id = $1 AND user_id = $2',
                guild_id, user_id
            )
            return dict(row) if row else None

    async def update_selfbot_tracking(self, guild_id: int, user_id: int,
                                       suspicion_score: int = None,
                                       fast_reactions: int = None,
                                       nitro_attempts: int = None,
                                       selfbot_commands: int = None,
                                       flagged: bool = None):
        """Update selfbot tracking data"""
        async with self.pool.acquire() as conn:
            # Get existing or create new
            existing = await self.get_selfbot_tracking(guild_id, user_id)

            if existing:
                updates = []
                values = [guild_id, user_id]
                idx = 3

                if suspicion_score is not None:
                    updates.append(f'suspicion_score = ${idx}')
                    values.append(suspicion_score)
                    idx += 1
                if fast_reactions is not None:
                    updates.append(f'fast_reactions = ${idx}')
                    values.append(fast_reactions)
                    idx += 1
                if nitro_attempts is not None:
                    updates.append(f'nitro_attempts = ${idx}')
                    values.append(nitro_attempts)
                    idx += 1
                if selfbot_commands is not None:
                    updates.append(f'selfbot_commands = ${idx}')
                    values.append(selfbot_commands)
                    idx += 1
                if flagged is not None:
                    updates.append(f'flagged = ${idx}')
                    values.append(flagged)
                    idx += 1

                updates.append('last_updated = CURRENT_TIMESTAMP')

                if updates:
                    query = f'''
                        UPDATE selfbot_tracking
                        SET {', '.join(updates)}
                        WHERE guild_id = $1 AND user_id = $2
                    '''
                    await conn.execute(query, *values)
            else:
                await conn.execute('''
                    INSERT INTO selfbot_tracking
                    (guild_id, user_id, suspicion_score, fast_reactions, nitro_attempts, selfbot_commands, flagged)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                ''', guild_id, user_id,
                   suspicion_score or 0,
                   fast_reactions or 0,
                   nitro_attempts or 0,
                   selfbot_commands or 0,
                   flagged or False)

    async def clear_selfbot_tracking(self, guild_id: int, user_id: int):
        """Clear selfbot tracking for a user"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                'DELETE FROM selfbot_tracking WHERE guild_id = $1 AND user_id = $2',
                guild_id, user_id
            )

    async def get_flagged_selfbots(self, guild_id: int) -> List[Dict]:
        """Get all flagged selfbot users in a guild"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                'SELECT * FROM selfbot_tracking WHERE guild_id = $1 AND flagged = TRUE ORDER BY suspicion_score DESC',
                guild_id
            )
            return [dict(row) for row in rows]

    # ==================== BACKUPS ====================

    async def get_backups(self, guild_id: int) -> List[Dict]:
        """Get all backups for a guild"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                'SELECT * FROM backups WHERE guild_id = $1 ORDER BY version ASC',
                guild_id
            )
            result = []
            for row in rows:
                backup_data = row['backup_data']
                if isinstance(backup_data, dict):
                    backup_data['backup_id'] = row['id']
                    result.append(backup_data)
                elif isinstance(backup_data, str):
                    try:
                        parsed = json.loads(backup_data)
                        parsed['backup_id'] = row['id']
                        result.append(parsed)
                    except json.JSONDecodeError:
                        pass
            return result

    async def save_backup(self, guild_id: int, backup_data: Dict):
        """Save a backup to the database"""
        version = backup_data.get('version', 1)
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO backups (guild_id, version, backup_data, created_at)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (guild_id, version) DO UPDATE SET
                    backup_data = $3,
                    created_at = $4
            ''', guild_id, version, json.dumps(backup_data), datetime.utcnow())

    async def delete_backup(self, guild_id: int, version: int):
        """Delete a backup from the database"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                'DELETE FROM backups WHERE guild_id = $1 AND version = $2',
                guild_id, version
            )

    async def clear_backups(self, guild_id: int):
        """Clear all backups for a guild"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                'DELETE FROM backups WHERE guild_id = $1',
                guild_id
            )

    async def get_backup_by_version(self, guild_id: int, version: int) -> Optional[Dict]:
        """Get a specific backup by version"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                'SELECT * FROM backups WHERE guild_id = $1 AND version = $2',
                guild_id, version
            )
            if row:
                backup_data = row['backup_data']
                if isinstance(backup_data, dict):
                    backup_data['backup_id'] = row['id']
                    return backup_data
                elif isinstance(backup_data, str):
                    try:
                        parsed = json.loads(backup_data)
                        parsed['backup_id'] = row['id']
                        return parsed
                    except json.JSONDecodeError:
                        pass
            return None

    # ==================== WHITELISTED ROLES CLEAR ====================

    async def clear_whitelisted_roles(self, guild_id: int):
        """Clear all whitelisted roles for a guild"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                'DELETE FROM whitelisted_roles WHERE guild_id = $1',
                guild_id
            )

    # ==================== BAN VELOCITY TRACKING ====================

    async def record_ban_action(self, guild_id: int, actor_id: int, target_id: int, action_type: str = 'ban'):
        """Record a ban/kick action for velocity tracking"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO ban_velocity (guild_id, actor_id, target_id, action_type)
                VALUES ($1, $2, $3, $4)
            ''', guild_id, actor_id, target_id, action_type)

    async def get_ban_velocity(self, guild_id: int, actor_id: int, seconds: int = 60) -> int:
        """Get number of bans by an actor in the last N seconds"""
        async with self.pool.acquire() as conn:
            count = await conn.fetchval('''
                SELECT COUNT(*) FROM ban_velocity
                WHERE guild_id = $1 AND actor_id = $2
                AND created_at > NOW() - INTERVAL '%s seconds'
            ''' % seconds, guild_id, actor_id)
            return count or 0

    async def cleanup_old_ban_velocity(self, hours: int = 24):
        """Clean up old ban velocity records"""
        async with self.pool.acquire() as conn:
            await conn.execute('''
                DELETE FROM ban_velocity
                WHERE created_at < NOW() - INTERVAL '%s hours'
            ''' % hours)


# Factory function to get the right database
async def get_database():
    """Get the appropriate database based on environment"""
    database_url = os.getenv('DATABASE_URL', '')

    if database_url.startswith('postgresql://') or database_url.startswith('postgres://'):
        db = PostgresDatabase(database_url)
        await db.connect()
        return db
    else:
        # Fall back to SQLite
        from .db import Database, init_database
        return await init_database()
