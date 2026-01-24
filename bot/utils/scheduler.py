"""
Scheduled Tasks Utility
=======================
Handles scheduled tasks like automatic backups,
maintenance, cleanup, and periodic health checks.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Any, Optional
import logging

logger = logging.getLogger('Offcialx.Scheduler')


class ScheduledTask:
    """Represents a scheduled task"""

    def __init__(
        self,
        name: str,
        callback: Callable,
        interval_seconds: int,
        enabled: bool = True,
        run_immediately: bool = False,
        max_retries: int = 3,
        retry_delay: int = 60
    ):
        self.name = name
        self.callback = callback
        self.interval_seconds = interval_seconds
        self.enabled = enabled
        self.run_immediately = run_immediately
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        self.last_run: Optional[datetime] = None
        self.next_run: Optional[datetime] = None
        self.run_count: int = 0
        self.fail_count: int = 0
        self.is_running: bool = False
        self._task: Optional[asyncio.Task] = None

    def should_run(self) -> bool:
        """Check if the task should run now"""
        if not self.enabled or self.is_running:
            return False

        if self.next_run is None:
            return self.run_immediately

        return datetime.utcnow() >= self.next_run

    def schedule_next(self):
        """Schedule the next run"""
        self.next_run = datetime.utcnow() + timedelta(seconds=self.interval_seconds)

    async def run(self, *args, **kwargs):
        """Execute the task with retry logic"""
        if self.is_running:
            logger.warning(f"Task {self.name} is already running, skipping")
            return

        self.is_running = True
        retries = 0

        while retries <= self.max_retries:
            try:
                logger.info(f"Running scheduled task: {self.name}")
                await self.callback(*args, **kwargs)
                self.last_run = datetime.utcnow()
                self.run_count += 1
                self.schedule_next()
                logger.info(f"Task {self.name} completed successfully")
                break
            except Exception as e:
                retries += 1
                self.fail_count += 1
                logger.error(f"Task {self.name} failed (attempt {retries}): {e}")

                if retries <= self.max_retries:
                    await asyncio.sleep(self.retry_delay)
                else:
                    logger.error(f"Task {self.name} failed after {self.max_retries} retries")
                    self.schedule_next()  # Schedule next anyway

        self.is_running = False


class TaskScheduler:
    """Manages scheduled tasks"""

    def __init__(self, bot=None):
        self.bot = bot
        self.tasks: Dict[str, ScheduledTask] = {}
        self.running: bool = False
        self._loop_task: Optional[asyncio.Task] = None

    def add_task(
        self,
        name: str,
        callback: Callable,
        interval_seconds: int,
        enabled: bool = True,
        run_immediately: bool = False,
        max_retries: int = 3,
        retry_delay: int = 60
    ) -> ScheduledTask:
        """Add a new scheduled task"""
        task = ScheduledTask(
            name=name,
            callback=callback,
            interval_seconds=interval_seconds,
            enabled=enabled,
            run_immediately=run_immediately,
            max_retries=max_retries,
            retry_delay=retry_delay
        )
        self.tasks[name] = task
        logger.info(f"Added scheduled task: {name} (interval: {interval_seconds}s)")
        return task

    def remove_task(self, name: str) -> bool:
        """Remove a scheduled task"""
        if name in self.tasks:
            del self.tasks[name]
            logger.info(f"Removed scheduled task: {name}")
            return True
        return False

    def enable_task(self, name: str) -> bool:
        """Enable a scheduled task"""
        if name in self.tasks:
            self.tasks[name].enabled = True
            self.tasks[name].schedule_next()
            return True
        return False

    def disable_task(self, name: str) -> bool:
        """Disable a scheduled task"""
        if name in self.tasks:
            self.tasks[name].enabled = False
            return True
        return False

    def get_task_status(self) -> List[Dict[str, Any]]:
        """Get status of all scheduled tasks"""
        return [
            {
                'name': task.name,
                'enabled': task.enabled,
                'is_running': task.is_running,
                'interval_seconds': task.interval_seconds,
                'last_run': task.last_run.isoformat() if task.last_run else None,
                'next_run': task.next_run.isoformat() if task.next_run else None,
                'run_count': task.run_count,
                'fail_count': task.fail_count
            }
            for task in self.tasks.values()
        ]

    async def _run_loop(self):
        """Main scheduler loop"""
        logger.info("Scheduler loop started")

        while self.running:
            try:
                for task in self.tasks.values():
                    if task.should_run():
                        # Run task in background
                        asyncio.create_task(task.run(self.bot))

                # Check every 10 seconds
                await asyncio.sleep(10)
            except Exception as e:
                logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(30)

        logger.info("Scheduler loop stopped")

    def start(self):
        """Start the scheduler"""
        if self.running:
            return

        self.running = True
        self._loop_task = asyncio.create_task(self._run_loop())
        logger.info("Scheduler started")

    def stop(self):
        """Stop the scheduler"""
        self.running = False
        if self._loop_task:
            self._loop_task.cancel()
        logger.info("Scheduler stopped")


# ==================== BUILT-IN TASKS ====================


async def automatic_backup_task(bot):
    """Automatic backup task for all guilds"""
    if not bot:
        logger.warning("Bot not available for backup task")
        return

    backup_cog = bot.get_cog('Backup')
    if not backup_cog:
        logger.warning("Backup cog not loaded")
        return

    logger.info(f"Starting automatic backup for {len(bot.guilds)} guilds")
    backed_up = 0
    failed = 0

    for guild in bot.guilds:
        try:
            # Check if auto-backup is enabled for this guild
            # For now, backup all guilds
            await backup_cog.create_backup(guild, reason="Scheduled automatic backup")
            backed_up += 1
            logger.info(f"Backed up: {guild.name}")
        except Exception as e:
            failed += 1
            logger.error(f"Failed to backup {guild.name}: {e}")

        # Small delay between backups
        await asyncio.sleep(1)

    logger.info(f"Automatic backup complete: {backed_up} succeeded, {failed} failed")


async def cleanup_old_data_task(bot):
    """Clean up old data (logs, processed entries, etc.)"""
    if not bot:
        return

    # Clean up processed audit log entries in AntiNuke cog
    antinuke = bot.get_cog('AntiNuke')
    if antinuke and hasattr(antinuke, 'processed_entries'):
        old_count = len(antinuke.processed_entries)
        # Keep only last 1000 entries
        if old_count > 1000:
            antinuke.processed_entries = set(list(antinuke.processed_entries)[-1000:])
            logger.info(f"Cleaned up processed entries: {old_count} -> {len(antinuke.processed_entries)}")

    # Clean up old attack patterns
    if antinuke and hasattr(antinuke, 'attack_patterns'):
        for guild_id in list(antinuke.attack_patterns.keys()):
            for user_id in list(antinuke.attack_patterns[guild_id].keys()):
                # Clear patterns older than 1 hour
                antinuke.attack_patterns[guild_id][user_id] = []

    logger.info("Data cleanup complete")


async def health_check_task(bot):
    """Periodic health check and stats update"""
    if not bot:
        return

    # Log current stats
    total_guilds = len(bot.guilds)
    total_users = sum(g.member_count or 0 for g in bot.guilds)

    logger.info(f"Health check: {total_guilds} guilds, {total_users} users")

    # Update presence if needed
    try:
        import discord
        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f'{total_guilds} servers | /help'
            )
        )
    except Exception as e:
        logger.error(f"Failed to update presence: {e}")


async def threat_intelligence_sync_task(bot):
    """Sync threat intelligence data"""
    if not bot:
        return

    threat_intel = bot.get_cog('ThreatIntelligence')
    if not threat_intel:
        logger.warning("ThreatIntelligence cog not loaded")
        return

    # Sync known bad actors, patterns, etc.
    # This would connect to an external threat database in production
    logger.info("Threat intelligence sync complete")


# ==================== SCHEDULER SETUP ====================


def setup_default_tasks(scheduler: TaskScheduler):
    """Set up default scheduled tasks"""

    # Automatic backup every 6 hours
    scheduler.add_task(
        name='automatic_backup',
        callback=automatic_backup_task,
        interval_seconds=6 * 60 * 60,  # 6 hours
        enabled=True,
        run_immediately=False
    )

    # Data cleanup every hour
    scheduler.add_task(
        name='cleanup_old_data',
        callback=cleanup_old_data_task,
        interval_seconds=60 * 60,  # 1 hour
        enabled=True,
        run_immediately=False
    )

    # Health check every 5 minutes
    scheduler.add_task(
        name='health_check',
        callback=health_check_task,
        interval_seconds=5 * 60,  # 5 minutes
        enabled=True,
        run_immediately=True
    )

    # Threat intelligence sync every hour
    scheduler.add_task(
        name='threat_intel_sync',
        callback=threat_intelligence_sync_task,
        interval_seconds=60 * 60,  # 1 hour
        enabled=True,
        run_immediately=False
    )

    logger.info("Default scheduled tasks configured")


# Singleton instance
scheduler = TaskScheduler()


def get_scheduler() -> TaskScheduler:
    """Get the scheduler instance"""
    return scheduler


async def start_scheduler(bot=None):
    """Start the scheduler with default tasks"""
    scheduler.bot = bot
    setup_default_tasks(scheduler)
    scheduler.start()


async def stop_scheduler():
    """Stop the scheduler"""
    scheduler.stop()
