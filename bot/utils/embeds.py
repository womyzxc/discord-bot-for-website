"""
Embed Utilities
===============
Beautiful, consistent embed styling for all bot responses.
Professional military-grade aesthetic with modern design.
Integrates with the theme system for per-server customization.
"""

import discord
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple


class EmbedStyle:
    """Color and style constants for embeds"""

    # Primary colors (defaults - will be overridden by themes)
    PRIMARY = 0x9B59B6       # Purple (main brand)
    SECONDARY = 0x8E44AD    # Dark purple
    ACCENT = 0xE91E63       # Pink accent

    # Status colors
    SUCCESS = 0x2ECC71      # Green
    WARNING = 0xF39C12      # Orange
    ERROR = 0xE74C3C        # Red
    INFO = 0x3498DB         # Blue

    # Security colors
    CRITICAL = 0xFF0000     # Bright red
    HIGH = 0xFF6600         # Orange
    MEDIUM = 0xFFCC00       # Yellow
    LOW = 0x00FF00          # Green
    SAFE = 0x00CCFF         # Cyan

    # Special colors
    GOLD = 0xFFD700         # Premium/VIP
    RAINBOW = [0xFF0000, 0xFF7F00, 0xFFFF00, 0x00FF00, 0x0000FF, 0x4B0082, 0x9400D3]

    # Brand
    BRAND_NAME = "Offcialx"
    BRAND_ICON = "https://i.imgur.com/YourIcon.png"  # Replace with actual icon
    VERSION = "3.5.1"
    WEBSITE = "https://offcialx.xyz"
    SUPPORT = "https://discord.gg/NXK5sFEJSy"


def get_themed_color(bot, guild_id: int, color_type: str = "primary") -> int:
    """
    Get a color from the guild's theme.
    Falls back to defaults if theme cog not loaded.

    Args:
        bot: The bot instance
        guild_id: The guild ID to get theme for
        color_type: Type of color (primary, success, error, warning, info, security)

    Returns:
        int: The color as an integer
    """
    try:
        themes_cog = bot.get_cog('Themes')
        if themes_cog:
            return themes_cog.get_color(guild_id, color_type)
    except Exception:
        pass

    # Fallback to defaults
    defaults = {
        "primary": EmbedStyle.PRIMARY,
        "secondary": EmbedStyle.SECONDARY,
        "success": EmbedStyle.SUCCESS,
        "warning": EmbedStyle.WARNING,
        "error": EmbedStyle.ERROR,
        "info": EmbedStyle.INFO,
        "security": EmbedStyle.ERROR,
    }
    return defaults.get(color_type, EmbedStyle.PRIMARY)


def get_guild_theme(bot, guild_id: int) -> Dict[str, Any]:
    """
    Get the full theme data for a guild.

    Args:
        bot: The bot instance
        guild_id: The guild ID

    Returns:
        Dict with theme data
    """
    try:
        themes_cog = bot.get_cog('Themes')
        if themes_cog:
            return themes_cog.get_guild_theme(guild_id)
    except Exception:
        pass

    # Return default theme
    return {
        "name": "Default",
        "description": "Classic Offcialx purple theme",
        "emoji": "💜",
        "primary": 0x9B59B6,
        "secondary": 0x8E44AD,
        "success": 0x2ECC71,
        "warning": 0xF39C12,
        "error": 0xE74C3C,
        "info": 0x3498DB,
        "security": 0xE74C3C,
    }


