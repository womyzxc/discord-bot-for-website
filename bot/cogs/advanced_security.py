"""
Advanced Security Cog
=====================
Implements cutting-edge security features:
1. Role Hierarchy Protection - Prevent role hierarchy manipulation
2. API Abuse Detection - Detect abnormal API usage patterns
3. Behavioral Fingerprinting - Track user behavior patterns
4. Message Timing Analysis - Detect selfbots via timing
5. Token Compromise Detection - Detect hijacked accounts
6. Honeypot Channels/Roles - Trap systems for attackers
"""

import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Optional, Any, Tuple
import asyncio
import logging
import statistics
import hashlib
import json

logger = logging.getLogger('Offcialx.AdvancedSecurity')

# Minimal embed color
EMBED_COLOR = 0x2b2d31

# ==================== DATA STRUCTURES ====================

class UserBehaviorProfile:
    """Tracks behavioral patterns for a user"""

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.created_at = datetime.utcnow()

        # Message timing data
        self.message_timestamps: List[datetime] = []
        self.response_times: List[float] = []  # Time between trigger and response
        self.typing_durations: List[float] = []

        # Activity patterns
        self.active_hours: Dict[int, int] = defaultdict(int)  # Hour -> count
        self.active_days: Dict[int, int] = defaultdict(int)   # Weekday -> count
        self.average_messages_per_session: float = 0

        # Command/action patterns
        self.commands_used: Dict[str, int] = defaultdict(int)
        self.channels_active: Dict[int, int] = defaultdict(int)
        self.reaction_times: List[float] = []

        # Session tracking
        self.sessions: List[Dict] = []  # Start time, end time, message count
        self.current_session_start: Optional[datetime] = None
        self.current_session_messages: int = 0

        # Fingerprint
        self.fingerprint_hash: Optional[str] = None
        self.last_fingerprint_update: Optional[datetime] = None

        # Risk factors
        self.anomaly_score: float = 0
        self.flags: List[str] = []

    def add_message(self, timestamp: datetime, channel_id: int):
        """Record a message"""
        self.message_timestamps.append(timestamp)
        self.active_hours[timestamp.hour] += 1
        self.active_days[timestamp.weekday()] += 1
        self.channels_active[channel_id] += 1

        # Session tracking
        if self.current_session_start is None:
            self.current_session_start = timestamp
            self.current_session_messages = 1
        elif (timestamp - self.message_timestamps[-2]).total_seconds() > 1800:  # 30 min gap = new session
            # Save old session
            self.sessions.append({
                'start': self.current_session_start,
                'end': self.message_timestamps[-2],
                'messages': self.current_session_messages
            })
            self.current_session_start = timestamp
            self.current_session_messages = 1
        else:
            self.current_session_messages += 1

        # Keep only last 1000 timestamps
        if len(self.message_timestamps) > 1000:
            self.message_timestamps = self.message_timestamps[-1000:]

    def add_response_time(self, seconds: float):
        """Record response time to a trigger"""
        self.response_times.append(seconds)
        if len(self.response_times) > 100:
            self.response_times = self.response_times[-100:]

    def add_reaction_time(self, seconds: float):
        """Record reaction add time"""
        self.reaction_times.append(seconds)
        if len(self.reaction_times) > 100:
            self.reaction_times = self.reaction_times[-100:]

    def get_message_intervals(self) -> List[float]:
        """Get intervals between messages in seconds"""
        intervals = []
        for i in range(1, len(self.message_timestamps)):
            delta = (self.message_timestamps[i] - self.message_timestamps[i-1]).total_seconds()
            if delta < 300:  # Only count intervals < 5 min
                intervals.append(delta)
        return intervals

    def calculate_fingerprint(self) -> str:
        """Generate a behavioral fingerprint hash"""
        data = {
            'peak_hours': sorted(self.active_hours.items(), key=lambda x: x[1], reverse=True)[:3],
            'peak_days': sorted(self.active_days.items(), key=lambda x: x[1], reverse=True)[:2],
            'avg_interval': statistics.mean(self.get_message_intervals()) if self.get_message_intervals() else 0,
            'top_channels': sorted(self.channels_active.items(), key=lambda x: x[1], reverse=True)[:3],
        }
        fingerprint = hashlib.sha256(json.dumps(data, default=str).encode()).hexdigest()[:16]
        self.fingerprint_hash = fingerprint
        self.last_fingerprint_update = datetime.utcnow()
        return fingerprint

    def detect_anomalies(self, new_behavior: Dict) -> Tuple[float, List[str]]:
        """Compare new behavior against profile and return anomaly score"""
        flags = []
        score = 0

        # Check active hours deviation
        current_hour = datetime.utcnow().hour
        if self.active_hours:
            total_messages = sum(self.active_hours.values())
            hour_ratio = self.active_hours.get(current_hour, 0) / max(total_messages, 1)
            if hour_ratio < 0.02 and total_messages > 50:  # Less than 2% of activity at this hour
                flags.append(f"unusual_hour:{current_hour}")
                score += 20

        # Check message interval patterns
        intervals = self.get_message_intervals()
        if intervals and len(intervals) > 10:
            avg_interval = statistics.mean(intervals)
            std_interval = statistics.stdev(intervals) if len(intervals) > 1 else 0

            new_interval = new_behavior.get('interval', avg_interval)
            if std_interval > 0:
                z_score = abs(new_interval - avg_interval) / std_interval
                if z_score > 3:  # 3 standard deviations
                    flags.append(f"unusual_interval:{new_interval:.2f}s")
                    score += 15

        # Check response time (for selfbot detection)
        if self.response_times and len(self.response_times) > 5:
            avg_response = statistics.mean(self.response_times)
            if avg_response < 0.5:  # Less than 500ms average
                flags.append("fast_responses")
                score += 30

        self.anomaly_score = score
        self.flags = flags
        return score, flags


