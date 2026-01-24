"""
Anti-Spam Protection Cog
========================
Spam detection and link filtering with database persistence.
Works with both ! prefix and / slash commands.
Only Server Owner and Bot Owner can use these commands.
"""
import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio
import logging
import re
import os
from typing import Dict, List, Set, Optional

logger = logging.getLogger('Offcialx.AntiSpam')
EMBED_COLOR = 0x2b2d31


class AntiSpam(commands.Cog):
    """Anti-Spam Protection System"""

    def __init__(self, bot):
        self.bot = bot
        self.db = None
        self._settings_loaded: set = set()

        # Owner IDs
        self.owner_ids: set = set()
        for oid in os.getenv('OWNER_IDS', '').split(','):
            try:
                self.owner_ids.add(int(oid.strip()))
            except:
                pass

        # Guild settings
        self.guild_settings: Dict[int, Dict] = {}

        # Spam tracking
        self.message_cache: Dict[int, Dict[int, List]] = defaultdict(lambda: defaultdict(list))
        self.warned_users: Dict[int, Set[int]] = defaultdict(set)

        # Patterns
        self.url_pattern = re.compile(r'https?://[^\s]+', re.IGNORECASE)
        self.invite_pattern = re.compile(r'(?:discord\.gg|discord(?:app)?\.com/invite)/[\w-]+', re.IGNORECASE)

        # Blocked domains
        self.shortener_domains = ['bit.ly', 'tinyurl.com', 't.co', 'goo.gl', 'ow.ly', 'is.gd', 'buff.ly', 'adf.ly', 'tiny.cc', 'j.mp']
        self.phishing_domains = ['discord-nitro.com', 'discordgift.com', 'free-nitro.com', 'discord-app.com', 'steamnity.com']

    def is_privileged(self, guild, user_id: int) -> bool:
        """Check if user is server owner or bot owner"""
        if user_id == guild.owner_id:
            return True
        if user_id in self.owner_ids:
            return True
        if self.bot.owner_ids and user_id in self.bot.owner_ids:
            return True
        return False

    async def owner_check(self, ctx) -> bool:
        """Check ownership and send error if not authorized"""
        if not self.is_privileged(ctx.guild, ctx.author.id):
            embed = discord.Embed(description="✕ Only server owner can use this command", color=EMBED_COLOR)
            await ctx.send(embed=embed)
            return False
        return True

    async def preload_all_settings(self):
        """Preload settings for all guilds on bot startup"""
        if not self.db:
            return

        logger.info("Preloading anti-spam settings for all guilds...")
        loaded_count = 0

        for guild in self.bot.guilds:
            try:
                db_settings = await self.db.get_guild_settings(guild.id, 'antispam')
                if db_settings:
                    self.guild_settings[guild.id] = {
                        'enabled': False,
                        'action': 'warn',
                        'message_limit': 5,
                        'message_timeframe': 5,
                        'allow_links': True,
                        'allow_invites': False,
                        'block_shorteners': True,
                        'block_phishing': True,
                        'link_whitelist': [],
                        'exempt_roles': [],
                        'exempt_channels': [],
                        'log_channel': None,
                    }
                    self.guild_settings[guild.id].update(db_settings)
                    loaded_count += 1
                self._settings_loaded.add(guild.id)
            except Exception as e:
                logger.warning(f'Failed to preload antispam settings for guild {guild.id}: {e}')

        logger.info(f"✅ Preloaded anti-spam settings for {loaded_count}/{len(self.bot.guilds)} guilds")

    async def get_settings(self, guild_id: int) -> Dict:
        """Get guild settings with database loading"""
        if guild_id not in self.guild_settings:
            self.guild_settings[guild_id] = {
                'enabled': False,
                'action': 'warn',
                'message_limit': 5,
                'message_timeframe': 5,
                'allow_links': True,
                'allow_invites': False,
                'block_shorteners': True,
                'block_phishing': True,
                'link_whitelist': [],
                'exempt_roles': [],
                'exempt_channels': [],
                'log_channel': None,
            }
            if self.db and guild_id not in self._settings_loaded:
                try:
                    db_settings = await self.db.get_guild_settings(guild_id, 'antispam')
                    if db_settings:
                        self.guild_settings[guild_id].update(db_settings)
                    self._settings_loaded.add(guild_id)
                except Exception as e:
                    logger.warning(f'Failed to load antispam settings: {e}')
        return self.guild_settings[guild_id]

    async def save_settings(self, guild_id: int):
        """Save guild settings to database"""
        if not self.db:
            return
        try:
            settings = self.guild_settings.get(guild_id, {})
            await self.db.save_guild_settings(guild_id, 'antispam', settings)
        except Exception as e:
            logger.warning(f'Failed to save antispam settings: {e}')

    # ==================== MAIN COMMAND GROUP ====================

    @commands.hybrid_group(name='antispam', aliases=['as'], invoke_without_command=True)
    @commands.guild_only()
    async def antispam(self, ctx: commands.Context):
        """View anti-spam protection status"""
        if not await self.owner_check(ctx):
            return

        settings = await self.get_settings(ctx.guild.id)
        status = "enabled" if settings['enabled'] else "disabled"

        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = (
            f"**Anti-Spam Protection**\n\n"
            f"› Status: `{status}`\n"
            f"› Action: `{settings['action']}`\n"
            f"› Message limit: `{settings['message_limit']}` in `{settings['message_timeframe']}s`\n\n"
            f"**Link Filtering**\n"
            f"› Links: `{'allowed' if settings['allow_links'] else 'blocked'}`\n"
            f"› Invites: `{'allowed' if settings['allow_invites'] else 'blocked'}`\n"
            f"› Shorteners: `{'blocked' if settings['block_shorteners'] else 'allowed'}`\n"
            f"› Phishing: `{'blocked' if settings['block_phishing'] else 'allowed'}`\n"
            f"› Whitelist: `{len(settings.get('link_whitelist', []))}` domains"
        )
        await ctx.send(embed=embed)

    @antispam.command(name='enable')
    @commands.guild_only()
    async def antispam_enable(self, ctx: commands.Context):
        """Enable anti-spam protection"""
        if not await self.owner_check(ctx):
            return

        settings = await self.get_settings(ctx.guild.id)
        settings['enabled'] = True
        await self.save_settings(ctx.guild.id)

        embed = discord.Embed(description="+ Enabled anti-spam protection", color=EMBED_COLOR)
        await ctx.send(embed=embed)

    @antispam.command(name='disable')
    @commands.guild_only()
    async def antispam_disable(self, ctx: commands.Context):
        """Disable anti-spam protection"""
        if not await self.owner_check(ctx):
            return

        settings = await self.get_settings(ctx.guild.id)
        settings['enabled'] = False
        await self.save_settings(ctx.guild.id)

        embed = discord.Embed(description="− Disabled anti-spam protection", color=EMBED_COLOR)
        await ctx.send(embed=embed)

    @antispam.command(name='action')
    @commands.guild_only()
    @app_commands.describe(action="The action to take on spam (warn/mute/kick/ban)")
    async def antispam_action(self, ctx: commands.Context, action: str):
        """Set spam action (warn/mute/kick/ban)"""
        if not await self.owner_check(ctx):
            return

        valid = ['warn', 'mute', 'kick', 'ban']
        if action.lower() not in valid:
            embed = discord.Embed(description=f"✕ Invalid action. Use: {', '.join(valid)}", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        settings = await self.get_settings(ctx.guild.id)
        settings['action'] = action.lower()
        await self.save_settings(ctx.guild.id)

        embed = discord.Embed(description=f"+ Set spam action to `{action.lower()}`", color=EMBED_COLOR)
        await ctx.send(embed=embed)

    @antispam.command(name='links')
    @commands.guild_only()
    @app_commands.describe(allow="Allow or block links (true/false)")
    async def antispam_links(self, ctx: commands.Context, allow: bool):
        """Toggle link blocking (true/false)"""
        if not await self.owner_check(ctx):
            return

        settings = await self.get_settings(ctx.guild.id)
        settings['allow_links'] = allow
        await self.save_settings(ctx.guild.id)

        status = "allowed" if allow else "blocked"
        embed = discord.Embed(description=f"+ Links are now {status}", color=EMBED_COLOR)
        await ctx.send(embed=embed)

    @antispam.command(name='invites')
    @commands.guild_only()
    @app_commands.describe(allow="Allow or block Discord invites (true/false)")
    async def antispam_invites(self, ctx: commands.Context, allow: bool):
        """Toggle invite blocking (true/false)"""
        if not await self.owner_check(ctx):
            return

        settings = await self.get_settings(ctx.guild.id)
        settings['allow_invites'] = allow
        await self.save_settings(ctx.guild.id)

        status = "allowed" if allow else "blocked"
        embed = discord.Embed(description=f"+ Discord invites are now {status}", color=EMBED_COLOR)
        await ctx.send(embed=embed)

    @antispam.command(name='shorteners')
    @commands.guild_only()
    @app_commands.describe(block="Block URL shorteners (true/false)")
    async def antispam_shorteners(self, ctx: commands.Context, block: bool):
        """Toggle URL shortener blocking (true/false)"""
        if not await self.owner_check(ctx):
            return

        settings = await self.get_settings(ctx.guild.id)
        settings['block_shorteners'] = block
        await self.save_settings(ctx.guild.id)

        status = "blocked" if block else "allowed"
        embed = discord.Embed(description=f"+ URL shorteners are now {status}", color=EMBED_COLOR)
        await ctx.send(embed=embed)

    @antispam.command(name='phishing')
    @commands.guild_only()
    @app_commands.describe(block="Block phishing links (true/false)")
    async def antispam_phishing(self, ctx: commands.Context, block: bool):
        """Toggle phishing link blocking (true/false)"""
        if not await self.owner_check(ctx):
            return

        settings = await self.get_settings(ctx.guild.id)
        settings['block_phishing'] = block
        await self.save_settings(ctx.guild.id)

        status = "blocked" if block else "allowed"
        embed = discord.Embed(description=f"+ Phishing links are now {status}", color=EMBED_COLOR)
        await ctx.send(embed=embed)

    @antispam.command(name='setlog')
    @commands.guild_only()
    @app_commands.describe(channel="The channel to log spam events")
    async def antispam_setlog(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set spam log channel"""
        if not await self.owner_check(ctx):
            return

        settings = await self.get_settings(ctx.guild.id)
        settings['log_channel'] = channel.id
        await self.save_settings(ctx.guild.id)

        embed = discord.Embed(description=f"+ Set spam log to {channel.mention}", color=EMBED_COLOR)
        await ctx.send(embed=embed)

    @antispam.command(name='exempt')
    @commands.guild_only()
    @app_commands.describe(role="Role to exempt from anti-spam")
    async def antispam_exempt_role(self, ctx: commands.Context, role: discord.Role):
        """Exempt a role from anti-spam"""
        if not await self.owner_check(ctx):
            return

        settings = await self.get_settings(ctx.guild.id)
        if 'exempt_roles' not in settings:
            settings['exempt_roles'] = []

        if role.id not in settings['exempt_roles']:
            settings['exempt_roles'].append(role.id)
            await self.save_settings(ctx.guild.id)
            embed = discord.Embed(description=f"+ Exempted {role.mention} from anti-spam", color=EMBED_COLOR)
        else:
            embed = discord.Embed(description=f"✕ {role.mention} is already exempt", color=EMBED_COLOR)

        await ctx.send(embed=embed)

    @antispam.command(name='unexempt')
    @commands.guild_only()
    @app_commands.describe(role="Role to remove from exemption")
    async def antispam_unexempt_role(self, ctx: commands.Context, role: discord.Role):
        """Remove role exemption from anti-spam"""
        if not await self.owner_check(ctx):
            return

        settings = await self.get_settings(ctx.guild.id)
        if role.id in settings.get('exempt_roles', []):
            settings['exempt_roles'].remove(role.id)
            await self.save_settings(ctx.guild.id)
            embed = discord.Embed(description=f"− Removed {role.mention} from exemption", color=EMBED_COLOR)
        else:
            embed = discord.Embed(description=f"✕ {role.mention} is not exempt", color=EMBED_COLOR)

        await ctx.send(embed=embed)

    @antispam.command(name='limit')
    @commands.guild_only()
    @app_commands.describe(count="Number of messages", seconds="Time window in seconds")
    async def antispam_limit(self, ctx: commands.Context, count: int, seconds: int = 5):
        """Set message limit (count in seconds)"""
        if not await self.owner_check(ctx):
            return

        if count < 1 or count > 50:
            embed = discord.Embed(description="✕ Count must be between 1 and 50", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        if seconds < 1 or seconds > 60:
            embed = discord.Embed(description="✕ Seconds must be between 1 and 60", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        settings = await self.get_settings(ctx.guild.id)
        settings['message_limit'] = count
        settings['message_timeframe'] = seconds
        await self.save_settings(ctx.guild.id)

        embed = discord.Embed(description=f"+ Set limit to `{count}` messages in `{seconds}` seconds", color=EMBED_COLOR)
        await ctx.send(embed=embed)

    # ==================== WHITELIST COMMANDS ====================

    @antispam.group(name='whitelist', invoke_without_command=True)
    @commands.guild_only()
    async def antispam_whitelist(self, ctx: commands.Context):
        """View whitelisted domains"""
        if not await self.owner_check(ctx):
            return

        settings = await self.get_settings(ctx.guild.id)
        whitelist = settings.get('link_whitelist', [])

        if not whitelist:
            embed = discord.Embed(description="No whitelisted domains", color=EMBED_COLOR)
        else:
            domains = "\n".join([f"› `{d}`" for d in whitelist])
            embed = discord.Embed(description=f"**Whitelisted Domains**\n\n{domains}", color=EMBED_COLOR)

        await ctx.send(embed=embed)

    @antispam_whitelist.command(name='add')
    @commands.guild_only()
    @app_commands.describe(domain="Domain to whitelist (e.g., youtube.com)")
    async def whitelist_add(self, ctx: commands.Context, domain: str):
        """Add domain to whitelist"""
        if not await self.owner_check(ctx):
            return

        domain = domain.lower().replace('https://', '').replace('http://', '').split('/')[0]
        settings = await self.get_settings(ctx.guild.id)

        if 'link_whitelist' not in settings:
            settings['link_whitelist'] = []

        if domain in settings['link_whitelist']:
            embed = discord.Embed(description=f"✕ `{domain}` already whitelisted", color=EMBED_COLOR)
        else:
            settings['link_whitelist'].append(domain)
            await self.save_settings(ctx.guild.id)
            embed = discord.Embed(description=f"+ Added `{domain}` to whitelist", color=EMBED_COLOR)

        await ctx.send(embed=embed)

    @antispam_whitelist.command(name='remove')
    @commands.guild_only()
    @app_commands.describe(domain="Domain to remove from whitelist")
    async def whitelist_remove(self, ctx: commands.Context, domain: str):
        """Remove domain from whitelist"""
        if not await self.owner_check(ctx):
            return

        domain = domain.lower().replace('https://', '').replace('http://', '').split('/')[0]
        settings = await self.get_settings(ctx.guild.id)

        if domain not in settings.get('link_whitelist', []):
            embed = discord.Embed(description=f"✕ `{domain}` not in whitelist", color=EMBED_COLOR)
        else:
            settings['link_whitelist'].remove(domain)
            await self.save_settings(ctx.guild.id)
            embed = discord.Embed(description=f"− Removed `{domain}` from whitelist", color=EMBED_COLOR)

        await ctx.send(embed=embed)

    @antispam_whitelist.command(name='clear')
    @commands.guild_only()
    async def whitelist_clear(self, ctx: commands.Context):
        """Clear all whitelisted domains"""
        if not await self.owner_check(ctx):
            return

        settings = await self.get_settings(ctx.guild.id)
        count = len(settings.get('link_whitelist', []))
        settings['link_whitelist'] = []
        await self.save_settings(ctx.guild.id)

        embed = discord.Embed(description=f"+ Cleared `{count}` domains", color=EMBED_COLOR)
        await ctx.send(embed=embed)

    # ==================== STATUS COMMAND ====================

    @antispam.command(name='status')
    @commands.guild_only()
    async def antispam_status(self, ctx: commands.Context):
        """View detailed anti-spam status"""
        if not await self.owner_check(ctx):
            return

        settings = await self.get_settings(ctx.guild.id)
        status = "enabled" if settings['enabled'] else "disabled"

        exempt_roles = []
        for role_id in settings.get('exempt_roles', []):
            role = ctx.guild.get_role(role_id)
            if role:
                exempt_roles.append(role.mention)

        log_channel = None
        if settings.get('log_channel'):
            ch = ctx.guild.get_channel(settings['log_channel'])
            if ch:
                log_channel = ch.mention

        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = (
            f"**Anti-Spam Status**\n\n"
            f"› Status: `{status}`\n"
            f"› Action: `{settings['action']}`\n"
            f"› Limit: `{settings['message_limit']}` msgs / `{settings['message_timeframe']}s`\n"
            f"› Log: {log_channel or 'Not set'}\n\n"
            f"**Link Filtering**\n"
            f"› Links: `{'allowed' if settings['allow_links'] else 'blocked'}`\n"
            f"› Invites: `{'allowed' if settings['allow_invites'] else 'blocked'}`\n"
            f"› Shorteners: `{'blocked' if settings['block_shorteners'] else 'allowed'}`\n"
            f"› Phishing: `{'blocked' if settings['block_phishing'] else 'allowed'}`\n\n"
            f"**Exemptions**\n"
            f"› Whitelisted domains: `{len(settings.get('link_whitelist', []))}`\n"
            f"› Exempt roles: {', '.join(exempt_roles) if exempt_roles else 'None'}"
        )
        await ctx.send(embed=embed)

    # ==================== MESSAGE LISTENER ====================

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Check messages for spam and blocked links"""
        if not message.guild or message.author.bot:
            return

        if message.author.id == self.bot.user.id:
            return

        settings = await self.get_settings(message.guild.id)
        if not settings['enabled']:
            return

        # Check exemptions
        if message.channel.id in settings.get('exempt_channels', []):
            return

        if any(r.id in settings.get('exempt_roles', []) for r in message.author.roles):
            return

        if self.is_privileged(message.guild, message.author.id):
            return

        content = message.content.lower()
        violation = None

        # Check phishing
        if settings['block_phishing']:
            for domain in self.phishing_domains:
                if domain in content:
                    violation = "phishing link"
                    break

        # Check shorteners
        if not violation and settings['block_shorteners']:
            for domain in self.shortener_domains:
                if domain in content:
                    violation = "URL shortener"
                    break

        # Check invites
        if not violation and not settings['allow_invites']:
            if self.invite_pattern.search(message.content):
                violation = "Discord invite"

        # Check links
        if not violation and not settings['allow_links']:
            urls = self.url_pattern.findall(message.content)
            whitelist = settings.get('link_whitelist', [])
            for url in urls:
                if not any(w in url.lower() for w in whitelist):
                    violation = "link"
                    break

        if violation:
            try:
                await message.delete()
                embed = discord.Embed(
                    description=f"✕ {message.author.mention}, {violation}s are not allowed here",
                    color=EMBED_COLOR
                )
                warn_msg = await message.channel.send(embed=embed)
                await asyncio.sleep(5)
                await warn_msg.delete()

                # Log if configured
                if settings.get('log_channel'):
                    log_ch = message.guild.get_channel(settings['log_channel'])
                    if log_ch:
                        log_embed = discord.Embed(color=EMBED_COLOR)
                        log_embed.description = (
                            f"**Spam Detected**\n\n"
                            f"› User: {message.author.mention}\n"
                            f"› Channel: {message.channel.mention}\n"
                            f"› Violation: `{violation}`\n"
                            f"› Content: `{message.content[:100]}...`"
                        )
                        await log_ch.send(embed=log_embed)
            except Exception as e:
                logger.warning(f"Failed to handle spam: {e}")


async def setup(bot):
    await bot.add_cog(AntiSpam(bot))
