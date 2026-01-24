"""
Themes & Customization Cog
==========================
Allow servers to customize the bot's embed colors and styling.
Includes preset themes and custom color options.
"""

import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
from typing import Literal, Optional, Dict, Any
import logging
import json
import os

logger = logging.getLogger('Offcialx.Themes')

# Minimal embed color (default)
EMBED_COLOR = 0x2b2d31

PRESET_THEMES = {
    "default": {
        "name": "Default",
        "description": "Classic Offcialx purple theme",
        "emoji": "💜",
        "primary": 0x9B59B6,      # Purple
        "secondary": 0x8E44AD,    # Dark purple
        "success": 0x2ECC71,      # Green
        "warning": 0xF39C12,      # Orange
        "error": 0xE74C3C,        # Red
        "info": 0x3498DB,         # Blue
        "security": 0xE74C3C,     # Red (for security alerts)
    },
    "midnight": {
        "name": "Midnight",
        "description": "Dark blue cyberpunk theme",
        "emoji": "🌙",
        "primary": 0x2C3E50,      # Dark blue
        "secondary": 0x34495E,    # Slate
        "success": 0x1ABC9C,      # Teal
        "warning": 0xF39C12,      # Orange
        "error": 0xE74C3C,        # Red
        "info": 0x3498DB,         # Blue
        "security": 0xE74C3C,
    },
    "crimson": {
        "name": "Crimson",
        "description": "Bold red security theme",
        "emoji": "🔴",
        "primary": 0xC0392B,      # Crimson
        "secondary": 0xE74C3C,    # Red
        "success": 0x27AE60,      # Green
        "warning": 0xF39C12,      # Orange
        "error": 0x922B21,        # Dark red
        "info": 0xE74C3C,         # Red
        "security": 0x922B21,
    },
    "emerald": {
        "name": "Emerald",
        "description": "Fresh green nature theme",
        "emoji": "💚",
        "primary": 0x27AE60,      # Emerald
        "secondary": 0x2ECC71,    # Green
        "success": 0x2ECC71,      # Green
        "warning": 0xF1C40F,      # Yellow
        "error": 0xE74C3C,        # Red
        "info": 0x3498DB,         # Blue
        "security": 0xE74C3C,
    },
    "ocean": {
        "name": "Ocean",
        "description": "Cool blue ocean theme",
        "emoji": "🌊",
        "primary": 0x2980B9,      # Ocean blue
        "secondary": 0x3498DB,    # Blue
        "success": 0x1ABC9C,      # Teal
        "warning": 0xF39C12,      # Orange
        "error": 0xE74C3C,        # Red
        "info": 0x3498DB,         # Blue
        "security": 0xE74C3C,
    },
    "sunset": {
        "name": "Sunset",
        "description": "Warm orange sunset theme",
        "emoji": "🌅",
        "primary": 0xE67E22,      # Orange
        "secondary": 0xD35400,    # Dark orange
        "success": 0x2ECC71,      # Green
        "warning": 0xF1C40F,      # Yellow
        "error": 0xC0392B,        # Red
        "info": 0xE67E22,         # Orange
        "security": 0xC0392B,
    },
    "gold": {
        "name": "Gold",
        "description": "Premium golden theme",
        "emoji": "✨",
        "primary": 0xF1C40F,      # Gold
        "secondary": 0xF39C12,    # Dark gold
        "success": 0x2ECC71,      # Green
        "warning": 0xE67E22,      # Orange
        "error": 0xE74C3C,        # Red
        "info": 0xF1C40F,         # Gold
        "security": 0xE74C3C,
    },
    "neon": {
        "name": "Neon",
        "description": "Vibrant neon cyberpunk theme",
        "emoji": "💫",
        "primary": 0xFF00FF,      # Magenta
        "secondary": 0x00FFFF,    # Cyan
        "success": 0x00FF00,      # Neon green
        "warning": 0xFFFF00,      # Yellow
        "error": 0xFF0000,        # Red
        "info": 0x00FFFF,         # Cyan
        "security": 0xFF0000,
    },
    "rose": {
        "name": "Rose",
        "description": "Elegant rose pink theme",
        "emoji": "🌹",
        "primary": 0xE91E63,      # Pink
        "secondary": 0xC2185B,    # Dark pink
        "success": 0x4CAF50,      # Green
        "warning": 0xFF9800,      # Orange
        "error": 0xF44336,        # Red
        "info": 0xE91E63,         # Pink
        "security": 0xF44336,
    },
    "arctic": {
        "name": "Arctic",
        "description": "Cool ice blue theme",
        "emoji": "❄️",
        "primary": 0x00BCD4,      # Cyan
        "secondary": 0x0097A7,    # Dark cyan
        "success": 0x4CAF50,      # Green
        "warning": 0xFF9800,      # Orange
        "error": 0xF44336,        # Red
        "info": 0x00BCD4,         # Cyan
        "security": 0xF44336,
    },
    "shadow": {
        "name": "Shadow",
        "description": "Dark mysterious theme",
        "emoji": "🖤",
        "primary": 0x1a1a2e,      # Very dark blue
        "secondary": 0x16213e,    # Dark navy
        "success": 0x0f3460,      # Dark blue
        "warning": 0xe94560,      # Pink-red
        "error": 0xe94560,        # Pink-red
        "info": 0x0f3460,         # Dark blue
        "security": 0xe94560,
    },
    "mint": {
        "name": "Mint",
        "description": "Fresh mint green theme",
        "emoji": "🍃",
        "primary": 0x00C853,      # Mint
        "secondary": 0x00E676,    # Light mint
        "success": 0x00C853,      # Mint
        "warning": 0xFFD600,      # Yellow
        "error": 0xFF5252,        # Red
        "info": 0x00B0FF,         # Blue
        "security": 0xFF5252,
    },
}


