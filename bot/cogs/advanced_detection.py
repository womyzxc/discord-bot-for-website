"""
Advanced Threat Detection Cog
=============================
Extended AI-powered detection patterns:
- Token grabber detection
- Scam/phishing detection
- Malicious link analysis
- Fake nitro detection
- Impersonation detection
- Mass DM detection
- Crypto scam detection
- QR code scam detection
"""

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio
import logging
import re
import hashlib
from typing import Dict, List, Optional, Tuple, Set
from urllib.parse import urlparse

logger = logging.getLogger('Offcialx.AdvancedDetection')

class ThreatSignature:
    """Represents a threat detection signature"""

    def __init__(self, name: str, category: str, severity: int,
                 patterns: List[str] = None,
                 keywords: List[str] = None,
                 domains: List[str] = None,
                 description: str = ""):
        self.name = name
        self.category = category
        self.severity = severity
        self.patterns = [re.compile(p, re.IGNORECASE) for p in (patterns or [])]
        self.keywords = [k.lower() for k in (keywords or [])]
        self.domains = [d.lower() for d in (domains or [])]
        self.description = description

    def check_content(self, content: str) -> Tuple[bool, List[str]]:
        """Check content against this signature"""
        matches = []
        content_lower = content.lower()

        # Check regex patterns
        for pattern in self.patterns:
            if pattern.search(content):
                matches.append(f"pattern:{pattern.pattern[:30]}")

        # Check keywords
        for keyword in self.keywords:
            if keyword in content_lower:
                matches.append(f"keyword:{keyword}")

        return len(matches) > 0, matches

    def check_url(self, url: str) -> Tuple[bool, str]:
        """Check a URL against this signature"""
        try:
            parsed = urlparse(url.lower())
            domain = parsed.netloc

            for bad_domain in self.domains:
                if bad_domain in domain:
                    return True, f"domain:{bad_domain}"
        except:
            pass

        return False, ""

