"""
Anti-Nuke Protection Cog - ULTRA AGGRESSIVE v3
================================================
COMPLETE protection against selfbot nukes.
Instantly deletes webhooks BEFORE they can spam.
Multiple redundant deletion layers.
Bans attackers on FIRST action.
Security log channel for all events.
"""

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio
import logging
import os
from typing import Optional, Dict, List, Any, Set

logger = logging.getLogger('Offcialx.AntiNuke')

# Dangerous permissions that should trigger protection
DANGEROUS_PERMISSIONS = [
    'administrator',
    'ban_members',
    'kick_members',
    'manage_channels',
    'manage_guild',
    'manage_roles',
    'manage_webhooks',
    'mention_everyone',
]


class AntiNuke(commands.Cog):
    """ULTRA AGGRESSIVE Anti-Nuke Protection v3 - COMPLETE"""

    def __init__(self, bot):
        self.bot = bot
        self.db = None  # Will be injected by bot
        self.guild_settings: Dict[int, Dict[str, Any]] = {}
        self.whitelisted: Dict[int, Set[int]] = defaultdict(set)
        self.trusted_bots: Dict[int, Set[int]] = defaultdict(set)  # Trusted bots
        self.recently_punished: Dict[int, Set[int]] = defaultdict(set)
        self.processed_entries: Set[int] = set()
        self.lockdown_active: Dict[int, bool] = {}

        # Caches
        self.known_channels: Dict[int, Set[int]] = defaultdict(set)
        self.channel_names: Dict[int, Dict[int, str]] = defaultdict(dict)
        self.channel_backups: Dict[int, Dict[int, Dict]] = defaultdict(dict)  # Full backup for restoration
        self.deleted_channels: Dict[int, List[Dict]] = defaultdict(list)  # Deleted channels
        self.known_webhooks: Dict[int, Dict[int, Set[int]]] = defaultdict(lambda: defaultdict(set))
        self.known_roles: Dict[int, Set[int]] = defaultdict(set)
        self.known_bots: Dict[int, Set[int]] = defaultdict(set)
        self.member_roles: Dict[int, Dict[int, Set[int]]] = defaultdict(lambda: defaultdict(set))

        # Lockdown permission backup - stores original @everyone permissions per channel
        self.lockdown_permission_backup: Dict[int, Dict[int, Optional[discord.PermissionOverwrite]]] = defaultdict(dict)

        # BLACKLIST - webhooks that MUST be deleted
        self.blacklisted_webhooks: Dict[int, Set[int]] = defaultdict(set)
        self.deleted_webhooks: Set[int] = set()  # Already deleted - ignore messages

        # Security stats
        self.attack_stats: Dict[int, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

        # Bot owner IDs
        self.owner_ids: Set[int] = set()
        for oid in os.getenv('OWNER_IDS', '').split(','):
            try:
                self.owner_ids.add(int(oid.strip()))
            except:
                pass

        self._cleanup_task = None
        self._webhook_scan_task = None
        self._fast_scan_task = None
        self._settings_loaded: Set[int] = set()  # Track which guilds have loaded settings

        # Nuke detection tracking
        self.nuke_in_progress: Dict[int, bool] = {}  # guild_id -> True if nuke detected
        self.nuke_attacker: Dict[int, int] = {}  # guild_id -> attacker_id
        self.first_delete_handled: Dict[int, bool] = {}  # guild_id -> True if first delete triggered mass restore

        # Server settings backup for restoration
        self.server_settings_backup: Dict[int, Dict] = {}  # guild_id -> settings backup

    async def cog_load(self):
        self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
        self._webhook_scan_task = asyncio.create_task(self._continuous_webhook_scan())
        self._fast_scan_task = asyncio.create_task(self._fast_webhook_scan())

    async def cog_unload(self):
        if self._cleanup_task:
            self._cleanup_task.cancel()
        if self._webhook_scan_task:
            self._webhook_scan_task.cancel()
        if self._fast_scan_task:
            self._fast_scan_task.cancel()

    async def _backup_server_settings(self, guild: discord.Guild, save_to_db: bool = True) -> Dict:
        """Backup current server settings for restoration"""
        backup = {
            'name': guild.name,
            'icon_url': str(guild.icon.url) if guild.icon else None,
            'banner_url': str(guild.banner.url) if guild.banner else None,
            'verification_level': guild.verification_level.value,
            'vanity_url_code': guild.vanity_url_code,
            'description': guild.description,
            'default_notifications': guild.default_notifications.value,
            'explicit_content_filter': guild.explicit_content_filter.value,
            'afk_channel_id': guild.afk_channel.id if guild.afk_channel else None,
            'afk_timeout': guild.afk_timeout,
            'system_channel_id': guild.system_channel.id if guild.system_channel else None,
        }

        # Save to database for persistence
        if save_to_db and self.db:
            try:
                await self.db.save_server_settings_backup(guild.id, backup)
            except Exception as e:
                logger.warning(f"Failed to save server settings backup to database: {e}")

        return backup

    async def _restore_server_settings(self, guild: discord.Guild, backup: Dict, setting_type: str = None) -> bool:
        """Restore server settings from backup"""
        try:
            kwargs = {}

            if setting_type == 'name' and backup.get('name') != guild.name:
                kwargs['name'] = backup['name']
            elif setting_type == 'verification_level' and backup.get('verification_level') != guild.verification_level.value:
                kwargs['verification_level'] = discord.VerificationLevel(backup['verification_level'])
            elif setting_type is None:
                # Restore all settings
                if backup.get('name') != guild.name:
                    kwargs['name'] = backup['name']
                if backup.get('verification_level') != guild.verification_level.value:
                    kwargs['verification_level'] = discord.VerificationLevel(backup['verification_level'])
                if backup.get('description') != guild.description:
                    kwargs['description'] = backup.get('description')
                if backup.get('default_notifications') != guild.default_notifications.value:
                    kwargs['default_notifications'] = discord.NotificationLevel(backup['default_notifications'])
                if backup.get('explicit_content_filter') != guild.explicit_content_filter.value:
                    kwargs['explicit_content_filter'] = discord.ContentFilter(backup['explicit_content_filter'])

            if kwargs:
                await guild.edit(**kwargs, reason="[ANTINUKE] Reverted unauthorized server changes")
                logger.info(f"✅ Restored server settings for {guild.name}: {list(kwargs.keys())}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to restore server settings: {e}")
            return False

    async def _periodic_cleanup(self):
        while True:
            await asyncio.sleep(300)
            if len(self.processed_entries) > 1000:
                self.processed_entries = set(list(self.processed_entries)[-500:])
            if len(self.deleted_webhooks) > 500:
                self.deleted_webhooks = set(list(self.deleted_webhooks)[-250:])

    async def _fast_webhook_scan(self):
        """Ultra-fast scan for blacklisted webhooks - runs every 0.5 seconds"""
        await asyncio.sleep(5)
        while True:
            try:
                for guild_id, webhook_ids in list(self.blacklisted_webhooks.items()):
                    for wh_id in list(webhook_ids):
                        if wh_id in self.deleted_webhooks:
                            self.blacklisted_webhooks[guild_id].discard(wh_id)
                            continue
                        # Try to delete via API
                        asyncio.create_task(self._delete_webhook_by_id_only(wh_id))
            except:
                pass
            await asyncio.sleep(0.5)

    async def _continuous_webhook_scan(self):
        """Scan for unauthorized webhooks every 1 second"""
        await asyncio.sleep(10)
        while True:
            try:
                for guild in self.bot.guilds:
                    settings = await self.get_settings(guild.id)
                    if not settings['enabled'] or not settings['anti_webhook']:
                        continue
                    for channel in guild.text_channels:
                        try:
                            webhooks = await channel.webhooks()
                            known = self.known_webhooks[guild.id].get(channel.id, set())
                            for webhook in webhooks:
                                if webhook.id not in known:
                                    # SKIP bot's own webhooks and application webhooks
                                    if webhook.user and webhook.user.id == self.bot.user.id:
                                        self.known_webhooks[guild.id][channel.id].add(webhook.id)
                                        continue
                                    if webhook.type == discord.WebhookType.application:
                                        self.known_webhooks[guild.id][channel.id].add(webhook.id)
                                        continue
                                    # ADD TO BLACKLIST + DELETE IMMEDIATELY
                                    self.blacklisted_webhooks[guild.id].add(webhook.id)
                                    asyncio.create_task(self._ultra_delete_webhook(webhook, guild))
                        except:
                            pass
                        await asyncio.sleep(0.02)
            except:
                pass
            await asyncio.sleep(1)

    async def preload_all_settings(self):
        """Preload settings for all guilds on bot startup"""
        if not self.db:
            logger.info("No database - using default settings")
            return

        logger.info("Preloading anti-nuke settings for all guilds...")
        loaded_count = 0
        trusted_users_count = 0
        trusted_bots_count = 0

        for guild in self.bot.guilds:
            try:
                # Always set default settings first
                self.guild_settings[guild.id] = {
                    'enabled': True,
                    'anti_channel_create': True,
                    'anti_channel_delete': True,
                    'anti_channel_rename': True,
                    'anti_webhook': True,
                    'anti_role_create': True,
                    'anti_role_delete': True,
                    'anti_role_update': True,
                    'anti_ban': True,
                    'anti_bot': True,
                    'anti_permissions': True,
                    'anti_integration': True,
                    'anti_vanity': True,
                    'log_channel_id': None,
                    'punishment': 'ban',
                }

                # Load settings from database and override defaults
                db_settings = await self.db.get_guild_settings(guild.id, 'antinuke')
                if db_settings and isinstance(db_settings, dict):
                    self.guild_settings[guild.id].update(db_settings)
                    loaded_count += 1

                # Load whitelist
                whitelist = await self.db.get_whitelist(guild.id)
                for entry in whitelist:
                    if isinstance(entry, dict) and 'user_id' in entry:
                        self.whitelisted[guild.id].add(entry['user_id'])

                # Load trusted users
                trusted_users = await self.db.get_trusted_users(guild.id)
                for user_id in trusted_users:
                    if isinstance(user_id, int):
                        self.whitelisted[guild.id].add(user_id)
                        trusted_users_count += 1

                # Load trusted bots
                trusted_bots = await self.db.get_trusted_bots(guild.id)
                for bot_id in trusted_bots:
                    if isinstance(bot_id, int):
                        self.trusted_bots[guild.id].add(bot_id)
                        self.known_bots[guild.id].add(bot_id)
                        trusted_bots_count += 1

                # Load channel backups from database
                try:
                    db_backups = await self.db.get_channel_backups(guild.id)
                    if db_backups:
                        self.channel_backups[guild.id].update(db_backups)
                        logger.info(f"  Loaded {len(db_backups)} channel backups for {guild.name}")
                except Exception as e:
                    logger.warning(f"Failed to load channel backups for {guild.name}: {e}")

                # Load server settings backup from database
                try:
                    server_backup = await self.db.get_server_settings_backup(guild.id)
                    if server_backup:
                        self.server_settings_backup[guild.id] = server_backup
                        logger.info(f"  Loaded server settings backup for {guild.name}")
                except Exception as e:
                    logger.warning(f"Failed to load server settings backup for {guild.name}: {e}")

                self._settings_loaded.add(guild.id)

            except Exception as e:
                logger.error(f'Failed to preload settings for guild {guild.id}: {e}')
                import traceback
                traceback.print_exc()

        logger.info(f"✅ Preloaded anti-nuke: {loaded_count} guilds, {trusted_users_count} trusted users, {trusted_bots_count} trusted bots")

    async def get_settings(self, guild_id: int) -> Dict[str, Any]:
        """Get guild settings - loads from database if available"""
        if guild_id not in self.guild_settings:
            # Default settings
            self.guild_settings[guild_id] = {
                'enabled': True,
                'anti_channel_create': True,
                'anti_channel_delete': True,
                'anti_channel_rename': True,
                'anti_webhook': True,
                'anti_role_create': True,
                'anti_role_delete': True,
                'anti_role_update': True,
                'anti_ban': True,
                'anti_bot': True,
                'anti_permissions': True,
                'anti_integration': True,
                'anti_vanity': True,
                'log_channel_id': None,
                'punishment': 'ban',
            }

            # Try to load from database
            if self.db and guild_id not in self._settings_loaded:
                try:
                    db_settings = await self.db.get_guild_settings(guild_id, 'antinuke')
                    if db_settings and isinstance(db_settings, dict):
                        self.guild_settings[guild_id].update(db_settings)

                    # Load whitelist from database
                    whitelist = await self.db.get_whitelist(guild_id)
                    for entry in whitelist:
                        if isinstance(entry, dict) and 'user_id' in entry:
                            self.whitelisted[guild_id].add(entry['user_id'])

                    # Load trusted users from database
                    trusted_users = await self.db.get_trusted_users(guild_id)
                    for user_id in trusted_users:
                        if isinstance(user_id, int):
                            self.whitelisted[guild_id].add(user_id)

                    # Load trusted bots from database
                    trusted_bots = await self.db.get_trusted_bots(guild_id)
                    for bot_id in trusted_bots:
                        if isinstance(bot_id, int):
                            self.trusted_bots[guild_id].add(bot_id)
                            self.known_bots[guild_id].add(bot_id)

                    self._settings_loaded.add(guild_id)
                except Exception as e:
                    logger.warning(f'Failed to load settings from database for guild {guild_id}: {e}')

        return self.guild_settings[guild_id]

    async def save_settings(self, guild_id: int):
        """Save guild settings to database"""
        if not self.db:
            return

        try:
            settings = self.guild_settings.get(guild_id, {})
            await self.db.save_guild_settings(guild_id, 'antinuke', settings)
        except Exception as e:
            logger.warning(f'Failed to save settings to database: {e}')

    # Minimal embed color
    EMBED_COLOR = 0x2b2d31

    def simple_embed(self, message: str, color: int = None) -> discord.Embed:
        """Create a simple, minimal embed"""
        return discord.Embed(
            description=message,
            color=color or self.EMBED_COLOR
        )

    def is_trusted(self, guild: discord.Guild, user_id: int) -> bool:
        """Check if a user is trusted (immune to anti-nuke) using unified whitelist"""
        # Always trust the bot itself
        if user_id == self.bot.user.id:
            return True
        # Bot owners are always trusted
        if user_id in self.owner_ids:
            return True
        # Server owner is always trusted
        if user_id == guild.owner_id:
            return True

        # Check unified whitelist cog (includes users, bots, and roles)
        whitelist_cog = self.bot.get_cog('Whitelist')
        if whitelist_cog:
            # This checks: whitelisted_users, whitelisted_bots, and whitelisted_roles
            if whitelist_cog.is_whitelisted(guild.id, user_id):
                return True

        # Fallback to local caches (for backwards compatibility during transition)
        if user_id in self.whitelisted.get(guild.id, set()):
            return True
        if user_id in self.trusted_bots.get(guild.id, set()):
            return True

        return False

    def has_dangerous_permissions(self, permissions: discord.Permissions) -> bool:
        """Check if permissions contain dangerous permissions"""
        for perm in DANGEROUS_PERMISSIONS:
            if getattr(permissions, perm, False):
                return True
        return False

    async def log_security_event(self, guild: discord.Guild, event_type: str, description: str,
                                  attacker: Optional[discord.User] = None, action_taken: str = "None",
                                  color: discord.Color = discord.Color.red()):
        """Log security events to the designated log channel"""
        settings = await self.get_settings(guild.id)
        log_channel_id = settings.get('log_channel_id')

        # Update stats
        self.attack_stats[guild.id][event_type] += 1
        self.attack_stats[guild.id]['total'] += 1

        if not log_channel_id:
            return

        channel = guild.get_channel(log_channel_id)
        if not channel:
            return

        # Minimal security log embed
        embed = discord.Embed(color=0x2b2d31)

        log_text = f"**{event_type}**\n{description}"
        if attacker:
            log_text += f"\n👤 {attacker.mention} (`{attacker.id}`)"
        if action_taken and action_taken != "None":
            log_text += f"\n⚡ {action_taken}"

        embed.description = log_text

        try:
            await channel.send(embed=embed)
        except:
            pass

    async def cache_guild(self, guild: discord.Guild):
        self.known_channels[guild.id] = {c.id for c in guild.channels}
        for channel in guild.channels:
            self.channel_names[guild.id][channel.id] = channel.name
            # Backup full channel data for restoration
            try:
                self.channel_backups[guild.id][channel.id] = await self._backup_channel(channel)
            except:
                pass
        self.known_roles[guild.id] = {r.id for r in guild.roles}
        self.known_bots[guild.id] = {m.id for m in guild.members if m.bot}

        # Cache member roles
        for member in guild.members:
            self.member_roles[guild.id][member.id] = {r.id for r in member.roles}

        for channel in guild.text_channels:
            try:
                webhooks = await channel.webhooks()
                self.known_webhooks[guild.id][channel.id] = {w.id for w in webhooks}
            except:
                pass

        # Save channel backups to database for persistence
        if self.db and self.channel_backups.get(guild.id):
            try:
                await self.db.save_channel_backups_bulk(guild.id, self.channel_backups[guild.id])
                logger.info(f"💾 Saved {len(self.channel_backups[guild.id])} channel backups to database for {guild.name}")
            except Exception as e:
                logger.warning(f"Failed to save channel backups to database: {e}")

        # Backup server settings for restoration
        self.server_settings_backup[guild.id] = await self._backup_server_settings(guild)

        logger.info(f"📦 Cached {guild.name} (channels: {len(self.known_channels[guild.id])}, roles: {len(self.known_roles[guild.id])}, bots: {len(self.known_bots[guild.id])})")

    async def _backup_channel(self, channel: discord.abc.GuildChannel) -> Dict:
        """Create a full backup of a channel for restoration"""
        backup = {
            'id': channel.id,
            'name': channel.name,
            'type': str(channel.type),
            'position': channel.position,
            'category_id': getattr(channel, 'category_id', None),
            'overwrites': {},
        }

        # Backup permission overwrites
        for target, overwrite in channel.overwrites.items():
            target_type = 'role' if isinstance(target, discord.Role) else 'member'
            backup['overwrites'][str(target.id)] = {
                'type': target_type,
                'allow': overwrite.pair()[0].value,
                'deny': overwrite.pair()[1].value,
            }

        # Type-specific properties
        if isinstance(channel, discord.TextChannel):
            backup['topic'] = channel.topic
            backup['slowmode_delay'] = channel.slowmode_delay
            backup['nsfw'] = channel.nsfw
        elif isinstance(channel, discord.VoiceChannel):
            backup['bitrate'] = channel.bitrate
            backup['user_limit'] = channel.user_limit
        elif isinstance(channel, discord.CategoryChannel):
            backup['is_category'] = True

        return backup

    async def _restore_channel(self, guild: discord.Guild, backup: Dict) -> Optional[discord.abc.GuildChannel]:
        """Restore a deleted channel from backup"""
        try:
            channel_type = backup.get('type', 'text')
            channel_name = backup.get('name', '')

            # CHECK IF CHANNEL ALREADY EXISTS - PREVENT DUPLICATES
            existing_channel = None
            if 'text' in channel_type:
                existing_channel = discord.utils.get(guild.text_channels, name=channel_name)
            elif 'voice' in channel_type:
                existing_channel = discord.utils.get(guild.voice_channels, name=channel_name)
            elif 'category' in channel_type:
                existing_channel = discord.utils.get(guild.categories, name=channel_name)
            elif 'stage' in channel_type:
                existing_channel = discord.utils.get(guild.stage_channels, name=channel_name)

            if existing_channel:
                logger.info(f"⏭️ Skipped restore - channel #{channel_name} already exists")
                # Update caches with existing channel
                self.known_channels[guild.id].add(existing_channel.id)
                self.channel_names[guild.id][existing_channel.id] = existing_channel.name
                return existing_channel

            category = None

            # Get category if exists
            if backup.get('category_id'):
                category = guild.get_channel(backup['category_id'])

            # Build permission overwrites
            overwrites = {}
            for target_id_str, overwrite_data in backup.get('overwrites', {}).items():
                target_id = int(target_id_str)
                if overwrite_data['type'] == 'role':
                    target = guild.get_role(target_id)
                else:
                    target = guild.get_member(target_id)

                if target:
                    overwrites[target] = discord.PermissionOverwrite.from_pair(
                        discord.Permissions(overwrite_data['allow']),
                        discord.Permissions(overwrite_data['deny'])
                    )

            # Create channel based on type
            if 'text' in channel_type:
                new_channel = await guild.create_text_channel(
                    name=backup['name'],
                    category=category,
                    topic=backup.get('topic'),
                    slowmode_delay=backup.get('slowmode_delay', 0),
                    nsfw=backup.get('nsfw', False),
                    overwrites=overwrites,
                    reason="[ANTINUKE] Channel restored after nuke attack"
                )
            elif 'voice' in channel_type:
                new_channel = await guild.create_voice_channel(
                    name=backup['name'],
                    category=category,
                    bitrate=backup.get('bitrate', 64000),
                    user_limit=backup.get('user_limit', 0),
                    overwrites=overwrites,
                    reason="[ANTINUKE] Channel restored after nuke attack"
                )
            elif 'category' in channel_type:
                new_channel = await guild.create_category(
                    name=backup['name'],
                    overwrites=overwrites,
                    reason="[ANTINUKE] Category restored after nuke attack"
                )
            elif 'stage' in channel_type:
                new_channel = await guild.create_stage_channel(
                    name=backup['name'],
                    category=category,
                    overwrites=overwrites,
                    reason="[ANTINUKE] Stage restored after nuke attack"
                )
            else:
                new_channel = await guild.create_text_channel(
                    name=backup['name'],
                    category=category,
                    overwrites=overwrites,
                    reason="[ANTINUKE] Channel restored after nuke attack"
                )

            logger.info(f"✅ RESTORED channel #{backup['name']} in {guild.name}")

            # Update caches
            self.known_channels[guild.id].add(new_channel.id)
            self.channel_names[guild.id][new_channel.id] = new_channel.name

            # Create new backup for the restored channel
            try:
                new_backup = await self._backup_channel(new_channel)
                self.channel_backups[guild.id][new_channel.id] = new_backup

                # Save to database
                if self.db:
                    await self.db.save_channel_backup(guild.id, new_channel.id, new_backup)
                    # Remove old backup from database (old channel ID)
                    old_channel_id = backup.get('id')
                    if old_channel_id:
                        await self.db.delete_channel_backup(guild.id, old_channel_id)
            except Exception as e:
                logger.warning(f"Failed to save restored channel backup: {e}")

            # Log the restoration
            await self.log_security_event(
                guild,
                "Channel Restored",
                f"Channel `#{backup['name']}` was automatically restored",
                action_taken="Channel recreated with permissions",
                color=discord.Color.green()
            )

            return new_channel

        except Exception as e:
            logger.error(f"Failed to restore channel {backup.get('name')}: {e}")
            return None

    # ============ EMERGENCY HELPER METHODS FOR ULTRA STRICT MODE ============

    async def _emergency_strip_roles(self, guild: discord.Guild, user_id: int):
        """Emergency: Strip ALL roles from attacker immediately"""
        try:
            member = guild.get_member(user_id)
            if member:
                await member.edit(roles=[], reason="[ANTINUKE EMERGENCY] Channel nuke detected")
                logger.critical(f"🚨 EMERGENCY: Stripped all roles from {user_id}")
        except Exception as e:
            logger.error(f"Failed to strip roles from {user_id}: {e}")

    async def _emergency_remove_all_permissions(self, guild: discord.Guild, user_id: int):
        """Emergency: Remove attacker's permission overwrites from ALL channels"""
        try:
            member = guild.get_member(user_id)
            if not member:
                return
            for channel in guild.channels:
                try:
                    if member in channel.overwrites:
                        await channel.set_permissions(member, overwrite=None, reason="[ANTINUKE EMERGENCY] Removing attacker permissions")
                except:
                    pass
            logger.critical(f"🚨 EMERGENCY: Removed {user_id} from all channel overwrites")
        except Exception as e:
            logger.error(f"Failed to remove permissions for {user_id}: {e}")

    async def _emergency_ban(self, guild: discord.Guild, user_id: int, reason: str) -> bool:
        """Emergency: Ban with multiple retry attempts"""
        for attempt in range(3):
            try:
                await guild.ban(discord.Object(id=user_id), reason=f"[ANTINUKE EMERGENCY] {reason}", delete_message_days=0)
                logger.critical(f"🚨 EMERGENCY BAN: {user_id} - {reason}")
                return True
            except discord.NotFound:
                return True  # Already banned or not in server
            except Exception as e:
                logger.error(f"Ban attempt {attempt+1} failed for {user_id}: {e}")
                await asyncio.sleep(0.1)
        return False

    async def _emergency_lockdown(self, guild: discord.Guild):
        """Emergency: Lock @everyone permissions for 30 seconds"""
        try:
            everyone = guild.default_role
            original_perms = everyone.permissions

            # Lock dangerous permissions
            new_perms = discord.Permissions(original_perms.value)
            new_perms.update(
                manage_channels=False,
                manage_roles=False,
                manage_webhooks=False,
                administrator=False
            )

            await everyone.edit(permissions=new_perms, reason="[ANTINUKE EMERGENCY] Server lockdown")
            logger.critical(f"🔒 EMERGENCY LOCKDOWN: {guild.name}")

            # Auto-unlock after 30 seconds
            async def unlock():
                await asyncio.sleep(30)
                try:
                    await everyone.edit(permissions=original_perms, reason="[ANTINUKE] Lockdown ended")
                    logger.info(f"🔓 Emergency lockdown ended: {guild.name}")
                except:
                    pass

            asyncio.create_task(unlock())

        except Exception as e:
            logger.error(f"Emergency lockdown failed: {e}")

    # ============ MASS CHANNEL RESTORE SYSTEM ============

    async def _restore_all_channels(self, guild: discord.Guild, attacker_id: int = None):
        """Restore ALL deleted channels from backup - handles mass nuke"""
        if guild.id not in self.channel_backups:
            return 0

        backups = dict(self.channel_backups[guild.id])  # Copy to avoid modification during iteration
        restored_count = 0
        failed_count = 0

        # Get current channel IDs
        current_channel_ids = {c.id for c in guild.channels}

        # Find channels that were deleted (in backup but not in current)
        deleted_backups = {
            ch_id: backup for ch_id, backup in backups.items()
            if ch_id not in current_channel_ids
        }

        if not deleted_backups:
            return 0

        logger.critical(f"🔄 MASS RESTORE: Restoring {len(deleted_backups)} channels in {guild.name}")

        # Get current channel names to avoid duplicates
        current_channel_names = {c.name.lower() for c in guild.channels}

        # Restore categories FIRST (they need to exist for child channels)
        categories_to_restore = [
            (ch_id, backup) for ch_id, backup in deleted_backups.items()
            if 'category' in backup.get('type', '').lower()
        ]

        # Then restore other channels
        other_channels_to_restore = [
            (ch_id, backup) for ch_id, backup in deleted_backups.items()
            if 'category' not in backup.get('type', '').lower()
        ]

        # Restore categories first
        category_id_map = {}  # Old ID -> New ID mapping
        for ch_id, backup in categories_to_restore:
            # Skip if channel already exists
            if backup['name'].lower() in current_channel_names:
                logger.info(f"⏭️ Skipped - #{backup['name']} already exists")
                continue
            try:
                new_channel = await self._restore_channel(guild, backup)
                if new_channel:
                    category_id_map[ch_id] = new_channel.id
                    restored_count += 1
                    logger.info(f"✅ Restored category: {backup['name']}")
                else:
                    failed_count += 1
                await asyncio.sleep(0.5)  # Rate limit protection
            except Exception as e:
                logger.error(f"Failed to restore category {backup['name']}: {e}")
                failed_count += 1

        # Restore other channels with updated category IDs
        for ch_id, backup in other_channels_to_restore:
            # Skip if channel already exists
            if backup['name'].lower() in current_channel_names:
                logger.info(f"⏭️ Skipped - #{backup['name']} already exists")
                continue
            try:
                # Update category_id if the category was also restored
                if backup.get('category_id') in category_id_map:
                    backup['category_id'] = category_id_map[backup['category_id']]

                new_channel = await self._restore_channel(guild, backup)
                if new_channel:
                    restored_count += 1
                    logger.info(f"✅ Restored channel: #{backup['name']}")
                else:
                    failed_count += 1
                await asyncio.sleep(0.3)  # Rate limit protection
            except Exception as e:
                logger.error(f"Failed to restore channel {backup['name']}: {e}")
                failed_count += 1

        # Log summary
        logger.critical(f"🔄 MASS RESTORE COMPLETE: {restored_count} restored, {failed_count} failed")

        # Send summary to a channel if possible
        try:
            for channel in guild.text_channels:
                if channel.permissions_for(guild.me).send_messages:
                    embed = discord.Embed(
                        title="Mass Channel Restore Complete",
                        description=(
                            f"**Channels Restored:** {restored_count}\n"
                            f"**Failed:** {failed_count}\n"
                            f"**Attacker:** {'<@' + str(attacker_id) + '>' if attacker_id else 'Unknown'}\n\n"
                            f"The attacker has been banned and their roles stripped."
                        ),
                        color=discord.Color.green() if failed_count == 0 else discord.Color.orange()
                    )
                    embed.set_footer(text="OffcialX Anti-Nuke Protection")
                    await channel.send(embed=embed)
                    break
        except:
            pass

        return restored_count

    async def _delayed_mass_restore(self, guild: discord.Guild, attacker_id: int):
        """Wait for nuke to complete then restore ALL channels"""
        # Wait for the nuke to finish (selfbots delete channels rapidly)
        logger.critical(f"⏳ Waiting 3 seconds for nuke to complete before mass restore...")
        await asyncio.sleep(3)

        # Now restore everything
        logger.critical(f"🔄 Starting mass restore for {guild.name}")
        restored = await self._restore_all_channels(guild, attacker_id)

        # Reset tracking flags after restore
        self.nuke_in_progress[guild.id] = False
        self.first_delete_handled[guild.id] = False

        logger.critical(f"✅ Mass restore complete: {restored} channels restored in {guild.name}")

        # Re-cache the guild with new channels
        await self.cache_guild(guild)

    async def _check_and_trigger_mass_restore(self, guild: discord.Guild, attacker_id: int):
        """Check if mass deletion occurred and trigger full restore (legacy method)"""
        # Wait a moment for all delete events to be processed
        await asyncio.sleep(2)

        # Check how many channels are missing from backups
        current_channel_ids = {c.id for c in guild.channels}
        backed_up_ids = set(self.channel_backups.get(guild.id, {}).keys())
        missing_count = len(backed_up_ids - current_channel_ids)

        if missing_count > 1:
            logger.critical(f"🚨 MASS DELETION DETECTED: {missing_count} channels missing in {guild.name}")
            await self._restore_all_channels(guild, attacker_id)

    async def instant_punish(self, guild: discord.Guild, user_id: int, reason: str):
        if user_id in self.recently_punished.get(guild.id, set()):
            return
        self.recently_punished[guild.id].add(user_id)
        asyncio.get_event_loop().call_later(60, lambda: self.recently_punished.get(guild.id, set()).discard(user_id))

        if self.is_trusted(guild, user_id):
            return

        # Get punishment type from settings
        settings = await self.get_settings(guild.id)
        punishment_type = settings.get('punishment', 'ban')

        member = guild.get_member(user_id)
        user = member or await self.bot.fetch_user(user_id)
        logger.critical(f"⚡ PUNISH ({punishment_type.upper()}): {user_id} - {reason}")

        # Step 1: Strip all roles
        if member:
            try:
                await member.edit(roles=[], reason=f"[ANTINUKE] {reason}")
            except:
                pass

        punished = False
        action_taken = "Roles stripped"

        # Step 2: Apply punishment based on setting
        if punishment_type == 'ban':
            try:
                if member:
                    await guild.ban(member, reason=f"[ANTINUKE] {reason}", delete_message_days=0)
                else:
                    await guild.ban(discord.Object(id=user_id), reason=f"[ANTINUKE] {reason}")
                punished = True
                action_taken = "Roles stripped + Banned"
                logger.info(f"✅ Banned {user_id}")
            except Exception as e:
                logger.warning(f"Failed to ban {user_id}: {e}")
                # Fallback to kick if ban fails
                if member:
                    try:
                        await guild.kick(member, reason=f"[ANTINUKE] {reason}")
                        punished = True
                        action_taken = "Roles stripped + Kicked (ban failed)"
                    except:
                        pass
        else:  # kick
            if member:
                try:
                    await guild.kick(member, reason=f"[ANTINUKE] {reason}")
                    punished = True
                    action_taken = "Roles stripped + Kicked"
                    logger.info(f"✅ Kicked {user_id}")
                except Exception as e:
                    logger.warning(f"Failed to kick {user_id}: {e}")

        # Log the punishment
        await self.log_security_event(
            guild,
            "Attacker Punished",
            f"**Reason:** {reason}",
            attacker=user,
            action_taken=action_taken,
            color=discord.Color.dark_red()
        )

        # NOTE: Auto-lockdown disabled - don't change channel permissions automatically
        # Use !serverlock manually if needed

    async def auto_lockdown(self, guild: discord.Guild, reason: str):
        """Auto-lockdown with proper permission backup and restore - trusted users/roles bypass"""
        self.lockdown_active[guild.id] = True
        logger.warning(f"🔒 LOCKDOWN: {guild.name}")

        await self.log_security_event(
            guild,
            "Auto-Lockdown",
            f"Server locked for 30 seconds\n**Trigger:** {reason}\n**Note:** Trusted users/roles can still send messages",
            action_taken="All channels locked (with bypass for trusted)",
            color=discord.Color.orange()
        )

        try:
            # BACKUP original @everyone permissions for each channel
            self.lockdown_permission_backup[guild.id] = {}
            locked_count = 0
            bypass_count = 0

            for channel in guild.text_channels:
                try:
                    # Store original overwrite
                    original_overwrite = channel.overwrites.get(guild.default_role)
                    self.lockdown_permission_backup[guild.id][channel.id] = original_overwrite

                    # Lock while preserving other permissions
                    if original_overwrite:
                        new_overwrite = discord.PermissionOverwrite.from_pair(
                            *original_overwrite.pair()
                        )
                        new_overwrite.send_messages = False
                        await channel.set_permissions(guild.default_role, overwrite=new_overwrite)
                    else:
                        await channel.set_permissions(guild.default_role, send_messages=False)

                    # Apply bypass for trusted users and roles
                    bypass_count += await self._apply_lockdown_bypass(channel, guild)
                    locked_count += 1
                except Exception as e:
                    logger.warning(f"Failed to lock channel {channel.name}: {e}")

            logger.info(f"🔒 Locked {locked_count} channels in {guild.name} (bypass for {bypass_count} trusted)")
            await asyncio.sleep(30)

            # RESTORE original permissions
            restored_count = 0
            for channel in guild.text_channels:
                try:
                    # Remove bypass permissions first
                    await self._remove_lockdown_bypass(channel, guild)

                    original_overwrite = self.lockdown_permission_backup[guild.id].get(channel.id)
                    if original_overwrite is not None:
                        await channel.set_permissions(guild.default_role, overwrite=original_overwrite)
                    else:
                        await channel.set_permissions(guild.default_role, overwrite=None)
                    restored_count += 1
                except Exception as e:
                    logger.warning(f"Failed to unlock channel {channel.name}: {e}")

            logger.info(f"🔓 UNLOCKED: {guild.name} ({restored_count} channels restored)")

            await self.log_security_event(
                guild,
                "Lockdown Ended",
                f"Server has been unlocked\n**Restored:** {restored_count} channels",
                action_taken="All channel permissions restored",
                color=discord.Color.green()
            )
        finally:
            # Clear backup
            if guild.id in self.lockdown_permission_backup:
                self.lockdown_permission_backup[guild.id] = {}
            self.lockdown_active[guild.id] = False

    async def _ultra_delete_webhook(self, webhook: discord.Webhook, guild: discord.Guild):
        """Ultra-aggressive webhook deletion with multiple attempts"""
        webhook_id = webhook.id
        creator_id = webhook.user.id if webhook.user else None

        # NEVER delete webhooks created by this bot
        if creator_id == self.bot.user.id:
            return

        # NEVER delete application webhooks (Discord's interaction system)
        if webhook.type == discord.WebhookType.application:
            return

        # FIXED: NEVER delete webhooks created by TRUSTED BOTS
        if creator_id and creator_id in self.trusted_bots.get(guild.id, set()):
            logger.info(f"✅ Skipped webhook deletion - created by trusted bot {creator_id}")
            return

        # FIXED: NEVER delete webhooks created by KNOWN BOTS
        if creator_id and creator_id in self.known_bots.get(guild.id, set()):
            logger.info(f"✅ Skipped webhook deletion - created by known bot {creator_id}")
            return

        # FIXED: NEVER delete webhooks created by TRUSTED USERS
        if creator_id and self.is_trusted(guild, creator_id):
            logger.info(f"✅ Skipped webhook deletion - created by trusted user {creator_id}")
            return

        # FIXED: NEVER delete webhooks created by users/bots with WHITELISTED ROLES
        if creator_id:
            member = guild.get_member(creator_id)
            if member:
                whitelist_cog = self.bot.get_cog('Whitelist')
                if whitelist_cog and whitelist_cog.has_whitelisted_role(guild.id, member):
                    logger.info(f"✅ Skipped webhook deletion - creator has whitelisted role {creator_id}")
                    return

        # Mark as deleted immediately to block messages
        self.deleted_webhooks.add(webhook_id)

        # Multiple deletion attempts in parallel
        async def attempt1():
            try:
                await webhook.delete(reason="[ANTINUKE] Unauthorized")
                logger.info(f"⚡ Deleted webhook {webhook_id} (method 1)")
            except discord.NotFound:
                pass
            except:
                pass

        async def attempt2():
            try:
                wh = await self.bot.fetch_webhook(webhook_id)
                await wh.delete(reason="[ANTINUKE] Unauthorized")
                logger.info(f"⚡ Deleted webhook {webhook_id} (method 2)")
            except discord.NotFound:
                pass
            except:
                pass

        async def attempt3():
            await asyncio.sleep(0.1)
            try:
                wh = await self.bot.fetch_webhook(webhook_id)
                await wh.delete(reason="[ANTINUKE] Unauthorized")
                logger.info(f"⚡ Deleted webhook {webhook_id} (method 3)")
            except discord.NotFound:
                pass
            except:
                pass

        # Run all attempts in parallel
        await asyncio.gather(attempt1(), attempt2(), attempt3(), return_exceptions=True)

        # Log and punish creator
        if creator_id:
            creator = guild.get_member(creator_id) or await self.bot.fetch_user(creator_id)
            await self.log_security_event(
                guild,
                "Webhook Blocked",
                f"Unauthorized webhook created and deleted\n**Webhook ID:** {webhook_id}",
                attacker=creator,
                action_taken="Webhook deleted + Creator banned"
            )
            if not self.is_trusted(guild, creator_id):
                await self.instant_punish(guild, creator_id, "Created unauthorized webhook")

    async def _delete_webhook_by_id_only(self, webhook_id: int):
        """Delete webhook by ID only"""
        if webhook_id in self.deleted_webhooks:
            return
        try:
            webhook = await self.bot.fetch_webhook(webhook_id)
            await webhook.delete(reason="[ANTINUKE] Blacklisted webhook")
            self.deleted_webhooks.add(webhook_id)
            logger.info(f"⚡ Deleted blacklisted webhook {webhook_id}")
        except discord.NotFound:
            self.deleted_webhooks.add(webhook_id)
        except:
            pass

    async def _force_delete_webhook(self, webhook: discord.Webhook):
        """Force delete webhook with retries"""
        self.deleted_webhooks.add(webhook.id)
        for _ in range(5):
            try:
                await webhook.delete(reason="[ANTINUKE] Unauthorized webhook")
                logger.info(f"⚡ Deleted webhook {webhook.id}")
                return
            except discord.NotFound:
                return
            except:
                await asyncio.sleep(0.05)

    async def _nuke_channel_webhooks(self, channel: discord.TextChannel, keep_known: bool = True):
        """Delete ALL webhooks from a channel"""
        try:
            webhooks = await channel.webhooks()
            known = self.known_webhooks[channel.guild.id].get(channel.id, set()) if keep_known else set()
            for webhook in webhooks:
                if webhook.id not in known:
                    self.deleted_webhooks.add(webhook.id)
                    asyncio.create_task(self._force_delete_webhook(webhook))
        except:
            pass

    # ==================== EVENT LISTENERS ====================

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info("⚡ ULTRA AntiNuke v3: Initializing...")
        for guild in self.bot.guilds:
            await self.cache_guild(guild)
        logger.info(f"⚡ ULTRA AntiNuke v3: Ready - COMPLETE PROTECTION ACTIVE")

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        await self.cache_guild(guild)

    # ============ SERVER SETTINGS PROTECTION ============
    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild):
        """Detect and revert unauthorized server settings changes"""
        settings = await self.get_settings(after.id)
        if not settings['enabled']:
            return

        # Check what changed
        changes = []
        if before.name != after.name:
            changes.append(('name', before.name, after.name))
        if before.verification_level != after.verification_level:
            changes.append(('verification_level', str(before.verification_level), str(after.verification_level)))
        if before.icon != after.icon:
            changes.append(('icon', 'changed', 'modified'))
        if before.banner != after.banner:
            changes.append(('banner', 'changed', 'modified'))
        if before.vanity_url_code != after.vanity_url_code:
            changes.append(('vanity_url', before.vanity_url_code, after.vanity_url_code))
        if before.description != after.description:
            changes.append(('description', 'changed', 'modified'))

        if not changes:
            return

        # Find who made the change via audit log
        try:
            await asyncio.sleep(0.5)  # Brief delay for audit log
            async for entry in after.audit_logs(limit=5, action=discord.AuditLogAction.guild_update):
                if entry.target and entry.target.id == after.id:
                    actor = entry.user

                    if actor.id == self.bot.user.id:
                        return

                    # Check if actor is trusted
                    if self.is_trusted(after, actor.id):
                        # Update backup for trusted changes
                        self.server_settings_backup[after.id] = await self._backup_server_settings(after)
                        return

                    # UNTRUSTED USER CHANGED SERVER SETTINGS - INSTANT PUNISHMENT
                    logger.critical(f"🚨 UNAUTHORIZED SERVER SETTINGS CHANGE in {after.name} by {actor}")

                    # Get backup to restore
                    backup = self.server_settings_backup.get(after.id)
                    if not backup:
                        backup = await self._backup_server_settings(before)
                        self.server_settings_backup[after.id] = backup

                    # Step 1: Instant punishment (ban)
                    punishment = settings.get('punishment', 'ban')
                    await self.instant_punish(after, actor.id, f"Unauthorized server settings change: {', '.join([c[0] for c in changes])}")

                    # Step 2: Revert changes
                    try:
                        revert_kwargs = {}
                        for change_type, old_val, new_val in changes:
                            if change_type == 'name':
                                revert_kwargs['name'] = old_val
                            elif change_type == 'verification_level':
                                revert_kwargs['verification_level'] = before.verification_level
                            elif change_type == 'description':
                                revert_kwargs['description'] = before.description

                        if revert_kwargs:
                            await after.edit(**revert_kwargs, reason=f"[ANTINUKE] Reverted unauthorized changes by {actor}")
                            logger.info(f"✅ Reverted server settings: {list(revert_kwargs.keys())}")
                    except Exception as e:
                        logger.error(f"Failed to revert server settings: {e}")

                    # Step 3: Log the event
                    change_details = "\n".join([f"• {c[0]}: `{c[1]}` → `{c[2]}`" for c in changes])
                    await self.log_security_event(
                        after,
                        "SERVER SETTINGS ATTACK BLOCKED",
                        f"Unauthorized server modification detected and reverted",
                        attacker=actor,
                        action_taken=f"{punishment.upper()} + Reverted changes",
                        color=discord.Color.red()
                    )

                    self.attack_stats[after.id]['Server Settings Blocked'] += 1
                    self.attack_stats[after.id]['total'] += 1
                    return

        except discord.Forbidden:
            logger.warning("Missing audit log permissions for guild update detection")
        except Exception as e:
            logger.error(f"Error in on_guild_update: {e}")

    # ============ ANTI-INTEGRATION - BLOCK UNAUTHORIZED APPS/INTEGRATIONS ============
    @commands.Cog.listener()
    async def on_integration_create(self, integration: discord.Integration):
        """Block unauthorized integrations and apps being added to the server

        Integrations include: Twitch, YouTube, third-party apps, OAuth2 apps,
        external services like Zapier, IFTTT, GitHub, etc.
        """
        guild = integration.guild
        settings = await self.get_settings(guild.id)

        if not settings['enabled'] or not settings.get('anti_integration', True):
            return

        # Find who added the integration
        try:
            await asyncio.sleep(0.3)
            async for entry in guild.audit_logs(limit=3, action=discord.AuditLogAction.integration_create):
                if entry.id not in self.processed_entries:
                    self.processed_entries.add(entry.id)
                    actor = entry.user

                    if actor.id == self.bot.user.id:
                        return

                    # Check if actor is trusted
                    if self.is_trusted(guild, actor.id):
                        logger.info(f"✅ Integration '{integration.name}' added by trusted user {actor}")
                        return

                    # UNTRUSTED USER ADDED INTEGRATION - DELETE + PUNISH
                    logger.critical(f"🚨 UNAUTHORIZED INTEGRATION in {guild.name}: {actor} added '{integration.name}'")

                    # Step 1: Delete the integration
                    try:
                        await integration.delete(reason=f"[ANTINUKE] Unauthorized integration by {actor}")
                        logger.info(f"⚡ Deleted unauthorized integration: {integration.name}")
                    except Exception as e:
                        logger.error(f"Failed to delete integration: {e}")

                    # Step 2: Punish the attacker
                    await self.instant_punish(guild, actor.id, f"Added unauthorized integration: {integration.name}")

                    # Step 3: Log
                    await self.log_security_event(
                        guild,
                        "UNAUTHORIZED INTEGRATION BLOCKED",
                        f"Integration `{integration.name}` was added and removed",
                        attacker=actor,
                        action_taken="Integration deleted + Attacker punished",
                        color=discord.Color.red()
                    )

                    self.attack_stats[guild.id]['Integration Blocked'] += 1
                    self.attack_stats[guild.id]['total'] += 1
                    return

        except discord.Forbidden:
            logger.warning("Missing audit log permissions for integration detection")
        except Exception as e:
            logger.error(f"Error in on_integration_create: {e}")

    @commands.Cog.listener()
    async def on_integration_update(self, integration: discord.Integration):
        """Detect unauthorized integration modifications"""
        guild = integration.guild
        settings = await self.get_settings(guild.id)

        if not settings['enabled'] or not settings.get('anti_integration', True):
            return

        try:
            async for entry in guild.audit_logs(limit=3, action=discord.AuditLogAction.integration_update):
                if entry.id not in self.processed_entries:
                    self.processed_entries.add(entry.id)
                    actor = entry.user

                    if actor.id == self.bot.user.id:
                        return

                    if self.is_trusted(guild, actor.id):
                        return

                    logger.critical(f"🚨 UNAUTHORIZED INTEGRATION UPDATE in {guild.name} by {actor}")
                    await self.instant_punish(guild, actor.id, f"Modified integration: {integration.name}")

                    await self.log_security_event(
                        guild,
                        "INTEGRATION MODIFICATION BLOCKED",
                        f"Integration `{integration.name}` was modified",
                        attacker=actor,
                        action_taken="Attacker punished",
                        color=discord.Color.red()
                    )
                    return

        except Exception as e:
            logger.error(f"Error in on_integration_update: {e}")

    # ============ BAN/KICK DETECTION - INSTANT PUNISHMENT ============
    @commands.Cog.listener()
    async def on_audit_log_entry_create(self, entry: discord.AuditLogEntry):
        """Detect bans and kicks by untrusted users - INSTANT PUNISHMENT"""
        guild = entry.guild
        settings = await self.get_settings(guild.id)
        if not settings['enabled']:
            return

        # Check for ban actions
        if entry.action == discord.AuditLogAction.ban:
            if not settings.get('anti_ban', True):
                return

            actor = entry.user
            target = entry.target

            if actor.id == self.bot.user.id:
                return

            # Check if actor is trusted
            if self.is_trusted(guild, actor.id):
                return

            # UNTRUSTED USER BANNED SOMEONE - INSTANT PUNISHMENT
            logger.critical(f"🚨 UNAUTHORIZED BAN in {guild.name}: {actor} banned {target}")

            # Step 1: Instant punishment
            await self.instant_punish(guild, actor.id, f"Unauthorized ban of {target}")

            # Step 2: Unban the victim
            try:
                if isinstance(target, (discord.User, discord.Member)):
                    await guild.unban(target, reason=f"[ANTINUKE] Reverted unauthorized ban by {actor}")
                    logger.info(f"✅ Unbanned {target} (victim of unauthorized ban)")
            except Exception as e:
                logger.warning(f"Could not unban victim: {e}")

            # Step 3: Log
            await self.log_security_event(
                guild,
                "UNAUTHORIZED BAN BLOCKED",
                f"Ban by untrusted user detected and reverted",
                attacker=actor,
                action_taken=f"Punished attacker + Unbanned victim",
                color=discord.Color.red()
            )

            self.attack_stats[guild.id]['Unauthorized Ban Blocked'] += 1
            self.attack_stats[guild.id]['total'] += 1
            return

        # Check for kick actions
        if entry.action == discord.AuditLogAction.kick:
            actor = entry.user
            target = entry.target

            if actor.id == self.bot.user.id:
                return

            # Check if actor is trusted
            if self.is_trusted(guild, actor.id):
                return

            # UNTRUSTED USER KICKED SOMEONE - INSTANT PUNISHMENT
            logger.critical(f"🚨 UNAUTHORIZED KICK in {guild.name}: {actor} kicked {target}")

            # Instant punishment
            await self.instant_punish(guild, actor.id, f"Unauthorized kick of {target}")

            # Log
            await self.log_security_event(
                guild,
                "UNAUTHORIZED KICK BLOCKED",
                f"Kick by untrusted user detected",
                attacker=actor,
                action_taken="Punished attacker",
                color=discord.Color.red()
            )

            self.attack_stats[guild.id]['Unauthorized Kick Blocked'] += 1
            self.attack_stats[guild.id]['total'] += 1
            return

        # Check for member prune (mass kick)
        if entry.action == discord.AuditLogAction.member_prune:
            actor = entry.user

            if actor.id == self.bot.user.id:
                return

            if self.is_trusted(guild, actor.id):
                return

            logger.critical(f"🚨 UNAUTHORIZED MEMBER PRUNE in {guild.name} by {actor}")

            await self.instant_punish(guild, actor.id, "Unauthorized member prune")

            await self.log_security_event(
                guild,
                "MEMBER PRUNE BLOCKED",
                f"Mass member prune by untrusted user",
                attacker=actor,
                action_taken="Punished attacker",
                color=discord.Color.red()
            )

            self.attack_stats[guild.id]['Member Prune Blocked'] += 1
            self.attack_stats[guild.id]['total'] += 1

    # ============ WEBHOOK MESSAGE - DELETE IMMEDIATELY ============
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Delete messages from unauthorized webhooks AND delete the webhook"""
        if not message.webhook_id or not message.guild:
            return

        # CRITICAL: Skip bot's own interaction responses (slash commands)
        # Interaction responses come through as webhook messages
        if message.author.id == self.bot.user.id:
            return

        # Skip messages from the bot's application (slash command responses)
        if message.application_id == self.bot.user.id:
            return

        # Skip if the message author is a bot (includes interaction webhooks)
        if message.author.bot and message.author.id == self.bot.user.id:
            return

        # FIXED: Skip messages from TRUSTED BOTS
        # Trusted bots can use webhooks freely
        if message.author.id in self.trusted_bots.get(message.guild.id, set()):
            return

        # FIXED: Skip messages from bots in known_bots (already in server before antinuke)
        if message.author.id in self.known_bots.get(message.guild.id, set()):
            return

        # FIXED: Skip if the message author (bot) is fully trusted (includes whitelisted roles)
        if self.is_trusted(message.guild, message.author.id):
            return

        # FIXED: Check if the bot has a WHITELISTED ROLE
        member = message.guild.get_member(message.author.id)
        if member:
            whitelist_cog = self.bot.get_cog('Whitelist')
            if whitelist_cog and whitelist_cog.has_whitelisted_role(message.guild.id, member):
                return

        # FIXED: Skip application/interaction webhooks from other bots
        # These are used by bots for buttons, select menus, slash commands, etc.
        if message.interaction_metadata is not None:
            return

        # FIXED: Skip if the message has application_id (it's from an app/bot)
        if message.application_id is not None:
            # Check if the application is a trusted bot
            if message.application_id in self.trusted_bots.get(message.guild.id, set()):
                return
            if message.application_id in self.known_bots.get(message.guild.id, set()):
                return
            # Check if the application is trusted (includes whitelisted roles)
            if self.is_trusted(message.guild, message.application_id):
                return

        # If webhook is already marked as deleted, just delete the message
        if message.webhook_id in self.deleted_webhooks:
            asyncio.create_task(self._safe_delete(message))
            return

        settings = await self.get_settings(message.guild.id)
        if not settings['enabled'] or not settings['anti_webhook']:
            return

        known = self.known_webhooks[message.guild.id].get(message.channel.id, set())

        if message.webhook_id not in known:
            # MARK AS DELETED IMMEDIATELY - blocks further messages
            self.deleted_webhooks.add(message.webhook_id)
            self.blacklisted_webhooks[message.guild.id].add(message.webhook_id)

            # DELETE MESSAGE FIRST
            asyncio.create_task(self._safe_delete(message))

            # DELETE WEBHOOK - multiple methods
            asyncio.create_task(self._delete_webhook_emergency(message.guild, message.channel, message.webhook_id))

            # PURGE ALL MESSAGES FROM THIS WEBHOOK
            asyncio.create_task(self._purge_webhook_messages(message.channel, [message.webhook_id]))

            # NUKE ALL WEBHOOKS IN CHANNEL (except known)
            asyncio.create_task(self._nuke_channel_webhooks(message.channel))

            # Log
            await self.log_security_event(
                message.guild,
                "Webhook Spam Blocked",
                f"Message from unauthorized webhook deleted\n**Channel:** {message.channel.mention}",
                action_taken="Message deleted + Webhook destroyed"
            )

    async def _safe_delete(self, message):
        try:
            await message.delete()
        except:
            pass

    async def _delete_webhook_emergency(self, guild, channel, webhook_id):
        """Emergency webhook deletion with multiple parallel attempts"""
        if webhook_id in self.deleted_webhooks:
            pass  # Continue anyway to ensure deletion

        self.deleted_webhooks.add(webhook_id)

        async def method1():
            try:
                webhook = await self.bot.fetch_webhook(webhook_id)
                if webhook:
                    creator_id = webhook.user.id if webhook.user else None
                    await webhook.delete(reason="[ANTINUKE] Emergency delete")
                    logger.critical(f"⚡ EMERGENCY DELETED WEBHOOK {webhook_id}")
                    if creator_id and not self.is_trusted(guild, creator_id):
                        await self.instant_punish(guild, creator_id, f"Webhook spam in #{channel.name}")
            except discord.NotFound:
                pass
            except:
                pass

        async def method2():
            await asyncio.sleep(0.05)
            try:
                webhook = await self.bot.fetch_webhook(webhook_id)
                await webhook.delete(reason="[ANTINUKE] Emergency delete 2")
            except:
                pass

        async def method3():
            await asyncio.sleep(0.1)
            try:
                webhook = await self.bot.fetch_webhook(webhook_id)
                await webhook.delete(reason="[ANTINUKE] Emergency delete 3")
            except:
                pass

        async def method4():
            # Delete via channel webhooks
            try:
                webhooks = await channel.webhooks()
                for wh in webhooks:
                    if wh.id == webhook_id:
                        await wh.delete(reason="[ANTINUKE] Emergency delete 4")
                        break
            except:
                pass

        # Run ALL methods in parallel
        await asyncio.gather(method1(), method2(), method3(), method4(), return_exceptions=True)

    async def _purge_webhook_messages(self, channel, webhook_ids):
        try:
            deleted = await channel.purge(limit=100, check=lambda m: m.webhook_id in webhook_ids)
            if deleted:
                logger.info(f"🧹 Purged {len(deleted)} messages")
        except:
            pass

    # ============ WEBHOOK CREATE - INSTANT DELETE ============
    @commands.Cog.listener()
    async def on_webhooks_update(self, channel: discord.TextChannel):
        guild = channel.guild
        settings = await self.get_settings(guild.id)
        if not settings['enabled'] or not settings['anti_webhook']:
            return

        try:
            current = await channel.webhooks()
        except:
            return

        current_ids = {w.id for w in current}
        known_ids = self.known_webhooks[guild.id].get(channel.id, set())
        new_webhooks = [w for w in current if w.id not in known_ids]

        if not new_webhooks:
            self.known_webhooks[guild.id][channel.id] = current_ids
            return

        # DELETE ALL NEW WEBHOOKS IMMEDIATELY - BEFORE THEY CAN SEND MESSAGES
        for webhook in new_webhooks:
            # SKIP webhooks created by this bot (for slash commands/interactions)
            if webhook.user and webhook.user.id == self.bot.user.id:
                self.known_webhooks[guild.id][channel.id].add(webhook.id)
                continue

            # SKIP application webhooks (Discord's interaction system)
            if webhook.type == discord.WebhookType.application:
                self.known_webhooks[guild.id][channel.id].add(webhook.id)
                continue

            # FIXED: SKIP webhooks created by TRUSTED BOTS
            if webhook.user and webhook.user.id in self.trusted_bots.get(guild.id, set()):
                self.known_webhooks[guild.id][channel.id].add(webhook.id)
                logger.info(f"✅ Allowed webhook from trusted bot: {webhook.user}")
                continue

            # FIXED: SKIP webhooks created by KNOWN BOTS (bots already in server)
            if webhook.user and webhook.user.id in self.known_bots.get(guild.id, set()):
                self.known_webhooks[guild.id][channel.id].add(webhook.id)
                logger.info(f"✅ Allowed webhook from known bot: {webhook.user}")
                continue

            # FIXED: SKIP webhooks created by TRUSTED USERS (includes is_trusted check)
            if webhook.user and self.is_trusted(guild, webhook.user.id):
                self.known_webhooks[guild.id][channel.id].add(webhook.id)
                logger.info(f"✅ Allowed webhook from trusted user: {webhook.user}")
                continue

            # FIXED: SKIP webhooks created by bots/users with WHITELISTED ROLES
            if webhook.user:
                member = guild.get_member(webhook.user.id)
                if member:
                    whitelist_cog = self.bot.get_cog('Whitelist')
                    if whitelist_cog and whitelist_cog.has_whitelisted_role(guild.id, member):
                        self.known_webhooks[guild.id][channel.id].add(webhook.id)
                        logger.info(f"✅ Allowed webhook from user with whitelisted role: {webhook.user}")
                        continue

            # ============ INSTANT WEBHOOK DESTRUCTION ============
            logger.critical(f"🚨 UNAUTHORIZED WEBHOOK DETECTED: {webhook.id} in #{channel.name}")

            # Mark as deleted IMMEDIATELY
            self.blacklisted_webhooks[guild.id].add(webhook.id)
            self.deleted_webhooks.add(webhook.id)

            creator_id = webhook.user.id if webhook.user else None

            # PARALLEL: Delete webhook + Punish creator simultaneously
            asyncio.create_task(self._instant_destroy_webhook(webhook, guild, creator_id))

        # Keep known webhooks only
        self.known_webhooks[guild.id][channel.id] = known_ids.copy()

    async def _instant_destroy_webhook(self, webhook: discord.Webhook, guild: discord.Guild, creator_id: int = None):
        """Instantly destroy webhook and punish creator - PARALLEL OPERATIONS"""
        webhook_id = webhook.id

        # Run deletion and punishment in parallel for speed
        tasks = []

        # Multiple deletion attempts
        async def delete_webhook():
            for attempt in range(5):
                try:
                    await webhook.delete(reason="[ANTINUKE] Unauthorized webhook - INSTANT DELETE")
                    logger.critical(f"⚡ DESTROYED webhook {webhook_id}")
                    return True
                except discord.NotFound:
                    return True  # Already deleted
                except:
                    await asyncio.sleep(0.02)
            return False

        tasks.append(delete_webhook())

        # Punish creator if found
        if creator_id and not self.is_trusted(guild, creator_id):
            logger.critical(f"⚡ PUNISHING webhook creator: {creator_id}")
            tasks.append(self._instant_strip_roles(guild, creator_id))
            tasks.append(self._instant_ban_user(guild, creator_id, f"Created unauthorized webhook"))

        # Execute all in parallel
        await asyncio.gather(*tasks, return_exceptions=True)

        # Log the attack
        if creator_id:
            try:
                attacker = await self.bot.fetch_user(creator_id)
                await self.log_security_event(
                    guild,
                    "WEBHOOK ATTACK BLOCKED",
                    f"Webhook `{webhook_id}` destroyed instantly",
                    attacker=attacker,
                    action_taken="INSTANT: Webhook deleted + Creator banned",
                    color=discord.Color.red()
                )
            except:
                pass

            self.attack_stats[guild.id]['Webhook Blocked'] += 1
            self.attack_stats[guild.id]['total'] += 1

    # ============ CHANNEL CREATE ============
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        guild = channel.guild
        settings = await self.get_settings(guild.id)

        if not settings['enabled'] or not settings['anti_channel_create']:
            self.known_channels[guild.id].add(channel.id)
            self.channel_names[guild.id][channel.id] = channel.name
            return

        if channel.id in self.known_channels.get(guild.id, set()):
            return

        # CHECK WHO CREATED IT FIRST - Don't delete if trusted!
        creator_id = None
        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_create):
                if entry.target.id == channel.id:
                    creator_id = entry.user.id
                    self.processed_entries.add(entry.id)
                    break
        except:
            pass

        # If creator is trusted (owner/whitelisted), allow the channel
        if creator_id and self.is_trusted(guild, creator_id):
            self.known_channels[guild.id].add(channel.id)
            self.channel_names[guild.id][channel.id] = channel.name

            # Backup the new channel and save to database
            try:
                backup = await self._backup_channel(channel)
                self.channel_backups[guild.id][channel.id] = backup
                if self.db:
                    await self.db.save_channel_backup(guild.id, channel.id, backup)
            except:
                pass

            logger.info(f"✅ Allowed channel #{channel.name} by trusted user {creator_id}")
            return

        # Store channel info for potential restore before deleting
        channel_info = {
            'name': channel.name,
            'type': str(channel.type),
            'category_id': channel.category_id if hasattr(channel, 'category_id') else None,
            'position': channel.position,
            'created_by': creator_id,
            'deleted_at': datetime.utcnow(),
        }
        if not hasattr(self, 'deleted_channels'):
            self.deleted_channels = defaultdict(list)
        self.deleted_channels[guild.id].append(channel_info)
        # Keep only last 20 deleted channels
        self.deleted_channels[guild.id] = self.deleted_channels[guild.id][-20:]

        # DELETE - only for untrusted users
        try:
            await channel.delete(reason="[ANTINUKE] Unauthorized")
            logger.info(f"⚡ Deleted #{channel.name} by untrusted user {creator_id}")
        except:
            pass

        # Log and punish
        if creator_id:
            try:
                attacker = guild.get_member(creator_id) or await self.bot.fetch_user(creator_id)
                await self.log_security_event(
                    guild,
                    "Channel Create Blocked",
                    f"Unauthorized channel `#{channel.name}` deleted",
                    attacker=attacker,
                    action_taken="Channel deleted + Creator banned"
                )
                await self.instant_punish(guild, creator_id, f"Created channel #{channel.name}")
            except:
                pass

    # ============ CHANNEL RENAME - ULTRA AGGRESSIVE ============
    @commands.Cog.listener()
    async def on_guild_channel_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        if before.name == after.name:
            return

        guild = after.guild
        settings = await self.get_settings(guild.id)

        if not settings['enabled'] or not settings['anti_channel_rename']:
            self.channel_names[guild.id][after.id] = after.name
            return

        logger.critical(f"🚨 CHANNEL RENAME DETECTED: #{before.name} → #{after.name} in {guild.name}")

        # Get original name from cache
        original = self.channel_names[guild.id].get(after.id, before.name)

        # STEP 1: IMMEDIATELY REVERT (don't wait for audit log)
        revert_task = asyncio.create_task(self._instant_revert_channel(after, original))

        # STEP 2: Find attacker in audit logs (parallel)
        editor_id = None
        editor = None
        try:
            async for entry in guild.audit_logs(limit=3, action=discord.AuditLogAction.channel_update):
                if entry.target.id == after.id and entry.id not in self.processed_entries:
                    self.processed_entries.add(entry.id)
                    editor_id = entry.user.id
                    editor = entry.user
                    break
        except:
            pass

        # STEP 3: Check if trusted AFTER starting revert
        if editor_id and self.is_trusted(guild, editor_id):
            # Cancel revert if trusted
            revert_task.cancel()
            self.channel_names[guild.id][after.id] = after.name
            logger.info(f"✅ Allowed rename by trusted user {editor_id}")
            return

        # Wait for revert to complete
        try:
            await revert_task
        except asyncio.CancelledError:
            pass

        # STEP 4: INSTANT PUNISHMENT (parallel operations)
        if editor_id:
            logger.critical(f"⚡ PUNISHING {editor_id} for channel rename")

            # Run all punishment steps in parallel for speed
            await asyncio.gather(
                self._instant_strip_roles(guild, editor_id),
                self._instant_ban_user(guild, editor_id, f"Renamed channel #{before.name}"),
                return_exceptions=True
            )

            # Log the event
            await self.log_security_event(
                guild,
                "CHANNEL RENAME BLOCKED",
                f"`#{before.name}` → `#{after.name}` → `#{original}`",
                attacker=editor,
                action_taken="INSTANT: Reverted + Roles stripped + Banned",
                color=discord.Color.red()
            )

            self.attack_stats[guild.id]['Channel Rename Blocked'] += 1
            self.attack_stats[guild.id]['total'] += 1

    async def _instant_revert_channel(self, channel: discord.abc.GuildChannel, original_name: str):
        """Instantly revert channel name with retries"""
        for attempt in range(3):
            try:
                await channel.edit(name=original_name, reason="[ANTINUKE] Instant revert")
                logger.info(f"⚡ Reverted channel to #{original_name}")
                return True
            except discord.Forbidden:
                logger.error(f"❌ No permission to revert channel")
                return False
            except Exception as e:
                if attempt < 2:
                    await asyncio.sleep(0.1)
                else:
                    logger.error(f"❌ Failed to revert after 3 attempts: {e}")
        return False

    async def _instant_strip_roles(self, guild: discord.Guild, user_id: int):
        """Instantly strip all roles from user"""
        try:
            member = guild.get_member(user_id)
            if member and member.top_role < guild.me.top_role:
                await member.edit(roles=[], reason="[ANTINUKE] Instant punishment")
                logger.info(f"⚡ Stripped roles from {user_id}")
        except Exception as e:
            logger.error(f"Failed to strip roles: {e}")

    async def _instant_ban_user(self, guild: discord.Guild, user_id: int, reason: str):
        """Instantly ban user with retries"""
        for attempt in range(3):
            try:
                await guild.ban(discord.Object(id=user_id), reason=f"[ANTINUKE] {reason}", delete_message_days=0)
                logger.info(f"⚡ Banned {user_id}")
                return True
            except discord.NotFound:
                return True  # Already banned/left
            except discord.Forbidden:
                logger.error(f"❌ No permission to ban {user_id}")
                return False
            except Exception as e:
                if attempt < 2:
                    await asyncio.sleep(0.05)
        return False

    # ============ CHANNEL DELETE ============
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        guild = channel.guild
        self.known_channels[guild.id].discard(channel.id)
        self.channel_names[guild.id].pop(channel.id, None)

        # Store channel info for restore (always store, even if trusted deleted it)
        channel_info = {
            'name': channel.name,
            'type': str(channel.type),
            'category_id': channel.category_id if hasattr(channel, 'category_id') else None,
            'position': channel.position,
            'deleted_at': datetime.utcnow(),
            'id': channel.id,
        }
        if not hasattr(self, 'deleted_channels'):
            self.deleted_channels = defaultdict(list)
        self.deleted_channels[guild.id].append(channel_info)
        # Keep only last 20 deleted channels
        self.deleted_channels[guild.id] = self.deleted_channels[guild.id][-20:]

        settings = await self.get_settings(guild.id)
        if not settings['enabled'] or not settings['anti_channel_delete']:
            return

        logger.critical(f"🚨 CHANNEL DELETE DETECTED: #{channel.name} in {guild.name}")

        # ============ ULTRA AGGRESSIVE - INSTANT RESPONSE ============
        # 1. Start punishment IMMEDIATELY (parallel with audit log check)
        # 2. Check audit logs while punishing
        # 3. Cancel punishment only if attacker is trusted

        # Find deleter from audit logs
        deleter_id = None
        deleter = None
        try:
            async for entry in guild.audit_logs(limit=3, action=discord.AuditLogAction.channel_delete):
                if entry.target.id == channel.id and entry.id not in self.processed_entries:
                    self.processed_entries.add(entry.id)
                    deleter_id = entry.user.id
                    deleter = entry.user
                    logger.critical(f"🚨 Channel deleted by: {deleter} ({deleter_id})")
                    break
        except discord.Forbidden:
            logger.warning("Missing audit log permissions")
        except:
            pass

        # If deleter is trusted, allow
        if deleter_id and self.is_trusted(guild, deleter_id):
            logger.info(f"✅ Channel #{channel.name} deleted by trusted user {deleter_id}")
            return

        # ============ INSTANT PUNISHMENT - NO MERCY ============
        if deleter_id:
            logger.critical(f"⚡ INSTANT PUNISHMENT for {deleter_id}")

            # Mark nuke in progress
            self.nuke_in_progress[guild.id] = True
            self.nuke_attacker[guild.id] = deleter_id

            # ALL PUNISHMENT IN PARALLEL - Maximum speed
            await asyncio.gather(
                self._instant_strip_roles(guild, deleter_id),
                self._instant_ban_user(guild, deleter_id, f"Deleted channel #{channel.name}"),
                self._emergency_remove_all_permissions(guild, deleter_id),
                return_exceptions=True
            )

            # Log the attack
            await self.log_security_event(
                guild,
                "CHANNEL DELETE BLOCKED",
                f"Channel `#{channel.name}` deleted - attacker INSTANTLY punished",
                attacker=deleter,
                action_taken="INSTANT: Roles stripped + Banned + Permissions removed",
                color=discord.Color.dark_red()
            )

            self.attack_stats[guild.id]['Channel Delete Blocked'] += 1
            self.attack_stats[guild.id]['total'] += 1

        # Trigger mass restore
        if not self.first_delete_handled.get(guild.id):
            self.first_delete_handled[guild.id] = True
            asyncio.create_task(self._delayed_mass_restore(guild, deleter_id))

    # ============ ROLE CREATE - NEW ============
    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        guild = role.guild
        settings = await self.get_settings(guild.id)

        if not settings['enabled'] or not settings['anti_role_create']:
            self.known_roles[guild.id].add(role.id)
            return

        if role.id in self.known_roles.get(guild.id, set()):
            return

        # Check if role has dangerous permissions
        is_dangerous = self.has_dangerous_permissions(role.permissions)

        # DELETE IMMEDIATELY if dangerous
        if is_dangerous:
            try:
                await role.delete(reason="[ANTINUKE] Dangerous role created")
                logger.info(f"⚡ Deleted dangerous role @{role.name}")
            except:
                pass

        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_create):
                if entry.target.id == role.id and entry.id not in self.processed_entries:
                    self.processed_entries.add(entry.id)
                    if not self.is_trusted(guild, entry.user.id):
                        if is_dangerous:
                            await self.log_security_event(
                                guild,
                                "Dangerous Role Blocked",
                                f"Role `@{role.name}` with dangerous permissions deleted",
                                attacker=entry.user,
                                action_taken="Role deleted + Creator banned"
                            )
                            await self.instant_punish(guild, entry.user.id, f"Created dangerous role @{role.name}")
                break
        except:
            pass

        # Add to known roles if not deleted
        if not is_dangerous:
            self.known_roles[guild.id].add(role.id)

    # ============ ROLE UPDATE - PERMISSION CHANGES ============
    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        guild = after.guild
        settings = await self.get_settings(guild.id)

        if not settings['enabled'] or not settings['anti_role_update']:
            return

        # Check if permissions were changed to add dangerous permissions
        before_dangerous = self.has_dangerous_permissions(before.permissions)
        after_dangerous = self.has_dangerous_permissions(after.permissions)

        if not before_dangerous and after_dangerous:
            # REVERT IMMEDIATELY
            try:
                await after.edit(permissions=before.permissions, reason="[ANTINUKE] Reverted dangerous permissions")
                logger.info(f"⚡ Reverted permissions on @{after.name}")
            except:
                pass

            try:
                async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_update):
                    if entry.target.id == after.id and entry.id not in self.processed_entries:
                        self.processed_entries.add(entry.id)
                        if not self.is_trusted(guild, entry.user.id):
                            await self.log_security_event(
                                guild,
                                "Permission Escalation Blocked",
                                f"Dangerous permissions on `@{after.name}` reverted",
                                attacker=entry.user,
                                action_taken="Permissions reverted + Attacker banned"
                            )
                            await self.instant_punish(guild, entry.user.id, f"Added dangerous perms to @{after.name}")
                    break
            except:
                pass

    # ============ ROLE DELETE ============
    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        guild = role.guild
        self.known_roles[guild.id].discard(role.id)

        settings = await self.get_settings(guild.id)
        if not settings['enabled'] or not settings['anti_role_delete']:
            return

        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
                if entry.target.id == role.id and entry.id not in self.processed_entries:
                    self.processed_entries.add(entry.id)
                    if not self.is_trusted(guild, entry.user.id):
                        await self.log_security_event(
                            guild,
                            "Role Delete Detected",
                            f"Role `@{role.name}` was deleted",
                            attacker=entry.user,
                            action_taken="Attacker banned"
                        )
                        await self.instant_punish(guild, entry.user.id, f"Deleted @{role.name}")
                break
        except:
            pass

    # ============ MEMBER UPDATE - DANGEROUS ROLE GRANT ============
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if before.roles == after.roles:
            return

        guild = after.guild
        settings = await self.get_settings(guild.id)

        if not settings['enabled'] or not settings['anti_permissions']:
            self.member_roles[guild.id][after.id] = {r.id for r in after.roles}
            return

        # Check for new roles with dangerous permissions
        new_roles = set(after.roles) - set(before.roles)
        dangerous_roles = [r for r in new_roles if self.has_dangerous_permissions(r.permissions)]

        if not dangerous_roles:
            self.member_roles[guild.id][after.id] = {r.id for r in after.roles}
            return

        # FIRST: Check WHO granted the role via audit logs
        granter_id = None
        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.member_role_update):
                if entry.target.id == after.id and entry.id not in self.processed_entries:
                    granter_id = entry.user.id
                    self.processed_entries.add(entry.id)
                    break
        except:
            pass

        # If the GRANTER is trusted (owner/whitelisted), allow the role grant
        if granter_id and self.is_trusted(guild, granter_id):
            logger.info(f"✅ Allowed dangerous role grant to {after} by trusted user {granter_id}")
            self.member_roles[guild.id][after.id] = {r.id for r in after.roles}
            return

        # If the member receiving the role is already trusted, allow it
        if self.is_trusted(guild, after.id):
            logger.info(f"✅ Allowed dangerous role for trusted user {after}")
            self.member_roles[guild.id][after.id] = {r.id for r in after.roles}
            return

        # UNTRUSTED granter - REMOVE DANGEROUS ROLES
        try:
            roles_to_keep = [r for r in after.roles if r not in dangerous_roles]
            await after.edit(roles=roles_to_keep, reason="[ANTINUKE] Removed dangerous roles - unauthorized grant")
            logger.info(f"⚡ Removed dangerous roles from {after} (granted by untrusted user)")
        except:
            pass

        # Log and punish the untrusted granter
        if granter_id and granter_id != after.id:
            try:
                granter = guild.get_member(granter_id) or await self.bot.fetch_user(granter_id)
                await self.log_security_event(
                    guild,
                    "Dangerous Role Grant Blocked",
                    f"Dangerous roles removed from {after.mention}\n**Roles:** {', '.join([r.name for r in dangerous_roles])}",
                    attacker=granter,
                    action_taken="Roles removed + Granter banned"
                )
                await self.instant_punish(guild, granter_id, f"Gave dangerous roles to {after}")
            except:
                pass

        self.member_roles[guild.id][after.id] = {r.id for r in after.roles}

    # ============ BOT ADD - NEW ============
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if not member.bot:
            return

        guild = member.guild
        settings = await self.get_settings(guild.id)

        if not settings['enabled'] or not settings['anti_bot']:
            self.known_bots[guild.id].add(member.id)
            return

        if member.id in self.known_bots.get(guild.id, set()):
            return

        if member.id == self.bot.user.id:
            return

        # KICK IMMEDIATELY
        try:
            await member.kick(reason="[ANTINUKE] Unauthorized bot")
            logger.info(f"⚡ Kicked unauthorized bot {member}")
        except:
            pass

        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.bot_add):
                if entry.target.id == member.id and entry.id not in self.processed_entries:
                    self.processed_entries.add(entry.id)
                    if not self.is_trusted(guild, entry.user.id):
                        await self.log_security_event(
                            guild,
                            "Unauthorized Bot Blocked",
                            f"Bot `{member}` was kicked",
                            attacker=entry.user,
                            action_taken="Bot kicked + Adder banned"
                        )
                        await self.instant_punish(guild, entry.user.id, f"Added unauthorized bot {member}")
                break
        except:
            pass

    # ============ BAN DETECTION ============
    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        settings = await self.get_settings(guild.id)
        if not settings['enabled'] or not settings['anti_ban']:
            return

        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
                if entry.target.id == user.id and entry.id not in self.processed_entries:
                    self.processed_entries.add(entry.id)
                    if not self.is_trusted(guild, entry.user.id):
                        try:
                            await guild.unban(user, reason="[ANTINUKE] Reverted")
                        except:
                            pass
                        await self.log_security_event(
                            guild,
                            "Unauthorized Ban Blocked",
                            f"Ban on {user.mention} was reverted",
                            attacker=entry.user,
                            action_taken="Victim unbanned + Attacker banned"
                        )
                        await self.instant_punish(guild, entry.user.id, f"Banned {user}")
                break
        except:
            pass

    # ==================== COMMANDS ====================

    @commands.hybrid_command(name="antinuke", description="View anti-nuke protection status")
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.has_permissions(administrator=True)
    async def antinuke_status(self, ctx: commands.Context):
        """View anti-nuke protection status"""
        settings = await self.get_settings(ctx.guild.id)

        status = "enabled" if settings['enabled'] else "disabled"
        trusted_count = len(self.whitelisted.get(ctx.guild.id, set()))
        trusted_bots_count = len(self.trusted_bots.get(ctx.guild.id, set()))
        blocked = len(self.deleted_webhooks)
        attacks = self.attack_stats[ctx.guild.id].get('total', 0)

        # Get whitelisted roles count from Whitelist cog
        whitelisted_roles_count = 0
        whitelist_cog = self.bot.get_cog('Whitelist')
        if whitelist_cog:
            whitelisted_roles_count = len(whitelist_cog.get_whitelisted_roles(ctx.guild.id))

        log_channel = ctx.guild.get_channel(settings.get('log_channel_id')) if settings.get('log_channel_id') else None

        embed = discord.Embed(color=0x2b2d31)
        embed.description = (
            f"**Anti-Nuke Protection**\n\n"
            f"› Status: `{status}`\n"
            f"› Trusted users: `{trusted_count}`\n"
            f"› Trusted bots: `{trusted_bots_count}`\n"
            f"› Whitelisted roles: `{whitelisted_roles_count}`\n"
            f"› Webhooks blocked: `{blocked}`\n"
            f"› Attacks blocked: `{attacks}`\n"
            f"› Log channel: {log_channel.mention if log_channel else '`not set`'}"
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="setlog", description="Set the security log channel")
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.has_permissions(administrator=True)
    async def set_log_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set the security log channel for anti-nuke events"""
        if ctx.author.id != ctx.guild.owner_id and ctx.author.id not in self.owner_ids:
            embed = discord.Embed(description="✖️ Only owner can set log channel", color=0x2b2d31)
            return await ctx.send(embed=embed)

        settings = await self.get_settings(ctx.guild.id)
        settings['log_channel_id'] = channel.id
        await self.save_settings(ctx.guild.id)

        embed = discord.Embed(description=f"➕ Set log channel to {channel.mention}", color=0x2b2d31)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="antinuke_enable", aliases=["antinuke-enable", "an-on"], description="Enable anti-nuke protection")
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.has_permissions(administrator=True)
    async def enable_antinuke(self, ctx: commands.Context):
        """Enable anti-nuke protection"""
        if ctx.author.id != ctx.guild.owner_id and ctx.author.id not in self.owner_ids:
            embed = discord.Embed(description="✖️ Only owner can enable anti-nuke", color=0x2b2d31)
            return await ctx.send(embed=embed)
        settings = await self.get_settings(ctx.guild.id)
        settings['enabled'] = True
        await self.save_settings(ctx.guild.id)
        embed = discord.Embed(description="➕ Enabled anti-nuke protection", color=0x2b2d31)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="antinuke_disable", aliases=["antinuke-disable", "an-off"], description="Disable anti-nuke protection")
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.has_permissions(administrator=True)
    async def disable_antinuke(self, ctx: commands.Context):
        """Disable anti-nuke protection (DANGEROUS)"""
        if ctx.author.id != ctx.guild.owner_id and ctx.author.id not in self.owner_ids:
            embed = discord.Embed(description="✖️ Only owner can disable anti-nuke", color=0x2b2d31)
            return await ctx.send(embed=embed)
        settings = await self.get_settings(ctx.guild.id)
        settings['enabled'] = False
        await self.save_settings(ctx.guild.id)
        embed = discord.Embed(description="➖ Disabled anti-nuke protection", color=0x2b2d31)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="punishment", aliases=["anpunish", "an-punishment"], description="Set punishment type (ban/kick)")
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.has_permissions(administrator=True)
    async def set_punishment(self, ctx: commands.Context, punishment_type: str = None):
        """Set punishment type for anti-nuke (ban/kick)

        Usage: !punishment ban OR !punishment kick
        """
        if ctx.author.id != ctx.guild.owner_id and ctx.author.id not in self.owner_ids:
            embed = discord.Embed(description="✖️ Only owner can change punishment type", color=0x2b2d31)
            return await ctx.send(embed=embed)

        settings = await self.get_settings(ctx.guild.id)
        current = settings.get('punishment', 'ban')

        if not punishment_type:
            embed = discord.Embed(
                description=f"**Anti-Nuke Punishment**\n\n"
                           f"› Current: `{current}`\n\n"
                           f"Usage:\n"
                           f"• `!punishment ban` - Ban attackers\n"
                           f"• `!punishment kick` - Kick attackers",
                color=0x2b2d31
            )
            return await ctx.send(embed=embed)

        punishment_type = punishment_type.lower()
        if punishment_type not in ['ban', 'kick']:
            embed = discord.Embed(description="✖️ Invalid punishment type. Use `ban` or `kick`", color=0x2b2d31)
            return await ctx.send(embed=embed)

        settings['punishment'] = punishment_type
        await self.save_settings(ctx.guild.id)

        embed = discord.Embed(description=f"➕ Anti-nuke punishment set to `{punishment_type}`", color=0x2b2d31)
        await ctx.send(embed=embed)

    # ==================== WHITELIST COMMANDS MOVED ====================
    # All whitelist commands are now in the unified whitelist.py cog
    # Use: !wlist user, !wlist role, !wlist bot
    # Use: !wlist remove user, !wlist remove role, !wlist remove bot
    # Use: !wlist (to view all whitelisted entries)

    def _get_whitelist_cog(self):
        """Get the unified whitelist cog"""
        return self.bot.get_cog('Whitelist')

    def is_whitelisted_unified(self, guild_id: int, user_id: int) -> bool:
        """Check if user is whitelisted using the unified whitelist system"""
        wl_cog = self._get_whitelist_cog()
        if wl_cog:
            return wl_cog.is_whitelisted(guild_id, user_id)
        # Fallback to local cache
        return user_id in self.whitelisted.get(guild_id, set())

    @commands.hybrid_command(name="lockdownstatus", description="View current lockdown status")
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.has_permissions(administrator=True)
    async def lockdown_status(self, ctx: commands.Context):
        """View current lockdown status and bypass configuration"""
        is_locked = self.lockdown_active.get(ctx.guild.id, False)

        # Get whitelist counts from unified whitelist cog
        whitelist_cog = self.bot.get_cog('Whitelist')
        user_count = 0
        bot_count = 0
        role_mentions = []

        if whitelist_cog:
            user_count = len(whitelist_cog.get_whitelisted_users(ctx.guild.id))
            bot_count = len(whitelist_cog.get_whitelisted_bots(ctx.guild.id))
            for rid in whitelist_cog.get_whitelisted_roles(ctx.guild.id):
                role = ctx.guild.get_role(rid)
                if role:
                    role_mentions.append(role.mention)

        status = "🔒 **LOCKED**" if is_locked else "🔓 Unlocked"

        embed = discord.Embed(color=0x2b2d31)
        embed.description = (
            f"**Lockdown Status**\n\n"
            f"› Status: {status}\n"
            f"› Backed up channels: `{len(self.lockdown_permission_backup.get(ctx.guild.id, {}))}`\n\n"
            f"**Whitelist (Bypass Anti-Nuke + Lockdown)**\n"
            f"› Whitelisted users: `{user_count}`\n"
            f"› Whitelisted bots: `{bot_count}`\n"
            f"› Whitelisted roles: {', '.join(role_mentions) if role_mentions else '`None`'}\n"
            f"› Admins/Mods: `Always bypass`\n\n"
            f"*Use `!wlist` to manage whitelist*"
        )
        await ctx.send(embed=embed)

    async def _apply_lockdown_bypass(self, channel: discord.TextChannel, guild: discord.Guild):
        """Apply lockdown bypass permissions for whitelisted users, bots, and roles"""
        bypass_count = 0

        # Get unified whitelist cog
        whitelist_cog = self.bot.get_cog('Whitelist')

        if whitelist_cog:
            # Get whitelisted users
            for user_id in whitelist_cog.get_whitelisted_users(guild.id):
                member = guild.get_member(user_id)
                if member:
                    try:
                        await channel.set_permissions(member, send_messages=True, reason="[LOCKDOWN] Whitelisted user bypass")
                        bypass_count += 1
                    except:
                        pass

            # Get whitelisted bots
            for bot_id in whitelist_cog.get_whitelisted_bots(guild.id):
                member = guild.get_member(bot_id)
                if member:
                    try:
                        await channel.set_permissions(member, send_messages=True, reason="[LOCKDOWN] Whitelisted bot bypass")
                        bypass_count += 1
                    except:
                        pass

            # Get whitelisted roles
            for role_id in whitelist_cog.get_whitelisted_roles(guild.id):
                role = guild.get_role(role_id)
                if role:
                    try:
                        await channel.set_permissions(role, send_messages=True, reason="[LOCKDOWN] Whitelisted role bypass")
                        bypass_count += 1
                    except:
                        pass

        # Always bypass for admins and mods with manage_guild
        for role in guild.roles:
            if role.permissions.administrator or role.permissions.manage_guild:
                try:
                    await channel.set_permissions(role, send_messages=True, reason="[LOCKDOWN] Admin/Mod bypass")
                    bypass_count += 1
                except:
                    pass

        return bypass_count

    async def _remove_lockdown_bypass(self, channel: discord.TextChannel, guild: discord.Guild):
        """Remove lockdown bypass permissions"""
        whitelist_cog = self.bot.get_cog('Whitelist')

        if whitelist_cog:
            # Remove whitelisted user overrides
            for user_id in whitelist_cog.get_whitelisted_users(guild.id):
                member = guild.get_member(user_id)
                if member:
                    try:
                        current = channel.overwrites.get(member)
                        if current and current.send_messages == True:
                            await channel.set_permissions(member, overwrite=None, reason="[LOCKDOWN END] Removing bypass")
                    except:
                        pass

            # Remove whitelisted bot overrides
            for bot_id in whitelist_cog.get_whitelisted_bots(guild.id):
                member = guild.get_member(bot_id)
                if member:
                    try:
                        current = channel.overwrites.get(member)
                        if current and current.send_messages == True:
                            await channel.set_permissions(member, overwrite=None, reason="[LOCKDOWN END] Removing bypass")
                    except:
                        pass

            # Remove whitelisted role overrides (except admin roles)
            for role_id in whitelist_cog.get_whitelisted_roles(guild.id):
                role = guild.get_role(role_id)
                if role and not role.permissions.administrator:
                    try:
                        current = channel.overwrites.get(role)
                        if current and current.send_messages == True:
                            await channel.set_permissions(role, overwrite=None, reason="[LOCKDOWN END] Removing bypass")
                    except:
                        pass

    @commands.hybrid_command(name="serverlock", description="Manually lock down the server")
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.has_permissions(administrator=True)
    async def manual_lockdown(self, ctx: commands.Context, seconds: int = 60):
        """Manually lock down the server - trusted users/roles can still send messages"""
        if self.lockdown_active.get(ctx.guild.id):
            embed = discord.Embed(description="✖️ Server already locked", color=0x2b2d31)
            return await ctx.send(embed=embed)

        embed = discord.Embed(description=f"⟳ Locking server for {seconds}s...", color=0x2b2d31)
        msg = await ctx.send(embed=embed)

        self.lockdown_active[ctx.guild.id] = True
        locked_count = 0
        bypass_count = 0

        # BACKUP original @everyone permissions for each channel BEFORE locking
        self.lockdown_permission_backup[ctx.guild.id] = {}

        for ch in ctx.guild.text_channels:
            try:
                # Store the ORIGINAL @everyone overwrite (could be None if no override exists)
                original_overwrite = ch.overwrites.get(ctx.guild.default_role)
                self.lockdown_permission_backup[ctx.guild.id][ch.id] = original_overwrite

                # Now set send_messages=False while preserving other permissions
                if original_overwrite:
                    # Clone existing overwrite and just change send_messages
                    new_overwrite = discord.PermissionOverwrite.from_pair(
                        *original_overwrite.pair()
                    )
                    new_overwrite.send_messages = False
                    await ch.set_permissions(ctx.guild.default_role, overwrite=new_overwrite)
                else:
                    # No existing overwrite, just set send_messages=False
                    await ch.set_permissions(ctx.guild.default_role, send_messages=False)

                # Apply bypass for trusted users and roles
                bypass_count += await self._apply_lockdown_bypass(ch, ctx.guild)
                locked_count += 1
            except Exception as e:
                logger.warning(f"Failed to lock channel {ch.name}: {e}")

        bypass_msg = f" (trusted users/roles can still send)" if bypass_count > 0 else ""
        embed = discord.Embed(description=f"➕ Locked {locked_count} channels for {seconds}s{bypass_msg}", color=0x2b2d31)
        await msg.edit(embed=embed)

        await asyncio.sleep(seconds)

        # RESTORE original permissions (don't just set to None - that removes ALL overrides)
        restored_count = 0
        for ch in ctx.guild.text_channels:
            try:
                # First remove bypass permissions
                await self._remove_lockdown_bypass(ch, ctx.guild)

                original_overwrite = self.lockdown_permission_backup[ctx.guild.id].get(ch.id)
                if original_overwrite is not None:
                    # Restore the EXACT original overwrite
                    await ch.set_permissions(ctx.guild.default_role, overwrite=original_overwrite)
                else:
                    # Original had no overwrite, so remove our lockdown override
                    await ch.set_permissions(ctx.guild.default_role, overwrite=None)
                restored_count += 1
            except Exception as e:
                logger.warning(f"Failed to unlock channel {ch.name}: {e}")

        # Clear backup
        self.lockdown_permission_backup[ctx.guild.id] = {}
        self.lockdown_active[ctx.guild.id] = False

        embed = discord.Embed(description=f"➕ Unlocked {restored_count} channels (permissions restored)", color=0x2b2d31)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="serverunlock", description="End server lockdown immediately")
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.has_permissions(administrator=True)
    async def end_lockdown(self, ctx: commands.Context):
        """End server lockdown immediately - restores original permissions"""
        embed = discord.Embed(description="⟳ Unlocking server...", color=0x2b2d31)
        msg = await ctx.send(embed=embed)

        restored_count = 0

        # Check if we have backed up permissions to restore
        has_backup = ctx.guild.id in self.lockdown_permission_backup and self.lockdown_permission_backup[ctx.guild.id]

        for ch in ctx.guild.text_channels:
            try:
                # First remove bypass permissions
                await self._remove_lockdown_bypass(ch, ctx.guild)

                if has_backup:
                    original_overwrite = self.lockdown_permission_backup[ctx.guild.id].get(ch.id)
                    if original_overwrite is not None:
                        await ch.set_permissions(ctx.guild.default_role, overwrite=original_overwrite)
                    else:
                        await ch.set_permissions(ctx.guild.default_role, overwrite=None)
                else:
                    # No backup available, just remove send_messages restriction
                    # This might not perfectly restore but is the safest option
                    await ch.set_permissions(ctx.guild.default_role, send_messages=None)
                restored_count += 1
            except Exception as e:
                logger.warning(f"Failed to unlock channel {ch.name}: {e}")

        # Clear backup
        if ctx.guild.id in self.lockdown_permission_backup:
            self.lockdown_permission_backup[ctx.guild.id] = {}
        self.lockdown_active[ctx.guild.id] = False

        if has_backup:
            embed = discord.Embed(description=f"➕ Unlocked {restored_count} channels (permissions restored)", color=0x2b2d31)
        else:
            embed = discord.Embed(description=f"➕ Unlocked {restored_count} channels", color=0x2b2d31)
        await msg.edit(embed=embed)

    @commands.hybrid_command(name="nukewebhooks", description="Delete ALL webhooks from the server")
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.has_permissions(administrator=True)
    async def nuke_all_webhooks(self, ctx: commands.Context):
        """Delete ALL webhooks from the server (emergency)"""
        if ctx.author.id != ctx.guild.owner_id and ctx.author.id not in self.owner_ids:
            embed = discord.Embed(description="✖️ Only owner can use this", color=0x2b2d31)
            return await ctx.send(embed=embed)

        embed = discord.Embed(description="⟳ Deleting all webhooks...", color=0x2b2d31)
        await ctx.send(embed=embed)

        count = 0
        for channel in ctx.guild.text_channels:
            try:
                webhooks = await channel.webhooks()
                for wh in webhooks:
                    try:
                        await wh.delete(reason="[ANTINUKE] Manual nuke")
                        count += 1
                    except:
                        pass
            except:
                pass

        self.known_webhooks[ctx.guild.id] = defaultdict(set)
        embed = discord.Embed(description=f"➕ Deleted {count} webhooks", color=0x2b2d31)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="attackstats", description="View attack statistics")
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.has_permissions(administrator=True)
    async def attack_statistics(self, ctx: commands.Context):
        """View attack statistics"""
        stats = self.attack_stats.get(ctx.guild.id, {})

        embed = discord.Embed(color=0x2b2d31)
        embed.description = (
            f"**Attack Statistics**\n\n"
            f"› Total blocked: `{stats.get('total', 0)}`\n"
            f"› Webhooks: `{stats.get('Webhook Blocked', 0) + stats.get('Webhook Spam Blocked', 0)}`\n"
            f"› Channels: `{stats.get('Channel Create Blocked', 0) + stats.get('Channel Rename Blocked', 0)}`\n"
            f"› Roles: `{stats.get('Dangerous Role Blocked', 0) + stats.get('Permission Escalation Blocked', 0)}`\n"
            f"› Bots kicked: `{stats.get('Unauthorized Bot Blocked', 0)}`\n"
            f"› Bans reverted: `{stats.get('Unauthorized Ban Blocked', 0)}`"
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="ancommands", description="List all anti-nuke commands")
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def list_commands(self, ctx: commands.Context):
        """List all anti-nuke commands"""
        embed = discord.Embed(color=0x2b2d31)
        embed.description = (
            "**Anti-Nuke Commands**\n\n"
            "**Status**\n"
            "› `/antinuke` - Protection status\n"
            "› `/attackstats` - Attack statistics\n\n"
            "**Configuration**\n"
            "› `/setlog #channel` - Set log channel\n"
            "› `/antinuke_enable` - Enable protection\n"
            "› `/antinuke_disable` - Disable protection\n"
            "› `/punishment ban/kick` - Set punishment type\n\n"
            "**Trust Management**\n"
            "› `/trust @user` - Add trusted user\n"
            "› `/untrust @user` - Remove trusted user\n"
            "› `/trusted` - View trusted users\n"
            "› `/trustbot @bot` - Trust a bot\n"
            "› `/untrustbot @bot` - Remove trusted bot\n"
            "› `/trustedbots` - View trusted bots\n\n"
            "**Emergency**\n"
            "› `/serverlock [seconds]` - Lock server\n"
            "› `/serverunlock` - Unlock server\n"
            "› `/nukewebhooks` - Delete all webhooks\n\n"
            "**Restore**\n"
            "› `/restore` - View deleted channels\n"
            "› `/restore_channel <num>` - Restore channel\n"
            "› `/restore_clear` - Clear restore list"
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="test_antinuke", aliases=["test-antinuke", "an-test"], description="Test anti-nuke logging")
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.has_permissions(administrator=True)
    async def test_antinuke(self, ctx: commands.Context):
        """Test anti-nuke logging (safe test)"""
        if ctx.author.id != ctx.guild.owner_id and ctx.author.id not in self.owner_ids:
            embed = discord.Embed(description="✖️ Only owner can test", color=0x2b2d31)
            return await ctx.send(embed=embed)

        settings = await self.get_settings(ctx.guild.id)
        if not settings.get('log_channel_id'):
            embed = discord.Embed(description="✖️ Set a log channel first with `/setlog #channel`", color=0x2b2d31)
            return await ctx.send(embed=embed)

        embed = discord.Embed(description="⟳ Testing anti-nuke logging...", color=0x2b2d31)
        await ctx.send(embed=embed)

        await self.log_security_event(
            ctx.guild,
            "Test Event",
            "This is a test security event",
            attacker=ctx.author,
            action_taken="Test action",
            color=discord.Color.orange()
        )

        await asyncio.sleep(1)
        embed = discord.Embed(description="➕ Test complete, check log channel", color=0x2b2d31)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="restore", description="View deleted channels that can be restored")
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.has_permissions(administrator=True)
    async def restore_list(self, ctx: commands.Context):
        """View recently deleted channels that can be restored"""
        if ctx.author.id != ctx.guild.owner_id and ctx.author.id not in self.owner_ids:
            embed = discord.Embed(description="✖️ Only owner can view restore list", color=0x2b2d31)
            return await ctx.send(embed=embed)

        if not hasattr(self, 'deleted_channels'):
            self.deleted_channels = defaultdict(list)

        deleted = self.deleted_channels.get(ctx.guild.id, [])
        if not deleted:
            embed = discord.Embed(description="No deleted channels to restore", color=0x2b2d31)
            return await ctx.send(embed=embed)

        channel_list = []
        for i, ch in enumerate(reversed(deleted), 1):
            time_ago = datetime.utcnow() - ch['deleted_at']
            minutes = int(time_ago.total_seconds() / 60)
            if minutes < 60:
                time_str = f"{minutes}m ago"
            else:
                hours = minutes // 60
                time_str = f"{hours}h ago"
            channel_list.append(f"`{i}.` #{ch['name']} ({ch['type']}) - {time_str}")

        embed = discord.Embed(color=0x2b2d31)
        embed.description = (
            f"**Restorable Channels**\n\n"
            + "\n".join(channel_list[:10])
            + f"\n\nUse `/restore_channel <number>` to restore"
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="restore_channel", aliases=["restorechannel", "rc"], description="Restore a deleted channel")
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.has_permissions(administrator=True)
    async def restore_channel(self, ctx: commands.Context, number: int):
        """Restore a deleted channel by number from /restore list"""
        if ctx.author.id != ctx.guild.owner_id and ctx.author.id not in self.owner_ids:
            embed = discord.Embed(description="✖️ Only owner can restore channels", color=0x2b2d31)
            return await ctx.send(embed=embed)

        if not hasattr(self, 'deleted_channels'):
            self.deleted_channels = defaultdict(list)

        deleted = self.deleted_channels.get(ctx.guild.id, [])
        if not deleted:
            embed = discord.Embed(description="✖️ No deleted channels to restore", color=0x2b2d31)
            return await ctx.send(embed=embed)

        reversed_list = list(reversed(deleted))
        index = number - 1

        if index < 0 or index >= len(reversed_list):
            embed = discord.Embed(description=f"✖️ Invalid number, use 1-{len(reversed_list)}", color=0x2b2d31)
            return await ctx.send(embed=embed)

        ch_info = reversed_list[index]

        try:
            category = None
            if ch_info.get('category_id'):
                category = ctx.guild.get_channel(ch_info['category_id'])

            ch_type = ch_info.get('type', 'text')

            if 'voice' in ch_type.lower():
                new_channel = await ctx.guild.create_voice_channel(
                    name=ch_info['name'], category=category,
                    reason=f"[RESTORE] Restored by {ctx.author}"
                )
            elif 'stage' in ch_type.lower():
                new_channel = await ctx.guild.create_stage_channel(
                    name=ch_info['name'], category=category,
                    reason=f"[RESTORE] Restored by {ctx.author}"
                )
            elif 'category' in ch_type.lower():
                new_channel = await ctx.guild.create_category(
                    name=ch_info['name'],
                    reason=f"[RESTORE] Restored by {ctx.author}"
                )
            else:
                new_channel = await ctx.guild.create_text_channel(
                    name=ch_info['name'], category=category,
                    reason=f"[RESTORE] Restored by {ctx.author}"
                )

            self.known_channels[ctx.guild.id].add(new_channel.id)
            self.channel_names[ctx.guild.id][new_channel.id] = new_channel.name

            original_index = len(deleted) - 1 - index
            self.deleted_channels[ctx.guild.id].pop(original_index)

            embed = discord.Embed(description=f"➕ Restored #{ch_info['name']} → {new_channel.mention}", color=0x2b2d31)
            await ctx.send(embed=embed)

        except discord.Forbidden:
            embed = discord.Embed(description="✖️ Missing permissions to create channels", color=0x2b2d31)
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(description=f"✖️ Failed to restore: {type(e).__name__}", color=0x2b2d31)
            await ctx.send(embed=embed)

    @commands.hybrid_command(name="restore_clear", description="Clear the deleted channels restore list")
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.user)
    @commands.has_permissions(administrator=True)
    async def restore_clear(self, ctx: commands.Context):
        """Clear the deleted channels restore list"""
        if ctx.author.id != ctx.guild.owner_id and ctx.author.id not in self.owner_ids:
            embed = discord.Embed(description="✖️ Only owner can clear restore list", color=0x2b2d31)
            return await ctx.send(embed=embed)

        if not hasattr(self, 'deleted_channels'):
            self.deleted_channels = defaultdict(list)

        count = len(self.deleted_channels.get(ctx.guild.id, []))
        self.deleted_channels[ctx.guild.id] = []
        embed = discord.Embed(description=f"➕ Cleared {count} channels from restore list", color=0x2b2d31)
        await ctx.send(embed=embed)

    # ==================== ERROR HANDLERS ====================

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error):
        """Handle command errors including cooldowns"""
        if hasattr(ctx.command, 'on_error'):
            return

        if isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                description=f"✖️ Cooldown: wait `{error.retry_after:.1f}s`",
                color=0x2b2d31
            )
            await ctx.send(embed=embed, delete_after=5)
        elif isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                description="✖️ You don't have permission to use this command",
                color=0x2b2d31
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MemberNotFound):
            embed = discord.Embed(
                description="✖️ Member not found",
                color=0x2b2d31
            )
            await ctx.send(embed=embed)
        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                description="✖️ Invalid argument provided",
                color=0x2b2d31
            )
            await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(AntiNuke(bot))
