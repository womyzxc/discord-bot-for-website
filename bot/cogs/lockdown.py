"""
Lockdown Management Cog
=======================
Server lockdown features:
- Full server lockdown
- Channel lockdown
- Category lockdown
- Panic mode (instant lockdown)
- Scheduled lockdowns
"""
import discord
from discord.ext import commands
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio
import logging
from typing import Dict, List, Optional, Set
logger = logging.getLogger('Offcialx.Lockdown')
class LockdownState:
    """Represents a lockdown state"""
    def __init__(self):
        self.active = False
        self.started_at: Optional[datetime] = None
        self.duration: Optional[int] = None
        self.reason: str = ""
        self.triggered_by: Optional[int] = None
        self.locked_channels: Set[int] = set()
        self.original_permissions: Dict[int, Dict[int, discord.PermissionOverwrite]] = {}
class Lockdown(commands.Cog):
    """Lockdown Management System"""
    # Minimal embed color
    EMBED_COLOR = 0x2b2d31
    def __init__(self, bot):
        self.bot = bot
        self.db = None  # Will be injected by bot
        self._settings_loaded: set = set()
        # Owner IDs from environment
        self.owner_ids: set = set()
        import os
        for oid in os.getenv('OWNER_IDS', '').split(','):
            try:
                self.owner_ids.add(int(oid.strip()))
            except:
                pass
        # Guild lockdown states
        self.lockdown_states: Dict[int, LockdownState] = defaultdict(LockdownState)
        # Guild settings
        self.guild_settings: Dict[int, Dict] = {}
        # Panic mode cooldown
        self.panic_cooldowns: Dict[int, datetime] = {}
    async def get_settings(self, guild_id: int) -> Dict:
        """Get guild settings - loads from database if available"""
        if guild_id not in self.guild_settings:
            self.guild_settings[guild_id] = {
                'enabled': True,
                'default_duration': 300,  # 5 minutes
                'max_duration': 3600,  # 1 hour
                'panic_cooldown': 60,  # 1 minute cooldown
                'auto_unlock': True,
                'notify_channel': None,
                'lockdown_message': "🔒 This server is currently in lockdown mode.",
                'unlock_message': "🔓 Lockdown has been lifted. Normal operations resumed.",
                'exempt_roles': [],
                'panic_triggers': ['nuke', 'raid', 'attack'],
            }
            # Try to load from database
            if self.db and guild_id not in self._settings_loaded:
                try:
                    db_settings = await self.db.get_guild_settings(guild_id, 'lockdown')
                    if db_settings:
                        self.guild_settings[guild_id].update(db_settings)
                    self._settings_loaded.add(guild_id)
                except Exception as e:
                    logger.warning(f'Failed to load lockdown settings from database: {e}')
        return self.guild_settings[guild_id]
    async def save_settings(self, guild_id: int):
        """Save guild settings to database"""
        if not self.db:
            return
        try:
            settings = self.guild_settings.get(guild_id, {})
            await self.db.save_guild_settings(guild_id, 'lockdown', settings)
        except Exception as e:
            logger.warning(f'Failed to save lockdown settings to database: {e}')

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
            embed = discord.Embed(description="✕ Only server owner can use this command", color=0x2b2d31)
            await ctx.send(embed=embed)
            return False
        return True

    def get_state(self, guild_id: int) -> LockdownState:
        """Get lockdown state for a guild"""
        return self.lockdown_states[guild_id]
    async def lock_channel(self, channel: discord.TextChannel, reason: str,
                          exempt_roles: List[discord.Role] = None) -> bool:
        """Lock a single channel"""
        state = self.get_state(channel.guild.id)
        try:
            # Store original permissions
            state.original_permissions[channel.id] = {}
            for target, overwrite in channel.overwrites.items():
                if isinstance(target, discord.Role):
                    state.original_permissions[channel.id][target.id] = overwrite
            # Set lockdown permissions
            overwrite = channel.overwrites_for(channel.guild.default_role)
            overwrite.send_messages = False
            overwrite.add_reactions = False
            await channel.set_permissions(
                channel.guild.default_role,
                overwrite=overwrite,
                reason=f"[Lockdown] {reason}"
            )
            # Allow exempt roles
            if exempt_roles:
                for role in exempt_roles:
                    role_overwrite = channel.overwrites_for(role)
                    role_overwrite.send_messages = True
                    await channel.set_permissions(role, overwrite=role_overwrite, reason="[Lockdown] Exempt role")
            state.locked_channels.add(channel.id)
            return True
        except discord.Forbidden:
            logger.error(f'Cannot lock channel {channel.name} - missing permissions')
            return False
    async def unlock_channel(self, channel: discord.TextChannel, reason: str) -> bool:
        """Unlock a single channel"""
        state = self.get_state(channel.guild.id)
        try:
            # Restore original permissions if stored
            if channel.id in state.original_permissions:
                for role_id, overwrite in state.original_permissions[channel.id].items():
                    role = channel.guild.get_role(role_id)
                    if role:
                        await channel.set_permissions(role, overwrite=overwrite, reason=f"[Unlock] {reason}")
            else:
                # Reset to default
                overwrite = channel.overwrites_for(channel.guild.default_role)
                overwrite.send_messages = None
                overwrite.add_reactions = None
                await channel.set_permissions(
                    channel.guild.default_role,
                    overwrite=overwrite,
                    reason=f"[Unlock] {reason}"
                )
            state.locked_channels.discard(channel.id)
            return True
        except discord.Forbidden:
            logger.error(f'Cannot unlock channel {channel.name} - missing permissions')
            return False
    async def lockdown_server(self, guild: discord.Guild, reason: str, duration: int,
                              triggered_by: discord.Member) -> int:
        """Lock down the entire server"""
        state = self.get_state(guild.id)
        settings = await self.get_settings(guild.id)
        state.active = True
        state.started_at = datetime.utcnow()
        state.duration = duration
        state.reason = reason
        state.triggered_by = triggered_by.id
        # Get exempt roles
        exempt_roles = [guild.get_role(r) for r in settings['exempt_roles'] if guild.get_role(r)]
        locked_count = 0
        for channel in guild.text_channels:
            if await self.lock_channel(channel, reason, exempt_roles):
                locked_count += 1
        logger.warning(f'SERVER LOCKDOWN: {guild.name} - {locked_count} channels locked - {reason}')
        # Send notification
        await self.send_lockdown_notification(guild, 'lock', reason, duration)
        # Schedule auto-unlock
        if settings['auto_unlock'] and duration > 0:
            asyncio.create_task(self.schedule_unlock(guild, duration))
        return locked_count
    async def unlock_server(self, guild: discord.Guild, reason: str = "Manual unlock") -> int:
        """Unlock the entire server"""
        state = self.get_state(guild.id)
        if not state.active:
            return 0
        unlocked_count = 0
        for channel_id in list(state.locked_channels):
            channel = guild.get_channel(channel_id)
            if channel:
                if await self.unlock_channel(channel, reason):
                    unlocked_count += 1
        state.active = False
        state.locked_channels.clear()
        state.original_permissions.clear()
        logger.info(f'SERVER UNLOCK: {guild.name} - {unlocked_count} channels unlocked')
        await self.send_lockdown_notification(guild, 'unlock', reason)
        return unlocked_count
    async def schedule_unlock(self, guild: discord.Guild, duration: int):
        """Schedule an automatic unlock"""
        await asyncio.sleep(duration)
        state = self.get_state(guild.id)
        if state.active:
            await self.unlock_server(guild, "Automatic unlock - duration expired")
    async def send_lockdown_notification(self, guild: discord.Guild, action: str,
                                         reason: str, duration: int = None):
        """Send lockdown notification"""
        settings = await self.get_settings(guild.id)
        channel_id = settings['notify_channel']
        if not channel_id:
            return
        channel = guild.get_channel(channel_id)
        if not channel:
            return
        embed = discord.Embed(color=self.EMBED_COLOR)
        if action == 'lock':
            text = f"**Server Locked**\n\n› Reason: `{reason}`"
            if duration:
                text += f"\n› Duration: `{duration // 60}m`"
            embed.description = text
        else:
            embed.description = f"**Server Unlocked**\n\n› Reason: `{reason}`"
        try:
            await channel.send(embed=embed)
        except:
            pass
    async def trigger_panic_mode(self, guild: discord.Guild, member: discord.Member, trigger: str) -> bool:
        """Trigger instant panic mode lockdown"""
        settings = await self.get_settings(guild.id)
        # Check cooldown
        if guild.id in self.panic_cooldowns:
            cooldown_end = self.panic_cooldowns[guild.id]
            if datetime.utcnow() < cooldown_end:
                return False
        # Set cooldown
        self.panic_cooldowns[guild.id] = datetime.utcnow() + timedelta(seconds=settings['panic_cooldown'])
        # Trigger lockdown
        await self.lockdown_server(
            guild,
            f"PANIC MODE: {trigger}",
            settings['default_duration'],
            member
        )
        return True
    # ==================== COMMANDS ====================
    @commands.hybrid_group(name='lockdown', aliases=['ld'], invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def lockdown_cmd(self, ctx: commands.Context, duration: int = None, *, reason: str = "No reason"):
        """Lock down the server"""
        if not await self.owner_check(ctx):
            return
        settings = await self.get_settings(ctx.guild.id)
        state = self.get_state(ctx.guild.id)
        if state.active:
            embed = discord.Embed(description="✕ Server already locked. Use `lockdown end`", color=self.EMBED_COLOR)
            return await ctx.send(embed=embed)
        if duration is None:
            duration = settings['default_duration']
        duration = min(duration, settings['max_duration'])
        locked = await self.lockdown_server(ctx.guild, reason, duration, ctx.author)
        embed = discord.Embed(color=self.EMBED_COLOR)
        embed.description = (
            f"+ Locked server\n\n"
            f"› Channels: `{locked}`\n"
            f"› Duration: `{duration // 60}m`\n"
            f"› Reason: `{reason}`"
        )
        await ctx.send(embed=embed)
    @lockdown_cmd.command(name='end', aliases=['unlock', 'stop'])
    @commands.has_permissions(administrator=True)
    async def lockdown_end(self, ctx: commands.Context, *, reason: str = "Manual unlock"):
        """End the server lockdown"""
        if not await self.owner_check(ctx):
            return
        state = self.get_state(ctx.guild.id)
        if not state.active:
            embed = discord.Embed(description="✕ Server not locked", color=self.EMBED_COLOR)
            return await ctx.send(embed=embed)
        unlocked = await self.unlock_server(ctx.guild, reason)
        embed = discord.Embed(description=f"+ Unlocked `{unlocked}` channels", color=self.EMBED_COLOR)
        await ctx.send(embed=embed)
    @lockdown_cmd.command(name='channel', aliases=['ch'])
    @commands.has_permissions(manage_channels=True)
    async def lockdown_channel(self, ctx: commands.Context, channel: discord.TextChannel = None, *, reason: str = "Channel lockdown"):
        """Lock a specific channel"""
        if not await self.owner_check(ctx):
            return
        channel = channel or ctx.channel
        settings = await self.get_settings(ctx.guild.id)
        exempt_roles = [ctx.guild.get_role(r) for r in settings['exempt_roles'] if ctx.guild.get_role(r)]
        if await self.lock_channel(channel, reason, exempt_roles):
            embed = discord.Embed(description=f"+ Locked {channel.mention}", color=self.EMBED_COLOR)
        else:
            embed = discord.Embed(description=f"✕ Failed to lock {channel.mention}", color=self.EMBED_COLOR)
        await ctx.send(embed=embed)
    @lockdown_cmd.command(name='unchannel', aliases=['unch'])
    @commands.has_permissions(manage_channels=True)
    async def lockdown_unchannel(self, ctx: commands.Context, channel: discord.TextChannel = None, *, reason: str = "Channel unlock"):
        """Unlock a specific channel"""
        if not await self.owner_check(ctx):
            return
        channel = channel or ctx.channel
        if await self.unlock_channel(channel, reason):
            embed = discord.Embed(description=f"+ Unlocked {channel.mention}", color=self.EMBED_COLOR)
        else:
            embed = discord.Embed(description=f"✕ Failed to unlock {channel.mention}", color=self.EMBED_COLOR)
        await ctx.send(embed=embed)
    @lockdown_cmd.command(name='status')
    @commands.has_permissions(administrator=True)
    async def lockdown_status(self, ctx: commands.Context):
        """Check lockdown status"""
        if not await self.owner_check(ctx):
            return
        state = self.get_state(ctx.guild.id)
        status = "active" if state.active else "inactive"
        embed = discord.Embed(color=self.EMBED_COLOR)
        if state.active:
            embed.description = (
                f"**Lockdown Status**\n\n"
                f"› Status: `{status}`\n"
                f"› Channels: `{len(state.locked_channels)}`\n"
                f"› Reason: `{state.reason}`"
            )
        else:
            embed.description = f"**Lockdown Status**\n\n› Status: `inactive`"
        await ctx.send(embed=embed)
    @lockdown_cmd.command(name='panic')
    @commands.has_permissions(administrator=True)
    async def lockdown_panic(self, ctx: commands.Context, *, trigger: str = "Manual panic"):
        """Trigger instant panic mode lockdown"""
        if not await self.owner_check(ctx):
            return
        success = await self.trigger_panic_mode(ctx.guild, ctx.author, trigger)
        if success:
            embed = discord.Embed(description="+ Panic mode activated - Server locked", color=self.EMBED_COLOR)
        else:
            embed = discord.Embed(description="✕ Panic mode on cooldown", color=self.EMBED_COLOR)
        await ctx.send(embed=embed)
    @lockdown_cmd.command(name='exempt')
    @commands.has_permissions(administrator=True)
    async def lockdown_exempt(self, ctx: commands.Context, role: discord.Role):
        """Add a role to lockdown exemptions"""
        if not await self.owner_check(ctx):
            return
        settings = await self.get_settings(ctx.guild.id)
        if role.id in settings['exempt_roles']:
            settings['exempt_roles'].remove(role.id)
            await self.save_settings(ctx.guild.id)
            embed = discord.Embed(description=f"− Removed {role.mention} from lockdown exemptions", color=self.EMBED_COLOR)
        else:
            settings['exempt_roles'].append(role.id)
            await self.save_settings(ctx.guild.id)
            embed = discord.Embed(description=f"+ Added {role.mention} to lockdown exemptions", color=self.EMBED_COLOR)
        await ctx.send(embed=embed)
    @lockdown_cmd.command(name='notify')
    @commands.has_permissions(administrator=True)
    async def lockdown_notify(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set lockdown notification channel"""
        if not await self.owner_check(ctx):
            return
        settings = await self.get_settings(ctx.guild.id)
        settings['notify_channel'] = channel.id
        await self.save_settings(ctx.guild.id)
        embed = discord.Embed(description=f"+ Set notification channel to {channel.mention}", color=self.EMBED_COLOR)
        await ctx.send(embed=embed)
async def setup(bot):
    await bot.add_cog(Lockdown(bot))
