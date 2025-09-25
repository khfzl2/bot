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
    async def create_template(self, ctx, *, description: str = None):
        """Create a server template with categories, channels, and roles"""
        # Check if user has administrator permission
        if not ctx.author.guild_permissions.administrator:
            await ctx.send(embed=create_error_embed("Insufficient Permissions", "You need Administrator permissions to use this command."))
            return
        await self._create_template_logic(ctx, description)

    @app_commands.command(name="template", description="Create a server template with categories, channels, and roles")
    @app_commands.describe(description="Describe the template you want or leave blank for default")
    async def slash_template(self, interaction: discord.Interaction, description: str = None):
        """Slash command version of template"""
        # Check permissions
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                embed=create_error_embed("Missing Permissions", "You need Administrator permissions to use this command."),
                ephemeral=True
            )
            return

        await interaction.response.defer()

        # Create a fake context for compatibility
        class FakeContext:
            def __init__(self, interaction):
                self.guild = interaction.guild
                self.author = interaction.user
                self.channel = interaction.channel
                self.interaction = interaction

            async def send(self, *args, **kwargs):
                if hasattr(self, 'interaction') and not self.interaction.response.is_done():
                    return await self.interaction.followup.send(*args, **kwargs)
                else:
                    return await self.interaction.followup.send(*args, **kwargs)

        ctx = FakeContext(interaction)
        await self._create_template_logic(ctx, description)

    @commands.command(name="roles", aliases=["roleinfo", "role-info"])
    async def describe_roles(self, ctx, role_name: str = None):
        """Describe server roles and their permissions"""
        await self._describe_roles_logic(ctx, role_name)

    async def _describe_roles_logic(self, ctx, role_name: str | None = None):
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
            
            embed.set_footer(text=f"Requested by {ctx.author.display_name}")
            await ctx.send(embed=embed)

    async def _create_template_logic(self, ctx, description: str | None = None):
        # Check bot permissions - more detailed checking
        bot_perms = ctx.guild.me.guild_permissions
        
        # Check essential permissions
        required_perms = {
            'manage_channels': bot_perms.manage_channels,
            'manage_roles': bot_perms.manage_roles,
            'administrator': bot_perms.administrator
        }

        missing_permissions = []
        for perm_name, has_perm in required_perms.items():
            if not has_perm:
                missing_permissions.append(perm_name.replace('_', ' ').title())

        if missing_permissions:
            # Create detailed error message with invite link
            error_msg = f"I'm missing required permissions to create the template.\n\n"
            error_msg += f"**Missing permissions:** {', '.join(missing_permissions)}\n\n"
            error_msg += "**Solutions:**\n"
            error_msg += "1. Give me **Administrator** permission (recommended)\n"
            error_msg += "2. Or re-invite me with this link:\n"
            error_msg += "https://discord.com/oauth2/authorize?client_id=1401261269432144045&permissions=8&integration_type=0&scope=bot\n\n"
            error_msg += "**Current permissions:** "
            current_perms = []
            if bot_perms.administrator: current_perms.append("Administrator")
            if bot_perms.manage_channels: current_perms.append("Manage Channels")  
            if bot_perms.manage_roles: current_perms.append("Manage Roles")
            if bot_perms.kick_members: current_perms.append("Kick Members")
            if bot_perms.ban_members: current_perms.append("Ban Members")
            
            error_msg += ", ".join(current_perms) if current_perms else "None of the required permissions"
            
            await ctx.send(embed=create_error_embed("❌ Missing Bot Permissions", error_msg))
            return

        

        # Send initial message
        status_msg = await ctx.send(embed=create_embed("🏗️ Template Creation", "Creating categories and channels..."))

        try:
            # Create roles if they don't exist (for appeal template)
            created_roles = {}
            
            # Check if this is an appeal template
            is_appeal_template = description and "appeal" in description.lower()
            
            if is_appeal_template:
                # Define roles for appeal template with specific permissions
                role_configs = {
                    "Owner": {"color": discord.Color.from_rgb(255, 0, 0), "permissions": discord.Permissions.all()},
                    "Co-Owner": {"color": discord.Color.from_rgb(255, 128, 0), "permissions": discord.Permissions.all()},
                    "Manager": {"color": discord.Color.from_rgb(255, 255, 0), "permissions": discord.Permissions.all()},
                    "Administrator": {"color": discord.Color.from_rgb(255, 0, 255), "permissions": discord.Permissions(
                        kick_members=True, ban_members=True, manage_channels=True, manage_guild=True,
                        manage_messages=True, manage_nicknames=True, manage_roles=True, manage_webhooks=True,
                        manage_emojis_and_stickers=True, view_audit_log=True, moderate_members=True
                    )},
                    "Moderator": {"color": discord.Color.from_rgb(0, 255, 0), "permissions": discord.Permissions(
                        kick_members=True, ban_members=True, manage_messages=True, manage_nicknames=True, 
                        moderate_members=True, view_audit_log=True
                    )}
                }
                
                # Create roles if they don't exist
                for role_name, config in role_configs.items():
                    existing_role = discord.utils.get(ctx.guild.roles, name=role_name)
                    if existing_role:
                        created_roles[role_name] = existing_role
                    else:
                        created_roles[role_name] = await ctx.guild.create_role(
                            name=role_name,
                            color=config["color"],
                            permissions=config["permissions"],
                            reason="Appeal template role creation"
                        )
                        await asyncio.sleep(0.5)  # Rate limit protection
            
            # Map existing roles in the server for non-appeal templates
            for role in ctx.guild.roles:
                if role.name not in created_roles:
                    created_roles[role.name] = role

            # Create categories and channels

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
                    if "Staff Only" in category_name or "Staff" in category_name:
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
                    full_channel_name = f"{emoji}{channel_name}"

                    # Check if channel already exists
                    existing_channel = discord.utils.get(category.channels, name=full_channel_name)
                    if existing_channel:
                        continue

                    # Set up channel permissions
                    overwrites = category.overwrites.copy()

                    # Special permissions for staff channels
                    if "Staff Only" in category_name or "Staff" in category_name:
                        if "moderator-chat" in channel_name:
                            # Only moderator+ can access
                            overwrites[ctx.guild.default_role] = discord.PermissionOverwrite(read_messages=False)
                            for role_name in ["Moderator", "Administrator", "Manager", "BOTS", "Co-Owner", "Owner"]:
                                if role_name in created_roles:
                                    overwrites[created_roles[role_name]] = discord.PermissionOverwrite(read_messages=True)
                        elif "administrator-chat" in channel_name:
                            # Only admin+ can access
                            overwrites[ctx.guild.default_role] = discord.PermissionOverwrite(read_messages=False)
                            for role_name in ["Administrator", "Manager", "BOTS", "Co-Owner", "Owner"]:
                                if role_name in created_roles:
                                    overwrites[created_roles[role_name]] = discord.PermissionOverwrite(read_messages=True)
                        elif "manager-chat" in channel_name or "manager-plus-chat" in channel_name:
                            # Only manager+ can access
                            overwrites[ctx.guild.default_role] = discord.PermissionOverwrite(read_messages=False)
                            for role_name in ["Manager", "BOTS", "Co-Owner", "Owner"]:
                                if role_name in created_roles:
                                    overwrites[created_roles[role_name]] = discord.PermissionOverwrite(read_messages=True)
                        elif "general-staff-chat" in channel_name or "system-logs" in channel_name:
                            # All staff can access
                            overwrites[ctx.guild.default_role] = discord.PermissionOverwrite(read_messages=False)
                            for role_name in ["Moderator", "Administrator", "Manager", "BOTS", "Co-Owner", "Owner"]:
                                if role_name in created_roles:
                                    overwrites[created_roles[role_name]] = discord.PermissionOverwrite(read_messages=True)

                    if channel_type == "text":
                        await ctx.guild.create_text_channel(
                            name=full_channel_name,
                            category=category,
                            overwrites=overwrites
                        )
                    elif channel_type == "voice":
                        await ctx.guild.create_voice_channel(
                            name=full_channel_name,
                            category=category,
                            overwrites=overwrites
                        )

                    await asyncio.sleep(0.5)  # Rate limit protection

            # Final completion message
            await status_msg.edit(embed=create_success_embed("✅ Template Creation", "Completed!"))

        except discord.Forbidden:
            await status_msg.edit(embed=create_error_embed("Error", "Sorry but my permission is not able to make the categorys, text channels, etc."))
        except discord.HTTPException as e:
            await status_msg.edit(embed=create_error_embed("Error", f"An error occurred while creating the template: {str(e)}"))
        except Exception as e:
            logger.error(f"Template creation error: {e}")
            await status_msg.edit(embed=create_error_embed("Error", "An unexpected error occurred during template creation."))

    def _get_template_structure(self, description: str | None = None):
        """Parse description and return custom template structure if applicable"""
        if not description:
            return None
            
        description = description.lower()
        
        # Check for special legacy templates first (must preserve existing behavior)
        if "appeal" in description or "appealing" in description:
            return [
                {
                    "category": "<==Staff==>",
                    "channels": [
                        ("💬", "general-staff-chat", "text"),
                        ("🛡️", "moderator-chat", "text"),
                        ("⚡", "administrator-chat", "text"),
                        ("👑", "manager-chat", "text"),
                        ("📊", "system-logs", "text")
                    ]
                },
                {
                    "category": "<==Information==>",
                    "channels": [
                        ("📢", "announcements", "text"),
                        ("👥", "staff-announcements", "text"),
                        ("📜", "appealing-rules", "text")
                    ]
                },
                {
                    "category": "<==Appeal Here!==>",
                    "channels": [
                        ("🎟️", "tickets", "text"),
                        ("⚖️", "appeal-command-ban", "text")
                    ]
                }
            ]
        
        # Use dynamic template engine for most descriptions
        template = self._generate_dynamic_template(description)
        if template:
            return template
        
        # Bot community template (fallback for compatibility)
        if "bot community" in description or "bot server" in description:
            return [
                {
                    "category": "📋 Information",
                    "channels": [
                        ("📜", "rules", "text"),
                        ("📢", "announcements", "text"),
                        ("🆕", "updates", "text"),
                        ("🎯", "events", "text"),
                        ("❓", "faq", "text")
                    ]
                },
                {
                    "category": "🤖 Bot Features",
                    "channels": [
                        ("💬", "general-chat", "text"),
                        ("🆘", "bot-support", "text"),
                        ("💡", "suggestions", "text"),
                        ("🐛", "bug-reports", "text"),
                        ("📝", "feedback", "text"),
                        ("🎮", "bot-commands", "text")
                    ]
                },
                {
                    "category": "🛠️ Development",
                    "channels": [
                        ("💻", "development-chat", "text"),
                        ("📊", "bot-status", "text"),
                        ("🔄", "change-logs", "text"),
                        ("🧪", "testing", "text"),
                        ("📚", "resources", "text")
                    ]
                },
                {
                    "category": "👥 Community",
                    "channels": [
                        ("🗨️", "general-discussion", "text"),
                        ("🎉", "celebrations", "text"),
                        ("💼", "partnerships", "text"),
                        ("🤝", "collaborations", "text"),
                        ("🎨", "showcase", "text")
                    ]
                },
                {
                    "category": "🔊 Voice Channels",
                    "channels": [
                        ("🔊", "general-voice", "voice"),
                        ("💻", "dev-voice", "voice"),
                        ("🎮", "gaming-voice", "voice"),
                        ("📞", "support-voice", "voice")
                    ]
                },
                {
                    "category": "⚙️ Staff Only",
                    "channels": [
                        ("📢", "staff-announcements", "text"),
                        ("💼", "staff-chat", "text"),
                        ("🔨", "moderation", "text"),
                        ("📊", "analytics", "text"),
                        ("🔊", "staff-voice", "voice")
                    ]
                }
            ]
        
        # Gaming-focused template
        elif "gaming" in description:
            return [
                {
                    "category": "🎮 Gaming Hub",
                    "channels": [
                        ("🎮", "general-gaming", "text"),
                        ("🏆", "tournaments", "text"),
                        ("📺", "streaming", "text"),
                        ("🎯", "lfg-looking-for-group", "text"),
                        ("🎮", "gaming-voice-1", "voice"),
                        ("🎮", "gaming-voice-2", "voice"),
                        ("🏆", "tournament-voice", "voice")
                    ]
                },
                {
                    "category": "🕹️ Game Specific",
                    "channels": [
                        ("🔫", "fps-games", "text"),
                        ("⚔️", "moba-games", "text"),
                        ("🏎️", "racing-games", "text"),
                        ("🎲", "indie-games", "text")
                    ]
                }
            ]
        
        # Staff Only template
        elif "staff only" in description or "staff-only" in description:
            return [
                {
                    "category": "👑 Executive",
                    "channels": [
                        ("👑", "owner-office", "text"),
                        ("💎", "co-owner-office", "text"),
                        ("⭐", "executive-meeting", "voice"),
                        ("📊", "executive-planning", "text"),
                        ("🔒", "private-discussions", "text")
                    ]
                },
                {
                    "category": "🏛️ Management",
                    "channels": [
                        ("⭐", "manager-headquarters", "text"),
                        ("💼", "management-meeting", "voice"),
                        ("📈", "performance-review", "text"),
                        ("🎯", "goal-setting", "text"),
                        ("📋", "task-assignment", "text")
                    ]
                },
                {
                    "category": "🛡️ Administration",
                    "channels": [
                        ("🛡️", "admin-control-room", "text"),
                        ("⚙️", "admin-meeting", "voice"),
                        ("🔧", "server-configuration", "text"),
                        ("📊", "analytics-review", "text"),
                        ("🔍", "audit-logs", "text")
                    ]
                },
                {
                    "category": "🔨 Moderation Center",
                    "channels": [
                        ("🔨", "moderation-hub", "text"),
                        ("👥", "mod-meeting", "voice"),
                        ("⚠️", "incident-reports", "text"),
                        ("📝", "mod-notes", "text"),
                        ("🚨", "urgent-alerts", "text"),
                        ("📚", "training-resources", "text")
                    ]
                },
                {
                    "category": "📞 Communication Hub",
                    "channels": [
                        ("💬", "all-staff-chat", "text"),
                        ("📢", "staff-announcements", "text"),
                        ("💡", "ideas-suggestions", "text"),
                        ("🎉", "staff-celebrations", "text"),
                        ("📞", "staff-voice-lobby", "voice"),
                        ("🔊", "staff-meeting-room", "voice")
                    ]
                },
                {
                    "category": "🔧 Operations",
                    "channels": [
                        ("🔧", "system-maintenance", "text"),
                        ("📈", "growth-metrics", "text"),
                        ("💰", "financial-overview", "text"),
                        ("📊", "weekly-reports", "text"),
                        ("🎯", "project-tracking", "text")
                    ]
                }
            ]
        
        return None

    @commands.command(name="temproles")
    @has_permissions(administrator=True)
    async def create_role_template(self, ctx, *, description: str = None):
        """Create a role template for the server (Administrator only). Use 'gaming', 'appeal', 'staff', or describe your own."""
        
        # Check bot permissions
        if not ctx.guild.me.guild_permissions.manage_roles:
            await ctx.send(embed=create_error_embed("Missing Permissions", "I need the 'Manage Roles' permission to create role templates."))
            return

        # Send initial status message
        status_msg = await ctx.send(embed=create_embed("🔄 Creating Role Template", "Starting role creation..."))

        try:
            # Get role template structure
            roles_structure = self._get_role_template_structure(description)
            
            if not roles_structure:
                await status_msg.edit(embed=create_error_embed("Unknown Template", "Unknown role template. Available templates: gaming, appeal, staff, community"))
                return

            # Update status
            await status_msg.edit(embed=create_embed("🔄 Creating Roles", f"Creating {len(roles_structure)} roles..."))

            created_roles = []
            
            for role_data in roles_structure:
                role_name = role_data["name"]
                role_color = role_data.get("color", 0x99AAB5)  # Default Discord gray
                role_permissions = role_data.get("permissions", discord.Permissions.none())
                role_hoist = role_data.get("hoist", False)
                role_mentionable = role_data.get("mentionable", True)

                # Check if role already exists
                existing_role = discord.utils.get(ctx.guild.roles, name=role_name)
                if existing_role:
                    continue

                # Create the role
                try:
                    new_role = await ctx.guild.create_role(
                        name=role_name,
                        color=discord.Color(role_color),
                        permissions=role_permissions,
                        hoist=role_hoist,
                        mentionable=role_mentionable
                    )
                    created_roles.append(new_role)
                    await asyncio.sleep(0.5)  # Rate limit protection
                    
                except discord.Forbidden:
                    continue
                except discord.HTTPException:
                    continue

            # Final completion message
            if created_roles:
                role_list = "\n".join([f"• {role.mention}" for role in created_roles])
                embed = create_success_embed(
                    "✅ Role Template Created",
                    f"Successfully created {len(created_roles)} roles:\n\n{role_list}"
                )
            else:
                embed = create_embed(
                    "ℹ️ No New Roles",
                    "All roles from this template already exist in the server."
                )
                
            await status_msg.edit(embed=embed)

        except discord.Forbidden:
            await status_msg.edit(embed=create_error_embed("Permission Error", "I don't have permission to create roles. Make sure my role is above the roles I'm trying to create."))
        except discord.HTTPException as e:
            await status_msg.edit(embed=create_error_embed("Discord Error", f"Discord API error: {str(e)}"))
        except Exception as e:
            logger.error(f"Role template creation error: {e}")
            await status_msg.edit(embed=create_error_embed("Error", "An unexpected error occurred during role template creation."))

    def _get_role_template_structure(self, description: str | None = None):
        """Get role template structure based on description"""
        if not description:
            description = "staff"
            
        description = description.lower()
        
        # Appeal server roles
        if "appeal" in description or "appealing" in description:
            return [
                {
                    "name": "Owner",
                    "color": 0xFF0000,  # Red
                    "permissions": discord.Permissions.all(),
                    "hoist": True,
                    "mentionable": True
                },
                {
                    "name": "Co-Owner", 
                    "color": 0xFF4500,  # Orange Red
                    "permissions": discord.Permissions.all(),
                    "hoist": True,
                    "mentionable": True
                },
                {
                    "name": "Manager",
                    "color": 0xFFD700,  # Gold
                    "permissions": discord.Permissions(administrator=True),
                    "hoist": True,
                    "mentionable": True
                },
                {
                    "name": "Administrator",
                    "color": 0x9932CC,  # Dark Orchid
                    "permissions": discord.Permissions(
                        kick_members=True, ban_members=True, manage_channels=True,
                        manage_guild=True, manage_messages=True, manage_roles=True,
                        view_audit_log=True, moderate_members=True
                    ),
                    "hoist": True,
                    "mentionable": True
                },
                {
                    "name": "Moderator",
                    "color": 0x00CED1,  # Dark Turquoise
                    "permissions": discord.Permissions(
                        kick_members=True, manage_messages=True, 
                        moderate_members=True, view_audit_log=True
                    ),
                    "hoist": True,
                    "mentionable": True
                }
            ]
            
        # Gaming server roles
        elif "gaming" in description or "game" in description or "gamer" in description:
            return [
                {
                    "name": "Server Owner",
                    "color": 0xFF0000,  # Red
                    "permissions": discord.Permissions.all(),
                    "hoist": True,
                    "mentionable": True
                },
                {
                    "name": "Admin",
                    "color": 0xFF4500,  # Orange Red
                    "permissions": discord.Permissions(administrator=True),
                    "hoist": True,
                    "mentionable": True
                },
                {
                    "name": "Moderator",
                    "color": 0x00CED1,  # Dark Turquoise
                    "permissions": discord.Permissions(
                        kick_members=True, manage_messages=True, moderate_members=True
                    ),
                    "hoist": True,
                    "mentionable": True
                },
                {
                    "name": "VIP",
                    "color": 0xFFD700,  # Gold
                    "permissions": discord.Permissions.none(),
                    "hoist": True,
                    "mentionable": True
                },
                {
                    "name": "Pro Gamer",
                    "color": 0x9932CC,  # Dark Orchid
                    "permissions": discord.Permissions.none(),
                    "hoist": False,
                    "mentionable": True
                },
                {
                    "name": "Gamer",
                    "color": 0x32CD32,  # Lime Green
                    "permissions": discord.Permissions.none(),
                    "hoist": False,
                    "mentionable": True
                },
                {
                    "name": "New Player",
                    "color": 0x87CEEB,  # Sky Blue
                    "permissions": discord.Permissions.none(),
                    "hoist": False,
                    "mentionable": True
                }
            ]
            
        # Staff roles template
        elif "staff" in description:
            return [
                {
                    "name": "Owner",
                    "color": 0xFF0000,  # Red
                    "permissions": discord.Permissions.all(),
                    "hoist": True,
                    "mentionable": True
                },
                {
                    "name": "Admin",
                    "color": 0xFF4500,  # Orange Red
                    "permissions": discord.Permissions(administrator=True),
                    "hoist": True,
                    "mentionable": True
                },
                {
                    "name": "Moderator",
                    "color": 0x00CED1,  # Dark Turquoise
                    "permissions": discord.Permissions(
                        kick_members=True, manage_messages=True, moderate_members=True
                    ),
                    "hoist": True,
                    "mentionable": True
                },
                {
                    "name": "Helper",
                    "color": 0x32CD32,  # Lime Green
                    "permissions": discord.Permissions.none(),
                    "hoist": True,
                    "mentionable": True
                }
            ]
            
        # Community server roles
        elif "community" in description:
            return [
                {
                    "name": "Server Owner",
                    "color": 0xFF0000,  # Red
                    "permissions": discord.Permissions.all(),
                    "hoist": True,
                    "mentionable": True
                },
                {
                    "name": "Admin",
                    "color": 0xFF4500,  # Orange Red
                    "permissions": discord.Permissions(administrator=True),
                    "hoist": True,
                    "mentionable": True
                },
                {
                    "name": "Moderator",
                    "color": 0x00CED1,  # Dark Turquoise
                    "permissions": discord.Permissions(
                        kick_members=True, manage_messages=True, moderate_members=True
                    ),
                    "hoist": True,
                    "mentionable": True
                },
                {
                    "name": "Active Member",
                    "color": 0xFFD700,  # Gold
                    "permissions": discord.Permissions.none(),
                    "hoist": False,
                    "mentionable": True
                },
                {
                    "name": "Member",
                    "color": 0x32CD32,  # Lime Green
                    "permissions": discord.Permissions.none(),
                    "hoist": False,
                    "mentionable": True
                },
                {
                    "name": "New Member",
                    "color": 0x87CEEB,  # Sky Blue
                    "permissions": discord.Permissions.none(),
                    "hoist": False,
                    "mentionable": True
                }
            ]
        
        # Default to staff template
        return [
            {
                "name": "Owner",
                "color": 0xFF0000,  # Red
                "permissions": discord.Permissions.all(),
                "hoist": True,
                "mentionable": True
            },
            {
                "name": "Admin",
                "color": 0xFF4500,  # Orange Red
                "permissions": discord.Permissions(administrator=True),
                "hoist": True,
                "mentionable": True
            },
            {
                "name": "Moderator",
                "color": 0x00CED1,  # Dark Turquoise
                "permissions": discord.Permissions(
                    kick_members=True, manage_messages=True, moderate_members=True
                ),
                "hoist": True,
                "mentionable": True
            }
        ]

    def _generate_dynamic_template(self, description: str):
        """Generate template structure dynamically based on description"""
        # Parse tags from description
        tags = self._parse_description_tags(description)
        if not tags:
            return None
            
        # Build template from blocks
        template_blocks = []
        
        # Add relevant blocks based on tags
        for tag in tags:
            block = self._get_template_block(tag)
            if block:
                template_blocks.extend(block)
                
        # Add base information block if not present
        has_info_block = any(
            block.get("category", "").lower().find("information") != -1 or 
            block.get("category", "").lower().find("info") != -1 
            for block in template_blocks
        )
        if not has_info_block:
            template_blocks.insert(0, self._get_info_block())
            
        # Add voice channels if server type suggests it
        if any(tag in ["gaming", "music", "community", "hangout"] for tag in tags):
            template_blocks.append(self._get_voice_block())
            
        return template_blocks if template_blocks else None
        
    def _parse_description_tags(self, description: str):
        """Parse description to extract relevant tags"""
        tags = []
        description = description.lower()
        
        # Define tag mappings
        tag_mappings = {
            "memes": ["meme", "memes", "funny", "humor", "dank"],
            "gaming": ["gaming", "game", "games", "gamer", "esports", "clan", "guild"],
            "art": ["art", "artist", "drawing", "creative", "design", "artwork"],
            "music": ["music", "musician", "band", "audio", "sound", "beat"],
            "coding": ["coding", "programming", "dev", "developer", "tech", "code"],
            "study": ["study", "education", "learning", "school", "homework", "tutoring"],
            "anime": ["anime", "manga", "weeb", "otaku", "japanese"],
            "community": ["community", "social", "hangout", "chat", "friends"],
            "support": ["support", "help", "assistance", "ticket", "customer"],
            "trading": ["trading", "marketplace", "buy", "sell", "economy"],
            "roleplay": ["rp", "roleplay", "role-play", "character", "story"],
            "fitness": ["fitness", "gym", "workout", "health", "exercise"],
            "cooking": ["cooking", "food", "recipe", "chef", "kitchen"],
            "photography": ["photo", "photography", "camera", "pictures", "shots"],
            "streaming": ["stream", "streaming", "twitch", "youtube", "content"]
        }
        
        # Find matching tags
        for tag, keywords in tag_mappings.items():
            if any(keyword in description for keyword in keywords):
                tags.append(tag)
                
        return tags[:3]  # Limit to 3 main tags to avoid overcomplexity
        
    def _get_template_block(self, tag: str):
        """Get template block for specific tag"""
        blocks = {
            "memes": [
                {
                    "category": "🎭 Meme Central",
                    "channels": [
                        ("😂", "memes", "text"),
                        ("📤", "meme-submissions", "text"),
                        ("🔥", "best-memes", "text"),
                        ("🎨", "meme-templates", "text"),
                        ("💬", "meme-discussion", "text")
                    ]
                }
            ],
            "gaming": [
                {
                    "category": "🎮 Gaming",
                    "channels": [
                        ("🎯", "game-chat", "text"),
                        ("👥", "looking-for-group", "text"),
                        ("🏆", "achievements", "text"),
                        ("📊", "leaderboards", "text"),
                        ("💭", "game-discussion", "text")
                    ]
                }
            ],
            "art": [
                {
                    "category": "🎨 Art Gallery",
                    "channels": [
                        ("🖼️", "artwork-showcase", "text"),
                        ("✏️", "work-in-progress", "text"),
                        ("💬", "art-critique", "text"),
                        ("📚", "resources-tutorials", "text"),
                        ("💰", "commissions", "text")
                    ]
                }
            ],
            "music": [
                {
                    "category": "🎵 Music",
                    "channels": [
                        ("🎶", "music-sharing", "text"),
                        ("🎤", "original-music", "text"),
                        ("💬", "music-discussion", "text"),
                        ("🎧", "now-playing", "text"),
                        ("🤝", "collaborations", "text")
                    ]
                }
            ],
            "coding": [
                {
                    "category": "💻 Programming",
                    "channels": [
                        ("💬", "general-coding", "text"),
                        ("❓", "help-support", "text"),
                        ("📂", "project-showcase", "text"),
                        ("📚", "resources", "text"),
                        ("🐛", "code-review", "text")
                    ]
                }
            ],
            "study": [
                {
                    "category": "📚 Study Zone",
                    "channels": [
                        ("📖", "study-chat", "text"),
                        ("❓", "homework-help", "text"),
                        ("📋", "study-resources", "text"),
                        ("👥", "study-groups", "text"),
                        ("🏆", "achievements", "text")
                    ]
                }
            ],
            "anime": [
                {
                    "category": "🌸 Anime & Manga",
                    "channels": [
                        ("💬", "anime-discussion", "text"),
                        ("📚", "manga-talk", "text"),
                        ("⭐", "recommendations", "text"),
                        ("📺", "currently-watching", "text"),
                        ("🎨", "fanart", "text")
                    ]
                }
            ],
            "community": [
                {
                    "category": "👥 Community",
                    "channels": [
                        ("💬", "general-chat", "text"),
                        ("🎉", "introductions", "text"),
                        ("📷", "selfies-pics", "text"),
                        ("🎮", "activities", "text"),
                        ("💭", "random-thoughts", "text")
                    ]
                }
            ],
            "support": [
                {
                    "category": "🛠️ Support",
                    "channels": [
                        ("🎫", "create-ticket", "text"),
                        ("❓", "general-help", "text"),
                        ("📚", "faq", "text"),
                        ("📢", "announcements", "text"),
                        ("💡", "suggestions", "text")
                    ]
                }
            ],
            "trading": [
                {
                    "category": "💰 Trading",
                    "channels": [
                        ("💵", "marketplace", "text"),
                        ("📈", "trading-discussion", "text"),
                        ("🤝", "deals", "text"),
                        ("⚖️", "middleman-services", "text"),
                        ("📋", "price-check", "text")
                    ]
                }
            ]
        }
        
        return blocks.get(tag, [])
        
    def _get_info_block(self):
        """Get standard information block"""
        return {
            "category": "📋 Information",
            "channels": [
                ("📜", "rules", "text"),
                ("📢", "announcements", "text"),
                ("👋", "welcome", "text")
            ]
        }
        
    def _get_voice_block(self):
        """Get voice channels block"""
        return {
            "category": "🔊 Voice Channels",
            "channels": [
                ("🎤", "general-voice", "voice"),
                ("🎮", "gaming-voice", "voice"),
                ("🎵", "music-lounge", "voice"),
                ("💼", "private-room", "voice")
            ]
        }

async def setup(bot):
    await bot.add_cog(TemplateCog(bot))
