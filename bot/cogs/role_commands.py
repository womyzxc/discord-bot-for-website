"""
Role Commands Cog - With Role Hierarchy Protection
"""

import discord
from discord.ext import commands
from discord import app_commands
import logging
import os

logger = logging.getLogger('Offcialx.RoleCommands')

EMBED_COLOR = 0x2b2d31

# Owner/Developer IDs
OWNER_IDS = set()
for oid in os.getenv('OWNER_IDS', '').split(','):
    try:
        OWNER_IDS.add(int(oid.strip()))
    except:
        pass
OWNER_IDS.add(1184454687865438218)  # Developer ID


class RoleCommands(commands.Cog):
    """Role Management Commands with Hierarchy Protection"""

    def __init__(self, bot):
        self.bot = bot
        logger.info("RoleCommands cog initialized")

    def is_privileged(self, guild: discord.Guild, user_id: int) -> bool:
        """Check if user is server owner, bot owner, or developer"""
        if user_id == guild.owner_id:
            return True
        if user_id in OWNER_IDS:
            return True
        if self.bot.owner_ids and user_id in self.bot.owner_ids:
            return True
        return False

    def check_role_hierarchy(self, guild: discord.Guild, author: discord.Member,
                             target: discord.Member, role: discord.Role) -> tuple[bool, str]:
        """
        Check role hierarchy for safety
        Returns (can_manage, error_message)

        Only checks bot limitations - if you have permission, you can manage any role the bot can
        """
        # Cannot manage roles higher than bot's top role
        if role >= guild.me.top_role:
            return False, f"Role is higher than my role (Bot: {guild.me.top_role.position}, Role: {role.position})"

        # Cannot manage managed roles (bot/integration roles)
        if role.managed:
            return False, "Cannot manage bot/integration roles"

        # Cannot manage @everyone
        if role.is_default():
            return False, "Cannot manage @everyone role"

        return True, ""

    @commands.Cog.listener()
    async def on_ready(self):
        logger.info("✅ RoleCommands cog is ready")

    # Test command
    @commands.command(name='roletest')
    async def role_test(self, ctx: commands.Context):
        """Test if role commands are working"""
        embed = discord.Embed(description="➕ Role commands are working!", color=EMBED_COLOR)
        await ctx.send(embed=embed)

    # Main role command - prefix version
    @commands.command(name='role', aliases=['r'])
    @commands.guild_only()
    async def role_cmd(self, ctx: commands.Context, member: discord.Member = None, *, role_name: str = None):
        """Toggle a role on a member (with hierarchy check)

        Usage: !role @user RoleName
        """
        logger.info(f"Role command called by {ctx.author} in {ctx.guild.name}")

        # Check if arguments provided
        if not member or not role_name:
            embed = discord.Embed(description="✖️ Usage: `!role @user RoleName`", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        # Check user has manage_roles permission
        if not ctx.author.guild_permissions.manage_roles and not self.is_privileged(ctx.guild, ctx.author.id):
            embed = discord.Embed(description="✖️ You need Manage Roles permission", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        # Find the role
        role = None
        role_name_clean = role_name.strip()

        # Check if it's a role mention
        if role_name_clean.startswith('<@&') and role_name_clean.endswith('>'):
            try:
                role_id = int(role_name_clean[3:-1])
                role = ctx.guild.get_role(role_id)
            except:
                pass

        # Check if it's a role ID
        if not role:
            try:
                role = ctx.guild.get_role(int(role_name_clean))
            except:
                pass

        # Search by name (case-insensitive exact match)
        if not role:
            for r in ctx.guild.roles:
                if r.name.lower() == role_name_clean.lower():
                    role = r
                    break

        # Search by name (partial match)
        if not role:
            for r in ctx.guild.roles:
                if role_name_clean.lower() in r.name.lower():
                    role = r
                    break

        if not role:
            embed = discord.Embed(description=f"✖️ Role `{role_name}` not found", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        # Check bot permissions
        if not ctx.guild.me.guild_permissions.manage_roles:
            embed = discord.Embed(description="✖️ I need Manage Roles permission", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        # Check role hierarchy
        can_manage, error = self.check_role_hierarchy(ctx.guild, ctx.author, member, role)
        if not can_manage:
            embed = discord.Embed(description=f"✖️ {error}", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        # Toggle role
        try:
            if role in member.roles:
                await member.remove_roles(role, reason=f"By {ctx.author}")
                embed = discord.Embed(description=f"➖ Removed {role.mention} from {member.mention}", color=EMBED_COLOR)
            else:
                await member.add_roles(role, reason=f"By {ctx.author}")
                embed = discord.Embed(description=f"➕ Added {role.mention} to {member.mention}", color=EMBED_COLOR)
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = discord.Embed(description="✖️ I don't have permission to manage that role", color=EMBED_COLOR)
            await ctx.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(description=f"✖️ Error: {e}", color=EMBED_COLOR)
            await ctx.send(embed=embed)

    @role_cmd.error
    async def role_cmd_error(self, ctx: commands.Context, error):
        """Handle role command errors"""
        if isinstance(error, commands.MemberNotFound):
            embed = discord.Embed(description="✖️ Member not found", color=EMBED_COLOR)
            await ctx.send(embed=embed)
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(description="✖️ Usage: `!role @user RoleName`", color=EMBED_COLOR)
            await ctx.send(embed=embed)
        else:
            logger.error(f"Role command error: {error}")
            embed = discord.Embed(description=f"✖️ Error: {error}", color=EMBED_COLOR)
            await ctx.send(embed=embed)

    # Slash command for role
    @app_commands.command(name='role', description='Toggle a role on a member')
    @app_commands.describe(member='The member', role='The role to toggle')
    @app_commands.default_permissions(manage_roles=True)
    async def role_slash(self, interaction: discord.Interaction, member: discord.Member, role: discord.Role):
        """Slash command to toggle a role (with hierarchy check)"""
        guild = interaction.guild
        author = interaction.user

        # Check bot permissions
        if not guild.me.guild_permissions.manage_roles:
            embed = discord.Embed(description="✖️ I need Manage Roles permission", color=EMBED_COLOR)
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        # Check role hierarchy
        can_manage, error = self.check_role_hierarchy(guild, author, member, role)
        if not can_manage:
            embed = discord.Embed(description=f"✖️ {error}", color=EMBED_COLOR)
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        # Toggle role
        try:
            if role in member.roles:
                await member.remove_roles(role, reason=f"By {author}")
                embed = discord.Embed(description=f"➖ Removed {role.mention} from {member.mention}", color=EMBED_COLOR)
            else:
                await member.add_roles(role, reason=f"By {author}")
                embed = discord.Embed(description=f"➕ Added {role.mention} to {member.mention}", color=EMBED_COLOR)
            await interaction.response.send_message(embed=embed)
        except discord.Forbidden:
            embed = discord.Embed(description="✖️ I don't have permission", color=EMBED_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            embed = discord.Embed(description=f"✖️ Error: {e}", color=EMBED_COLOR)
            await interaction.response.send_message(embed=embed, ephemeral=True)

    # Add role command
    @commands.command(name='addrole', aliases=['giverole'])
    @commands.guild_only()
    async def add_role(self, ctx: commands.Context, member: discord.Member = None, *, role_name: str = None):
        """Add a role to a member (with hierarchy check)"""
        if not member or not role_name:
            embed = discord.Embed(description="✖️ Usage: `!addrole @user RoleName`", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        # Check permissions
        if not ctx.author.guild_permissions.manage_roles and not self.is_privileged(ctx.guild, ctx.author.id):
            embed = discord.Embed(description="✖️ You need Manage Roles permission", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        # Find role
        role = None
        for r in ctx.guild.roles:
            if r.name.lower() == role_name.strip().lower():
                role = r
                break
        if not role:
            for r in ctx.guild.roles:
                if role_name.strip().lower() in r.name.lower():
                    role = r
                    break

        if not role:
            embed = discord.Embed(description=f"✖️ Role `{role_name}` not found", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        # Check hierarchy
        can_manage, error = self.check_role_hierarchy(ctx.guild, ctx.author, member, role)
        if not can_manage:
            embed = discord.Embed(description=f"✖️ {error}", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        if role in member.roles:
            embed = discord.Embed(description=f"✖️ {member.mention} already has {role.mention}", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        try:
            await member.add_roles(role, reason=f"By {ctx.author}")
            embed = discord.Embed(description=f"➕ Added {role.mention} to {member.mention}", color=EMBED_COLOR)
            await ctx.send(embed=embed)
        except:
            embed = discord.Embed(description="✖️ Failed to add role", color=EMBED_COLOR)
            await ctx.send(embed=embed)

    # Remove role command
    @commands.command(name='removerole', aliases=['takerole'])
    @commands.guild_only()
    async def remove_role(self, ctx: commands.Context, member: discord.Member = None, *, role_name: str = None):
        """Remove a role from a member (with hierarchy check)"""
        if not member or not role_name:
            embed = discord.Embed(description="✖️ Usage: `!removerole @user RoleName`", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        # Check permissions
        if not ctx.author.guild_permissions.manage_roles and not self.is_privileged(ctx.guild, ctx.author.id):
            embed = discord.Embed(description="✖️ You need Manage Roles permission", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        # Find role
        role = None
        for r in ctx.guild.roles:
            if r.name.lower() == role_name.strip().lower():
                role = r
                break
        if not role:
            for r in ctx.guild.roles:
                if role_name.strip().lower() in r.name.lower():
                    role = r
                    break

        if not role:
            embed = discord.Embed(description=f"✖️ Role `{role_name}` not found", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        # Check hierarchy
        can_manage, error = self.check_role_hierarchy(ctx.guild, ctx.author, member, role)
        if not can_manage:
            embed = discord.Embed(description=f"✖️ {error}", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        if role not in member.roles:
            embed = discord.Embed(description=f"✖️ {member.mention} doesn't have {role.mention}", color=EMBED_COLOR)
            return await ctx.send(embed=embed)

        try:
            await member.remove_roles(role, reason=f"By {ctx.author}")
            embed = discord.Embed(description=f"➖ Removed {role.mention} from {member.mention}", color=EMBED_COLOR)
            await ctx.send(embed=embed)
        except:
            embed = discord.Embed(description="✖️ Failed to remove role", color=EMBED_COLOR)
            await ctx.send(embed=embed)


async def setup(bot):
    try:
        cog = RoleCommands(bot)
        await bot.add_cog(cog)
        logger.info("✅ RoleCommands cog loaded successfully")
        # Log registered commands
        for cmd in cog.get_commands():
            logger.info(f"  - Registered command: {cmd.name}")
    except Exception as e:
        logger.error(f"❌ Failed to load RoleCommands cog: {e}")
        import traceback
        traceback.print_exc()
        raise
