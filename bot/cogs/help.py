"""
Custom Help Command Cog - Minimal Style
All commands work with both ! and /
"""
import discord
from discord.ext import commands
from typing import Optional
import logging

logger = logging.getLogger('Offcialx.Help')

# Minimal embed color
EMBED_COLOR = 0x2b2d31


class Help(commands.Cog):
    """Help Command System"""

    def __init__(self, bot):
        self.bot = bot
        self.bot.help_command = None

    def get_main_embed(self) -> discord.Embed:
        """Main help embed"""
        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = (
            "**Offcialx Security Bot**\n\n"
            "Use `/command` or `!command`\n\n"
            "**Categories**\n"
            "› `/help antinuke` − Server protection\n"
            "› `/help mod` − Moderation & Roles\n"
            "› `/help whitelist` − Whitelist management\n"
            "› `/help raid` − Anti-raid protection\n"
            "› `/help spam` − Anti-spam system\n"
            "› `/help lockdown` − Lockdown controls\n"
            "› `/help mirror` − Cross-server forwarding\n"
            "› `/help utility` − General commands\n"
            "› `/help owner` − Bot owner commands\n\n"
            "**Quick Start**\n"
            "› `/setup` − Run setup wizard\n"
            "› `/setlog #channel` − Set log channel\n"
            "› `/wlist user @user` − Whitelist a user\n\n"
            "**Popular Commands**\n"
            "› `/role` − Manage member roles\n"
            "› `/ban` `/kick` `/mute` − Moderation"
        )
        return embed

    def get_antinuke_embed(self) -> discord.Embed:
        """Anti-nuke commands embed"""
        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = (
            "**Anti-Nuke Commands**\n\n"
            "**Status** (Server Owner Only)\n"
            "› `antinuke` − View protection status\n"
            "› `antinuke enable` − Enable protection\n"
            "› `antinuke disable` − Disable protection\n"
            "› `attackstats` − View blocked attacks\n\n"
            "**Configuration**\n"
            "› `setlog #channel` − Set log channel\n"
            "› `punishment ban/kick` − Set punishment type\n\n"
            "**Whitelist** (bypass anti-nuke + lockdown)\n"
            "› `wlist` − View all whitelisted\n"
            "› `wlist user @user` − Whitelist user\n"
            "› `wlist role @role` − Whitelist role\n"
            "› `wlist bot @bot` − Whitelist bot\n"
            "› See `!help whitelist` for more\n\n"
            "**Emergency**\n"
            "› `serverlock [secs]` − Lock server\n"
            "› `serverunlock` − Unlock server\n"
            "› `lockdownstatus` − View lockdown status\n"
            "› `nukewebhooks` − Delete all webhooks\n\n"
            "**Recovery**\n"
            "› `recover` − Restore ALL deleted channels\n"
            "› `restore` − View deleted channels\n"
            "› `restore_channel <num>` − Restore one channel\n"
            "› `restore_clear` − Clear restore list\n\n"
            "**Protection**\n"
            "Server settings, vanity URL, and all changes\n"
            "are monitored. Attackers are banned instantly."
        )
        return embed

    def get_mod_embed(self) -> discord.Embed:
        """Moderation commands embed"""
        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = (
            "**Moderation Commands**\n\n"
            "**Member Actions** (Admin)\n"
            "› `/ban` `!ban @user [reason]` − Ban member\n"
            "› `/kick` `!kick @user [reason]` − Kick member\n"
            "› `/mute` `!mute @user [time]` − Timeout member\n"
            "› `/unmute` `!unmute @user` − Remove timeout\n\n"
            "**Role Management** (Admin)\n"
            "› `/role` − Toggle role (slash picker)\n"
            "› `!role @user RoleName` − Toggle by name\n"
            "› `!giverole @user RoleName` − Add role\n"
            "› `!takerole @user RoleName` − Remove role\n\n"
            "**Channel Management** (Manage Channels)\n"
            "› `!purge [amount]` − Delete messages\n"
            "› `!purge @user [amount]` − Delete user messages\n"
            "› `!slowmode [secs]` − Set slowmode\n"
            "› `!lock` − Lock channel\n"
            "› `!unlockc` − Unlock channel\n\n"
            "**Other** (Admin)\n"
            "› `!nick @user [name]` − Set nickname\n"
            "› `!serverlock [secs]` − Lock server"
        )
        return embed

    def get_whitelist_embed(self) -> discord.Embed:
        """Whitelist commands embed"""
        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = (
            "**Unified Whitelist** (Server Owner Only)\n\n"
            "Whitelisted entries bypass:\n"
            "› All anti-nuke protection\n"
            "› Cannot be punished\n"
            "› Can send messages during lockdown\n\n"
            "**Add to Whitelist**\n"
            "› `wlist user @user` − Whitelist a user\n"
            "› `wlist role @role` − Whitelist a role\n"
            "› `wlist bot @bot` − Whitelist a bot\n\n"
            "**Remove from Whitelist**\n"
            "› `wlist remove user @user`\n"
            "› `wlist remove role @role`\n"
            "› `wlist remove bot @bot`\n\n"
            "**View Whitelist**\n"
            "› `wlist` − View all whitelisted\n"
            "› `wlist users` − View whitelisted users\n"
            "› `wlist roles` − View whitelisted roles\n"
            "› `wlist bots` − View whitelisted bots\n\n"
            "**Clear Whitelist**\n"
            "› `wlist clear` − Clear all\n"
            "› `wlist clear users` − Clear users only\n"
            "› `wlist clear roles` − Clear roles only\n"
            "› `wlist clear bots` − Clear bots only\n\n"
            "**Database**\n"
            "All whitelist data persists in database."
        )
        return embed

    def get_raid_embed(self) -> discord.Embed:
        """Anti-raid commands embed"""
        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = (
            "**Anti-Raid Commands** (Server Owner Only)\n\n"
            "**Status**\n"
            "› `antiraid` − View status\n"
            "› `antiraid status` − Detailed status\n\n"
            "**Configuration**\n"
            "› `antiraid enable` − Enable protection\n"
            "› `antiraid disable` − Disable protection\n"
            "› `antiraid action <kick/ban>` − Set action\n"
            "› `antiraid setlog #channel` − Set log channel\n\n"
            "**VPN Detection**\n"
            "› `vpn` − View VPN status\n"
            "› `vpn enable` − Enable detection\n"
            "› `vpn disable` − Disable detection\n"
            "› `vpn action <kick/ban>` − Set action\n\n"
            "**Ban Sync**\n"
            "› `bansync` − View network\n"
            "› `bansync create` − Create network\n"
            "› `bansync list` − List servers\n\n"
            "**Database**\n"
            "All settings persist in database."
        )
        return embed

    def get_spam_embed(self) -> discord.Embed:
        """Anti-spam commands embed"""
        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = (
            "**Anti-Spam Commands** (Server Owner Only)\n\n"
            "**Status**\n"
            "› `antispam` − View spam protection\n"
            "› `antispam status` − Detailed status\n\n"
            "**Configuration**\n"
            "› `antispam enable` − Enable protection\n"
            "› `antispam disable` − Disable protection\n"
            "› `antispam setlog #channel` − Set log\n"
            "› `antispam action <warn/mute/kick/ban>`\n"
            "› `antispam limit <count> <seconds>`\n\n"
            "**Link Filtering**\n"
            "› `antispam links <true/false>` − Allow/block links\n"
            "› `antispam invites <true/false>` − Allow/block invites\n"
            "› `antispam shorteners <true/false>` − Block URL shorteners\n"
            "› `antispam phishing <true/false>` − Block phishing\n\n"
            "**Exemptions**\n"
            "› `antispam exempt @role` − Exempt role\n"
            "› `antispam unexempt @role` − Remove exemption\n\n"
            "**Anti-Selfbot** (Server Owner Only)\n"
            "› `antiselfbot` − View status\n"
            "› `antiselfbot enable/disable` − Toggle\n"
            "› `antiselfbot action <alert/mute/kick/ban>`\n"
            "Detects: embed spam, fast reactions, nitro sniping\n\n"
            "**Database**\n"
            "All settings persist in database."
        )
        return embed

    def get_lockdown_embed(self) -> discord.Embed:
        """Lockdown commands embed"""
        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = (
            "**Lockdown Commands** (Server Owner Only)\n\n"
            "**Server Lockdown**\n"
            "› `lockdown [duration] [reason]` − Lock server\n"
            "› `lockdown end` − End lockdown\n"
            "› `lockdown status` − View status\n\n"
            "**Configuration**\n"
            "› `lockdown setlog #channel` − Set log\n"
            "› `lockdown duration <seconds>` − Default duration\n\n"
            "**Channel Locking** (Manage Channels)\n"
            "› `lock` − Lock current channel\n"
            "› `unlockc` − Unlock current channel\n\n"
            "**Emergency**\n"
            "› `panic` − Instant full lockdown\n"
            "› `serverlock [secs]` − Quick lock\n"
            "› `serverunlock` − Quick unlock\n\n"
            "**Database**\n"
            "All settings persist in database."
        )
        return embed

    def get_owner_embed(self) -> discord.Embed:
        """Bot owner commands embed"""
        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = (
            "**Bot Owner Commands**\n\n"
            "**Bot Status**\n"
            "› `botstatus` − View current status\n"
            "› `botstatus watching <text>` − Set watching\n"
            "› `botstatus playing <text>` − Set playing\n"
            "› `botstatus listening <text>` − Set listening\n"
            "› `botstatus streaming <url> <text>` − Set streaming\n"
            "› `botstatus online/idle/dnd/invisible` − Set status\n"
            "› `botstatus clear` − Remove activity\n\n"
            "**Server Management**\n"
            "› `servers` − View server count & stats\n"
            "› `serverlist` − List all servers with IDs\n"
            "› `leaveserver <id>` − Leave a server\n\n"
            "**Join/Leave Logging**\n"
            "› `setjoinlog #channel` − Set log channel\n"
            "Bot owners receive DM when bot joins/leaves\n\n"
            "**Bot Information**\n"
            "› `ownerinfo` − View bot stats & uptime\n\n"
            "**Anti-Nuke Settings**\n"
            "› `punishment ban/kick` − Set punishment type\n"
            "› `antiselfbot action ban/kick/mute/alert`"
        )
        return embed

    def get_utility_embed(self) -> discord.Embed:
        """Utility commands embed"""
        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = (
            "**Utility Commands**\n\n"
            "**Information**\n"
            "› `help [category]` − This menu\n"
            "› `ping` − Check latency\n"
            "› `botstats` − Bot statistics\n"
            "› `info` − Bot information\n\n"
            "**User Info**\n"
            "› `userinfo [@user]` − User details\n"
            "› `avatar [@user]` − User avatar\n"
            "› `banner [@user]` − User banner\n\n"
            "**Server Info**\n"
            "› `serverinfo` − Server details\n"
            "› `servericon` − Server icon\n"
            "› `serverbanner` − Server banner\n"
            "› `serverprofile` − Full server profile\n\n"
            "**Links**\n"
            "› `invite` − Invite link\n"
            "› `support` − Support server\n\n"
            "**Setup** (Server Owner)\n"
            "› `setup` − Setup wizard\n"
            "› `setlog #channel` − Set log channel\n\n"
            "**Backup** (Server Owner)\n"
            "› `backup create` − Create backup\n"
            "› `backup list` − List backups\n\n"
            "**Sync** (Bot Owner)\n"
            "› `sync` − Sync global commands\n"
            "› `syncguild` − Sync to this server"
        )
        return embed

    def get_mirror_embed(self) -> discord.Embed:
        """Mirror commands embed"""
        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = (
            "**Channel Mirror** (Server Owner Only)\n\n"
            "Forward messages from one channel to another,\n"
            "even across different servers!\n\n"
            "**Setup Mirror**\n"
            "› `mirror add #source <dest_id>` − Create mirror\n"
            "› `mirror remove #source` − Remove all mirrors\n"
            "› `mirror remove #source <dest_id>` − Remove specific\n\n"
            "**Copy History**\n"
            "› `mirror copy #source <dest_id> [amount]` − Copy messages\n"
            "› Copies up to 100 messages at once\n\n"
            "**View & Test**\n"
            "› `mirror` − View all active mirrors\n"
            "› `mirror test <channel_id>` − Test connection\n\n"
            "**How to Get Channel ID:**\n"
            "› Enable Developer Mode in Discord settings\n"
            "› Right-click channel → Copy ID\n\n"
            "**Example:**\n"
            "› `!mirror add #announcements 123456789`\n"
            "› Messages in #announcements will forward\n"
            "› to channel 123456789 in another server"
        )
        return embed

    @commands.hybrid_command(name="help", aliases=["h", "cmds", "commands"])
    async def help_command(self, ctx: commands.Context, *, category: Optional[str] = None):
        """Show help menu"""
        if category:
            cat = category.lower().strip()

            if cat in ["antinuke", "anti-nuke", "nuke", "an", "protection", "security"]:
                embed = self.get_antinuke_embed()
            elif cat in ["mod", "moderation", "moderate", "admin", "mods"]:
                embed = self.get_mod_embed()
            elif cat in ["whitelist", "wl", "trust", "trusted", "white"]:
                embed = self.get_whitelist_embed()
            elif cat in ["raid", "antiraid", "anti-raid", "vpn", "bansync", "raids"]:
                embed = self.get_raid_embed()
            elif cat in ["spam", "antispam", "anti-spam", "as"]:
                embed = self.get_spam_embed()
            elif cat in ["lockdown", "ld", "lock", "emergency"]:
                embed = self.get_lockdown_embed()
            elif cat in ["utility", "util", "info", "general", "core", "backup", "utils"]:
                embed = self.get_utility_embed()
            elif cat in ["owner", "admin", "botadmin", "bot", "status", "servers"]:
                embed = self.get_owner_embed()
            elif cat in ["mirror", "forward", "copy", "sync", "crossserver"]:
                embed = self.get_mirror_embed()
            else:
                embed = self.get_main_embed()
        else:
            embed = self.get_main_embed()

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="test", aliases=["t"])
    async def test_cmd(self, ctx: commands.Context):
        """Test command"""
        embed = discord.Embed(description="+ Bot is working", color=EMBED_COLOR)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Help(bot))
