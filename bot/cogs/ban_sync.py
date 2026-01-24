"""
Cross-Server Ban Sync
=====================
Synchronizes bans across multiple servers owned by the same user.
Features:
- Global ban list shared between linked servers
- Automatic ban propagation
- Ban import/export
- Unban sync option
- Ban reasons and evidence tracking
"""

import discord
from discord.ext import commands
from datetime import datetime
from typing import Dict, List, Optional, Set, Any
from collections import defaultdict
import asyncio
import logging
import json

logger = logging.getLogger('Offcialx.BanSync')

# Minimal embed color
EMBED_COLOR = 0x2b2d31


class BanRecord:
    """Represents a synchronized ban"""

    def __init__(
        self,
        user_id: int,
        user_name: str,
        reason: str,
        banned_by: int,
        banned_by_name: str,
        source_guild_id: int,
        source_guild_name: str,
        timestamp: datetime,
        evidence: List[str] = None,
        tags: List[str] = None
    ):
        self.user_id = user_id
        self.user_name = user_name
        self.reason = reason
        self.banned_by = banned_by
        self.banned_by_name = banned_by_name
        self.source_guild_id = source_guild_id
        self.source_guild_name = source_guild_name
        self.timestamp = timestamp
        self.evidence = evidence or []
        self.tags = tags or []  # e.g., ['nuke', 'raid', 'spam', 'scam']

    def to_dict(self) -> Dict:
        return {
            'user_id': self.user_id,
            'user_name': self.user_name,
            'reason': self.reason,
            'banned_by': self.banned_by,
            'banned_by_name': self.banned_by_name,
            'source_guild_id': self.source_guild_id,
            'source_guild_name': self.source_guild_name,
            'timestamp': self.timestamp.isoformat(),
            'evidence': self.evidence,
            'tags': self.tags
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'BanRecord':
        return cls(
            user_id=data['user_id'],
            user_name=data['user_name'],
            reason=data['reason'],
            banned_by=data['banned_by'],
            banned_by_name=data['banned_by_name'],
            source_guild_id=data['source_guild_id'],
            source_guild_name=data['source_guild_name'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            evidence=data.get('evidence', []),
            tags=data.get('tags', [])
        )


class BanSyncNetwork:
    """A network of linked servers that share bans"""

    def __init__(self, network_id: str, owner_id: int):
        self.network_id = network_id
        self.owner_id = owner_id
        self.guild_ids: Set[int] = set()
        self.global_bans: Dict[int, BanRecord] = {}  # user_id -> BanRecord
        self.settings = {
            'auto_ban': True,           # Automatically ban users from global list
            'sync_unbans': False,       # Sync unbans across network
            'notify_on_ban': True,      # Notify when a ban is synced
            'require_reason': True,     # Require ban reason for sync
            'min_servers': 1,           # Min servers that must ban before global
        }
        self.created_at = datetime.utcnow()

    def add_guild(self, guild_id: int):
        self.guild_ids.add(guild_id)

    def remove_guild(self, guild_id: int):
        self.guild_ids.discard(guild_id)

    def add_ban(self, record: BanRecord):
        self.global_bans[record.user_id] = record

    def remove_ban(self, user_id: int):
        self.global_bans.pop(user_id, None)

    def is_banned(self, user_id: int) -> bool:
        return user_id in self.global_bans

    def get_ban(self, user_id: int) -> Optional[BanRecord]:
        return self.global_bans.get(user_id)


class BanSync(commands.Cog):
    """Cross-Server Ban Synchronization System"""

    def __init__(self, bot):
        self.bot = bot
        self.db = None

        # Networks: owner_id -> BanSyncNetwork
        self.networks: Dict[int, BanSyncNetwork] = {}

        # Guild to network mapping: guild_id -> owner_id (network key)
        self.guild_network: Dict[int, int] = {}

        # Pending bans to sync (to avoid duplicates)
        self.pending_syncs: Set[tuple] = set()  # (user_id, guild_id)

    def get_network(self, owner_id: int) -> Optional[BanSyncNetwork]:
        """Get or create a network for an owner"""
        return self.networks.get(owner_id)

    def get_guild_network(self, guild_id: int) -> Optional[BanSyncNetwork]:
        """Get the network a guild belongs to"""
        owner_id = self.guild_network.get(guild_id)
        if owner_id:
            return self.networks.get(owner_id)
        return None

    def create_network(self, owner_id: int) -> BanSyncNetwork:
        """Create a new ban sync network"""
        network_id = f"net_{owner_id}_{int(datetime.utcnow().timestamp())}"
        network = BanSyncNetwork(network_id, owner_id)
        self.networks[owner_id] = network
        return network

    async def sync_ban_to_network(self, record: BanRecord, source_guild: discord.Guild):
        """Sync a ban to all servers in the network"""
        network = self.get_guild_network(source_guild.id)
        if not network:
            return

        # Add to global list
        network.add_ban(record)

        # Sync to other guilds
        synced_count = 0
        failed_count = 0

        for guild_id in network.guild_ids:
            if guild_id == source_guild.id:
                continue

            # Skip if already pending
            if (record.user_id, guild_id) in self.pending_syncs:
                continue

            self.pending_syncs.add((record.user_id, guild_id))

            try:
                guild = self.bot.get_guild(guild_id)
                if not guild:
                    continue

                # Check if auto-ban is enabled
                if not network.settings.get('auto_ban', True):
                    continue

                # Check if user is already banned
                try:
                    await guild.fetch_ban(discord.Object(id=record.user_id))
                    continue  # Already banned
                except discord.NotFound:
                    pass

                # Ban the user
                await guild.ban(
                    discord.Object(id=record.user_id),
                    reason=f"[BanSync] {record.reason} (from {record.source_guild_name})",
                    delete_message_days=0
                )
                synced_count += 1

                # Notify if enabled
                if network.settings.get('notify_on_ban', True):
                    await self.notify_guild(guild, record)

            except discord.Forbidden:
                failed_count += 1
                logger.warning(f"Cannot sync ban to {guild_id}: Missing permissions")
            except Exception as e:
                failed_count += 1
                logger.error(f"Error syncing ban to {guild_id}: {e}")
            finally:
                self.pending_syncs.discard((record.user_id, guild_id))

        logger.info(f"Ban synced for {record.user_name}: {synced_count} synced, {failed_count} failed")
        return synced_count, failed_count

    async def notify_guild(self, guild: discord.Guild, record: BanRecord):
        """Notify a guild about a synced ban"""
        # Find a log channel
        antinuke = self.bot.get_cog('AntiNuke')
        if antinuke:
            settings = await antinuke.get_settings(guild.id)
            log_channel_id = settings.get('log_channel_id')
            if log_channel_id:
                channel = guild.get_channel(log_channel_id)
                if channel:
                    tags_str = f"\n› Tags: `{', '.join(record.tags)}`" if record.tags else ""
                    embed = discord.Embed(color=EMBED_COLOR)
                    embed.description = (
                        f"**Ban Synced**\n\n"
                        f"› User: {record.user_name} (`{record.user_id}`)\n"
                        f"› Reason: {record.reason[:200] if record.reason else 'No reason'}\n"
                        f"› Source: {record.source_guild_name}\n"
                        f"› Banned By: {record.banned_by_name}{tags_str}"
                    )
                    try:
                        await channel.send(embed=embed)
                    except:
                        pass

    # ==================== EVENT LISTENERS ====================

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        """Detect bans and sync to network"""
        network = self.get_guild_network(guild.id)
        if not network:
            return

        # Get ban details from audit log
        reason = "No reason provided"
        banned_by = None

        try:
            async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.ban):
                if entry.target.id == user.id:
                    reason = entry.reason or "No reason provided"
                    banned_by = entry.user
                    break
        except:
            pass

        # Don't sync bans made by the bot (to avoid loops)
        if banned_by and banned_by.id == self.bot.user.id:
            # Check if this is a synced ban
            if "[BanSync]" in (reason or ""):
                return

        # Create ban record
        record = BanRecord(
            user_id=user.id,
            user_name=str(user),
            reason=reason,
            banned_by=banned_by.id if banned_by else 0,
            banned_by_name=str(banned_by) if banned_by else "Unknown",
            source_guild_id=guild.id,
            source_guild_name=guild.name,
            timestamp=datetime.utcnow()
        )

        # Auto-tag based on reason
        reason_lower = reason.lower()
        if any(word in reason_lower for word in ['nuke', 'raid', 'attack']):
            record.tags.append('security')
        if any(word in reason_lower for word in ['spam', 'advertising']):
            record.tags.append('spam')
        if any(word in reason_lower for word in ['scam', 'phishing']):
            record.tags.append('scam')

        # Sync to network
        await self.sync_ban_to_network(record, guild)

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        """Handle unbans - optionally sync"""
        network = self.get_guild_network(guild.id)
        if not network or not network.settings.get('sync_unbans', False):
            return

        # Remove from global list
        network.remove_ban(user.id)

        # Sync unban to other guilds
        for guild_id in network.guild_ids:
            if guild_id == guild.id:
                continue

            try:
                target_guild = self.bot.get_guild(guild_id)
                if target_guild:
                    await target_guild.unban(user, reason=f"[BanSync] Unban synced from {guild.name}")
            except:
                pass

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Check if joining member is in global ban list"""
        network = self.get_guild_network(member.guild.id)
        if not network:
            return

        # Check if user is in global ban list
        ban_record = network.get_ban(member.id)
        if ban_record and network.settings.get('auto_ban', True):
            try:
                await member.guild.ban(
                    member,
                    reason=f"[BanSync] User is on global ban list: {ban_record.reason}",
                    delete_message_days=0
                )
                logger.info(f"Auto-banned {member} in {member.guild.name} (on global ban list)")
            except:
                pass

    # ==================== COMMANDS ====================

    @commands.hybrid_group(name='bansync', aliases=['bs'], invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def bansync(self, ctx):
        """Cross-server ban synchronization"""
        network = self.get_guild_network(ctx.guild.id)

        if network:
            settings_list = []
            if network.settings['auto_ban']:
                settings_list.append("› Auto-ban: `on`")
            else:
                settings_list.append("› Auto-ban: `off`")
            if network.settings['sync_unbans']:
                settings_list.append("› Sync unbans: `on`")
            else:
                settings_list.append("› Sync unbans: `off`")
            if network.settings['notify_on_ban']:
                settings_list.append("› Notify: `on`")
            else:
                settings_list.append("› Notify: `off`")

            embed = discord.Embed(color=EMBED_COLOR)
            embed.description = (
                f"**Ban Sync System**\n\n"
                f"**Network Status**\n"
                f"› Status: `connected`\n"
                f"› Servers: `{len(network.guild_ids)}`\n"
                f"› Global Bans: `{len(network.global_bans)}`\n\n"
                f"**Settings**\n" + "\n".join(settings_list) + "\n\n"
                f"**Commands**\n"
                f"› `!bansync create` − Create network\n"
                f"› `!bansync join @owner` − Join network\n"
                f"› `!bansync leave` − Leave network\n"
                f"› `!bansync list` − List servers\n"
                f"› `!bansync bans` − View ban list\n"
                f"› `!bansync add @user [reason]` − Add to list\n"
                f"› `!bansync remove @user` − Remove from list\n"
                f"› `!bansync import` − Import server bans\n"
                f"› `!bansync settings` − Configure"
            )
        else:
            embed = discord.Embed(color=EMBED_COLOR)
            embed.description = (
                f"**Ban Sync System**\n\n"
                f"› Status: `not connected`\n\n"
                f"Use `!bansync create` to create a network\n\n"
                f"**Commands**\n"
                f"› `!bansync create` − Create network\n"
                f"› `!bansync join @owner` − Join network"
            )
        await ctx.send(embed=embed)

    @bansync.command(name='create')
    @commands.has_permissions(administrator=True)
    async def bansync_create(self, ctx):
        """Create a new ban sync network"""
        # Check if already in a network
        if self.get_guild_network(ctx.guild.id):
            embed = discord.Embed(description="✖️ This server is already in a network. Use `!bansync leave` first", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        # Check if user already has a network
        if ctx.author.id in self.networks:
            network = self.networks[ctx.author.id]
            network.add_guild(ctx.guild.id)
            self.guild_network[ctx.guild.id] = ctx.author.id

            embed = discord.Embed(color=EMBED_COLOR)
            embed.description = (
                f"+ Added to existing network\n\n"
                f"› Network ID: `{network.network_id}`\n"
                f"› Total Servers: `{len(network.guild_ids)}`"
            )
        else:
            # Create new network
            network = self.create_network(ctx.author.id)
            network.add_guild(ctx.guild.id)
            self.guild_network[ctx.guild.id] = ctx.author.id

            embed = discord.Embed(color=EMBED_COLOR)
            embed.description = (
                f"+ Network created\n\n"
                f"› Network ID: `{network.network_id}`\n\n"
                f"Use `!bansync join` in your other servers to link them"
            )

        await ctx.send(embed=embed)

    @bansync.command(name='join')
    @commands.has_permissions(administrator=True)
    async def bansync_join(self, ctx, owner: discord.User = None):
        """Join a ban sync network by owner ID"""
        if self.get_guild_network(ctx.guild.id):
            embed = discord.Embed(description="✖️ This server is already in a network. Use `!bansync leave` first", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        if not owner:
            embed = discord.Embed(description="✖️ Please specify the network owner: `!bansync join @owner`", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        network = self.get_network(owner.id)
        if not network:
            embed = discord.Embed(description=f"✖️ No network found for {owner}. They need to create one first", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        # Only allow the owner or server owner to add servers
        if ctx.author.id != owner.id and ctx.author.id != ctx.guild.owner_id:
            embed = discord.Embed(description="✖️ Only the network owner or server owner can join a network", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        network.add_guild(ctx.guild.id)
        self.guild_network[ctx.guild.id] = owner.id

        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = (
            f"+ Joined network\n\n"
            f"› Owner: {owner}\n"
            f"› Total Servers: `{len(network.guild_ids)}`\n"
            f"› Global Bans: `{len(network.global_bans)}`"
        )

        # Auto-apply existing bans
        if network.settings.get('auto_ban', True):
            embed.description += f"\n\nUsers on the global ban list (`{len(network.global_bans)}`) will be auto-banned if they join"

        await ctx.send(embed=embed)

    @bansync.command(name='leave')
    @commands.has_permissions(administrator=True)
    async def bansync_leave(self, ctx):
        """Leave the ban sync network"""
        network = self.get_guild_network(ctx.guild.id)
        if not network:
            embed = discord.Embed(description="✖️ This server is not in any network", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        network.remove_guild(ctx.guild.id)
        del self.guild_network[ctx.guild.id]

        embed = discord.Embed(description="➕ Left the ban sync network", color=EMBED_COLOR)
        await ctx.send(embed=embed)

    @bansync.command(name='list')
    @commands.has_permissions(administrator=True)
    async def bansync_list(self, ctx):
        """List all servers in the network"""
        network = self.get_guild_network(ctx.guild.id)
        if not network:
            embed = discord.Embed(description="✖️ This server is not in any network", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        server_list = []
        for guild_id in network.guild_ids:
            guild = self.bot.get_guild(guild_id)
            if guild:
                is_current = " (current)" if guild_id == ctx.guild.id else ""
                server_list.append(f"› **{guild.name}** ({guild.member_count or 0} members){is_current}")
            else:
                server_list.append(f"› Unknown Server (`{guild_id}`)")

        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = (
            f"**Network Servers** `{len(network.guild_ids)}`\n\n" +
            "\n".join(server_list) if server_list else "No servers in network"
        )
        await ctx.send(embed=embed)

    @bansync.command(name='bans')
    @commands.has_permissions(administrator=True)
    async def bansync_bans(self, ctx, page: int = 1):
        """View the global ban list"""
        network = self.get_guild_network(ctx.guild.id)
        if not network:
            embed = discord.Embed(description="✖️ This server is not in any network", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        bans = list(network.global_bans.values())
        bans.sort(key=lambda x: x.timestamp, reverse=True)

        per_page = 10
        start = (page - 1) * per_page
        end = start + per_page
        page_bans = bans[start:end]
        total_pages = (len(bans) + per_page - 1) // per_page

        if not page_bans:
            embed = discord.Embed(description="No bans in the global list", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        desc = f"**Global Ban List** `{len(bans)}`\n\n"
        for record in page_bans:
            tags = f" [{', '.join(record.tags)}]" if record.tags else ""
            desc += f"› **{record.user_name}**{tags}\n  ID: `{record.user_id}` | From: {record.source_guild_name}\n"

        desc += f"\nPage {page}/{max(1, total_pages)}"

        embed = discord.Embed(description=desc, color=EMBED_COLOR)
        await ctx.send(embed=embed)

    @bansync.command(name='add')
    @commands.has_permissions(ban_members=True)
    async def bansync_add(self, ctx, user: discord.User, *, reason: str = "No reason provided"):
        """Add a user to the global ban list"""
        network = self.get_guild_network(ctx.guild.id)
        if not network:
            embed = discord.Embed(description="✖️ This server is not in any network", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        record = BanRecord(
            user_id=user.id,
            user_name=str(user),
            reason=reason,
            banned_by=ctx.author.id,
            banned_by_name=str(ctx.author),
            source_guild_id=ctx.guild.id,
            source_guild_name=ctx.guild.name,
            timestamp=datetime.utcnow()
        )

        # Sync to network
        synced, failed = await self.sync_ban_to_network(record, ctx.guild)

        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = (
            f"+ Added to global ban list\n\n"
            f"› User: {user} (`{user.id}`)\n"
            f"› Reason: {reason[:200]}\n"
            f"› Synced: `{synced}` servers"
        )
        if failed > 0:
            embed.description += f"\n› Failed: `{failed}` servers"

        await ctx.send(embed=embed)

    @bansync.command(name='remove')
    @commands.has_permissions(ban_members=True)
    async def bansync_remove(self, ctx, user: discord.User):
        """Remove a user from the global ban list"""
        network = self.get_guild_network(ctx.guild.id)
        if not network:
            embed = discord.Embed(description="✖️ This server is not in any network", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        if not network.is_banned(user.id):
            embed = discord.Embed(description=f"✖️ {user} is not on the global ban list", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        network.remove_ban(user.id)
        embed = discord.Embed(description=f"➖ Removed {user} from the global ban list", color=EMBED_COLOR)
        await ctx.send(embed=embed)

    @bansync.command(name='import')
    @commands.has_permissions(administrator=True)
    async def bansync_import(self, ctx):
        """Import all current server bans to the global list"""
        network = self.get_guild_network(ctx.guild.id)
        if not network:
            embed = discord.Embed(description="✖️ This server is not in any network", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        embed = discord.Embed(description="Importing bans...", color=EMBED_COLOR)
        status_msg = await ctx.send(embed=embed)

        imported = 0
        async for ban_entry in ctx.guild.bans():
            if not network.is_banned(ban_entry.user.id):
                record = BanRecord(
                    user_id=ban_entry.user.id,
                    user_name=str(ban_entry.user),
                    reason=ban_entry.reason or "Imported ban",
                    banned_by=ctx.author.id,
                    banned_by_name=str(ctx.author),
                    source_guild_id=ctx.guild.id,
                    source_guild_name=ctx.guild.name,
                    timestamp=datetime.utcnow()
                )
                network.add_ban(record)
                imported += 1

        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = (
            f"+ Import complete\n\n"
            f"› Imported: `{imported}` bans\n"
            f"› Total Global Bans: `{len(network.global_bans)}`"
        )

        await status_msg.edit(embed=embed)

    @bansync.command(name='settings')
    @commands.has_permissions(administrator=True)
    async def bansync_settings(self, ctx, setting: str = None, value: str = None):
        """Configure ban sync settings"""
        network = self.get_guild_network(ctx.guild.id)
        if not network:
            embed = discord.Embed(description="✖️ This server is not in any network", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        if not setting:
            settings_list = [
                f"› auto_ban: `{'on' if network.settings['auto_ban'] else 'off'}` − Auto-ban users on global list",
                f"› sync_unbans: `{'on' if network.settings['sync_unbans'] else 'off'}` − Sync unbans to other servers",
                f"› notify_on_ban: `{'on' if network.settings['notify_on_ban'] else 'off'}` − Notify when bans are synced",
            ]

            embed = discord.Embed(color=EMBED_COLOR)
            embed.description = (
                f"**Ban Sync Settings**\n\n" +
                "\n".join(settings_list) + "\n\n"
                f"**Usage**\n"
                f"`!bansync settings <setting> <on/off>`"
            )

            return await ctx.send(embed=embed)

        valid_settings = ['auto_ban', 'sync_unbans', 'notify_on_ban']
        if setting not in valid_settings:
            embed = discord.Embed(description=f"✖️ Invalid setting. Choose from: `{', '.join(valid_settings)}`", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        if value not in ['on', 'off', 'true', 'false', '1', '0']:
            embed = discord.Embed(description="✖️ Value must be `on` or `off`", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        new_value = value in ['on', 'true', '1']
        network.settings[setting] = new_value

        status = "enabled" if new_value else "disabled"
        embed = discord.Embed(description=f"➕ `{setting}` is now `{status}`", color=EMBED_COLOR)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(BanSync(bot))
