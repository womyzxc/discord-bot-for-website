"""
Whitelist Management Cog - Minimal Style
All commands work with both ! and /
Supports both user and role whitelisting
"""

import discord
from discord.ext import commands
from datetime import datetime
from collections import defaultdict
import logging
from typing import Dict, Optional, Set

logger = logging.getLogger('Offcialx.Whitelist')

# Minimal embed color
EMBED_COLOR = 0x2b2d31


class WhitelistEntry:
    """Represents a whitelist entry"""

    def __init__(self, user_id: int, level: str, added_by: int, reason: str = ""):
        self.user_id = user_id
        self.level = level
        self.added_by = added_by
        self.added_at = datetime.utcnow()
        self.reason = reason


class RoleWhitelistEntry:
    """Represents a role whitelist entry"""

    def __init__(self, role_id: int, added_by: int, reason: str = ""):
        self.role_id = role_id
        self.added_by = added_by
        self.added_at = datetime.utcnow()
        self.reason = reason


class Whitelist(commands.Cog):
    """Whitelist Management System"""

    def __init__(self, bot):
        self.bot = bot
        self.db = None  # Will be injected by bot
        self.whitelists: Dict[int, Dict[int, WhitelistEntry]] = defaultdict(dict)
        self.whitelisted_roles: Dict[int, Dict[int, RoleWhitelistEntry]] = defaultdict(dict)  # guild_id -> {role_id -> entry}
        self.guild_settings: Dict[int, Dict] = {}
        self.levels = {'trusted': 1, 'admin': 2, 'owner': 3}
        self._settings_loaded: set = set()

        # Owner IDs from environment
        self.owner_ids: set = set()
        import os
        for oid in os.getenv('OWNER_IDS', '').split(','):
            try:
                self.owner_ids.add(int(oid.strip()))
            except:
                pass

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

    async def preload_all_settings(self):
        """Preload settings for all guilds on bot startup"""
        if not self.db:
            return

        logger.info("Preloading whitelist settings for all guilds...")
        loaded_count = 0
        users_count = 0
        roles_count = 0

        for guild in self.bot.guilds:
            try:
                # Always set defaults first
                self.guild_settings[guild.id] = {
                    'enabled': True,
                    'max_trusted': 10,
                    'max_admins': 5,
                    'max_roles': 10,
                    'auto_whitelist_owner': True,
                    'require_2fa': False,
                    'log_channel': None,
                }

                # Load and override with database settings
                db_settings = await self.db.get_guild_settings(guild.id, 'whitelist')
                if db_settings and isinstance(db_settings, dict):
                    self.guild_settings[guild.id].update(db_settings)
                    loaded_count += 1

                # Load whitelist entries
                entries = await self.db.get_whitelist(guild.id)
                for entry in entries:
                    if isinstance(entry, dict) and 'user_id' in entry:
                        self.whitelists[guild.id][entry['user_id']] = WhitelistEntry(
                            user_id=entry['user_id'],
                            level=entry.get('level', 'trusted'),
                            added_by=entry.get('added_by', 0),
                            reason=entry.get('reason', '')
                        )
                        users_count += 1

                # Load whitelisted roles
                roles = await self.db.get_whitelisted_roles(guild.id)
                for entry in roles:
                    if isinstance(entry, dict) and 'role_id' in entry:
                        role_id = entry['role_id']
                        self.whitelisted_roles[guild.id][role_id] = RoleWhitelistEntry(
                            role_id=role_id,
                            added_by=entry.get('added_by', 0),
                            reason=entry.get('reason', '')
                        )
                        roles_count += 1
                    elif isinstance(entry, int):
                        # Handle case where only role_id is returned
                        self.whitelisted_roles[guild.id][entry] = RoleWhitelistEntry(
                            role_id=entry,
                            added_by=0,
                            reason=''
                        )
                        roles_count += 1

                self._settings_loaded.add(guild.id)
            except Exception as e:
                logger.error(f'Failed to preload whitelist settings for guild {guild.id}: {e}')
                import traceback
                traceback.print_exc()

        logger.info(f"✅ Preloaded whitelist: {loaded_count} guilds, {users_count} users, {roles_count} roles")

    async def get_settings(self, guild_id: int) -> Dict:
        """Get guild settings - loads from database if available"""
        if guild_id not in self.guild_settings:
            # Default settings
            self.guild_settings[guild_id] = {
                'enabled': True,
                'max_trusted': 10,
                'max_admins': 5,
                'max_roles': 10,  # Max whitelisted roles
                'auto_whitelist_owner': True,
                'require_2fa': False,
                'log_channel': None,
            }

            # Try to load from database
            if self.db and guild_id not in self._settings_loaded:
                try:
                    db_settings = await self.db.get_guild_settings(guild_id, 'whitelist')
                    if db_settings:
                        self.guild_settings[guild_id].update(db_settings)

                    # Load whitelist entries from database
                    entries = await self.db.get_whitelist(guild_id)
                    for entry in entries:
                        self.whitelists[guild_id][entry['user_id']] = WhitelistEntry(
                            user_id=entry['user_id'],
                            level=entry['level'],
                            added_by=entry['added_by'],
                            reason=entry.get('reason', '')
                        )

                    # Load whitelisted roles from database
                    roles = await self.db.get_whitelisted_roles(guild_id)
                    for entry in roles:
                        role_id = entry.get('role_id') if isinstance(entry, dict) else entry
                        self.whitelisted_roles[guild_id][role_id] = RoleWhitelistEntry(
                            role_id=role_id,
                            added_by=entry.get('added_by', 0) if isinstance(entry, dict) else 0,
                            reason=entry.get('reason', '') if isinstance(entry, dict) else ''
                        )

                    self._settings_loaded.add(guild_id)
                except Exception as e:
                    logger.warning(f'Failed to load whitelist settings from database: {e}')

        return self.guild_settings[guild_id]

    async def save_settings(self, guild_id: int):
        """Save guild settings to database"""
        if not self.db:
            return

        try:
            settings = self.guild_settings.get(guild_id, {})
            await self.db.save_guild_settings(guild_id, 'whitelist', settings)
        except Exception as e:
            logger.warning(f'Failed to save whitelist settings to database: {e}')

    def is_whitelisted(self, guild_id: int, user_id: int, min_level: str = 'trusted') -> bool:
        """Check if a user is whitelisted at minimum level"""
        if guild_id not in self.whitelists:
            return False
        entry = self.whitelists[guild_id].get(user_id)
        if not entry:
            return False
        return self.levels.get(entry.level, 0) >= self.levels.get(min_level, 0)

    def is_role_whitelisted(self, guild_id: int, role_id: int) -> bool:
        """Check if a role is whitelisted"""
        return role_id in self.whitelisted_roles.get(guild_id, {})

    def has_whitelisted_role(self, guild_id: int, member: discord.Member) -> bool:
        """Check if a member has any whitelisted role"""
        if guild_id not in self.whitelisted_roles:
            return False
        whitelisted = self.whitelisted_roles[guild_id]
        for role in member.roles:
            if role.id in whitelisted:
                return True
        return False

    def get_whitelist_level(self, guild_id: int, user_id: int) -> Optional[str]:
        """Get the whitelist level for a user"""
        if guild_id not in self.whitelists:
            return None
        entry = self.whitelists[guild_id].get(user_id)
        return entry.level if entry else None

    def get_whitelisted_roles(self, guild_id: int) -> Dict[int, RoleWhitelistEntry]:
        """Get all whitelisted roles for a guild"""
        return self.whitelisted_roles.get(guild_id, {})

    def add_role_to_whitelist(self, guild_id: int, role_id: int, added_by: int, reason: str = "") -> bool:
        """Add a role to the whitelist"""
        self.whitelisted_roles[guild_id][role_id] = RoleWhitelistEntry(role_id, added_by, reason)
        logger.info(f'Added role {role_id} to whitelist in guild {guild_id}')
        return True

    def remove_role_from_whitelist(self, guild_id: int, role_id: int) -> bool:
        """Remove a role from the whitelist"""
        if role_id in self.whitelisted_roles.get(guild_id, {}):
            del self.whitelisted_roles[guild_id][role_id]
            logger.info(f'Removed role {role_id} from whitelist in guild {guild_id}')
            return True
        return False

    async def add_to_whitelist_async(self, guild_id: int, user_id: int, level: str, added_by: int, reason: str = "") -> bool:
        """Add a user to the whitelist (async with database)"""
        if level not in self.levels:
            return False
        self.whitelists[guild_id][user_id] = WhitelistEntry(user_id, level, added_by, reason)

        # Save to database
        if self.db:
            try:
                await self.db.add_to_whitelist(guild_id, user_id, level, added_by, reason)
            except Exception as e:
                logger.warning(f'Failed to save whitelist to database: {e}')

        logger.info(f'Added {user_id} to whitelist in guild {guild_id} at level {level}')
        return True

    def add_to_whitelist(self, guild_id: int, user_id: int, level: str, added_by: int, reason: str = "") -> bool:
        """Add a user to the whitelist (sync version for compatibility)"""
        if level not in self.levels:
            return False
        self.whitelists[guild_id][user_id] = WhitelistEntry(user_id, level, added_by, reason)
        logger.info(f'Added {user_id} to whitelist in guild {guild_id} at level {level}')
        return True

    async def remove_from_whitelist_async(self, guild_id: int, user_id: int) -> bool:
        """Remove a user from the whitelist (async with database)"""
        if user_id in self.whitelists.get(guild_id, {}):
            del self.whitelists[guild_id][user_id]

            # Remove from database
            if self.db:
                try:
                    await self.db.remove_from_whitelist(guild_id, user_id)
                except Exception as e:
                    logger.warning(f'Failed to remove from whitelist in database: {e}')

            logger.info(f'Removed {user_id} from whitelist in guild {guild_id}')
            return True
        return False

    def remove_from_whitelist(self, guild_id: int, user_id: int) -> bool:
        """Remove a user from the whitelist (sync version for compatibility)"""
        if user_id in self.whitelists.get(guild_id, {}):
            del self.whitelists[guild_id][user_id]
            logger.info(f'Removed {user_id} from whitelist in guild {guild_id}')
            return True
        return False

    def get_all_whitelisted(self, guild_id: int) -> Dict[int, WhitelistEntry]:
        """Get all whitelisted users for a guild"""
        return self.whitelists.get(guild_id, {})

    async def log_whitelist_action(self, guild: discord.Guild, action: str, target,
                                    by: discord.User, level: str = None, reason: str = None):
        """Log a whitelist action"""
        settings = await self.get_settings(guild.id)
        if not settings['log_channel']:
            return

        channel = guild.get_channel(settings['log_channel'])
        if not channel:
            return

        embed = discord.Embed(color=EMBED_COLOR)

        # Handle both users and roles
        if isinstance(target, discord.Role):
            text = f"**Whitelist Role {action.title()}**\n\n› Role: {target.mention}\n› By: {by.mention}"
        else:
            text = f"**Whitelist {action.title()}**\n\n› User: {target.mention}\n› By: {by.mention}"

        if level:
            text += f"\n› Level: `{level}`"
        if reason:
            text += f"\n› Reason: `{reason}`"
        embed.description = text

        try:
            await channel.send(embed=embed)
        except:
            pass

    # ==================== COMMANDS ====================

    @commands.hybrid_group(name='wlist', aliases=['wl'], invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def wlist(self, ctx: commands.Context):
        """Whitelist management commands"""
        if not await self.owner_check(ctx):
            return

        entries = self.get_all_whitelisted(ctx.guild.id)
        role_entries = self.get_whitelisted_roles(ctx.guild.id)

        if not entries and not role_entries:
            embed = discord.Embed(description="No whitelisted users or roles\nUse `wlist add @user` or `wlist role @role`", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        owners = []
        admins = []
        trusted = []
        roles = []

        for user_id, entry in entries.items():
            member = ctx.guild.get_member(user_id)
            display = f"› {member.mention}" if member else f"› `{user_id}`"

            if entry.level == 'owner':
                owners.append(display)
            elif entry.level == 'admin':
                admins.append(display)
            else:
                trusted.append(display)

        for role_id, entry in role_entries.items():
            role = ctx.guild.get_role(role_id)
            display = f"› {role.mention}" if role else f"› `{role_id}`"
            roles.append(display)

        text = f"**Whitelist** `{len(entries)} users, {len(role_entries)} roles`\n\n"
        if owners:
            text += f"**Owners**\n" + "\n".join(owners) + "\n\n"
        if admins:
            text += f"**Admins**\n" + "\n".join(admins) + "\n\n"
        if trusted:
            text += f"**Trusted**\n" + "\n".join(trusted) + "\n\n"
        if roles:
            text += f"**Whitelisted Roles**\n" + "\n".join(roles)

        embed = discord.Embed(description=text.strip(), color=EMBED_COLOR)
        await ctx.send(embed=embed)

    @wlist.command(name='add')
    @commands.has_permissions(administrator=True)
    async def whitelist_add(self, ctx: commands.Context, member: discord.Member, level: str = 'trusted', *, reason: str = ""):
        """Add a user to the whitelist"""
        if not await self.owner_check(ctx):
            return

        valid_levels = ['owner', 'admin', 'trusted']
        if level.lower() not in valid_levels:
            embed = discord.Embed(description=f"✕ Invalid level. Use: `{', '.join(valid_levels)}`", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        settings = await self.get_settings(ctx.guild.id)
        entries = self.get_all_whitelisted(ctx.guild.id)

        level_counts = {'owner': 0, 'admin': 0, 'trusted': 0}
        for entry in entries.values():
            level_counts[entry.level] = level_counts.get(entry.level, 0) + 1

        if level.lower() == 'admin' and level_counts['admin'] >= settings['max_admins']:
            embed = discord.Embed(description=f"✕ Max admin slots reached `{settings['max_admins']}`", color=EMBED_COLOR)
            return await ctx.send(embed=embed)
        if level.lower() == 'trusted' and level_counts['trusted'] >= settings['max_trusted']:
            embed = discord.Embed(description=f"✕ Max trusted slots reached `{settings['max_trusted']}`", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        if level.lower() == 'owner' and not self.is_privileged(ctx.guild, ctx.author.id):
            embed = discord.Embed(description="✕ Only server owner can add owner level", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        await self.add_to_whitelist_async(ctx.guild.id, member.id, level.lower(), ctx.author.id, reason)
        await self.log_whitelist_action(ctx.guild, 'add', member, ctx.author, level.lower(), reason)

        embed = discord.Embed(description=f"+ Added {member.mention} to whitelist as `{level.lower()}`", color=EMBED_COLOR)
        await ctx.send(embed=embed)

    @wlist.command(name='remove', aliases=['rm', 'del'])
    @commands.has_permissions(administrator=True)
    async def whitelist_remove(self, ctx: commands.Context, member: discord.Member):
        """Remove a user from the whitelist"""
        if not await self.owner_check(ctx):
            return

        entry = self.whitelists.get(ctx.guild.id, {}).get(member.id)

        if not entry:
            embed = discord.Embed(description=f"✕ {member.mention} not whitelisted", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        if entry.level == 'owner' and not self.is_privileged(ctx.guild, ctx.author.id):
            embed = discord.Embed(description="✕ Only server owner can remove owner level", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        await self.remove_from_whitelist_async(ctx.guild.id, member.id)
        await self.log_whitelist_action(ctx.guild, 'remove', member, ctx.author)

        embed = discord.Embed(description=f"− Removed {member.mention} from whitelist", color=EMBED_COLOR)
        await ctx.send(embed=embed)

    @wlist.command(name='check')
    @commands.has_permissions(administrator=True)
    async def whitelist_check(self, ctx: commands.Context, member: discord.Member):
        """Check a user's whitelist status"""
        if not await self.owner_check(ctx):
            return

        entry = self.whitelists.get(ctx.guild.id, {}).get(member.id)

        if not entry:
            embed = discord.Embed(description=f"{member.mention} not whitelisted", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        added_by = ctx.guild.get_member(entry.added_by)
        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = (
            f"**{member.display_name}**\n\n"
            f"› Level: `{entry.level}`\n"
            f"› Added by: {added_by.mention if added_by else '`Unknown`'}\n"
            f"› Added: `{entry.added_at.strftime('%Y-%m-%d')}`"
        )
        if entry.reason:
            embed.description += f"\n› Reason: `{entry.reason}`"
        await ctx.send(embed=embed)

    @wlist.command(name='update')
    @commands.has_permissions(administrator=True)
    async def whitelist_update(self, ctx: commands.Context, member: discord.Member, level: str):
        """Update a user's whitelist level"""
        if not await self.owner_check(ctx):
            return

        valid_levels = ['owner', 'admin', 'trusted']
        if level.lower() not in valid_levels:
            embed = discord.Embed(description=f"✕ Invalid level. Use: `{', '.join(valid_levels)}`", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        entry = self.whitelists.get(ctx.guild.id, {}).get(member.id)

        if not entry:
            embed = discord.Embed(description=f"✕ {member.mention} not whitelisted", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        if entry.level == 'owner' and not self.is_privileged(ctx.guild, ctx.author.id):
            embed = discord.Embed(description="✕ Only server owner can modify owner level", color=EMBED_COLOR)
            return await ctx.send(embed=embed)
        if level.lower() == 'owner' and not self.is_privileged(ctx.guild, ctx.author.id):
            embed = discord.Embed(description="✕ Only server owner can set owner level", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        old_level = entry.level
        entry.level = level.lower()

        await self.log_whitelist_action(ctx.guild, 'update', member, ctx.author, level.lower(),
                                        f"Changed from {old_level} to {level.lower()}")

        embed = discord.Embed(description=f"+ Updated {member.mention} from `{old_level}` to `{level.lower()}`", color=EMBED_COLOR)
        await ctx.send(embed=embed)

    @wlist.command(name='clear')
    @commands.has_permissions(administrator=True)
    async def whitelist_clear(self, ctx: commands.Context, level: str = None):
        """Clear the whitelist (optionally by level)"""
        if not await self.owner_check(ctx):
            return

        if level:
            if level.lower() not in ['owner', 'admin', 'trusted']:
                embed = discord.Embed(description="✕ Invalid level", color=EMBED_COLOR)
                return await ctx.send(embed=embed)

            to_remove = [
                user_id for user_id, entry in self.whitelists.get(ctx.guild.id, {}).items()
                if entry.level == level.lower()
            ]
            for user_id in to_remove:
                del self.whitelists[ctx.guild.id][user_id]

            embed = discord.Embed(description=f"+ Cleared `{len(to_remove)}` {level.lower()} entries", color=EMBED_COLOR)
        else:
            count = len(self.whitelists.get(ctx.guild.id, {}))
            self.whitelists[ctx.guild.id] = {}
            embed = discord.Embed(description=f"+ Cleared whitelist `{count}` entries", color=EMBED_COLOR)
        await ctx.send(embed=embed)

    @wlist.command(name='setlog')
    @commands.has_permissions(administrator=True)
    async def whitelist_setlog(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set the whitelist log channel"""
        if not await self.owner_check(ctx):
            return

        settings = await self.get_settings(ctx.guild.id)
        settings['log_channel'] = channel.id
        await self.save_settings(ctx.guild.id)
        embed = discord.Embed(description=f"+ Set whitelist log to {channel.mention}", color=EMBED_COLOR)
        await ctx.send(embed=embed)

    # ==================== ROLE WHITELIST COMMANDS ====================

    @wlist.command(name='role')
    @commands.has_permissions(administrator=True)
    async def whitelist_role(self, ctx: commands.Context, role: discord.Role, *, reason: str = ""):
        """Add a role to the whitelist (members with this role are immune to anti-nuke)"""
        if not await self.owner_check(ctx):
            return

        settings = await self.get_settings(ctx.guild.id)
        current_roles = len(self.whitelisted_roles.get(ctx.guild.id, {}))

        if current_roles >= settings.get('max_roles', 10):
            embed = discord.Embed(description=f"✕ Max whitelisted roles reached `{settings.get('max_roles', 10)}`", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        if self.is_role_whitelisted(ctx.guild.id, role.id):
            embed = discord.Embed(description=f"✕ {role.mention} is already whitelisted", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        self.add_role_to_whitelist(ctx.guild.id, role.id, ctx.author.id, reason)
        # Save to database
        if self.db:
            try:
                await self.db.add_whitelisted_role(ctx.guild.id, role.id, ctx.author.id, reason)
            except Exception as e:
                logger.warning(f'Failed to save whitelisted role to database: {e}')
        await self.log_whitelist_action(ctx.guild, 'add', role, ctx.author, reason=reason)

        embed = discord.Embed(description=f"+ Added {role.mention} to whitelisted roles\n› Members with this role are now immune to anti-nuke", color=EMBED_COLOR)
        await ctx.send(embed=embed)

    @wlist.command(name='unrole')
    @commands.has_permissions(administrator=True)
    async def whitelist_unrole(self, ctx: commands.Context, role: discord.Role):
        """Remove a role from the whitelist"""
        if not await self.owner_check(ctx):
            return

        if not self.is_role_whitelisted(ctx.guild.id, role.id):
            embed = discord.Embed(description=f"✕ {role.mention} is not whitelisted", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        self.remove_role_from_whitelist(ctx.guild.id, role.id)
        # Remove from database
        if self.db:
            try:
                await self.db.remove_whitelisted_role(ctx.guild.id, role.id)
            except Exception as e:
                logger.warning(f'Failed to remove whitelisted role from database: {e}')
        await self.log_whitelist_action(ctx.guild, 'remove', role, ctx.author)

        embed = discord.Embed(description=f"− Removed {role.mention} from whitelisted roles", color=EMBED_COLOR)
        await ctx.send(embed=embed)

    @wlist.command(name='roles')
    @commands.has_permissions(administrator=True)
    async def whitelist_roles_list(self, ctx: commands.Context):
        """List all whitelisted roles"""
        if not await self.owner_check(ctx):
            return

        role_entries = self.get_whitelisted_roles(ctx.guild.id)

        if not role_entries:
            embed = discord.Embed(description="No whitelisted roles\nUse `wlist role @role` to add one", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        roles_list = []
        for role_id, entry in role_entries.items():
            role = ctx.guild.get_role(role_id)
            if role:
                added_by = ctx.guild.get_member(entry.added_by)
                added_by_str = added_by.mention if added_by else f"`{entry.added_by}`"
                roles_list.append(f"› {role.mention} − added by {added_by_str}")
            else:
                roles_list.append(f"› `{role_id}` (deleted)")

        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = f"**Whitelisted Roles** `{len(role_entries)}`\n\n" + "\n".join(roles_list)
        await ctx.send(embed=embed)

    @wlist.command(name='clearroles')
    @commands.has_permissions(administrator=True)
    async def whitelist_clear_roles(self, ctx: commands.Context):
        """Clear all whitelisted roles"""
        if not await self.owner_check(ctx):
            return

        count = len(self.whitelisted_roles.get(ctx.guild.id, {}))
        self.whitelisted_roles[ctx.guild.id] = {}
        # Clear from database
        if self.db:
            try:
                await self.db.clear_whitelisted_roles(ctx.guild.id)
            except Exception as e:
                logger.warning(f'Failed to clear whitelisted roles from database: {e}')
        embed = discord.Embed(description=f"+ Cleared `{count}` whitelisted roles", color=EMBED_COLOR)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Whitelist(bot))
