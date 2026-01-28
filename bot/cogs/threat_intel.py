"""
AI-Powered Threat Intelligence Cog
===================================
Advanced threat detection using pattern analysis
"""

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from collections import defaultdict
import logging
import statistics
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger('Offcialx.ThreatIntel')

EMBED_COLOR = 0x2b2d31


class BehaviorProfile:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.actions: List[Dict] = []
        self.action_velocity: List[float] = []
        self.anomaly_score: float = 0.0
        self.threat_indicators: List[str] = []
        self.last_analysis: Optional[datetime] = None

    def add_action(self, action_type: str, details: str = None):
        now = datetime.utcnow()
        self.actions.append({'type': action_type, 'details': details, 'time': now})

        if len(self.actions) >= 2:
            delta = (now - self.actions[-2]['time']).total_seconds()
            if delta > 0:
                self.action_velocity.append(1 / delta)

        cutoff = now - timedelta(hours=1)
        self.actions = [a for a in self.actions if a['time'] > cutoff]
        self.action_velocity = self.action_velocity[-100:]


class ThreatPattern:
    def __init__(self, name, pattern_type, indicators, severity=50, description=""):
        self.name = name
        self.pattern_type = pattern_type
        self.indicators = indicators
        self.severity = severity
        self.description = description

    def matches(self, profile: BehaviorProfile) -> Tuple[bool, int]:
        hits = sum(1 for i in self.indicators if i in profile.threat_indicators)
        if hits == 0:
            return False, 0
        confidence = int((hits / len(self.indicators)) * 100)
        return confidence >= 50, confidence


class ThreatIntelligence(commands.Cog):
    """AI-Powered Threat Intelligence System"""

    MAX_EVIDENCE_LEN = 2000  # 🔒 critical safety limit

    def __init__(self, bot):
        self.bot = bot
        self.db = None
        self.profiles: Dict[int, Dict[int, BehaviorProfile]] = defaultdict(dict)
        self.global_threats: Dict[int, Dict] = {}
        self.threat_patterns = self._init_threat_patterns()
        self.guild_settings: Dict[int, Dict] = {}

        self.thresholds = {
            'action_velocity': 5.0,
            'permission_changes': 3,
        }

    # ================= SAFETY =================

    def _sanitize_evidence(self, evidence: Optional[str]) -> Optional[str]:
        if not evidence:
            return None

        if not isinstance(evidence, str):
            evidence = str(evidence)

        if len(evidence) > self.MAX_EVIDENCE_LEN:
            evidence = evidence[:self.MAX_EVIDENCE_LEN] + "…[truncated]"

        return evidence

    # ================= CORE =================

    def _init_threat_patterns(self):
        return [
            ThreatPattern(
                "nuke_attempt",
                "destructive",
                ["mass_ban", "channel_delete", "role_delete", "high_velocity"],
                100,
                "Server destruction attempt"
            )
        ]

    async def get_settings(self, guild_id: int) -> Dict:
        if guild_id not in self.guild_settings:
            self.guild_settings[guild_id] = {
                'enabled': True,
                'alert_channel': None,
                'min_threat_score': 50,
            }
        return self.guild_settings[guild_id]

    def get_profile(self, guild_id: int, user_id: int) -> BehaviorProfile:
        if user_id not in self.profiles[guild_id]:
            self.profiles[guild_id][user_id] = BehaviorProfile(user_id)
        return self.profiles[guild_id][user_id]

    async def analyze_behavior(self, guild_id: int, user_id: int) -> Dict:
        profile = self.get_profile(guild_id, user_id)
        now = datetime.utcnow()

        if profile.last_analysis and (now - profile.last_analysis).seconds < 60:
            return {
                'threat_score': profile.anomaly_score,
                'indicators': profile.threat_indicators,
                'patterns': []
            }

        profile.last_analysis = now
        profile.threat_indicators = []

        if profile.action_velocity:
            avg = statistics.mean(profile.action_velocity)
            if avg > self.thresholds['action_velocity']:
                profile.threat_indicators.append('high_velocity')

        patterns = []
        for pattern in self.threat_patterns:
            match, confidence = pattern.matches(profile)
            if match:
                patterns.append({
                    'name': pattern.name,
                    'confidence': confidence,
                    'severity': pattern.severity,
                })

        base = len(profile.threat_indicators) * 10
        pattern_score = sum(p['severity'] * p['confidence'] / 100 for p in patterns)
        profile.anomaly_score = min(base + pattern_score, 100)

        return {
            'threat_score': profile.anomaly_score,
            'indicators': profile.threat_indicators,
            'patterns': patterns
        }

    async def report_threat(self, guild, user_id, threat_type, evidence=None):
        evidence = self._sanitize_evidence(evidence)
        settings = await self.get_settings(guild.id)

        data = self.global_threats.setdefault(user_id, {
            'threat_types': [],
            'guild_ids': [],
            'total_score': 0,
            'last_seen': datetime.utcnow()
        })

        if threat_type not in data['threat_types']:
            data['threat_types'].append(threat_type)

        if guild.id not in data['guild_ids']:
            data['guild_ids'].append(guild.id)

        data['threat_types'] = data['threat_types'][-10:]
        data['guild_ids'] = data['guild_ids'][-20:]
        data['total_score'] = min(data['total_score'] + 10, 100)
        data['last_seen'] = datetime.utcnow()

        if self.db:
            try:
                await self.db.add_threat_intel(
                    user_id=user_id,
                    threat_type=threat_type,
                    threat_score=10,
                    evidence=evidence,
                    guild_id=guild.id
                )
            except Exception as e:
                logger.error(f"ThreatIntel DB error: {e}")

        if settings['alert_channel']:
            await self.send_threat_alert(guild, user_id, threat_type, evidence)

    async def send_threat_alert(self, guild, user_id, threat_type, evidence=None):
        channel_id = (await self.get_settings(guild.id))['alert_channel']
        if not channel_id:
            return

        channel = guild.get_channel(channel_id)
        if not channel:
            return

        embed = discord.Embed(
            title="Threat Alert",
            description=f"User ID: `{user_id}`\nType: `{threat_type}`\n\n{evidence or ''}",
            color=EMBED_COLOR
        )
        await channel.send(embed=embed)

    # ================= EVENTS =================

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        guild = channel.guild
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete):
            profile = self.get_profile(guild.id, entry.user.id)
            profile.add_action('channel_delete', f'Deleted #{channel.name}')

            analysis = await self.analyze_behavior(guild.id, entry.user.id)
            if analysis['threat_score'] >= 50:
                await self.report_threat(
                    guild,
                    entry.user.id,
                    'channel_deletion',
                    f"Deleted channel: {channel.name} ({channel.id})"
                )
            break


async def setup(bot):
    await bot.add_cog(ThreatIntelligence(bot))
