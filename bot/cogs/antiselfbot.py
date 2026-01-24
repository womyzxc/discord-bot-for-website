"""
Anti-Selfbot Detection Cog
==========================
Detects and prevents selfbot usage:
- Automated response patterns
- Impossibly fast reactions
- Nitro sniping behavior
- Automated message patterns
- API abuse detection
"""

import discord
from discord.ext import commands
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio
import logging
from typing import Dict, List, Optional
import re

logger = logging.getLogger('Offcialx.AntiSelfbot')

# Minimal embed color
EMBED_COLOR = 0x2b2d31


class SelfbotTracker:
    """Track suspicious selfbot behavior for a user"""

    def __init__(self):
        self.fast_reactions: List[datetime] = []
        self.command_responses: List[Dict] = []
        self.nitro_attempts: List[datetime] = []
        self.automated_patterns: List[Dict] = []
        self.suspicion_score: int = 0
        self.flagged: bool = False
        self.last_message_time: Optional[datetime] = None
        self.message_intervals: List[float] = []


class AntiSelfbot(commands.Cog):
    """Anti-Selfbot Detection System"""

    def __init__(self, bot):
        self.bot = bot

        # Owner IDs from environment
        self.owner_ids: set = set()
        import os
        for oid in os.getenv('OWNER_IDS', '').split(','):
            try:
                self.owner_ids.add(int(oid.strip()))
            except (ValueError, AttributeError):
                pass  # Invalid or empty ID - skip


        # Track users
        self.trackers: Dict[int, Dict[int, SelfbotTracker]] = defaultdict(lambda: defaultdict(SelfbotTracker))

        # Guild settings
        self.guild_settings: Dict[int, Dict] = {}
        self.db = None  # Will be injected by bot
        self._settings_loaded: set = set()

        # Known selfbot command patterns
        self.selfbot_patterns = [
            r'^\.(?:snipe|editsnipe|reactionsnipe)',
            r'^\.(?:steal|yoink|grab)',
            r'^\.(?:nitro|token|grab)',
            r'^\.(?:afk|status|activity)',
            r'^\?(?:snipe|steal|grab)',
        ]

        # Compiled patterns
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.selfbot_patterns]

        # Nitro gift pattern
        self.nitro_pattern = re.compile(
            r'(?:https?://)?(?:www\.)?discord(?:app)?\.(?:com|gift)/gifts?/[\w-]+',
            re.IGNORECASE
        )

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
            embed = discord.Embed(description="✖️ Only server owner can use this command", color=EMBED_COLOR)
            await ctx.send(embed=embed)
            return False
        return True
    async def get_settings(self, guild_id: int) -> Dict:
        """Get guild settings - loads from database if available"""
        if guild_id not in self.guild_settings:
            self.guild_settings[guild_id] = {
                'enabled': True,
                'detect_fast_reactions': True,
                'detect_nitro_sniping': True,
                'detect_selfbot_commands': True,
                'detect_automation': True,
                'detect_embed_spam': True,
                'reaction_threshold_ms': 50,
                'automation_interval_variance': 0.1,
                'suspicion_threshold': 100,
                'action': 'alert',
                'log_channel': None,
                'alert_role': None,
            }
            # Try to load from database
            if self.db and guild_id not in self._settings_loaded:
                try:
                    db_settings = await self.db.get_guild_settings(guild_id, 'antiselfbot')
                    if db_settings:
                        self.guild_settings[guild_id].update(db_settings)
                    self._settings_loaded.add(guild_id)
                except Exception as e:
                    logger.warning(f'Failed to load antiselfbot settings from database: {e}')
        return self.guild_settings[guild_id]

    async def save_settings(self, guild_id: int):
        """Save guild settings to database"""
        if not self.db:
            return
        try:
            settings = self.guild_settings.get(guild_id, {})
            await self.db.save_guild_settings(guild_id, 'antiselfbot', settings)
        except Exception as e:
            logger.warning(f'Failed to save antiselfbot settings to database: {e}')

    def get_tracker(self, guild_id: int, user_id: int) -> SelfbotTracker:
        """Get tracker for a user"""
        return self.trackers[guild_id][user_id]

    async def check_fast_reaction(self, payload: discord.RawReactionActionEvent, message: discord.Message):
        """Check for impossibly fast reactions"""
        if payload.user_id == self.bot.user.id:
            return

        guild_id = payload.guild_id
        if not guild_id:
            return

        settings = await self.get_settings(guild_id)
        if not settings['enabled'] or not settings['detect_fast_reactions']:
            return

        # Calculate reaction time
        now = datetime.utcnow()
        message_time = message.created_at.replace(tzinfo=None)
        reaction_time_ms = (now - message_time).total_seconds() * 1000

        # Check if reaction is suspiciously fast (especially for new messages)
        if reaction_time_ms < settings['reaction_threshold_ms']:
            tracker = self.get_tracker(guild_id, payload.user_id)
            tracker.fast_reactions.append(now)
            tracker.suspicion_score += 20

            # Clean old entries
            cutoff = now - timedelta(minutes=10)
            tracker.fast_reactions = [t for t in tracker.fast_reactions if t > cutoff]

            # If multiple fast reactions, flag as potential selfbot
            if len(tracker.fast_reactions) >= 3:
                await self.flag_user(guild_id, payload.user_id, "Multiple impossibly fast reactions detected")

    async def check_nitro_sniping(self, message: discord.Message):
        """Check for nitro sniping behavior"""
        if message.author.bot:
            return

        if not message.guild:
            return

        settings = await self.get_settings(message.guild.id)
        if not settings['enabled'] or not settings['detect_nitro_sniping']:
            return

        # Check if message contains a nitro gift link claim attempt
        if self.nitro_pattern.search(message.content):
            tracker = self.get_tracker(message.guild.id, message.author.id)
            tracker.nitro_attempts.append(datetime.utcnow())

            # Check response time (if this is in response to another nitro message)
            # This would require tracking recent nitro messages in the channel
            tracker.suspicion_score += 15

            # Multiple nitro attempts is very suspicious
            cutoff = datetime.utcnow() - timedelta(hours=1)
            tracker.nitro_attempts = [t for t in tracker.nitro_attempts if t > cutoff]

            if len(tracker.nitro_attempts) >= 5:
                await self.flag_user(message.guild.id, message.author.id, "Multiple nitro sniping attempts detected")

    async def check_selfbot_commands(self, message: discord.Message):
        """Check for known selfbot command patterns"""
        if message.author.bot:
            return

        if not message.guild:
            return

        settings = await self.get_settings(message.guild.id)
        if not settings['enabled'] or not settings['detect_selfbot_commands']:
            return

        content = message.content.strip()

        for pattern in self.compiled_patterns:
            if pattern.search(content):
                tracker = self.get_tracker(message.guild.id, message.author.id)
                tracker.command_responses.append({
                    'time': datetime.utcnow(),
                    'content': content
                })
                tracker.suspicion_score += 25

                # Immediate flag for obvious selfbot commands
                await self.flag_user(
                    message.guild.id,
                    message.author.id,
                    f"Selfbot command detected: `{content[:50]}`"
                )

                # Delete the message
                try:
                    await message.delete()
                except:
                    pass

                break

    async def check_automation_patterns(self, message: discord.Message):
        """Check for automated/bot-like behavior patterns"""
        if message.author.bot:
            return

        if not message.guild:
            return

        settings = await self.get_settings(message.guild.id)
        if not settings['enabled'] or not settings['detect_automation']:
            return

        tracker = self.get_tracker(message.guild.id, message.author.id)
        now = datetime.utcnow()

        # Track message timing
        if tracker.last_message_time:
            interval = (now - tracker.last_message_time).total_seconds()
            tracker.message_intervals.append(interval)

            # Keep only last 20 intervals
            tracker.message_intervals = tracker.message_intervals[-20:]

            # Check for suspiciously consistent timing (automation)
            if len(tracker.message_intervals) >= 10:
                avg_interval = sum(tracker.message_intervals) / len(tracker.message_intervals)
                if avg_interval > 0:
                    variance = sum((i - avg_interval) ** 2 for i in tracker.message_intervals) / len(tracker.message_intervals)
                    std_dev = variance ** 0.5
                    coefficient_of_variation = std_dev / avg_interval if avg_interval > 0 else 0

                    # Very low variance in message timing is suspicious
                    if coefficient_of_variation < settings['automation_interval_variance']:
                        tracker.suspicion_score += 30
                        await self.flag_user(
                            message.guild.id,
                            message.author.id,
                            f"Automated message pattern detected (CV: {coefficient_of_variation:.3f})"
                        )

        tracker.last_message_time = now

    async def check_embed_spam(self, message: discord.Message):
        """Check for selfbot embed spam (users can't normally send rich embeds)"""
        if message.author.bot:
            return

        if not message.guild:
            return

        settings = await self.get_settings(message.guild.id)
        if not settings['enabled'] or not settings.get('detect_embed_spam', True):
            return

        # Regular users cannot send rich embeds - only bots and webhooks can
        # If a "user" sends embeds with no content, it's suspicious
        if message.embeds and not message.content:
            for embed in message.embeds:
                # Check if it's a rich embed (not just a link preview)
                if embed.type == 'rich':
                    tracker = self.get_tracker(message.guild.id, message.author.id)
                    tracker.suspicion_score += 50

                    logger.warning(f"EMBED SPAM DETECTED: {message.author.id} sent rich embed")

                    # Immediate action - rich embeds from users are highly suspicious
                    await self.flag_user(
                        message.guild.id,
                        message.author.id,
                        "Sent rich embed (only bots can do this)"
                    )

                    # Delete the message
                    try:
                        await message.delete()
                    except:
                        pass

                    return

        # Check for multiple embeds in short time
        if message.embeds:
            tracker = self.get_tracker(message.guild.id, message.author.id)
            if not hasattr(tracker, 'embed_times'):
                tracker.embed_times = []

            now = datetime.utcnow()
            tracker.embed_times.append(now)

            # Keep only last minute
            cutoff = now - timedelta(minutes=1)
            tracker.embed_times = [t for t in tracker.embed_times if t > cutoff]

            # If more than 5 embeds in a minute, flag
            if len(tracker.embed_times) >= 5:
                tracker.suspicion_score += 30
                await self.flag_user(
                    message.guild.id,
                    message.author.id,
                    f"Sent {len(tracker.embed_times)} embeds in 1 minute"
                )

    async def flag_user(self, guild_id: int, user_id: int, reason: str):
        """Flag a user as potential selfbot"""
        tracker = self.get_tracker(guild_id, user_id)
        settings = await self.get_settings(guild_id)

        if tracker.flagged and tracker.suspicion_score < settings['suspicion_threshold'] * 2:
            return  # Already flagged and not getting worse

        tracker.flagged = True

        logger.warning(f'SELFBOT DETECTED: User {user_id} in guild {guild_id} - {reason}')

        # Log the event
        await self.log_selfbot_event(guild_id, user_id, reason, tracker.suspicion_score)

        # Take action if threshold exceeded
        if tracker.suspicion_score >= settings['suspicion_threshold']:
            await self.take_action(guild_id, user_id, reason)

    async def log_selfbot_event(self, guild_id: int, user_id: int, reason: str, score: int):
        """Log a selfbot detection event"""
        settings = await self.get_settings(guild_id)

        if not settings['log_channel']:
            return

        guild = self.bot.get_guild(guild_id)
        if not guild:
            return

        channel = guild.get_channel(settings['log_channel'])
        if not channel:
            return

        user = guild.get_member(user_id)

        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = (
            f"**Potential Selfbot Detected**\n\n"
            f"› User: {user.mention if user else f'<@{user_id}>'} (`{user_id}`)\n"
            f"› Score: `{score}/100`\n"
            f"› Reason: {reason}"
        )

        try:
            alert_content = ""
            if settings['alert_role']:
                role = guild.get_role(settings['alert_role'])
                if role:
                    alert_content = f"{role.mention}"

            await channel.send(content=alert_content, embed=embed)
        except:
            pass

    async def take_action(self, guild_id: int, user_id: int, reason: str):
        """Take action against a detected selfbot"""
        settings = await self.get_settings(guild_id)
        action = settings['action']

        if action == 'alert':
            return  # Already logged

        guild = self.bot.get_guild(guild_id)
        if not guild:
            return

        member = guild.get_member(user_id)
        if not member:
            return

        try:
            if action == 'mute':
                await member.timeout(timedelta(hours=1), reason=f"[AntiSelfbot] {reason}")
            elif action == 'kick':
                await member.kick(reason=f"[AntiSelfbot] {reason}")
            elif action == 'ban':
                await member.ban(reason=f"[AntiSelfbot] {reason}")

            logger.info(f'Selfbot action taken: {action} on {member}')
        except discord.Forbidden:
            logger.error(f'Cannot take action on {member} - missing permissions')

    # ==================== EVENT LISTENERS ====================

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Monitor messages for selfbot patterns"""
        if message.author.bot or not message.guild:
            return

        # NEVER touch messages from this bot
        if message.author.id == self.bot.user.id:
            return

        # Skip bot commands
        try:
            prefixes = await self.bot.get_prefix(message)
            if isinstance(prefixes, str):
                prefixes = [prefixes]
            if any(message.content.startswith(p) for p in prefixes):
                return
            # Also skip slash command style messages
            if message.content.startswith('/'):
                return
        except:
            pass

        # Run all checks
        await self.check_selfbot_commands(message)
        await self.check_nitro_sniping(message)
        await self.check_automation_patterns(message)
        await self.check_embed_spam(message)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Monitor reactions for impossibly fast additions"""
        if not payload.guild_id:
            return

        try:
            channel = self.bot.get_channel(payload.channel_id)
            if channel:
                message = await channel.fetch_message(payload.message_id)
                await self.check_fast_reaction(payload, message)
        except:
            pass

    # ==================== COMMANDS ====================

    @commands.hybrid_group(name='antiselfbot', aliases=['asb'], invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def antiselfbot(self, ctx: commands.Context):
        """Anti-Selfbot configuration commands"""
        if not await self.owner_check(ctx):
            return

        settings = await self.get_settings(ctx.guild.id)

        status = "enabled" if settings['enabled'] else "disabled"

        detections = []
        if settings['detect_fast_reactions']:
            detections.append("› Fast Reactions: `on`")
        else:
            detections.append("› Fast Reactions: `off`")
        if settings['detect_nitro_sniping']:
            detections.append("› Nitro Sniping: `on`")
        else:
            detections.append("› Nitro Sniping: `off`")
        if settings['detect_selfbot_commands']:
            detections.append("› Selfbot Commands: `on`")
        else:
            detections.append("› Selfbot Commands: `off`")
        if settings['detect_automation']:
            detections.append("› Automation Patterns: `on`")
        else:
            detections.append("› Automation Patterns: `off`")

        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = (
            f"**Anti-Selfbot Protection**\n\n"
            f"› Status: `{status}`\n"
            f"› Action: `{settings['action']}`\n"
            f"› Threshold: `{settings['suspicion_threshold']}`\n\n"
            f"**Detection Methods**\n" + "\n".join(detections)
        )

        await ctx.send(embed=embed)

    @antiselfbot.command(name='enable')
    @commands.has_permissions(administrator=True)
    async def antiselfbot_enable(self, ctx: commands.Context):
        """Enable anti-selfbot protection"""
        if not await self.owner_check(ctx):
            return

        settings = await self.get_settings(ctx.guild.id)
        settings['enabled'] = True
        await self.save_settings(ctx.guild.id)
        embed = discord.Embed(description="➕ Enabled anti-selfbot protection", color=EMBED_COLOR)
        await ctx.send(embed=embed)

    @antiselfbot.command(name='disable')
    @commands.has_permissions(administrator=True)
    async def antiselfbot_disable(self, ctx: commands.Context):
        """Disable anti-selfbot protection"""
        if not await self.owner_check(ctx):
            return

        settings = await self.get_settings(ctx.guild.id)
        settings['enabled'] = False
        await self.save_settings(ctx.guild.id)
        embed = discord.Embed(description="➖ Disabled anti-selfbot protection", color=EMBED_COLOR)
        await ctx.send(embed=embed)

    @antiselfbot.command(name='action')
    @commands.has_permissions(administrator=True)
    async def antiselfbot_action(self, ctx: commands.Context, action: str):
        """Set selfbot action (alert/mute/kick/ban)"""
        if not await self.owner_check(ctx):
            return

        valid = ['alert', 'mute', 'kick', 'ban']
        if action.lower() not in valid:
            embed = discord.Embed(description=f"✖️ Invalid action. Use: `{', '.join(valid)}`", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        settings = await self.get_settings(ctx.guild.id)
        settings['action'] = action.lower()
        await self.save_settings(ctx.guild.id)
        embed = discord.Embed(description=f"➕ Set selfbot action to `{action.lower()}`", color=EMBED_COLOR)
        await ctx.send(embed=embed)

    @antiselfbot.command(name='check')
    @commands.has_permissions(administrator=True)
    async def antiselfbot_check(self, ctx: commands.Context, member: discord.Member):
        """Check a user's suspicion score"""
        if not await self.owner_check(ctx):
            return

        tracker = self.get_tracker(ctx.guild.id, member.id)

        flagged_str = "yes" if tracker.flagged else "no"

        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = (
            f"**Selfbot Check: {member}**\n\n"
            f"› Score: `{tracker.suspicion_score}/100`\n"
            f"› Flagged: `{flagged_str}`\n"
            f"› Fast Reactions: `{len(tracker.fast_reactions)}`\n"
            f"› Nitro Attempts: `{len(tracker.nitro_attempts)}`\n"
            f"› Selfbot Commands: `{len(tracker.command_responses)}`"
        )

        await ctx.send(embed=embed)

    @antiselfbot.command(name='clear')
    @commands.has_permissions(administrator=True)
    async def antiselfbot_clear(self, ctx: commands.Context, member: discord.Member):
        """Clear a user's selfbot tracking data"""
        if not await self.owner_check(ctx):
            return

        self.trackers[ctx.guild.id][member.id] = SelfbotTracker()
        embed = discord.Embed(description=f"➕ Cleared selfbot tracking for {member.mention}", color=EMBED_COLOR)
        await ctx.send(embed=embed)

    @antiselfbot.command(name='setlog')
    @commands.has_permissions(administrator=True)
    async def antiselfbot_setlog(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set the selfbot detection log channel"""
        if not await self.owner_check(ctx):
            return

        settings = await self.get_settings(ctx.guild.id)
        settings['log_channel'] = channel.id
        await self.save_settings(ctx.guild.id)
        embed = discord.Embed(description=f"➕ Set selfbot log channel to {channel.mention}", color=EMBED_COLOR)
        await ctx.send(embed=embed)

    @antiselfbot.command(name='threshold')
    @commands.has_permissions(administrator=True)
    async def antiselfbot_threshold(self, ctx: commands.Context, value: int):
        """Set the suspicion threshold (0-100)"""
        if not await self.owner_check(ctx):
            return

        if value < 0 or value > 100:
            embed = discord.Embed(description="✖️ Threshold must be 0-100", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        settings = await self.get_settings(ctx.guild.id)
        settings['suspicion_threshold'] = value
        await self.save_settings(ctx.guild.id)
        embed = discord.Embed(description=f"➕ Set suspicion threshold to `{value}`", color=EMBED_COLOR)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(AntiSelfbot(bot))
