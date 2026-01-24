"""
Moderation Commands Cog - Minimal Style
All commands work with both ! and /
"""

import discord
from discord.ext import commands
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio
import logging
from typing import Optional

logger = logging.getLogger('Offcialx.Moderation')

# Minimal embed color
EMBED_COLOR = 0x2b2d31


class Moderation(commands.Cog):
    """Moderation Commands"""

    def __init__(self, bot):
        self.bot = bot
        self.db = None  # Will be injected by bot
        self.warnings: dict = defaultdict(lambda: defaultdict(list))
        self.guild_settings: dict = {}
        self._settings_loaded: set = set()

    async def get_settings(self, guild_id: int) -> dict:
        """Get guild moderation settings - loads from database if available"""
        if guild_id not in self.guild_settings:
            # Default settings
            self.guild_settings[guild_id] = {
                'warn_threshold': 3,
                'warn_action': 'mute',
                'warn_mute_duration': 3600,
                'default_mute_duration': 3600,
                'dm_on_action': True,
                'log_channel': None,
            }

            # Try to load from database
            if self.db and guild_id not in self._settings_loaded:
                try:
                    db_settings = await self.db.get_guild_settings(guild_id, 'moderation')
                    if db_settings:
                        self.guild_settings[guild_id].update(db_settings)

                    # Load warnings from database
                    # Note: warnings are loaded on-demand per user
                    self._settings_loaded.add(guild_id)
                except Exception as e:
                    logger.warning(f'Failed to load mod settings from database: {e}')

        return self.guild_settings[guild_id]

    async def save_settings(self, guild_id: int):
        """Save guild settings to database"""
        if not self.db:
            return

        try:
            settings = self.guild_settings.get(guild_id, {})
            await self.db.save_guild_settings(guild_id, 'moderation', settings)
        except Exception as e:
            logger.warning(f'Failed to save mod settings to database: {e}')

    async def get_warnings_from_db(self, guild_id: int, user_id: int) -> list:
        """Get warnings from database"""
        if self.db:
            try:
                return await self.db.get_warnings(guild_id, user_id)
            except:
                pass
        return self.warnings[guild_id].get(user_id, [])

    async def add_warning_to_db(self, guild_id: int, user_id: int, moderator_id: int, reason: str):
        """Add warning to database"""
        if self.db:
            try:
                await self.db.add_warning(guild_id, user_id, moderator_id, reason)
            except Exception as e:
                logger.warning(f'Failed to save warning to database: {e}')

    async def dm_user(self, member: discord.Member, action: str, reason: str,
                      duration: str = None, guild_name: str = None):
        """Send DM to user about moderation action"""
        try:
            embed = discord.Embed(color=EMBED_COLOR)
            text = f"You have been **{action}** in **{guild_name or 'a server'}**"
            if reason:
                text += f"\n› Reason: `{reason}`"
            if duration:
                text += f"\n› Duration: `{duration}`"
            embed.description = text
            await member.send(embed=embed)
            return True
        except:
            return False

    async def log_mod_action(self, guild: discord.Guild, action: str,
                            moderator: discord.Member, target,
                            reason: str = None, duration: str = None):
        """Log moderation action"""
        settings = await self.get_settings(guild.id)
        if not settings['log_channel']:
            return

        channel = guild.get_channel(settings['log_channel'])
        if not channel:
            return

        embed = discord.Embed(color=EMBED_COLOR)
        text = f"**{action.title()}**\n\n› User: {target.mention}\n› Moderator: {moderator.mention}"
        if duration:
            text += f"\n› Duration: `{duration}`"
        if reason:
            text += f"\n› Reason: `{reason}`"
        embed.description = text

        try:
            await channel.send(embed=embed)
        except:
            pass

    # ==================== BAN COMMANDS ====================

    @commands.hybrid_command(name='ban')
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban(self, ctx: commands.Context, member: discord.Member, *, reason: str = None):
        """Ban a member from the server"""
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            embed = discord.Embed(description="✕ Cannot ban someone with higher role", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        if member.id == ctx.author.id:
            embed = discord.Embed(description="✕ Cannot ban yourself", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        if member.id == self.bot.user.id:
            embed = discord.Embed(description="✕ Cannot ban me", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        settings = await self.get_settings(ctx.guild.id)

        if settings['dm_on_action']:
            await self.dm_user(member, "banned", reason, guild_name=ctx.guild.name)

        try:
            await member.ban(reason=f"{reason or 'No reason'} | By: {ctx.author}")
            embed = discord.Embed(description=f"+ Banned {member.mention}", color=EMBED_COLOR)
            if reason:
                embed.description += f"\n› Reason: `{reason}`"
            await ctx.send(embed=embed)
            await self.log_mod_action(ctx.guild, 'ban', ctx.author, member, reason)
        except discord.Forbidden:
            embed = discord.Embed(description="✕ Missing permissions to ban", color=EMBED_COLOR)
            await ctx.send(embed=embed)

    @commands.hybrid_command(name='unban')
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban(self, ctx: commands.Context, user_id: int, *, reason: str = None):
        """Unban a user by ID"""
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user, reason=f"{reason or 'No reason'} | By: {ctx.author}")
            embed = discord.Embed(description=f"+ Unbanned {user.mention}", color=EMBED_COLOR)
            await ctx.send(embed=embed)
            await self.log_mod_action(ctx.guild, 'unban', ctx.author, user, reason)
        except discord.NotFound:
            embed = discord.Embed(description="✕ User not found or not banned", color=EMBED_COLOR)
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = discord.Embed(description="✕ Missing permissions to unban", color=EMBED_COLOR)
            await ctx.send(embed=embed)

    @commands.hybrid_command(name='massban')
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(ban_members=True)
    async def massban(self, ctx: commands.Context, user_ids: str, *, reason: str = "Mass ban"):
        """Ban multiple users by ID (comma separated)"""
        ids = [int(i.strip()) for i in user_ids.split(',') if i.strip().isdigit()]

        if not ids:
            embed = discord.Embed(description="✕ Provide user IDs separated by commas", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        if len(ids) > 50:
            embed = discord.Embed(description="✕ Maximum 50 users per mass ban", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        banned = 0
        for user_id in ids:
            try:
                await ctx.guild.ban(discord.Object(id=user_id), reason=f"Mass ban: {reason} | By: {ctx.author}")
                banned += 1
            except:
                pass

        embed = discord.Embed(description=f"+ Banned `{banned}/{len(ids)}` users", color=EMBED_COLOR)
        await ctx.send(embed=embed)

    # ==================== KICK COMMANDS ====================

    @commands.hybrid_command(name='kick')
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: str = None):
        """Kick a member from the server"""
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            embed = discord.Embed(description="✕ Cannot kick someone with higher role", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        if member.id == ctx.author.id:
            embed = discord.Embed(description="✕ Cannot kick yourself", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        settings = await self.get_settings(ctx.guild.id)

        if settings['dm_on_action']:
            await self.dm_user(member, "kicked", reason, guild_name=ctx.guild.name)

        try:
            await member.kick(reason=f"{reason or 'No reason'} | By: {ctx.author}")
            embed = discord.Embed(description=f"+ Kicked {member.mention}", color=EMBED_COLOR)
            if reason:
                embed.description += f"\n› Reason: `{reason}`"
            await ctx.send(embed=embed)
            await self.log_mod_action(ctx.guild, 'kick', ctx.author, member, reason)
        except discord.Forbidden:
            embed = discord.Embed(description="✕ Missing permissions to kick", color=EMBED_COLOR)
            await ctx.send(embed=embed)

    # ==================== MUTE/TIMEOUT COMMANDS ====================

    @commands.hybrid_command(name='mute', aliases=['timeout'])
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def mute(self, ctx: commands.Context, member: discord.Member, duration: str = "1h", *, reason: str = None):
        """Timeout a member (e.g., 10m, 1h, 1d)"""
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            embed = discord.Embed(description="✕ Cannot mute someone with higher role", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        duration_map = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
        try:
            unit = duration[-1].lower()
            amount = int(duration[:-1])
            seconds = amount * duration_map.get(unit, 60)
        except:
            seconds = 3600

        seconds = min(seconds, 28 * 24 * 3600)
        settings = await self.get_settings(ctx.guild.id)

        if settings['dm_on_action']:
            await self.dm_user(member, "muted", reason, duration=duration, guild_name=ctx.guild.name)

        try:
            await member.timeout(timedelta(seconds=seconds), reason=f"{reason or 'No reason'} | By: {ctx.author}")
            embed = discord.Embed(description=f"+ Muted {member.mention} for `{duration}`", color=EMBED_COLOR)
            if reason:
                embed.description += f"\n› Reason: `{reason}`"
            await ctx.send(embed=embed)
            await self.log_mod_action(ctx.guild, 'mute', ctx.author, member, reason, duration)
        except discord.Forbidden:
            embed = discord.Embed(description="✕ Missing permissions to mute", color=EMBED_COLOR)
            await ctx.send(embed=embed)

    @commands.hybrid_command(name='unmute', aliases=['untimeout'])
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def unmute(self, ctx: commands.Context, member: discord.Member, *, reason: str = None):
        """Remove timeout from a member"""
        try:
            await member.timeout(None, reason=f"{reason or 'No reason'} | By: {ctx.author}")
            embed = discord.Embed(description=f"+ Unmuted {member.mention}", color=EMBED_COLOR)
            await ctx.send(embed=embed)
            await self.log_mod_action(ctx.guild, 'unmute', ctx.author, member, reason)
        except discord.Forbidden:
            embed = discord.Embed(description="✕ Missing permissions to unmute", color=EMBED_COLOR)
            await ctx.send(embed=embed)

    # ==================== WARN COMMANDS ====================

    @commands.hybrid_command(name='warn')
    @commands.has_permissions(moderate_members=True)
    async def warn(self, ctx: commands.Context, member: discord.Member, *, reason: str = "No reason"):
        """Warn a member"""
        if member.id == ctx.author.id:
            embed = discord.Embed(description="✕ Cannot warn yourself", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        if member.bot:
            embed = discord.Embed(description="✕ Cannot warn bots", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        settings = await self.get_settings(ctx.guild.id)

        warning = {
            'reason': reason,
            'moderator': ctx.author.id,
            'time': datetime.utcnow().isoformat()
        }
        self.warnings[ctx.guild.id][member.id].append(warning)

        # Save to database
        await self.add_warning_to_db(ctx.guild.id, member.id, ctx.author.id, reason)

        warn_count = len(self.warnings[ctx.guild.id][member.id])

        embed = discord.Embed(
            description=f"+ Warned {member.mention} `{warn_count}/{settings['warn_threshold']}`\n› Reason: `{reason}`",
            color=EMBED_COLOR
        )
        await ctx.send(embed=embed)
        await self.log_mod_action(ctx.guild, 'warn', ctx.author, member, reason)

        if settings['dm_on_action']:
            await self.dm_user(member, "warned", reason, guild_name=ctx.guild.name)

        if warn_count >= settings['warn_threshold']:
            action = settings['warn_action']
            if action == 'mute':
                duration = timedelta(seconds=settings['warn_mute_duration'])
                await member.timeout(duration, reason=f"Warning threshold reached")
                embed = discord.Embed(description=f"+ Muted {member.mention} for reaching warn threshold", color=EMBED_COLOR)
                await ctx.send(embed=embed)
            elif action == 'kick':
                await member.kick(reason=f"Warning threshold reached")
                embed = discord.Embed(description=f"+ Kicked {member.mention} for reaching warn threshold", color=EMBED_COLOR)
                await ctx.send(embed=embed)
            elif action == 'ban':
                await member.ban(reason=f"Warning threshold reached")
                embed = discord.Embed(description=f"+ Banned {member.mention} for reaching warn threshold", color=EMBED_COLOR)
                await ctx.send(embed=embed)
            self.warnings[ctx.guild.id][member.id] = []

    @commands.hybrid_command(name='warnings', aliases=['warns'])
    @commands.has_permissions(moderate_members=True)
    async def warnings_cmd(self, ctx: commands.Context, member: discord.Member):
        """View warnings for a member"""
        warns = self.warnings[ctx.guild.id].get(member.id, [])

        if not warns:
            embed = discord.Embed(description=f"{member.mention} has no warnings", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        warn_list = []
        for i, warn in enumerate(warns[-10:], 1):
            warn_list.append(f"`{i}.` {warn['reason']}")

        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = f"**Warnings for {member.display_name}** `{len(warns)}`\n\n" + "\n".join(warn_list)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='clearwarns', aliases=['clearwarnings'])
    @commands.has_permissions(administrator=True)
    async def clearwarns(self, ctx: commands.Context, member: discord.Member):
        """Clear all warnings for a member"""
        count = len(self.warnings[ctx.guild.id].get(member.id, []))
        self.warnings[ctx.guild.id][member.id] = []

        # Clear from database
        if self.db:
            try:
                await self.db.clear_warnings(ctx.guild.id, member.id)
            except:
                pass

        embed = discord.Embed(description=f"+ Cleared `{count}` warnings for {member.mention}", color=EMBED_COLOR)
        await ctx.send(embed=embed)

    # ==================== PURGE COMMANDS ====================

    @commands.command(name='purge', aliases=['clear', 'prune'])
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def purge(self, ctx: commands.Context, target: str = None, amount: int = None):
        """Delete messages from the channel

        Usage:
        !purge 10 - Delete 10 messages
        !purge @user 10 - Delete 10 messages from user
        """
        # Parse arguments
        member = None

        if target is None:
            # No args - default to 10
            amount = 10
        elif target.isdigit():
            # Just a number: !purge 10
            amount = int(target)
        else:
            # User mention: !purge @user 10
            # Try to get member from mention
            try:
                # Remove <@> and <@!> from mention
                user_id = target.replace('<@', '').replace('>', '').replace('!', '')
                if user_id.isdigit():
                    member = ctx.guild.get_member(int(user_id))
            except:
                pass

            if member is None:
                embed = discord.Embed(description="User not found", color=EMBED_COLOR)
                return await ctx.send(embed=embed)

            if amount is None:
                amount = 10

        if amount < 1 or amount > 1000:
            embed = discord.Embed(description="Amount must be 1-1000", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        try:
            await ctx.message.delete()

            if member:
                # Purge from specific user - search more messages to find enough
                deleted_messages = []

                async for message in ctx.channel.history(limit=500):
                    if message.author.id == member.id:
                        deleted_messages.append(message)
                        if len(deleted_messages) >= amount:
                            break

                if deleted_messages:
                    await ctx.channel.delete_messages(deleted_messages)

                embed = discord.Embed(description=f"+ Deleted `{len(deleted_messages)}` messages from {member.mention}", color=EMBED_COLOR)
            else:
                # Purge all messages
                deleted = await ctx.channel.purge(limit=amount)
                embed = discord.Embed(description=f"+ Deleted `{len(deleted)}` messages", color=EMBED_COLOR)

            msg = await ctx.send(embed=embed)
            await asyncio.sleep(3)
            await msg.delete()
        except discord.Forbidden:
            embed = discord.Embed(description="Missing permissions", color=EMBED_COLOR)
            await ctx.send(embed=embed)
        except discord.HTTPException:
            embed = discord.Embed(description="Failed to delete (messages may be too old)", color=EMBED_COLOR)
            await ctx.send(embed=embed)

    @commands.hybrid_command(name='purgeuser')
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def purgeuser(self, ctx: commands.Context, member: discord.Member, amount: int = 100):
        """Delete messages from a specific user"""
        if amount < 1 or amount > 1000:
            embed = discord.Embed(description="Amount must be 1-1000", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        try:
            deleted_messages = []

            async for message in ctx.channel.history(limit=500):
                if message.author.id == member.id:
                    deleted_messages.append(message)
                    if len(deleted_messages) >= amount:
                        break

            if deleted_messages:
                await ctx.channel.delete_messages(deleted_messages)

            embed = discord.Embed(description=f"+ Deleted `{len(deleted_messages)}` messages from {member.mention}", color=EMBED_COLOR)
            msg = await ctx.send(embed=embed)
            await asyncio.sleep(3)
            await msg.delete()
        except discord.Forbidden:
            embed = discord.Embed(description="Missing permissions", color=EMBED_COLOR)
            await ctx.send(embed=embed)
        except discord.HTTPException:
            embed = discord.Embed(description="Failed to delete (messages may be too old)", color=EMBED_COLOR)
            await ctx.send(embed=embed)

    # ==================== SLOWMODE COMMAND ====================

    @commands.hybrid_command(name='slowmode')
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def slowmode(self, ctx: commands.Context, seconds: int = 0):
        """Set slowmode for the channel (0 to disable)"""
        if seconds < 0 or seconds > 21600:
            embed = discord.Embed(description="✕ Slowmode must be 0-21600 seconds", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        await ctx.channel.edit(slowmode_delay=seconds)

        if seconds == 0:
            embed = discord.Embed(description="+ Disabled slowmode", color=EMBED_COLOR)
        else:
            embed = discord.Embed(description=f"+ Set slowmode to `{seconds}s`", color=EMBED_COLOR)
        await ctx.send(embed=embed)

    # ==================== SETLOG COMMAND ====================

    @commands.hybrid_command(name='modlog')
    @commands.has_permissions(administrator=True)
    async def modlog(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set the moderation log channel"""
        settings = await self.get_settings(ctx.guild.id)
        settings['log_channel'] = channel.id
        await self.save_settings(ctx.guild.id)
        embed = discord.Embed(description=f"+ Set mod log to {channel.mention}", color=EMBED_COLOR)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Moderation(bot))
