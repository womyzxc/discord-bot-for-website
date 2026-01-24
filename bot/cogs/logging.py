"""
Security Logging Cog
====================
Comprehensive logging for security events:
- Moderation actions
- Permission changes
- Member events
- Message events
- Security alerts
"""

import discord
from discord.ext import commands
from datetime import datetime
from collections import defaultdict
import logging
from typing import Dict, Optional

logger = logging.getLogger('Offcialx.Logging')

# Minimal embed color
EMBED_COLOR = 0x2b2d31


class SecurityLogging(commands.Cog):
    """Security Logging System"""

    def __init__(self, bot):
        self.bot = bot

        # Guild settings
        self.guild_settings: Dict[int, Dict] = {}

    async def get_settings(self, guild_id: int) -> Dict:
        """Get guild settings"""
        if guild_id not in self.guild_settings:
            self.guild_settings[guild_id] = {
                'enabled': True,
                'log_channel': None,
                'security_channel': None,

                # Event toggles
                'log_bans': True,
                'log_kicks': True,
                'log_mutes': True,
                'log_role_changes': True,
                'log_channel_changes': True,
                'log_permission_changes': True,
                'log_message_deletes': True,
                'log_message_edits': False,
                'log_joins': True,
                'log_leaves': True,
                'log_nickname_changes': True,
                'log_voice_state': False,

                # Security events (always to security channel)
                'log_security_events': True,
            }
        return self.guild_settings[guild_id]

    async def log_event(self, guild: discord.Guild, embed: discord.Embed,
                       security: bool = False):
        """Send a log message"""
        settings = await self.get_settings(guild.id)

        if not settings['enabled']:
            return

        channel_id = settings['security_channel'] if security else settings['log_channel']
        if not channel_id:
            return

        channel = guild.get_channel(channel_id)
        if not channel:
            return

        try:
            await channel.send(embed=embed)
        except:
            pass

    # ==================== EVENT LISTENERS ====================

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        """Log member bans"""
        settings = await self.get_settings(guild.id)
        if not settings['log_bans']:
            return

        desc = f"**Member Banned**\n\n› User: {user.mention} ({user})\n› ID: `{user.id}`"

        # Try to get moderator from audit log
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
            if entry.target.id == user.id:
                desc += f"\n› By: {entry.user.mention}"
                if entry.reason:
                    desc += f"\n› Reason: {entry.reason}"
                break

        embed = discord.Embed(description=desc, color=EMBED_COLOR)
        embed.set_thumbnail(url=user.display_avatar.url if user.avatar else None)
        await self.log_event(guild, embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        """Log member unbans"""
        settings = await self.get_settings(guild.id)
        if not settings['log_bans']:
            return

        desc = f"**Member Unbanned**\n\n› User: {user.mention} ({user})\n› ID: `{user.id}`"

        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.unban):
            if entry.target.id == user.id:
                desc += f"\n› By: {entry.user.mention}"
                break

        embed = discord.Embed(description=desc, color=EMBED_COLOR)
        await self.log_event(guild, embed)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Log member joins"""
        settings = await self.get_settings(member.guild.id)
        if not settings['log_joins']:
            return

        # Account age
        account_age = datetime.utcnow() - member.created_at.replace(tzinfo=None)
        age_str = f"{account_age.days}d {account_age.seconds // 3600}h"

        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = (
            f"**Member Joined**\n\n"
            f"› User: {member.mention} ({member})\n"
            f"› ID: `{member.id}`\n"
            f"› Account Age: `{age_str}`\n"
            f"› Member #: `{member.guild.member_count or 0}`"
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await self.log_event(member.guild, embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Log member leaves/kicks"""
        settings = await self.get_settings(member.guild.id)
        if not settings['log_leaves'] and not settings['log_kicks']:
            return

        title = "Member Left"
        extra = ""

        # Check if it was a kick
        async for entry in member.guild.audit_logs(limit=1, action=discord.AuditLogAction.kick):
            if entry.target.id == member.id and (datetime.utcnow() - entry.created_at.replace(tzinfo=None)).seconds < 5:
                title = "Member Kicked"
                extra = f"\n› By: {entry.user.mention}"
                if entry.reason:
                    extra += f"\n› Reason: {entry.reason}"
                break

        # Roles
        roles = [r.mention for r in member.roles if r != member.guild.default_role]
        roles_str = f"\n› Roles: {' '.join(roles[:10])}" if roles else ""

        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = (
            f"**{title}**\n\n"
            f"› User: {member.mention} ({member})\n"
            f"› ID: `{member.id}`{extra}{roles_str}"
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        await self.log_event(member.guild, embed)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """Log member updates (roles, nickname)"""
        settings = await self.get_settings(after.guild.id)

        # Role changes
        if settings['log_role_changes'] and before.roles != after.roles:
            added_roles = [r for r in after.roles if r not in before.roles]
            removed_roles = [r for r in before.roles if r not in after.roles]

            if added_roles or removed_roles:
                desc = f"**Member Roles Updated**\n\n› User: {after.mention} ({after})"

                if added_roles:
                    desc += f"\n› Added: {' '.join(r.mention for r in added_roles)}"
                if removed_roles:
                    desc += f"\n› Removed: {' '.join(r.mention for r in removed_roles)}"

                embed = discord.Embed(description=desc, color=EMBED_COLOR)
                embed.set_thumbnail(url=after.display_avatar.url)
                await self.log_event(after.guild, embed)

        # Nickname changes
        if settings['log_nickname_changes'] and before.nick != after.nick:
            embed = discord.Embed(color=EMBED_COLOR)
            embed.description = (
                f"**Nickname Changed**\n\n"
                f"› User: {after.mention} ({after})\n"
                f"› Before: `{before.nick or 'None'}`\n"
                f"› After: `{after.nick or 'None'}`"
            )
            await self.log_event(after.guild, embed)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        """Log channel creation"""
        settings = await self.get_settings(channel.guild.id)
        if not settings['log_channel_changes']:
            return

        channel_type = "Text" if isinstance(channel, discord.TextChannel) else "Voice" if isinstance(channel, discord.VoiceChannel) else "Category"
        desc = f"**Channel Created**\n\n› Channel: {channel.mention if hasattr(channel, 'mention') else channel.name}\n› Type: `{channel_type}`\n› ID: `{channel.id}`"

        async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_create):
            if entry.target.id == channel.id:
                desc += f"\n› By: {entry.user.mention}"
                break

        embed = discord.Embed(description=desc, color=EMBED_COLOR)
        await self.log_event(channel.guild, embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        """Log channel deletion"""
        settings = await self.get_settings(channel.guild.id)
        if not settings['log_channel_changes']:
            return

        channel_type = "Text" if isinstance(channel, discord.TextChannel) else "Voice" if isinstance(channel, discord.VoiceChannel) else "Category"
        desc = f"**Channel Deleted**\n\n› Channel: #{channel.name}\n› Type: `{channel_type}`\n› ID: `{channel.id}`"

        async for entry in channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
            if entry.target.id == channel.id:
                desc += f"\n› By: {entry.user.mention}"
                break

        embed = discord.Embed(description=desc, color=EMBED_COLOR)
        await self.log_event(channel.guild, embed, security=True)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        """Log role creation"""
        settings = await self.get_settings(role.guild.id)
        if not settings['log_role_changes']:
            return

        desc = f"**Role Created**\n\n› Role: {role.mention}\n› ID: `{role.id}`\n› Color: `{role.color}`"

        async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_create):
            if entry.target.id == role.id:
                desc += f"\n› By: {entry.user.mention}"
                break

        embed = discord.Embed(description=desc, color=EMBED_COLOR)
        await self.log_event(role.guild, embed)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        """Log role deletion"""
        settings = await self.get_settings(role.guild.id)
        if not settings['log_role_changes']:
            return

        desc = f"**Role Deleted**\n\n› Role: @{role.name}\n› ID: `{role.id}`\n› Color: `{role.color}`"

        async for entry in role.guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
            if entry.target.id == role.id:
                desc += f"\n› By: {entry.user.mention}"
                break

        embed = discord.Embed(description=desc, color=EMBED_COLOR)
        await self.log_event(role.guild, embed, security=True)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        """Log message deletions"""
        if not message.guild or message.author.bot:
            return

        settings = await self.get_settings(message.guild.id)
        if not settings['log_message_deletes']:
            return

        content = message.content[:500] if message.content else "No content"
        attachments_str = f"\n› Attachments: `{len(message.attachments)}`" if message.attachments else ""

        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = (
            f"**Message Deleted**\n\n"
            f"› Author: {message.author.mention} ({message.author})\n"
            f"› Channel: {message.channel.mention}{attachments_str}\n\n"
            f"**Content**\n{content}"
        )
        embed.set_thumbnail(url=message.author.display_avatar.url)
        await self.log_event(message.guild, embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """Log message edits"""
        if not after.guild or after.author.bot:
            return

        if before.content == after.content:
            return

        settings = await self.get_settings(after.guild.id)
        if not settings['log_message_edits']:
            return

        before_content = before.content[:300] if len(before.content) > 300 else before.content
        after_content = after.content[:300] if len(after.content) > 300 else after.content

        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = (
            f"**Message Edited**\n\n"
            f"› Author: {after.author.mention} ({after.author})\n"
            f"› Channel: {after.channel.mention}\n"
            f"› [Jump]({after.jump_url})\n\n"
            f"**Before**\n{before_content or 'Empty'}\n\n"
            f"**After**\n{after_content or 'Empty'}"
        )
        await self.log_event(after.guild, embed)

    # ==================== COMMANDS ====================

    @commands.group(name='logs', invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def logs(self, ctx):
        """Logging configuration commands"""
        settings = await self.get_settings(ctx.guild.id)

        log_ch = ctx.guild.get_channel(settings['log_channel']) if settings['log_channel'] else None
        sec_ch = ctx.guild.get_channel(settings['security_channel']) if settings['security_channel'] else None

        events = [
            f"› Bans: `{'on' if settings['log_bans'] else 'off'}`",
            f"› Kicks: `{'on' if settings['log_kicks'] else 'off'}`",
            f"› Roles: `{'on' if settings['log_role_changes'] else 'off'}`",
            f"› Channels: `{'on' if settings['log_channel_changes'] else 'off'}`",
            f"› Messages: `{'on' if settings['log_message_deletes'] else 'off'}`",
            f"› Joins: `{'on' if settings['log_joins'] else 'off'}`",
            f"› Leaves: `{'on' if settings['log_leaves'] else 'off'}`",
        ]

        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = (
            f"**Logging Configuration**\n\n"
            f"› Status: `{'enabled' if settings['enabled'] else 'disabled'}`\n"
            f"› Log Channel: {log_ch.mention if log_ch else '`Not set`'}\n"
            f"› Security Channel: {sec_ch.mention if sec_ch else '`Not set`'}\n\n"
            f"**Events**\n" + "\n".join(events)
        )

        await ctx.send(embed=embed)

    @logs.command(name='channel')
    @commands.has_permissions(administrator=True)
    async def logs_channel(self, ctx, channel: discord.TextChannel = None):
        """Set the log channel"""
        settings = await self.get_settings(ctx.guild.id)
        settings['log_channel'] = channel.id if channel else None

        if channel:
            embed = discord.Embed(description=f"➕ Log channel set to {channel.mention}", color=EMBED_COLOR)
        else:
            embed = discord.Embed(description="➕ Log channel cleared", color=EMBED_COLOR)
        await ctx.send(embed=embed)

    @logs.command(name='security')
    @commands.has_permissions(administrator=True)
    async def logs_security(self, ctx, channel: discord.TextChannel = None):
        """Set the security log channel"""
        settings = await self.get_settings(ctx.guild.id)
        settings['security_channel'] = channel.id if channel else None

        if channel:
            embed = discord.Embed(description=f"➕ Security log channel set to {channel.mention}", color=EMBED_COLOR)
        else:
            embed = discord.Embed(description="➕ Security log channel cleared", color=EMBED_COLOR)
        await ctx.send(embed=embed)

    @logs.command(name='enable')
    @commands.has_permissions(administrator=True)
    async def logs_enable(self, ctx):
        """Enable logging"""
        settings = await self.get_settings(ctx.guild.id)
        settings['enabled'] = True
        embed = discord.Embed(description="➕ Logging enabled", color=EMBED_COLOR)
        await ctx.send(embed=embed)

    @logs.command(name='disable')
    @commands.has_permissions(administrator=True)
    async def logs_disable(self, ctx):
        """Disable logging"""
        settings = await self.get_settings(ctx.guild.id)
        settings['enabled'] = False
        embed = discord.Embed(description="➖ Logging disabled", color=EMBED_COLOR)
        await ctx.send(embed=embed)

    @logs.command(name='toggle')
    @commands.has_permissions(administrator=True)
    async def logs_toggle(self, ctx, event: str):
        """Toggle a specific log event"""
        event_map = {
            'bans': 'log_bans',
            'kicks': 'log_kicks',
            'mutes': 'log_mutes',
            'roles': 'log_role_changes',
            'channels': 'log_channel_changes',
            'messages': 'log_message_deletes',
            'edits': 'log_message_edits',
            'joins': 'log_joins',
            'leaves': 'log_leaves',
            'nicknames': 'log_nickname_changes',
        }

        if event.lower() not in event_map:
            embed = discord.Embed(description=f"✖️ Unknown event. Choose from: `{', '.join(event_map.keys())}`", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        settings = await self.get_settings(ctx.guild.id)
        key = event_map[event.lower()]
        settings[key] = not settings[key]

        status = "enabled" if settings[key] else "disabled"
        embed = discord.Embed(description=f"➕ {event.title()} logging is now `{status}`", color=EMBED_COLOR)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(SecurityLogging(bot))
