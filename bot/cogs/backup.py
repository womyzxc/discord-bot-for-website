"""
Backup & Restore Cog
====================
Server backup and recovery features:
- Full server backup (channels, roles, permissions)
- Automatic backups on schedule
- Quick restore after attacks
- Backup versioning
- Database persistence
"""

import discord
from discord.ext import commands, tasks
from discord import app_commands
from datetime import datetime
from collections import defaultdict
import asyncio
import logging
import json
from typing import Dict, List, Optional
import os

logger = logging.getLogger('Offcialx.Backup')

# Minimal embed color
EMBED_COLOR = 0x2b2d31


class ServerBackup:
    """Represents a server backup"""

    def __init__(self, guild_id: int):
        self.guild_id = guild_id
        self.created_at = datetime.utcnow()
        self.version = 1
        self.backup_id = None  # Database ID

        # Server settings
        self.name = ""
        self.icon_url = None
        self.banner_url = None
        self.description = ""
        self.verification_level = 0
        self.default_notifications = 0

        # Roles (excluding @everyone and managed roles)
        self.roles: List[Dict] = []

        # Channels
        self.categories: List[Dict] = []
        self.text_channels: List[Dict] = []
        self.voice_channels: List[Dict] = []

        # Other
        self.emojis: List[Dict] = []

    def to_dict(self) -> Dict:
        """Convert backup to dictionary for database storage"""
        return {
            'guild_id': self.guild_id,
            'created_at': self.created_at.isoformat(),
            'version': self.version,
            'name': self.name,
            'icon_url': self.icon_url,
            'banner_url': self.banner_url,
            'description': self.description,
            'verification_level': self.verification_level,
            'default_notifications': self.default_notifications,
            'roles': self.roles,
            'categories': self.categories,
            'text_channels': self.text_channels,
            'voice_channels': self.voice_channels,
            'emojis': self.emojis,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'ServerBackup':
        """Create backup from dictionary"""
        backup = cls(data['guild_id'])
        backup.created_at = datetime.fromisoformat(data['created_at']) if isinstance(data['created_at'], str) else data['created_at']
        backup.version = data.get('version', 1)
        backup.backup_id = data.get('backup_id')
        backup.name = data.get('name', '')
        backup.icon_url = data.get('icon_url')
        backup.banner_url = data.get('banner_url')
        backup.description = data.get('description', '')
        backup.verification_level = data.get('verification_level', 0)
        backup.default_notifications = data.get('default_notifications', 0)
        backup.roles = data.get('roles', [])
        backup.categories = data.get('categories', [])
        backup.text_channels = data.get('text_channels', [])
        backup.voice_channels = data.get('voice_channels', [])
        backup.emojis = data.get('emojis', [])
        return backup


class Backup(commands.Cog):
    """Backup & Restore System"""

    def __init__(self, bot):
        self.bot = bot
        self.db = None  # Will be injected by bot

        # Guild backups: guild_id -> List[ServerBackup]
        self.backups: Dict[int, List[ServerBackup]] = defaultdict(list)

        # Guild settings
        self.guild_settings: Dict[int, Dict] = {}
        self._settings_loaded: set = set()

        # Owner IDs from environment
        self.owner_ids: set = set()
        for oid in os.getenv('OWNER_IDS', '').split(','):
            try:
                self.owner_ids.add(int(oid.strip()))
            except:
                pass

        # Start auto-backup task
        self.auto_backup_task.start()

    def cog_unload(self):
        self.auto_backup_task.cancel()

    def is_privileged(self, guild, user_id: int) -> bool:
        """Check if user is server owner, bot owner, or developer"""
        if user_id == guild.owner_id:
            return True
        if user_id in self.owner_ids:
            return True
        if self.bot.owner_ids and user_id in self.bot.owner_ids:
            return True
        return False

    async def owner_check(self, ctx) -> bool:
        """Check ownership and send error if not owner"""
        if not self.is_privileged(ctx.guild, ctx.author.id):
            embed = discord.Embed(description="✕ Only server owner can use this command", color=EMBED_COLOR)
            await ctx.send(embed=embed)
            return False
        return True

    async def get_settings(self, guild_id: int) -> Dict:
        """Get guild settings"""
        if guild_id not in self.guild_settings:
            self.guild_settings[guild_id] = {
                'enabled': True,
                'auto_backup': True,
                'backup_interval': 86400,  # 24 hours
                'max_backups': 5,
                'backup_roles': True,
                'backup_channels': True,
                'backup_permissions': True,
                'backup_emojis': False,
                'log_channel': None,
            }

            # Try to load from database
            if self.db and guild_id not in self._settings_loaded:
                try:
                    db_settings = await self.db.get_guild_settings(guild_id, 'backup')
                    if db_settings:
                        self.guild_settings[guild_id].update(db_settings)

                    # Load backups from database
                    db_backups = await self.db.get_backups(guild_id)
                    if db_backups:
                        for backup_data in db_backups:
                            try:
                                backup = ServerBackup.from_dict(backup_data)
                                self.backups[guild_id].append(backup)
                            except Exception as e:
                                logger.warning(f"Failed to load backup: {e}")
                        logger.info(f"Loaded {len(self.backups[guild_id])} backups for guild {guild_id}")

                    self._settings_loaded.add(guild_id)
                except Exception as e:
                    logger.warning(f'Failed to load backup settings from database: {e}')

        return self.guild_settings[guild_id]

    async def save_settings(self, guild_id: int):
        """Save guild settings to database"""
        if not self.db:
            return

        try:
            settings = self.guild_settings.get(guild_id, {})
            await self.db.save_guild_settings(guild_id, 'backup', settings)
        except Exception as e:
            logger.warning(f'Failed to save backup settings to database: {e}')

    async def save_backup_to_db(self, guild_id: int, backup: ServerBackup):
        """Save a backup to database"""
        if not self.db:
            return

        try:
            backup_data = backup.to_dict()
            await self.db.save_backup(guild_id, backup_data)
            logger.info(f"Saved backup v{backup.version} to database for guild {guild_id}")
        except Exception as e:
            logger.warning(f'Failed to save backup to database: {e}')

    async def delete_backup_from_db(self, guild_id: int, version: int):
        """Delete a backup from database"""
        if not self.db:
            return

        try:
            await self.db.delete_backup(guild_id, version)
            logger.info(f"Deleted backup v{version} from database for guild {guild_id}")
        except Exception as e:
            logger.warning(f'Failed to delete backup from database: {e}')

    async def create_backup(self, guild: discord.Guild, manual: bool = True) -> ServerBackup:
        """Create a full server backup"""
        backup = ServerBackup(guild.id)
        settings = await self.get_settings(guild.id)

        # Basic server info
        backup.name = guild.name
        backup.icon_url = str(guild.icon.url) if guild.icon else None
        backup.banner_url = str(guild.banner.url) if guild.banner else None
        backup.description = guild.description or ""
        backup.verification_level = guild.verification_level.value
        backup.default_notifications = guild.default_notifications.value

        # Backup roles
        if settings['backup_roles']:
            for role in guild.roles:
                if role.is_default() or role.managed:
                    continue

                backup.roles.append({
                    'id': role.id,
                    'name': role.name,
                    'color': role.color.value,
                    'hoist': role.hoist,
                    'mentionable': role.mentionable,
                    'permissions': role.permissions.value,
                    'position': role.position,
                })

        # Backup channels
        if settings['backup_channels']:
            # Categories
            for category in guild.categories:
                cat_data = {
                    'id': category.id,
                    'name': category.name,
                    'position': category.position,
                    'overwrites': self._serialize_overwrites(category, guild) if settings['backup_permissions'] else []
                }
                backup.categories.append(cat_data)

            # Text channels
            for channel in guild.text_channels:
                ch_data = {
                    'id': channel.id,
                    'name': channel.name,
                    'topic': channel.topic,
                    'slowmode': channel.slowmode_delay,
                    'nsfw': channel.nsfw,
                    'position': channel.position,
                    'category': channel.category.name if channel.category else None,
                    'category_id': channel.category.id if channel.category else None,
                    'overwrites': self._serialize_overwrites(channel, guild) if settings['backup_permissions'] else []
                }
                backup.text_channels.append(ch_data)

            # Voice channels
            for channel in guild.voice_channels:
                ch_data = {
                    'id': channel.id,
                    'name': channel.name,
                    'bitrate': channel.bitrate,
                    'user_limit': channel.user_limit,
                    'position': channel.position,
                    'category': channel.category.name if channel.category else None,
                    'category_id': channel.category.id if channel.category else None,
                    'overwrites': self._serialize_overwrites(channel, guild) if settings['backup_permissions'] else []
                }
                backup.voice_channels.append(ch_data)

        # Backup emojis (optional - can be slow)
        if settings['backup_emojis']:
            for emoji in guild.emojis:
                backup.emojis.append({
                    'name': emoji.name,
                    'url': str(emoji.url),
                })

        # Set version
        existing = self.backups[guild.id]
        backup.version = (max([b.version for b in existing], default=0) + 1) if existing else 1

        # Add to backups
        self.backups[guild.id].append(backup)

        # Enforce max backups
        max_backups = settings['max_backups']
        while len(self.backups[guild.id]) > max_backups:
            old_backup = self.backups[guild.id].pop(0)
            await self.delete_backup_from_db(guild.id, old_backup.version)

        # Save to database
        await self.save_backup_to_db(guild.id, backup)

        logger.info(f'Created backup v{backup.version} for {guild.name}')

        # Log if manual
        if manual:
            await self.log_backup_event(guild, 'create', backup)

        return backup

    def _serialize_overwrites(self, channel, guild: discord.Guild) -> List[Dict]:
        """Serialize channel permission overwrites"""
        overwrites = []
        for target, overwrite in channel.overwrites.items():
            ow_data = {
                'type': 'role' if isinstance(target, discord.Role) else 'member',
                'id': target.id,
                'name': target.name if isinstance(target, discord.Role) else str(target.id),
                'allow': overwrite.pair()[0].value,
                'deny': overwrite.pair()[1].value,
            }
            overwrites.append(ow_data)
        return overwrites

    def _deserialize_overwrites(self, overwrites_data: List[Dict], guild: discord.Guild) -> Dict:
        """Deserialize permission overwrites"""
        overwrites = {}
        for ow_data in overwrites_data:
            if ow_data['type'] == 'role':
                target = guild.get_role(ow_data.get('id')) or discord.utils.get(guild.roles, name=ow_data['name'])
            else:
                target = guild.get_member(ow_data.get('id'))

            if target:
                allow = discord.Permissions(ow_data['allow'])
                deny = discord.Permissions(ow_data['deny'])
                overwrites[target] = discord.PermissionOverwrite.from_pair(allow, deny)

        return overwrites

    async def restore_backup(self, guild: discord.Guild, backup: ServerBackup,
                            options: Dict = None) -> Dict:
        """Restore a server backup"""
        options = options or {
            'roles': True,
            'channels': True,
            'permissions': True,
        }

        results = {
            'roles_created': 0,
            'roles_updated': 0,
            'channels_created': 0,
            'channels_updated': 0,
            'permissions_restored': 0,
            'errors': []
        }

        role_map = {}  # old_id/name -> new_role

        # Restore roles first (needed for permissions)
        if options.get('roles'):
            # Sort by position (lowest first)
            sorted_roles = sorted(backup.roles, key=lambda r: r['position'])

            for role_data in sorted_roles:
                try:
                    # Check if role already exists by ID or name
                    existing = guild.get_role(role_data.get('id')) or discord.utils.get(guild.roles, name=role_data['name'])

                    if existing:
                        role_map[role_data['name']] = existing
                        role_map[role_data.get('id', role_data['name'])] = existing
                        # Update existing role
                        try:
                            await existing.edit(
                                color=discord.Color(role_data['color']),
                                hoist=role_data['hoist'],
                                mentionable=role_data['mentionable'],
                                permissions=discord.Permissions(role_data['permissions']),
                                reason="[Backup Restore]"
                            )
                            results['roles_updated'] += 1
                        except:
                            pass
                    else:
                        new_role = await guild.create_role(
                            name=role_data['name'],
                            color=discord.Color(role_data['color']),
                            hoist=role_data['hoist'],
                            mentionable=role_data['mentionable'],
                            permissions=discord.Permissions(role_data['permissions']),
                            reason="[Backup Restore]"
                        )
                        role_map[role_data['name']] = new_role
                        role_map[role_data.get('id', role_data['name'])] = new_role
                        results['roles_created'] += 1

                    await asyncio.sleep(0.3)  # Rate limit protection
                except Exception as e:
                    results['errors'].append(f"Role {role_data['name']}: {str(e)}")

        # Restore channels
        if options.get('channels'):
            # Create categories first
            category_map = {}  # name -> category
            for cat_data in sorted(backup.categories, key=lambda c: c['position']):
                try:
                    existing = guild.get_channel(cat_data.get('id')) or discord.utils.get(guild.categories, name=cat_data['name'])

                    if existing:
                        category_map[cat_data['name']] = existing
                        category_map[cat_data.get('id', cat_data['name'])] = existing
                    else:
                        # Prepare overwrites
                        overwrites = {}
                        if options.get('permissions') and cat_data.get('overwrites'):
                            overwrites = self._deserialize_overwrites(cat_data['overwrites'], guild)
                            results['permissions_restored'] += len(overwrites)

                        cat = await guild.create_category(
                            name=cat_data['name'],
                            overwrites=overwrites,
                            reason="[Backup Restore]"
                        )
                        category_map[cat_data['name']] = cat
                        category_map[cat_data.get('id', cat_data['name'])] = cat
                        results['channels_created'] += 1

                    await asyncio.sleep(0.3)
                except Exception as e:
                    results['errors'].append(f"Category {cat_data['name']}: {str(e)}")

            # Create text channels
            for ch_data in sorted(backup.text_channels, key=lambda c: c['position']):
                try:
                    existing = guild.get_channel(ch_data.get('id')) or discord.utils.get(guild.text_channels, name=ch_data['name'])

                    if existing:
                        # Update existing channel
                        try:
                            await existing.edit(
                                topic=ch_data.get('topic'),
                                slowmode_delay=ch_data.get('slowmode', 0),
                                nsfw=ch_data.get('nsfw', False),
                                reason="[Backup Restore]"
                            )
                            results['channels_updated'] += 1

                            # Restore permissions
                            if options.get('permissions') and ch_data.get('overwrites'):
                                overwrites = self._deserialize_overwrites(ch_data['overwrites'], guild)
                                for target, perms in overwrites.items():
                                    try:
                                        await existing.set_permissions(target, overwrite=perms, reason="[Backup Restore]")
                                        results['permissions_restored'] += 1
                                    except:
                                        pass
                        except:
                            pass
                    else:
                        category = category_map.get(ch_data.get('category_id')) or category_map.get(ch_data.get('category'))

                        # Prepare overwrites
                        overwrites = {}
                        if options.get('permissions') and ch_data.get('overwrites'):
                            overwrites = self._deserialize_overwrites(ch_data['overwrites'], guild)
                            results['permissions_restored'] += len(overwrites)

                        await guild.create_text_channel(
                            name=ch_data['name'],
                            topic=ch_data.get('topic'),
                            slowmode_delay=ch_data.get('slowmode', 0),
                            nsfw=ch_data.get('nsfw', False),
                            category=category,
                            overwrites=overwrites,
                            reason="[Backup Restore]"
                        )
                        results['channels_created'] += 1

                    await asyncio.sleep(0.3)
                except Exception as e:
                    results['errors'].append(f"Text channel {ch_data['name']}: {str(e)}")

            # Create voice channels
            for ch_data in sorted(backup.voice_channels, key=lambda c: c['position']):
                try:
                    existing = guild.get_channel(ch_data.get('id')) or discord.utils.get(guild.voice_channels, name=ch_data['name'])

                    if existing:
                        # Update existing channel
                        try:
                            await existing.edit(
                                bitrate=ch_data.get('bitrate', 64000),
                                user_limit=ch_data.get('user_limit', 0),
                                reason="[Backup Restore]"
                            )
                            results['channels_updated'] += 1

                            # Restore permissions
                            if options.get('permissions') and ch_data.get('overwrites'):
                                overwrites = self._deserialize_overwrites(ch_data['overwrites'], guild)
                                for target, perms in overwrites.items():
                                    try:
                                        await existing.set_permissions(target, overwrite=perms, reason="[Backup Restore]")
                                        results['permissions_restored'] += 1
                                    except:
                                        pass
                        except:
                            pass
                    else:
                        category = category_map.get(ch_data.get('category_id')) or category_map.get(ch_data.get('category'))

                        # Prepare overwrites
                        overwrites = {}
                        if options.get('permissions') and ch_data.get('overwrites'):
                            overwrites = self._deserialize_overwrites(ch_data['overwrites'], guild)
                            results['permissions_restored'] += len(overwrites)

                        await guild.create_voice_channel(
                            name=ch_data['name'],
                            bitrate=ch_data.get('bitrate', 64000),
                            user_limit=ch_data.get('user_limit', 0),
                            category=category,
                            overwrites=overwrites,
                            reason="[Backup Restore]"
                        )
                        results['channels_created'] += 1

                    await asyncio.sleep(0.3)
                except Exception as e:
                    results['errors'].append(f"Voice channel {ch_data['name']}: {str(e)}")

        logger.info(f'Restored backup v{backup.version} for {guild.name}')
        await self.log_backup_event(guild, 'restore', backup, results)

        return results

    async def log_backup_event(self, guild: discord.Guild, action: str,
                               backup: ServerBackup, results: Dict = None):
        """Log a backup event"""
        settings = await self.get_settings(guild.id)

        if not settings['log_channel']:
            return

        channel = guild.get_channel(settings['log_channel'])
        if not channel:
            return

        embed = discord.Embed(color=EMBED_COLOR)

        if action == 'create':
            ch_count = len(backup.text_channels) + len(backup.voice_channels)
            embed.description = (
                f"**Backup Created**\n\n"
                f"› Version: `{backup.version}`\n"
                f"› Roles: `{len(backup.roles)}`\n"
                f"› Channels: `{ch_count}`\n"
                f"› Categories: `{len(backup.categories)}`"
            )
        elif action == 'restore' and results:
            embed.description = (
                f"**Backup Restored**\n\n"
                f"› Version: `{backup.version}`\n"
                f"› Roles created: `{results['roles_created']}`\n"
                f"› Roles updated: `{results['roles_updated']}`\n"
                f"› Channels created: `{results['channels_created']}`\n"
                f"› Channels updated: `{results['channels_updated']}`\n"
                f"› Permissions restored: `{results['permissions_restored']}`"
            )
            if results['errors']:
                embed.description += f"\n› Errors: `{len(results['errors'])}`"
        else:
            embed.description = f"**Backup {action.title()}** − Version `{backup.version}`"

        try:
            await channel.send(embed=embed)
        except:
            pass

    @tasks.loop(hours=24)
    async def auto_backup_task(self):
        """Run automatic backups for all guilds"""
        for guild in self.bot.guilds:
            try:
                settings = await self.get_settings(guild.id)
                if settings['enabled'] and settings['auto_backup']:
                    await self.create_backup(guild, manual=False)
                    await asyncio.sleep(2)  # Rate limit protection
            except Exception as e:
                logger.error(f'Auto-backup failed for {guild.name}: {e}')

    @auto_backup_task.before_loop
    async def before_auto_backup(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(60)  # Wait 1 minute after bot starts

    # ==================== COMMANDS ====================

    @commands.hybrid_group(name='backup', aliases=['bk'], invoke_without_command=True)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def backup(self, ctx: commands.Context):
        """Backup management commands"""
        if not await self.owner_check(ctx):
            return

        # Ensure settings are loaded
        await self.get_settings(ctx.guild.id)

        backups = self.backups.get(ctx.guild.id, [])

        if not backups:
            embed = discord.Embed(
                description="**Server Backups**\n\n› No backups found\n\nUse `!backup create` to create one",
                color=EMBED_COLOR
            )
            return await ctx.send(embed=embed)

        backup_list = []
        for backup in reversed(backups[-5:]):
            ch_count = len(backup.text_channels) + len(backup.voice_channels)
            cat_count = len(backup.categories)
            backup_list.append(
                f"› `v{backup.version}` − {backup.created_at.strftime('%Y-%m-%d %H:%M')} UTC\n"
                f"   {len(backup.roles)} roles, {ch_count} channels, {cat_count} categories"
            )

        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = f"**Server Backups** `{len(backups)}`\n\n" + "\n".join(backup_list)
        embed.set_footer(text="Use !backup info <version> to view details")
        await ctx.send(embed=embed)

    @backup.command(name='create')
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    @commands.cooldown(1, 300, commands.BucketType.guild)
    async def backup_create(self, ctx: commands.Context):
        """Create a new server backup"""
        if not await self.owner_check(ctx):
            return

        embed = discord.Embed(description="⟳ Creating backup...", color=EMBED_COLOR)
        msg = await ctx.send(embed=embed)

        try:
            backup = await self.create_backup(ctx.guild)
            ch_count = len(backup.text_channels) + len(backup.voice_channels)

            embed = discord.Embed(color=EMBED_COLOR)
            embed.description = (
                f"+ Backup created\n\n"
                f"› Version: `{backup.version}`\n"
                f"› Roles: `{len(backup.roles)}`\n"
                f"› Channels: `{ch_count}`\n"
                f"› Categories: `{len(backup.categories)}`"
            )
            await msg.edit(embed=embed)
        except Exception as e:
            logger.error(f"Backup creation failed: {e}")
            embed = discord.Embed(description=f"✕ Backup failed: {str(e)[:100]}", color=EMBED_COLOR)
            await msg.edit(embed=embed)

    @backup.command(name='info')
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def backup_info(self, ctx: commands.Context, version: int = None):
        """View details of a specific backup"""
        if not await self.owner_check(ctx):
            return

        await self.get_settings(ctx.guild.id)
        backups = self.backups.get(ctx.guild.id, [])

        if not backups:
            embed = discord.Embed(description="✕ No backups found", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        if version is None:
            backup = backups[-1]  # Latest backup
        else:
            backup = next((b for b in backups if b.version == version), None)
            if not backup:
                embed = discord.Embed(description=f"✕ Backup v{version} not found", color=EMBED_COLOR)
                return await ctx.send(embed=embed)

        ch_count = len(backup.text_channels) + len(backup.voice_channels)

        # Role summary
        role_names = [r['name'] for r in backup.roles[:10]]
        roles_str = ", ".join(role_names)
        if len(backup.roles) > 10:
            roles_str += f" +{len(backup.roles) - 10} more"

        # Channel summary
        text_names = [f"#{c['name']}" for c in backup.text_channels[:5]]
        channels_str = ", ".join(text_names)
        if len(backup.text_channels) > 5:
            channels_str += f" +{len(backup.text_channels) - 5} more"

        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = (
            f"**Backup v{backup.version}**\n\n"
            f"› Server: `{backup.name}`\n"
            f"› Created: `{backup.created_at.strftime('%Y-%m-%d %H:%M')} UTC`\n\n"
            f"**Contents**\n"
            f"› Roles: `{len(backup.roles)}`\n"
            f"› Categories: `{len(backup.categories)}`\n"
            f"› Text Channels: `{len(backup.text_channels)}`\n"
            f"› Voice Channels: `{len(backup.voice_channels)}`\n"
            f"› Emojis: `{len(backup.emojis)}`\n\n"
            f"**Roles**\n{roles_str or 'None'}\n\n"
            f"**Text Channels**\n{channels_str or 'None'}"
        )
        embed.set_footer(text="Use !backup restore <version> to restore")
        await ctx.send(embed=embed)

    @backup.command(name='restore')
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def backup_restore(self, ctx: commands.Context, version: int = None):
        """Restore a server backup"""
        if not await self.owner_check(ctx):
            return

        await self.get_settings(ctx.guild.id)
        backups = self.backups.get(ctx.guild.id, [])

        if not backups:
            embed = discord.Embed(description="✕ No backups found", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        if version is None:
            backup = backups[-1]
        else:
            backup = next((b for b in backups if b.version == version), None)
            if not backup:
                embed = discord.Embed(description=f"✕ Backup v{version} not found", color=EMBED_COLOR)
                return await ctx.send(embed=embed)

        ch_count = len(backup.text_channels) + len(backup.voice_channels)

        embed = discord.Embed(
            description=(
                f"**Restore Backup v{backup.version}?**\n\n"
                f"This will restore:\n"
                f"› `{len(backup.roles)}` roles\n"
                f"› `{ch_count}` channels\n"
                f"› `{len(backup.categories)}` categories\n\n"
                f"React with ✅ to confirm or ❌ to cancel"
            ),
            color=EMBED_COLOR
        )
        msg = await ctx.send(embed=embed)
        await msg.add_reaction("✅")
        await msg.add_reaction("❌")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == msg.id

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)

            if str(reaction.emoji) == "❌":
                embed = discord.Embed(description="− Restore cancelled", color=EMBED_COLOR)
                await msg.edit(embed=embed)
                try:
                    await msg.clear_reactions()
                except:
                    pass
                return

            embed = discord.Embed(description="⟳ Restoring backup... This may take a while.", color=EMBED_COLOR)
            await msg.edit(embed=embed)
            try:
                await msg.clear_reactions()
            except:
                pass

            results = await self.restore_backup(ctx.guild, backup)

            embed = discord.Embed(color=EMBED_COLOR)
            embed.description = (
                f"+ Backup v{backup.version} restored\n\n"
                f"› Roles created: `{results['roles_created']}`\n"
                f"› Roles updated: `{results['roles_updated']}`\n"
                f"› Channels created: `{results['channels_created']}`\n"
                f"› Channels updated: `{results['channels_updated']}`\n"
                f"› Permissions restored: `{results['permissions_restored']}`"
            )
            if results['errors']:
                embed.description += f"\n› Errors: `{len(results['errors'])}`"
                # Show first 3 errors
                if len(results['errors']) <= 3:
                    embed.description += "\n\n**Errors:**\n" + "\n".join([f"› {e}" for e in results['errors']])
                else:
                    embed.description += "\n\n**First 3 Errors:**\n" + "\n".join([f"› {e}" for e in results['errors'][:3]])

            await msg.edit(embed=embed)

        except asyncio.TimeoutError:
            embed = discord.Embed(description="✕ Restore timed out", color=EMBED_COLOR)
            await msg.edit(embed=embed)
            try:
                await msg.clear_reactions()
            except:
                pass

    @backup.command(name='list')
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def backup_list(self, ctx: commands.Context):
        """List all available backups"""
        if not await self.owner_check(ctx):
            return

        await self.get_settings(ctx.guild.id)
        backups = self.backups.get(ctx.guild.id, [])

        if not backups:
            embed = discord.Embed(description="✕ No backups found", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        backup_list = []
        for backup in reversed(backups):
            ch_count = len(backup.text_channels) + len(backup.voice_channels)
            backup_list.append(
                f"› `v{backup.version}` − {backup.created_at.strftime('%Y-%m-%d %H:%M')} UTC − "
                f"{len(backup.roles)} roles, {ch_count} channels"
            )

        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = f"**All Backups** `{len(backups)}`\n\n" + "\n".join(backup_list)
        await ctx.send(embed=embed)

    @backup.command(name='delete')
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def backup_delete(self, ctx: commands.Context, version: int):
        """Delete a specific backup"""
        if not await self.owner_check(ctx):
            return

        await self.get_settings(ctx.guild.id)
        backups = self.backups.get(ctx.guild.id, [])

        backup = next((b for b in backups if b.version == version), None)
        if not backup:
            embed = discord.Embed(description=f"✕ Backup v{version} not found", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        backups.remove(backup)
        await self.delete_backup_from_db(ctx.guild.id, version)

        embed = discord.Embed(description=f"+ Deleted backup v{version}", color=EMBED_COLOR)
        await ctx.send(embed=embed)

    @backup.command(name='clear')
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def backup_clear(self, ctx: commands.Context):
        """Clear all backups"""
        if not await self.owner_check(ctx):
            return

        # Extra check - only server owner can clear all backups
        if ctx.author.id != ctx.guild.owner_id and ctx.author.id not in self.owner_ids:
            embed = discord.Embed(description="✕ Only server owner can clear all backups", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        count = len(self.backups.get(ctx.guild.id, []))

        # Delete all from database
        for backup in self.backups.get(ctx.guild.id, []):
            await self.delete_backup_from_db(ctx.guild.id, backup.version)

        self.backups[ctx.guild.id] = []
        embed = discord.Embed(description=f"+ Cleared `{count}` backups", color=EMBED_COLOR)
        await ctx.send(embed=embed)

    @backup.command(name='auto')
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def backup_auto(self, ctx: commands.Context, enabled: bool = None):
        """Toggle automatic backups"""
        if not await self.owner_check(ctx):
            return

        settings = await self.get_settings(ctx.guild.id)

        if enabled is None:
            enabled = not settings['auto_backup']

        settings['auto_backup'] = enabled
        await self.save_settings(ctx.guild.id)

        status = "enabled" if enabled else "disabled"
        embed = discord.Embed(description=f"+ Auto backups `{status}`", color=EMBED_COLOR)
        await ctx.send(embed=embed)

    @backup.command(name='setlog')
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def backup_setlog(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set the backup log channel"""
        if not await self.owner_check(ctx):
            return

        settings = await self.get_settings(ctx.guild.id)
        settings['log_channel'] = channel.id
        await self.save_settings(ctx.guild.id)

        embed = discord.Embed(description=f"+ Set backup log to {channel.mention}", color=EMBED_COLOR)
        await ctx.send(embed=embed)

    @backup.command(name='settings')
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def backup_settings(self, ctx: commands.Context):
        """View backup settings"""
        if not await self.owner_check(ctx):
            return

        settings = await self.get_settings(ctx.guild.id)
        backups = self.backups.get(ctx.guild.id, [])

        log_channel = ctx.guild.get_channel(settings.get('log_channel')) if settings.get('log_channel') else None

        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = (
            f"**Backup Settings**\n\n"
            f"› Auto backup: `{'enabled' if settings['auto_backup'] else 'disabled'}`\n"
            f"› Max backups: `{settings['max_backups']}`\n"
            f"› Current backups: `{len(backups)}`\n"
            f"› Log channel: {log_channel.mention if log_channel else 'Not set'}\n\n"
            f"**What gets backed up:**\n"
            f"› Roles: `{'yes' if settings['backup_roles'] else 'no'}`\n"
            f"› Channels: `{'yes' if settings['backup_channels'] else 'no'}`\n"
            f"› Permissions: `{'yes' if settings['backup_permissions'] else 'no'}`\n"
            f"› Emojis: `{'yes' if settings['backup_emojis'] else 'no'}`"
        )
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Backup(bot))
