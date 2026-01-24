"""
Comprehensive Help Command - All Commands with Slash Support
=============================================================
Shows all commands, permissions, and features
"""
import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
import logging

logger = logging.getLogger('Offcialx.Help')

EMBED_COLOR = 0x2b2d31


class Help(commands.Cog):
    """Help Command System"""

    def __init__(self, bot):
        self.bot = bot
        self.bot.help_command = None

    def get_main_embed(self) -> discord.Embed:
        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = (
            "**Offcialx Security Bot**\n\n"
            "All commands work with `/command` or `!command`\n\n"
            "**Categories**\n"
            "› `/help antinuke` − Anti-nuke protection\n"
            "› `/help whitelist` − Trust management\n"
            "› `/help backup` − Server backups\n"
            "› `/help mod` − Moderation tools\n"
            "› `/help antiraid` − Raid protection\n"
            "› `/help antispam` − Spam protection\n"
            "› `/help lockdown` − Server lockdown\n"
            "› `/help mirror` − Message forwarding\n"
            "› `/help utility` − General commands\n"
            "› `/help owner` − Bot owner only\n\n"
            "**Permission Levels**\n"
            "👑 Server Owner − Full access\n"
            "🛡️ Admin − Most commands\n"
            "🔧 Mod − Basic moderation\n"
            "🤖 Bot Owner − Bot management"
        )
        return embed

    def get_antinuke_embed(self) -> discord.Embed:
        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = (
            "**Anti-Nuke Protection** 👑 Server Owner\n\n"
            "Protects against server destruction attacks.\n"
            "Instant punishment on first unauthorized action.\n\n"
            "**Status & Config**\n"
            "› `/antinuke` − View protection status\n"
            "› `/antinuke_enable` − Enable protection\n"
            "› `/antinuke_disable` − Disable protection\n"
            "› `/setlog #channel` − Set security log\n"
            "› `/punishment ban|kick` − Set punishment type\n"
            "› `/attackstats` − View blocked attacks\n\n"
            "**Emergency Controls**\n"
            "› `/serverlock [seconds]` − Lock all channels\n"
            "› `/serverunlock` − Unlock all channels\n"
            "› `/lockdownstatus` − View lockdown status\n"
            "› `/nukewebhooks` − Delete all webhooks\n\n"
            "**Channel Recovery**\n"
            "› `/restore` − View deleted channels\n"
            "› `/restore_channel <num>` − Restore a channel\n"
            "› `/restore_clear` − Clear restore list\n\n"
            "**Protection Includes**\n"
            "• Channel create/delete/rename\n"
            "• Role create/delete/modify\n"
            "• Webhook spam blocking\n"
            "• Mass ban/kick detection\n"
            "• Bot addition blocking\n"
            "• Permission escalation\n"
            "• Server settings changes"
        )
        return embed

    def get_whitelist_embed(self) -> discord.Embed:
        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = (
            "**Unified Whitelist** 👑 Server Owner\n\n"
            "Whitelisted entries bypass:\n"
            "• All anti-nuke protection\n"
            "• Cannot be punished by bot\n"
            "• Can send during lockdown\n\n"
            "**Add to Whitelist**\n"
            "› `/wlist user @user` − Whitelist user\n"
            "› `/wlist role @role` − Whitelist role\n"
            "› `/wlist bot @bot` − Whitelist bot\n\n"
            "**Remove from Whitelist**\n"
            "› `/wlist remove user @user`\n"
            "› `/wlist remove role @role`\n"
            "› `/wlist remove bot @bot`\n\n"
            "**View Whitelist**\n"
            "› `/wlist` − View all whitelisted\n"
            "› `/wlist users` − View users only\n"
            "› `/wlist roles` − View roles only\n"
            "› `/wlist bots` − View bots only\n\n"
            "**Clear Whitelist**\n"
            "› `/wlist clear` − Clear everything\n"
            "› `/wlist clear users|roles|bots`\n\n"
            "**Note:** All data persists in database"
        )
        return embed

    def get_backup_embed(self) -> discord.Embed:
        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = (
            "**Server Backup** 👑 Server Owner\n\n"
            "Full server backup and restore system.\n\n"
            "**Backup Commands**\n"
            "› `/backup` − View all backups\n"
            "› `/backup create` − Create new backup\n"
            "› `/backup list` − List all backups\n"
            "› `/backup info [version]` − Backup details\n"
            "› `/backup restore [version]` − Restore backup\n"
            "› `/backup delete <version>` − Delete backup\n"
            "› `/backup clear` − Delete all backups\n\n"
            "**Settings**\n"
            "› `/backup auto` − Toggle auto-backup\n"
            "› `/backup setlog #channel` − Set log\n"
            "› `/backup settings` − View settings\n\n"
            "**What Gets Backed Up**\n"
            "• Server name, icon, banner\n"
            "• All roles with permissions\n"
            "• All channels with permissions\n"
            "• Categories and positions\n"
            "• Channel topics, slowmode, NSFW\n\n"
            "**Limits:** Max 5 backups per server"
        )
        return embed

    def get_mod_embed(self) -> discord.Embed:
        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = (
            "**Moderation** 🛡️ Admin / 🔧 Mod\n\n"
            "**Member Actions** 🛡️\n"
            "› `/ban @user [reason]` − Ban member\n"
            "› `/kick @user [reason]` − Kick member\n"
            "› `/mute @user [duration]` − Timeout\n"
            "› `/unmute @user` − Remove timeout\n\n"
            "**Role Management** 🛡️\n"
            "› `/role @user @role` − Toggle role\n"
            "› `/addrole @user @role` − Add role\n"
            "› `/removerole @user @role` − Remove role\n\n"
            "**Channel Management** 🔧\n"
            "› `/purge [amount]` − Delete messages\n"
            "› `/purge @user [amount]` − User msgs\n"
            "› `/slowmode [seconds]` − Set slowmode\n"
            "› `/lock` − Lock channel\n"
            "› `/unlock` − Unlock channel\n\n"
            "**Other** 🛡️\n"
            "› `/nick @user [name]` − Set nickname\n"
            "› `/warn @user [reason]` − Warn user"
        )
        return embed

    def get_antiraid_embed(self) -> discord.Embed:
        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = (
            "**Anti-Raid** 👑 Server Owner\n\n"
            "Protection against mass join attacks.\n\n"
            "**Status & Config**\n"
            "› `/antiraid` − View status\n"
            "› `/antiraid enable` − Enable\n"
            "› `/antiraid disable` − Disable\n"
            "› `/antiraid action kick|ban` − Set action\n"
            "› `/antiraid setlog #channel` − Set log\n\n"
            "**VPN Detection**\n"
            "› `/vpn` − View VPN status\n"
            "› `/vpn enable` − Enable detection\n"
            "› `/vpn disable` − Disable detection\n"
            "› `/vpn action kick|ban` − Set action\n\n"
            "**Ban Sync Network**\n"
            "› `/bansync` − View network\n"
            "› `/bansync create` − Create network\n"
            "› `/bansync join <code>` − Join network\n"
            "› `/bansync list` − List servers\n\n"
            "**Detection Includes**\n"
            "• Mass join detection\n"
            "• New account filtering\n"
            "• VPN/Proxy blocking\n"
            "• Cross-server ban sync"
        )
        return embed

    def get_antispam_embed(self) -> discord.Embed:
        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = (
            "**Anti-Spam** 👑 Server Owner\n\n"
            "Protection against message spam.\n\n"
            "**Status & Config**\n"
            "› `/antispam` − View status\n"
            "› `/antispam enable` − Enable\n"
            "› `/antispam disable` − Disable\n"
            "› `/antispam action warn|mute|kick|ban`\n"
            "› `/antispam setlog #channel` − Set log\n\n"
            "**Link Filtering**\n"
            "› `/antispam links true|false`\n"
            "› `/antispam invites true|false`\n"
            "› `/antispam phishing true|false`\n\n"
            "**Exemptions**\n"
            "› `/antispam exempt @role`\n"
            "› `/antispam unexempt @role`\n\n"
            "**Anti-Selfbot** 👑\n"
            "› `/antiselfbot` − View status\n"
            "› `/antiselfbot enable|disable`\n"
            "› `/antiselfbot action`\n\n"
            "**Detection Includes**\n"
            "• Message flood\n"
            "• Duplicate messages\n"
            "• Mention spam\n"
            "• Invite links\n"
            "• Phishing links"
        )
        return embed

    def get_lockdown_embed(self) -> discord.Embed:
        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = (
            "**Lockdown** 👑 Server Owner / 🛡️ Admin\n\n"
            "Emergency server lockdown controls.\n\n"
            "**Server Lockdown** 👑\n"
            "› `/serverlock [seconds]` − Lock server\n"
            "› `/serverunlock` − Unlock server\n"
            "› `/lockdownstatus` − View status\n\n"
            "**Channel Lock** 🛡️\n"
            "› `/lock` − Lock current channel\n"
            "› `/unlock` − Unlock current channel\n\n"
            "**Features**\n"
            "• Backs up original permissions\n"
            "• Restores permissions on unlock\n"
            "• Whitelisted users can still send\n"
            "• Admins/Mods bypass lockdown\n"
            "• Auto-unlock after duration"
        )
        return embed

    def get_mirror_embed(self) -> discord.Embed:
        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = (
            "**Channel Mirror** 👑 Server Owner\n\n"
            "Forward messages between channels/servers.\n\n"
            "**Setup Mirror**\n"
            "› `/mirror` − View active mirrors\n"
            "› `/mirror add #source <dest_id>`\n"
            "› `/mirror remove #source [dest_id]`\n"
            "› `/mirror test <channel_id>`\n\n"
            "**Copy History**\n"
            "› `/mirror copy #src <dest> 50`\n"
            "› `/mirror copy #src <dest> all`\n"
            "› `/mirror cancel` − Stop copying\n\n"
            "**Features**\n"
            "• Cross-server forwarding\n"
            "• File/image links preserved\n"
            "• Rate limit protected\n"
            "• Database persistent\n"
            "• Queue system (one at a time)\n\n"
            "**Get Channel ID**\n"
            "Enable Developer Mode → Right-click → Copy ID"
        )
        return embed

    def get_utility_embed(self) -> discord.Embed:
        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = (
            "**Utility Commands** 👤 Everyone\n\n"
            "**Information**\n"
            "› `/help [category]` − This menu\n"
            "› `/ping` − Bot latency\n"
            "› `/info` − Bot information\n"
            "› `/botstats` − Bot statistics\n\n"
            "**User Info**\n"
            "› `/userinfo [@user]` − User details\n"
            "› `/avatar [@user]` − User avatar\n"
            "› `/banner [@user]` − User banner\n\n"
            "**Server Info**\n"
            "› `/serverinfo` − Server details\n"
            "› `/servericon` − Server icon\n"
            "› `/serverbanner` − Server banner\n\n"
            "**Setup** 👑\n"
            "› `/setup` − Setup wizard\n"
            "› `/setlog #channel` − Set log\n\n"
            "**Links**\n"
            "› `/invite` − Invite bot\n"
            "› `/support` − Support server"
        )
        return embed

    def get_owner_embed(self) -> discord.Embed:
        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = (
            "**Bot Owner Commands** 🤖\n\n"
            "Only bot owners can use these.\n\n"
            "**Bot Status**\n"
            "› `/botstatus` − View status\n"
            "› `/botstatus watching <text>`\n"
            "› `/botstatus playing <text>`\n"
            "› `/botstatus listening <text>`\n"
            "› `/botstatus streaming <url> <text>`\n"
            "› `/botstatus online|idle|dnd|invisible`\n"
            "› `/botstatus clear` − Remove activity\n\n"
            "**Server Management**\n"
            "› `/servers` − Server count\n"
            "› `/serverlist` − All servers\n"
            "› `/leaveserver <id>` − Leave server\n\n"
            "**Logging**\n"
            "› `/setjoinlog #channel` − Join/leave log\n\n"
            "**Sync**\n"
            "› `/sync` − Sync global commands\n"
            "› `/syncguild` − Sync to this server\n\n"
            "**Info**\n"
            "› `/ownerinfo` − Bot stats & uptime"
        )
        return embed

    @commands.hybrid_command(name="help", aliases=["h", "commands"])
    @app_commands.describe(category="Command category to view")
    async def help_command(self, ctx: commands.Context, *, category: Optional[str] = None):
        """Show help menu with all commands"""
        if category:
            cat = category.lower().strip()
            embeds = {
                "antinuke": self.get_antinuke_embed,
                "anti-nuke": self.get_antinuke_embed,
                "nuke": self.get_antinuke_embed,
                "protection": self.get_antinuke_embed,
                "whitelist": self.get_whitelist_embed,
                "wlist": self.get_whitelist_embed,
                "trust": self.get_whitelist_embed,
                "backup": self.get_backup_embed,
                "backups": self.get_backup_embed,
                "restore": self.get_backup_embed,
                "mod": self.get_mod_embed,
                "moderation": self.get_mod_embed,
                "admin": self.get_mod_embed,
                "antiraid": self.get_antiraid_embed,
                "raid": self.get_antiraid_embed,
                "vpn": self.get_antiraid_embed,
                "antispam": self.get_antispam_embed,
                "spam": self.get_antispam_embed,
                "lockdown": self.get_lockdown_embed,
                "lock": self.get_lockdown_embed,
                "mirror": self.get_mirror_embed,
                "forward": self.get_mirror_embed,
                "copy": self.get_mirror_embed,
                "utility": self.get_utility_embed,
                "util": self.get_utility_embed,
                "info": self.get_utility_embed,
                "owner": self.get_owner_embed,
                "bot": self.get_owner_embed,
            }
            embed_func = embeds.get(cat, self.get_main_embed)
            embed = embed_func()
        else:
            embed = self.get_main_embed()

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="commands", aliases=["cmds"])
    async def commands_list(self, ctx: commands.Context):
        """Quick command reference"""
        embed = discord.Embed(color=EMBED_COLOR)
        embed.description = (
            "**Quick Command Reference**\n\n"
            "**Security** 👑\n"
            "`/antinuke` `/wlist` `/backup` `/serverlock`\n\n"
            "**Moderation** 🛡️\n"
            "`/ban` `/kick` `/mute` `/purge` `/role`\n\n"
            "**Protection** 👑\n"
            "`/antiraid` `/antispam` `/antiselfbot`\n\n"
            "**Utility** 👤\n"
            "`/help` `/ping` `/userinfo` `/serverinfo`\n\n"
            "Use `/help <category>` for details"
        )
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Help(bot))
