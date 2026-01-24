"""
Audit Log Cache
================
Caches audit log entries to prevent rate limiting during attacks.
Discord rate limits audit log requests to ~10 per 10 seconds.
During a nuke attack with 50+ events, this cache prevents hitting those limits.
"""

import discord
import asyncio
import logging
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Optional, Any

logger = logging.getLogger('Offcialx.AuditCache')


class AuditLogCache:
    """
    Caches audit log entries to prevent rate limiting.

    Instead of fetching audit logs for every event, we:
    1. Fetch once and cache for 2 seconds
    2. All concurrent event handlers share the cached data
    3. Automatically refresh when cache expires
    """

    def __init__(self, bot):
        self.bot = bot
        self.cache: Dict[int, List[discord.AuditLogEntry]] = {}  # guild_id -> entries
        self.cache_time: Dict[int, datetime] = {}  # guild_id -> last fetch time
        self.locks: Dict[int, asyncio.Lock] = defaultdict(asyncio.Lock)  # guild_id -> lock
        self.CACHE_DURATION = 2.0  # seconds - short enough to catch attackers, long enough to prevent spam
        self.MAX_ENTRIES = 25  # entries to fetch per refresh

        # Stats for monitoring
        self.stats = {
            'cache_hits': 0,
            'cache_misses': 0,
            'rate_limit_saves': 0,
        }

    async def get_entries(
        self,
        guild: discord.Guild,
        action: discord.AuditLogAction = None,
        limit: int = 5,
        target_id: int = None
    ) -> List[discord.AuditLogEntry]:
        """
        Get audit log entries, using cache when available.

        Args:
            guild: The guild to get audit logs from
            action: Filter by action type (e.g., AuditLogAction.channel_delete)
            limit: Maximum entries to return
            target_id: Filter by target ID (e.g., the deleted channel ID)

        Returns:
            List of matching audit log entries
        """
        guild_id = guild.id
        now = datetime.utcnow()

        # Check if cache is valid
        async with self.locks[guild_id]:
            cache_valid = (
                guild_id in self.cache_time and
                (now - self.cache_time[guild_id]).total_seconds() < self.CACHE_DURATION
            )

            if cache_valid:
                self.stats['cache_hits'] += 1
                entries = self.cache.get(guild_id, [])
            else:
                self.stats['cache_misses'] += 1

                # Fetch fresh entries
                try:
                    entries = []
                    async for entry in guild.audit_logs(limit=self.MAX_ENTRIES):
                        entries.append(entry)

                    self.cache[guild_id] = entries
                    self.cache_time[guild_id] = now

                except discord.Forbidden:
                    logger.warning(f"No audit log permission in {guild.name}")
                    return []
                except discord.HTTPException as e:
                    if e.status == 429:  # Rate limited
                        logger.warning(f"Rate limited fetching audit logs for {guild.name}")
                        self.stats['rate_limit_saves'] += 1
                        # Return cached data even if expired
                        entries = self.cache.get(guild_id, [])
                    else:
                        logger.error(f"HTTP error fetching audit logs: {e}")
                        return []
                except Exception as e:
                    logger.error(f"Unexpected error fetching audit logs: {e}")
                    return []

        # Filter entries based on criteria
        filtered = entries

        if action is not None:
            filtered = [e for e in filtered if e.action == action]

        if target_id is not None:
            filtered = [e for e in filtered if e.target and e.target.id == target_id]

        return filtered[:limit]

    async def get_actor(
        self,
        guild: discord.Guild,
        action: discord.AuditLogAction,
        target_id: int,
        max_age_seconds: float = 5.0
    ) -> Optional[discord.User]:
        """
        Get the user who performed an action on a target.

        Args:
            guild: The guild
            action: The action type
            target_id: The ID of the target (channel, role, etc.)
            max_age_seconds: Only consider entries newer than this

        Returns:
            The user who performed the action, or None
        """
        entries = await self.get_entries(guild, action=action, target_id=target_id, limit=1)

        if not entries:
            return None

        entry = entries[0]

        # Check if entry is recent enough
        now = datetime.utcnow()
        entry_time = entry.created_at.replace(tzinfo=None)
        age = (now - entry_time).total_seconds()

        if age > max_age_seconds:
            return None

        return entry.user

    async def get_recent_actions_by_user(
        self,
        guild: discord.Guild,
        user_id: int,
        action: discord.AuditLogAction = None,
        seconds: int = 60
    ) -> List[discord.AuditLogEntry]:
        """
        Get recent actions performed by a specific user.

        Useful for detecting if a user is mass-deleting, mass-banning, etc.
        """
        entries = await self.get_entries(guild, action=action, limit=25)

        cutoff = datetime.utcnow() - timedelta(seconds=seconds)

        user_entries = [
            e for e in entries
            if e.user and e.user.id == user_id and
            e.created_at.replace(tzinfo=None) > cutoff
        ]

        return user_entries

    def invalidate(self, guild_id: int):
        """Force invalidate cache for a guild (use after bot actions)"""
        if guild_id in self.cache_time:
            del self.cache_time[guild_id]
        if guild_id in self.cache:
            del self.cache[guild_id]

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total = self.stats['cache_hits'] + self.stats['cache_misses']
        hit_rate = (self.stats['cache_hits'] / total * 100) if total > 0 else 0

        return {
            **self.stats,
            'hit_rate': f"{hit_rate:.1f}%",
            'cached_guilds': len(self.cache),
        }

    async def cleanup(self):
        """Remove old cache entries"""
        now = datetime.utcnow()
        expired = [
            gid for gid, time in self.cache_time.items()
            if (now - time).total_seconds() > 60  # Clean entries older than 1 minute
        ]

        for gid in expired:
            self.invalidate(gid)

        if expired:
            logger.debug(f"Cleaned up audit cache for {len(expired)} guilds")


# Global instance - will be initialized in main.py
audit_cache: Optional[AuditLogCache] = None


def get_audit_cache() -> Optional[AuditLogCache]:
    """Get the global audit cache instance"""
    return audit_cache


def init_audit_cache(bot) -> AuditLogCache:
    """Initialize the global audit cache"""
    global audit_cache
    audit_cache = AuditLogCache(bot)
    logger.info("Audit log cache initialized")
    return audit_cache
