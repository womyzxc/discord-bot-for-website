"""
AI-Powered Threat Intelligence Cog
===================================
Advanced threat detection using pattern analysis:
- Behavioral pattern recognition
- Cross-server threat intelligence
- Anomaly detection
- Risk scoring
- Predictive threat analysis
"""

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio
import logging
import hashlib
import statistics
from typing import Dict, List, Optional, Tuple
import re

logger = logging.getLogger('Offcialx.ThreatIntel')

# Minimal embed color
EMBED_COLOR = 0x2b2d31

class BehaviorProfile:
    """User behavior profile for pattern analysis"""

    def __init__(self, user_id: int):
        self.user_id = user_id
        self.actions: List[Dict] = []
        self.message_timestamps: List[datetime] = []
        self.command_usage: Dict[str, int] = defaultdict(int)
        self.action_velocity: List[float] = []
        self.anomaly_score: float = 0.0
        self.threat_indicators: List[str] = []
        self.last_analysis: Optional[datetime] = None

    def add_action(self, action_type: str, details: str = None):
        """Record an action"""
        now = datetime.utcnow()
        self.actions.append({
            'type': action_type,
            'details': details,
            'time': now
        })

        # Calculate velocity if we have previous actions
        if len(self.actions) >= 2:
            time_diff = (now - self.actions[-2]['time']).total_seconds()
            if time_diff > 0:
                self.action_velocity.append(1 / time_diff)  # Actions per second

        # Keep only recent actions (last hour)
        cutoff = now - timedelta(hours=1)
        self.actions = [a for a in self.actions if a['time'] > cutoff]
        self.action_velocity = self.action_velocity[-100:]  # Keep last 100 velocities

class ThreatPattern:
    """Represents a known threat pattern"""

    def __init__(self, name: str, pattern_type: str, indicators: List[str],
                 severity: int = 50, description: str = ""):
        self.name = name
        self.pattern_type = pattern_type
        self.indicators = indicators
        self.severity = severity
        self.description = description

    def matches(self, profile: BehaviorProfile) -> Tuple[bool, int]:
        """Check if profile matches this pattern, return (matches, confidence)"""
        matches = 0
        for indicator in self.indicators:
            if indicator in profile.threat_indicators:
                matches += 1

        if matches == 0:
            return False, 0

        confidence = int((matches / len(self.indicators)) * 100)
        return confidence >= 50, confidence