class EmbedBuilder:
    """Build beautiful embeds with consistent styling"""

    @staticmethod
    def create_base(
        title: str = None,
        description: str = None,
        color: int = EmbedStyle.PRIMARY,
        thumbnail: str = None,
        image: str = None,
        author_name: str = None,
        author_icon: str = None,
        footer_text: str = None,
        timestamp: bool = True
    ) -> discord.Embed:
        """Create a base embed with common styling"""

        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.utcnow() if timestamp else None
        )

        if thumbnail:
            embed.set_thumbnail(url=thumbnail)

        if image:
            embed.set_image(url=image)

        if author_name:
            embed.set_author(name=author_name, icon_url=author_icon)

        if footer_text:
            embed.set_footer(text=footer_text)
        else:
            embed.set_footer(text=f"{EmbedStyle.BRAND_NAME} Security v{EmbedStyle.VERSION}")

        return embed

    @staticmethod
    def themed(
        bot,
        guild_id: int,
        title: str = None,
        description: str = None,
        color_type: str = "primary",
        **kwargs
    ) -> discord.Embed:
        """Create a themed embed using the guild's color scheme"""
        color = get_themed_color(bot, guild_id, color_type)
        return EmbedBuilder.create_base(
            title=title,
            description=description,
            color=color,
            **kwargs
        )

    @staticmethod
    def success(
        title: str = "Success",
        description: str = None,
        bot=None,
        guild_id: int = None,
        **kwargs
    ) -> discord.Embed:
        """Create a success embed"""
        if bot and guild_id:
            color = get_themed_color(bot, guild_id, "success")
        else:
            color = EmbedStyle.SUCCESS

        return EmbedBuilder.create_base(
            title=f"✅ {title}" if not title.startswith(("✅", "<")) else title,
            description=description,
            color=color,
            **kwargs
        )

    @staticmethod
    def error(
        title: str = "Error",
        description: str = None,
        bot=None,
        guild_id: int = None,
        **kwargs
    ) -> discord.Embed:
        """Create an error embed"""
        if bot and guild_id:
            color = get_themed_color(bot, guild_id, "error")
        else:
            color = EmbedStyle.ERROR

        return EmbedBuilder.create_base(
            title=f"❌ {title}" if not title.startswith(("❌", "<")) else title,
            description=description,
            color=color,
            **kwargs
        )

    @staticmethod
    def warning(
        title: str = "Warning",
        description: str = None,
        bot=None,
        guild_id: int = None,
        **kwargs
    ) -> discord.Embed:
        """Create a warning embed"""
        if bot and guild_id:
            color = get_themed_color(bot, guild_id, "warning")
        else:
            color = EmbedStyle.WARNING

        return EmbedBuilder.create_base(
            title=f"⚠️ {title}" if not title.startswith(("⚠️", "<")) else title,
            description=description,
            color=color,
            **kwargs
        )

    @staticmethod
    def info(
        title: str = "Information",
        description: str = None,
        bot=None,
        guild_id: int = None,
        **kwargs
    ) -> discord.Embed:
        """Create an info embed"""
        if bot and guild_id:
            color = get_themed_color(bot, guild_id, "info")
        else:
            color = EmbedStyle.INFO

        return EmbedBuilder.create_base(
            title=f"ℹ️ {title}" if not title.startswith(("ℹ️", "<")) else title,
            description=description,
            color=color,
            **kwargs
        )

    @staticmethod
    def security_alert(
        title: str,
        description: str,
        severity: str = "high",
        threat_type: str = None,
        attacker: discord.Member = None,
        action_taken: str = None,
        guild: discord.Guild = None,
        bot=None,
        **kwargs
    ) -> discord.Embed:
        """Create a security alert embed"""

        colors = {
            'critical': EmbedStyle.CRITICAL,
            'high': EmbedStyle.HIGH,
            'medium': EmbedStyle.MEDIUM,
            'low': EmbedStyle.LOW,
            'safe': EmbedStyle.SAFE
        }

        severity_icons = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🟢',
            'safe': '🔵'
        }

        # Use themed security color if available
        if bot and guild:
            color = get_themed_color(bot, guild.id, "security")
        else:
            color = colors.get(severity, EmbedStyle.HIGH)

        embed = EmbedBuilder.create_base(
            title=f"{severity_icons.get(severity, '🟠')} {title}",
            description=description,
            color=color,
            **kwargs
        )

        if threat_type:
            embed.add_field(name="🎯 Threat Type", value=f"`{threat_type}`", inline=True)

        if severity:
            embed.add_field(name="⚠️ Severity", value=f"`{severity.upper()}`", inline=True)

        if attacker:
            embed.add_field(
                name="👤 Attacker",
                value=f"{attacker.mention}\n`{attacker.id}`",
                inline=True
            )

        if action_taken:
            embed.add_field(name="⚡ Action Taken", value=f"`{action_taken}`", inline=True)

        if guild:
            embed.add_field(name="🏠 Server", value=f"{guild.name}", inline=True)

        return embed