class ThemePreviewView(discord.ui.View):
    """View for previewing and selecting themes"""

    def __init__(self, bot, author: discord.Member, current_theme: str):
        super().__init__(timeout=180)
        self.bot = bot
        self.author = author
        self.current_theme = current_theme
        self.selected_theme = current_theme
        self.add_theme_select()

    def add_theme_select(self):
        options = []
        for theme_id, theme in PRESET_THEMES.items():
            options.append(discord.SelectOption(
                label=theme["name"],
                value=theme_id,
                emoji=theme["emoji"],
                description=theme["description"][:50],
                default=(theme_id == self.selected_theme)
            ))

        select = discord.ui.Select(
            placeholder="Select a theme to preview...",
            options=options,
            row=0
        )
        select.callback = self.theme_select_callback
        self.add_item(select)

    async def theme_select_callback(self, interaction: discord.Interaction):
        self.selected_theme = interaction.data["values"][0]
        embed = self.create_preview_embed(self.selected_theme)

        # Update buttons
        self.clear_items()
        self.add_theme_select()
        self.add_item(ApplyThemeButton(self.selected_theme))
        self.add_item(CancelButton())

        await interaction.response.edit_message(embed=embed, view=self)

    def create_preview_embed(self, theme_id: str) -> discord.Embed:
        theme = PRESET_THEMES[theme_id]

        embed = discord.Embed(color=theme["primary"])

        embed.description = f"""
**Theme Preview: {theme['name']}**

*{theme['description']}*

This is a preview of how your embeds will look with this theme.

**Color Palette**
› Primary: `#{theme['primary']:06X}`
› Secondary: `#{theme['secondary']:06X}`
› Success: `#{theme['success']:06X}`
› Warning: `#{theme['warning']:06X}`
› Error: `#{theme['error']:06X}`
› Info: `#{theme['info']:06X}`

**Applied To**
› Success messages
› Warning alerts
› Error notifications
› Security alerts
› Information panels
"""
        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            embed = discord.Embed(description="✕ Only the command author can use this menu", color=EMBED_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return False
        return True


class ApplyThemeButton(discord.ui.Button):
    def __init__(self, theme_id: str):
        self.theme_id = theme_id
        theme = PRESET_THEMES[theme_id]
        super().__init__(
            label=f"Apply {theme['name']} Theme",
            style=discord.ButtonStyle.success,
            row=1
        )

    async def callback(self, interaction: discord.Interaction):
        cog = interaction.client.get_cog('Themes')
        if cog:
            cog.set_guild_theme(interaction.guild.id, self.theme_id)

        theme = PRESET_THEMES[self.theme_id]
        embed = discord.Embed(color=theme["primary"])
        embed.description = f"+ **{theme['name']}** theme is now active\n\nAll bot embeds will now use your selected color scheme."

        await interaction.response.edit_message(embed=embed, view=None)


class CancelButton(discord.ui.Button):
    def __init__(self):
        super().__init__(
            label="Cancel",
            style=discord.ButtonStyle.secondary,
            row=1
        )

    async def callback(self, interaction: discord.Interaction):
        embed = discord.Embed(description="Theme selection cancelled", color=EMBED_COLOR)
        await interaction.response.edit_message(embed=embed, view=None)


class CustomColorModal(discord.ui.Modal, title="Custom Theme Colors"):
    """Modal for entering custom hex colors"""

    primary = discord.ui.TextInput(
        label="Primary Color (Hex)",
        placeholder="e.g., #9B59B6 or 9B59B6",
        default="#9B59B6",
        max_length=7,
        required=True
    )

    success = discord.ui.TextInput(
        label="Success Color (Hex)",
        placeholder="e.g., #2ECC71",
        default="#2ECC71",
        max_length=7,
        required=True
    )

    error = discord.ui.TextInput(
        label="Error Color (Hex)",
        placeholder="e.g., #E74C3C",
        default="#E74C3C",
        max_length=7,
        required=True
    )

    warning = discord.ui.TextInput(
        label="Warning Color (Hex)",
        placeholder="e.g., #F39C12",
        default="#F39C12",
        max_length=7,
        required=True
    )

    info = discord.ui.TextInput(
        label="Info Color (Hex)",
        placeholder="e.g., #3498DB",
        default="#3498DB",
        max_length=7,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Parse hex colors
            def parse_hex(val: str) -> int:
                val = val.strip().lstrip('#')
                return int(val, 16)

            custom_theme = {
                "name": "Custom",
                "description": "Your custom color theme",
                "emoji": "",
                "primary": parse_hex(self.primary.value),
                "secondary": parse_hex(self.primary.value),
                "success": parse_hex(self.success.value),
                "warning": parse_hex(self.warning.value),
                "error": parse_hex(self.error.value),
                "info": parse_hex(self.info.value),
                "security": parse_hex(self.error.value),
            }

            cog = interaction.client.get_cog('Themes')
            if cog:
                cog.set_guild_theme(interaction.guild.id, "custom", custom_theme)

            embed = discord.Embed(color=custom_theme["primary"])
            embed.description = f"""
+ **Custom Theme** is now active

**Your Colors**
› Primary: `{self.primary.value}`
› Success: `{self.success.value}`
› Error: `{self.error.value}`
› Warning: `{self.warning.value}`
› Info: `{self.info.value}`
"""
            await interaction.response.send_message(embed=embed)

        except ValueError as e:
            embed = discord.Embed(description=f"✕ Invalid hex color format. Use format like `#9B59B6`", color=EMBED_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)


class Themes(commands.Cog):
    """Theme & Customization System"""

    def __init__(self, bot):
        self.bot = bot
        self.guild_themes: Dict[int, Dict[str, Any]] = {}
        self.data_file = "data/themes.json"
        self.load_themes()

    def load_themes(self):
        """Load saved themes from file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    self.guild_themes = json.load(f)
                    # Convert string keys to int
                    self.guild_themes = {int(k): v for k, v in self.guild_themes.items()}
                logger.info(f"Loaded {len(self.guild_themes)} guild themes")
        except Exception as e:
            logger.error(f"Failed to load themes: {e}")
            self.guild_themes = {}

    def save_themes(self):
        """Save themes to file"""
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, 'w') as f:
                json.dump(self.guild_themes, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save themes: {e}")

    def get_guild_theme(self, guild_id: int) -> Dict[str, Any]:
        """Get the theme for a guild"""
        if guild_id in self.guild_themes:
            theme_data = self.guild_themes[guild_id]
            if theme_data.get("theme_id") == "custom":
                return theme_data.get("custom_theme", PRESET_THEMES["default"])
            return PRESET_THEMES.get(theme_data.get("theme_id", "default"), PRESET_THEMES["default"])
        return PRESET_THEMES["default"]

    def get_guild_theme_id(self, guild_id: int) -> str:
        """Get the theme ID for a guild"""
        if guild_id in self.guild_themes:
            return self.guild_themes[guild_id].get("theme_id", "default")
        return "default"

    def set_guild_theme(self, guild_id: int, theme_id: str, custom_theme: Dict = None):
        """Set the theme for a guild"""
        self.guild_themes[guild_id] = {
            "theme_id": theme_id,
            "custom_theme": custom_theme
        }
        self.save_themes()
        logger.info(f"Set theme for guild {guild_id} to {theme_id}")

    def get_color(self, guild_id: int, color_type: str = "primary") -> int:
        """Get a specific color for a guild's theme"""
        theme = self.get_guild_theme(guild_id)
        return theme.get(color_type, theme.get("primary", 0x9B59B6))

    # ═══════════════════════════════════════════════════════════
    # PREFIX COMMANDS
    # ═══════════════════════════════════════════════════════════

    @commands.group(name='theme', aliases=['themes', 'color', 'colors'], invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def theme_group(self, ctx):
        """Theme customization commands"""
        current_theme_id = self.get_guild_theme_id(ctx.guild.id)
        current_theme = self.get_guild_theme(ctx.guild.id)

        # Show available themes
        themes_preview = ", ".join([f"`{t['name']}`" for t in list(PRESET_THEMES.values())[:6]]) + "..."

        embed = discord.Embed(color=current_theme["primary"])
        embed.description = f"""
**Theme Customization**

› Current Theme: **{current_theme.get('name', 'Default')}**

**Commands**
› `!theme list` − View all themes
› `!theme set` − Open theme selector
› `!theme set <name>` − Apply theme directly
› `!theme custom` − Create custom theme
› `!theme reset` − Reset to default
› `!theme preview` − Preview current theme

**Available Themes**
{themes_preview}
"""
        await ctx.send(embed=embed)

    @theme_group.command(name='list')
    @commands.has_permissions(administrator=True)
    async def theme_list(self, ctx):
        """List all available themes"""
        current_theme_id = self.get_guild_theme_id(ctx.guild.id)

        theme_list = ""
        for theme_id, theme in PRESET_THEMES.items():
            current = " (current)" if theme_id == current_theme_id else ""
            theme_list += f"› **{theme['name']}**{current}\n   *{theme['description']}*\n\n"

        embed = discord.Embed(color=self.get_color(ctx.guild.id))
        embed.description = f"**Available Themes**\n\n{theme_list}Use `!theme set` to open the selector or `!theme set <name>` to apply directly."

        await ctx.send(embed=embed)

    @theme_group.command(name='set')
    @commands.has_permissions(administrator=True)
    async def theme_set(self, ctx, theme_name: str = None):
        """Set a theme for this server"""
        if theme_name:
            # Direct theme set
            theme_id = theme_name.lower()
            if theme_id not in PRESET_THEMES:
                # Try to find by name
                for tid, theme in PRESET_THEMES.items():
                    if theme["name"].lower() == theme_id:
                        theme_id = tid
                        break
                else:
                    available = ", ".join([f"`{t['name']}`" for t in PRESET_THEMES.values()])
                    embed = discord.Embed(description=f"✕ Unknown theme `{theme_name}`\n\nAvailable: {available}", color=EMBED_COLOR)
                    return await ctx.send(embed=embed)

            self.set_guild_theme(ctx.guild.id, theme_id)
            theme = PRESET_THEMES[theme_id]

            embed = discord.Embed(color=theme["primary"])
            embed.description = f"+ **{theme['name']}** theme is now active\n\n*{theme['description']}*"
            await ctx.send(embed=embed)
        else:
            # Open theme selector
            current_theme_id = self.get_guild_theme_id(ctx.guild.id)
            view = ThemePreviewView(self.bot, ctx.author, current_theme_id)
            embed = view.create_preview_embed(current_theme_id)
            await ctx.send(embed=embed, view=view)

    @theme_group.command(name='custom')
    @commands.has_permissions(administrator=True)
    async def theme_custom(self, ctx):
        """Create a custom color theme"""
        embed = discord.Embed(color=self.get_color(ctx.guild.id))
        embed.description = """
**Custom Theme Creator**

Create your own custom color theme.

Click the button below to enter your custom hex colors.

**Tip**
Use a color picker like [coolors.co](https://coolors.co) to find colors.
"""

        view = discord.ui.View(timeout=180)

        async def open_modal(interaction: discord.Interaction):
            if interaction.user.id != ctx.author.id:
                embed = discord.Embed(description="✕ Only the command author can use this", color=EMBED_COLOR)
                return await interaction.response.send_message(embed=embed, ephemeral=True)
            await interaction.response.send_modal(CustomColorModal())

        button = discord.ui.Button(label="Create Custom Theme", style=discord.ButtonStyle.primary)
        button.callback = open_modal
        view.add_item(button)

        await ctx.send(embed=embed, view=view)

    @theme_group.command(name='reset')
    @commands.has_permissions(administrator=True)
    async def theme_reset(self, ctx):
        """Reset to default theme"""
        self.set_guild_theme(ctx.guild.id, "default")

        embed = discord.Embed(description="+ Theme reset to **Default**", color=PRESET_THEMES["default"]["primary"])
        await ctx.send(embed=embed)

    @theme_group.command(name='preview')
    @commands.has_permissions(administrator=True)
    async def theme_preview(self, ctx):
        """Preview the current theme"""
        theme = self.get_guild_theme(ctx.guild.id)

        embed = discord.Embed(color=theme["primary"])
        embed.description = f"""
**Current Theme: {theme.get('name', 'Default')}**

*{theme.get('description', 'Classic theme')}*

**Color Codes**
› Primary: `#{theme['primary']:06X}`
› Success: `#{theme['success']:06X}`
› Warning: `#{theme['warning']:06X}`
› Error: `#{theme['error']:06X}`
› Info: `#{theme['info']:06X}`
"""
        await ctx.send(embed=embed)

    # ═══════════════════════════════════════════════════════════
    # SLASH COMMANDS
    # ═══════════════════════════════════════════════════════════

    theme_slash = app_commands.Group(name='theme', description='Theme customization commands')

    @theme_slash.command(name='list', description='View all available themes')
    @app_commands.default_permissions(administrator=True)
    async def slash_theme_list(self, interaction: discord.Interaction):
        current_theme_id = self.get_guild_theme_id(interaction.guild.id)

        theme_list = ""
        for theme_id, theme in PRESET_THEMES.items():
            current = " (current)" if theme_id == current_theme_id else ""
            theme_list += f"› **{theme['name']}**{current}\n"

        embed = discord.Embed(color=self.get_color(interaction.guild.id))
        embed.description = f"**Available Themes**\n\n{theme_list}\nUse `/theme set` to change"
        await interaction.response.send_message(embed=embed)

    @theme_slash.command(name='set', description='Set a theme for your server')
    @app_commands.describe(theme='Choose a theme')
    @app_commands.default_permissions(administrator=True)
    async def slash_theme_set(
        self,
        interaction: discord.Interaction,
        theme: Literal['default', 'midnight', 'crimson', 'emerald', 'ocean', 'sunset', 'gold', 'neon', 'rose', 'arctic', 'shadow', 'mint']
    ):
        self.set_guild_theme(interaction.guild.id, theme)
        theme_data = PRESET_THEMES[theme]

        embed = discord.Embed(color=theme_data["primary"])
        embed.description = f"+ **{theme_data['name']}** theme is now active\n\n*{theme_data['description']}*"
        await interaction.response.send_message(embed=embed)

    @theme_slash.command(name='custom', description='Create a custom color theme')
    @app_commands.default_permissions(administrator=True)
    async def slash_theme_custom(self, interaction: discord.Interaction):
        await interaction.response.send_modal(CustomColorModal())

    @theme_slash.command(name='reset', description='Reset to default theme')
    @app_commands.default_permissions(administrator=True)
    async def slash_theme_reset(self, interaction: discord.Interaction):
        self.set_guild_theme(interaction.guild.id, "default")

        embed = discord.Embed(description="+ Theme reset to **Default**", color=PRESET_THEMES["default"]["primary"])
        await interaction.response.send_message(embed=embed)

    @theme_slash.command(name='preview', description='Preview current theme colors')
    @app_commands.default_permissions(administrator=True)
    async def slash_theme_preview(self, interaction: discord.Interaction):
        current_theme_id = self.get_guild_theme_id(interaction.guild.id)
        view = ThemePreviewView(self.bot, interaction.user, current_theme_id)
        embed = view.create_preview_embed(current_theme_id)
        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(Themes(bot))