class ThreatIntelligence(commands.Cog):
    """AI-Powered Threat Intelligence System"""

    def __init__(self, bot):
        self.bot = bot
        self.db = None  # Will be set when database is loaded

        # User behavior profiles: guild_id -> user_id -> BehaviorProfile
        self.profiles: Dict[int, Dict[int, BehaviorProfile]] = defaultdict(dict)

        # Known threat patterns
        self.threat_patterns = self._init_threat_patterns()

        # Cross-server threat cache
        self.global_threats: Dict[int, Dict] = {}

        # Anomaly thresholds
        self.thresholds = {
            'action_velocity': 5.0,  # Actions per second
            'permission_changes': 3,  # In 5 minutes
            'role_modifications': 5,  # In 5 minutes
            'channel_operations': 3,  # In 5 minutes
            'message_rate': 10,  # Messages per 5 seconds
            'command_spam': 5,  # Same command in 10 seconds
        }

        # Guild settings
        self.guild_settings: Dict[int, Dict] = {}

    def _init_threat_patterns(self) -> List[ThreatPattern]:
        """Initialize known threat patterns"""
        return [
            ThreatPattern(
                "nuke_attempt",
                "destructive",
                ["mass_ban", "mass_kick", "channel_delete", "role_delete", "high_velocity"],
                severity=100,
                description="Server destruction attempt detected"
            ),
            ThreatPattern(
                "raid_leader",
                "coordinated",
                ["mass_invite", "rapid_joins", "coordinated_timing", "new_accounts"],
                severity=90,
                description="Raid coordination detected"
            ),
            ThreatPattern(
                "privilege_escalation",
                "infiltration",
                ["role_self_assign", "permission_modify", "admin_role_create"],
                severity=85,
                description="Privilege escalation attempt"
            ),
            ThreatPattern(
                "selfbot",
                "automation",
                ["fast_reaction", "automated_response", "nitro_snipe", "consistent_timing"],
                severity=70,
                description="Selfbot/automation detected"
            ),
            ThreatPattern(
                "spam_bot",
                "spam",
                ["message_flood", "duplicate_content", "link_spam", "mention_spam"],
                severity=60,
                description="Spam bot behavior"
            ),
            ThreatPattern(
                "account_compromise",
                "compromise",
                ["behavior_change", "unusual_activity", "login_anomaly", "new_ip"],
                severity=75,
                description="Possible account compromise"
            ),
            ThreatPattern(
                "phishing",
                "social_engineering",
                ["dm_spam", "fake_nitro", "credential_request", "impersonation"],
                severity=80,
                description="Phishing attempt detected"
            ),
        ]

    async def get_settings(self, guild_id: int) -> Dict:
        """Get guild settings"""
        if guild_id not in self.guild_settings:
            self.guild_settings[guild_id] = {
                'enabled': True,
                'auto_action': True,
                'min_threat_score': 50,
                'alert_channel': None,
                'share_intel': True,  # Share threat data cross-server
                'predictive_blocking': False,  # Block users based on global intel
                'log_all_analysis': False,
            }
        return self.guild_settings[guild_id]

    def get_profile(self, guild_id: int, user_id: int) -> BehaviorProfile:
        """Get or create behavior profile for a user"""
        if user_id not in self.profiles[guild_id]:
            self.profiles[guild_id][user_id] = BehaviorProfile(user_id)
        return self.profiles[guild_id][user_id]

    async def analyze_behavior(self, guild_id: int, user_id: int) -> Dict:
        """Perform comprehensive behavior analysis"""
        profile = self.get_profile(guild_id, user_id)
        now = datetime.utcnow()

        # Skip if recently analyzed
        if profile.last_analysis and (now - profile.last_analysis).seconds < 60:
            return {
                'threat_score': profile.anomaly_score,
                'indicators': profile.threat_indicators,
                'patterns': []
            }

        profile.last_analysis = now
        profile.threat_indicators = []

        # Analyze action velocity
        if profile.action_velocity:
            avg_velocity = statistics.mean(profile.action_velocity)
            if avg_velocity > self.thresholds['action_velocity']:
                profile.threat_indicators.append('high_velocity')

        # Analyze action patterns
        action_counts = defaultdict(int)
        recent_actions = [a for a in profile.actions
                         if (now - a['time']).seconds < 300]  # Last 5 minutes

        for action in recent_actions:
            action_counts[action['type']] += 1

        # Check for mass actions
        if action_counts.get('ban', 0) >= 3:
            profile.threat_indicators.append('mass_ban')
        if action_counts.get('kick', 0) >= 3:
            profile.threat_indicators.append('mass_kick')
        if action_counts.get('channel_delete', 0) >= 2:
            profile.threat_indicators.append('channel_delete')
        if action_counts.get('role_delete', 0) >= 2:
            profile.threat_indicators.append('role_delete')
        if action_counts.get('permission_change', 0) >= self.thresholds['permission_changes']:
            profile.threat_indicators.append('permission_modify')

        # Check for automation patterns
        if profile.action_velocity:
            # Low variance in timing suggests automation
            if len(profile.action_velocity) >= 5:
                try:
                    variance = statistics.variance(profile.action_velocity)
                    if variance < 0.1:
                        profile.threat_indicators.append('consistent_timing')
                        profile.threat_indicators.append('automated_response')
                except:
                    pass

        # Pattern matching
        matched_patterns = []
        for pattern in self.threat_patterns:
            matches, confidence = pattern.matches(profile)
            if matches:
                matched_patterns.append({
                    'name': pattern.name,
                    'type': pattern.pattern_type,
                    'confidence': confidence,
                    'severity': pattern.severity,
                    'description': pattern.description
                })

        # Calculate threat score
        base_score = len(profile.threat_indicators) * 10
        pattern_score = sum(p['severity'] * p['confidence'] / 100 for p in matched_patterns)
        profile.anomaly_score = min(base_score + pattern_score, 100)

        return {
            'threat_score': profile.anomaly_score,
            'indicators': profile.threat_indicators,
            'patterns': matched_patterns
        }

    async def report_threat(self, guild: discord.Guild, user_id: int,
                           threat_type: str, evidence: str = None):
        """Report a threat to the intelligence database"""
        settings = await self.get_settings(guild.id)

        # Update local cache
        if user_id not in self.global_threats:
            self.global_threats[user_id] = {
                'threat_types': [],
                'guild_ids': [],
                'total_score': 0,
                'first_seen': datetime.utcnow(),
                'last_seen': datetime.utcnow()
            }

        threat_data = self.global_threats[user_id]
        if threat_type not in threat_data['threat_types']:
            threat_data['threat_types'].append(threat_type)
        if guild.id not in threat_data['guild_ids']:
            threat_data['guild_ids'].append(guild.id)
        threat_data['total_score'] += 10
        threat_data['last_seen'] = datetime.utcnow()

        # Save to database if available
        if self.db:
            await self.db.add_threat_intel(
                user_id=user_id,
                threat_type=threat_type,
                threat_score=10,
                evidence=evidence,
                guild_id=guild.id
            )

        logger.warning(f'Threat reported: {threat_type} for user {user_id} in {guild.name}')

        # Alert if configured
        if settings['alert_channel']:
            await self.send_threat_alert(guild, user_id, threat_type, evidence)

    async def send_threat_alert(self, guild: discord.Guild, user_id: int,
                               threat_type: str, evidence: str = None):
        """Send threat alert to configured channel"""
        settings = await self.get_settings(guild.id)

        if not settings['alert_channel']:
            return

        channel = guild.get_channel(settings['alert_channel'])
        if not channel:
            return

        user = guild.get_member(user_id) or await self.bot.fetch_user(user_id)
        analysis = await self.analyze_behavior(guild.id, user_id)

        indicators_str = ""
        if analysis['indicators']:
            indicators_str = "\n› Indicators: " + ", ".join(i.replace('_', ' ').title() for i in analysis['indicators'][:10])

        patterns_str = ""
        if analysis['patterns']:
            patterns_str = "\n\n**Matched Patterns**\n" + "\n".join(
                f"› **{p['name'].replace('_', ' ').title()}** ({p['confidence']}%)"
                for p in analysis['patterns'][:5]
            )

        evidence_str = f"\n\n**Evidence**\n{evidence[:500]}" if evidence else ""

        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = (
            f"**Threat Intelligence Alert**\n\n"
            f"› User: {user.mention if isinstance(user, discord.Member) else f'<@{user_id}>'} (`{user_id}`)\n"
            f"› Type: {threat_type.replace('_', ' ').title()}\n"
            f"› Threat Score: `{analysis['threat_score']:.1f}/100`{indicators_str}{patterns_str}{evidence_str}"
        )

        try:
            await channel.send(embed=embed)
        except:
            pass

    async def check_global_threat(self, user_id: int) -> Optional[Dict]:
        """Check if user is a known global threat"""
        if user_id in self.global_threats:
            return self.global_threats[user_id]

        # Check database
        if self.db:
            intel = await self.db.get_threat_intel(user_id)
            if intel:
                total_score = sum(i['threat_score'] for i in intel)
                if total_score >= 50:
                    return {
                        'threat_types': [i['threat_type'] for i in intel],
                        'total_score': total_score,
                        'records': intel
                    }

        return None

    # ==================== EVENT LISTENERS ====================

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Check new members against threat intelligence"""
        settings = await self.get_settings(member.guild.id)

        if not settings['enabled']:
            return

        # Check global threats
        threat_data = await self.check_global_threat(member.id)

        if threat_data and threat_data.get('total_score', 0) >= settings['min_threat_score']:
            await self.send_threat_alert(
                member.guild,
                member.id,
                'known_threat_joined',
                f"Known threat with score {threat_data['total_score']} joined. "
                f"Threat types: {', '.join(threat_data.get('threat_types', []))}"
            )

            # Auto-action if enabled
            if settings['predictive_blocking'] and threat_data['total_score'] >= 80:
                try:
                    await member.ban(reason=f"[ThreatIntel] Known threat (score: {threat_data['total_score']})")
                    logger.info(f'Auto-banned known threat {member} in {member.guild.name}')
                except:
                    pass

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """Track role changes for threat analysis"""
        if before.roles == after.roles:
            return

        settings = await self.get_settings(after.guild.id)
        if not settings['enabled']:
            return

        # Check for dangerous permission gains
        dangerous_perms = ['administrator', 'ban_members', 'kick_members',
                         'manage_channels', 'manage_guild', 'manage_roles']

        for role in after.roles:
            if role not in before.roles:
                perms = dict(role.permissions)
                for perm in dangerous_perms:
                    if perms.get(perm, False):
                        profile = self.get_profile(after.guild.id, after.id)
                        profile.add_action('dangerous_permission_gain', f'Gained {perm} via {role.name}')
                        break

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        """Track channel deletions"""
        guild = channel.guild
        settings = await self.get_settings(guild.id)

        if not settings['enabled']:
            return

        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
            if entry.target.id == channel.id:
                profile = self.get_profile(guild.id, entry.user.id)
                profile.add_action('channel_delete', f'Deleted #{channel.name}')

                # Analyze immediately
                analysis = await self.analyze_behavior(guild.id, entry.user.id)

                if analysis['threat_score'] >= 50:
                    await self.report_threat(
                        guild, entry.user.id, 'channel_deletion',
                        f"Deleted channel: {channel.name}"
                    )
                break

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        """Track role deletions"""
        guild = role.guild
        settings = await self.get_settings(guild.id)

        if not settings['enabled']:
            return

        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.role_delete):
            if entry.target.id == role.id:
                profile = self.get_profile(guild.id, entry.user.id)
                profile.add_action('role_delete', f'Deleted @{role.name}')

                analysis = await self.analyze_behavior(guild.id, entry.user.id)

                if analysis['threat_score'] >= 50:
                    await self.report_threat(
                        guild, entry.user.id, 'role_deletion',
                        f"Deleted role: {role.name}"
                    )
                break

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        """Track bans"""
        settings = await self.get_settings(guild.id)

        if not settings['enabled']:
            return

        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
            if entry.target.id == user.id:
                if entry.user.id == self.bot.user.id:
                    return  # Skip bot actions

                profile = self.get_profile(guild.id, entry.user.id)
                profile.add_action('ban', f'Banned {user}')

                analysis = await self.analyze_behavior(guild.id, entry.user.id)

                if analysis['threat_score'] >= 50:
                    await self.report_threat(
                        guild, entry.user.id, 'mass_ban_attempt',
                        f"Multiple bans detected"
                    )
                break

    # ==================== SLASH COMMANDS ====================

    @app_commands.command(name='threatscan', description='Scan a user for threat indicators')
    @app_commands.describe(user='The user to scan')
    @app_commands.default_permissions(administrator=True)
    async def threat_scan(self, interaction: discord.Interaction, user: discord.Member):
        """Scan a user for threats"""
        await interaction.response.defer(ephemeral=True)

        analysis = await self.analyze_behavior(interaction.guild.id, user.id)
        global_threat = await self.check_global_threat(user.id)

        # Risk level
        if analysis['threat_score'] >= 75:
            risk_level = "HIGH RISK"
        elif analysis['threat_score'] >= 50:
            risk_level = "MEDIUM RISK"
        elif analysis['threat_score'] >= 25:
            risk_level = "LOW RISK"
        else:
            risk_level = "MINIMAL RISK"

        global_str = ""
        if global_threat:
            global_str = (
                f"\n\n**Global Intelligence**\n"
                f"› Known in {len(global_threat.get('guild_ids', []))} servers\n"
                f"› Global score: `{global_threat.get('total_score', 0)}`"
            )

        indicators_str = "None detected"
        if analysis['indicators']:
            indicators_str = "\n".join(f"› {i.replace('_', ' ').title()}" for i in analysis['indicators'][:10])

        patterns_str = ""
        if analysis['patterns']:
            patterns_str = "\n\n**Matched Patterns**\n" + "\n".join(
                f"› **{p['name'].replace('_', ' ').title()}** − {p['confidence']}% ({p['description']})"
                for p in analysis['patterns']
            )

        profile = self.get_profile(interaction.guild.id, user.id)

        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = (
            f"**Threat Analysis: {user}**\n\n"
            f"› Risk Level: `{risk_level}`\n"
            f"› Threat Score: `{analysis['threat_score']:.1f}/100`\n"
            f"› Recent Activity: `{len(profile.actions)}` actions in last hour{global_str}\n\n"
            f"**Threat Indicators**\n{indicators_str}{patterns_str}"
        )
        embed.set_thumbnail(url=user.display_avatar.url)

        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name='threatlist', description='View known threats')
    @app_commands.default_permissions(administrator=True)
    async def threat_list(self, interaction: discord.Interaction):
        """List known threats"""
        await interaction.response.defer(ephemeral=True)

        if not self.global_threats:
            embed = discord.Embed(description="No known threats in cache", color=EMBED_COLOR)
            return await interaction.followup.send(embed=embed, ephemeral=True)

        threats = sorted(
            self.global_threats.items(),
            key=lambda x: x[1].get('total_score', 0),
            reverse=True
        )[:10]

        threat_list = []
        for user_id, data in threats:
            user = self.bot.get_user(user_id)
            name = str(user) if user else f"Unknown ({user_id})"
            types = ', '.join(data.get('threat_types', [])[:3])
            threat_list.append(f"› **{name}** − Score: `{data.get('total_score', 0)}` | Servers: `{len(data.get('guild_ids', []))}`\n  Types: {types}")

        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = f"**Known Threats**\n\n" + "\n\n".join(threat_list)
        await interaction.followup.send(embed=embed, ephemeral=True)

    # ==================== PREFIX COMMANDS ====================

    @commands.group(name='threatintel', aliases=['ti'], invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def threatintel(self, ctx):
        """Threat Intelligence commands"""
        settings = await self.get_settings(ctx.guild.id)

        status = "enabled" if settings['enabled'] else "disabled"

        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = (
            f"**Threat Intelligence**\n\n"
            f"› Status: `{status}`\n"
            f"› Auto Action: `{'yes' if settings['auto_action'] else 'no'}`\n"
            f"› Min Score: `{settings['min_threat_score']}`\n"
            f"› Cross-server Intel: `{'yes' if settings['share_intel'] else 'no'}`\n"
            f"› Predictive Blocking: `{'yes' if settings['predictive_blocking'] else 'no'}`\n\n"
            f"**Commands**\n"
            f"› `!ti scan @user` − Scan a user\n"
            f"› `!ti report @user <type>` − Report a threat\n"
            f"› `!ti list` − View known threats\n"
            f"› `!ti enable/disable` − Toggle system"
        )

        await ctx.send(embed=embed)

    @threatintel.command(name='scan')
    @commands.has_permissions(administrator=True)
    async def ti_scan(self, ctx, member: discord.Member):
        """Scan a user for threats"""
        analysis = await self.analyze_behavior(ctx.guild.id, member.id)

        # Risk level
        if analysis['threat_score'] >= 75:
            risk_level = "HIGH"
        elif analysis['threat_score'] >= 50:
            risk_level = "MEDIUM"
        elif analysis['threat_score'] >= 25:
            risk_level = "LOW"
        else:
            risk_level = "MINIMAL"

        indicators_str = ", ".join(analysis['indicators'][:10]) if analysis['indicators'] else "None"

        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = (
            f"**Threat Scan: {member}**\n\n"
            f"› Risk: `{risk_level}`\n"
            f"› Score: `{analysis['threat_score']:.1f}/100`\n"
            f"› Indicators: `{len(analysis['indicators'])}`\n"
            f"› Patterns: `{len(analysis['patterns'])}`\n\n"
            f"**Detected**\n› {indicators_str}"
        )

        await ctx.send(embed=embed)

    @threatintel.command(name='report')
    @commands.has_permissions(administrator=True)
    async def ti_report(self, ctx, member: discord.Member, threat_type: str, *, evidence: str = None):
        """Report a threat manually"""
        valid_types = ['nuke', 'raid', 'spam', 'selfbot', 'scam', 'phishing', 'other']

        if threat_type.lower() not in valid_types:
            embed = discord.Embed(description=f"✕ Invalid type. Choose from: `{', '.join(valid_types)}`", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        await self.report_threat(ctx.guild, member.id, threat_type.lower(), evidence)
        embed = discord.Embed(description=f"+ Reported {member.mention} for `{threat_type}`", color=EMBED_COLOR)
        await ctx.send(embed=embed)

    @threatintel.command(name='enable')
    @commands.has_permissions(administrator=True)
    async def ti_enable(self, ctx):
        """Enable threat intelligence"""
        settings = await self.get_settings(ctx.guild.id)
        settings['enabled'] = True
        embed = discord.Embed(description="+ Enabled threat intelligence", color=EMBED_COLOR)
        await ctx.send(embed=embed)

    @threatintel.command(name='disable')
    @commands.has_permissions(administrator=True)
    async def ti_disable(self, ctx):
        """Disable threat intelligence"""
        settings = await self.get_settings(ctx.guild.id)
        settings['enabled'] = False
        embed = discord.Embed(description="− Disabled threat intelligence", color=EMBED_COLOR)
        await ctx.send(embed=embed)

    @threatintel.command(name='alert')
    @commands.has_permissions(administrator=True)
    async def ti_alert(self, ctx, channel: discord.TextChannel = None):
        """Set alert channel"""
        settings = await self.get_settings(ctx.guild.id)
        settings['alert_channel'] = channel.id if channel else None

        if channel:
            embed = discord.Embed(description=f"+ Set alert channel to {channel.mention}", color=EMBED_COLOR)
        else:
            embed = discord.Embed(description="+ Alert channel cleared", color=EMBED_COLOR)
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ThreatIntelligence(bot))
