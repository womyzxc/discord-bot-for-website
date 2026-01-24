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
import io
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

    async def _download_attachment(self, attachment: discord.Attachment) -> Optional[discord.File]:
        """Download an attachment and return as discord.File"""
        try:
            file_bytes = await attachment.read()
            return discord.File(
                io.BytesIO(file_bytes),
                filename=attachment.filename,
                spoiler=attachment.is_spoiler()
            )
        except Exception as e:
            logger.warning(f"Failed to download attachment {attachment.filename}: {e}")
            return None

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Forward messages to mirrored channels with full file/image/link support"""
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

        # Collect files to forward
        files_to_send: List[discord.File] = []
        image_urls: List[str] = []
        file_links: List[str] = []

        # Process all attachments
        for attachment in message.attachments:
            is_image = attachment.content_type and attachment.content_type.startswith('image/')
            is_video = attachment.content_type and attachment.content_type.startswith('video/')

            # Try to download and re-upload files (up to 8MB to stay under Discord limit)
            if attachment.size <= 8 * 1024 * 1024:  # 8MB limit
                file = await self._download_attachment(attachment)
                if file:
                    files_to_send.append(file)
                else:
                    # Fallback to link if download fails
                    file_links.append(f"📎 [{attachment.filename}]({attachment.url})")
            else:
                # File too large, send as link
                size_mb = attachment.size / (1024 * 1024)
                file_links.append(f"📎 [{attachment.filename}]({attachment.url}) ({size_mb:.1f}MB)")

            # Also collect image URLs for embed (first image only)
            if is_image and not image_urls:
                image_urls.append(attachment.url)

        # Set first image in embed
        if image_urls:
            embed.set_image(url=image_urls[0])

        # Add file links if any couldn't be uploaded
        if file_links:
            embed.add_field(name="Files", value="\n".join(file_links[:10]), inline=False)

        # Handle stickers
        if message.stickers:
            sticker_info = []
            for sticker in message.stickers:
                sticker_info.append(f"🏷️ {sticker.name}")
            if sticker_info:
                embed.add_field(name="Stickers", value="\n".join(sticker_info), inline=False)

        # Handle replies
        if message.reference and message.reference.message_id:
            try:
                ref_msg = await message.channel.fetch_message(message.reference.message_id)
                reply_preview = ref_msg.content[:100] + "..." if len(ref_msg.content) > 100 else ref_msg.content
                embed.add_field(
                    name=f"↩️ Replying to {ref_msg.author.display_name}",
                    value=reply_preview or "*[No text]*",
                    inline=False
                )
            except:
                pass

        # Forward original embeds (like link previews)
        embeds_to_send = [embed]
        for orig_embed in message.embeds[:3]:  # Max 3 additional embeds
            if orig_embed.type in ['rich', 'image', 'video', 'gifv', 'article', 'link']:
                embeds_to_send.append(orig_embed)

        # Forward to all destinations
        for dest_id in destinations:
            try:
                dest_channel = self.bot.get_channel(dest_id)
                if dest_channel:
                    # Need to recreate files for each destination (files can only be sent once)
                    if files_to_send:
                        # Re-download files for each destination
                        dest_files = []
                        for attachment in message.attachments:
                            if attachment.size <= 8 * 1024 * 1024:
                                file = await self._download_attachment(attachment)
                                if file:
                                    dest_files.append(file)
                        await dest_channel.send(embeds=embeds_to_send, files=dest_files if dest_files else None)
                    else:
                        await dest_channel.send(embeds=embeds_to_send)
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

        embed = discord.Embed(description=f"⟳ Copying {amount} messages from #{source.name}...\n› Including files, images, and links", color=EMBED_COLOR)
        msg = await ctx.send(embed=embed)

        # Fetch messages
        messages = []
        async for message in source.history(limit=amount):
            if not message.author.bot:
                messages.append(message)

        messages.reverse()  # Oldest first

        copied = 0
        files_copied = 0
        for message in messages:
            try:
                # Create embed
                msg_embed = discord.Embed(
                    description=message.content if message.content else None,
                    color=EMBED_COLOR,
                    timestamp=message.created_at
                )
                msg_embed.set_author(
                    name=f"{message.author.display_name} (@{message.author.name})",
                    icon_url=message.author.display_avatar.url if message.author.display_avatar else None
                )
                msg_embed.set_footer(text=f"#{source.name} • {source.guild.name}")

                # Collect files and images
                files_to_send = []
                file_links = []
                image_set = False

                for attachment in message.attachments:
                    is_image = attachment.content_type and attachment.content_type.startswith('image/')

                    # Set first image in embed
                    if is_image and not image_set:
                        msg_embed.set_image(url=attachment.url)
                        image_set = True

                    # Try to download and re-upload files (up to 8MB)
                    if attachment.size <= 8 * 1024 * 1024:
                        file = await self._download_attachment(attachment)
                        if file:
                            files_to_send.append(file)
                            files_copied += 1
                        else:
                            file_links.append(f"📎 [{attachment.filename}]({attachment.url})")
                    else:
                        size_mb = attachment.size / (1024 * 1024)
                        file_links.append(f"📎 [{attachment.filename}]({attachment.url}) ({size_mb:.1f}MB)")

                # Add file links if any
                if file_links:
                    msg_embed.add_field(name="Files", value="\n".join(file_links[:5]), inline=False)

                # Include original embeds (link previews)
                embeds_to_send = [msg_embed]
                for orig_embed in message.embeds[:2]:
                    if orig_embed.type in ['rich', 'image', 'video', 'gifv', 'article', 'link']:
                        embeds_to_send.append(orig_embed)

                # Send message with files
                await dest_channel.send(embeds=embeds_to_send, files=files_to_send if files_to_send else None)
                copied += 1

                # Rate limit protection
                if copied % 3 == 0:
                    await asyncio.sleep(1.5)

                # Update progress every 10 messages
                if copied % 10 == 0:
                    progress_embed = discord.Embed(
                        description=f"⟳ Copying... `{copied}/{len(messages)}` messages\n› Files copied: `{files_copied}`",
                        color=EMBED_COLOR
                    )
                    await msg.edit(embed=progress_embed)

            except Exception as e:
                logger.warning(f"Failed to copy message: {e}")

        embed = discord.Embed(
            description=f"+ Copied `{copied}` messages to #{dest_channel.name}\n› Server: {dest_channel.guild.name}\n› Files copied: `{files_copied}`",
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
