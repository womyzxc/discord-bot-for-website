"""
Anti-Raid Protection Cog
========================
Detects and prevents raid attempts including:
- Mass join detection
- New account detection
- Profile similarity detection
- Coordinated join patterns
"""
import discord
from discord.ext import commands
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio
import logging
from typing import Dict, List, Set
import re

logger = logging.getLogger('Offcialx.AntiRaid')


class AntiRaid(commands.Cog):
    """Anti-Raid Protection System"""

    def __init__(self, bot):
        self.bot = bot
        self.db = None  # Will be injected by bot
        self._settings_loaded: set = set()

        # Owner IDs from environment
        self.owner_ids: set = set()
        import os
        for oid in os.getenv('OWNER_IDS', '').split(','):
            try:
                self.owner_ids.add(int(oid.strip()))
            except (ValueError, AttributeError):
                pass  # Invalid or empty ID - skip

        # Guild settings
        self.guild_settings: Dict[int, Dict] = {}
        # Join tracking
        self.recent_joins: Dict[int, List[Dict]] = defaultdict(list)
        # Raid mode status
        self.raid_mode: Dict[int, Dict] = {}
        # Suspicious accounts queue
        self.suspicious_accounts: Dict[int, Set[int]] = defaultdict(set)
        # Pattern detection
        self.name_patterns: Dict[int, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

    async def preload_all_settings(self):
        """Preload settings for all guilds on bot startup"""
        if not self.db:
            return

        logger.info("Preloading anti-raid settings for all guilds...")
        loaded_count = 0

        for guild in self.bot.guilds:
            try:
                db_settings = await self.db.get_guild_settings(guild.id, 'antiraid')
                if db_settings:
                    self.guild_settings[guild.id] = {
                        'enabled': True,
                        'join_threshold': 10,
                        'join_timeframe': 10,
                        'min_account_age': 7,
                        'auto_raid_mode': True,
                        'raid_mode_duration': 300,
                        'verification_level': 'medium',
                        'action': 'kick',
                        'log_channel': None,
                        'alert_role': None,
                        'smart_detection': True,
                    }
                    self.guild_settings[guild.id].update(db_settings)
                    loaded_count += 1
                self._settings_loaded.add(guild.id)
            except Exception as e:
                logger.warning(f'Failed to preload antiraid settings for guild {guild.id}: {e}')

        logger.info(f"✅ Preloaded anti-raid settings for {loaded_count}/{len(self.bot.guilds)} guilds")

    async def get_settings(self, guild_id: int) -> Dict:
        """Get guild settings - loads from database if available"""
        if guild_id not in self.guild_settings:
            self.guild_settings[guild_id] = {
                'enabled': True,
                'join_threshold': 10,
                'join_timeframe': 10,
                'min_account_age': 7,  # days
                'auto_raid_mode': True,
                'raid_mode_duration': 300,  # seconds
                'verification_level': 'medium',  # none, low, medium, high, highest
                'action': 'kick',  # kick, ban, quarantine
                'log_channel': None,
                'alert_role': None,
                'smart_detection': True,
            }

            # Try to load from database
            if self.db and guild_id not in self._settings_loaded:
                try:
                    db_settings = await self.db.get_guild_settings(guild_id, 'antiraid')
                    if db_settings:
                        self.guild_settings[guild_id].update(db_settings)
                    self._settings_loaded.add(guild_id)
                except Exception as e:
                    logger.warning(f'Failed to load antiraid settings from database: {e}')

        return self.guild_settings[guild_id]

    async def save_settings(self, guild_id: int):
        """Save guild settings to database"""
        if not self.db:
            return

        try:
            settings = self.guild_settings.get(guild_id, {})
            await self.db.save_guild_settings(guild_id, 'antiraid', settings)
        except Exception as e:
            logger.warning(f'Failed to save antiraid settings to database: {e}')

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
            embed = discord.Embed(description="✕ Only server owner can use this command", color=0x2b2d31)
            await ctx.send(embed=embed)
            return False
        return True

    def is_new_account(self, member: discord.Member, days: int) -> bool:
        """Check if account is newer than specified days"""
        age = datetime.utcnow() - member.created_at.replace(tzinfo=None)
        return age.days < days

    def detect_suspicious_name(self, name: str) -> List[str]:
        """Detect suspicious username patterns"""
        flags = []

        # Check for common raid patterns
        patterns = [
            (r'^[a-zA-Z]+\d{4,}$', 'Automated name pattern'),
            (r'^.{1,3}$', 'Very short name'),
            (r'^\d+$', 'Numbers only'),
            (r'(.)\1{4,}', 'Repeated characters'),
            (r'raid|nuke|destroy|spam', 'Suspicious keywords'),
            (r'^[A-Z]{5,}$', 'All caps'),
        ]

        for pattern, reason in patterns:
            if re.search(pattern, name, re.IGNORECASE):
                flags.append(reason)

        return flags

    def calculate_raid_score(self, member: discord.Member, settings: Dict) -> int:
        """Calculate a raid likelihood score for a member"""
        score = 0

        # New account
        if self.is_new_account(member, settings['min_account_age']):
            score += 30

        # No avatar
        if member.avatar is None:
            score += 20

        # Suspicious name
        name_flags = self.detect_suspicious_name(member.name)
        score += len(name_flags) * 15

        # No bio/about me (can't check directly, but new accounts rarely have)
        if self.is_new_account(member, 1):  # Created within 24 hours
            score += 25

        return min(score, 100)

    async def enable_raid_mode(self, guild: discord.Guild, reason: str):
        """Enable raid mode for a guild"""
        settings = await self.get_settings(guild.id)

        self.raid_mode[guild.id] = {
            'enabled': True,
            'started': datetime.utcnow(),
            'reason': reason,
            'original_verification': guild.verification_level
        }

        # Increase verification level
        try:
            if settings['verification_level'] == 'highest':
                await guild.edit(verification_level=discord.VerificationLevel.highest)
            elif settings['verification_level'] == 'high':
                await guild.edit(verification_level=discord.VerificationLevel.high)
            elif settings['verification_level'] == 'medium':
                await guild.edit(verification_level=discord.VerificationLevel.medium)
        except discord.Forbidden:
            pass

        logger.warning(f'RAID MODE ENABLED in {guild.name}: {reason}')

        # Log the event
        await self.log_raid_event(guild, 'raid_mode_enabled', reason)

        # Schedule automatic disable
        if settings['raid_mode_duration'] > 0:
            await asyncio.sleep(settings['raid_mode_duration'])
            await self.disable_raid_mode(guild)

    async def disable_raid_mode(self, guild: discord.Guild):
        """Disable raid mode for a guild"""
        if guild.id not in self.raid_mode:
            return

        mode = self.raid_mode[guild.id]
        if not mode['enabled']:
            return

        # Restore original verification level
        try:
            await guild.edit(verification_level=mode['original_verification'])
        except:
            pass

        self.raid_mode[guild.id]['enabled'] = False
        logger.info(f'RAID MODE DISABLED in {guild.name}')

        await self.log_raid_event(guild, 'raid_mode_disabled', 'Automatic timeout')

    async def log_raid_event(self, guild: discord.Guild, event_type: str, details: str):
        """Log a raid-related event"""
        settings = await self.get_settings(guild.id)

        if not settings['log_channel']:
            return

        channel = guild.get_channel(settings['log_channel'])
        if not channel:
            return

        colors = {
            'raid_mode_enabled': discord.Color.red(),
            'raid_mode_disabled': discord.Color.green(),
            'suspicious_join': discord.Color.orange(),
            'raid_detected': discord.Color.dark_red(),
        }

        embed = discord.Embed(
            title=f"🚨 {event_type.replace('_', ' ').title()}",
            description=details,
            color=colors.get(event_type, discord.Color.blue()),
            timestamp=datetime.utcnow()
        )

        try:
            # Alert role if set
            if settings['alert_role'] and event_type in ['raid_detected', 'raid_mode_enabled']:
                role = guild.get_role(settings['alert_role'])
                if role:
                    await channel.send(f"{role.mention}", embed=embed)
                    return

            await channel.send(embed=embed)
        except:
            pass

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Monitor member joins for raid detection"""
        guild = member.guild
        settings = await self.get_settings(guild.id)

        if not settings['enabled']:
            return

        now = datetime.utcnow()

        # Track the join
        self.recent_joins[guild.id].append({
            'member_id': member.id,
            'time': now,
            'name': member.name,
            'created': member.created_at.replace(tzinfo=None)
        })

        # Clean old entries
        cutoff = now - timedelta(seconds=settings['join_timeframe'])
        self.recent_joins[guild.id] = [
            j for j in self.recent_joins[guild.id]
            if j['time'] > cutoff
        ]

        recent_count = len(self.recent_joins[guild.id])

        # Check for mass join (raid)
        if recent_count >= settings['join_threshold']:
            if settings['auto_raid_mode'] and guild.id not in self.raid_mode:
                await self.enable_raid_mode(
                    guild,
                    f"Mass join detected: {recent_count} joins in {settings['join_timeframe']}s"
                )

            # Take action on joining members during raid
            await self.handle_raid_member(member, settings)
            return

        # Calculate raid score for individual suspicious detection
        raid_score = self.calculate_raid_score(member, settings)

        if raid_score >= 60:  # High suspicion threshold
            self.suspicious_accounts[guild.id].add(member.id)

            await self.log_raid_event(
                guild,
                'suspicious_join',
                f"**{member}** joined with high risk score: {raid_score}/100\n"
                f"Account age: {(now - member.created_at.replace(tzinfo=None)).days} days\n"
                f"Flags: {', '.join(self.detect_suspicious_name(member.name)) or 'None'}"
            )

            # If raid mode is active, take action
            if guild.id in self.raid_mode and self.raid_mode[guild.id].get('enabled'):
                await self.handle_raid_member(member, settings)

    async def handle_raid_member(self, member: discord.Member, settings: Dict):
        """Handle a member during a raid"""
        action = settings['action']

        try:
            if action == 'ban':
                await member.ban(reason="[AntiRaid] Raid detection - automatic action")
            elif action == 'kick':
                await member.kick(reason="[AntiRaid] Raid detection - automatic action")
            elif action == 'quarantine':
                # Remove all roles (quarantine)
                await member.edit(roles=[], reason="[AntiRaid] Quarantine - suspicious join during raid")

            logger.info(f'Raid action taken on {member}: {action}')
        except discord.Forbidden:
            logger.error(f'Cannot take raid action on {member} - missing permissions')

    # Minimal embed color
    EMBED_COLOR = 0x2b2d31

    # ==================== COMMANDS ====================

    @commands.hybrid_group(name='antiraid', aliases=['ar'], invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def antiraid(self, ctx: commands.Context):
        """Anti-Raid configuration commands"""
        if not await self.owner_check(ctx):
            return

        settings = await self.get_settings(ctx.guild.id)
        raid_active = ctx.guild.id in self.raid_mode and self.raid_mode[ctx.guild.id].get('enabled', False)
        status = "RAID MODE" if raid_active else ("enabled" if settings['enabled'] else "disabled")

        embed = discord.Embed(color=self.EMBED_COLOR)
        embed.description = (
            f"**Anti-Raid Protection**\n\n"
            f"› Status: `{status}`\n"
            f"› Action: `{settings['action']}`\n"
            f"› Min age: `{settings['min_account_age']} days`\n"
            f"› Threshold: `{settings['join_threshold']} joins/{settings['join_timeframe']}s`"
        )

        if raid_active:
            mode = self.raid_mode[ctx.guild.id]
            embed.description += f"\n\n**Raid Mode Active**\n› Reason: `{mode['reason']}`"

        await ctx.send(embed=embed)

    @antiraid.command(name='enable')
    @commands.has_permissions(administrator=True)
    async def antiraid_enable(self, ctx: commands.Context):
        """Enable anti-raid protection"""
        if not await self.owner_check(ctx):
            return

        settings = await self.get_settings(ctx.guild.id)
        settings['enabled'] = True
        await self.save_settings(ctx.guild.id)

        embed = discord.Embed(description="+ Enabled anti-raid protection", color=self.EMBED_COLOR)
        await ctx.send(embed=embed)

    @antiraid.command(name='disable')
    @commands.has_permissions(administrator=True)
    async def antiraid_disable(self, ctx: commands.Context):
        """Disable anti-raid protection"""
        if not await self.owner_check(ctx):
            return

        settings = await self.get_settings(ctx.guild.id)
        settings['enabled'] = False
        await self.save_settings(ctx.guild.id)

        embed = discord.Embed(description="− Disabled anti-raid protection", color=self.EMBED_COLOR)
        await ctx.send(embed=embed)

    @antiraid.command(name='raidmode')
    @commands.has_permissions(administrator=True)
    async def antiraid_raidmode(self, ctx: commands.Context, action: str = 'toggle'):
        """Toggle raid mode manually"""
        if not await self.owner_check(ctx):
            return

        if action.lower() in ['on', 'enable']:
            await self.enable_raid_mode(ctx.guild, "Manually enabled")
            embed = discord.Embed(description="+ Raid mode enabled", color=self.EMBED_COLOR)
        elif action.lower() in ['off', 'disable']:
            await self.disable_raid_mode(ctx.guild)
            embed = discord.Embed(description="− Raid mode disabled", color=self.EMBED_COLOR)
        else:
            if ctx.guild.id in self.raid_mode and self.raid_mode[ctx.guild.id].get('enabled'):
                await self.disable_raid_mode(ctx.guild)
                embed = discord.Embed(description="− Raid mode disabled", color=self.EMBED_COLOR)
            else:
                await self.enable_raid_mode(ctx.guild, "Manually enabled")
                embed = discord.Embed(description="+ Raid mode enabled", color=self.EMBED_COLOR)

        await ctx.send(embed=embed)

    @antiraid.command(name='action')
    @commands.has_permissions(administrator=True)
    async def antiraid_action(self, ctx: commands.Context, action: str):
        """Set raid action (kick/ban/quarantine)"""
        if not await self.owner_check(ctx):
            return

        valid = ['kick', 'ban', 'quarantine']
        if action.lower() not in valid:
            embed = discord.Embed(description=f"✕ Invalid action. Use: `{', '.join(valid)}`", color=self.EMBED_COLOR)
            return await ctx.send(embed=embed)

        settings = await self.get_settings(ctx.guild.id)
        settings['action'] = action.lower()
        await self.save_settings(ctx.guild.id)

        embed = discord.Embed(description=f"+ Set raid action to `{action.lower()}`", color=self.EMBED_COLOR)
        await ctx.send(embed=embed)

    @antiraid.command(name='threshold')
    @commands.has_permissions(administrator=True)
    async def antiraid_threshold(self, ctx: commands.Context, joins: int, timeframe: int = 10):
        """Set join threshold (joins in timeframe seconds)"""
        if not await self.owner_check(ctx):
            return

        if joins < 3 or joins > 50:
            embed = discord.Embed(description="✕ Joins must be 3-50", color=self.EMBED_COLOR)
            return await ctx.send(embed=embed)

        if timeframe < 5 or timeframe > 60:
            embed = discord.Embed(description="✕ Timeframe must be 5-60 seconds", color=self.EMBED_COLOR)
            return await ctx.send(embed=embed)

        settings = await self.get_settings(ctx.guild.id)
        settings['join_threshold'] = joins
        settings['join_timeframe'] = timeframe
        await self.save_settings(ctx.guild.id)

        embed = discord.Embed(description=f"+ Set threshold to `{joins} joins/{timeframe}s`", color=self.EMBED_COLOR)
        await ctx.send(embed=embed)

    @antiraid.command(name='minage')
    @commands.has_permissions(administrator=True)
    async def antiraid_minage(self, ctx: commands.Context, days: int):
        """Set minimum account age in days"""
        if not await self.owner_check(ctx):
            return

        if days < 0 or days > 365:
            embed = discord.Embed(description="✕ Days must be 0-365", color=self.EMBED_COLOR)
            return await ctx.send(embed=embed)

        settings = await self.get_settings(ctx.guild.id)
        settings['min_account_age'] = days
        await self.save_settings(ctx.guild.id)

        embed = discord.Embed(description=f"+ Set min account age to `{days} days`", color=self.EMBED_COLOR)
        await ctx.send(embed=embed)

    @antiraid.command(name='status')
    @commands.has_permissions(administrator=True)
    async def antiraid_status(self, ctx: commands.Context):
        """View detailed anti-raid status"""
        if not await self.owner_check(ctx):
            return

        settings = await self.get_settings(ctx.guild.id)
        raid_active = ctx.guild.id in self.raid_mode and self.raid_mode[ctx.guild.id].get('enabled', False)
        recent = len(self.recent_joins.get(ctx.guild.id, []))
        suspicious = len(self.suspicious_accounts.get(ctx.guild.id, set()))

        status = "RAID MODE" if raid_active else ("enabled" if settings['enabled'] else "disabled")

        embed = discord.Embed(color=self.EMBED_COLOR)
        embed.description = (
            f"**Anti-Raid Status**\n\n"
            f"› Status: `{status}`\n"
            f"› Recent joins: `{recent}`\n"
            f"› Suspicious accounts: `{suspicious}`\n"
            f"› Action: `{settings['action']}`\n"
            f"› Threshold: `{settings['join_threshold']}/{settings['join_timeframe']}s`\n"
            f"› Min age: `{settings['min_account_age']} days`\n"
            f"› Auto raid mode: `{settings['auto_raid_mode']}`"
        )
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(AntiRaid(bot))
