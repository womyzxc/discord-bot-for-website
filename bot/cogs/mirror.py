"""
Channel Mirror Cog - Optimized with Smart Rate Limiting
=========================================================
Forward messages from one channel to another (cross-server supported)
- Live mirroring of new messages
- Copy message history with rate limit protection
- Queue system for stable copying
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

EMBED_COLOR = 0x2b2d31


class Mirror(commands.Cog):
    """Cross-Server Channel Mirroring System - Optimized"""

    def __init__(self, bot):
        self.bot = bot
        self.db = None
        self.mirrors: Dict[int, List[int]] = defaultdict(list)
        self.mirror_owners: Dict[int, int] = {}
        self._loaded = False
        self.owner_ids: Set[int] = set()
        for oid in os.getenv('OWNER_IDS', '').split(','):
            try:
                self.owner_ids.add(int(oid.strip()))
            except:
                pass

        # Rate limit protection
        self.copy_locks: Dict[int, asyncio.Lock] = defaultdict(asyncio.Lock)
        self.active_copies: Dict[int, bool] = {}
        self.MESSAGE_DELAY = 1.0
        self.BATCH_DELAY = 3.0
        self.FILE_DELAY = 2.0
        self.RATE_LIMIT_BACKOFF = 5.0

    def is_owner(self, guild: discord.Guild, user_id: int) -> bool:
        if user_id == guild.owner_id:
            return True
        if user_id in self.owner_ids:
            return True
        if self.bot.owner_ids and user_id in self.bot.owner_ids:
            return True
        return False

    async def preload_all_settings(self):
        if not self.db or self._loaded:
            return
        try:
            mirror_data = await self.db.get_bot_setting('mirrors')
            if mirror_data and isinstance(mirror_data, dict):
                mirrors_dict = mirror_data.get('mirrors', {})
                for source_id_str, destinations in mirrors_dict.items():
                    try:
                        source_id = int(source_id_str)
                        self.mirrors[source_id] = [int(d) for d in destinations]
                    except:
                        pass
                owners_dict = mirror_data.get('owners', {})
                for source_id_str, guild_id in owners_dict.items():
                    try:
                        self.mirror_owners[int(source_id_str)] = int(guild_id)
                    except:
                        pass
                total_mirrors = sum(len(d) for d in self.mirrors.values())
                logger.info(f"Loaded {total_mirrors} mirrors from database")
            self._loaded = True
        except Exception as e:
            logger.warning(f"Failed to load mirrors from database: {e}")

    async def save_mirrors_to_db(self):
        if not self.db:
            return
        try:
            mirrors_dict = {str(k): v for k, v in self.mirrors.items() if v}
            owners_dict = {str(k): v for k, v in self.mirror_owners.items()}
            mirror_data = {'mirrors': mirrors_dict, 'owners': owners_dict}
            await self.db.save_bot_setting('mirrors', mirror_data)
        except Exception as e:
            logger.warning(f"Failed to save mirrors: {e}")

    async def _safe_send(self, channel, **kwargs) -> bool:
        for attempt in range(3):
            try:
                await channel.send(**kwargs)
                return True
            except discord.HTTPException as e:
                if e.status == 429:
                    retry_after = getattr(e, 'retry_after', self.RATE_LIMIT_BACKOFF)
                    await asyncio.sleep(retry_after)
                else:
                    return False
            except:
                return False
        return False

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        if message.channel.id not in self.mirrors:
            return
        destinations = self.mirrors[message.channel.id]
        if not destinations:
            return

        embed = discord.Embed(
            description=message.content if message.content else None,
            color=EMBED_COLOR,
            timestamp=message.created_at
        )
        embed.set_author(
            name=message.author.display_name,
            icon_url=message.author.display_avatar.url if message.author.display_avatar else None
        )
        embed.set_footer(text=f"#{message.channel.name}")

        if message.attachments:
            file_links = []
            for att in message.attachments:
                is_image = att.content_type and att.content_type.startswith('image/')
                if is_image and not embed.image:
                    embed.set_image(url=att.url)
                else:
                    file_links.append(f"[{att.filename}]({att.url})")
            if file_links:
                embed.add_field(name="Files", value="\n".join(file_links[:5]), inline=False)

        for dest_id in destinations:
            asyncio.create_task(self._forward_to_destination(dest_id, embed))

    async def _forward_to_destination(self, dest_id: int, embed: discord.Embed):
        try:
            dest_channel = self.bot.get_channel(dest_id)
            if dest_channel:
                await dest_channel.send(embed=embed)
        except:
            pass

    @commands.hybrid_group(name='mirror', invoke_without_command=True)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def mirror(self, ctx: commands.Context):
        if not self.is_owner(ctx.guild, ctx.author.id):
            return await ctx.send(embed=discord.Embed(description="✕ Only server owner", color=EMBED_COLOR))

        guild_mirrors = []
        for source_id, destinations in self.mirrors.items():
            source_channel = self.bot.get_channel(source_id)
            if source_channel and source_channel.guild.id == ctx.guild.id:
                for dest_id in destinations:
                    dest_channel = self.bot.get_channel(dest_id)
                    if dest_channel:
                        guild_mirrors.append(f"› #{source_channel.name} → #{dest_channel.name}")

        if not guild_mirrors:
            embed = discord.Embed(description="**Mirrors**\n\n› No active mirrors\n\n`mirror add #source <dest_id>`", color=EMBED_COLOR)
        else:
            embed = discord.Embed(description="**Mirrors**\n\n" + "\n".join(guild_mirrors), color=EMBED_COLOR)
        await ctx.send(embed=embed)

    @mirror.command(name='add')
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def mirror_add(self, ctx, source: discord.TextChannel, destination_id: str):
        if not self.is_owner(ctx.guild, ctx.author.id):
            return await ctx.send(embed=discord.Embed(description="✕ Only server owner", color=EMBED_COLOR))
        try:
            dest_id = int(destination_id.strip('<>#'))
        except:
            return await ctx.send(embed=discord.Embed(description="✕ Invalid ID", color=EMBED_COLOR))

        dest_channel = self.bot.get_channel(dest_id)
        if not dest_channel:
            return await ctx.send(embed=discord.Embed(description="✕ Channel not found", color=EMBED_COLOR))

        if dest_id in self.mirrors[source.id]:
            return await ctx.send(embed=discord.Embed(description="› Already mirrored", color=EMBED_COLOR))

        self.mirrors[source.id].append(dest_id)
        self.mirror_owners[source.id] = ctx.guild.id
        await self.save_mirrors_to_db()

        await ctx.send(embed=discord.Embed(description=f"+ Mirror: #{source.name} → #{dest_channel.name}", color=EMBED_COLOR))

    @mirror.command(name='remove')
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def mirror_remove(self, ctx, source: discord.TextChannel, destination_id: str = None):
        if not self.is_owner(ctx.guild, ctx.author.id):
            return await ctx.send(embed=discord.Embed(description="✕ Only server owner", color=EMBED_COLOR))

        if destination_id:
            try:
                dest_id = int(destination_id.strip('<>#'))
                if dest_id in self.mirrors[source.id]:
                    self.mirrors[source.id].remove(dest_id)
                    await self.save_mirrors_to_db()
                    return await ctx.send(embed=discord.Embed(description=f"− Removed mirror", color=EMBED_COLOR))
            except:
                pass
        else:
            self.mirrors[source.id] = []
            await self.save_mirrors_to_db()
            return await ctx.send(embed=discord.Embed(description=f"− Removed all mirrors from #{source.name}", color=EMBED_COLOR))

    @mirror.command(name='copy')
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def mirror_copy(self, ctx, source: discord.TextChannel, destination_id: str, amount: str = "50"):
        if not self.is_owner(ctx.guild, ctx.author.id):
            return await ctx.send(embed=discord.Embed(description="✕ Only server owner", color=EMBED_COLOR))

        if self.active_copies.get(ctx.guild.id):
            return await ctx.send(embed=discord.Embed(description="✕ Copy already running", color=EMBED_COLOR))

        copy_all = amount.lower() == 'all'
        limit = None if copy_all else min(int(amount) if amount.isdigit() else 50, 1000)

        try:
            dest_id = int(destination_id.strip('<>#'))
        except:
            return await ctx.send(embed=discord.Embed(description="✕ Invalid ID", color=EMBED_COLOR))

        dest_channel = self.bot.get_channel(dest_id)
        if not dest_channel:
            return await ctx.send(embed=discord.Embed(description="✕ Channel not found", color=EMBED_COLOR))

        async with self.copy_locks[ctx.guild.id]:
            self.active_copies[ctx.guild.id] = True
            try:
                status_msg = await ctx.send(embed=discord.Embed(description="⟳ Fetching messages...", color=EMBED_COLOR))

                messages = []
                async for msg in source.history(limit=limit):
                    if not msg.author.bot:
                        messages.append(msg)
                    if len(messages) % 100 == 0:
                        await asyncio.sleep(0.3)

                messages.reverse()
                total = len(messages)

                if total == 0:
                    return await status_msg.edit(embed=discord.Embed(description="✕ No messages", color=EMBED_COLOR))

                await status_msg.edit(embed=discord.Embed(description=f"⟳ Copying {total} messages...", color=EMBED_COLOR))

                copied = 0
                for i, msg in enumerate(messages):
                    if not self.active_copies.get(ctx.guild.id):
                        break

                    embed = discord.Embed(
                        description=msg.content if msg.content else None,
                        color=EMBED_COLOR,
                        timestamp=msg.created_at
                    )
                    embed.set_author(name=msg.author.display_name, icon_url=msg.author.display_avatar.url if msg.author.display_avatar else None)
                    embed.set_footer(text=f"#{source.name}")

                    if msg.attachments:
                        for att in msg.attachments:
                            if att.content_type and att.content_type.startswith('image/') and not embed.image:
                                embed.set_image(url=att.url)
                            else:
                                embed.add_field(name="File", value=f"[{att.filename}]({att.url})", inline=False)

                    if await self._safe_send(dest_channel, embed=embed):
                        copied += 1

                    await asyncio.sleep(self.MESSAGE_DELAY)
                    if (i + 1) % 5 == 0:
                        await asyncio.sleep(self.BATCH_DELAY)

                    if copied % 25 == 0:
                        try:
                            await status_msg.edit(embed=discord.Embed(description=f"⟳ {copied}/{total}", color=EMBED_COLOR))
                        except:
                            pass

                await status_msg.edit(embed=discord.Embed(description=f"+ Copied {copied}/{total} messages", color=EMBED_COLOR))
            finally:
                self.active_copies[ctx.guild.id] = False

    @mirror.command(name='test')
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def mirror_test(self, ctx, destination_id: str):
        try:
            dest_id = int(destination_id.strip('<>#'))
            dest_channel = self.bot.get_channel(dest_id)
            if dest_channel:
                await dest_channel.send(embed=discord.Embed(description=f"Test from {ctx.guild.name}", color=EMBED_COLOR))
                await ctx.send(embed=discord.Embed(description=f"+ Test sent to #{dest_channel.name}", color=EMBED_COLOR))
            else:
                await ctx.send(embed=discord.Embed(description="✕ Channel not found", color=EMBED_COLOR))
        except:
            await ctx.send(embed=discord.Embed(description="✕ Invalid ID", color=EMBED_COLOR))

    @mirror.command(name='cancel')
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def mirror_cancel(self, ctx):
        if self.active_copies.get(ctx.guild.id):
            self.active_copies[ctx.guild.id] = False
            await ctx.send(embed=discord.Embed(description="+ Cancelled", color=EMBED_COLOR))
        else:
            await ctx.send(embed=discord.Embed(description="› Nothing running", color=EMBED_COLOR))


async def setup(bot):
    await bot.add_cog(Mirror(bot))