class APIUsageTracker:
    """Tracks API usage per user"""

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.actions: Dict[str, List[datetime]] = defaultdict(list)
        self.warnings: int = 0

    def add_action(self, action_type: str) -> int:
        """Add an action and return count in last minute"""
        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=1)

        # Clean old actions
        self.actions[action_type] = [t for t in self.actions[action_type] if t > cutoff]
        self.actions[action_type].append(now)

        return len(self.actions[action_type])

    def get_total_actions(self, seconds: int = 60) -> int:
        """Get total actions across all types in timeframe"""
        cutoff = datetime.utcnow() - timedelta(seconds=seconds)
        total = 0
        for action_list in self.actions.values():
            total += len([t for t in action_list if t > cutoff])
        return total


class HoneypotSystem:
    """Manages honeypot channels and roles"""

    def __init__(self):
        self.honeypot_channels: Dict[int, List[int]] = defaultdict(list)  # guild_id -> [channel_ids]
        self.honeypot_roles: Dict[int, List[int]] = defaultdict(list)      # guild_id -> [role_ids]
        self.triggered_users: Dict[int, Dict[int, datetime]] = defaultdict(dict)  # guild_id -> {user_id: timestamp}

    def add_honeypot_channel(self, guild_id: int, channel_id: int):
        if channel_id not in self.honeypot_channels[guild_id]:
            self.honeypot_channels[guild_id].append(channel_id)

    def add_honeypot_role(self, guild_id: int, role_id: int):
        if role_id not in self.honeypot_roles[guild_id]:
            self.honeypot_roles[guild_id].append(role_id)

    def is_honeypot_channel(self, guild_id: int, channel_id: int) -> bool:
        return channel_id in self.honeypot_channels.get(guild_id, [])

    def is_honeypot_role(self, guild_id: int, role_id: int) -> bool:
        return role_id in self.honeypot_roles.get(guild_id, [])

    def trigger(self, guild_id: int, user_id: int):
        self.triggered_users[guild_id][user_id] = datetime.utcnow()

    def was_triggered_by(self, guild_id: int, user_id: int) -> bool:
        return user_id in self.triggered_users.get(guild_id, {})


# ==================== MAIN COG ====================

