"""
Run Bot with API Server
=======================
Starts both the Discord bot and the FastAPI dashboard server.
Optimized for Railway deployment with 24/7 uptime.
"""

import asyncio
import os
import sys
import signal
import logging
from threading import Thread
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('Offcialx.Launcher')

# Import after loading env
from main import OffcialxBot, BotConfig

def run_api_server(bot, db):
    """Run the FastAPI server in a separate thread"""
    try:
        from api.dashboard import create_api_app

        app = create_api_app(bot, db)

        host = os.getenv('API_HOST', '0.0.0.0')
        # Railway uses PORT environment variable
        port = int(os.getenv('PORT', os.getenv('API_PORT', '8080')))

        logger.info(f'Starting API server on {host}:{port}')

        config = uvicorn.Config(
            app,
            host=host,
            port=port,
            log_level="info",
            access_log=True,
            timeout_keep_alive=120
        )
        server = uvicorn.Server(config)

        # Run in the current thread's event loop
        asyncio.run(server.serve())
    except Exception as e:
        logger.error(f'API server error: {e}')


async def main():
    """Main entry point"""
    logger.info('=' * 60)
    logger.info('  OFFCIALX ANTI-NUKE SECURITY BOT v3.5.1')
    logger.info('  Military-Grade Discord Server Protection')
    logger.info('=' * 60)

    bot = OffcialxBot()

    if not BotConfig.TOKEN:
        logger.error('No bot token provided!')
        logger.error('Set DISCORD_BOT_TOKEN environment variable.')
        logger.error('In Railway: Add it in the Variables tab')
        sys.exit(1)

    # Check if API should be enabled
    enable_api = os.getenv('ENABLE_API', 'true').lower() == 'true'

    # Track if we've started the API
    api_started = False

    if enable_api:
        # Store reference to original on_ready from the bot
        original_on_ready = bot.on_ready

        @bot.event
        async def on_ready():
            nonlocal api_started

            # IMPORTANT: Call the original on_ready FIRST to preload database settings
            try:
                await original_on_ready()
            except Exception as e:
                logger.error(f'Error in original on_ready: {e}')
                import traceback
                traceback.print_exc()

            # Start API in background (only once)
            if not api_started:
                api_started = True
                api_thread = Thread(
                    target=run_api_server,
                    args=(bot, getattr(bot, 'db', None)),
                    daemon=True,
                    name='API-Server'
                )
                api_thread.start()
                logger.info('API server thread started')

    # Handle graceful shutdown
    def signal_handler(sig, frame):
        logger.info('Shutdown signal received, closing bot...')
        asyncio.create_task(bot.close())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        logger.info('Connecting to Discord...')
        await bot.start(BotConfig.TOKEN)
    except discord.LoginFailure:
        logger.error('Invalid bot token! Please check DISCORD_BOT_TOKEN')
        sys.exit(1)
    except Exception as e:
        logger.error(f'Failed to start bot: {e}')
        sys.exit(1)
    finally:
        if not bot.is_closed():
            await bot.close()
        logger.info('Bot has been shut down.')


if __name__ == '__main__':
    # Import discord for error handling
    import discord

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('Interrupted by user')
    except Exception as e:
        logger.error(f'Fatal error: {e}')
        sys.exit(1)