class HelpEmbed:
    """Beautiful help embed builder"""

    # Category configurations with icons and colors
    CATEGORIES = {
        'antinuke': {
            'icon': '🛡️',
            'title': 'Anti-Nuke Protection',
            'color_type': 'error',  # Use themed error color (red-ish)
            'description': 'Military-grade protection against server destruction',
            'banner': '```ansi\n\u001b[1;31m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n       ANTI-NUKE PROTECTION SYSTEM\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\u001b[0m```',
        },
        'antiraid': {
            'icon': '🚨',
            'title': 'Anti-Raid Protection',
            'color_type': 'warning',  # Use themed warning color (orange-ish)
            'description': 'Advanced protection against coordinated mass joins',
            'banner': '```ansi\n\u001b[1;33m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n       ANTI-RAID DEFENSE SYSTEM\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\u001b[0m```',
        },
        'security': {
            'icon': '🔐',
            'title': 'Advanced Security',
            'color_type': 'primary',  # Use themed primary color
            'description': 'Behavioral analysis, honeypots, and threat detection',
            'banner': '```ansi\n\u001b[1;35m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n       ADVANCED SECURITY SUITE\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\u001b[0m```',
        },
        'moderation': {
            'icon': '🔨',
            'title': 'Moderation Tools',
            'color_type': 'info',  # Use themed info color (blue-ish)
            'description': 'Powerful moderation commands for server management',
            'banner': '```ansi\n\u001b[1;34m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n       MODERATION TOOLKIT\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\u001b[0m```',
        },
        'utility': {
            'icon': '⚙️',
            'title': 'Utility & Settings',
            'color_type': 'success',  # Use themed success color (green-ish)
            'description': 'Bot configuration, backups, and utility commands',
            'banner': '```ansi\n\u001b[1;32m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n       UTILITY & CONFIGURATION\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\u001b[0m```',
        },
        'themes': {
            'icon': '🎨',
            'title': 'Theme Customization',
            'color_type': 'primary',
            'description': 'Customize the bot appearance with themes',
            'banner': '```ansi\n\u001b[1;35m━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n       THEME CUSTOMIZATION\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\u001b[0m```',
        },
    }

    @staticmethod
    def create_main_help(bot, guild_id: int = None) -> discord.Embed:
        """Create the main help menu embed with themed colors"""

        # Calculate stats
        total_servers = len(bot.guilds)
        total_users = sum(g.member_count or 0 for g in bot.guilds)

        # Get themed color
        if guild_id:
            color = get_themed_color(bot, guild_id, "primary")
            theme = get_guild_theme(bot, guild_id)
            theme_name = theme.get("name", "Default")
        else:
            color = EmbedStyle.PRIMARY
            theme_name = "Default"

        embed = discord.Embed(
            title="",
            description="",
            color=color,
            timestamp=datetime.utcnow()
        )

        # Header with ASCII art style
        header = """```ansi
\u001b[1;35m╔═══════════════════════════════════════════════════════════╗
║                                                             ║
║   ██████╗ ███████╗███████╗ ██████╗██╗ █████╗ ██╗     ██╗  ██╗║
║  ██╔═══██╗██╔════╝██╔════╝██╔════╝██║██╔══██╗██║     ╚██╗██╔╝║
║  ██║   ██║█████╗  █████╗  ██║     ██║███████║██║      ╚███╔╝ ║
║  ██║   ██║██╔══╝  ██╔══╝  ██║     ██║██╔══██║██║      ██╔██╗ ║
║  ╚██████╔╝██║     ██║     ╚██████╗██║██║  ██║███████╗██╔╝ ██╗║
║   ╚═════╝ ╚═╝     ╚═╝      ╚═════╝╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝║
║                                                             ║
║           ⚡ MILITARY-GRADE SERVER PROTECTION ⚡           ║
╚═══════════════════════════════════════════════════════════╝\u001b[0m
```"""

        embed.description = header + "\n**Select a category below to view commands:**"

        # Categories grid
        categories_text = """
╭─────────────────────────────────────────────────────────────╮
│                                                             │
│  🛡️ **Anti-Nuke**          │  🚨 **Anti-Raid**             │
│  `!help antinuke`          │  `!help antiraid`             │
│  Server destruction guard  │  Mass join protection         │
│                                                             │
│  🔐 **Security**           │  🔨 **Moderation**            │
│  `!help security`          │  `!help mod`                  │
│  Advanced threat detect    │  Server management tools      │
│                                                             │
│  ⚙️ **Utility**            │  🎨 **Themes**                │
│  `!help utility`           │  `!theme`                     │
│  Configuration & backups   │  Customize bot colors         │
│                                                             │
╰─────────────────────────────────────────────────────────────╯
"""

        embed.add_field(
            name="📚 Command Categories",
            value=categories_text,
            inline=False
        )

        # Quick actions
        quick_actions = """
> 🚀 `!setup` - Quick setup wizard
> 📋 `!antinuke` - View protection status
> 🎨 `!theme` - Customize colors
> 🔗 `!invite` - Add bot to server
"""

        embed.add_field(
            name="⚡ Quick Actions",
            value=quick_actions,
            inline=False
        )

        # Stats bar
        stats_bar = f"```\n🌐 {total_servers:,} Servers  │  👥 {total_users:,} Users  │  🛡️ 27 Protections  │  🎨 Theme: {theme_name}\n```"

        embed.add_field(
            name="📈 Live Statistics",
            value=stats_bar,
            inline=False
        )

        # Footer with links
        embed.set_footer(
            text=f"Offcialx v{EmbedStyle.VERSION} │ !help <category> for details │ Prefix: !",
            icon_url=bot.user.display_avatar.url if bot.user else None
        )

        return embed

    @staticmethod
    def create_category_help(
        category: str,
        commands_data: List[Tuple[str, str, str]],
        bot=None,
        guild_id: int = None
    ) -> discord.Embed:
        """Create a category-specific help embed

        Args:
            category: Category key
            commands_data: List of (command, description, example) tuples
            bot: Bot instance for theming
            guild_id: Guild ID for theming
        """

        cat_config = HelpEmbed.CATEGORIES.get(category, {
            'icon': '📖',
            'title': category.title(),
            'color_type': 'primary',
            'description': 'Command list',
            'banner': ''
        })

        # Get themed color
        if bot and guild_id:
            color = get_themed_color(bot, guild_id, cat_config.get('color_type', 'primary'))
        else:
            color = EmbedStyle.PRIMARY

        embed = discord.Embed(
            title="",
            description=cat_config.get('banner', ''),
            color=color,
            timestamp=datetime.utcnow()
        )

        # Category header
        embed.add_field(
            name=f"{cat_config['icon']} {cat_config['title']}",
            value=f"*{cat_config['description']}*\n\u200b",
            inline=False
        )

        # Commands list with formatting
        for cmd, desc, example in commands_data:
            # Format command with styling
            cmd_formatted = f"```\n{cmd}\n```"
            value = f"{desc}\n> **Example:** `{example}`" if example else desc

            embed.add_field(
                name=cmd_formatted,
                value=value,
                inline=False
            )

        # Navigation footer
        embed.add_field(
            name="\u200b",
            value="```\n<required>  [optional]  │  Use !help for main menu\n```",
            inline=False
        )

        embed.set_footer(text=f"Offcialx v{EmbedStyle.VERSION} │ {cat_config['title']}")

        return embed


