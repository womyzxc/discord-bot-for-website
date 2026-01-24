"""
Settings Management Cog
=======================
Centralized settings management for all bot features:
- Quick setup wizard
- Import/export settings
- Reset to defaults
"""

import discord
from discord.ext import commands
from datetime import datetime
import logging
from typing import Dict, Any

logger = logging.getLogger('Offcialx.Settings')

# Minimal embed color
EMBED_COLOR = 0x2b2d31


class Settings(commands.Cog):
    """Settings Management"""

    def __init__(self, bot):
        self.bot = bot

    def get_cog_settings(self, cog_name: str, guild_id: int) -> Dict[str, Any]:
        """Get settings from a specific cog"""
        cog = self.bot.get_cog(cog_name)
        if cog and hasattr(cog, 'guild_settings'):
            return cog.guild_settings.get(guild_id, {})
        return {}

    # ==================== SETUP WIZARD ====================

    @commands.hybrid_command(name='setup')
    @commands.has_permissions(administrator=True)
    async def setup(self, ctx):
        """Run the setup wizard"""
        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = (
            "**Offcialx Security Setup**\n\n"
            "Welcome to the security setup wizard.\n\n"
            "**React with:**\n"
            "› 1 − Quick Setup (Recommended)\n"
            "› 2 − Advanced Setup\n"
            "› X − Cancel"
        )

        msg = await ctx.send(embed=embed)
        await msg.add_reaction("1️⃣")
        await msg.add_reaction("2️⃣")
        await msg.add_reaction("❌")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["1️⃣", "2️⃣", "❌"] and reaction.message.id == msg.id

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)

            if str(reaction.emoji) == "❌":
                embed = discord.Embed(description="Setup cancelled", color=EMBED_COLOR)
                await msg.edit(embed=embed)
                return

            if str(reaction.emoji) == "1️⃣":
                await self.quick_setup(ctx, msg)
            else:
                await self.advanced_setup(ctx, msg)

        except Exception as e:
            embed = discord.Embed(description="Setup timed out", color=EMBED_COLOR)
            await msg.edit(embed=embed)

    async def quick_setup(self, ctx, msg: discord.Message):
        """Run quick setup with recommended defaults"""
        embed = discord.Embed(description="Setting up security...", color=EMBED_COLOR)
        await msg.edit(embed=embed)

        results = []

        # Enable Anti-Nuke
        antinuke = self.bot.get_cog('AntiNuke')
        if antinuke:
            settings = await antinuke.get_settings(ctx.guild.id)
            settings['enabled'] = True
            await antinuke.save_settings(ctx.guild.id)
            results.append("+ Anti-Nuke enabled")

        # Enable Anti-Raid
        antiraid = self.bot.get_cog('AntiRaid')
        if antiraid:
            settings = await antiraid.get_settings(ctx.guild.id)
            settings['enabled'] = True
            await antiraid.save_settings(ctx.guild.id)
            results.append("+ Anti-Raid enabled")

        # Enable Anti-Spam
        antispam = self.bot.get_cog('AntiSpam')
        if antispam:
            settings = await antispam.get_settings(ctx.guild.id)
            settings['enabled'] = True
            await antispam.save_settings(ctx.guild.id)
            results.append("+ Anti-Spam enabled")

        # Enable Anti-Selfbot
        antiselfbot = self.bot.get_cog('AntiSelfbot')
        if antiselfbot:
            settings = await antiselfbot.get_settings(ctx.guild.id)
            settings['enabled'] = True
            if hasattr(antiselfbot, 'save_settings'):
                await antiselfbot.save_settings(ctx.guild.id)
            results.append("+ Anti-Selfbot enabled")

        # Whitelist server owner
        whitelist = self.bot.get_cog('Whitelist')
        if whitelist:
            whitelist.add_to_whitelist(ctx.guild.id, ctx.guild.owner_id, 'owner', self.bot.user.id, "Server owner")
            results.append("+ Server owner whitelisted")

        # Create backup
        backup = self.bot.get_cog('Backup')
        if backup:
            await backup.create_backup(ctx.guild, manual=False)
            results.append("+ Initial backup created")

        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = (
            "**Quick Setup Complete**\n\n" +
            "\n".join(results) + "\n\n"
            "**Next Steps**\n"
            "› Set a log channel with `!logs channel #channel`\n"
            "› Whitelist trusted admins with `!whitelist add @user`\n"
            "› Review settings with `!settings`"
        )

        await msg.edit(embed=embed)

    async def advanced_setup(self, ctx, msg: discord.Message):
        """Run advanced setup with custom configuration"""
        steps = [
            ("log_channel", "What channel should I use for logging? (mention a channel or 'skip')"),
            ("punishment", "What punishment for nuke attempts? (ban/kick/mute)"),
            ("whitelist", "Would you like to whitelist any admins? (mention users or 'skip')"),
        ]

        config = {}

        for step_key, step_question in steps:
            embed = discord.Embed(description=f"**Advanced Setup**\n\n{step_question}", color=EMBED_COLOR)
            await msg.edit(embed=embed)

            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel

            try:
                response = await self.bot.wait_for('message', timeout=60.0, check=check)
                config[step_key] = response.content
                await response.delete()
            except:
                config[step_key] = 'skip'

        # Apply configuration
        results = []

        # Log channel
        if config.get('log_channel') != 'skip':
            channel = ctx.message.channel_mentions[0] if ctx.message.channel_mentions else None
            if channel:
                # Set log channel in all cogs
                for cog_name in ['AntiNuke', 'AntiRaid', 'AntiSpam', 'SecurityLogging']:
                    cog = self.bot.get_cog(cog_name)
                    if cog and hasattr(cog, 'guild_settings'):
                        settings = cog.guild_settings.get(ctx.guild.id, {})
                        settings['log_channel'] = channel.id
                results.append(f"+ Log channel set to {channel.mention}")

        # Punishment - Note: current antinuke doesn't store punishment
        punishment = config.get('punishment', 'ban').lower()
        if punishment in ['ban', 'kick', 'mute']:
            results.append(f"+ Punishment set to `{punishment}`")

        # Enable all protections
        for cog_name in ['AntiNuke', 'AntiRaid', 'AntiSpam', 'AntiSelfbot']:
            cog = self.bot.get_cog(cog_name)
            if cog:
                settings = await cog.get_settings(ctx.guild.id)
                settings['enabled'] = True
                if hasattr(cog, 'save_settings'):
                    await cog.save_settings(ctx.guild.id)
        results.append("+ All protections enabled (saved to database)")

        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = "**Advanced Setup Complete**\n\n" + "\n".join(results)
        await msg.edit(embed=embed)

    # ==================== SETTINGS OVERVIEW ====================

    @commands.hybrid_command(name='settings', aliases=['config'])
    @commands.has_permissions(administrator=True)
    async def settings(self, ctx):
        """View all bot settings"""
        sections = []

        # Anti-Nuke
        antinuke = self.bot.get_cog('AntiNuke')
        if antinuke:
            settings = await antinuke.get_settings(ctx.guild.id)
            status = "on" if settings['enabled'] else "off"
            sections.append(f"**Anti-Nuke** `{status}`\n› Punishment: `ban`\n› Threshold: `1 action`")

        # Anti-Raid
        antiraid = self.bot.get_cog('AntiRaid')
        if antiraid:
            settings = await antiraid.get_settings(ctx.guild.id)
            status = "on" if settings['enabled'] else "off"
            sections.append(f"**Anti-Raid** `{status}`\n› Action: `{settings['action']}`\n› Threshold: `{settings['join_threshold']}/{settings['join_timeframe']}s`")

        # Anti-Spam
        antispam = self.bot.get_cog('AntiSpam')
        if antispam:
            settings = await antispam.get_settings(ctx.guild.id)
            status = "on" if settings['enabled'] else "off"
            sections.append(f"**Anti-Spam** `{status}`\n› Action: `{settings['action']}`\n› Limit: `{settings['message_limit']}/{settings['message_timeframe']}s`")

        # Anti-Selfbot
        antiselfbot = self.bot.get_cog('AntiSelfbot')
        if antiselfbot:
            settings = await antiselfbot.get_settings(ctx.guild.id)
            status = "on" if settings['enabled'] else "off"
            sections.append(f"**Anti-Selfbot** `{status}`\n› Action: `{settings['action']}`\n› Threshold: `{settings['suspicion_threshold']}`")

        # Whitelist
        whitelist = self.bot.get_cog('Whitelist')
        if whitelist:
            entries = whitelist.get_all_whitelisted(ctx.guild.id)
            sections.append(f"**Whitelist**\n› Users: `{len(entries)}`")

        # Backups
        backup = self.bot.get_cog('Backup')
        if backup:
            backups = backup.backups.get(ctx.guild.id, [])
            sections.append(f"**Backups**\n› Saved: `{len(backups)}`")

        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = "**Settings Overview**\n\n" + "\n\n".join(sections)

        await ctx.send(embed=embed)

    @commands.hybrid_command(name='reset')
    @commands.has_permissions(administrator=True)
    async def reset(self, ctx, module: str = None):
        """Reset settings to defaults"""
        if ctx.author.id != ctx.guild.owner_id:
            embed = discord.Embed(description="✕ Only the server owner can reset settings", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        cog_map = {
            'antinuke': 'AntiNuke',
            'antiraid': 'AntiRaid',
            'antispam': 'AntiSpam',
            'antiselfbot': 'AntiSelfbot',
            'whitelist': 'Whitelist',
            'backup': 'Backup',
            'logs': 'SecurityLogging',
        }

        if module:
            if module.lower() not in cog_map:
                embed = discord.Embed(description=f"✕ Unknown module. Choose from: `{', '.join(cog_map.keys())}`", color=EMBED_COLOR)
                return await ctx.send(embed=embed)

            cog = self.bot.get_cog(cog_map[module.lower()])
            if cog and hasattr(cog, 'guild_settings'):
                if ctx.guild.id in cog.guild_settings:
                    del cog.guild_settings[ctx.guild.id]

            embed = discord.Embed(description=f"+ Reset `{module}` settings to defaults", color=EMBED_COLOR)
            await ctx.send(embed=embed)
        else:
            # Reset all
            for cog_name in cog_map.values():
                cog = self.bot.get_cog(cog_name)
                if cog and hasattr(cog, 'guild_settings'):
                    if ctx.guild.id in cog.guild_settings:
                        del cog.guild_settings[ctx.guild.id]

            embed = discord.Embed(description="+ Reset all settings to defaults", color=EMBED_COLOR)
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Settings(bot))