class AdvancedSecurity(commands.Cog):
    """Advanced Security Features"""

    def __init__(self, bot):
        self.bot = bot
        self.db = None

        # Behavioral profiles per user
        self.user_profiles: Dict[int, UserBehaviorProfile] = {}

        # API usage tracking
        self.api_trackers: Dict[int, APIUsageTracker] = {}

        # Honeypot system
        self.honeypot = HoneypotSystem()

        # Token compromise detection
        self.user_locations: Dict[int, Dict] = {}  # user_id -> last known behavior
        self.compromise_alerts: Dict[int, List[datetime]] = defaultdict(list)

        # Role hierarchy cache
        self.role_hierarchy_cache: Dict[int, Dict[int, int]] = {}  # guild_id -> {role_id: position}

        # Message timing for selfbot detection
        self.pending_responses: Dict[int, Dict] = {}  # message_id -> {author_id, timestamp, trigger_words}

        # API abuse thresholds - ULTRA STRICT
        self.API_THRESHOLDS = {
            'message_edit': 5,       # 5 edits per minute (was 10)
            'message_delete': 8,     # 8 deletes per minute (was 15)
            'reaction_add': 10,      # 10 reactions per minute (was 20)
            'reaction_remove': 10,   # (was 20)
            'channel_edit': 2,       # 2 per minute (was 5) - VERY STRICT
            'role_edit': 2,          # 2 per minute (was 5) - VERY STRICT
            'nickname_change': 3,    # 3 per minute (was 5)
            'webhook_action': 1,     # INSTANT - 1 per minute (was 3)
            'total': 25              # 25 total per minute (was 50)
        }

        # Selfbot detection thresholds - ULTRA STRICT
        self.SELFBOT_THRESHOLDS = {
            'min_response_time': 0.5,      # 500ms minimum (was 300ms) - more strict
            'suspicious_response_time': 0.8,  # 800ms is suspicious (was 500ms)
            'consistent_timing_threshold': 0.2,  # 200ms variance (was 100ms)
            'max_messages_per_second': 2,  # Max 2 messages per second
            'min_typing_time': 0.5,        # Min 500ms between start typing and send
        }

        # Start background tasks
        self.cleanup_old_data.start()
        self.update_role_hierarchy_cache.start()

    def cog_unload(self):
        self.cleanup_old_data.cancel()
        self.update_role_hierarchy_cache.cancel()

    # ==================== HELPER METHODS ====================

    def get_user_profile(self, user_id: int) -> UserBehaviorProfile:
        """Get or create a user behavior profile"""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserBehaviorProfile(user_id)
        return self.user_profiles[user_id]

    def get_api_tracker(self, user_id: int) -> APIUsageTracker:
        """Get or create an API usage tracker"""
        if user_id not in self.api_trackers:
            self.api_trackers[user_id] = APIUsageTracker(user_id)
        return self.api_trackers[user_id]

    async def punish_user(self, guild: discord.Guild, user: discord.Member, reason: str, severity: str = "high"):
        """Punish a user based on severity"""
        try:
            if severity == "critical":
                await guild.ban(user, reason=f"[AdvancedSecurity] {reason}", delete_message_days=0)
                logger.warning(f"BANNED {user} in {guild.name}: {reason}")
            elif severity == "high":
                await user.edit(roles=[], reason=f"[AdvancedSecurity] {reason}")
                logger.warning(f"STRIPPED ROLES from {user} in {guild.name}: {reason}")
            else:
                # Just log and alert
                logger.info(f"FLAGGED {user} in {guild.name}: {reason}")

            # Send webhook notification
            if hasattr(self.bot, 'webhook_notifier') and self.bot.webhook_notifier:
                await self.bot.webhook_notifier.send_nuke_alert(
                    guild_name=guild.name,
                    guild_id=guild.id,
                    attacker_name=str(user),
                    attacker_id=user.id,
                    threat_type=reason.split(':')[0] if ':' in reason else reason,
                    action_taken="Banned" if severity == "critical" else "Roles Stripped" if severity == "high" else "Flagged",
                    details=reason
                )
        except discord.Forbidden:
            logger.error(f"Cannot punish {user} - missing permissions")
        except Exception as e:
            logger.error(f"Error punishing {user}: {e}")

    async def alert_admins(self, guild: discord.Guild, title: str, description: str, user: discord.Member = None):
        """Alert server admins about a security event"""
        # Find a log channel or alert the owner
        antinuke = self.bot.get_cog('AntiNuke')
        if antinuke:
            settings = await antinuke.get_settings(guild.id)
            log_channel_id = settings.get('log_channel_id')
            if log_channel_id:
                channel = guild.get_channel(log_channel_id)
                if channel:
                    user_info = f"\n› User: {user.mention} (`{user.id}`)" if user else ""
                    embed = discord.Embed(color=EMBED_COLOR)
                    embed.description = f"**{title}**\n\n{description}{user_info}"
                    await channel.send(embed=embed)

    # ==================== ROLE HIERARCHY PROTECTION ====================

    @tasks.loop(minutes=5)
    async def update_role_hierarchy_cache(self):
        """Cache role hierarchy for all guilds"""
        for guild in self.bot.guilds:
            self.role_hierarchy_cache[guild.id] = {
                role.id: role.position for role in guild.roles
            }

    @update_role_hierarchy_cache.before_loop
    async def before_hierarchy_cache(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        """Detect role hierarchy manipulation"""
        guild = after.guild

        # Get bot's highest role (needed for both position and permission checks)
        bot_member = guild.get_member(self.bot.user.id)
        if not bot_member:
            return

        bot_top_role = bot_member.top_role

        # Check if position changed
        if before.position != after.position:

            # Check if role was moved above bot
            if after.position >= bot_top_role.position and before.position < bot_top_role.position:
                # Someone moved a role above the bot - suspicious!
                async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_update):
                    if entry.target.id == after.id:
                        moderator = entry.user

                        # Don't flag the owner
                        if moderator.id == guild.owner_id:
                            return

                        logger.warning(f"ROLE HIERARCHY MANIPULATION: {moderator} moved {after.name} above bot in {guild.name}")

                        # Revert the change
                        try:
                            await after.edit(position=before.position, reason="[Security] Reverting unauthorized hierarchy change")
                        except:
                            pass

                        # Punish the user
                        member = guild.get_member(moderator.id)
                        if member:
                            await self.punish_user(guild, member, "Role Hierarchy Manipulation: Attempted to move role above security bot", "high")

                        await self.alert_admins(guild, "Role Hierarchy Attack Blocked",
                            f"{moderator.mention} tried to move **{after.name}** above the bot's role. This was reverted.", member)
                        break

        # Check if dangerous permissions were added to a high role
        dangerous_perms = ['administrator', 'manage_guild', 'manage_roles', 'ban_members', 'kick_members']
        before_perms = dict(before.permissions)
        after_perms = dict(after.permissions)

        for perm in dangerous_perms:
            if not before_perms.get(perm) and after_perms.get(perm):
                # Dangerous permission was added
                if after.position > bot_top_role.position - 3:  # Close to bot's role
                    async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_update):
                        if entry.target.id == after.id:
                            moderator = entry.user
                            if moderator.id != guild.owner_id:
                                logger.warning(f"DANGEROUS PERMISSION ADDED: {moderator} added {perm} to {after.name}")

                                # Revert
                                try:
                                    await after.edit(permissions=before.permissions, reason="[Security] Reverting dangerous permission change")
                                except:
                                    pass

                                await self.alert_admins(guild, "Dangerous Permission Blocked",
                                    f"{moderator.mention} tried to add `{perm}` to **{after.name}**. This was reverted.")
                            break

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        """Monitor for dangerous role creation"""
        guild = role.guild

        # Check if role has dangerous permissions
        dangerous_perms = ['administrator', 'manage_guild', 'manage_roles', 'ban_members', 'kick_members', 'manage_channels']
        has_dangerous = any(getattr(role.permissions, perm, False) for perm in dangerous_perms)

        if has_dangerous:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_create):
                if entry.target.id == role.id:
                    moderator = entry.user

                    if moderator.id == guild.owner_id or moderator.id == self.bot.user.id:
                        return

                    # Check if user is whitelisted
                    antinuke = self.bot.get_cog('AntiNuke')
                    if antinuke and antinuke.is_trusted(guild, moderator.id):
                        return

                    logger.warning(f"DANGEROUS ROLE CREATED: {moderator} created {role.name} with admin perms")

                    # Delete the role
                    try:
                        await role.delete(reason="[Security] Unauthorized dangerous role creation")
                    except:
                        pass

                    # Punish
                    member = guild.get_member(moderator.id)
                    if member:
                        await self.punish_user(guild, member, f"Created dangerous role: {role.name} with {', '.join(p for p in dangerous_perms if getattr(role.permissions, p, False))}", "high")
                    break

    # ==================== API ABUSE DETECTION ====================

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """Track message edits for API abuse"""
        if not after.guild or after.author.bot:
            return

        tracker = self.get_api_tracker(after.author.id)
        count = tracker.add_action('message_edit')

        if count >= self.API_THRESHOLDS['message_edit']:
            member = after.guild.get_member(after.author.id)
            if member:
                await self.punish_user(after.guild, member, f"API Abuse: {count} message edits in 1 minute", "medium")
                await self.alert_admins(after.guild, "API Abuse Detected",
                    f"User made {count} message edits in 1 minute (threshold: {self.API_THRESHOLDS['message_edit']})", member)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        """Track message deletions"""
        if not message.guild:
            return

        # Check who deleted it via audit log
        try:
            async for entry in message.guild.audit_logs(limit=1, action=discord.AuditLogAction.message_delete):
                if entry.target.id == message.author.id:
                    deleter = entry.user
                    if deleter.bot:
                        return

                    tracker = self.get_api_tracker(deleter.id)
                    count = tracker.add_action('message_delete')

                    if count >= self.API_THRESHOLDS['message_delete']:
                        member = message.guild.get_member(deleter.id)
                        if member:
                            await self.alert_admins(message.guild, "High Message Deletion Rate",
                                f"User deleted {count} messages in 1 minute", member)
                    break
        except:
            pass

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        """Track reaction additions"""
        if not reaction.message.guild or user.bot:
            return

        tracker = self.get_api_tracker(user.id)
        count = tracker.add_action('reaction_add')

        # Also track for behavioral fingerprinting
        profile = self.get_user_profile(user.id)
        # Estimate reaction time (not perfect but indicative)
        msg_age = (datetime.utcnow() - reaction.message.created_at.replace(tzinfo=None)).total_seconds()
        if msg_age < 60:  # Only track recent reactions
            profile.add_reaction_time(msg_age)

        if count >= self.API_THRESHOLDS['reaction_add']:
            member = reaction.message.guild.get_member(user.id)
            if member:
                await self.alert_admins(reaction.message.guild, "Reaction Spam Detected",
                    f"User added {count} reactions in 1 minute", member)

    # ==================== BEHAVIORAL FINGERPRINTING ====================

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Track message patterns for behavioral fingerprinting"""
        if not message.guild or message.author.bot:
            return

        # NEVER track this bot's own messages
        if message.author.id == self.bot.user.id:
            return

        # Skip command messages
        if message.content.startswith('!') or message.content.startswith('/'):
            return

        profile = self.get_user_profile(message.author.id)
        now = datetime.utcnow()

        # Record message
        profile.add_message(now, message.channel.id)

        # Track command usage
        if message.content.startswith('!') or message.content.startswith('/'):
            cmd = message.content.split()[0] if message.content.split() else ''
            profile.commands_used[cmd] += 1

        # Check for anomalies
        intervals = profile.get_message_intervals()
        if len(intervals) > 20:
            last_interval = intervals[-1] if intervals else 10
            score, flags = profile.detect_anomalies({'interval': last_interval})

            if score >= 50:
                await self.alert_admins(message.guild, "Behavioral Anomaly Detected",
                    f"Anomaly score: {score}\nFlags: {', '.join(flags)}", message.author)

        # Store for response time tracking (selfbot detection)
        # Track mentions and replies
        if message.mentions or message.reference:
            self.pending_responses[message.id] = {
                'timestamp': now,
                'mentions': [u.id for u in message.mentions],
                'reply_to': message.reference.message_id if message.reference else None
            }

    # ==================== MESSAGE TIMING ANALYSIS (SELFBOT DETECTION) ====================

    @commands.Cog.listener()
    async def on_message_for_timing(self, message: discord.Message):
        """Analyze message timing for selfbot detection"""
        if not message.guild or message.author.bot:
            return

        now = datetime.utcnow()
        profile = self.get_user_profile(message.author.id)

        # Check if this is a response to a tracked message
        if message.reference and message.reference.message_id in self.pending_responses:
            original = self.pending_responses[message.reference.message_id]
            response_time = (now - original['timestamp']).total_seconds()

            profile.add_response_time(response_time)

            # Check for inhuman response times
            if response_time < self.SELFBOT_THRESHOLDS['min_response_time']:
                logger.warning(f"SELFBOT SUSPECTED: {message.author} responded in {response_time:.3f}s")
                profile.flags.append(f"inhuman_response:{response_time:.3f}s")

                # Check pattern
                if len(profile.response_times) >= 5:
                    avg = statistics.mean(profile.response_times[-5:])
                    if avg < self.SELFBOT_THRESHOLDS['suspicious_response_time']:
                        await self.alert_admins(message.guild, "Possible Selfbot Detected",
                            f"Average response time: {avg:.3f}s (last 5 messages)\nThis is faster than humanly possible.", message.author)

        # Check for consistent timing (bots often have very consistent intervals)
        intervals = profile.get_message_intervals()
        if len(intervals) >= 10:
            recent_intervals = intervals[-10:]
            try:
                std_dev = statistics.stdev(recent_intervals)
                mean_interval = statistics.mean(recent_intervals)

                # Very low standard deviation with short intervals = likely bot
                if std_dev < self.SELFBOT_THRESHOLDS['consistent_timing_threshold'] and mean_interval < 2:
                    logger.warning(f"SELFBOT PATTERN: {message.author} has suspiciously consistent timing (std: {std_dev:.3f}s)")
                    await self.alert_admins(message.guild, "Suspicious Message Pattern",
                        f"Message timing is suspiciously consistent:\n- Std Dev: {std_dev:.3f}s\n- Mean Interval: {mean_interval:.2f}s", message.author)
            except:
                pass

    # ==================== TOKEN COMPROMISE DETECTION ====================

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """Detect potential token compromise via behavior changes"""
        if after.bot:
            return

        profile = self.get_user_profile(after.id)
        user_id = after.id

        # Check for sudden permission escalation
        before_perms = before.guild_permissions
        after_perms = after.guild_permissions

        dangerous_gained = []
        for perm in ['administrator', 'manage_guild', 'ban_members', 'kick_members', 'manage_roles']:
            if not getattr(before_perms, perm) and getattr(after_perms, perm):
                dangerous_gained.append(perm)

        if dangerous_gained:
            # Check if this is unusual for this user
            now = datetime.utcnow()

            if user_id in self.user_locations:
                last_activity = self.user_locations[user_id]
                time_since_last = (now - last_activity.get('timestamp', now)).total_seconds()

                # If they were inactive and suddenly gained perms, suspicious
                if time_since_last > 3600:  # 1 hour inactive
                    await self.alert_admins(after.guild, "Potential Token Compromise",
                        f"User was inactive for {time_since_last/3600:.1f} hours and suddenly gained permissions: {', '.join(dangerous_gained)}", after)

            self.user_locations[user_id] = {
                'timestamp': now,
                'permissions': list(after.guild_permissions),
            }

    @commands.Cog.listener()
    async def on_user_update(self, before: discord.User, after: discord.User):
        """Detect account changes that might indicate compromise"""
        # Avatar change + name change at once is suspicious
        changes = []
        if before.avatar != after.avatar:
            changes.append("avatar")
        if before.name != after.name:
            changes.append("username")
        if before.discriminator != after.discriminator:
            changes.append("discriminator")

        if len(changes) >= 2:
            logger.info(f"Multiple account changes for {after}: {changes}")
            # Could alert guilds this user is in

    # ==================== HONEYPOT CHANNELS/ROLES ====================

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        """Check if honeypot channel was deleted"""
        guild = channel.guild

        if self.honeypot.is_honeypot_channel(guild.id, channel.id):
            # HONEYPOT TRIGGERED!
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
                if entry.target.id == channel.id:
                    attacker = entry.user

                    if attacker.id == self.bot.user.id or attacker.id == guild.owner_id:
                        return

                    logger.critical(f"HONEYPOT TRIGGERED: {attacker} deleted honeypot channel in {guild.name}")
                    self.honeypot.trigger(guild.id, attacker.id)

                    member = guild.get_member(attacker.id)
                    if member:
                        await self.punish_user(guild, member, "HONEYPOT TRIGGERED: Deleted trap channel - Confirmed attacker", "critical")

                    await self.alert_admins(guild, "HONEYPOT TRAP TRIGGERED",
                        f"**{attacker}** deleted a honeypot channel. Confirmed malicious intent. User has been banned.", member)
                    break

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        """Check if honeypot channel was modified"""
        guild = after.guild

        if self.honeypot.is_honeypot_channel(guild.id, after.id):
            # Check what changed
            if before.name != after.name or before.category != after.category:
                async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_update):
                    if entry.target.id == after.id:
                        attacker = entry.user

                        if attacker.id == self.bot.user.id or attacker.id == guild.owner_id:
                            return

                        logger.warning(f"HONEYPOT TOUCHED: {attacker} modified honeypot channel in {guild.name}")

                        # Revert the change
                        try:
                            await after.edit(name=before.name, category=before.category, reason="[Security] Reverting honeypot modification")
                        except:
                            pass

                        member = guild.get_member(attacker.id)
                        await self.alert_admins(guild, "Honeypot Channel Modified",
                            f"**{attacker}** modified a honeypot channel. This is suspicious behavior.", member)
                        break

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        """Check if honeypot role was deleted"""
        guild = role.guild

        if self.honeypot.is_honeypot_role(guild.id, role.id):
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
                if entry.target.id == role.id:
                    attacker = entry.user

                    if attacker.id == self.bot.user.id or attacker.id == guild.owner_id:
                        return

                    logger.critical(f"HONEYPOT TRIGGERED: {attacker} deleted honeypot role in {guild.name}")
                    self.honeypot.trigger(guild.id, attacker.id)

                    member = guild.get_member(attacker.id)
                    if member:
                        await self.punish_user(guild, member, "HONEYPOT TRIGGERED: Deleted trap role - Confirmed attacker", "critical")

                    await self.alert_admins(guild, "HONEYPOT TRAP TRIGGERED",
                        f"**{attacker}** deleted a honeypot role. Confirmed malicious intent. User has been banned.", member)
                    break

    # ==================== COMMANDS ====================

    @commands.group(name='security', aliases=['sec'], invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def security(self, ctx):
        """Advanced security commands"""
        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = (
            "**Advanced Security System**\n\n"
            "**Features**\n"
            "› Role Hierarchy Protection\n"
            "› API Abuse Detection\n"
            "› Behavioral Fingerprinting\n"
            "› Message Timing Analysis\n"
            "› Token Compromise Detection\n"
            "› Honeypot System\n\n"
            "**Commands**\n"
            "› `!security honeypot create channel`\n"
            "› `!security honeypot create role`\n"
            "› `!security honeypot list`\n"
            "› `!security profile @user`\n"
            "› `!security scan @user`"
        )
        await ctx.send(embed=embed)

    @security.group(name='honeypot', aliases=['hp'], invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def honeypot_cmd(self, ctx):
        """Honeypot management"""
        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = (
            "**Honeypot System**\n\n"
            "Create trap channels and roles that catch attackers instantly.\n\n"
            "**How it works**\n"
            "Honeypots are hidden channels/roles that normal users never interact with. "
            "If anyone deletes or modifies them, they're instantly flagged as an attacker.\n\n"
            "**Commands**\n"
            "› `!security honeypot create channel`\n"
            "› `!security honeypot create role`\n"
            "› `!security honeypot list`\n"
            "› `!security honeypot remove <id>`"
        )
        await ctx.send(embed=embed)

    @honeypot_cmd.command(name='create')
    @commands.has_permissions(administrator=True)
    async def honeypot_create(self, ctx, type: str):
        """Create a honeypot channel or role"""
        guild = ctx.guild

        if type.lower() == 'channel':
            # Create a hidden honeypot channel
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False),
                guild.me: discord.PermissionOverwrite(view_channel=True, manage_channels=True)
            }

            channel = await guild.create_text_channel(
                name="do-not-delete",
                overwrites=overwrites,
                reason="[Security] Creating honeypot channel",
                topic="SECURITY: This channel is a honeypot. Do not delete."
            )

            self.honeypot.add_honeypot_channel(guild.id, channel.id)

            embed = discord.Embed(color=EMBED_COLOR)
            embed.description = f"+ Created honeypot channel: {channel.mention}\n\nAnyone who deletes this channel will be instantly banned."
            await ctx.send(embed=embed)

        elif type.lower() == 'role':
            # Create a honeypot role
            role = await guild.create_role(
                name="[Security] Do Not Delete",
                permissions=discord.Permissions.none(),
                color=discord.Color.default(),
                reason="[Security] Creating honeypot role"
            )

            # Move it to the bottom
            await role.edit(position=1)

            self.honeypot.add_honeypot_role(guild.id, role.id)

            embed = discord.Embed(color=EMBED_COLOR)
            embed.description = f"+ Created honeypot role: {role.mention}\n\nAnyone who deletes this role will be instantly banned."
            await ctx.send(embed=embed)

        else:
            embed = discord.Embed(description="✕ Invalid type. Use `channel` or `role`", color=EMBED_COLOR)
            await ctx.send(embed=embed)

    @honeypot_cmd.command(name='list')
    @commands.has_permissions(administrator=True)
    async def honeypot_list(self, ctx):
        """List all honeypots in this server"""
        guild = ctx.guild

        channels = self.honeypot.honeypot_channels.get(guild.id, [])
        roles = self.honeypot.honeypot_roles.get(guild.id, [])

        if not channels and not roles:
            embed = discord.Embed(description="No honeypots configured. Use `!security honeypot create channel/role`", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        desc = "**Honeypot List**\n\n"

        if channels:
            desc += f"**Channels** `{len(channels)}`\n"
            for ch_id in channels:
                ch = guild.get_channel(ch_id)
                desc += f"› {ch.mention if ch else f'`{ch_id}` (deleted)'}\n"

        if roles:
            desc += f"\n**Roles** `{len(roles)}`\n"
            for r_id in roles:
                r = guild.get_role(r_id)
                desc += f"› {r.mention if r else f'`{r_id}` (deleted)'}\n"

        embed = discord.Embed(description=desc, color=EMBED_COLOR)
        await ctx.send(embed=embed)

    @security.command(name='profile')
    @commands.has_permissions(administrator=True)
    async def security_profile(self, ctx, member: discord.Member):
        """View a user's behavioral profile"""
        profile = self.get_user_profile(member.id)

        desc = f"**Behavioral Profile: {member}**\n\n"

        # Message stats
        msg_count = len(profile.message_timestamps)
        desc += f"› Messages Tracked: `{msg_count}`\n"

        # Active hours
        if profile.active_hours:
            peak_hour = max(profile.active_hours.items(), key=lambda x: x[1])[0]
            desc += f"› Peak Activity Hour: `{peak_hour}:00 UTC`\n"

        # Response times
        if profile.response_times:
            avg_response = statistics.mean(profile.response_times)
            desc += f"› Avg Response Time: `{avg_response:.2f}s`\n"

        # Message intervals
        intervals = profile.get_message_intervals()
        if intervals:
            avg_interval = statistics.mean(intervals)
            desc += f"› Avg Message Interval: `{avg_interval:.2f}s`\n"

        # Anomaly score
        score_symbol = "+" if profile.anomaly_score < 20 else "−" if profile.anomaly_score < 50 else "✕"
        desc += f"› Anomaly Score: {score_symbol} `{profile.anomaly_score}`\n"

        # Flags
        if profile.flags:
            desc += f"\n**Flags**\n› " + "\n› ".join(profile.flags)

        # Fingerprint
        fingerprint = profile.calculate_fingerprint()
        desc += f"\n\n› Fingerprint: `{fingerprint}`"

        embed = discord.Embed(description=desc, color=EMBED_COLOR)
        embed.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=embed)

    @security.command(name='scan')
    @commands.has_permissions(administrator=True)
    async def security_scan(self, ctx, member: discord.Member):
        """Scan a user for suspicious activity"""
        profile = self.get_user_profile(member.id)
        api_tracker = self.get_api_tracker(member.id)

        issues = []
        warnings = []

        # Check response times
        if profile.response_times and len(profile.response_times) >= 3:
            avg = statistics.mean(profile.response_times)
            if avg < 0.5:
                issues.append(f"✕ **Selfbot Suspected**: Average response time is {avg:.3f}s (inhuman)")
            elif avg < 1.0:
                warnings.append(f"Response time is fast ({avg:.2f}s)")

        # Check message timing consistency
        intervals = profile.get_message_intervals()
        if len(intervals) >= 10:
            try:
                std = statistics.stdev(intervals[-10:])
                if std < 0.2:
                    issues.append(f"✕ **Bot-like Timing**: Message intervals too consistent (std: {std:.3f}s)")
            except:
                pass

        # Check API usage
        total_actions = api_tracker.get_total_actions(300)  # Last 5 minutes
        if total_actions > 100:
            issues.append(f"✕ **High API Usage**: {total_actions} actions in 5 minutes")
        elif total_actions > 50:
            warnings.append(f"Elevated API usage ({total_actions} actions in 5 minutes)")

        # Check anomaly score
        if profile.anomaly_score >= 50:
            issues.append(f"✕ **High Anomaly Score**: {profile.anomaly_score}")
        elif profile.anomaly_score >= 20:
            warnings.append(f"Elevated anomaly score ({profile.anomaly_score})")

        # Check if triggered honeypot
        if self.honeypot.was_triggered_by(ctx.guild.id, member.id):
            issues.append("✕ **HONEYPOT TRIGGERED**: User touched a trap channel/role!")

        # Build description
        desc = f"**Security Scan: {member}**\n\n"

        if issues:
            desc += "**Issues Found**\n" + "\n".join(issues) + "\n\n"

        if warnings:
            desc += "**Warnings**\n› " + "\n› ".join(warnings) + "\n\n"

        if not issues and not warnings:
            desc += "+ No suspicious activity detected\n\n"

        if issues:
            desc += "**Recommendation**\n› Consider investigating this user or restricting permissions"

        embed = discord.Embed(description=desc, color=EMBED_COLOR)
        await ctx.send(embed=embed)

    # ==================== BACKGROUND TASKS ====================

    @tasks.loop(hours=1)
    async def cleanup_old_data(self):
        """Clean up old tracking data"""
        cutoff = datetime.utcnow() - timedelta(days=7)

        # Clean old message timestamps
        for profile in self.user_profiles.values():
            profile.message_timestamps = [t for t in profile.message_timestamps if t > cutoff]

        # Clean old pending responses
        old_cutoff = datetime.utcnow() - timedelta(minutes=5)
        self.pending_responses = {
            k: v for k, v in self.pending_responses.items()
            if v['timestamp'] > old_cutoff
        }

        logger.info("Cleaned up old security tracking data")

    @cleanup_old_data.before_loop
    async def before_cleanup(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(AdvancedSecurity(bot))
