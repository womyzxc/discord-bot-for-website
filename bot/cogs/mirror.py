"""
Channel Mirror Cog
===================
Forward messages from one channel to another (cross-server supported)
- Live mirroring of new messages
- Copy message history
- Works across different servers
"""

import discord
from discord.ext import commands
from datetime import datetime
from collections import defaultdict
import logging
import asyncio
from typing import Dict, List, Optional, Set
import os

logger = logging.getLogger('Offcialx.Mirror')

# Minimal embed color
EMBED_COLOR = 0x2b2d31


class Mirror(commands.Cog):
    """Cross-Server Channel Mirroring System"""

    def __init__(self, bot):
        self.bot = bot
        self.db = None  # Will be injected by bot

        # Active mirrors: source_channel_id -> list of destination_channel_ids
        self.mirrors: Dict[int, List[int]] = defaultdict(list)

        # Track which guilds set up each mirror (for permission checks)
        self.mirror_owners: Dict[int, int] = {}  # source_channel_id -> guild_id that created it

        # Owner IDs from environment
        self.owner_ids: Set[int] = set()
        for oid in os.getenv('OWNER_IDS', '').split(','):
            try:
                self.owner_ids.add(int(oid.strip()))
            except:
                pass

    def is_owner(self, guild: discord.Guild, user_id: int) -> bool:
        """Check if user is server owner or bot owner"""
        if user_id == guild.owner_id:
            return True
        if user_id in self.owner_ids:
            return True
        if self.bot.owner_ids and user_id in self.bot.owner_ids:
            return True
        return False

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Forward messages to mirrored channels"""
        # Ignore bot messages to prevent loops
        if message.author.bot:
            return

        # Ignore DMs
        if not message.guild:
            return

        # Check if this channel has mirrors
        if message.channel.id not in self.mirrors:
            return

        destinations = self.mirrors[message.channel.id]
        if not destinations:
            return

        # Create embed for the forwarded message
        embed = discord.Embed(
            description=message.content if message.content else None,
            color=EMBED_COLOR,
            timestamp=message.created_at
        )
        embed.set_author(
            name=f"{message.author.display_name} (@{message.author.name})",
            icon_url=message.author.display_avatar.url if message.author.display_avatar else None
        )
        embed.set_footer(text=f"#{message.channel.name} • {message.guild.name}")

        # Handle attachments
        image_set = False
        attachment_links = []
        for attachment in message.attachments:
            if attachment.content_type and attachment.content_type.startswith('image/') and not image_set:
                embed.set_image(url=attachment.url)
                image_set = True
            else:
                attachment_links.append(f"[{attachment.filename}]({attachment.url})")

        if attachment_links:
            embed.add_field(name="Attachments", value="\n".join(attachment_links), inline=False)

        # Handle replies
        if message.reference and message.reference.message_id:
            try:
                ref_msg = await message.channel.fetch_message(message.reference.message_id)
                reply_preview = ref_msg.content[:100] + "..." if len(ref_msg.content) > 100 else ref_msg.content
                embed.add_field(
                    name=f"Replying to {ref_msg.author.display_name}",
                    value=reply_preview or "*[No text]*",
                    inline=False
                )
            except:
                pass

        # Forward to all destinations
        for dest_id in destinations:
            try:
                dest_channel = self.bot.get_channel(dest_id)
                if dest_channel:
                    await dest_channel.send(embed=embed)
            except Exception as e:
                logger.warning(f"Failed to forward message to {dest_id}: {e}")

    # ==================== COMMANDS ====================

    @commands.hybrid_group(name='mirror', invoke_without_command=True)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def mirror(self, ctx: commands.Context):
        """View all active mirrors for this server"""
        if not self.is_owner(ctx.guild, ctx.author.id):
            embed = discord.Embed(description="✕ Only server owner can manage mirrors", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        # Find mirrors where source is in this guild
        guild_mirrors = []
        for source_id, destinations in self.mirrors.items():
            source_channel = self.bot.get_channel(source_id)
            if source_channel and source_channel.guild.id == ctx.guild.id:
                for dest_id in destinations:
                    dest_channel = self.bot.get_channel(dest_id)
                    if dest_channel:
                        guild_mirrors.append(f"› #{source_channel.name} → #{dest_channel.name} ({dest_channel.guild.name})")
                    else:
                        guild_mirrors.append(f"› #{source_channel.name} → `{dest_id}` (unknown)")

        # Find mirrors where destination is in this guild
        incoming_mirrors = []
        for source_id, destinations in self.mirrors.items():
            source_channel = self.bot.get_channel(source_id)
            for dest_id in destinations:
                dest_channel = self.bot.get_channel(dest_id)
                if dest_channel and dest_channel.guild.id == ctx.guild.id and source_channel:
                    if source_channel.guild.id != ctx.guild.id:
                        incoming_mirrors.append(f"› #{source_channel.name} ({source_channel.guild.name}) → #{dest_channel.name}")

        if not guild_mirrors and not incoming_mirrors:
            embed = discord.Embed(
                description=(
                    "**Channel Mirrors**\n\n"
                    "› No active mirrors\n\n"
                    "**Setup a Mirror:**\n"
                    "› `mirror add #source <dest_channel_id>`\n"
                    "› Source must be in this server\n"
                    "› Destination can be in any server with the bot"
                ),
                color=EMBED_COLOR
            )
            return await ctx.send(embed=embed)

        text = "**Channel Mirrors**\n\n"
        if guild_mirrors:
            text += "**Outgoing (from this server):**\n" + "\n".join(guild_mirrors) + "\n\n"
        if incoming_mirrors:
            text += "**Incoming (to this server):**\n" + "\n".join(incoming_mirrors)

        embed = discord.Embed(description=text.strip(), color=EMBED_COLOR)
        await ctx.send(embed=embed)

    @mirror.command(name='add', aliases=['setup', 'create'])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def mirror_add(self, ctx: commands.Context, source: discord.TextChannel, destination_id: str):
        """
        Set up a mirror from source channel to destination

        Usage: !mirror add #source-channel 123456789 (destination channel ID)
        The destination can be in another server where the bot is
        """
        if not self.is_owner(ctx.guild, ctx.author.id):
            embed = discord.Embed(description="✕ Only server owner can manage mirrors", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        # Source must be in this guild
        if source.guild.id != ctx.guild.id:
            embed = discord.Embed(description="✕ Source channel must be in this server", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        # Parse destination ID
        try:
            dest_id = int(destination_id.strip('<>#'))
        except ValueError:
            embed = discord.Embed(description="✕ Invalid destination channel ID", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        # Check if destination exists and bot has access
        dest_channel = self.bot.get_channel(dest_id)
        if not dest_channel:
            embed = discord.Embed(
                description="✕ Cannot find destination channel\n› Make sure the bot is in that server\n› Make sure the channel ID is correct",
                color=EMBED_COLOR
            )
            return await ctx.send(embed=embed)

        # Check if bot can send to destination
        if not dest_channel.permissions_for(dest_channel.guild.me).send_messages:
            embed = discord.Embed(description="✕ Bot cannot send messages to destination channel", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        # Check if already mirrored
        if dest_id in self.mirrors[source.id]:
            embed = discord.Embed(description="› This mirror already exists", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        # Add mirror
        self.mirrors[source.id].append(dest_id)
        self.mirror_owners[source.id] = ctx.guild.id

        embed = discord.Embed(
            description=(
                f"+ Mirror created\n\n"
                f"› From: #{source.name} (this server)\n"
                f"› To: #{dest_channel.name} ({dest_channel.guild.name})\n\n"
                f"*All new messages in #{source.name} will be forwarded*"
            ),
            color=EMBED_COLOR
        )
        await ctx.send(embed=embed)

        # Send confirmation to destination
        try:
            confirm_embed = discord.Embed(
                description=(
                    f"**Mirror Connected**\n\n"
                    f"This channel will now receive messages from:\n"
                    f"› #{source.name} in **{source.guild.name}**"
                ),
                color=EMBED_COLOR
            )
            await dest_channel.send(embed=confirm_embed)
        except:
            pass

    @mirror.command(name='remove', aliases=['delete', 'stop'])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def mirror_remove(self, ctx: commands.Context, source: discord.TextChannel, destination_id: str = None):
        """
        Remove a mirror

        Usage:
        !mirror remove #source-channel 123456789 - Remove specific destination
        !mirror remove #source-channel - Remove all destinations for this source
        """
        if not self.is_owner(ctx.guild, ctx.author.id):
            embed = discord.Embed(description="✕ Only server owner can manage mirrors", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        if source.id not in self.mirrors or not self.mirrors[source.id]:
            embed = discord.Embed(description="✕ No mirrors found for this channel", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        if destination_id:
            try:
                dest_id = int(destination_id.strip('<>#'))
            except ValueError:
                embed = discord.Embed(description="✕ Invalid destination channel ID", color=EMBED_COLOR)
                return await ctx.send(embed=embed)

            if dest_id in self.mirrors[source.id]:
                self.mirrors[source.id].remove(dest_id)
                embed = discord.Embed(description=f"− Removed mirror from #{source.name} to `{dest_id}`", color=EMBED_COLOR)
            else:
                embed = discord.Embed(description="✕ Mirror not found", color=EMBED_COLOR)
        else:
            count = len(self.mirrors[source.id])
            self.mirrors[source.id] = []
            embed = discord.Embed(description=f"− Removed all `{count}` mirrors from #{source.name}", color=EMBED_COLOR)

        await ctx.send(embed=embed)

    @mirror.command(name='copy', aliases=['history'])
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def mirror_copy(self, ctx: commands.Context, source: discord.TextChannel, destination_id: str, amount: int = 50):
        """
        Copy message history from source to destination (max 100)

        Usage: !mirror copy #source-channel 123456789 50
        """
        if not self.is_owner(ctx.guild, ctx.author.id):
            embed = discord.Embed(description="✕ Only server owner can copy messages", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        if amount > 100:
            amount = 100
        if amount < 1:
            amount = 1

        # Parse destination
        try:
            dest_id = int(destination_id.strip('<>#'))
        except ValueError:
            embed = discord.Embed(description="✕ Invalid destination channel ID", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        dest_channel = self.bot.get_channel(dest_id)
        if not dest_channel:
            embed = discord.Embed(description="✕ Cannot find destination channel", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        embed = discord.Embed(description=f"⟳ Copying {amount} messages from #{source.name}...", color=EMBED_COLOR)
        msg = await ctx.send(embed=embed)

        # Fetch messages
        messages = []
        async for message in source.history(limit=amount):
            if not message.author.bot:
                messages.append(message)

        messages.reverse()  # Oldest first

        copied = 0
        for message in messages:
            try:
                # Create embed
                embed = discord.Embed(
                    description=message.content if message.content else None,
                    color=EMBED_COLOR,
                    timestamp=message.created_at
                )
                embed.set_author(
                    name=f"{message.author.display_name} (@{message.author.name})",
                    icon_url=message.author.display_avatar.url if message.author.display_avatar else None
                )
                embed.set_footer(text=f"#{source.name} • {source.guild.name}")

                # Handle attachments
                for attachment in message.attachments:
                    if attachment.content_type and attachment.content_type.startswith('image/'):
                        embed.set_image(url=attachment.url)
                        break

                await dest_channel.send(embed=embed)
                copied += 1

                # Rate limit protection
                if copied % 5 == 0:
                    await asyncio.sleep(1)

            except Exception as e:
                logger.warning(f"Failed to copy message: {e}")

        embed = discord.Embed(
            description=f"+ Copied `{copied}` messages to #{dest_channel.name} ({dest_channel.guild.name})",
            color=EMBED_COLOR
        )
        await msg.edit(embed=embed)

    @mirror.command(name='test')
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def mirror_test(self, ctx: commands.Context, destination_id: str):
        """
        Test if bot can send to a channel in another server

        Usage: !mirror test 123456789
        """
        try:
            dest_id = int(destination_id.strip('<>#'))
        except ValueError:
            embed = discord.Embed(description="✕ Invalid channel ID", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        dest_channel = self.bot.get_channel(dest_id)
        if not dest_channel:
            embed = discord.Embed(
                description=(
                    "✕ Cannot find channel\n\n"
                    "**Possible reasons:**\n"
                    "› Bot is not in that server\n"
                    "› Channel ID is incorrect\n"
                    "› Bot doesn't have access to the channel"
                ),
                color=EMBED_COLOR
            )
            return await ctx.send(embed=embed)

        # Try to send test message
        try:
            test_embed = discord.Embed(
                description=f"**Test Message**\n\nThis is a test from **{ctx.guild.name}**",
                color=EMBED_COLOR,
                timestamp=datetime.utcnow()
            )
            test_embed.set_footer(text=f"Sent by {ctx.author.display_name}")
            await dest_channel.send(embed=test_embed)

            embed = discord.Embed(
                description=(
                    f"+ Test successful!\n\n"
                    f"› Channel: #{dest_channel.name}\n"
                    f"› Server: {dest_channel.guild.name}\n"
                    f"› Channel ID: `{dest_id}`"
                ),
                color=EMBED_COLOR
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = discord.Embed(description="✕ Bot doesn't have permission to send messages there", color=EMBED_COLOR)
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(description=f"✕ Failed: {str(e)[:100]}", color=EMBED_COLOR)
            await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Mirror(bot))