class AdvancedDetection(commands.Cog):
    """Advanced AI-Powered Threat Detection"""

    # Minimal embed color
    EMBED_COLOR = 0x2b2d31

    def __init__(self, bot):
        self.bot = bot
        self.db = None

        # Initialize threat signatures
        self.signatures = self._init_signatures()

        # Known malicious hashes (file hashes, link hashes)
        self.malicious_hashes: Set[str] = set()

        # User DM tracking for mass DM detection
        self.dm_tracking: Dict[int, List[Dict]] = defaultdict(list)

        # Suspicious link cache
        self.suspicious_links: Dict[str, Dict] = {}

        # Guild settings
        self.guild_settings: Dict[int, Dict] = {}

        # Detection statistics
        self.detection_stats: Dict[str, int] = defaultdict(int)

    def _init_signatures(self) -> List[ThreatSignature]:
        """Initialize all threat detection signatures"""
        return [
            # Token Grabber Detection
            ThreatSignature(
                name="token_grabber",
                category="malware",
                severity=100,
                patterns=[
                    r'token[s]?\s*[=:]\s*["\'][a-zA-Z0-9._-]{50,}["\']',
                    r'localStorage\.getItem\(["\']token',
                    r'document\.body\.appendChild.*script',
                    r'eval\s*\(\s*atob',
                    r'window\.__TAURI__',
                    r'require\s*\(\s*["\']electron',
                    r'\.authToken\b',
                    r'discord\.com/api.*token',
                ],
                keywords=[
                    'grabber', 'stealer', 'token logger', 'discord token',
                    'steal token', 'token grab', 'get token'
                ],
                description="Potential token grabber/stealer code detected"
            ),

            # Fake Nitro Scam
            ThreatSignature(
                name="fake_nitro",
                category="scam",
                severity=90,
                patterns=[
                    r'discord\.gift/[a-zA-Z0-9]{16,}',
                    r'dis(?:c|k)ord\.(?:gifts?|nitro)',
                    r'dlscord\.(?:com|gift|gg)',
                    r'discorcl\.com',
                    r'discord\.corn',
                    r'discordapp\.co(?!m\b)',
                    r'free\s+nitro.*click',
                    r'nitro\s+(?:gift|giveaway).*(?:claim|click)',
                ],
                keywords=[
                    'free nitro', 'nitro generator', 'nitro gift free',
                    'claim nitro', 'nitro giveaway link'
                ],
                domains=[
                    'dlscord.com', 'discorcl.com', 'discord.corn',
                    'dlscord.gift', 'discordgift.site', 'discordnitro.gift'
                ],
                description="Fake Discord Nitro scam detected"
            ),

            # QR Code Scam
            ThreatSignature(
                name="qr_scam",
                category="scam",
                severity=85,
                patterns=[
                    r'scan\s+(?:this\s+)?qr\s+code',
                    r'qr\s+code.*(?:login|verify|claim)',
                    r'(?:login|verify).*qr\s+code',
                ],
                keywords=[
                    'scan qr', 'qr login', 'qr verification',
                    'scan to verify', 'scan to claim'
                ],
                description="QR code login scam detected"
            ),

            # Crypto Scam
            ThreatSignature(
                name="crypto_scam",
                category="scam",
                severity=80,
                patterns=[
                    r'(?:btc|eth|crypto)\s*(?:giveaway|airdrop)',
                    r'send\s+\d+\s*(?:btc|eth).*(?:get|receive|double)',
                    r'(?:double|triple)\s+your\s+(?:btc|eth|crypto)',
                    r'elon\s*musk.*(?:btc|crypto|giveaway)',
                    r'(?:wallet|address).*[13][a-km-zA-HJ-NP-Z1-9]{25,34}',
                ],
                keywords=[
                    'crypto giveaway', 'bitcoin giveaway', 'eth airdrop',
                    'double your crypto', 'free bitcoin', 'crypto doubler'
                ],
                domains=[
                    'elonmusk-crypto.com', 'btc-giveaway', 'eth-airdrop',
                    'crypto-double.com', 'bitcoin-generator'
                ],
                description="Cryptocurrency scam detected"
            ),

            # Phishing Links
            ThreatSignature(
                name="phishing",
                category="phishing",
                severity=85,
                patterns=[
                    r'(?:login|signin|verify).*discord(?!app\.com|\.com|\.gg)',
                    r'discord.*(?:login|signin|verify).*\.(?:xyz|tk|ml|ga|cf)',
                    r'(?:steam|roblox|epic)community.*\.(?:xyz|tk|ml)',
                    r'verify.*(?:account|identity).*click',
                ],
                keywords=[
                    'verify your account', 'confirm identity',
                    'account suspended', 'click to verify'
                ],
                domains=[
                    'discordlogin.com', 'discord-verify.com',
                    'steamcommunity.ru', 'roblox-login.com',
                    'epicgames-verify.com'
                ],
                description="Phishing attempt detected"
            ),

            # IP Logger
            ThreatSignature(
                name="ip_logger",
                category="tracking",
                severity=70,
                patterns=[
                    r'grabify\.link',
                    r'iplogger\.org',
                    r'2no\.co',
                    r'yip\.su',
                    r'ipgrabber',
                ],
                keywords=[],
                domains=[
                    'grabify.link', 'iplogger.org', '2no.co',
                    'yip.su', 'ipgrab.com', 'blasze.tk'
                ],
                description="IP logger/grabber link detected"
            ),

            # Malware Distribution
            ThreatSignature(
                name="malware_distribution",
                category="malware",
                severity=95,
                patterns=[
                    r'\.(?:exe|bat|cmd|ps1|vbs|scr)\b.*(?:download|click|run)',
                    r'download.*(?:hack|cheat|crack|keygen)',
                    r'(?:free|cracked).*(?:photoshop|office|windows)',
                ],
                keywords=[
                    'free hack', 'game hack download', 'crack download',
                    'keygen free', 'activation tool'
                ],
                description="Potential malware distribution detected"
            ),

            # Impersonation
            ThreatSignature(
                name="impersonation",
                category="social_engineering",
                severity=75,
                patterns=[
                    r'(?:i\s+am|this\s+is)\s+(?:staff|admin|mod|support)',
                    r'official\s+(?:discord|staff|support)',
                    r'discord\s+(?:staff|employee|partner)',
                    r'verify.*(?:staff|admin).*role',
                ],
                keywords=[
                    'i am from discord', 'discord support here',
                    'official staff', 'discord employee'
                ],
                description="Staff/support impersonation detected"
            ),

            # Credential Harvesting
            ThreatSignature(
                name="credential_harvest",
                category="phishing",
                severity=90,
                patterns=[
                    r'(?:enter|send|dm).*(?:password|email|login)',
                    r'(?:password|credentials).*(?:verify|confirm)',
                    r'login\s+(?:here|now).*(?:\.xyz|\.tk|\.ml)',
                ],
                keywords=[
                    'send password', 'dm password', 'enter credentials',
                    'verify password', 'login details'
                ],
                description="Credential harvesting attempt detected"
            ),

            # Raid Coordination
            ThreatSignature(
                name="raid_coordination",
                category="raid",
                severity=80,
                patterns=[
                    r'raid\s+(?:this|the)\s+server',
                    r'(?:lets|let\'s)\s+(?:raid|nuke|destroy)',
                    r'join\s+(?:and|to)\s+raid',
                    r'mass\s+(?:ping|mention|spam)',
                ],
                keywords=[
                    'raid server', 'nuke server', 'destroy server',
                    'mass ping', 'spam everyone'
                ],
                description="Raid coordination detected"
            ),

            # NSFW/Gore
            ThreatSignature(
                name="nsfw_content",
                category="content",
                severity=60,
                patterns=[
                    r'(?:gore|shock|disturbing)\s*(?:content|video|image)',
                ],
                keywords=[],
                domains=[
                    'shock.com', 'gore.com', 'bestgore'
                ],
                description="Potentially disturbing content detected"
            ),

            # Selfbot Advertising
            ThreatSignature(
                name="selfbot_ad",
                category="tos_violation",
                severity=65,
                patterns=[
                    r'selfbot\s+(?:for\s+sale|download|free)',
                    r'(?:buy|get)\s+(?:a\s+)?selfbot',
                    r'discord\s+selfbot\s+(?:2024|2025)',
                ],
                keywords=[
                    'selfbot download', 'selfbot for sale',
                    'best selfbot', 'selfbot features'
                ],
                description="Selfbot advertising detected"
            ),

            # Account Selling
            ThreatSignature(
                name="account_selling",
                category="tos_violation",
                severity=70,
                patterns=[
                    r'(?:sell|selling|buy)\s+(?:discord|nitro)\s+account',
                    r'account\s+(?:for\s+sale|marketplace)',
                    r'(?:aged|og)\s+(?:discord\s+)?account',
                ],
                keywords=[
                    'selling account', 'account for sale',
                    'buy discord account', 'og account'
                ],
                description="Account selling/buying detected"
            ),
        ]

    async def get_settings(self, guild_id: int) -> Dict:
        """Get guild settings"""
        if guild_id not in self.guild_settings:
            self.guild_settings[guild_id] = {
                'enabled': True,
                'auto_delete': True,
                'auto_mute': True,
                'mute_duration': 3600,
                'log_channel': None,
                'alert_role': None,
                'whitelist_roles': [],
                'whitelist_channels': [],
                'sensitivity': 'medium',  # low, medium, high
            }
        return self.guild_settings[guild_id]

    def get_severity_threshold(self, sensitivity: str) -> int:
        """Get severity threshold based on sensitivity"""
        thresholds = {
            'low': 80,
            'medium': 60,
            'high': 40
        }
        return thresholds.get(sensitivity, 60)

    async def scan_content(self, content: str, guild_id: int = None) -> List[Dict]:
        """Scan content for all threat signatures"""
        detections = []
        settings = await self.get_settings(guild_id) if guild_id else {}
        threshold = self.get_severity_threshold(settings.get('sensitivity', 'medium'))

        for sig in self.signatures:
            if sig.severity < threshold:
                continue

            matched, matches = sig.check_content(content)
            if matched:
                detections.append({
                    'signature': sig.name,
                    'category': sig.category,
                    'severity': sig.severity,
                    'description': sig.description,
                    'matches': matches
                })

                # Update stats
                self.detection_stats[sig.name] += 1

        return detections

    async def scan_urls(self, urls: List[str]) -> List[Dict]:
        """Scan URLs for threats"""
        detections = []

        for url in urls:
            # Check against signatures
            for sig in self.signatures:
                matched, match = sig.check_url(url)
                if matched:
                    detections.append({
                        'url': url,
                        'signature': sig.name,
                        'category': sig.category,
                        'severity': sig.severity,
                        'match': match
                    })
                    break

            # Check known malicious hash
            url_hash = hashlib.sha256(url.encode()).hexdigest()
            if url_hash in self.malicious_hashes:
                detections.append({
                    'url': url,
                    'signature': 'known_malicious',
                    'category': 'malware',
                    'severity': 100,
                    'match': 'hash_match'
                })

        return detections

    def extract_urls(self, content: str) -> List[str]:
        """Extract URLs from content"""
        url_pattern = re.compile(
            r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*',
            re.IGNORECASE
        )
        return url_pattern.findall(content)

    async def handle_detection(self, message: discord.Message, detections: List[Dict]):
        """Handle a detection event"""
        if not detections:
            return

        settings = await self.get_settings(message.guild.id)
        max_severity = max(d['severity'] for d in detections)

        # Delete message if enabled
        if settings['auto_delete'] and max_severity >= 70:
            try:
                await message.delete()
            except:
                pass

        # Mute user if enabled and severity is high
        if settings['auto_mute'] and max_severity >= 85:
            try:
                duration = timedelta(seconds=settings['mute_duration'])
                reason = f"[AutoMod] {detections[0]['signature']}: {detections[0]['description']}"
                await message.author.timeout(duration, reason=reason)
            except:
                pass

        # Log the detection
        await self.log_detection(message, detections)

        # Report to threat intelligence
        ti_cog = self.bot.get_cog('ThreatIntelligence')
        if ti_cog:
            for detection in detections:
                await ti_cog.report_threat(
                    message.guild,
                    message.author.id,
                    detection['signature'],
                    f"Content: {message.content[:200]}"
                )

    async def log_detection(self, message: discord.Message, detections: List[Dict]):
        """Log a detection to the configured channel"""
        settings = await self.get_settings(message.guild.id)

        if not settings['log_channel']:
            return

        channel = message.guild.get_channel(settings['log_channel'])
        if not channel:
            return

        detection_info = []
        for detection in detections[:3]:
            detection_info.append(f"› {detection['category']}/{detection['signature']} `{detection['severity']}/100`")

        content = message.content[:500] if message.content else "No content"

        embed = discord.Embed(color=self.EMBED_COLOR)
        embed.description = (
            f"**Threat Detected**\n\n"
            f"› User: {message.author.mention} ({message.author})\n"
            f"› Channel: {message.channel.mention}\n\n"
            f"**Detections**\n" + "\n".join(detection_info) + "\n\n"
            f"**Content**\n```{content}```"
        )

        try:
            alert_content = ""
            if settings['alert_role']:
                role = message.guild.get_role(settings['alert_role'])
                if role:
                    alert_content = role.mention

            await channel.send(content=alert_content, embed=embed)
        except:
            pass

    # ==================== EVENT LISTENERS ====================

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Scan all messages for threats"""
        if message.author.bot or not message.guild:
            return

        # NEVER touch messages from this bot
        if message.author.id == self.bot.user.id:
            return

        # Skip bot commands - don't scan them
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
            return

        settings = await self.get_settings(message.guild.id)

        if not settings['enabled']:
            return

        # Check exemptions
        if any(role.id in settings['whitelist_roles'] for role in message.author.roles):
            return
        if message.channel.id in settings['whitelist_channels']:
            return
        if message.author.guild_permissions.administrator:
            return

        # Scan content
        detections = await self.scan_content(message.content, message.guild.id)

        # Scan URLs
        urls = self.extract_urls(message.content)
        if urls:
            url_detections = await self.scan_urls(urls)
            detections.extend(url_detections)

        # Scan attachments (file names)
        for attachment in message.attachments:
            if any(attachment.filename.lower().endswith(ext)
                   for ext in ['.exe', '.bat', '.cmd', '.ps1', '.vbs', '.scr', '.jar']):
                detections.append({
                    'signature': 'suspicious_file',
                    'category': 'malware',
                    'severity': 75,
                    'description': f"Suspicious file: {attachment.filename}",
                    'matches': ['file_extension']
                })

        if detections:
            await self.handle_detection(message, detections)

    # ==================== COMMANDS ====================

    @commands.group(name='detection', aliases=['detect'], invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def detection(self, ctx):
        """Advanced detection configuration"""
        settings = await self.get_settings(ctx.guild.id)

        status = "enabled" if settings['enabled'] else "disabled"

        # Detection stats
        top_detections = sorted(self.detection_stats.items(), key=lambda x: x[1], reverse=True)[:5]
        stats_str = "\n".join(f"› {name}: `{count}`" for name, count in top_detections) if top_detections else "› None"

        embed = discord.Embed(color=self.EMBED_COLOR)
        embed.description = (
            f"**Advanced Detection**\n\n"
            f"› Status: `{status}`\n"
            f"› Sensitivity: `{settings['sensitivity']}`\n"
            f"› Auto Delete: `{'yes' if settings['auto_delete'] else 'no'}`\n"
            f"› Auto Mute: `{'yes' if settings['auto_mute'] else 'no'}`\n"
            f"› Signatures: `{len(self.signatures)}`\n\n"
            f"**Top Detections**\n{stats_str}"
        )

        await ctx.send(embed=embed)

    @detection.command(name='enable')
    @commands.has_permissions(administrator=True)
    async def detection_enable(self, ctx):
        """Enable advanced detection"""
        settings = await self.get_settings(ctx.guild.id)
        settings['enabled'] = True
        embed = discord.Embed(description="+ Enabled advanced detection", color=self.EMBED_COLOR)
        await ctx.send(embed=embed)

    @detection.command(name='disable')
    @commands.has_permissions(administrator=True)
    async def detection_disable(self, ctx):
        """Disable advanced detection"""
        settings = await self.get_settings(ctx.guild.id)
        settings['enabled'] = False
        embed = discord.Embed(description="− Disabled advanced detection", color=self.EMBED_COLOR)
        await ctx.send(embed=embed)

    @detection.command(name='sensitivity')
    @commands.has_permissions(administrator=True)
    async def detection_sensitivity(self, ctx, level: str):
        """Set detection sensitivity (low/medium/high)"""
        if level.lower() not in ['low', 'medium', 'high']:
            embed = discord.Embed(description="✕ Invalid level. Use: `low`, `medium`, `high`", color=self.EMBED_COLOR)
            return await ctx.send(embed=embed)

        settings = await self.get_settings(ctx.guild.id)
        settings['sensitivity'] = level.lower()
        embed = discord.Embed(description=f"+ Set sensitivity to `{level.lower()}`", color=self.EMBED_COLOR)
        await ctx.send(embed=embed)

    @detection.command(name='test')
    @commands.has_permissions(administrator=True)
    async def detection_test(self, ctx, *, content: str):
        """Test detection on content"""
        detections = await self.scan_content(content, ctx.guild.id)

        if not detections:
            embed = discord.Embed(description="+ No threats detected", color=self.EMBED_COLOR)
            return await ctx.send(embed=embed)

        detection_list = []
        for detection in detections:
            detection_list.append(f"› {detection['signature']} `{detection['severity']}/100`\n  {detection['description']}")

        embed = discord.Embed(color=self.EMBED_COLOR)
        embed.description = f"**Detection Results**\n\n" + "\n".join(detection_list)
        await ctx.send(embed=embed)

    @detection.command(name='signatures')
    @commands.has_permissions(administrator=True)
    async def detection_signatures(self, ctx):
        """List all detection signatures"""
        # Group by category
        categories = defaultdict(list)
        for sig in self.signatures:
            categories[sig.category].append(sig)

        cat_list = []
        for category, sigs in categories.items():
            sig_names = ", ".join(f"`{s.name}`" for s in sigs)
            cat_list.append(f"› **{category}**: {sig_names}")

        embed = discord.Embed(color=self.EMBED_COLOR)
        embed.description = f"**Detection Signatures**\n\n" + "\n".join(cat_list)
        await ctx.send(embed=embed)

    # ==================== SLASH COMMANDS ====================

    @app_commands.command(name='scan', description='Scan content for threats')
    @app_commands.describe(content='Content to scan')
    @app_commands.default_permissions(administrator=True)
    async def scan_cmd(self, interaction: discord.Interaction, content: str):
        """Scan content for threats"""
        detections = await self.scan_content(content, interaction.guild.id)

        if not detections:
            embed = discord.Embed(description="+ No threats detected", color=self.EMBED_COLOR)
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        detection_list = []
        for detection in detections[:5]:
            detection_list.append(f"› {detection['signature']} `{detection['severity']}/100` ({detection['category']})")

        embed = discord.Embed(color=self.EMBED_COLOR)
        embed.description = f"**Scan Results**\n\n" + "\n".join(detection_list)
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(AdvancedDetection(bot))
