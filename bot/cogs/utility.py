"""
Utility Commands Cog
====================
Server and user information commands
Works with both prefix (!) and slash (/)
"""

import discord
from discord.ext import commands
from discord import app_commands
import logging

logger = logging.getLogger('Offcialx.Utility')

EMBED_COLOR = 0x2b2d31


class Utility(commands.Cog):
    """Utility commands for server and user information"""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name='avatar', aliases=['av', 'pfp'])
    @app_commands.describe(member="The user to get avatar of")
    async def avatar(self, ctx: commands.Context, member: discord.Member = None):
        """Get user's avatar"""
        member = member or ctx.author
        embed = discord.Embed(color=EMBED_COLOR)
        avatar_url = member.display_avatar.url
        embed.set_image(url=avatar_url)
        links = []
        try:
            links.append(f"[PNG]({member.display_avatar.replace(format='png', size=1024)})")
            links.append(f"[JPG]({member.display_avatar.replace(format='jpg', size=1024)})")
            links.append(f"[WEBP]({member.display_avatar.replace(format='webp', size=1024)})")
            if member.display_avatar.is_animated():
                links.append(f"[GIF]({member.display_avatar.replace(format='gif', size=1024)})")
        except:
            pass
        embed.description = f"**{member.display_name}'s Avatar**\n\n› {' • '.join(links) if links else ''}"
        if member.avatar and member.guild_avatar:
            embed.description += f"\n› [Global Avatar]({member.avatar.url})"
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='banner', aliases=['userbanner', 'ub'])
    @app_commands.describe(member="The user to get banner of")
    async def banner(self, ctx: commands.Context, member: discord.Member = None):
        """Get user's banner"""
        member = member or ctx.author
        try:
            user = await self.bot.fetch_user(member.id)
        except:
            user = member
        embed = discord.Embed(color=EMBED_COLOR)
        if user.banner:
            embed.set_image(url=user.banner.url)
            links = []
            try:
                links.append(f"[PNG]({user.banner.replace(format='png', size=1024)})")
                links.append(f"[JPG]({user.banner.replace(format='jpg', size=1024)})")
                links.append(f"[WEBP]({user.banner.replace(format='webp', size=1024)})")
                if user.banner.is_animated():
                    links.append(f"[GIF]({user.banner.replace(format='gif', size=1024)})")
            except:
                pass
            embed.description = f"**{member.display_name}'s Banner**\n\n› {' • '.join(links) if links else ''}"
        else:
            if hasattr(user, 'accent_color') and user.accent_color:
                embed.color = user.accent_color
                embed.description = f"**{member.display_name}**\n\n› No banner set\n› Accent color: `{user.accent_color}`"
            else:
                embed.description = f"**{member.display_name}**\n\n› No banner set"
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='userinfo', aliases=['ui', 'whois', 'user'])
    @app_commands.describe(member="The user to get info of")
    async def userinfo(self, ctx: commands.Context, member: discord.Member = None):
        """Get user information"""
        member = member or ctx.author
        try:
            user = await self.bot.fetch_user(member.id)
        except:
            user = member
        embed = discord.Embed(color=EMBED_COLOR)
        created = member.created_at.strftime("%b %d, %Y")
        joined = member.joined_at.strftime("%b %d, %Y") if member.joined_at else "Unknown"
        account_age = (discord.utils.utcnow() - member.created_at).days
        roles = [r.mention for r in member.roles if r.name != "@everyone"]
        roles_str = ", ".join(roles[:10]) if roles else "None"
        if len(roles) > 10:
            roles_str += f" +{len(roles) - 10} more"
        status_emoji = {
            discord.Status.online: "🟢",
            discord.Status.idle: "🟡",
            discord.Status.dnd: "🔴",
            discord.Status.offline: "⚫"
        }
        status = status_emoji.get(member.status, "⚫")
        desc = f"**{member}** {status}\n\n"
        desc += f"› ID: `{member.id}`\n"
        desc += f"› Created: `{created}` ({account_age} days ago)\n"
        desc += f"› Joined: `{joined}`\n"
        if member.nick:
            desc += f"› Nickname: `{member.nick}`\n"
        if member.top_role.name != "@everyone":
            desc += f"› Top Role: {member.top_role.mention}\n"
        desc += f"\n**Roles** [{len(roles)}]\n{roles_str}"
        if user.banner:
            desc += f"\n\n› [Banner]({user.banner.url})"
        embed.description = desc
        embed.set_thumbnail(url=member.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='serverinfo', aliases=['si', 'guildinfo', 'server'])
    async def serverinfo(self, ctx: commands.Context):
        """Get server information"""
        guild = ctx.guild
        created = guild.created_at.strftime("%b %d, %Y")
        age_days = (discord.utils.utcnow() - guild.created_at).days
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        total = guild.member_count or len(guild.members)
        bots = len([m for m in guild.members if m.bot])
        humans = total - bots
        boost_level = guild.premium_tier
        boost_count = guild.premium_subscription_count or 0
        embed = discord.Embed(color=EMBED_COLOR)
        desc = f"**{guild.name}**\n\n"
        desc += f"› ID: `{guild.id}`\n"
        desc += f"› Owner: {guild.owner.mention if guild.owner else 'Unknown'}\n"
        desc += f"› Created: `{created}` ({age_days} days ago)\n\n"
        desc += f"**Members** `{total}`\n"
        desc += f"› Humans: `{humans}` • Bots: `{bots}`\n\n"
        desc += f"**Channels** `{len(guild.channels)}`\n"
        desc += f"› Text: `{text_channels}` • Voice: `{voice_channels}` • Categories: `{categories}`\n\n"
        desc += f"**Boost**\n"
        desc += f"› Level: `{boost_level}` • Boosts: `{boost_count}`"
        embed.description = desc
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='servericon', aliases=['sicon', 'guildicon', 'icon'])
    async def servericon(self, ctx: commands.Context):
        """Get server's icon"""
        guild = ctx.guild
        embed = discord.Embed(color=EMBED_COLOR)
        if guild.icon:
            embed.set_image(url=guild.icon.url)
            links = []
            try:
                links.append(f"[PNG]({guild.icon.replace(format='png', size=1024)})")
                links.append(f"[JPG]({guild.icon.replace(format='jpg', size=1024)})")
                links.append(f"[WEBP]({guild.icon.replace(format='webp', size=1024)})")
                if guild.icon.is_animated():
                    links.append(f"[GIF]({guild.icon.replace(format='gif', size=1024)})")
            except:
                pass
            embed.description = f"**{guild.name}'s Icon**\n\n› {' • '.join(links) if links else ''}"
        else:
            embed.description = f"**{guild.name}**\n\n› No server icon set"
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='serverbanner', aliases=['sb', 'guildbanner'])
    async def serverbanner(self, ctx: commands.Context):
        """Get server's banner"""
        guild = ctx.guild
        embed = discord.Embed(color=EMBED_COLOR)
        if guild.banner:
            embed.set_image(url=guild.banner.url)
            links = []
            try:
                links.append(f"[PNG]({guild.banner.replace(format='png', size=1024)})")
                links.append(f"[JPG]({guild.banner.replace(format='jpg', size=1024)})")
                links.append(f"[WEBP]({guild.banner.replace(format='webp', size=1024)})")
                if guild.banner.is_animated():
                    links.append(f"[GIF]({guild.banner.replace(format='gif', size=1024)})")
            except:
                pass
            embed.description = f"**{guild.name}'s Banner**\n\n› {' • '.join(links) if links else ''}"
        else:
            embed.description = f"**{guild.name}**\n\n› No server banner set (requires boost level 2)"
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='serverprofile', aliases=['sp', 'guildprofile'])
    async def serverprofile(self, ctx: commands.Context):
        """View all server assets (icon, banner, splash)"""
        guild = ctx.guild
        embed = discord.Embed(color=EMBED_COLOR)
        desc = f"**{guild.name}'s Profile**\n\n"
        if guild.icon:
            desc += f"› [Server Icon]({guild.icon.url})\n"
        else:
            desc += "› No server icon\n"
        if guild.banner:
            desc += f"› [Server Banner]({guild.banner.url})\n"
        else:
            desc += "› No server banner\n"
        if guild.splash:
            desc += f"› [Invite Splash]({guild.splash.url})\n"
        else:
            desc += "› No invite splash\n"
        if guild.discovery_splash:
            desc += f"› [Discovery Splash]({guild.discovery_splash.url})\n"
        else:
            desc += "› No discovery splash\n"
        embed.description = desc
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        if guild.banner:
            embed.set_image(url=guild.banner.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='ping')
    async def ping(self, ctx: commands.Context):
        """Check bot latency"""
        latency = round(self.bot.latency * 1000)
        embed = discord.Embed(description=f"› Pong! `{latency}ms`", color=EMBED_COLOR)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='invite')
    async def invite(self, ctx: commands.Context):
        """Get bot invite link"""
        invite_url = f"https://discord.com/oauth2/authorize?client_id={self.bot.user.id}&permissions=8&scope=bot%20applications.commands"
        embed = discord.Embed(description=f"[Click here to invite me]({invite_url})", color=EMBED_COLOR)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='info', aliases=['about', 'botinfo'])
    async def info(self, ctx: commands.Context):
        """Bot information"""
        total_users = sum(g.member_count or 0 for g in self.bot.guilds)
        latency = round(self.bot.latency * 1000)

        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = (
            f"**Offcialx Security Bot**\n\n"
            f"› Servers: `{len(self.bot.guilds)}`\n"
            f"› Users: `{total_users:,}`\n"
            f"› Latency: `{latency}ms`\n\n"
            f"**Features**\n"
            f"› Anti-Nuke Protection\n"
            f"› Anti-Raid Detection\n"
            f"› Anti-Spam Filtering\n"
            f"› Whitelist Management\n"
            f"› Server Backup/Restore\n\n"
            f"[Support Server](https://discord.gg/NXK5sFEJSy)"
        )
        await ctx.send(embed=embed)

    # ==================== ADMIN SYNC COMMANDS ====================

    @commands.command(name='sync', hidden=True)
    @commands.is_owner()
    async def sync_commands(self, ctx: commands.Context):
        """Sync slash commands with Discord - Bot owner only"""
        try:
            # Show commands in tree before sync
            tree_commands = self.bot.tree.get_commands()
            await ctx.send(f"⟳ Found {len(tree_commands)} commands in tree, syncing...")

            synced = await self.bot.tree.sync()
            await ctx.send(f"+ Synced {len(synced)} commands globally\nCommands: {', '.join([c.name for c in synced[:20]])}")
        except Exception as e:
            await ctx.send(f"✕ Failed to sync: {e}")

    @commands.command(name='syncguild', hidden=True)
    @commands.is_owner()
    async def sync_guild_commands(self, ctx: commands.Context):
        """Sync slash commands to current guild - Bot owner only"""
        try:
            # Show commands in tree before sync
            tree_commands = self.bot.tree.get_commands()
            await ctx.send(f"⟳ Found {len(tree_commands)} commands, copying to guild...")

            self.bot.tree.copy_global_to(guild=ctx.guild)
            synced = await self.bot.tree.sync(guild=ctx.guild)
            await ctx.send(f"+ Synced {len(synced)} commands to this server\nCommands: {', '.join([c.name for c in synced[:20]])}")
        except Exception as e:
            await ctx.send(f"✕ Failed to sync: {e}")

    @commands.command(name='clearsync', hidden=True)
    @commands.is_owner()
    async def clear_and_sync(self, ctx: commands.Context):
        """Clear all slash commands and resync - Bot owner only"""
        try:
            # Clear global commands
            self.bot.tree.clear_commands(guild=None)
            await self.bot.tree.sync()

            # Clear guild commands for current guild
            self.bot.tree.clear_commands(guild=ctx.guild)
            await self.bot.tree.sync(guild=ctx.guild)

            # Now resync all commands
            synced = await self.bot.tree.sync()
            await ctx.send(f"+ Cleared and resynced {len(synced)} commands globally")
        except Exception as e:
            await ctx.send(f"✕ Failed: {e}")

    @commands.command(name='listcmds', hidden=True)
    @commands.is_owner()
    async def list_commands(self, ctx: commands.Context):
        """List all registered slash commands - Bot owner only"""
        try:
            commands_list = self.bot.tree.get_commands()
            if commands_list:
                cmd_names = [cmd.name for cmd in commands_list]
                await ctx.send(f"**Registered Commands ({len(cmd_names)}):**\n`{', '.join(cmd_names[:50])}`")
            else:
                await ctx.send("No slash commands registered!")
        except Exception as e:
            await ctx.send(f"✕ Failed: {e}")


async def setup(bot):
    await bot.add_cog(Utility(bot))
