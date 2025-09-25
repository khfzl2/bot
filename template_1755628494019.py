import discord
from discord.ext import commands
from discord import app_commands
import logging
import asyncio
from ..utils import create_embed, create_error_embed, create_success_embed, has_permissions

logger = logging.getLogger(__name__)

class TemplateCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="template")
    @has_permissions(administrator=False, manage_channels=True)
    async def create_template(self, ctx, *, description: str = None):
        """Create a server template with categories, channels, and roles"""
        await self._create_template_logic(ctx, description)

    @commands.command(name="roles", aliases=["roleinfo", "role-info"])
    async def describe_roles(self, ctx, role_name: str = None):
        """Describe server roles and their permissions"""
        await self._describe_roles_logic(ctx, role_name)

    async def _describe_roles_logic(self, ctx, role_name: str = None):
        """Logic for describing roles and their permissions"""

        # Role descriptions and their purposes
        role_descriptions = {
            "Owner": {
                "description": "The highest authority in the server with complete control over all aspects.",
                "purpose": "Server ownership, final decision making, and complete administrative control",
                "permissions": "All permissions including server deletion and ownership transfer",
                "color": discord.Color.from_rgb(255, 0, 0),
                "icon": "👑"
            },
            "Co-Owner": {
                "description": "Second-in-command with nearly all administrative powers, trusted with server management.",
                "purpose": "Assist the owner in server management and handle major administrative tasks",
                "permissions": "All permissions except server deletion and ownership transfer",
                "color": discord.Color.from_rgb(255, 128, 0),
                "icon": "💎"
            },
            "Manager": {
                "description": "Senior staff member responsible for overseeing operations and managing other staff.",
                "purpose": "Oversee daily operations, manage staff, and implement server policies",
                "permissions": "Full administrative permissions including role management and server settings",
                "color": discord.Color.from_rgb(255, 255, 0),
                "icon": "⭐"
            },
            "BOTS": {
                "description": "Automated systems that help manage and moderate the server.",
                "purpose": "Provide automated moderation, utilities, and enhanced server functionality",
                "permissions": "Full permissions to perform automated tasks and server management",
                "color": discord.Color.from_rgb(128, 128, 128),
                "icon": "🤖"
            },
            "Administrator": {
                "description": "High-level staff with broad administrative powers for server management.",
                "purpose": "Handle complex administrative tasks, manage channels, and assist with server development",
                "permissions": "Full administrative permissions including channel/role management",
                "color": discord.Color.from_rgb(255, 0, 255),
                "icon": "🛡️"
            },
            "Moderator": {
                "description": "Frontline staff responsible for maintaining order and enforcing server rules.",
                "purpose": "Monitor chat, enforce rules, handle reports, and moderate user behavior",
                "permissions": "Moderation permissions: kick, ban, mute, manage messages, timeout members",
                "color": discord.Color.from_rgb(0, 255, 0),
                "icon": "🔨"
            },
            "Member": {
                "description": "Standard server member with basic participation privileges.",
                "purpose": "Participate in server activities, chat, and use voice channels",
                "permissions": "Basic permissions: send messages, connect to voice, use emojis",
                "color": discord.Color.from_rgb(0, 191, 255),
                "icon": "👤"
            }
        }

        if role_name:
            # Show specific role information
            role_name = role_name.title()
            if role_name in role_descriptions:
                role_info = role_descriptions[role_name]
                embed = discord.Embed(
                    title=f"{role_info['icon']} {role_name} Role Information",
                    description=role_info['description'],
                    color=role_info['color']
                )
                embed.add_field(
                    name="📋 Purpose",
                    value=role_info['purpose'],
                    inline=False
                )
                embed.add_field(
                    name="🔐 Permissions",
                    value=role_info['permissions'],
                    inline=False
                )

                # Check if role exists in server
                server_role = discord.utils.get(ctx.guild.roles, name=role_name)
                if server_role:
                    embed.add_field(
                        name="📊 Server Info",
                        value=f"**Members:** {len(server_role.members)}\n**Position:** {server_role.position}\n**Mentionable:** {'Yes' if server_role.mentionable else 'No'}",
                        inline=True
                    )
                else:
                    embed.add_field(
                        name="❌ Server Status",
                        value="This role doesn't exist in this server yet",
                        inline=True
                    )

                embed.set_footer(text=f"Requested by {ctx.author.display_name}")
                await ctx.send(embed=embed)
            else:
                await ctx.send(embed=create_error_embed("Role Not Found", f"No information available for role '{role_name}'. Available roles: {', '.join(role_descriptions.keys())}"))
        else:
            # Show all roles overview
            embed = discord.Embed(
                title="🏛️ Server Role Hierarchy & Descriptions",
                description="Complete guide to server roles, their purposes, and permissions",
                color=discord.Color.blue()
            )

            # Add role hierarchy
            hierarchy_text = ""
            for role_name, info in role_descriptions.items():
                if role_name == "BOTS":
                    continue  # Skip bots in hierarchy display
                server_role = discord.utils.get(ctx.guild.roles, name=role_name)
                member_count = len(server_role.members) if server_role else 0
                hierarchy_text += f"{info['icon']} **{role_name}** - {member_count} members\n{info['description']}\n\n"

            embed.add_field(
                name="📊 Role Hierarchy (Highest to Lowest)",
                value=hierarchy_text,
                inline=False
            )

            # Permission categories explanation
            permission_info = """
**🔴 Owner/Co-Owner:** Complete server control
**🟡 Manager/Admin:** Full administrative powers
**🟢 Moderator:** Moderation and rule enforcement
**🔵 Member:** Basic participation rights
**⚪ Bots:** Automated server management
            """

            embed.add_field(
                name="🔐 Permission Categories",
                value=permission_info,
                inline=False
            )

            embed.add_field(
                name="💡 Usage",
                value="Use `k!roles <role_name>` for detailed information about a specific role",
                inline=False
            )
            
            embed.add_field
                name="Command Information",
                value="This command is currently under development and may not work as expected. We are currently working on a fix with the bot.
                inline=False"
            )
            
            embed.set_footer(text=f"Requested by {ctx.author.display_name}")
            await ctx.send(embed=embed)

    async def _create_template_logic(self, ctx, description: str = None):
        # Check bot permissions
        required_permissions = [
            'manage_channels', 'manage_roles', 'send_messages`
        ]

        missing_permissions = []
        for perm in required_permissions:
            if not getattr(ctx.guild.me.guild_permissions, perm, False):
                missing_permissions.append(perm.replace('_', ' ').title())

        if missing_permissions:
            error_msg = f"Sorry but my permission is not able to make the categories, text channels, etc.\n\nMissing permissions: {', '.join(missing_permissions)}"
            await ctx.send(embed=create_error_embed("Insufficient Permissions", error_msg))
            return

        # Send initial message
        status_msg = await ctx.send(embed=create_embed("🏗️ Template Creation", "Creating Categories..."))

        try:
            # Create roles with appropriate permissions and colors
            roles_data = [
                ("Owner", discord.Permissions.all(), discord.Color.from_rgb(255, 0, 0)),  # Red
                ("Co-Owner", discord.Permissions.all(), discord.Color.from_rgb(255, 128, 0)),  # Orange
                ("Manager", discord.Permissions.all(), discord.Color.from_rgb(255, 255, 0)),  # Yellow
                ("BOTS", discord.Permissions.all(), discord.Color.from_rgb(128, 128, 128)),  # Gray
                ("Administrator", discord.Permissions.all(), discord.Color.from_rgb(255, 0, 255)),  # Magenta
                ("Moderator", discord.Permissions(
                    kick_members=True,
                    ban_members=True,
                    manage_messages=True,
                    mute_members=True,
                    deafen_members=True,
                    move_members=True,
                    manage_nicknames=True,
                    view_audit_log=True,
                    moderate_members=True
                ), discord.Color.from_rgb(0, 255, 0)),  # Green
                ("Member", discord.Permissions(
                    send_messages=True,
                    read_messages=True,
                    connect=True,
                    speak=True,
                    use_voice_activation=True
                ), discord.Color.from_rgb(0, 191, 255)),  # Blue
                ("@everyone", discord.Permissions.none(), discord.Color.default())
            ]

            # Update status to creating roles
            await status_msg.edit(embed=create_embed("🏗️ Template Creation", "Creating roles..."))

            created_roles = {}
            for role_name, permissions, color in roles_data:
                if role_name == "@everyone":
                    # Update @everyone role
                    await ctx.guild.default_role.edit(permissions=permissions)
                    created_roles["@everyone"] = ctx.guild.default_role
                else:
                    # Check if role already exists
                    existing_role = discord.utils.get(ctx.guild.roles, name=role_name)
                    if existing_role:
                        # Update existing role
                        await existing_role.edit(permissions=permissions, color=color)
                        created_roles[role_name] = existing_role
                    else:
                        # Create new role
                        role = await ctx.guild.create_role(
                            name=role_name,
                            permissions=permissions,
                            color=color,
                            reason=f"Template setup by {ctx.author}"
                        )
                        created_roles[role_name] = role
                        await asyncio.sleep(0.5)  # Rate limit protection

            # Create categories and channels
            await status_msg.edit(embed=create_embed("🏗️ Template Creation", "Creating Text Channels..."))

            # Get template structure based on description
            template_structure = self._get_template_structure(description)

            # Default template structure if no custom one
            if not template_structure:
                template_structure = [
                    {
                        "category": "‼️Information",
                        "channels": [
                            ("📜", "rules", "text"),
                            ("📢", "announcements", "text"),
                            ("📝", "beside-notes", "text"),
                            ("💱", "change-logs", "text"),
                            ("🖥️", "staff-applications", "text")
                        ]
                    },
                    {
                        "category": "👋 General",
                        "channels": [
                            ("🗨️", "general", "text"),
                            ("😂", "memes", "text"),
                            ("👋", "introductions", "text"),
                            ("🎊", "birthdays", "text"),
                            ("💻", "self-promotion", "text"),
                            ("🐶", "pet-reveals", "text"),
                            ("🙎", "face-reveals", "text")
                        ]
                    },
                    {
                        "category": "➕Extra",
                        "channels": [
                            ("🔢", "counting", "text"),
                            ("😈", "spam", "text"),
                            ("🎟️", "tickets", "text"),
                            ("😭", "mental-health-zone", "text"),
                            ("🗣️", "voice-reveal", "text")
                        ]
                    },
                    {
                        "category": "🔈Voice Chat",
                        "channels": [
                            ("🔊", "voice-chat-1", "voice"),
                            ("🔊", "voice-chat-2", "voice"),
                            ("🎮", "gaming", "voice"),
                            ("🎭", "theatre", "voice"),
                            ("🔊", "staff-voice-chat", "voice")
                        ]
                    },
                    {
                        "category": "💼 Staff Only",
                        "channels": [
                            ("📢", "staff-announcements", "text"),
                            ("💼", "all-staff-chat", "text"),
                            ("💼", "moderator-chat", "text"),
                            ("💼", "administrator-chat", "text"),
                            ("💼", "manager-plus-chat", "text"),
                            ("👀", "staff-logs", "text")
                        ]
                    }
                ]

            # Create categories and channels
            for category_data in template_structure:
                category_name = category_data["category"]

                # Check if category already exists
                existing_category = discord.utils.get(ctx.guild.categories, name=category_name)
                if existing_category:
                    category = existing_category
                else:
                    # Set up permissions for categories
                    overwrites = {
                        ctx.guild.default_role: discord.PermissionOverwrite(read_messages=True)
                    }

                    # Staff only category permissions
                    if "Staff Only" in category_name:
                        overwrites[ctx.guild.default_role] = discord.PermissionOverwrite(read_messages=False)
                        for role_name in ["Owner", "Co-Owner", "Manager", "BOTS", "Administrator", "Moderator"]:
                            if role_name in created_roles:
                                overwrites[created_roles[role_name]] = discord.PermissionOverwrite(read_messages=True)

                    category = await ctx.guild.create_category(
                        name=category_name,
                        overwrites=overwrites
                    )
                    await asyncio.sleep(0.5)

                # Create channels in category
                for emoji, channel_name, channel_type in category_data["channels"]:
                    full_channel_name = f