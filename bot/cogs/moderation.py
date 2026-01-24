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
import re
from typing import Optional, Union

logger = logging.getLogger('Offcialx.Moderation')

# Minimal embed color
EMBED_COLOR = 0x2b2d31


class Moderation(commands.Cog):
    """Moderation Commands"""

    def __init__(self, bot):
        self.bot = bot
        self.db = None
        self.warnings: dict = defaultdict(lambda: defaultdict(list))
        self.guild_settings: dict = {}
        self._settings_loaded: set = set()

    async def get_settings(self, guild_id: int) -> dict:
        """Get guild moderation settings"""
        if guild_id not in self.guild_settings:
            self.guild_settings[guild_id] = {
                'warn_threshold': 3,
                'warn_action': 'mute',
                'warn_mute_duration': 3600,
                'default_mute_duration': 3600,
                'dm_on_action': True,
                'log_channel': None,
            }

            if self.db and guild_id not in self._settings_loaded:
                try:
                    db_settings = await self.db.get_guild_settings(guild_id, 'moderation')
                    if db_settings:
                        self.guild_settings[guild_id].update(db_settings)
                    self._settings_loaded.add(guild_id)
                except Exception as e:
                    logger.warning(f'Failed to load mod settings: {e}')

        return self.guild_settings[guild_id]

    async def save_settings(self, guild_id: int):
        """Save guild settings to database"""
        if not self.db:
            return
        try:
            settings = self.guild_settings.get(guild_id, {})
            await self.db.save_guild_settings(guild_id, 'moderation', settings)
        except Exception as e:
            logger.warning(f'Failed to save mod settings: {e}')

    async def add_warning_to_db(self, guild_id: int, user_id: int, moderator_id: int, reason: str):
        """Add warning to database"""
        if self.db:
            try:
                await self.db.add_warning(guild_id, user_id, moderator_id, reason)
            except Exception as e:
                logger.warning(f'Failed to save warning: {e}')

    # ==================== HELPER FUNCTIONS ====================

    async def resolve_member(self, ctx, user_input: str) -> Optional[discord.Member]:
        """Resolve a member from User ID, mention, or username"""
        if not user_input:
            return None

        user_input = user_input.strip()

        # Extract ID from mention <@123> or <@!123>
        mention_match = re.match(r'<@!?(\d+)>', user_input)
        if mention_match:
            user_id = int(mention_match.group(1))
            member = ctx.guild.get_member(user_id)
            if member:
                return member

        # Try as raw user ID
        if user_input.isdigit():
            user_id = int(user_input)
            member = ctx.guild.get_member(user_id)
            if member:
                return member
            try:
                member = await ctx.guild.fetch_member(user_id)
                if member:
                    return member
            except:
                pass

        # Search by username (case-insensitive)
        user_input_lower = user_input.lower().lstrip('@')

        # Exact match first
        for member in ctx.guild.members:
            if member.name.lower() == user_input_lower:
                return member
            if member.display_name.lower() == user_input_lower:
                return member

        # Partial match
        for member in ctx.guild.members:
            if user_input_lower in member.name.lower():
                return member
            if user_input_lower in member.display_name.lower():
                return member

        return None

    async def resolve_user(self, user_input: str) -> Optional[discord.User]:
        """Resolve a user from User ID or mention (for users not in server)"""
        if not user_input:
            return None

        user_input = user_input.strip()

        mention_match = re.match(r'<@!?(\d+)>', user_input)
        if mention_match:
            try:
                return await self.bot.fetch_user(int(mention_match.group(1)))
            except:
                return None

        if user_input.isdigit():
            try:
                return await self.bot.fetch_user(int(user_input))
            except:
                return None

        return None

    def parse_duration(self, duration_str: str) -> tuple:
        """Parse duration string like 10m, 1h, 1d. Returns (seconds, display_str)"""
        duration_map = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
        try:
            unit = duration_str[-1].lower()
            if unit in duration_map:
                amount = int(duration_str[:-1])
                seconds = amount * duration_map[unit]
                return (min(seconds, 28 * 24 * 3600), duration_str)
        except:
            pass
        return (3600, "1h")

    def is_duration(self, text: str) -> bool:
        """Check if text looks like a duration"""
        if not text:
            return False
        return bool(re.match(r'^\d+[smhd]$', text.lower()))

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
    async def ban(self, ctx: commands.Context, *, args: str = None):
        """Ban a member (Usage: !ban <user> [reason])"""
        if not args:
            embed = discord.Embed(description="✖️ Usage: `!ban <user> [reason]`", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        parts = args.split(maxsplit=1)
        user_input = parts[0]
        reason = parts[1] if len(parts) > 1 else None

        member = await self.resolve_member(ctx, user_input)

        if not member:
            # Try to ban by ID even if not in server
            user = await self.resolve_user(user_input)
            if user:
                try:
                    await ctx.guild.ban(user, reason=f"{reason or 'No reason'} | By: {ctx.author}")
                    embed = discord.Embed(description=f"➕ Banned **{user.name}** (`{user.id}`)", color=EMBED_COLOR)
                    if reason:
                        embed.description += f"\n› Reason: `{reason}`"
                    return await ctx.send(embed=embed)
                except discord.Forbidden:
                    embed = discord.Embed(description="✖️ Missing permissions to ban", color=EMBED_COLOR)
                    return await ctx.send(embed=embed)

            embed = discord.Embed(description=f"✖️ User not found: `{user_input}`", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        # Can't ban yourself
        if member.id == ctx.author.id:
            embed = discord.Embed(description="✖️ Cannot ban yourself", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        # Can't ban the bot
        if member.id == self.bot.user.id:
            embed = discord.Embed(description="✖️ Cannot ban me", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        # Can't ban server owner
        if member.id == ctx.guild.owner_id:
            embed = discord.Embed(description="✖️ Cannot ban the server owner", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        # Check if bot's role is high enough
        bot_member = ctx.guild.me
        if member.top_role >= bot_member.top_role:
            embed = discord.Embed(description="✖️ My role is not high enough to ban this user", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        # Check if command user can ban this person (skip for owner)
        if ctx.author.id != ctx.guild.owner_id and member.top_role >= ctx.author.top_role:
            embed = discord.Embed(description="✖️ You cannot ban someone with equal or higher role", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        settings = await self.get_settings(ctx.guild.id)
        if settings['dm_on_action']:
            await self.dm_user(member, "banned", reason, guild_name=ctx.guild.name)

        try:
            await member.ban(reason=f"{reason or 'No reason'} | By: {ctx.author}")
            embed = discord.Embed(description=f"➕ Banned {member.mention}", color=EMBED_COLOR)
            if reason:
                embed.description += f"\n› Reason: `{reason}`"
            await ctx.send(embed=embed)
            await self.log_mod_action(ctx.guild, 'ban', ctx.author, member, reason)
        except discord.Forbidden:
            embed = discord.Embed(description="✖️ Cannot ban this user (check bot permissions)", color=EMBED_COLOR)
            await ctx.send(embed=embed)

    @commands.hybrid_command(name='unban')
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban(self, ctx: commands.Context, *, args: str = None):
        """Unban a user (Usage: !unban <user> [reason])"""
        if not args:
            embed = discord.Embed(description="✖️ Usage: `!unban <user_id or username>`", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        parts = args.split(maxsplit=1)
        user_input = parts[0]
        reason = parts[1] if len(parts) > 1 else None

        user = None
        user_id = None

        mention_match = re.match(r'<@!?(\d+)>', user_input)
        if mention_match:
            user_id = int(mention_match.group(1))
        elif user_input.isdigit():
            user_id = int(user_input)

        try:
            if user_id:
                user = await self.bot.fetch_user(user_id)
                await ctx.guild.unban(user, reason=f"{reason or 'No reason'} | By: {ctx.author}")
            else:
                bans = [entry async for entry in ctx.guild.bans()]
                user_input_lower = user_input.lower().lstrip('@')

                for ban_entry in bans:
                    if ban_entry.user.name.lower() == user_input_lower:
                        user = ban_entry.user
                        break

                if not user:
                    for ban_entry in bans:
                        if user_input_lower in ban_entry.user.name.lower():
                            user = ban_entry.user
                            break

                if not user:
                    embed = discord.Embed(description=f"✖️ No banned user found: `{user_input}`", color=EMBED_COLOR)
                    return await ctx.send(embed=embed)

                await ctx.guild.unban(user, reason=f"{reason or 'No reason'} | By: {ctx.author}")

            embed = discord.Embed(description=f"➕ Unbanned **{user.name}** (`{user.id}`)", color=EMBED_COLOR)
            await ctx.send(embed=embed)
            await self.log_mod_action(ctx.guild, 'unban', ctx.author, user, reason)

        except discord.NotFound:
            embed = discord.Embed(description="✖️ User not found or not banned", color=EMBED_COLOR)
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = discord.Embed(description="✖️ Missing permissions to unban", color=EMBED_COLOR)
            await ctx.send(embed=embed)

    @commands.hybrid_command(name='bans', aliases=['banlist', 'banned'])
    @commands.has_permissions(ban_members=True)
    async def bans(self, ctx: commands.Context, page: int = 1):
        """List all banned users"""
        try:
            bans = [entry async for entry in ctx.guild.bans()]

            if not bans:
                embed = discord.Embed(description="➕ No banned users", color=EMBED_COLOR)
                return await ctx.send(embed=embed)

            per_page = 10
            total_pages = (len(bans) + per_page - 1) // per_page
            page = max(1, min(page, total_pages))
            start = (page - 1) * per_page
            end = start + per_page

            ban_list = []
            for entry in bans[start:end]:
                user = entry.user
                reason = entry.reason or "No reason"
                if len(reason) > 30:
                    reason = reason[:27] + "..."
                ban_list.append(f"➖ **{user.name}** (`{user.id}`)\n   {reason}")

            embed = discord.Embed(color=EMBED_COLOR)
            embed.description = f"**Banned Users** ({len(bans)} total)\n\n" + "\n".join(ban_list)
            embed.set_footer(text=f"Page {page}/{total_pages} ➖ Use !bans <page>")
            await ctx.send(embed=embed)

        except discord.Forbidden:
            embed = discord.Embed(description="✖️ Missing permissions to view bans", color=EMBED_COLOR)
            await ctx.send(embed=embed)

    @commands.hybrid_command(name='massban')
    @commands.has_permissions(administrator=True)
    @commands.bot_has_permissions(ban_members=True)
    async def massban(self, ctx: commands.Context, *, user_ids: str):
        """Ban multiple users by ID (comma separated)"""
        ids = [int(i.strip()) for i in user_ids.split(',') if i.strip().isdigit()]

        if not ids:
            embed = discord.Embed(description="✖️ Provide user IDs separated by commas", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        if len(ids) > 50:
            embed = discord.Embed(description="✖️ Maximum 50 users per mass ban", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        banned = 0
        for user_id in ids:
            try:
                await ctx.guild.ban(discord.Object(id=user_id), reason=f"Mass ban | By: {ctx.author}")
                banned += 1
            except:
                pass

        embed = discord.Embed(description=f"➕ Banned `{banned}/{len(ids)}` users", color=EMBED_COLOR)
        await ctx.send(embed=embed)

    # ==================== KICK COMMAND ====================

    @commands.hybrid_command(name='kick')
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick(self, ctx: commands.Context, *, args: str = None):
        """Kick a member (Usage: !kick <user> [reason])"""
        if not args:
            embed = discord.Embed(description="✖️ Usage: `!kick <user> [reason]`", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        parts = args.split(maxsplit=1)
        user_input = parts[0]
        reason = parts[1] if len(parts) > 1 else None

        member = await self.resolve_member(ctx, user_input)

        if not member:
            embed = discord.Embed(description=f"✖️ Member not found: `{user_input}`", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        # Can't kick yourself
        if member.id == ctx.author.id:
            embed = discord.Embed(description="✖️ Cannot kick yourself", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        # Can't kick the bot
        if member.id == self.bot.user.id:
            embed = discord.Embed(description="✖️ Cannot kick me", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        # Can't kick server owner
        if member.id == ctx.guild.owner_id:
            embed = discord.Embed(description="✖️ Cannot kick the server owner", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        # Check if bot's role is high enough
        bot_member = ctx.guild.me
        if member.top_role >= bot_member.top_role:
            embed = discord.Embed(description="✖️ My role is not high enough to kick this user", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        # Check if command user can kick this person (skip for owner)
        if ctx.author.id != ctx.guild.owner_id and member.top_role >= ctx.author.top_role:
            embed = discord.Embed(description="✖️ You cannot kick someone with equal or higher role", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        settings = await self.get_settings(ctx.guild.id)
        if settings['dm_on_action']:
            await self.dm_user(member, "kicked", reason, guild_name=ctx.guild.name)

        try:
            await member.kick(reason=f"{reason or 'No reason'} | By: {ctx.author}")
            embed = discord.Embed(description=f"➕ Kicked {member.mention}", color=EMBED_COLOR)
            if reason:
                embed.description += f"\n› Reason: `{reason}`"
            await ctx.send(embed=embed)
            await self.log_mod_action(ctx.guild, 'kick', ctx.author, member, reason)
        except discord.Forbidden:
            embed = discord.Embed(description="✖️ Cannot kick this user (check bot permissions)", color=EMBED_COLOR)
            await ctx.send(embed=embed)

    # ==================== MUTE/TIMEOUT COMMANDS ====================

    @commands.hybrid_command(name='mute', aliases=['timeout'])
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def mute(self, ctx: commands.Context, *, args: str = None):
        """Timeout a member (Usage: !mute <user> [duration] [reason])"""
        if not args:
            embed = discord.Embed(description="✖️ Usage: `!mute <user> [duration] [reason]`\n› Example: `!mute @user 1h spamming`", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        parts = args.split()
        user_input = parts[0]
        duration_str = "1h"
        reason = None

        if len(parts) > 1:
            if self.is_duration(parts[1]):
                duration_str = parts[1]
                if len(parts) > 2:
                    reason = " ".join(parts[2:])
            else:
                reason = " ".join(parts[1:])

        member = await self.resolve_member(ctx, user_input)

        if not member:
            embed = discord.Embed(description=f"✖️ Member not found: `{user_input}`", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        # Can't mute yourself
        if member.id == ctx.author.id:
            embed = discord.Embed(description="✖️ Cannot mute yourself", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        # Can't mute the bot
        if member.id == self.bot.user.id:
            embed = discord.Embed(description="✖️ Cannot mute me", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        # Can't mute server owner
        if member.id == ctx.guild.owner_id:
            embed = discord.Embed(description="✖️ Cannot mute the server owner", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        # Check if bot's role is high enough
        bot_member = ctx.guild.me
        if member.top_role >= bot_member.top_role:
            embed = discord.Embed(description="✖️ My role is not high enough to mute this user", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        # Check if command user can mute this person (skip for owner)
        if ctx.author.id != ctx.guild.owner_id and member.top_role >= ctx.author.top_role:
            embed = discord.Embed(description="✖️ You cannot mute someone with equal or higher role", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        seconds, duration_display = self.parse_duration(duration_str)
        settings = await self.get_settings(ctx.guild.id)

        if settings['dm_on_action']:
            await self.dm_user(member, "muted", reason, duration=duration_display, guild_name=ctx.guild.name)

        try:
            await member.timeout(timedelta(seconds=seconds), reason=f"{reason or 'No reason'} | By: {ctx.author}")
            embed = discord.Embed(description=f"➕ Muted {member.mention} for `{duration_display}`", color=EMBED_COLOR)
            if reason:
                embed.description += f"\n› Reason: `{reason}`"
            await ctx.send(embed=embed)
            await self.log_mod_action(ctx.guild, 'mute', ctx.author, member, reason, duration_display)
        except discord.Forbidden:
            embed = discord.Embed(description="✖️ Cannot mute this user (check bot permissions)", color=EMBED_COLOR)
            await ctx.send(embed=embed)

    @commands.hybrid_command(name='unmute', aliases=['untimeout'])
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def unmute(self, ctx: commands.Context, *, args: str = None):
        """Remove timeout (Usage: !unmute <user> [reason])"""
        if not args:
            embed = discord.Embed(description="✖️ Usage: `!unmute <user> [reason]`", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        parts = args.split(maxsplit=1)
        user_input = parts[0]
        reason = parts[1] if len(parts) > 1 else None

        member = await self.resolve_member(ctx, user_input)

        if not member:
            embed = discord.Embed(description=f"✖️ Member not found: `{user_input}`", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        # Check if bot's role is high enough
        bot_member = ctx.guild.me
        if member.top_role >= bot_member.top_role:
            embed = discord.Embed(description="✖️ My role is not high enough to unmute this user", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        try:
            await member.timeout(None, reason=f"{reason or 'No reason'} | By: {ctx.author}")
            embed = discord.Embed(description=f"➕ Unmuted {member.mention}", color=EMBED_COLOR)
            await ctx.send(embed=embed)
            await self.log_mod_action(ctx.guild, 'unmute', ctx.author, member, reason)
        except discord.Forbidden:
            embed = discord.Embed(description="✖️ Cannot unmute this user (check bot permissions)", color=EMBED_COLOR)
            await ctx.send(embed=embed)

    # ==================== NICK COMMAND ====================

    @commands.hybrid_command(name='nick', aliases=['nickname', 'setnick'])
    @commands.has_permissions(manage_nicknames=True)
    @commands.bot_has_permissions(manage_nicknames=True)
    async def nick(self, ctx: commands.Context, *, args: str = None):
        """Change nickname (Usage: !nick <user> [new_nickname])"""
        if not args:
            embed = discord.Embed(description="✖️ Usage: `!nick <user> [new_nickname]`", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        parts = args.split(maxsplit=1)
        user_input = parts[0]
        nickname = parts[1] if len(parts) > 1 else None

        member = await self.resolve_member(ctx, user_input)

        if not member:
            embed = discord.Embed(description=f"✖️ Member not found: `{user_input}`", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        # Check if bot's role is high enough
        bot_member = ctx.guild.me
        if member.top_role >= bot_member.top_role and member.id != self.bot.user.id:
            embed = discord.Embed(description="✖️ My role is not high enough to change this user's nickname", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        # Check if command user can change this person's nick (skip for owner)
        if ctx.author.id != ctx.guild.owner_id and member.top_role >= ctx.author.top_role and member.id != ctx.author.id:
            embed = discord.Embed(description="✖️ You cannot change nickname of someone with equal or higher role", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        try:
            await member.edit(nick=nickname)
            if nickname:
                embed = discord.Embed(description=f"➕ Changed {member.mention}'s nickname to `{nickname}`", color=EMBED_COLOR)
            else:
                embed = discord.Embed(description=f"➕ Reset {member.mention}'s nickname", color=EMBED_COLOR)
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = discord.Embed(description="✖️ Missing permissions to change nickname", color=EMBED_COLOR)
            await ctx.send(embed=embed)

    # ==================== WARN COMMANDS ====================

    @commands.hybrid_command(name='warn')
    @commands.has_permissions(moderate_members=True)
    async def warn(self, ctx: commands.Context, *, args: str = None):
        """Warn a member (Usage: !warn <user> [reason])"""
        if not args:
            embed = discord.Embed(description="✖️ Usage: `!warn <user> [reason]`", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        parts = args.split(maxsplit=1)
        user_input = parts[0]
        reason = parts[1] if len(parts) > 1 else "No reason"

        member = await self.resolve_member(ctx, user_input)

        if not member:
            embed = discord.Embed(description=f"✖️ Member not found: `{user_input}`", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        if member.id == ctx.author.id:
            embed = discord.Embed(description="✖️ Cannot warn yourself", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        if member.bot:
            embed = discord.Embed(description="✖️ Cannot warn bots", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        settings = await self.get_settings(ctx.guild.id)

        warning = {
            'reason': reason,
            'moderator': ctx.author.id,
            'time': datetime.utcnow().isoformat()
        }
        self.warnings[ctx.guild.id][member.id].append(warning)
        await self.add_warning_to_db(ctx.guild.id, member.id, ctx.author.id, reason)

        warn_count = len(self.warnings[ctx.guild.id][member.id])

        embed = discord.Embed(
            description=f"➕ Warned {member.mention} `{warn_count}/{settings['warn_threshold']}`\n› Reason: `{reason}`",
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
                await member.timeout(duration, reason="Warning threshold reached")
                embed = discord.Embed(description=f"➕ Muted {member.mention} for reaching warn threshold", color=EMBED_COLOR)
                await ctx.send(embed=embed)
            elif action == 'kick':
                await member.kick(reason="Warning threshold reached")
                embed = discord.Embed(description=f"➕ Kicked {member.mention} for reaching warn threshold", color=EMBED_COLOR)
                await ctx.send(embed=embed)
            elif action == 'ban':
                await member.ban(reason="Warning threshold reached")
                embed = discord.Embed(description=f"➕ Banned {member.mention} for reaching warn threshold", color=EMBED_COLOR)
                await ctx.send(embed=embed)
            self.warnings[ctx.guild.id][member.id] = []

    @commands.hybrid_command(name='warnings', aliases=['warns'])
    @commands.has_permissions(moderate_members=True)
    async def warnings_cmd(self, ctx: commands.Context, *, user_input: str = None):
        """View warnings (Usage: !warnings <user>)"""
        if not user_input:
            embed = discord.Embed(description="✖️ Usage: `!warnings <user>`", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        member = await self.resolve_member(ctx, user_input)

        if not member:
            embed = discord.Embed(description=f"✖️ Member not found: `{user_input}`", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

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
    async def clearwarns(self, ctx: commands.Context, *, user_input: str = None):
        """Clear warnings (Usage: !clearwarns <user>)"""
        if not user_input:
            embed = discord.Embed(description="✖️ Usage: `!clearwarns <user>`", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        member = await self.resolve_member(ctx, user_input)

        if not member:
            embed = discord.Embed(description=f"✖️ Member not found: `{user_input}`", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        count = len(self.warnings[ctx.guild.id].get(member.id, []))
        self.warnings[ctx.guild.id][member.id] = []

        if self.db:
            try:
                await self.db.clear_warnings(ctx.guild.id, member.id)
            except:
                pass

        embed = discord.Embed(description=f"➕ Cleared `{count}` warnings for {member.mention}", color=EMBED_COLOR)
        await ctx.send(embed=embed)

    # ==================== PURGE COMMANDS ====================

    @commands.command(name='purge', aliases=['clear', 'prune'])
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def purge(self, ctx: commands.Context, target: str = None, amount: int = None):
        """Delete messages (Usage: !purge [amount] or !purge <user> [amount])"""
        member = None

        if target is None:
            amount = 10
        elif target.isdigit():
            amount = int(target)
        else:
            member = await self.resolve_member(ctx, target)
            if member is None:
                embed = discord.Embed(description=f"✖️ User not found: `{target}`", color=EMBED_COLOR)
                return await ctx.send(embed=embed)
            if amount is None:
                amount = 10

        if amount < 1 or amount > 1000:
            embed = discord.Embed(description="✖️ Amount must be 1-1000", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        try:
            await ctx.message.delete()

            if member:
                deleted_messages = []
                async for message in ctx.channel.history(limit=500):
                    if message.author.id == member.id:
                        deleted_messages.append(message)
                        if len(deleted_messages) >= amount:
                            break

                if deleted_messages:
                    await ctx.channel.delete_messages(deleted_messages)
                embed = discord.Embed(description=f"➕ Deleted `{len(deleted_messages)}` messages from {member.mention}", color=EMBED_COLOR)
            else:
                deleted = await ctx.channel.purge(limit=amount)
                embed = discord.Embed(description=f"➕ Deleted `{len(deleted)}` messages", color=EMBED_COLOR)

            msg = await ctx.send(embed=embed)
            await asyncio.sleep(3)
            await msg.delete()
        except discord.Forbidden:
            embed = discord.Embed(description="✖️ Missing permissions", color=EMBED_COLOR)
            await ctx.send(embed=embed)
        except discord.HTTPException:
            embed = discord.Embed(description="✖️ Failed to delete (messages may be too old)", color=EMBED_COLOR)
            await ctx.send(embed=embed)

    @commands.hybrid_command(name='purgeuser')
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def purgeuser(self, ctx: commands.Context, *, args: str = None):
        """Delete user's messages (Usage: !purgeuser <user> [amount])"""
        if not args:
            embed = discord.Embed(description="✖️ Usage: `!purgeuser <user> [amount]`", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        parts = args.split()
        user_input = parts[0]
        amount = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 100

        member = await self.resolve_member(ctx, user_input)

        if not member:
            embed = discord.Embed(description=f"✖️ Member not found: `{user_input}`", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        if amount < 1 or amount > 1000:
            embed = discord.Embed(description="✖️ Amount must be 1-1000", color=EMBED_COLOR)
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

            embed = discord.Embed(description=f"➕ Deleted `{len(deleted_messages)}` messages from {member.mention}", color=EMBED_COLOR)
            msg = await ctx.send(embed=embed)
            await asyncio.sleep(3)
            await msg.delete()
        except discord.Forbidden:
            embed = discord.Embed(description="✖️ Missing permissions", color=EMBED_COLOR)
            await ctx.send(embed=embed)
        except discord.HTTPException:
            embed = discord.Embed(description="✖️ Failed to delete (messages may be too old)", color=EMBED_COLOR)
            await ctx.send(embed=embed)

    # ==================== SLOWMODE & LOG ====================

    @commands.hybrid_command(name='slowmode')
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def slowmode(self, ctx: commands.Context, seconds: int = 0):
        """Set slowmode (0 to disable)"""
        if seconds < 0 or seconds > 21600:
            embed = discord.Embed(description="✖️ Slowmode must be 0-21600 seconds", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        await ctx.channel.edit(slowmode_delay=seconds)

        if seconds == 0:
            embed = discord.Embed(description="➕ Disabled slowmode", color=EMBED_COLOR)
        else:
            embed = discord.Embed(description=f"➕ Set slowmode to `{seconds}s`", color=EMBED_COLOR)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='modlog')
    @commands.has_permissions(administrator=True)
    async def modlog(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set moderation log channel"""
        settings = await self.get_settings(ctx.guild.id)
        settings['log_channel'] = channel.id
        await self.save_settings(ctx.guild.id)
        embed = discord.Embed(description=f"➕ Set mod log to {channel.mention}", color=EMBED_COLOR)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Moderation(bot))
