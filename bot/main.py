"""
Offcialx Anti-Nuke Security Bot
================================
A military-grade Discord security bot with advanced anti-nuke,
anti-selfbot, and comprehensive server protection features.

Features:
- Anti-Nuke Protection (mass ban/kick/channel deletion detection)
- Anti-Selfbot Detection
- Anti-Raid Protection
- Anti-Spam System
- Whitelist Management
- Permission Monitoring
- Audit Log Analysis
- Lockdown Mode
- Quarantine System
- Backup & Restore
- Threat Intelligence (AI-Powered)
- Real-time Alerts
- Slash Commands Support
- Persistent Database Storage

Author: Offcialx Team
Version: 3.0.0
"""

import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('Offcialx')

# Bot configuration
class BotConfig:
    TOKEN = os.getenv('DISCORD_BOT_TOKEN', '')
    PREFIX = os.getenv('BOT_PREFIX', '!')

    # Developer/Owner IDs - these users have full control
    # Add your developer ID here as fallback
    DEFAULT_OWNER_IDS = [1184454687865438218]  # Developer ID

    # Load from environment + add defaults
    _env_owners = [int(id) for id in os.getenv('OWNER_IDS', '').split(',') if id.strip()]
    OWNER_IDS = list(set(_env_owners + DEFAULT_OWNER_IDS))

    DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/offcialx.db')

    # Security thresholds - ULTRA MAXIMUM PROTECTION (Immediate/Auto)
    MASS_BAN_THRESHOLD = 1  # INSTANT - 1 ban triggers immediately
    MASS_KICK_THRESHOLD = 1  # INSTANT - 1 kick triggers immediately
    MASS_CHANNEL_DELETE_THRESHOLD = 1  # INSTANT - 1 channel delete triggers
    MASS_CHANNEL_CREATE_THRESHOLD = 1  # INSTANT - 1 channel create triggers
    MASS_CHANNEL_RENAME_THRESHOLD = 1  # INSTANT - 1 channel rename triggers
    MASS_ROLE_DELETE_THRESHOLD = 1  # INSTANT - 1 role delete triggers
    MASS_ROLE_CREATE_THRESHOLD = 1  # INSTANT - 1 role create triggers
    MASS_WEBHOOK_CREATE_THRESHOLD = 1  # INSTANT - 1 webhook triggers
    MASS_EMOJI_DELETE_THRESHOLD = 1  # INSTANT - 1 emoji delete triggers
    MASS_STICKER_DELETE_THRESHOLD = 1  # INSTANT - 1 sticker delete triggers
    MASS_THREAD_DELETE_THRESHOLD = 1  # INSTANT - 1 thread delete triggers
    MASS_PRUNE_THRESHOLD = 1  # INSTANT - 1 prune triggers
    MASS_INVITE_THRESHOLD = 1  # INSTANT - 1 invite spam triggers
    ACTION_TIMEFRAME = 3  # 3 seconds - ultra fast detection

    # Anti-spam thresholds
    MESSAGE_THRESHOLD = 10
    MESSAGE_TIMEFRAME = 5
    DUPLICATE_THRESHOLD = 5
    MENTION_THRESHOLD = 10
    EMOJI_THRESHOLD = 20

    # Anti-raid thresholds
    JOIN_THRESHOLD = 10
    JOIN_TIMEFRAME = 10
    NEW_ACCOUNT_DAYS = 7

    # Lockdown settings
    LOCKDOWN_DURATION = 300

# Minimal embed color
EMBED_COLOR = 0x2b2d31

# Intents
intents = discord.Intents.all()

class OffcialxBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned_or(BotConfig.PREFIX),
            intents=intents,
            help_command=None,
            owner_ids=set(BotConfig.OWNER_IDS) if BotConfig.OWNER_IDS else None
        )
        self.start_time = datetime.utcnow()
        self.config = BotConfig
        self.db = None  # Will be set after database init
        self._commands_synced = False  # Track if commands have been synced

    async def setup_hook(self):
        """Load all cogs/extensions and initialize database"""

        # Initialize audit log cache
        try:
            from utils.audit_cache import init_audit_cache
            self.audit_cache = init_audit_cache(self)
            logger.info('✅ Audit log cache initialized')
        except Exception as e:
            logger.error(f'❌ Audit cache initialization failed: {e}')
            self.audit_cache = None

        # Initialize database first - Use PostgreSQL if DATABASE_URL is set
        try:
            database_url = os.getenv('DATABASE_URL', '')
            if database_url and (database_url.startswith('postgresql://') or database_url.startswith('postgres://')):
                from database.postgres import PostgresDatabase
                self.db = PostgresDatabase(database_url)
                await self.db.connect()
                logger.info('✅ Connected to PostgreSQL database')
            else:
                from database.db import init_database
                self.db = await init_database()
                logger.info('✅ Connected to SQLite database')
        except Exception as e:
            logger.error(f'❌ Database initialization failed: {e}')
            import traceback
            traceback.print_exc()
            self.db = None
            logger.warning('⚠️ Running without persistent storage - settings will NOT be saved!')

        # Load cogs
        cogs = [
            'cogs.antinuke',
            'cogs.antiraid',
            'cogs.antispam',
            'cogs.antiselfbot',
            'cogs.whitelist',
            'cogs.lockdown',
            'cogs.backup',
            'cogs.logging',
            'cogs.moderation',
            'cogs.settings',
            'cogs.help',
            'cogs.utility',
            'cogs.threat_intel',
            'cogs.slash_commands',
            'cogs.role_commands',       # Role management commands
            'cogs.advanced_detection',  # Advanced AI detection
            'cogs.advanced_security',   # Role hierarchy, API abuse, selfbot detection, honeypots
            'cogs.ban_sync',            # Cross-server ban synchronization
            'cogs.vpn_detection',       # VPN/Proxy detection for raid prevention
            'cogs.themes',              # Custom theme system
            'cogs.bot_admin',           # Bot admin commands (status, servers, join/leave logging)
            'cogs.mirror',              # Cross-server message mirroring
        ]

        for cog in cogs:
            try:
                await self.load_extension(cog)
                logger.info(f'✅ Loaded: {cog}')
            except Exception as e:
                logger.error(f'❌ Failed to load {cog}: {e}')
                import traceback
                traceback.print_exc()

        # Log commands in tree after loading cogs
        tree_cmds = self.tree.get_commands()
        logger.info(f'Commands in tree after loading cogs: {len(tree_cmds)}')
        for cmd in tree_cmds[:10]:
            logger.info(f'  - {cmd.name}')

        # Inject database into cogs that need it
        await self._inject_database()

    async def on_ready(self):
        """Called when the bot is ready"""
        logger.info(f'{"="*60}')
        logger.info(f'  Offcialx Anti-Nuke Bot v3.0.0')
        logger.info(f'  Now with Slash Commands & AI Threat Intelligence!')
        logger.info(f'{"="*60}')
        logger.info(f'Logged in as: {self.user.name}#{self.user.discriminator}')
        logger.info(f'Bot ID: {self.user.id}')
        logger.info(f'Servers: {len(self.guilds)}')
        logger.info(f'Users: {sum(g.member_count or 0 for g in self.guilds)}')
        if self.db:
            logger.info(f'Database: ✅ Connected (PostgreSQL)')
        else:
            logger.warning(f'Database: ❌ NOT CONNECTED - Settings will NOT persist!')
        logger.info(f'{"="*60}')

        # Set presence
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f'{len(self.guilds)} servers | /help'
            ),
            status=discord.Status.online
        )

        # Preload all settings from database
        if self.db:
            logger.info('📂 Loading saved settings from database...')
            await self._preload_all_settings()
            logger.info('✅ All whitelisted users/roles loaded - NO need to re-whitelist!')
        else:
            logger.warning('⚠️ No database - you will need to re-whitelist after restart!')

        # Sync slash commands only once
        if not self._commands_synced:
            try:
                # Log how many commands are in the tree
                tree_commands = self.tree.get_commands()
                logger.info(f'Commands in tree before sync: {len(tree_commands)}')
                for cmd in tree_commands[:15]:
                    logger.info(f'  - /{cmd.name}')

                # Sync commands globally (do NOT clear - hybrid commands are already registered)
                synced = await self.tree.sync()
                self._commands_synced = True
                logger.info(f'✅ Synced {len(synced)} slash commands globally')
            except Exception as e:
                logger.error(f'Failed to sync commands: {e}')
                import traceback
                traceback.print_exc()

        # Start scheduler
        if hasattr(self, 'start_scheduler'):
            self.start_scheduler()
            logger.info('Scheduler started')

        # Send online notification via webhook
        if hasattr(self, 'webhook_notifier') and self.webhook_notifier:
            await self.webhook_notifier.send_bot_status(
                'online',
                f"Now protecting {len(self.guilds)} servers with {sum(g.member_count or 0 for g in self.guilds)} users"
            )

    async def _inject_database(self):
        """Inject database and audit cache into cogs that need it"""
        if not self.db:
            logger.warning('⚠️ No database to inject into cogs')

        cogs_needing_db = [
            'AntiNuke', 'AntiRaid', 'AntiSpam', 'AntiSelfbot',
            'Whitelist', 'Lockdown', 'Backup', 'SecurityLogging',
            'Moderation', 'ThreatIntelligence', 'BotAdmin'
        ]

        # Cogs that need audit cache
        cogs_needing_audit = [
            'AntiNuke', 'AntiRaid', 'AdvancedSecurity'
        ]

        injected_db = 0
        injected_audit = 0

        for cog_name in cogs_needing_db:
            cog = self.get_cog(cog_name)
            if cog and self.db:
                cog.db = self.db
                injected_db += 1

        for cog_name in cogs_needing_audit:
            cog = self.get_cog(cog_name)
            if cog and self.audit_cache:
                cog.audit_cache = self.audit_cache
                injected_audit += 1

        logger.info(f'💉 Injected database into {injected_db} cogs, audit cache into {injected_audit} cogs')

    async def _preload_all_settings(self):
        """Preload settings from database for all cogs on startup"""
        if not self.db:
            logger.warning('⚠️ No database connection - using default settings (settings will NOT persist!)')
            return

        logger.info(f'📂 Preloading settings from database for {len(self.guilds)} guilds...')

        # Preload settings for cogs that have the preload method
        cogs_with_preload = ['AntiNuke', 'AntiRaid', 'AntiSpam', 'Whitelist']

        for cog_name in cogs_with_preload:
            cog = self.get_cog(cog_name)
            if cog and hasattr(cog, 'preload_all_settings'):
                try:
                    await cog.preload_all_settings()
                    logger.info(f'  ✅ Preloaded {cog_name} settings')
                except Exception as e:
                    logger.error(f'  ❌ Failed to preload settings for {cog_name}: {e}')
                    import traceback
                    traceback.print_exc()
            elif cog:
                logger.warning(f'  ⚠️ {cog_name} has no preload_all_settings method')
            else:
                logger.warning(f'  ⚠️ {cog_name} cog not found')

        # Log summary of what was loaded
        antinuke = self.get_cog('AntiNuke')
        whitelist = self.get_cog('Whitelist')

        if antinuke:
            total_trusted = sum(len(users) for users in antinuke.whitelisted.values())
            total_bots = sum(len(bots) for bots in antinuke.trusted_bots.values())
            logger.info(f'  📊 AntiNuke: {total_trusted} trusted users, {total_bots} trusted bots loaded')

        if whitelist:
            total_wl_users = sum(len(users) for users in whitelist.whitelists.values())
            total_wl_roles = sum(len(roles) for roles in whitelist.whitelisted_roles.values())
            logger.info(f'  📊 Whitelist: {total_wl_users} users, {total_wl_roles} roles loaded')

        logger.info('✅ All settings preloaded from database - trusted users/roles are now active!')

    async def on_message(self, message: discord.Message):
        """Process messages and commands"""
        # Ignore messages from bots
        if message.author.bot:
            return

        # Always process commands - this is critical for prefix commands to work
        await self.process_commands(message)

    async def on_guild_join(self, guild: discord.Guild):
        """Called when the bot joins a new guild"""
        logger.info(f'Joined new guild: {guild.name} (ID: {guild.id})')

        # Send welcome message
        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).send_messages:
                embed = discord.Embed(color=EMBED_COLOR)
                embed.description = (
                    "**Offcialx Security Bot**\n\n"
                    "Thanks for adding me to your server.\n\n"
                    "**Quick Setup**\n"
                    "› `/setup` or `!setup` - Configure protection\n"
                    "› `/trust @user` - Add trusted admins\n"
                    "› `/setlog #channel` - Set log channel\n\n"
                    "Make sure my role is at the top of the hierarchy."
                )
                await channel.send(embed=embed)
                break

    async def on_command_error(self, ctx, error):
        """Global error handler - minimal embed style"""
        if isinstance(error, commands.CommandNotFound):
            return

        embed = discord.Embed(color=EMBED_COLOR)

        if isinstance(error, commands.MissingPermissions):
            embed.description = "✕ You don't have permission"
        elif isinstance(error, commands.BotMissingPermissions):
            perms = ', '.join(error.missing_permissions)
            embed.description = f"✕ Missing permissions: `{perms}`"
        elif isinstance(error, commands.NotOwner):
            embed.description = "✕ Owner only command"
        elif isinstance(error, commands.MissingRequiredArgument):
            embed.description = f"✕ Missing argument: `{error.param.name}`"
        elif isinstance(error, commands.CommandOnCooldown):
            embed.description = f"✕ Cooldown: `{error.retry_after:.1f}s`"
        elif isinstance(error, commands.BadArgument):
            embed.description = f"✕ Invalid argument"
        elif isinstance(error, commands.MemberNotFound):
            embed.description = "✕ Member not found"
        elif isinstance(error, commands.RoleNotFound):
            embed.description = "✕ Role not found"
        elif isinstance(error, commands.ChannelNotFound):
            embed.description = "✕ Channel not found"
        else:
            logger.error(f'Command error in {ctx.command}: {error}')
            embed.description = "✕ An error occurred"

        try:
            await ctx.send(embed=embed)
        except:
            pass

    async def close(self):
        """Clean up on shutdown"""
        if self.db:
            await self.db.close()
        await super().close()

