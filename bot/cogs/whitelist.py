"""
Unified Whitelist Management Cog
================================
Single whitelist system for all anti-nuke bypass:
- Users, Roles, and Bots
- Bypass ALL anti-nuke features
- Cannot be punished
- Can send messages during lockdown
- Database persistent
"""

import discord
from discord.ext import commands
from datetime import datetime
from collections import defaultdict
import logging
from typing import Dict, Optional, Set, List
import os

logger = logging.getLogger('Offcialx.Whitelist')

# Minimal embed color
EMBED_COLOR = 0x2b2d31


class Whitelist(commands.Cog):
    """Unified Whitelist Management System"""

    def __init__(self, bot):
        self.bot = bot
        self.db = None  # Will be injected by bot

        # Whitelisted entities (all bypass anti-nuke + lockdown)
        self.whitelisted_users: Dict[int, Set[int]] = defaultdict(set)  # guild_id -> set of user_ids
        self.whitelisted_roles: Dict[int, Set[int]] = defaultdict(set)  # guild_id -> set of role_ids
        self.whitelisted_bots: Dict[int, Set[int]] = defaultdict(set)   # guild_id -> set of bot_ids

        self._loaded_guilds: Set[int] = set()

        # Owner IDs from environment
        self.owner_ids: Set[int] = set()
        for oid in os.getenv('OWNER_IDS', '').split(','):
            try:
                self.owner_ids.add(int(oid.strip()))
            except:
                pass

    def is_owner(self, guild: discord.Guild, user_id: int) -> bool:
        """Check if user is server owner or bot owner"""
        if user_id == guild.owner_id:
            return True
        if user_id in self.owner_ids:
            return True
        if self.bot.owner_ids and user_id in self.bot.owner_ids:
            return True
        return False

    async def owner_check(self, ctx) -> bool:
        """Check ownership and send error if not owner"""
        if not self.is_owner(ctx.guild, ctx.author.id):
            embed = discord.Embed(description="✖️ Only server owner can manage whitelist", color=EMBED_COLOR)
            await ctx.send(embed=embed)
            return False
        return True

    async def load_guild_whitelist(self, guild_id: int):
        """Load whitelist from database for a guild"""
        if guild_id in self._loaded_guilds or not self.db:
            return

        try:
            # Load trusted users
            users = await self.db.get_trusted_users(guild_id)
            self.whitelisted_users[guild_id] = set(users)

            # Load trusted bots
            bots = await self.db.get_trusted_bots(guild_id)
            self.whitelisted_bots[guild_id] = set(bots)

            # Load trusted roles
            roles = await self.db.get_trusted_roles(guild_id)
            self.whitelisted_roles[guild_id] = set(roles)

            self._loaded_guilds.add(guild_id)
            logger.info(f"Loaded whitelist for guild {guild_id}: {len(users)} users, {len(bots)} bots, {len(roles)} roles")
        except Exception as e:
            logger.warning(f"Failed to load whitelist for guild {guild_id}: {e}")

    async def preload_all_guilds(self):
        """Preload whitelist for all guilds on startup"""
        if not self.db:
            return

        for guild in self.bot.guilds:
            await self.load_guild_whitelist(guild.id)

    async def preload_all_settings(self):
        """Preload whitelist for all guilds (called by main.py on startup)"""
        await self.preload_all_guilds()

    # ==================== CHECK METHODS (Used by Anti-Nuke) ====================

    def is_whitelisted(self, guild_id: int, user_id: int) -> bool:
        """Check if a user is whitelisted (bypasses anti-nuke)"""
        # Check if user is directly whitelisted
        if user_id in self.whitelisted_users.get(guild_id, set()):
            return True

        # Check if user is a whitelisted bot
        if user_id in self.whitelisted_bots.get(guild_id, set()):
            return True

        # Check if user has a whitelisted role
        guild = self.bot.get_guild(guild_id)
        if guild:
            member = guild.get_member(user_id)
            if member:
                member_role_ids = {r.id for r in member.roles}
                if member_role_ids & self.whitelisted_roles.get(guild_id, set()):
                    return True

        return False

    def is_whitelisted_bot(self, guild_id: int, bot_id: int) -> bool:
        """Check if a bot is whitelisted"""
        return bot_id in self.whitelisted_bots.get(guild_id, set())

    def is_whitelisted_role(self, guild_id: int, role_id: int) -> bool:
        """Check if a role is whitelisted"""
        return role_id in self.whitelisted_roles.get(guild_id, set())

    def has_whitelisted_role(self, guild_id: int, member: discord.Member) -> bool:
        """Check if a member has any whitelisted role"""
        if not member:
            return False
        member_role_ids = {r.id for r in member.roles}
        return bool(member_role_ids & self.whitelisted_roles.get(guild_id, set()))

    def get_whitelisted_users(self, guild_id: int) -> Set[int]:
        """Get all whitelisted user IDs"""
        return self.whitelisted_users.get(guild_id, set())

    def get_whitelisted_bots(self, guild_id: int) -> Set[int]:
        """Get all whitelisted bot IDs"""
        return self.whitelisted_bots.get(guild_id, set())

    def get_whitelisted_roles(self, guild_id: int) -> Set[int]:
        """Get all whitelisted role IDs"""
        return self.whitelisted_roles.get(guild_id, set())

    # ==================== COMMANDS ====================

    @commands.hybrid_group(name='wlist', aliases=['wl', 'whitelist'], invoke_without_command=True)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def wlist(self, ctx: commands.Context):
        """View all whitelisted users, roles, and bots"""
        if not await self.owner_check(ctx):
            return

        await self.load_guild_whitelist(ctx.guild.id)

        users = self.whitelisted_users.get(ctx.guild.id, set())
        roles = self.whitelisted_roles.get(ctx.guild.id, set())
        bots = self.whitelisted_bots.get(ctx.guild.id, set())

        total = len(users) + len(roles) + len(bots)

        if total == 0:
            embed = discord.Embed(
                description=(
                    "**Whitelist** `empty`\n\n"
                    "Use these commands to add:\n"
                    "› `wlist user @user` − Add user\n"
                    "› `wlist role @role` − Add role\n"
                    "› `wlist bot @bot` − Add bot\n\n"
                    "*Whitelisted entries bypass anti-nuke and lockdown*"
                ),
                color=EMBED_COLOR
            )
            return await ctx.send(embed=embed)

        text = f"**Whitelist** `{total} entries`\n\n"

        # Users
        if users:
            user_list = []
            for uid in users:
                member = ctx.guild.get_member(uid)
                user_list.append(f"› {member.mention}" if member else f"› `{uid}`")
            text += f"**Users** `{len(users)}`\n" + "\n".join(user_list[:10])
            if len(users) > 10:
                text += f"\n› +{len(users) - 10} more"
            text += "\n\n"

        # Roles
        if roles:
            role_list = []
            for rid in roles:
                role = ctx.guild.get_role(rid)
                role_list.append(f"› {role.mention}" if role else f"› `{rid}`")
            text += f"**Roles** `{len(roles)}`\n" + "\n".join(role_list[:10])
            if len(roles) > 10:
                text += f"\n› +{len(roles) - 10} more"
            text += "\n\n"

        # Bots
        if bots:
            bot_list = []
            for bid in bots:
                member = ctx.guild.get_member(bid)
                bot_list.append(f"› {member.mention}" if member else f"› `{bid}`")
            text += f"**Bots** `{len(bots)}`\n" + "\n".join(bot_list[:10])
            if len(bots) > 10:
                text += f"\n› +{len(bots) - 10} more"

        text += "\n\n*All bypass anti-nuke + lockdown*"

        embed = discord.Embed(description=text.strip(), color=EMBED_COLOR)
        await ctx.send(embed=embed)

    # ==================== ADD COMMANDS ====================

    @wlist.command(name='user')
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def wlist_user(self, ctx: commands.Context, user: discord.Member):
        """Add a user to the whitelist (bypasses anti-nuke + lockdown)"""
        if not await self.owner_check(ctx):
            return

        await self.load_guild_whitelist(ctx.guild.id)

        if user.id in self.whitelisted_users[ctx.guild.id]:
            embed = discord.Embed(description=f"› {user.mention} is already whitelisted", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        self.whitelisted_users[ctx.guild.id].add(user.id)

        # Save to database
        if self.db:
            try:
                await self.db.add_trusted_user(ctx.guild.id, user.id)
            except Exception as e:
                logger.warning(f'Failed to save whitelisted user: {e}')

        embed = discord.Embed(
            description=f"➕ Added {user.mention} to whitelist\n› Bypasses anti-nuke + lockdown",
            color=EMBED_COLOR
        )
        await ctx.send(embed=embed)

    @wlist.command(name='role')
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def wlist_role(self, ctx: commands.Context, role: discord.Role):
        """Add a role to the whitelist (all members bypass anti-nuke + lockdown)"""
        if not await self.owner_check(ctx):
            return

        if role.is_default():
            embed = discord.Embed(description="✖️ Cannot whitelist @everyone", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        await self.load_guild_whitelist(ctx.guild.id)

        if role.id in self.whitelisted_roles[ctx.guild.id]:
            embed = discord.Embed(description=f"› {role.mention} is already whitelisted", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        self.whitelisted_roles[ctx.guild.id].add(role.id)

        # Save to database
        if self.db:
            try:
                await self.db.add_trusted_role(ctx.guild.id, role.id, ctx.author.id)
            except Exception as e:
                logger.warning(f'Failed to save whitelisted role: {e}')

        embed = discord.Embed(
            description=f"➕ Added {role.mention} to whitelist\n› All members bypass anti-nuke + lockdown",
            color=EMBED_COLOR
        )
        await ctx.send(embed=embed)

    @wlist.command(name='bot')
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def wlist_bot(self, ctx: commands.Context, bot: discord.Member):
        """Add a bot to the whitelist (bypasses anti-nuke + lockdown)"""
        if not await self.owner_check(ctx):
            return

        if not bot.bot:
            embed = discord.Embed(description="✖️ That's not a bot. Use `wlist user` for users", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        await self.load_guild_whitelist(ctx.guild.id)

        if bot.id in self.whitelisted_bots[ctx.guild.id]:
            embed = discord.Embed(description=f"› {bot.mention} is already whitelisted", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        self.whitelisted_bots[ctx.guild.id].add(bot.id)

        # Save to database
        if self.db:
            try:
                await self.db.add_trusted_bot(ctx.guild.id, bot.id)
            except Exception as e:
                logger.warning(f'Failed to save whitelisted bot: {e}')

        embed = discord.Embed(
            description=f"➕ Added {bot.mention} to whitelist\n› Bypasses anti-nuke + lockdown",
            color=EMBED_COLOR
        )
        await ctx.send(embed=embed)

    # ==================== REMOVE COMMANDS ====================

    @wlist.group(name='remove', aliases=['rm', 'del'], invoke_without_command=True)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def wlist_remove(self, ctx: commands.Context):
        """Remove users, roles, or bots from whitelist"""
        embed = discord.Embed(
            description=(
                "**Remove from Whitelist**\n\n"
                "› `wlist remove user @user`\n"
                "› `wlist remove role @role`\n"
                "› `wlist remove bot @bot`"
            ),
            color=EMBED_COLOR
        )
        await ctx.send(embed=embed)

    @wlist_remove.command(name='user')
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def wlist_remove_user(self, ctx: commands.Context, user: discord.Member):
        """Remove a user from the whitelist"""
        if not await self.owner_check(ctx):
            return

        await self.load_guild_whitelist(ctx.guild.id)

        if user.id not in self.whitelisted_users[ctx.guild.id]:
            embed = discord.Embed(description=f"› {user.mention} is not whitelisted", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        self.whitelisted_users[ctx.guild.id].discard(user.id)

        # Remove from database
        if self.db:
            try:
                await self.db.remove_trusted_user(ctx.guild.id, user.id)
            except Exception as e:
                logger.warning(f'Failed to remove whitelisted user: {e}')

        embed = discord.Embed(description=f"➖ Removed {user.mention} from whitelist", color=EMBED_COLOR)
        await ctx.send(embed=embed)

    @wlist_remove.command(name='role')
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def wlist_remove_role(self, ctx: commands.Context, role: discord.Role):
        """Remove a role from the whitelist"""
        if not await self.owner_check(ctx):
            return

        await self.load_guild_whitelist(ctx.guild.id)

        if role.id not in self.whitelisted_roles[ctx.guild.id]:
            embed = discord.Embed(description=f"› {role.mention} is not whitelisted", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        self.whitelisted_roles[ctx.guild.id].discard(role.id)

        # Remove from database
        if self.db:
            try:
                await self.db.remove_trusted_role(ctx.guild.id, role.id)
            except Exception as e:
                logger.warning(f'Failed to remove whitelisted role: {e}')

        embed = discord.Embed(description=f"➖ Removed {role.mention} from whitelist", color=EMBED_COLOR)
        await ctx.send(embed=embed)

    @wlist_remove.command(name='bot')
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def wlist_remove_bot(self, ctx: commands.Context, bot: discord.Member):
        """Remove a bot from the whitelist"""
        if not await self.owner_check(ctx):
            return

        if not bot.bot:
            embed = discord.Embed(description="✖️ That's not a bot", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        await self.load_guild_whitelist(ctx.guild.id)

        if bot.id not in self.whitelisted_bots[ctx.guild.id]:
            embed = discord.Embed(description=f"› {bot.mention} is not whitelisted", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        self.whitelisted_bots[ctx.guild.id].discard(bot.id)

        # Remove from database
        if self.db:
            try:
                await self.db.remove_trusted_bot(ctx.guild.id, bot.id)
            except Exception as e:
                logger.warning(f'Failed to remove whitelisted bot: {e}')

        embed = discord.Embed(description=f"➖ Removed {bot.mention} from whitelist", color=EMBED_COLOR)
        await ctx.send(embed=embed)

    # ==================== CLEAR COMMANDS ====================

    @wlist.command(name='clear')
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def wlist_clear(self, ctx: commands.Context, category: str = None):
        """Clear whitelist (all, users, roles, or bots)"""
        if not await self.owner_check(ctx):
            return

        # Extra safety: only server owner can clear
        if ctx.author.id != ctx.guild.owner_id and ctx.author.id not in self.owner_ids:
            embed = discord.Embed(description="✖️ Only server owner can clear whitelist", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        await self.load_guild_whitelist(ctx.guild.id)

        if category is None or category.lower() == 'all':
            # Clear all
            user_count = len(self.whitelisted_users.get(ctx.guild.id, set()))
            role_count = len(self.whitelisted_roles.get(ctx.guild.id, set()))
            bot_count = len(self.whitelisted_bots.get(ctx.guild.id, set()))
            total = user_count + role_count + bot_count

            self.whitelisted_users[ctx.guild.id] = set()
            self.whitelisted_roles[ctx.guild.id] = set()
            self.whitelisted_bots[ctx.guild.id] = set()

            # Clear from database
            if self.db:
                try:
                    # Clear all trusted entries for this guild
                    for uid in list(self.whitelisted_users.get(ctx.guild.id, set())):
                        await self.db.remove_trusted_user(ctx.guild.id, uid)
                    for rid in list(self.whitelisted_roles.get(ctx.guild.id, set())):
                        await self.db.remove_trusted_role(ctx.guild.id, rid)
                    for bid in list(self.whitelisted_bots.get(ctx.guild.id, set())):
                        await self.db.remove_trusted_bot(ctx.guild.id, bid)
                except Exception as e:
                    logger.warning(f'Failed to clear whitelist from database: {e}')

            embed = discord.Embed(description=f"➕ Cleared entire whitelist `{total} entries`", color=EMBED_COLOR)
            await ctx.send(embed=embed)

        elif category.lower() == 'users':
            count = len(self.whitelisted_users.get(ctx.guild.id, set()))
            for uid in list(self.whitelisted_users.get(ctx.guild.id, set())):
                if self.db:
                    try:
                        await self.db.remove_trusted_user(ctx.guild.id, uid)
                    except:
                        pass
            self.whitelisted_users[ctx.guild.id] = set()
            embed = discord.Embed(description=f"➕ Cleared `{count}` whitelisted users", color=EMBED_COLOR)
            await ctx.send(embed=embed)

        elif category.lower() == 'roles':
            count = len(self.whitelisted_roles.get(ctx.guild.id, set()))
            for rid in list(self.whitelisted_roles.get(ctx.guild.id, set())):
                if self.db:
                    try:
                        await self.db.remove_trusted_role(ctx.guild.id, rid)
                    except:
                        pass
            self.whitelisted_roles[ctx.guild.id] = set()
            embed = discord.Embed(description=f"➕ Cleared `{count}` whitelisted roles", color=EMBED_COLOR)
            await ctx.send(embed=embed)

        elif category.lower() == 'bots':
            count = len(self.whitelisted_bots.get(ctx.guild.id, set()))
            for bid in list(self.whitelisted_bots.get(ctx.guild.id, set())):
                if self.db:
                    try:
                        await self.db.remove_trusted_bot(ctx.guild.id, bid)
                    except:
                        pass
            self.whitelisted_bots[ctx.guild.id] = set()
            embed = discord.Embed(description=f"➕ Cleared `{count}` whitelisted bots", color=EMBED_COLOR)
            await ctx.send(embed=embed)

        else:
            embed = discord.Embed(
                description="**Clear Whitelist**\n\n› `wlist clear` − Clear all\n› `wlist clear users`\n› `wlist clear roles`\n› `wlist clear bots`",
                color=EMBED_COLOR
            )
            await ctx.send(embed=embed)

    # ==================== LIST COMMANDS ====================

    @wlist.command(name='users')
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def wlist_users(self, ctx: commands.Context):
        """View all whitelisted users"""
        if not await self.owner_check(ctx):
            return

        await self.load_guild_whitelist(ctx.guild.id)
        users = self.whitelisted_users.get(ctx.guild.id, set())

        if not users:
            embed = discord.Embed(description="**Whitelisted Users** `0`\n\n› No whitelisted users", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        user_list = []
        for uid in users:
            member = ctx.guild.get_member(uid)
            user_list.append(f"› {member.mention}" if member else f"› `{uid}`")

        embed = discord.Embed(
            description=f"**Whitelisted Users** `{len(users)}`\n\n" + "\n".join(user_list),
            color=EMBED_COLOR
        )
        await ctx.send(embed=embed)

    @wlist.command(name='roles')
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def wlist_roles(self, ctx: commands.Context):
        """View all whitelisted roles"""
        if not await self.owner_check(ctx):
            return

        await self.load_guild_whitelist(ctx.guild.id)
        roles = self.whitelisted_roles.get(ctx.guild.id, set())

        if not roles:
            embed = discord.Embed(description="**Whitelisted Roles** `0`\n\n› No whitelisted roles", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        role_list = []
        for rid in roles:
            role = ctx.guild.get_role(rid)
            role_list.append(f"› {role.mention}" if role else f"› `{rid}`")

        embed = discord.Embed(
            description=f"**Whitelisted Roles** `{len(roles)}`\n\n" + "\n".join(role_list),
            color=EMBED_COLOR
        )
        await ctx.send(embed=embed)

    @wlist.command(name='bots')
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def wlist_bots(self, ctx: commands.Context):
        """View all whitelisted bots"""
        if not await self.owner_check(ctx):
            return

        await self.load_guild_whitelist(ctx.guild.id)
        bots = self.whitelisted_bots.get(ctx.guild.id, set())

        if not bots:
            embed = discord.Embed(description="**Whitelisted Bots** `0`\n\n› No whitelisted bots", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        bot_list = []
        for bid in bots:
            member = ctx.guild.get_member(bid)
            bot_list.append(f"› {member.mention}" if member else f"› `{bid}`")

        embed = discord.Embed(
            description=f"**Whitelisted Bots** `{len(bots)}`\n\n" + "\n".join(bot_list),
            color=EMBED_COLOR
        )
        await ctx.send(embed=embed)


async def setup(bot):
    cog = Whitelist(bot)
    await bot.add_cog(cog)
    # Note: preload_all_settings() is called by main.py after database is injected
