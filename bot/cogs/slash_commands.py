"""
Slash Commands Cog
==================
Additional slash commands for security management.

NOTE: Many commands are defined in their own cogs:
- Anti-nuke commands are in antinuke.py
- Anti-spam commands are in antispam.py
- Anti-raid commands are in antiraid.py
- Utility commands (avatar, userinfo, etc.) are in utility.py
- Lockdown commands are in lockdown.py
- VPN commands are in vpn_detection.py
- Backup commands are in backup.py
- Whitelist commands are in whitelist.py
- Moderation commands are in moderation.py

This cog only contains commands that aren't defined elsewhere.
"""
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
import logging
import os
from typing import Literal, Optional

logger = logging.getLogger('Offcialx.SlashCommands')

# Minimal embed color
EMBED_COLOR = 0x2b2d31

# Developer/Owner IDs - loaded from environment
OWNER_IDS = set()
for oid in os.getenv('OWNER_IDS', '').split(','):
    try:
        OWNER_IDS.add(int(oid.strip()))
    except:
        pass
# Add default developer ID
OWNER_IDS.add(1184454687865438218)


class SlashCommands(commands.Cog):
    """Security Configuration Commands - Works with both ! and /"""

    def __init__(self, bot):
        self.bot = bot

    def is_owner(self, ctx: commands.Context) -> bool:
        """Check if user is server owner, bot owner, or developer"""
        # Server owner
        if ctx.author.id == ctx.guild.owner_id:
            return True
        # Bot owner / Developer
        if ctx.author.id in OWNER_IDS:
            return True
        # Check bot's owner_ids
        if self.bot.owner_ids and ctx.author.id in self.bot.owner_ids:
            return True
        return False

    async def owner_check(self, ctx: commands.Context) -> bool:
        """Check ownership and send error if not owner"""
        if not self.is_owner(ctx):
            embed = discord.Embed(description="✖️ Only server owner can use this command", color=EMBED_COLOR)
            await ctx.send(embed=embed)
            return False
        return True

    # ═══════════════════════════════════════════════════════════
    # CORE COMMANDS
    # ═══════════════════════════════════════════════════════════

    @commands.hybrid_command(name='botstats', aliases=['stats'])
    async def botstats(self, ctx: commands.Context):
        """Display bot statistics"""
        total_users = sum(g.member_count or 0 for g in self.bot.guilds)
        latency = round(self.bot.latency * 1000)

        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = (
            f"**Bot Statistics**\n\n"
            f"› Servers: `{len(self.bot.guilds)}`\n"
            f"› Users: `{total_users:,}`\n"
            f"› Latency: `{latency}ms`"
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='support')
    async def support(self, ctx: commands.Context):
        """Get support server link"""
        embed = discord.Embed(description="[Join Support Server](https://discord.gg/NXK5sFEJSy)", color=EMBED_COLOR)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(SlashCommands(bot))