async def main():
    """Main entry point"""
    bot = OffcialxBot()

    if not BotConfig.TOKEN:
        logger.error('No bot token provided! Set DISCORD_BOT_TOKEN environment variable.')
        return

    # Initialize webhook notifier
    try:
        from utils.webhooks import init_webhooks, close_webhooks, webhook_notifier
        webhook_config = {
            'security': os.getenv('SECURITY_WEBHOOK_URL', '').split(',') if os.getenv('SECURITY_WEBHOOK_URL') else [],
            'system': os.getenv('SYSTEM_WEBHOOK_URL', '').split(',') if os.getenv('SYSTEM_WEBHOOK_URL') else [],
        }
        await init_webhooks(webhook_config)
        bot.webhook_notifier = webhook_notifier
        logger.info('Webhook notifier initialized')
    except Exception as e:
        logger.warning(f'Webhook notifier initialization failed: {e}')
        bot.webhook_notifier = None

    # Initialize scheduler
    try:
        from utils.scheduler import start_scheduler, stop_scheduler
        bot.start_scheduler = lambda: asyncio.create_task(start_scheduler(bot))
        bot.stop_scheduler = stop_scheduler
    except Exception as e:
        logger.warning(f'Scheduler initialization failed: {e}')

    try:
        await bot.start(BotConfig.TOKEN)
    except discord.LoginFailure:
        logger.error('Invalid bot token!')
    except Exception as e:
        logger.error(f'Failed to start bot: {e}')
    finally:
        # Cleanup
        try:
            from utils.webhooks import close_webhooks
            await close_webhooks()
        except:
            pass
        try:
            from utils.scheduler import stop_scheduler
            stop_scheduler()
        except:
            pass
        await bot.close()

if __name__ == '__main__':
    asyncio.run(main())
