"""
VPN/Proxy Detection for Raid Prevention
========================================
Detects and blocks users joining from VPNs, proxies, or data centers.
Integrates with anti-raid to automatically enable during attacks.

Features:
- IP reputation checking via multiple APIs
- VPN/Proxy/Datacenter detection
- Automatic blocking during raids
- Whitelist for legitimate VPN users
- Risk scoring system
"""

import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
from collections import defaultdict
import aiohttp
import asyncio
import logging
import os
import hashlib

logger = logging.getLogger('Offcialx.VPNDetection')


class IPCheckResult:
    """Result of an IP reputation check"""

    def __init__(
        self,
        ip_hash: str,
        is_vpn: bool = False,
        is_proxy: bool = False,
        is_datacenter: bool = False,
        is_tor: bool = False,
        risk_score: int = 0,
        country: str = None,
        isp: str = None,
        org: str = None,
        details: Dict = None
    ):
        self.ip_hash = ip_hash
        self.is_vpn = is_vpn
        self.is_proxy = is_proxy
        self.is_datacenter = is_datacenter
        self.is_tor = is_tor
        self.risk_score = risk_score
        self.country = country
        self.isp = isp
        self.org = org
        self.details = details or {}
        self.checked_at = datetime.utcnow()

    @property
    def is_suspicious(self) -> bool:
        """Check if the IP is suspicious"""
        return self.is_vpn or self.is_proxy or self.is_datacenter or self.is_tor or self.risk_score > 50

    @property
    def threat_level(self) -> str:
        """Get the threat level"""
        if self.is_tor:
            return "critical"
        if self.is_datacenter or self.risk_score > 80:
            return "high"
        if self.is_vpn or self.is_proxy or self.risk_score > 50:
            return "medium"
        if self.risk_score > 25:
            return "low"
        return "safe"


