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
    @has_permissions(administrator=True)
    async def create_template(self, ctx, *, description: str = None):
        """Create a server template with categories, channels, and roles"""
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

    async def _create_template_logic(self, ctx, description: str = None):
        # Check bot permissions
        required_permissions = [
            'manage_channels', 'manage_roles', 'administrator'
        ]

        missing_permissions = []
        for perm in required_permissions:
            if not getattr(ctx.guild.me.guild_permissions, perm, False):
                missing_permissions.append(perm.replace('_', ' ').title())

        if missing_permissions:
            error_msg = f"Sorry but my permission is not able to make the categorys, text channels, etc.\n\nMissing permissions: {', '.join(missing_permissions)}"
            await ctx.send(embed=create_error_embed("Insufficient Permissions", error_msg))
            return

        # Send initial message
        status_msg = await ctx.send(embed=create_embed("🏗️ Template Creation", "Creating Categorys..."))

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
                    full_channel_name = f"{emoji}{channel_name}"

                    # Check if channel already exists
                    existing_channel = discord.utils.get(category.channels, name=full_channel_name)
                    if existing_channel:
                        continue

                    # Set up channel permissions
                    overwrites = category.overwrites.copy()

                    # Special permissions for staff channels
                    if "Staff Only" in category_name:
                        if "moderator-chat" in channel_name:
                            # Only moderator+ can access
                            for role_name in ["Moderator", "Administrator", "Manager", "BOTS", "Co-Owner", "Owner"]:
                                if role_name in created_roles:
                                    overwrites[created_roles[role_name]] = discord.PermissionOverwrite(read_messages=True)
                        elif "administrator-chat" in channel_name:
                            # Only admin+ can access
                            for role_name in ["Administrator", "Manager", "BOTS", "Co-Owner", "Owner"]:
                                if role_name in created_roles:
                                    overwrites[created_roles[role_name]] = discord.PermissionOverwrite(read_messages=True)
                        elif "manager-plus-chat" in channel_name:
                            # Only manager+ can access
                            for role_name in ["Manager", "BOTS", "Co-Owner", "Owner"]:
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
            logger.error(f"HTTP Exception during template creation: {e}")
            await status_msg.edit(embed=create_error_embed("Error", f"An error occurred during template creation: {e}"))
        except Exception as e:
            logger.error(f"Error creating template: {e}")
            await status_msg.edit(embed=create_error_embed("Error", f"An unexpected error occurred: {e}"))

    def _get_template_structure(self, description: str = None):
        """Generate template structure based on description"""
        if not description:
            return None  # Use default template

        description_lower = description.lower()

        # Gaming template
        if any(word in description_lower for word in ["gaming", "game", "gamer", "esports", "tournament"]):
            return [
                {
                    "category": "📋 Information",
                    "channels": [
                        ("📜", "rules", "text"),
                        ("📢", "announcements", "text"),
                        ("🎮", "game-updates", "text"),
                        ("🏆", "tournaments", "text")
                    ]
                },
                {
                    "category": "💬 General",
                    "channels": [
                        ("🗨️", "general-chat", "text"),
                        ("👋", "introductions", "text"),
                        ("🎮", "game-discussion", "text"),
                        ("🏆", "achievements", "text")
                    ]
                },
                {
                    "category": "🎮 Gaming",
                    "channels": [
                        ("🎯", "looking-for-group", "text"),
                        ("🎪", "game-reviews", "text"),
                        ("📺", "streams-and-videos", "text"),
                        ("🎮", "gaming-voice-1", "voice"),
                        ("🎮", "gaming-voice-2", "voice"),
                        ("🏆", "tournament-voice", "voice")
                    ]
                },
                {
                    "category": "🛠️ Staff Only",
                    "channels": [
                        ("📢", "staff-announcements", "text"),
                        ("💼", "staff-chat", "text"),
                        ("🔧", "admin-tools", "text"),
                        ("🔊", "staff-voice", "voice")
                    ]
                }
            ]

        # Study/Education template
        elif any(word in description_lower for word in ["study", "education", "school", "learning", "homework", "university", "college"]):
            return [
                {
                    "category": "📚 Information",
                    "channels": [
                        ("📜", "rules-and-guidelines", "text"),
                        ("📢", "announcements", "text"),
                        ("📅", "study-schedule", "text"),
                        ("ℹ️", "resources", "text")
                    ]
                },
                {
                    "category": "💬 General",
                    "channels": [
                        ("🗨️", "general-chat", "text"),
                        ("👋", "introductions", "text"),
                        ("🎉", "achievements", "text"),
                        ("☕", "break-room", "text")
                    ]
                },
                {
                    "category": "📖 Study",
                    "channels": [
                        ("📝", "homework-help", "text"),
                        ("🤝", "study-groups", "text"),
                        ("📚", "subject-discussion", "text"),
                        ("❓", "questions-and-answers", "text"),
                        ("📞", "study-voice-1", "voice"),
                        ("📞", "study-voice-2", "voice"),
                        ("🎧", "silent-study", "voice")
                    ]
                },
                {
                    "category": "👨‍🏫 Staff Only",
                    "channels": [
                        ("📢", "staff-announcements", "text"),
                        ("💼", "staff-discussion", "text"),
                        ("🔊", "staff-voice", "voice")
                    ]
                }
            ]

        # Business/Professional template
        elif any(word in description_lower for word in ["business", "professional", "work", "company", "corporate", "team"]):
            return [
                {
                    "category": "📋 Company Info",
                    "channels": [
                        ("📜", "company-policies", "text"),
                        ("📢", "announcements", "text"),
                        ("📰", "news-and-updates", "text"),
                        ("🎯", "goals-and-objectives", "text")
                    ]
                },
                {
                    "category": "💼 General",
                    "channels": [
                        ("💬", "general-discussion", "text"),
                        ("👋", "introductions", "text"),
                        ("🎉", "celebrations", "text"),
                        ("💡", "ideas-and-suggestions", "text")
                    ]
                },
                {
                    "category": "🏢 Work",
                    "channels": [
                        ("📊", "project-updates", "text"),
                        ("🤝", "collaboration", "text"),
                        ("❓", "help-and-support", "text"),
                        ("📞", "meeting-room-1", "voice"),
                        ("📞", "meeting-room-2", "voice"),
                        ("💼", "private-office", "voice")
                    ]
                },
                {
                    "category": "👔 Management",
                    "channels": [
                        ("📢", "management-announcements", "text"),
                        ("💼", "management-chat", "text"),
                        ("📊", "reports-and-analytics", "text"),
                        ("🔊", "management-voice", "voice")
                    ]
                }
            ]

        # Art/Creative template
        elif any(word in description_lower for word in ["art", "creative", "design", "drawing", "painting", "music", "artist"]):
            return [
                {
                    "category": "ℹ️ Information",
                    "channels": [
                        ("📜", "community-rules", "text"),
                        ("📢", "announcements", "text"),
                        ("🎨", "featured-artwork", "text"),
                        ("📅", "events-and-challenges", "text")
                    ]
                },
                {
                    "category": "💬 Community",
                    "channels": [
                        ("🗨️", "general-chat", "text"),
                        ("👋", "introductions", "text"),
                        ("💡", "inspiration", "text"),
                        ("🤝", "collaborations", "text")
                    ]
                },
                {
                    "category": "🎨 Creative",
                    "channels": [
                        ("🖼️", "artwork-showcase", "text"),
                        ("💬", "art-feedback", "text"),
                        ("🎵", "music-sharing", "text"),
                        ("📚", "tutorials-and-resources", "text"),
                        ("🎨", "creative-voice-1", "voice"),
                        ("🎵", "music-voice", "voice"),
                        ("🎧", "chill-creative", "voice")
                    ]
                },
                {
                    "category": "🛠️ Staff Only",
                    "channels": [
                        ("📢", "staff-announcements", "text"),
                        ("💼", "staff-chat", "text"),
                        ("🔊", "staff-voice", "voice")
                    ]
                }
            ]

        # Return None for default template if no match
        return None

async def setup(bot):
    await bot.add_cog(TemplateCog(bot))