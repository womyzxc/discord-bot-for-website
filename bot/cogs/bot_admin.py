"""
Bot Admin Cog
=============
Bot owner commands for:
- Changing bot status/activity
- Viewing server count
- Logging when bot joins/leaves servers
"""

import discord
from discord.ext import commands
from datetime import datetime
import logging
import os
from typing import Optional

logger = logging.getLogger('Offcialx.BotAdmin')

# Minimal embed color
EMBED_COLOR = 0x2b2d31


class BotAdmin(commands.Cog):
    """Bot Administration Commands"""

    def __init__(self, bot):
        self.bot = bot
        self.db = None  # Will be injected by bot
        self._settings_loaded = False

        # Owner IDs from environment
        self.owner_ids: set = set()
        for oid in os.getenv('OWNER_IDS', '').split(','):
            try:
                self.owner_ids.add(int(oid.strip()))
            except:
                pass

        # Add default developer ID
        self.owner_ids.add(1184454687865438218)

        # Join/leave log channel ID (set via command)
        self.log_channel_id: Optional[int] = None

        # Bot activity settings
        self.saved_activity_type: Optional[str] = None
        self.saved_activity_text: Optional[str] = None
        self.saved_status: Optional[str] = None

    async def load_settings(self):
        """Load bot settings from database"""
        if not self.db or self._settings_loaded:
            return

        try:
            # Load join/leave log channel
            log_settings = await self.db.get_bot_setting('join_leave_log')
            if log_settings and 'channel_id' in log_settings:
                self.log_channel_id = log_settings['channel_id']
                logger.info(f"Loaded join/leave log channel: {self.log_channel_id}")

            # Load bot status/activity
            activity_settings = await self.db.get_bot_setting('bot_activity')
            if activity_settings:
                self.saved_activity_type = activity_settings.get('type')
                self.saved_activity_text = activity_settings.get('text')
                self.saved_status = activity_settings.get('status')

                # Apply the saved activity
                await self._apply_saved_activity()
                logger.info(f"Loaded bot activity: {self.saved_activity_type} {self.saved_activity_text}")

            self._settings_loaded = True
        except Exception as e:
            logger.warning(f"Failed to load bot settings: {e}")

    async def _apply_saved_activity(self):
        """Apply saved activity settings"""
        if not self.saved_activity_type and not self.saved_status:
            return

        try:
            activity = None
            if self.saved_activity_type and self.saved_activity_text:
                activity_map = {
                    'watching': discord.ActivityType.watching,
                    'playing': discord.ActivityType.playing,
                    'listening': discord.ActivityType.listening,
                    'competing': discord.ActivityType.competing,
                }
                if self.saved_activity_type in activity_map:
                    activity = discord.Activity(
                        type=activity_map[self.saved_activity_type],
                        name=self.saved_activity_text
                    )
                elif self.saved_activity_type == 'streaming':
                    activity = discord.Streaming(
                        name=self.saved_activity_text,
                        url="https://twitch.tv/placeholder"
                    )

            status = discord.Status.online
            if self.saved_status:
                status_map = {
                    'online': discord.Status.online,
                    'idle': discord.Status.idle,
                    'dnd': discord.Status.do_not_disturb,
                    'invisible': discord.Status.invisible
                }
                status = status_map.get(self.saved_status, discord.Status.online)

            await self.bot.change_presence(activity=activity, status=status)
        except Exception as e:
            logger.warning(f"Failed to apply saved activity: {e}")

    async def save_activity_settings(self, activity_type: str = None, text: str = None, status: str = None):
        """Save bot activity settings to database"""
        if not self.db:
            return

        try:
            settings = {
                'type': activity_type,
                'text': text,
                'status': status
            }
            await self.db.save_bot_setting('bot_activity', settings)
            self.saved_activity_type = activity_type
            self.saved_activity_text = text
            self.saved_status = status
        except Exception as e:
            logger.warning(f"Failed to save activity settings: {e}")

    async def save_log_channel(self, channel_id: int):
        """Save join/leave log channel to database"""
        if not self.db:
            return

        try:
            await self.db.save_bot_setting('join_leave_log', {'channel_id': channel_id})
        except Exception as e:
            logger.warning(f"Failed to save log channel: {e}")

    @commands.Cog.listener()
    async def on_ready(self):
        """Load settings when bot is ready"""
        await self.load_settings()

    def is_bot_owner(self, user_id: int) -> bool:
        """Check if user is a bot owner"""
        if user_id in self.owner_ids:
            return True
        if self.bot.owner_ids and user_id in self.bot.owner_ids:
            return True
        return False

    # ==================== BOT JOIN/LEAVE LOGGING ====================

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        """Log when bot joins a new server"""
        logger.info(f"BOT JOINED: {guild.name} (ID: {guild.id}) - Members: {guild.member_count}")

        embed = discord.Embed(
            description=f"**Bot Added to Server**\n\n"
                       f"Server: `{guild.name}`\n"
                       f"ID: `{guild.id}`\n"
                       f"Members: `{guild.member_count}`\n"
                       f"Owner: `{guild.owner}`\n"
                       f"Total Servers: `{len(self.bot.guilds)}`",
            color=EMBED_COLOR
        )

        await self._send_log(embed)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        """Log when bot is removed from a server"""
        logger.info(f"BOT REMOVED: {guild.name} (ID: {guild.id})")

        embed = discord.Embed(
            description=f"**Bot Removed from Server**\n\n"
                       f"Server: `{guild.name}`\n"
                       f"ID: `{guild.id}`\n"
                       f"Remaining: `{len(self.bot.guilds)}`",
            color=EMBED_COLOR
        )

        await self._send_log(embed)

    async def _send_log(self, embed: discord.Embed):
        """Send log embed to bot owners and log channel"""
        # Send to log channel if set
        if self.log_channel_id:
            try:
                channel = self.bot.get_channel(self.log_channel_id)
                if channel:
                    await channel.send(embed=embed)
            except Exception as e:
                logger.warning(f"Failed to send to log channel: {e}")

        # Send to all bot owners via DM
        for owner_id in self.owner_ids:
            try:
                owner = await self.bot.fetch_user(owner_id)
                if owner:
                    await owner.send(embed=embed)
            except Exception as e:
                logger.debug(f"Failed to DM owner {owner_id}: {e}")

    # ==================== COMMANDS ====================

    @commands.command(name="botstatus", aliases=["setstatus", "status"])
    async def set_status(self, ctx: commands.Context, status_type: str = None, *, text: str = None):
        """Change the bot's status/activity"""
        if not self.is_bot_owner(ctx.author.id):
            embed = discord.Embed(description="Only bot owners can change status", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        if not status_type:
            current_activity = self.bot.activity
            current_status = self.bot.status

            activity_str = "None"
            if current_activity:
                activity_str = f"{current_activity.type.name}: {current_activity.name}"

            embed = discord.Embed(
                description=f"**Bot Status**\n\n"
                           f"Status: `{current_status}`\n"
                           f"Activity: `{activity_str}`\n\n"
                           f"**Usage:**\n"
                           f"`!botstatus watching <text>`\n"
                           f"`!botstatus playing <text>`\n"
                           f"`!botstatus listening <text>`\n"
                           f"`!botstatus online/idle/dnd/invisible`\n"
                           f"`!botstatus clear`",
                color=EMBED_COLOR
            )
            return await ctx.send(embed=embed)

        status_type = status_type.lower()

        # Handle status changes (online, idle, dnd, invisible)
        if status_type in ['online', 'idle', 'dnd', 'invisible']:
            status_map = {
                'online': discord.Status.online,
                'idle': discord.Status.idle,
                'dnd': discord.Status.do_not_disturb,
                'invisible': discord.Status.invisible
            }
            await self.bot.change_presence(
                activity=self.bot.activity,
                status=status_map[status_type]
            )
            # Save to database
            await self.save_activity_settings(
                activity_type=self.saved_activity_type,
                text=self.saved_activity_text,
                status=status_type
            )
            embed = discord.Embed(description=f"+ Changed status to `{status_type}`", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        # Handle clear
        if status_type == 'clear':
            await self.bot.change_presence(activity=None)
            # Save to database
            await self.save_activity_settings(activity_type=None, text=None, status=self.saved_status)
            embed = discord.Embed(description="+ Cleared bot activity", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        # Handle activity types
        if not text:
            embed = discord.Embed(description="Please provide activity text", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        activity_map = {
            'watching': discord.ActivityType.watching,
            'playing': discord.ActivityType.playing,
            'listening': discord.ActivityType.listening,
            'competing': discord.ActivityType.competing,
        }

        if status_type == 'streaming':
            parts = text.split(' ', 1)
            url = parts[0] if parts else "https://twitch.tv/placeholder"
            name = parts[1] if len(parts) > 1 else "Live"
            activity = discord.Streaming(name=name, url=url)
        elif status_type in activity_map:
            activity = discord.Activity(type=activity_map[status_type], name=text)
        else:
            embed = discord.Embed(
                description="Invalid type. Use: `watching`, `playing`, `listening`, `competing`, `streaming`",
                color=EMBED_COLOR
            )
            return await ctx.send(embed=embed)

        await self.bot.change_presence(activity=activity)
        # Save to database
        await self.save_activity_settings(activity_type=status_type, text=text, status=self.saved_status)
        embed = discord.Embed(description=f"+ Set activity to `{status_type} {text}`", color=EMBED_COLOR)
        await ctx.send(embed=embed)

    @commands.command(name="servers", aliases=["servercount", "guildcount", "guilds"])
    async def server_count(self, ctx: commands.Context):
        """View how many servers the bot is in"""
        if not self.is_bot_owner(ctx.author.id):
            embed = discord.Embed(description="Only bot owners can view this", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        total_servers = len(self.bot.guilds)
        total_members = sum(g.member_count or 0 for g in self.bot.guilds)

        sorted_guilds = sorted(self.bot.guilds, key=lambda g: g.member_count or 0, reverse=True)[:10]

        server_list = []
        for i, guild in enumerate(sorted_guilds, 1):
            server_list.append(f"`{i}.` {guild.name} - `{guild.member_count}`")

        embed = discord.Embed(
            description=f"**Bot Statistics**\n\n"
                       f"Servers: `{total_servers}`\n"
                       f"Members: `{total_members:,}`\n"
                       f"Ping: `{round(self.bot.latency * 1000)}ms`\n\n"
                       f"**Top Servers**\n" + "\n".join(server_list),
            color=EMBED_COLOR
        )

        await ctx.send(embed=embed)

    @commands.command(name="serverlist", aliases=["listservers", "allservers"])
    async def server_list(self, ctx: commands.Context):
        """View all servers the bot is in"""
        if not self.is_bot_owner(ctx.author.id):
            embed = discord.Embed(description="Only bot owners can view this", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        servers = sorted(self.bot.guilds, key=lambda g: g.member_count or 0, reverse=True)

        pages = []
        current_page = []
        for i, guild in enumerate(servers, 1):
            current_page.append(f"`{i}.` {guild.name} (`{guild.id}`) - {guild.member_count}")
            if len(current_page) >= 15:
                pages.append("\n".join(current_page))
                current_page = []

        if current_page:
            pages.append("\n".join(current_page))

        if not pages:
            embed = discord.Embed(description="Bot is not in any servers", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        embed = discord.Embed(
            description=f"**Server List ({len(servers)})**\n\n{pages[0]}",
            color=EMBED_COLOR
        )
        if len(pages) > 1:
            embed.set_footer(text=f"Page 1/{len(pages)}")

        await ctx.send(embed=embed)

        for i, page in enumerate(pages[1:], 2):
            embed = discord.Embed(
                description=f"**Server List (continued)**\n\n{page}",
                color=EMBED_COLOR
            )
            embed.set_footer(text=f"Page {i}/{len(pages)}")
            await ctx.send(embed=embed)

    @commands.command(name="setjoinlog", aliases=["setbotlog", "joinlogchannel"])
    async def set_join_log(self, ctx: commands.Context, channel: discord.TextChannel = None):
        """Set the channel for bot join/leave logs"""
        if not self.is_bot_owner(ctx.author.id):
            embed = discord.Embed(description="Only bot owners can set log channel", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        if not channel:
            current = self.bot.get_channel(self.log_channel_id) if self.log_channel_id else None
            embed = discord.Embed(
                description=f"**Bot Join/Leave Log**\n\n"
                           f"Current: {current.mention if current else '`not set`'}\n\n"
                           f"Usage: `!setjoinlog #channel`",
                color=EMBED_COLOR
            )
            return await ctx.send(embed=embed)

        self.log_channel_id = channel.id
        # Save to database
        await self.save_log_channel(channel.id)
        embed = discord.Embed(description=f"+ Set join/leave log to {channel.mention}", color=EMBED_COLOR)
        await ctx.send(embed=embed)

    @commands.command(name="leaveserver", aliases=["leave"])
    async def leave_server(self, ctx: commands.Context, guild_id: int = None):
        """Make the bot leave a server"""
        if not self.is_bot_owner(ctx.author.id):
            embed = discord.Embed(description="Only bot owners can use this", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        if not guild_id:
            embed = discord.Embed(description="Provide a server ID: `!leaveserver <id>`", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        guild = self.bot.get_guild(guild_id)
        if not guild:
            embed = discord.Embed(description="Server not found", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        guild_name = guild.name
        await guild.leave()
        embed = discord.Embed(description=f"+ Left server: `{guild_name}`", color=EMBED_COLOR)
        await ctx.send(embed=embed)

    @commands.command(name="ownerinfo", aliases=["oi"])
    async def show_owner_info(self, ctx: commands.Context):
        """View bot statistics and information"""
        if not self.is_bot_owner(ctx.author.id):
            embed = discord.Embed(description="Only bot owners can view this", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        uptime = datetime.utcnow() - self.bot.start_time if hasattr(self.bot, 'start_time') else None

        uptime_str = "Unknown"
        if uptime:
            days = uptime.days
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            uptime_str = f"{days}d {hours}h {minutes}m"

        embed = discord.Embed(
            description=f"**Offcialx Security Bot**\n\n"
                       f"Servers: `{len(self.bot.guilds)}`\n"
                       f"Users: `{sum(g.member_count or 0 for g in self.bot.guilds):,}`\n"
                       f"Ping: `{round(self.bot.latency * 1000)}ms`\n"
                       f"Uptime: `{uptime_str}`\n"
                       f"Prefix: `!`\n"
                       f"Version: `3.0.0`",
            color=EMBED_COLOR
        )

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(BotAdmin(bot))
