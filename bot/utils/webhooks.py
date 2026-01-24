"""
Discord Webhook Notifications Utility
=====================================
Sends security alerts and notifications via Discord webhooks.
Supports multiple webhook channels for different alert types.
"""

import aiohttp
import asyncio
from datetime import datetime
from typing import Optional, Dict, List, Any
import logging

logger = logging.getLogger('Offcialx.Webhooks')


class WebhookNotifier:
    """Handles sending notifications via Discord webhooks"""

    def __init__(self):
        self.webhooks: Dict[str, List[str]] = {
            'security': [],       # Security alerts (nuke, raid, etc.)
            'moderation': [],     # Moderation actions
            'system': [],         # System status updates
            'audit': [],          # Audit log notifications
        }
        self.session: Optional[aiohttp.ClientSession] = None
        self.rate_limit_queue: Dict[str, List[float]] = {}
        self.max_requests_per_second = 5

    async def init_session(self):
        """Initialize the aiohttp session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()

    def add_webhook(self, category: str, webhook_url: str) -> bool:
        """Add a webhook URL to a category"""
        if category not in self.webhooks:
            return False
        if webhook_url not in self.webhooks[category]:
            self.webhooks[category].append(webhook_url)
            logger.info(f"Added webhook to {category} category")
        return True

    def remove_webhook(self, category: str, webhook_url: str) -> bool:
        """Remove a webhook URL from a category"""
        if category not in self.webhooks:
            return False
        if webhook_url in self.webhooks[category]:
            self.webhooks[category].remove(webhook_url)
            logger.info(f"Removed webhook from {category} category")
            return True
        return False

    def set_webhooks(self, category: str, webhooks: List[str]):
        """Set all webhooks for a category"""
        if category in self.webhooks:
            self.webhooks[category] = webhooks

    async def _send_webhook(self, webhook_url: str, payload: Dict) -> bool:
        """Send a webhook message with rate limiting"""
        await self.init_session()

        try:
            async with self.session.post(
                webhook_url,
                json=payload,
                headers={'Content-Type': 'application/json'}
            ) as response:
                if response.status == 204:
                    return True
                elif response.status == 429:
                    # Rate limited, wait and retry
                    retry_after = (await response.json()).get('retry_after', 1)
                    logger.warning(f"Rate limited, retrying after {retry_after}s")
                    await asyncio.sleep(retry_after)
                    return await self._send_webhook(webhook_url, payload)
                else:
                    logger.error(f"Webhook failed with status {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Error sending webhook: {e}")
            return False

    async def send_to_category(self, category: str, payload: Dict) -> int:
        """Send a message to all webhooks in a category"""
        if category not in self.webhooks:
            return 0

        sent = 0
        for webhook_url in self.webhooks[category]:
            if await self._send_webhook(webhook_url, payload):
                sent += 1
        return sent

    def create_security_embed(
        self,
        title: str,
        description: str,
        threat_type: str,
        severity: str = "high",
        guild_name: str = None,
        guild_id: int = None,
        attacker: Dict = None,
        action_taken: str = None,
        details: Dict = None
    ) -> Dict:
        """Create a security alert embed"""

        # Color based on severity
        colors = {
            'critical': 0xFF0000,  # Red
            'high': 0xFF6600,      # Orange
            'medium': 0xFFCC00,    # Yellow
            'low': 0x00FF00,       # Green
            'info': 0x00CCFF       # Blue
        }
        color = colors.get(severity, colors['high'])

        # Severity emoji
        severity_emojis = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🟢',
            'info': '🔵'
        }
        severity_emoji = severity_emojis.get(severity, '🟠')

        embed = {
            'title': f"{severity_emoji} {title}",
            'description': description,
            'color': color,
            'timestamp': datetime.utcnow().isoformat(),
            'footer': {
                'text': 'Offcialx Anti-Nuke Protection'
            },
            'fields': []
        }

        # Add threat type
        embed['fields'].append({
            'name': '🎯 Threat Type',
            'value': threat_type,
            'inline': True
        })

        # Add severity
        embed['fields'].append({
            'name': '⚠️ Severity',
            'value': severity.upper(),
            'inline': True
        })

        # Add guild info
        if guild_name:
            embed['fields'].append({
                'name': '🏠 Server',
                'value': f"{guild_name}\n`{guild_id}`" if guild_id else guild_name,
                'inline': True
            })

        # Add attacker info
        if attacker:
            embed['fields'].append({
                'name': '👤 Attacker',
                'value': f"**{attacker.get('name', 'Unknown')}**\n`{attacker.get('id', 'N/A')}`",
                'inline': True
            })

        # Add action taken
        if action_taken:
            embed['fields'].append({
                'name': '⚡ Action Taken',
                'value': action_taken,
                'inline': True
            })

        # Add extra details
        if details:
            for key, value in details.items():
                embed['fields'].append({
                    'name': key,
                    'value': str(value),
                    'inline': True
                })

        return {'embeds': [embed]}

    def create_moderation_embed(
        self,
        title: str,
        action: str,
        moderator: Dict,
        target: Dict,
        reason: str = None,
        guild_name: str = None,
        guild_id: int = None
    ) -> Dict:
        """Create a moderation action embed"""

        embed = {
            'title': f"🔨 {title}",
            'color': 0x9B59B6,  # Purple
            'timestamp': datetime.utcnow().isoformat(),
            'footer': {
                'text': 'Offcialx Moderation Log'
            },
            'fields': [
                {
                    'name': '📋 Action',
                    'value': action,
                    'inline': True
                },
                {
                    'name': '👮 Moderator',
                    'value': f"**{moderator.get('name', 'Unknown')}**\n`{moderator.get('id', 'N/A')}`",
                    'inline': True
                },
                {
                    'name': '🎯 Target',
                    'value': f"**{target.get('name', 'Unknown')}**\n`{target.get('id', 'N/A')}`",
                    'inline': True
                }
            ]
        }

        if reason:
            embed['fields'].append({
                'name': '📝 Reason',
                'value': reason,
                'inline': False
            })

        if guild_name:
            embed['fields'].append({
                'name': '🏠 Server',
                'value': f"{guild_name}\n`{guild_id}`" if guild_id else guild_name,
                'inline': True
            })

        return {'embeds': [embed]}

    def create_system_embed(
        self,
        title: str,
        description: str,
        status: str = 'info'
    ) -> Dict:
        """Create a system status embed"""

        colors = {
            'online': 0x00FF00,
            'offline': 0xFF0000,
            'warning': 0xFFCC00,
            'info': 0x00CCFF,
            'error': 0xFF0000
        }
        color = colors.get(status, colors['info'])

        status_emojis = {
            'online': '🟢',
            'offline': '🔴',
            'warning': '⚠️',
            'info': 'ℹ️',
            'error': '❌'
        }
        emoji = status_emojis.get(status, 'ℹ️')

        embed = {
            'title': f"{emoji} {title}",
            'description': description,
            'color': color,
            'timestamp': datetime.utcnow().isoformat(),
            'footer': {
                'text': 'Offcialx System'
            }
        }

        return {'embeds': [embed]}

    # Convenience methods for common alerts

    async def send_nuke_alert(
        self,
        guild_name: str,
        guild_id: int,
        attacker_name: str,
        attacker_id: int,
        threat_type: str,
        action_taken: str,
        details: str = None
    ):
        """Send a nuke attempt alert"""
        payload = self.create_security_embed(
            title="NUKE ATTEMPT DETECTED",
            description=f"A nuke attempt was detected and neutralized in **{guild_name}**",
            threat_type=threat_type,
            severity='critical',
            guild_name=guild_name,
            guild_id=guild_id,
            attacker={'name': attacker_name, 'id': attacker_id},
            action_taken=action_taken,
            details={'📄 Details': details} if details else None
        )
        return await self.send_to_category('security', payload)

    async def send_raid_alert(
        self,
        guild_name: str,
        guild_id: int,
        raid_size: int,
        action_taken: str
    ):
        """Send a raid detection alert"""
        payload = self.create_security_embed(
            title="RAID DETECTED",
            description=f"A coordinated raid was detected in **{guild_name}**",
            threat_type="Mass Join / Raid",
            severity='high',
            guild_name=guild_name,
            guild_id=guild_id,
            action_taken=action_taken,
            details={
                '👥 Raid Size': f"{raid_size} accounts"
            }
        )
        return await self.send_to_category('security', payload)

    async def send_permission_alert(
        self,
        guild_name: str,
        guild_id: int,
        user_name: str,
        user_id: int,
        permissions_changed: List[str]
    ):
        """Send a permission escalation alert"""
        payload = self.create_security_embed(
            title="PERMISSION ESCALATION",
            description=f"Dangerous permissions were modified in **{guild_name}**",
            threat_type="Permission Change",
            severity='high',
            guild_name=guild_name,
            guild_id=guild_id,
            attacker={'name': user_name, 'id': user_id},
            details={
                '🔐 Permissions': ', '.join(permissions_changed)
            }
        )
        return await self.send_to_category('security', payload)

    async def send_recovery_notification(
        self,
        guild_name: str,
        guild_id: int,
        recovered_by: str,
        stats: Dict
    ):
        """Send a recovery completion notification"""
        stats_text = '\n'.join([
            f"• Users Unbanned: **{stats.get('unbanned', 0)}**",
            f"• Channels Restored: **{stats.get('channels_restored', 0)}**",
            f"• Roles Restored: **{stats.get('roles_restored', 0)}**",
            f"• Webhooks Deleted: **{stats.get('webhooks_deleted', 0)}**",
            f"• Permissions Reverted: **{stats.get('permissions_reverted', 0)}**"
        ])

        payload = self.create_security_embed(
            title="RECOVERY COMPLETE",
            description=f"Server recovery completed in **{guild_name}**\n\n{stats_text}",
            threat_type="Recovery Operation",
            severity='info',
            guild_name=guild_name,
            guild_id=guild_id,
            action_taken=f"Recovered by {recovered_by}"
        )
        return await self.send_to_category('security', payload)

    async def send_bot_status(self, status: str, details: str = None):
        """Send bot status update"""
        if status == 'online':
            title = "Bot Online"
            description = "Offcialx Anti-Nuke Protection is now online and protecting servers."
        elif status == 'offline':
            title = "Bot Offline"
            description = "Offcialx Anti-Nuke Protection has gone offline."
        elif status == 'restart':
            title = "Bot Restarting"
            description = "Offcialx Anti-Nuke Protection is restarting..."
        else:
            title = f"Status: {status.title()}"
            description = details or "Status update"

        if details:
            description += f"\n\n{details}"

        payload = self.create_system_embed(title, description, status)
        return await self.send_to_category('system', payload)


# Singleton instance
webhook_notifier = WebhookNotifier()


async def init_webhooks(config: Dict = None):
    """Initialize webhooks from config"""
    if config:
        for category, urls in config.items():
            if isinstance(urls, list):
                webhook_notifier.set_webhooks(category, urls)
            elif isinstance(urls, str):
                webhook_notifier.add_webhook(category, urls)
    await webhook_notifier.init_session()
    logger.info("Webhook notifier initialized")


async def close_webhooks():
    """Close webhook session"""
    await webhook_notifier.close()
    logger.info("Webhook notifier closed")