# Convenience functions for quick embeds with theme support
def success_embed(title: str, description: str = None, bot=None, guild_id: int = None) -> discord.Embed:
    """Quick success embed"""
    if bot and guild_id:
        color = get_themed_color(bot, guild_id, "success")
    else:
        color = EmbedStyle.SUCCESS

    return discord.Embed(
        title=f"✅ {title}",
        description=description,
        color=color,
        timestamp=datetime.utcnow()
    ).set_footer(text=f"{EmbedStyle.BRAND_NAME} v{EmbedStyle.VERSION}")


def error_embed(title: str, description: str = None, bot=None, guild_id: int = None) -> discord.Embed:
    """Quick error embed"""
    if bot and guild_id:
        color = get_themed_color(bot, guild_id, "error")
    else:
        color = EmbedStyle.ERROR

    return discord.Embed(
        title=f"❌ {title}",
        description=description,
        color=color,
        timestamp=datetime.utcnow()
    ).set_footer(text=f"{EmbedStyle.BRAND_NAME} v{EmbedStyle.VERSION}")


def warning_embed(title: str, description: str = None, bot=None, guild_id: int = None) -> discord.Embed:
    """Quick warning embed"""
    if bot and guild_id:
        color = get_themed_color(bot, guild_id, "warning")
    else:
        color = EmbedStyle.WARNING

    return discord.Embed(
        title=f"⚠️ {title}",
        description=description,
        color=color,
        timestamp=datetime.utcnow()
    ).set_footer(text=f"{EmbedStyle.BRAND_NAME} v{EmbedStyle.VERSION}")


def info_embed(title: str, description: str = None, bot=None, guild_id: int = None) -> discord.Embed:
    """Quick info embed"""
    if bot and guild_id:
        color = get_themed_color(bot, guild_id, "info")
    else:
        color = EmbedStyle.INFO

    return discord.Embed(
        title=f"ℹ️ {title}",
        description=description,
        color=color,
        timestamp=datetime.utcnow()
    ).set_footer(text=f"{EmbedStyle.BRAND_NAME} v{EmbedStyle.VERSION}")


def loading_embed(title: str = "Processing...", description: str = None, bot=None, guild_id: int = None) -> discord.Embed:
    """Quick loading embed"""
    if bot and guild_id:
        color = get_themed_color(bot, guild_id, "info")
    else:
        color = EmbedStyle.INFO

    return discord.Embed(
        title=f"⏳ {title}",
        description=description or "Please wait...",
        color=color,
        timestamp=datetime.utcnow()
    ).set_footer(text=f"{EmbedStyle.BRAND_NAME} v{EmbedStyle.VERSION}")


def themed_embed(bot, guild_id: int, title: str = None, description: str = None, color_type: str = "primary") -> discord.Embed:
    """Create a themed embed quickly"""
    return discord.Embed(
        title=title,
        description=description,
        color=get_themed_color(bot, guild_id, color_type),
        timestamp=datetime.utcnow()
    ).set_footer(text=f"{EmbedStyle.BRAND_NAME} v{EmbedStyle.VERSION}")