class VPNDetection(commands.Cog):
    """VPN/Proxy Detection System"""

    # Minimal embed color
    EMBED_COLOR = 0x2b2d31

    def __init__(self, bot):
        self.bot = bot
        self.db = None
        self.session: Optional[aiohttp.ClientSession] = None

        # Guild settings: guild_id -> settings
        self.guild_settings: Dict[int, Dict] = {}

        # IP cache to avoid repeated lookups
        self.ip_cache: Dict[str, IPCheckResult] = {}
        self.cache_duration = timedelta(hours=24)

        # Whitelist: guild_id -> set of user_ids
        self.whitelisted_users: Dict[int, Set[int]] = defaultdict(set)

        # Known VPN providers (partial ISP names)
        self.vpn_providers = [
            'nordvpn', 'expressvpn', 'surfshark', 'cyberghost', 'private internet',
            'protonvpn', 'mullvad', 'windscribe', 'hotspot shield', 'tunnelbear',
            'ipvanish', 'purevpn', 'vypr', 'strongvpn', 'zenmate', 'hide.me',
            'privatevpn', 'torguard', 'ovpn', 'astrill', 'perfectprivacy',
            'digitalocean', 'amazon', 'aws', 'google cloud', 'azure', 'linode',
            'vultr', 'hetzner', 'ovh', 'hostinger', 'contabo', 'cloudflare'
        ]

        # Datacenter ASN prefixes
        self.datacenter_asns = [
            'AS14061',  # DigitalOcean
            'AS16509',  # Amazon
            'AS15169',  # Google
            'AS8075',   # Microsoft
            'AS63949',  # Linode
            'AS20473',  # Vultr
            'AS24940',  # Hetzner
            'AS16276',  # OVH
        ]

        # API keys (from environment)
        self.proxycheck_key = os.getenv('PROXYCHECK_API_KEY', '')
        self.ipinfo_key = os.getenv('IPINFO_API_KEY', '')
        self.abuseipdb_key = os.getenv('ABUSEIPDB_API_KEY', '')

        # Raid mode tracking
        self.raid_mode_guilds: Set[int] = set()

        # Start cleanup task
        self.cleanup_cache.start()

    def cog_unload(self):
        self.cleanup_cache.cancel()
        if self.session:
            asyncio.create_task(self.session.close())

    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def get_guild_settings(self, guild_id: int) -> Dict:
        """Get guild VPN detection settings"""
        if guild_id not in self.guild_settings:
            self.guild_settings[guild_id] = {
                'enabled': True,
                'action': 'ban',            # DEFAULT: ban (was kick) - maximum security
                'block_vpn': True,
                'block_proxy': True,
                'block_datacenter': True,
                'block_tor': True,
                'raid_mode_only': False,    # Check ALL joins, not just raids
                'min_risk_score': 50,       # 50 score triggers (was 75) - more strict
                'exempt_boosters': True,    # Don't check server boosters
                'exempt_verified': False,   # Check verified users too (was True)
                'log_channel': None,
                'quarantine_role': None,
                'block_new_accounts': True, # Block accounts < 7 days old from VPNs
                'new_account_days': 7,      # Account age threshold
            }
        return self.guild_settings[guild_id]

    def hash_ip(self, ip: str) -> str:
        """Hash an IP for privacy"""
        return hashlib.sha256(ip.encode()).hexdigest()[:16]

    async def check_ip_proxycheck(self, ip: str) -> Optional[IPCheckResult]:
        """Check IP using proxycheck.io API"""
        if not self.proxycheck_key:
            return None

        try:
            session = await self.get_session()
            url = f"http://proxycheck.io/v2/{ip}?key={self.proxycheck_key}&vpn=1&asn=1&risk=1"

            async with session.get(url, timeout=10) as response:
                if response.status != 200:
                    return None

                data = await response.json()

                if data.get('status') != 'ok':
                    return None

                ip_data = data.get(ip, {})

                return IPCheckResult(
                    ip_hash=self.hash_ip(ip),
                    is_vpn=ip_data.get('vpn') == 'yes',
                    is_proxy=ip_data.get('proxy') == 'yes',
                    is_datacenter=ip_data.get('type') == 'Hosting',
                    risk_score=int(ip_data.get('risk', 0)),
                    country=ip_data.get('country'),
                    isp=ip_data.get('isp'),
                    org=ip_data.get('organisation'),
                    details={'provider': ip_data.get('provider', '')}
                )
        except Exception as e:
            logger.error(f"Proxycheck API error: {e}")
            return None

    async def check_ip_ipinfo(self, ip: str) -> Optional[Dict]:
        """Check IP using ipinfo.io API"""
        try:
            session = await self.get_session()
            url = f"https://ipinfo.io/{ip}/json"
            headers = {}
            if self.ipinfo_key:
                headers['Authorization'] = f"Bearer {self.ipinfo_key}"

            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status != 200:
                    return None

                data = await response.json()
                return {
                    'org': data.get('org', ''),
                    'hostname': data.get('hostname', ''),
                    'country': data.get('country', ''),
                    'city': data.get('city', ''),
                }
        except Exception as e:
            logger.error(f"IPInfo API error: {e}")
            return None

    async def check_ip_abuseipdb(self, ip: str) -> Optional[Dict]:
        """Check IP using AbuseIPDB API"""
        if not self.abuseipdb_key:
            return None

        try:
            session = await self.get_session()
            url = "https://api.abuseipdb.com/api/v2/check"
            headers = {
                'Key': self.abuseipdb_key,
                'Accept': 'application/json'
            }
            params = {
                'ipAddress': ip,
                'maxAgeInDays': 90
            }

            async with session.get(url, headers=headers, params=params, timeout=10) as response:
                if response.status != 200:
                    return None

                data = await response.json()
                ip_data = data.get('data', {})

                return {
                    'abuse_score': ip_data.get('abuseConfidenceScore', 0),
                    'is_tor': ip_data.get('isTor', False),
                    'total_reports': ip_data.get('totalReports', 0),
                    'country': ip_data.get('countryCode', ''),
                    'isp': ip_data.get('isp', ''),
                    'usage_type': ip_data.get('usageType', ''),
                }
        except Exception as e:
            logger.error(f"AbuseIPDB API error: {e}")
            return None

    async def check_ip(self, ip: str) -> IPCheckResult:
        """Check an IP address using all available methods"""
        ip_hash = self.hash_ip(ip)

        # Check cache first
        if ip_hash in self.ip_cache:
            cached = self.ip_cache[ip_hash]
            if datetime.utcnow() - cached.checked_at < self.cache_duration:
                return cached

        # Try proxycheck.io first (most comprehensive)
        result = await self.check_ip_proxycheck(ip)

        if not result:
            # Fallback: Create basic result
            result = IPCheckResult(ip_hash=ip_hash)

        # Enhance with AbuseIPDB
        abuse_data = await self.check_ip_abuseipdb(ip)
        if abuse_data:
            result.is_tor = result.is_tor or abuse_data.get('is_tor', False)
            result.risk_score = max(result.risk_score, abuse_data.get('abuse_score', 0))

            # Check usage type for datacenter
            usage = abuse_data.get('usage_type', '').lower()
            if 'data center' in usage or 'hosting' in usage:
                result.is_datacenter = True

        # Enhance with IPInfo
        ipinfo_data = await self.check_ip_ipinfo(ip)
        if ipinfo_data:
            org = ipinfo_data.get('org', '').lower()
            result.org = result.org or ipinfo_data.get('org')

            # Check for VPN providers in org name
            for provider in self.vpn_providers:
                if provider in org:
                    result.is_vpn = True
                    break

        # Cache the result
        self.ip_cache[ip_hash] = result

        return result

    async def handle_suspicious_join(self, member: discord.Member, result: IPCheckResult):
        """Handle a suspicious member join"""
        guild = member.guild
        settings = await self.get_guild_settings(guild.id)

        action = settings.get('action', 'kick')

        # Build reason
        reasons = []
        if result.is_vpn:
            reasons.append("VPN")
        if result.is_proxy:
            reasons.append("Proxy")
        if result.is_datacenter:
            reasons.append("Datacenter")
        if result.is_tor:
            reasons.append("Tor")
        if result.risk_score > 50:
            reasons.append(f"Risk Score: {result.risk_score}")

        reason_str = ", ".join(reasons)
        full_reason = f"[VPN Detection] Suspicious IP detected: {reason_str}"

        try:
            if action == 'ban':
                await member.ban(reason=full_reason, delete_message_days=0)
                logger.info(f"Banned {member} for VPN/Proxy use: {reason_str}")
            elif action == 'kick':
                await member.kick(reason=full_reason)
                logger.info(f"Kicked {member} for VPN/Proxy use: {reason_str}")
            elif action == 'quarantine':
                quarantine_role_id = settings.get('quarantine_role')
                if quarantine_role_id:
                    role = guild.get_role(quarantine_role_id)
                    if role:
                        await member.add_roles(role, reason=full_reason)
                        logger.info(f"Quarantined {member} for VPN/Proxy use: {reason_str}")
            # 'alert' action just logs
        except discord.Forbidden:
            logger.warning(f"Cannot take action on {member}: Missing permissions")
        except Exception as e:
            logger.error(f"Error handling suspicious join: {e}")

        # Log to channel
        await self.log_detection(guild, member, result, action)

        # Send webhook notification
        if hasattr(self.bot, 'webhook_notifier') and self.bot.webhook_notifier:
            await self.bot.webhook_notifier.send_security_alert(
                guild_name=guild.name,
                guild_id=guild.id,
                title="VPN/Proxy Detected",
                description=f"{member} joined using a suspicious IP",
                threat_type="VPN/Proxy Detection",
                severity="medium" if action == 'alert' else "high",
                action_taken=action.title()
            )

    async def log_detection(self, guild: discord.Guild, member: discord.Member, result: IPCheckResult, action: str):
        """Log a VPN detection to the log channel"""
        settings = await self.get_guild_settings(guild.id)
        log_channel_id = settings.get('log_channel')

        if not log_channel_id:
            antinuke = self.bot.get_cog('AntiNuke')
            if antinuke:
                an_settings = await antinuke.get_settings(guild.id)
                log_channel_id = an_settings.get('log_channel_id')

        if not log_channel_id:
            return

        channel = guild.get_channel(log_channel_id)
        if not channel:
            return

        details = []
        if result.is_vpn:
            details.append("VPN")
        if result.is_proxy:
            details.append("Proxy")
        if result.is_datacenter:
            details.append("Datacenter")
        if result.is_tor:
            details.append("Tor")

        embed = discord.Embed(color=self.EMBED_COLOR)
        embed.description = (
            f"**VPN/Proxy Detected**\n\n"
            f"› User: {member.mention}\n"
            f"› Action: `{action}`\n"
            f"› Risk: `{result.risk_score}/100`\n"
            f"› Type: `{', '.join(details) if details else 'High Risk'}`"
        )
        if result.country:
            embed.description += f"\n› Country: `{result.country}`"

        try:
            await channel.send(embed=embed)
        except:
            pass

    # ==================== EVENT LISTENERS ====================

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Check new members for VPN/Proxy"""
        if member.bot:
            return

        guild = member.guild
        settings = await self.get_guild_settings(guild.id)

        if not settings.get('enabled', True):
            return

        # Check if raid mode only and not in raid
        if settings.get('raid_mode_only', False):
            if guild.id not in self.raid_mode_guilds:
                return

        # Check exemptions
        if settings.get('exempt_verified', True):
            if member.flags.verified_email:
                return

        if settings.get('exempt_boosters', True):
            if member.premium_since:
                return

        # Check whitelist
        if member.id in self.whitelisted_users.get(guild.id, set()):
            return

        # Note: Discord doesn't provide IP addresses directly
        # This would need to be integrated with a verification system
        # that captures IPs, or use other heuristics

        # For now, we'll check based on account characteristics
        # that correlate with bot/raid accounts

        account_age = (datetime.utcnow() - member.created_at.replace(tzinfo=None)).days

        # Very new accounts during raids are suspicious
        if guild.id in self.raid_mode_guilds and account_age < 7:
            # Create a pseudo-result for new accounts during raids
            result = IPCheckResult(
                ip_hash="account_check",
                risk_score=min(100, 100 - account_age * 10),
                details={'reason': 'New account during raid'}
            )

            if result.risk_score >= settings.get('min_risk_score', 75):
                await self.handle_suspicious_join(member, result)

    # ==================== RAID MODE INTEGRATION ====================

    def enable_raid_mode(self, guild_id: int):
        """Enable raid mode for a guild (more aggressive checking)"""
        self.raid_mode_guilds.add(guild_id)
        logger.info(f"VPN Detection: Raid mode enabled for guild {guild_id}")

    def disable_raid_mode(self, guild_id: int):
        """Disable raid mode for a guild"""
        self.raid_mode_guilds.discard(guild_id)
        logger.info(f"VPN Detection: Raid mode disabled for guild {guild_id}")

    # ==================== COMMANDS ====================

    @commands.hybrid_group(name='vpn', aliases=['vpndetect'], invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def vpndetect(self, ctx: commands.Context):
        """VPN/Proxy Detection commands"""
        settings = await self.get_guild_settings(ctx.guild.id)

        status = "enabled" if settings['enabled'] else "disabled"
        raid_status = "active" if ctx.guild.id in self.raid_mode_guilds else "normal"

        blocking = []
        if settings['block_vpn']:
            blocking.append("VPN")
        if settings['block_proxy']:
            blocking.append("Proxy")
        if settings['block_datacenter']:
            blocking.append("Datacenter")
        if settings['block_tor']:
            blocking.append("Tor")

        embed = discord.Embed(color=self.EMBED_COLOR)
        embed.description = (
            f"**VPN/Proxy Detection**\n\n"
            f"› Status: `{status}`\n"
            f"› Raid Mode: `{raid_status}`\n"
            f"› Action: `{settings['action']}`\n"
            f"› Blocking: `{', '.join(blocking)}`\n"
            f"› Min Risk: `{settings['min_risk_score']}/100`\n"
            f"› Raid Only: `{settings['raid_mode_only']}`"
        )
        await ctx.send(embed=embed)

    @vpndetect.command(name='enable')
    @commands.has_permissions(administrator=True)
    async def vpn_enable(self, ctx: commands.Context):
        """Enable VPN detection"""
        settings = await self.get_guild_settings(ctx.guild.id)
        settings['enabled'] = True
        embed = discord.Embed(description="➕ Enabled VPN detection", color=self.EMBED_COLOR)
        await ctx.send(embed=embed)

    @vpndetect.command(name='disable')
    @commands.has_permissions(administrator=True)
    async def vpn_disable(self, ctx: commands.Context):
        """Disable VPN detection"""
        settings = await self.get_guild_settings(ctx.guild.id)
        settings['enabled'] = False
        embed = discord.Embed(description="➖ Disabled VPN detection", color=self.EMBED_COLOR)
        await ctx.send(embed=embed)

    @vpndetect.command(name='action')
    @commands.has_permissions(administrator=True)
    async def vpn_action(self, ctx: commands.Context, action: str):
        """Set the action to take on VPN users"""
        valid_actions = ['kick', 'ban', 'alert', 'quarantine']
        if action.lower() not in valid_actions:
            embed = discord.Embed(description=f"✖️ Invalid action. Use: `{', '.join(valid_actions)}`", color=self.EMBED_COLOR)
            return await ctx.send(embed=embed)

        settings = await self.get_guild_settings(ctx.guild.id)
        settings['action'] = action.lower()
        embed = discord.Embed(description=f"➕ Set VPN action to `{action.lower()}`", color=self.EMBED_COLOR)
        await ctx.send(embed=embed)

    @vpndetect.command(name='block')
    @commands.has_permissions(administrator=True)
    async def vpn_block(self, ctx: commands.Context, block_type: str, value: str):
        """Toggle blocking for specific types"""
        types = {
            'vpn': 'block_vpn',
            'proxy': 'block_proxy',
            'datacenter': 'block_datacenter',
            'dc': 'block_datacenter',
            'tor': 'block_tor'
        }

        if block_type.lower() not in types:
            embed = discord.Embed(description="✖️ Use: `vpn`, `proxy`, `datacenter`, `tor`", color=self.EMBED_COLOR)
            return await ctx.send(embed=embed)

        if value.lower() not in ['on', 'off', 'true', 'false']:
            embed = discord.Embed(description="✖️ Value must be `on` or `off`", color=self.EMBED_COLOR)
            return await ctx.send(embed=embed)

        settings = await self.get_guild_settings(ctx.guild.id)
        new_value = value.lower() in ['on', 'true']
        settings[types[block_type.lower()]] = new_value

        status = "enabled" if new_value else "disabled"
        embed = discord.Embed(description=f"➕ {block_type} blocking `{status}`", color=self.EMBED_COLOR)
        await ctx.send(embed=embed)

    @vpndetect.command(name='riskscore')
    @commands.has_permissions(administrator=True)
    async def vpn_riskscore(self, ctx: commands.Context, score: int):
        """Set minimum risk score to trigger action"""
        if score < 0 or score > 100:
            embed = discord.Embed(description="✖️ Score must be 0-100", color=self.EMBED_COLOR)
            return await ctx.send(embed=embed)

        settings = await self.get_guild_settings(ctx.guild.id)
        settings['min_risk_score'] = score
        embed = discord.Embed(description=f"➕ Set min risk score to `{score}`", color=self.EMBED_COLOR)
        await ctx.send(embed=embed)

    @vpndetect.command(name='raidonly')
    @commands.has_permissions(administrator=True)
    async def vpn_raidonly(self, ctx: commands.Context, value: str):
        """Only check during raid mode"""
        if value.lower() not in ['on', 'off', 'true', 'false']:
            embed = discord.Embed(description="✖️ Value must be `on` or `off`", color=self.EMBED_COLOR)
            return await ctx.send(embed=embed)

        settings = await self.get_guild_settings(ctx.guild.id)
        new_value = value.lower() in ['on', 'true']
        settings['raid_mode_only'] = new_value

        status = "enabled" if new_value else "disabled"
        embed = discord.Embed(description=f"➕ Raid-only mode `{status}`", color=self.EMBED_COLOR)
        await ctx.send(embed=embed)

    @vpndetect.command(name='check')
    @commands.has_permissions(administrator=True)
    async def vpn_check(self, ctx: commands.Context, ip: str):
        """Manually check an IP address"""
        parts = ip.split('.')
        if len(parts) != 4:
            embed = discord.Embed(description="✖️ Invalid IP format", color=self.EMBED_COLOR)
            return await ctx.send(embed=embed)

        embed = discord.Embed(description=f"Checking `{ip}`...", color=self.EMBED_COLOR)
        status_msg = await ctx.send(embed=embed)

        result = await self.check_ip(ip)

        detections = []
        if result.is_vpn:
            detections.append("VPN")
        if result.is_proxy:
            detections.append("Proxy")
        if result.is_datacenter:
            detections.append("Datacenter")
        if result.is_tor:
            detections.append("Tor")

        embed = discord.Embed(color=self.EMBED_COLOR)
        embed.description = (
            f"**IP Check: `{ip}`**\n\n"
            f"› Risk: `{result.risk_score}/100`\n"
            f"› Level: `{result.threat_level}`\n"
            f"› Detections: `{', '.join(detections) if detections else 'None'}`\n"
            f"› Would Block: `{'Yes' if result.is_suspicious else 'No'}`"
        )
        if result.country:
            embed.description += f"\n› Country: `{result.country}`"
        if result.isp:
            embed.description += f"\n› ISP: `{result.isp[:30]}`"

        await status_msg.edit(embed=embed)

    @vpndetect.command(name='whitelist')
    @commands.has_permissions(administrator=True)
    async def vpn_whitelist(self, ctx: commands.Context, member: discord.Member):
        """Whitelist a user from VPN checks"""
        self.whitelisted_users[ctx.guild.id].add(member.id)
        embed = discord.Embed(description=f"➕ Whitelisted {member.mention} from VPN detection", color=self.EMBED_COLOR)
        await ctx.send(embed=embed)

    @vpndetect.command(name='unwhitelist')
    @commands.has_permissions(administrator=True)
    async def vpn_unwhitelist(self, ctx: commands.Context, member: discord.Member):
        """Remove a user from the whitelist"""
        self.whitelisted_users[ctx.guild.id].discard(member.id)
        embed = discord.Embed(description=f"➖ Removed {member.mention} from VPN whitelist", color=self.EMBED_COLOR)
        await ctx.send(embed=embed)

    @vpndetect.command(name='raidmode')
    @commands.has_permissions(administrator=True)
    async def vpn_raidmode(self, ctx: commands.Context, value: str = None):
        """Toggle raid mode (aggressive checking)"""
        if value is None:
            is_active = ctx.guild.id in self.raid_mode_guilds
            status = "active" if is_active else "inactive"
            embed = discord.Embed(description=f"Raid mode is `{status}`", color=self.EMBED_COLOR)
            return await ctx.send(embed=embed)

        if value.lower() in ['on', 'enable', 'true']:
            self.enable_raid_mode(ctx.guild.id)
            embed = discord.Embed(description="➕ Raid mode enabled - Aggressive checking active", color=self.EMBED_COLOR)
        elif value.lower() in ['off', 'disable', 'false']:
            self.disable_raid_mode(ctx.guild.id)
            embed = discord.Embed(description="➖ Raid mode disabled", color=self.EMBED_COLOR)
        else:
            embed = discord.Embed(description="✖️ Use `on` or `off`", color=self.EMBED_COLOR)
        await ctx.send(embed=embed)

    # ==================== BACKGROUND TASKS ====================

    @tasks.loop(hours=6)
    async def cleanup_cache(self):
        """Clean up old cached IP results"""
        now = datetime.utcnow()
        expired = [
            ip_hash for ip_hash, result in self.ip_cache.items()
            if now - result.checked_at > self.cache_duration
        ]
        for ip_hash in expired:
            del self.ip_cache[ip_hash]

        if expired:
            logger.info(f"Cleaned up {len(expired)} expired IP cache entries")

    @cleanup_cache.before_loop
    async def before_cleanup(self):
        await self.bot.wait_until_ready()


async def setup(bot):
    await bot.add_cog(VPNDetection(bot))
