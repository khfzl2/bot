import discord
from discord.ext import commands
from discord import app_commands
import logging
from datetime import datetime, timedelta
from ..utils import create_embed, create_error_embed, create_success_embed, has_permissions, is_bot_owner, is_super_admin

logger = logging.getLogger(__name__)

def is_kh2_official(ctx):
    """Check if user is one of the bot owners"""
    return is_bot_owner(ctx.author)

def kh2_only():
    """Decorator to restrict commands to bot owners only"""
    def predicate(ctx):
        return is_kh2_official(ctx)
    return commands.check(predicate)

class ModerationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send_moderation_dm(self, user, action: str, moderator, reason: str, guild, duration: str = None):
        """Send standardized moderation DM to user"""
        try:
            # Get appeal ban link for server bans only (not command bans)
            appeal_text = ""
            if action.lower() == "ban" and self.bot.database:
                appeal_link = await self.bot.database.get_appeal_ban_link(guild.id)
                if appeal_link:
                    appeal_text = f"\n\n**Appeal:** You can appeal at: {appeal_link}"
                else:
                    appeal_text = "\n\n**Appeal:** Contact server administrators to appeal this action."

            # Format action display
            action_display = action
            if action.lower() == "timeout" and duration:
                action_display = f"Timeout ({duration})"

            # Create embed
            dm_embed = create_embed(
                f"🚫 Moderation Action - {action.title()}",
                f"**Action:** {action_display}\n"
                f"**Moderator:** {moderator} ({moderator.mention})\n"
                f"**Reason:** {reason}\n"
                f"**Server:** {guild.name}{appeal_text}"
            )
            await user.send(embed=dm_embed)
        except discord.Forbidden:
            pass  # User has DMs disabled

    @commands.command(name="kick")
    @has_permissions(kick_members=True)
    async def kick_member(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Kick a member from the server"""
        if member.id == ctx.author.id:
            await ctx.send(embed=create_error_embed("Error", "You cannot kick yourself!"))
            return

        if member.top_role >= ctx.author.top_role:
            await ctx.send(embed=create_error_embed("Error", "You cannot kick someone with a higher or equal role!"))
            return

        try:
            # Send DM before kicking using standardized format
            await self.send_moderation_dm(member, "Kick", ctx.author, reason, ctx.guild)

            await member.kick(reason=f"{reason} - Kicked by {ctx.author}")

            # Log to database
            if self.bot.database:
                await self.bot.database.add_moderation_log(
                    ctx.guild.id, member.id, ctx.author.id, "kick", reason
                )

            embed = create_success_embed("Member Kicked", f"{member.mention} has been kicked.\n**Reason:** {reason}")
            await ctx.send(embed=embed)

            # Send to modlog channel
            await self.send_modlog(ctx.guild, "kick", ctx.author, member, reason)

        except discord.Forbidden:
            await ctx.send(embed=create_error_embed("Error", "I don't have permission to kick this member."))

    @commands.command(name="ban")
    @has_permissions(ban_members=True)
    async def ban_member(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Ban a member from the server"""
        if member.id == ctx.author.id:
            await ctx.send(embed=create_error_embed("Error", "You cannot ban yourself!"))
            return

        if member.top_role >= ctx.author.top_role:
            await ctx.send(embed=create_error_embed("Error", "You cannot ban someone with a higher or equal role!"))
            return

        try:
            # Send DM before banning using standardized format
            await self.send_moderation_dm(member, "Ban", ctx.author, reason, ctx.guild)

            await member.ban(reason=f"{reason} - Banned by {ctx.author}")

            # Log to database
            if self.bot.database:
                await self.bot.database.add_moderation_log(
                    ctx.guild.id, member.id, ctx.author.id, "ban", reason
                )

            embed = create_success_embed("Member Banned", f"{member.mention} has been banned.\n**Reason:** {reason}")
            await ctx.send(embed=embed)

            # Send to modlog channel
            await self.send_modlog(ctx.guild, "ban", ctx.author, member, reason)

        except discord.Forbidden:
            await ctx.send(embed=create_error_embed("Error", "I don't have permission to ban this member."))

    @commands.command(name="unban")
    @has_permissions(ban_members=True)
    async def unban_member(self, ctx, user_id: int, *, reason: str = "No reason provided"):
        """Unban a user from the server"""
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user, reason=f"{reason} - Unbanned by {ctx.author}")

            # Log to database
            if self.bot.database:
                await self.bot.database.add_moderation_log(
                    ctx.guild.id, user.id, ctx.author.id, "unban", reason
                )

            # Send DM after unbanning using standardized format
            await self.send_moderation_dm(user, "Unban", ctx.author, reason, ctx.guild)

            embed = create_success_embed("User Unbanned", f"{user.mention} has been unbanned.\n**Reason:** {reason}")
            await ctx.send(embed=embed)

            # Send to modlog channel
            await self.send_modlog(ctx.guild, "unban", ctx.author, user, reason)

        except discord.NotFound:
            await ctx.send(embed=create_error_embed("Error", "User not found or not banned."))

    @commands.command(name="purge", aliases=["clear"])
    @has_permissions(manage_messages=True)
    async def purge_messages(self, ctx, amount: int = 10, member: discord.Member = None):
        """Delete multiple messages at once"""
        # Safety limits
        if amount < 1:
            await ctx.send(embed=create_error_embed("Invalid Amount", "Amount must be at least 1."))
            return

        if amount > 100:
            await ctx.send(embed=create_error_embed("Too Many Messages", "Cannot purge more than 100 messages at once."))
            return

        # Check bot permissions
        if not ctx.channel.permissions_for(ctx.guild.me).manage_messages:
            await ctx.send(embed=create_error_embed("Missing Permissions", "I don't have permission to manage messages in this channel."))
            return

        try:
            # Delete the command message first
            await ctx.message.delete()

            if member:
                # Purge messages from specific member
                def check(message):
                    return message.author == member
                deleted = await ctx.channel.purge(limit=amount, check=check)
            else:
                # Purge any messages
                deleted = await ctx.channel.purge(limit=amount)

            # Send confirmation message that will auto-delete
            if member:
                embed = create_success_embed(
                    "🧹 Messages Purged",
                    f"Deleted **{len(deleted)}** messages from {member.mention}."
                )
            else:
                embed = create_success_embed(
                    "🧹 Messages Purged", 
                    f"Deleted **{len(deleted)}** messages."
                )

            embed.set_footer(text=f"Purged by {ctx.author.display_name}")
            confirmation = await ctx.send(embed=embed)

            # Log the action
            if self.bot.database:
                action_desc = f"Purged {len(deleted)} messages" + (f" from {member}" if member else "")
                await self.bot.database.add_moderation_log(
                    ctx.guild.id, member.id if member else ctx.author.id, ctx.author.id, "purge", action_desc
                )

            # Auto-delete confirmation after 5 seconds
            await confirmation.delete(delay=5)

            # Send to modlog channel
            if member:
                await self.send_modlog(ctx.guild, "purge", ctx.author, member, action_desc)
            else:
                await self.send_modlog(ctx.guild, "purge", ctx.author, ctx.channel, action_desc)

        except discord.Forbidden:
            await ctx.send(embed=create_error_embed("Permission Error", "I don't have permission to delete messages."))
        except discord.HTTPException as e:
            await ctx.send(embed=create_error_embed("Error", f"Failed to purge messages: {str(e)}"))
        except discord.Forbidden:
            await ctx.send(embed=create_error_embed("Error", "I don't have permission to unban users."))

    @commands.command(name="setuplogs")
    @has_permissions(administrator=True)
    async def setup_logs(self, ctx, channel: discord.TextChannel = None):
        """Set up moderation logs channel"""
        if not channel:
            # Show current log channel
            current_channel_id = await self.bot.database.get_modlog_channel(ctx.guild.id)
            if current_channel_id:
                current_channel = ctx.guild.get_channel(current_channel_id)
                if current_channel:
                    embed = create_embed("Current Log Channel", f"Moderation logs are sent to: {current_channel.mention}")
                else:
                    embed = create_error_embed("Invalid Channel", "The configured log channel no longer exists. Please set a new one.")
            else:
                embed = create_embed("No Log Channel", "No moderation log channel is currently configured.\nUse `k!setuplogs #channel` to set one.")
            await ctx.send(embed=embed)
            return

        # Check if bot can send messages to the channel
        if not channel.permissions_for(ctx.guild.me).send_messages:
            await ctx.send(embed=create_error_embed("Missing Permissions", "I don't have permission to send messages in that channel."))
            return

        # Set the log channel
        await self.bot.database.set_modlog_channel(ctx.guild.id, channel.id)

        embed = create_success_embed(
            "📋 Moderation Logs Setup Complete",
            f"**Log Channel:** {channel.mention}\n\n"
            f"All moderation actions (bans, kicks, timeouts, etc.) will now be logged to this channel."
        )
        await ctx.send(embed=embed)

    async def send_modlog(self, guild, action, moderator, target, reason, extra_info=""):
        """Send a log message to the configured modlog channel"""
        modlog_channel_id = await self.bot.database.get_modlog_channel(guild.id)
        if not modlog_channel_id:
            return

        modlog_channel = guild.get_channel(modlog_channel_id)
        if not modlog_channel:
            return

        # Create log embed
        action_emojis = {
            "kick": "👢",
            "ban": "🔨", 
            "unban": "✅",
            "timeout": "⏰",
            "untimeout": "🔓",
            "purge": "🧹",
            "warn": "⚠️"
        }

        action_colors = {
            "kick": discord.Color.orange(),
            "ban": discord.Color.red(),
            "unban": discord.Color.green(),
            "timeout": discord.Color.yellow(),
            "untimeout": discord.Color.blue(),
            "purge": discord.Color.purple(),
            "warn": discord.Color.gold()
        }

        emoji = action_emojis.get(action, "📝")
        color = action_colors.get(action, discord.Color.blue())

        embed = discord.Embed(
            title=f"{emoji} Moderation Action: {action.title()}",
            color=color,
            timestamp=datetime.now()
        )

        if hasattr(target, 'mention'):
            embed.add_field(name="Target", value=f"{target.mention}\n`{target}` (ID: {target.id})", inline=True)
        else:
            embed.add_field(name="Target", value=f"`{target}`", inline=True)

        embed.add_field(name="Moderator", value=f"{moderator.mention}\n`{moderator}` (ID: {moderator.id})", inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)

        if extra_info:
            embed.add_field(name="Additional Info", value=extra_info, inline=False)

        try:
            await modlog_channel.send(embed=embed)
        except discord.Forbidden:
            pass  # No permission to send to log channel

    @commands.command(name="timeout", aliases=["mute"])
    @has_permissions(moderate_members=True)
    async def timeout_member(self, ctx, member: discord.Member, duration: str = "10m", *, reason: str = "No reason provided"):
        """Timeout a member for a specified duration"""
        if member.id == ctx.author.id:
            await ctx.send(embed=create_error_embed("Error", "You cannot timeout yourself!"))
            return

        if member.top_role >= ctx.author.top_role:
            await ctx.send(embed=create_error_embed("Error", "You cannot timeout someone with a higher or equal role!"))
            return

        # Parse duration
        try:
            if duration.endswith('s'):
                seconds = int(duration[:-1])
            elif duration.endswith('m'):
                seconds = int(duration[:-1]) * 60
            elif duration.endswith('h'):
                seconds = int(duration[:-1]) * 3600
            elif duration.endswith('d'):
                seconds = int(duration[:-1]) * 86400
            else:
                seconds = int(duration) * 60  # Default to minutes

            if seconds > 2419200:  # 28 days max
                await ctx.send(embed=create_error_embed("Error", "Timeout duration cannot exceed 28 days."))
                return

            timeout_until = datetime.now() + timedelta(seconds=seconds)

        except ValueError:
            await ctx.send(embed=create_error_embed("Error", "Invalid duration format. Use: 10s, 5m, 2h, 1d"))
            return

        try:
            # Send DM before timing out using standardized format
            await self.send_moderation_dm(member, "Timeout", ctx.author, reason, ctx.guild, duration)

            await member.timeout(timeout_until, reason=f"{reason} - Timed out by {ctx.author}")

            # Log to database
            if self.bot.database:
                await self.bot.database.add_moderation_log(
                    ctx.guild.id, member.id, ctx.author.id, "timeout", f"{reason} (Duration: {duration})"
                )

            embed = create_success_embed("Member Timed Out", f"{member.mention} has been timed out for {duration}.\n**Reason:** {reason}")
            await ctx.send(embed=embed)

            # Send to modlog channel
            await self.send_modlog(ctx.guild, "timeout", ctx.author, member, reason, f"Duration: {duration}")

        except discord.Forbidden:
            await ctx.send(embed=create_error_embed("Error", "I don't have permission to timeout this member."))

    @commands.command(name="untimeout", aliases=["unmute"])
    @has_permissions(moderate_members=True)
    async def untimeout_member(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Remove timeout from a member"""
        try:
            await member.timeout(None, reason=f"{reason} - Timeout removed by {ctx.author}")

            # Log to database
            if self.bot.database:
                await self.bot.database.add_moderation_log(
                    ctx.guild.id, member.id, ctx.author.id, "untimeout", reason
                )

            # Send DM after removing timeout using standardized format
            await self.send_moderation_dm(member, "Timeout Removed", ctx.author, reason, ctx.guild)

            embed = create_success_embed("Timeout Removed", f"{member.mention}'s timeout has been removed.\n**Reason:** {reason}")
            await ctx.send(embed=embed)

            # Send to modlog channel
            await self.send_modlog(ctx.guild, "untimeout", ctx.author, member, reason)

        except discord.Forbidden:
            await ctx.send(embed=create_error_embed("Error", "I don't have permission to remove timeout from this member."))

    @commands.command(name="warn")
    @has_permissions(moderate_members=True)
    async def warn_member(self, ctx, member: discord.Member, *, reason: str = "No reason provided"):
        """Warn a member"""
        if member.id == ctx.author.id:
            await ctx.send(embed=create_error_embed("Error", "You cannot warn yourself!"))
            return

        if member.top_role >= ctx.author.top_role:
            await ctx.send(embed=create_error_embed("Error", "You cannot warn someone with a higher or equal role!"))
            return

        try:
            # Send DM notification using standardized format
            await self.send_moderation_dm(member, "Warn", ctx.author, reason, ctx.guild)

            # Log to database
            if self.bot.database:
                await self.bot.database.add_moderation_log(
                    ctx.guild.id, member.id, ctx.author.id, "warn", reason
                )

            embed = create_success_embed("Member Warned", f"{member.mention} has been warned.\n**Reason:** {reason}")
            await ctx.send(embed=embed)

            # Send to modlog channel
            await self.send_modlog(ctx.guild, "warn", ctx.author, member, reason)

        except discord.Forbidden:
            await ctx.send(embed=create_error_embed("Error", "I don't have permission to warn this member."))

    @commands.command(name="addappealbanlink")
    @has_permissions(administrator=True)
    async def add_appeal_ban_link(self, ctx, *, link: str = None):
        """Set custom appeal server link for ban appeals"""
        if not link:
            # Show current appeal ban link
            if self.bot.database:
                current_link = await self.bot.database.get_appeal_ban_link(ctx.guild.id)
                if current_link:
                    embed = create_embed("Current Appeal Ban Link", f"Users banned from this server can appeal at: {current_link}")
                else:
                    embed = create_embed("No Appeal Ban Link Set", "No custom appeal link is currently configured for server bans.\nUse `k!addappealbanlink <link>` to set one.")
            else:
                embed = create_error_embed("Database Error", "Unable to check appeal ban link.")
            await ctx.send(embed=embed)
            return

        # Set the appeal ban link
        if self.bot.database:
            await self.bot.database.set_appeal_ban_link(ctx.guild.id, link)
            embed = create_success_embed(
                "📋 Appeal Ban Link Updated",
                f"**Appeal Link:** {link}\n\n"
                f"Users banned from this server will now be told they can appeal at this link."
            )
        else:
            embed = create_error_embed("Database Error", "Unable to set appeal ban link.")

        await ctx.send(embed=embed)



    @app_commands.command(name="appealcommandban", description="Appeal your command ban")
    async def appeal_command_ban(self, interaction: discord.Interaction, reason: str):
        """Allow users to appeal their command ban"""
        if self.bot.database:
            # Check for both server and global command bans
            restriction = await self.bot.database.get_command_restriction(interaction.guild.id, interaction.user.id)
            if not restriction or restriction["type"] != "command_ban":
                await interaction.response.send_message(
                    embed=create_error_embed("No Ban Found", "You are not currently banned from using commands."),
                    ephemeral=True
                )
                return

            # Check appeal cooldown
            can_appeal, remaining_time = await self.bot.database.check_appeal_cooldown(interaction.guild.id, interaction.user.id)
            if not can_appeal:
                minutes = int(remaining_time // 60)
                seconds = int(remaining_time % 60)
                await interaction.response.send_message(
                    embed=create_error_embed(
                        "Appeal Cooldown", 
                        f"You must wait {minutes} minutes and {seconds} seconds before appealing again."
                    ),
                    ephemeral=True
                )
                return

        # Send confirmation to user
        embed = create_embed(
            "Appeal Submitted", 
            f"Your appeal has been submitted with reason: {reason}\n"
            "A staff member will review your case."
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

        # DM bot owners and admin users about the appeal
        try:
            # Find bot owner users
            owner_users = []
            for guild in self.bot.guilds:
                for member in guild.members:
                    if is_bot_owner(member):
                        owner_users.append(member)

            # Get all admin users
            admin_users = []
            if self.bot.database:
                admin_list = await self.bot.database.get_all_admin_users()
                for admin_data in admin_list:
                    admin_id = admin_data[0]
                    try:
                        admin_user = await self.bot.fetch_user(admin_id)
                        if admin_user:
                            admin_users.append(admin_user)
                    except:
                        pass

            appeal_embed = create_embed(
                "🚨 Command Ban Appeal",
                f"**User:** {interaction.user.mention} ({interaction.user})\n"
                f"**User ID:** {interaction.user.id}\n"
                f"**Server:** {interaction.guild.name}\n"
                f"**Server ID:** {interaction.guild.id}\n"
                f"**Reason:** {reason}\n\n"
                "React with ✅ to unban or ❌ to deny the appeal."
            )

            # Send to bot owners
            for owner_user in owner_users:
                try:
                    appeal_message = await owner_user.send(embed=appeal_embed)
                    # Add reactions for approval/denial
                    await appeal_message.add_reaction("✅")
                    await appeal_message.add_reaction("❌")
                except discord.Forbidden:
                    pass

            # Send to all admin users
            for admin_user in admin_users:
                try:
                    appeal_message = await admin_user.send(embed=appeal_embed)
                    # Add reactions for approval/denial
                    await appeal_message.add_reaction("✅")
                    await appeal_message.add_reaction("❌")
                except discord.Forbidden:
                    pass

        except Exception as e:
            logger.error(f"Error sending appeal notifications: {e}")
            pass

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Handle reactions on appeal messages"""
        # Check if user is a bot owner or an admin, and if it's in DMs
        is_authorized = False
        if is_bot_owner(user):
            is_authorized = True
        elif self.bot.database:
            is_authorized = await self.bot.database.is_admin_user(user.id)

        if not is_authorized or not isinstance(reaction.message.channel, discord.DMChannel):
            return

        # Check if it's a reaction on an appeal message
        if not reaction.message.embeds:
            return

        embed = reaction.message.embeds[0]
        if not embed.title or "Command Ban Appeal" not in embed.title:
            return

        # Extract user ID and guild ID from the embed
        embed_desc = embed.description or ""
        user_id = None
        guild_id = None

        for line in embed_desc.split("\n"):
            if line.startswith("**User ID:**"):
                try:
                    user_id = int(line.split("**User ID:**")[1].strip())
                except (ValueError, IndexError):
                    pass
            elif line.startswith("**Server ID:**"):
                try:
                    guild_id = int(line.split("**Server ID:**")[1].strip())
                except (ValueError, IndexError):
                    pass

        if not user_id or not guild_id:
            return

        # Handle approval (✅) or denial (❌)
        if str(reaction.emoji) == "✅":
            # Approve appeal - unban the user
            if self.bot.database:
                await self.bot.database.remove_command_restriction(guild_id, user_id)

                # Send confirmation message
                response_embed = create_success_embed(
                    "Appeal Approved",
                    f"Command ban appeal for user ID {user_id} has been approved. User has been unbanned."
                )
                await reaction.message.channel.send(embed=response_embed)

                # Try to DM the user about the approval
                try:
                    appealing_user = await self.bot.fetch_user(user_id)
                    guild = self.bot.get_guild(guild_id)
                    if appealing_user and guild:
                        approval_embed = create_embed(
                            "✅ Appeal Approved",
                            f"Your command ban appeal in **{guild.name}** has been approved. You can now use bot commands again."
                        )
                        await appealing_user.send(embed=approval_embed)
                except (discord.Forbidden, discord.NotFound):
                    pass

        elif str(reaction.emoji) == "❌":
            # Deny appeal and set 15-minute cooldown
            if self.bot.database:
                await self.bot.database.set_appeal_cooldown(guild_id, user_id)

            response_embed = create_error_embed(
                "Appeal Denied",
                f"Command ban appeal for user ID {user_id} has been denied. User remains banned and cannot appeal again for 15 minutes."
            )
            await reaction.message.channel.send(embed=response_embed)

            # Try to DM the user about the denial
            try:
                appealing_user = await self.bot.fetch_user(user_id)
                guild = self.bot.get_guild(guild_id)
                if appealing_user and guild:
                    denial_embed = create_embed(
                        "❌ Appeal Denied",
                        f"Your command ban appeal in **{guild.name}** has been denied. You remain banned from using bot commands and cannot appeal again for 15 minutes."
                    )
                    await appealing_user.send(embed=denial_embed)
            except (discord.Forbidden, discord.NotFound):
                pass

    @commands.command(name="say")
    @has_permissions(send_messages= True)
    async def say(self, ctx, *, message: str):
        """Make the bot say something"""
        await ctx.message.delete()  # Delete the command message
        await ctx.send(message)

    @commands.command(name="sayembed")
    @has_permissions(send_messages=True)
    async def say_embed(self, ctx, *, message: str):
        """Make the bot say something in an embed"""
        await ctx.message.delete()  # Delete the command message
        embed = create_embed("📢 Announcement", message)
        await ctx.send(embed=embed)

    # Owner-only slash commands
    def is_owner(self, interaction: discord.Interaction) -> bool:
        """Check if user is a bot owner for slash commands"""
        return is_bot_owner(interaction.user)

    async def is_owner_or_admin(self, interaction: discord.Interaction) -> bool:
        """Check if user is a bot owner or an admin for slash commands"""
        if is_bot_owner(interaction.user):
            return True
        if self.bot.database:
            return await self.bot.database.is_admin_user(interaction.user.id)
        return False

    @app_commands.command(name="commandban", description="Ban a user from using bot commands (Owner/Admin only)")
    @app_commands.describe(member="The member to ban from commands", reason="Reason for the ban")
    async def slash_command_ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        """Ban a user from using bot commands globally (bot owners or admin only)"""
        if not await self.is_owner_or_admin(interaction):
            await interaction.response.send_message(
                embed=create_error_embed("Access Denied", "Only the bot owner or admins can use this command."),
                ephemeral=True
            )
            return

        if member.id == interaction.user.id:
            await interaction.response.send_message(
                embed=create_error_embed("Error", "You cannot command ban yourself!"),
                ephemeral=True
            )
            return

        full_reason = f"{reason}. You may appeal at /appealcommandban if you continue breaking the rules."

        if self.bot.database:
            await self.bot.database.add_command_restriction(
                interaction.guild.id, member.id, "command_ban", full_reason, interaction.user.id, is_global=True
            )

            embed = create_success_embed(
                "Global Command Ban Applied", 
                f"{member.mention} has been banned from using commands globally across all servers.\n**Reason:** {full_reason}"
            )
            await interaction.response.send_message(embed=embed)

            # DM the user
            try:
                dm_embed = create_embed(
                    "🚫 Moderation Action - Global Command Ban",
                    f"**Action:** Global Command Ban\n**Reason:** {full_reason}\n**Moderator:** {interaction.user} ({interaction.user.mention})\n**Server:** {interaction.guild.name}"
                )
                await member.send(embed=dm_embed)
            except discord.Forbidden:
                pass  # User has DMs disabled


    @app_commands.command(name="commandmute", description="Mute a user from using bot commands (Owner/Admin only)")
    @app_commands.describe(member="The member to mute from commands", duration="Duration (e.g., 1h, 30m, 1d)", reason="Reason for the mute")
    async def slash_command_mute(self, interaction: discord.Interaction, member: discord.Member, duration: str, reason: str = "No reason provided"):
        """Mute a user from using bot commands for a specific duration (bot owners or admin only)"""
        if not await self.is_owner_or_admin(interaction):
            await interaction.response.send_message(
                embed=create_error_embed("Access Denied", "Only the bot owner or admins can use this command."),
                ephemeral=True
            )
            return

        if member.id == interaction.user.id:
            await interaction.response.send_message(
                embed=create_error_embed("Error", "You cannot command mute yourself!"),
                ephemeral=True
            )
            return

        # Parse duration with flexible format
        def parse_duration(duration_str):
            import re
            duration_str = duration_str.lower().strip()

            # Pattern to match numbers followed by time units
            pattern = r'(\d+)\s*(s|sec|second|seconds|m|min|minute|minutes|h|hr|hour|hours|d|day|days|w|week|weeks|mo|month|months|y|year|years)'
            matches = re.findall(pattern, duration_str)

            if not matches:
                return None

            total_seconds = 0
            for number, unit in matches:
                number = int(number)

                if unit in ['s', 'sec', 'second', 'seconds']:
                    total_seconds += number
                elif unit in ['m', 'min', 'minute', 'minutes']:
                    total_seconds += number * 60
                elif unit in ['h', 'hr', 'hour', 'hours']:
                    total_seconds += number * 3600
                elif unit in ['d', 'day', 'days']:
                    total_seconds += number * 86400
                elif unit in ['w', 'week', 'weeks']:
                    total_seconds += number * 604800
                elif unit in ['mo', 'month', 'months']:
                    total_seconds += number * 2592000  # 30 days
                elif unit in ['y', 'year', 'years']:
                    total_seconds += number * 31536000  # 365 days

            return timedelta(seconds=total_seconds)

        mute_duration = parse_duration(duration)
        if not mute_duration:
            await interaction.response.send_message(
                embed=create_error_embed(
                    "Invalid Duration", 
                    "Valid formats: `30s`, `5m`, `2h`, `1d`, `1w`, `1mo`, `1y`\nYou can also combine: `1h 30m`, `2d 5h`"
                ),
                ephemeral=True
            )
            return

        full_reason = f"{reason} You may get command banned if you continue."
        expires_at = datetime.utcnow() + mute_duration

        if self.bot.database:
            await self.bot.database.add_command_restriction(
                interaction.guild.id, member.id, "command_mute", full_reason, interaction.user.id, expires_at
            )

            embed = create_success_embed(
                "Command Mute Applied", 
                f"{member.mention} has been muted from using commands for {duration}.\n**Reason:** {full_reason}"
            )
            await interaction.response.send_message(embed=embed)

            # DM the user
            try:
                dm_embed = create_embed(
                    "🔇 Moderation Action - Command Mute",
                    f"**Action:** Command Mute ({duration})\n**Reason:** {full_reason}\n**Moderator:** {interaction.user} ({interaction.user.mention})\n**Server:** {interaction.guild.name}"
                )
                await member.send(embed=dm_embed)
            except discord.Forbidden:
                pass  # User has DMs disabled


    @app_commands.command(name="commandwarn", description="Warn a user about command usage (Owner/Admin only)")
    @app_commands.describe(member="The member to warn", reason="Reason for the warning")
    async def slash_command_warn(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        """Warn a user about command usage (bot owners or admin only)"""
        if not await self.is_owner_or_admin(interaction):
            await interaction.response.send_message(
                embed=create_error_embed("Access Denied", "Only the bot owner or admins can use this command."),
                ephemeral=True
            )
            return

        if member.id == interaction.user.id:
            await interaction.response.send_message(
                embed=create_error_embed("Error", "You cannot command warn yourself!"),
                ephemeral=True
            )
            return

        full_reason = f"{reason} You may get command muted if you continue"

        if self.bot.database:
            await self.bot.database.add_moderation_log(
                interaction.guild.id, member.id, interaction.user.id, "command_warn", full_reason
            )

            embed = create_success_embed(
                "Command Warning Issued", 
                f"{member.mention} has been warned about command usage.\n**Reason:** {full_reason}"
            )
            await interaction.response.send_message(embed=embed)

            # DM the user
            try:
                dm_embed = create_embed(
                    "⚠️ Moderation Action - Command Warning",
                    f"**Action:** Command Warning\n**Reason:** {full_reason}\n**Moderator:** {interaction.user} ({interaction.user.mention})\n**Server:** {interaction.guild.name}"
                )
                await member.send(embed=dm_embed)
            except discord.Forbidden:
                pass  # User has DMs disabled


    @app_commands.command(name="viewcommandmodlogs", description="View command moderation logs (Owner/Admin only)")
    @app_commands.describe(member="Optional: View logs for a specific member", limit="Number of logs to show (max 20)")
    async def slash_view_command_mod_logs(self, interaction: discord.Interaction, member: discord.Member = None, limit: int = 10):
        """View command moderation logs (bot owners or admin only)"""
        if not await self.is_owner_or_admin(interaction):
            await interaction.response.send_message(
                embed=create_error_embed("Access Denied", "Only the bot owner or admins can use this command."),
                ephemeral=True
            )
            return

        if limit > 20:
            limit = 20
        elif limit < 1:
            limit = 10

        if self.bot.database:
            logs = await self.bot.database.get_command_moderation_logs(
                interaction.guild.id, 
                member.id if member else None, 
                limit
            )

            if not logs:
                embed = create_embed(
                    "📋 Command Moderation Logs",
                    f"No command moderation logs found{'for ' + member.mention if member else ''} in this server."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            embed = discord.Embed(
                title="📋 Command Moderation Logs",
                description=f"Showing last {len(logs)} command moderation entries{'for ' + member.mention if member else ''}",
                color=discord.Color.blue()
            )

            for log in logs:
                case_id, user_id, moderator_id, action, reason, timestamp = log

                # Get user and moderator objects
                try:
                    log_user = await self.bot.fetch_user(user_id)
                    user_mention = log_user.mention if log_user else f"<@{user_id}>"
                except:
                    user_mention = f"<@{user_id}>"

                try:
                    moderator = await self.bot.fetch_user(moderator_id)
                    mod_mention = moderator.mention if moderator else f"<@{moderator_id}>"
                except:
                    mod_mention = f"<@{moderator_id}>"

                # Format action for display
                action_display = action.replace("command_", "").title()

                embed.add_field(
                    name=f"Case #{case_id} - {action_display}",
                    value=f"**User:** {user_mention}\n**Moderator:** {mod_mention}\n**Reason:** {reason}\n**Date:** {timestamp}",
                    inline=False
                )

            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="commandunban", description="Unban a user from using bot commands (Owner/Admin only)")
    @app_commands.describe(member="The member to unban from commands")
    async def slash_command_unban(self, interaction: discord.Interaction, member: discord.Member):
        """Unban a user from using bot commands globally (bot owners or admin only)"""
        if not await self.is_owner_or_admin(interaction):
            await interaction.response.send_message(
                embed=create_error_embed("Access Denied", "Only the bot owner or admins can use this command."),
                ephemeral=True
            )
            return

        if self.bot.database:
            # Check if user is currently banned
            restriction = await self.bot.database.get_command_restriction(interaction.guild.id, member.id)
            if not restriction or restriction["type"] != "command_ban":
                embed = create_embed(
                    "ℹ️ Already Unbanned",
                    f"{member.mention} is already unbanned from using commands."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            # Remove global command ban
            await self.bot.database.remove_global_command_restriction(member.id)

            embed = create_success_embed("Global Command Ban Removed", f"{member.mention} can now use commands again across all servers.")
            await interaction.response.send_message(embed=embed)

            # DM the user
            try:
                dm_embed = create_embed(
                    "✅ Moderation Action - Global Command Ban Lifted",
                    f"**Action:** Global Command Unban\n**Reason:** Ban Removed\n**Moderator:** {interaction.user} ({interaction.user.mention})\n**Server:** {interaction.guild.name}"
                )
                await member.send(embed=dm_embed)
            except discord.Forbidden:
                pass  # User has DMs disabled


    @app_commands.command(name="commandunmute", description="Unmute a user from using bot commands (Owner/Admin only)")
    @app_commands.describe(member="The member to unmute from commands")
    async def slash_command_unmute(self, interaction: discord.Interaction, member: discord.Member):
        """Unmute a user from using bot commands (bot owners or admin only)"""
        if not await self.is_owner_or_admin(interaction):
            await interaction.response.send_message(
                embed=create_error_embed("Access Denied", "Only the bot owner or admins can use this command."),
                ephemeral=True
            )
            return

        if self.bot.database:
            # Check if user is currently muted
            restriction = await self.bot.database.get_command_restriction(interaction.guild.id, member.id)
            if not restriction or restriction["type"] != "command_mute":
                embed = create_embed(
                    "ℹ️ Already Unmuted",
                    f"{member.mention} is already unmuted from using commands."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            await self.bot.database.remove_command_restriction(interaction.guild.id, member.id)

            embed = create_success_embed("Command Mute Removed", f"{member.mention} can now use commands again.")
            await interaction.response.send_message(embed=embed)

            # DM the user
            try:
                dm_embed = create_embed(
                    "✅ Moderation Action - Command Mute Lifted",
                    f"**Action:** Command Unmute\n**Reason:** Mute Removed\n**Moderator:** {interaction.user} ({interaction.user.mention})\n**Server:** {interaction.guild.name}"
                )
                await member.send(embed=dm_embed)
            except discord.Forbidden:
                pass  # User has DMs disabled

    @commands.command(name="promoteservercmd")
    async def promote_server_cmd(self, ctx, *, promotion_text: str):
        """Set global server promotion text (Bot owners only)"""
        # Check if user is bot owner
        if not is_bot_owner(ctx.author):
            embed = create_error_embed("Access Denied", "This command is restricted to bot owners only.")
            await ctx.send(embed=embed)
            return

        if len(promotion_text) > 1000:
            embed = create_error_embed(
                "Text Too Long",
                "Promotion text cannot exceed 1000 characters."
            )
            await ctx.send(embed=embed)
            return

        if self.bot.database:
            # Set global promotion instead of per-server
            await self.bot.database.set_global_setting("global_promotion", promotion_text, str(ctx.author))

            embed = create_success_embed(
                "🌐 Global Server Promotion Set",
                f"Global server promotion has been set to:\n\n{promotion_text}\n\nThis will be displayed across **all servers** the bot is in."
            )
            embed.add_field(name="Scope", value="🌍 All Servers", inline=True)
            embed.add_field(name="Set by", value=ctx.author.mention, inline=True)
            embed.set_footer(text="This affects all servers the bot is in")
            await ctx.send(embed=embed)

    @commands.command(name="viewpromotionserver")
    async def view_promotion_server(self, ctx):
        """View current global server promotion (anyone can use)"""
        if self.bot.database:
            # Get global promotion instead of per-server
            promotion_text = await self.bot.database.get_global_setting("global_promotion")

            if not promotion_text:
                embed = create_embed(
                    "📢 Global Server Promotion",
                    "No global server promotion has been set yet."
                )
                await ctx.send(embed=embed)
                return

            embed = create_embed(
                "🌐 Global Server Promotion",
                f"{promotion_text}"
            )
            embed.add_field(name="Scope", value="🌍 All Servers", inline=True)
            embed.set_footer(text="This promotion is displayed across all servers")
            await ctx.send(embed=embed)

    @commands.command(name="viewcommandbans")
    async def view_command_bans(self, ctx, page: int = 1):
        """View list of users who are command banned (Owner/Admin only)"""
        # Check if user is owner or admin
        if not (is_bot_owner(ctx.author) or (self.bot.database and await self.bot.database.is_admin_user(ctx.author.id))):
            await ctx.send(embed=create_error_embed("Access Denied", "Only the bot owner or admins can use this command."))
            return
        if self.bot.database:
            # Get all command bans for this guild and global bans
            bans = await self.bot.database.get_all_command_bans(ctx.guild.id, page=page, per_page=10)

            if not bans:
                embed = create_embed(
                    "📋 Command Bans",
                    "No command bans found in this server or globally."
                )
                await ctx.send(embed=embed)
                return

            embed = discord.Embed(
                title="📋 Command Banned Users",
                description=f"Showing command bans (Page {page})",
                color=discord.Color.red()
            )

            for ban in bans:
                user_id, restriction_type, reason, moderator_id, timestamp, is_global = ban

                # Get user and moderator objects
                try:
                    banned_user = await self.bot.fetch_user(user_id)
                    user_display = f"{banned_user.mention} ({banned_user})"
                except:
                    user_display = f"<@{user_id}> (ID: {user_id})"

                try:
                    moderator = await self.bot.fetch_user(moderator_id)
                    mod_display = moderator.mention if moderator else f"<@{moderator_id}>"
                except:
                    mod_display = f"<@{moderator_id}>"

                ban_scope = "🌍 Global" if is_global else "🏠 Server"

                embed.add_field(
                    name=f"{ban_scope} - {user_display}",
                    value=f"**Reason:** {reason}\n**Moderator:** {mod_display}\n**Date:** {timestamp}",
                    inline=False
                )

            embed.set_footer(text=f"Use k!viewcommandbans {page + 1} for next page")
            await ctx.send(embed=embed)

    @app_commands.command(name="viewcommandbans", description="View list of users who are command banned (Owner only)")
    @app_commands.describe(page="Page number to view (default: 1)")
    async def slash_view_command_bans(self, interaction: discord.Interaction, page: int = 1):
        """View list of users who are command banned (bot owners only)"""
        if not self.is_owner(interaction):
            await interaction.response.send_message(
                embed=create_error_embed("Access Denied", "Only the bot owner can use this command."),
                ephemeral=True
            )
            return

        if self.bot.database:
            # Get all command bans for this guild and global bans
            bans = await self.bot.database.get_all_command_bans(interaction.guild.id, page=page, per_page=10)

            if not bans:
                embed = create_embed(
                    "📋 Command Bans",
                    "No command bans found in this server or globally."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return

            embed = discord.Embed(
                title="📋 Command Banned Users",
                description=f"Showing command bans (Page {page})",
                color=discord.Color.red()
            )

            for ban in bans:
                user_id, restriction_type, reason, moderator_id, timestamp, is_global = ban

                # Get user and moderator objects
                try:
                    banned_user = await self.bot.fetch_user(user_id)
                    user_display = f"{banned_user.mention} ({banned_user})"
                except:
                    user_display = f"<@{user_id}> (ID: {user_id})"

                try:
                    moderator = await self.bot.fetch_user(moderator_id)
                    mod_display = moderator.mention if moderator else f"<@{moderator_id}>"
                except:
                    mod_display = f"<@{moderator_id}>"

                ban_scope = "🌍 Global" if is_global else "🏠 Server"

                embed.add_field(
                    name=f"{ban_scope} - {user_display}",
                    value=f"**Reason:** {reason}\n**Moderator:** {mod_display}\n**Date:** {timestamp}",
                    inline=False
                )

            embed.set_footer(text=f"Use /viewcommandbans page:{page + 1} for next page")
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.command(name="addadmin")
    async def add_admin(self, ctx, member: discord.Member, *, reason: str = "Granted admin privileges"):
        """Grant admin privileges to a user (bot owners only)"""
        # Check if user is original owner or added bot owner
        if not await is_super_admin(ctx.author, self.bot.database):
            embed = create_error_embed("Access Denied", "Only bot owners can use this command.")
            await ctx.send(embed=embed)
            return

        if member.id == ctx.author.id:
            await ctx.send(embed=create_error_embed("Error", "You cannot grant admin privileges to yourself!"))
            return

        if self.bot.database:
            # Add user to admin list
            await self.bot.database.add_admin_user(member.id, reason, ctx.author.id)

            embed = create_success_embed(
                "🛡️ Admin Privileges Granted", 
                f"{member.mention} has been granted admin privileges.\n**Reason:** {reason}\n\n"
                "They can now use owner-only commands like `/commandban`, `/commandmute`, etc."
            )
            await ctx.send(embed=embed)

            # DM the user about their new privileges and appealing process
            try:
                dm_embed = create_embed(
                    "🛡️ Admin Privileges Granted",
                    f"**Congratulations!** You have been granted admin privileges by {ctx.author} ({ctx.author.mention}).\n\n"
                    f"**Reason:** {reason}\n"
                    f"**Server:** {ctx.guild.name}\n\n"
                    "**You can now use the following owner-only commands:**\n"
                    "• `/commandban` - Ban users from using bot commands\n"
                    "• `/commandmute` - Mute users from using bot commands\n"
                    "• `/commandwarn` - Warn users about command usage\n"
                    "• `/commandunban` - Unban users from commands\n"
                    "• `/commandunmute` - Unmute users from commands\n"
                    "• `/viewcommandmodlogs` - View command moderation logs\n"
                    "• `/viewcommandbans` - View list of command banned users\n\n"
                    "**Important Information:**\n"
                    "• Use these commands responsibly\n"
                    "• Users who are command banned can appeal using `k!appealcommandban <reason>`\n"
                    "• You will receive DMs about appeals that you can approve (✅) or deny (❌)\n"
                    "• Denied appeals have a 15-minute cooldown before users can appeal again\n\n"
                    "**Appeal Process:**\n"
                    "1. User uses `k!appealcommandban <reason>`\n"
                    "2. You receive a DM with appeal details\n"
                    "3. React with ✅ to approve or ❌ to deny\n"
                    "4. User gets notified of your decision\n\n"
                    "Thank you for helping moderate the bot commands!"
                )
                await member.send(embed=dm_embed)
            except discord.Forbidden:
                pass  # User has DMs disabled

            # Log the action
            if self.bot.database:
                await self.bot.database.add_moderation_log(
                    ctx.guild.id, member.id, ctx.author.id, "admin_granted", reason
                )

    @app_commands.command(name="addadmin", description="Grant admin privileges to a user (Owner only)")
    @app_commands.describe(member="The member to grant admin privileges", reason="Reason for granting admin privileges")
    async def slash_add_admin(self, interaction: discord.Interaction, member: discord.Member, reason: str = "Granted admin privileges"):
        """Grant admin privileges to a user (bot owners only)"""
        if not self.is_owner(interaction):
            await interaction.response.send_message(
                embed=create_error_embed("Access Denied", "Only the bot owner can use this command."),
                ephemeral=True
            )
            return

        if member.id == interaction.user.id:
            await interaction.response.send_message(
                embed=create_error_embed("Error", "You cannot grant admin privileges to yourself!"),
                ephemeral=True
            )
            return

        if self.bot.database:
            # Add user to admin list
            await self.bot.database.add_admin_user(member.id, reason, interaction.user.id)

            embed = create_success_embed(
                "🛡️ Admin Privileges Granted", 
                f"{member.mention} has been granted admin privileges.\n**Reason:** {reason}\n\n"
                "They can now use owner-only commands like `/commandban`, `/commandmute`, etc."
            )
            await interaction.response.send_message(embed=embed)

            # DM the user about their new privileges and appealing process
            try:
                dm_embed = create_embed(
                    "🛡️ Admin Privileges Granted",
                    f"**Congratulations!** You have been granted admin privileges by {interaction.user} ({interaction.user.mention}).\n\n"
                    f"**Reason:** {reason}\n"
                    f"**Server:** {interaction.guild.name}\n\n"
                    "**You can now use the following owner-only commands:**\n"
                    "• `/commandban` - Ban users from using bot commands\n"
                    "• `/commandmute` - Mute users from using bot commands\n"
                    "• `/commandwarn` - Warn users about command usage\n"
                    "• `/commandunban` - Unban users from commands\n"
                    "• `/commandunmute` - Unmute users from commands\n"
                    "• `/viewcommandmodlogs` - View command moderation logs\n"
                    "• `/viewcommandbans` - View list of command banned users\n\n"
                    "**Important Information:**\n"
                    "• Use these commands responsibly\n"
                    "• Users who are command banned can appeal using `k!appealcommandban <reason>`\n"
                    "• You will receive DMs about appeals that you can approve (✅) or deny (❌)\n"
                    "• Denied appeals have a 15-minute cooldown before users can appeal again\n\n"
                    "**Appeal Process:**\n"
                    "1. User uses `k!appealcommandban <reason>`\n"
                    "2. You receive a DM with appeal details\n"
                    "3. React with ✅ to approve or ❌ to deny\n"
                    "4. User gets notified of your decision\n\n"
                    "Thank you for helping moderate the bot commands!"
                )
                await member.send(embed=dm_embed)
            except discord.Forbidden:
                pass  # User has DMs disabled

            # Log the action
            if self.bot.database:
                await self.bot.database.add_moderation_log(
                    interaction.guild.id, member.id, interaction.user.id, "admin_granted", reason
                )

    @app_commands.command(name="removeadmin", description="Remove admin privileges from a user (Owner only)")
    @app_commands.describe(member="The member to remove admin privileges from", reason="Reason for removing admin privileges")
    async def slash_delete_admin(self, interaction: discord.Interaction, member: discord.Member, reason: str = "Admin privileges revoked"):
        """Remove admin privileges from a user (bot owners only)"""
        if not self.is_owner(interaction):
            await interaction.response.send_message(
                embed=create_error_embed("Access Denied", "Only the bot owner can use this command."),
                ephemeral=True
            )
            return

        if self.bot.database:
            # Check if user is actually an admin
            if not await self.bot.database.is_admin_user(member.id):
                await interaction.response.send_message(
                    embed=create_error_embed("Not an Admin", f"{member.mention} is not currently an admin."),
                    ephemeral=True
                )
                return

            # Remove user from admin list
            await self.bot.database.remove_admin_user(member.id)

            embed = create_success_embed(
                "🛡️ Admin Privileges Revoked", 
                f"{member.mention}'s admin privileges have been removed.\n**Reason:** {reason}\n\n"
                "They can no longer use owner-only commands."
            )
            await interaction.response.send_message(embed=embed)

            # DM the user about their revoked privileges
            try:
                dm_embed = create_embed(
                    "🛡️ Admin Privileges Revoked",
                    f"Your admin privileges have been revoked by {interaction.user} ({interaction.user.mention}).\n\n"
                    f"**Reason:** {reason}\n"
                    f"**Server:** {interaction.guild.name}\n\n"
                    "**You no longer have access to:**\n"
                    "• `/commandban` - Ban users from using bot commands\n"
                    "• `/commandmute` - Mute users from using bot commands\n"
                    "• `/commandwarn` - Warn users about command usage\n"
                    "• `/commandunban` - Unban users from commands\n"
                    "• `/commandunmute` - Unmute users from commands\n"
                    "• `/viewcommandmodlogs` - View command moderation logs\n"
                    "• `/viewcommandbans` - View list of command banned users\n\n"
                    "If you believe this was done in error, please contact the bot owner."
                )
                await member.send(embed=dm_embed)
            except discord.Forbidden:
                pass  # User has DMs disabled

            # Log the action
            if self.bot.database:
                await self.bot.database.add_moderation_log(
                    interaction.guild.id, member.id, interaction.user.id, "admin_revoked", reason
                )

    @commands.command(name="removeadmin")
    async def delete_admin(self, ctx, member: discord.Member, *, reason: str = "Admin privileges revoked"):
        """Remove admin privileges from a user (bot owners only)"""
        # Check if user is original owner or added bot owner
        if not await is_super_admin(ctx.author, self.bot.database):
            embed = create_error_embed("Access Denied", "Only bot owners can use this command.")
            await ctx.send(embed=embed)
            return

        if self.bot.database:
            # Check if user is actually an admin
            if not await self.bot.database.is_admin_user(member.id):
                await ctx.send(embed=create_error_embed("Not an Admin", f"{member.mention} is not currently an admin."))
                return

            # Remove user from admin list
            await self.bot.database.remove_admin_user(member.id)

            embed = create_success_embed(
                "🛡️ Admin Privileges Revoked", 
                f"{member.mention}'s admin privileges have been removed.\n**Reason:** {reason}\n\n"
                "They can no longer use owner-only commands."
            )
            await ctx.send(embed=embed)

            # DM the user about their revoked privileges
            try:
                dm_embed = create_embed(
                    "🛡️ Admin Privileges Revoked",
                    f"Your admin privileges have been revoked by {ctx.author} ({ctx.author.mention}).\n\n"
                    f"**Reason:** {reason}\n"
                    f"**Server:** {ctx.guild.name}\n\n"
                    "**You no longer have access to:**\n"
                    "• `/commandban` - Ban users from using bot commands\n"
                    "• `/commandmute` - Mute users from using bot commands\n"
                    "• `/commandwarn` - Warn users about command usage\n"
                    "• `/commandunban` - Unban users from commands\n"
                    "• `/commandunmute` - Unmute users from commands\n"
                    "• `/viewcommandmodlogs` - View command moderation logs\n"
                    "• `/viewcommandbans` - View list of command banned users\n\n"
                    "If you believe this was done in error, please contact the bot owner."
                )
                await member.send(embed=dm_embed)
            except discord.Forbidden:
                pass  # User has DMs disabled

            # Log the action
            if self.bot.database:
                await self.bot.database.add_moderation_log(
                    ctx.guild.id, member.id, ctx.author.id, "admin_revoked", reason
                )

    async def is_admin_user_prefix(self, user_id: int) -> bool:
        """Check if user is an admin for prefix commands"""
        if self.bot.database:
            return await self.bot.database.is_admin_user(user_id)
        return False

    @commands.command(name="commandserverban")
    async def command_server_ban(self, ctx, server_id: int, limit: int = None, *, reason: str = "No reason provided"):
        """Ban a server from using bot commands (Admin only)"""
        # Check if user is owner or admin
        if not (is_bot_owner(ctx.author) or await self.is_admin_user_prefix(ctx.author.id)):
            await ctx.send(embed=create_error_embed("Access Denied", "Only the bot owner or admins can use this command."))
            return

        # Get the server
        try:
            guild = self.bot.get_guild(server_id)
            if not guild:
                await ctx.send(embed=create_error_embed("Server Not Found", f"Bot is not in a server with ID {server_id}."))
                return
        except:
            await ctx.send(embed=create_error_embed("Invalid Server ID", "Please provide a valid server ID."))
            return

        if self.bot.database:
            await self.bot.database.add_server_command_ban(
                server_id, reason, ctx.author.id, limit
            )

            limit_text = f" with limit of {limit}" if limit else ""
            embed = create_success_embed(
                "🚫 Server Command Ban Applied", 
                f"**Server:** {guild.name} ({server_id})\n"
                f"**Reason:** {reason}\n"
                f"**Limit:** {limit if limit else 'No limit'}\n"
                f"**Moderator:** {ctx.author.mention}\n\n"
                f"This server is now banned from using bot commands{limit_text}.\n"
                "Server members cannot use commands like `/commandban`."
            )
            await ctx.send(embed=embed)

            # DM the server owner
            try:
                owner = guild.owner
                if owner:
                    dm_embed = create_embed(
                        "🚫 Server Command Ban Notice",
                        f"Your server **{guild.name}** has been banned from using bot commands.\n\n"
                        f"**Reason:** {reason}\n"
                        f"**Limit:** {limit if limit else 'No limit'}\n"
                        f"**Banned by:** {ctx.author} ({ctx.author.mention})\n\n"
                        "**What this means:**\n"
                        "• Server members cannot use moderation commands like `/commandban`\n"
                        "• The bot will still function for basic commands\n"
                        "• This restriction affects all server members\n\n"
                        "If you believe this was done in error, please contact the bot administrators."
                    )
                    await owner.send(embed=dm_embed)
            except discord.Forbidden:
                pass  # Owner has DMs disabled

            # Log the action
            await self.bot.database.add_moderation_log(
                ctx.guild.id, 0, ctx.author.id, "server_command_ban", f"Server {guild.name} ({server_id}) - {reason}"
            )

    @commands.command(name="uncomandserverban")
    async def uncommand_server_ban(self, ctx, server_id: int, *, reason: str = "Ban lifted"):
        """Unban a server from using bot commands (Admin only)"""
        # Check if user is owner or admin
        if not (is_bot_owner(ctx.author) or await self.is_admin_user_prefix(ctx.author.id)):
            await ctx.send(embed=create_error_embed("Access Denied", "Only the bot owner or admins can use this command."))
            return

        # Get the server
        try:
            guild = self.bot.get_guild(server_id)
            if not guild:
                await ctx.send(embed=create_error_embed("Server Not Found", f"Bot is not in a server with ID {server_id}."))
                return
        except:
            await ctx.send(embed=create_error_embed("Invalid Server ID", "Please provide a valid server ID."))
            return

        if self.bot.database:
            # Check if server is actually banned
            if not await self.bot.database.is_server_command_banned(server_id):
                await ctx.send(embed=create_error_embed("Not Banned", f"Server {guild.name} is not currently command banned."))
                return

            await self.bot.database.remove_server_command_ban(server_id)

            embed = create_success_embed(
                "✅ Server Command Ban Removed", 
                f"**Server:** {guild.name} ({server_id})\n"
                f"**Reason:** {reason}\n"
                f"**Moderator:** {ctx.author.mention}\n\n"
                "This server can now use bot commands again."
            )
            await ctx.send(embed=embed)

            # DM the server owner
            try:
                owner = guild.owner
                if owner:
                    dm_embed = create_embed(
                        "✅ Server Command Ban Lifted",
                        f"Your server **{guild.name}** command ban has been lifted.\n\n"
                        f"**Reason:** {reason}\n"
                        f"**Lifted by:** {ctx.author} ({ctx.author.mention})\n\n"
                        "**What this means:**\n"
                        "• Server members can now use all bot commands again\n"
                        "• Moderation commands like `/commandban` are available\n"
                        "• All restrictions have been removed\n\n"
                        "Thank you for your patience."
                    )
                    await owner.send(embed=dm_embed)
            except discord.Forbidden:
                pass  # Owner has DMs disabled

            # Log the action
            await self.bot.database.add_moderation_log(
                ctx.guild.id, 0, ctx.author.id, "server_command_unban", f"Server {guild.name} ({server_id}) - {reason}"
            )

    @app_commands.command(name="commandserverban", description="Ban a server from using bot commands (Admin only)")
    @app_commands.describe(server_id="The server ID to ban", limit="Optional limit", reason="Reason for the ban")
    async def slash_command_server_ban(self, interaction: discord.Interaction, server_id: str, limit: int = None, reason: str = "No reason provided"):
        """Ban a server from using bot commands (Admin only)"""
        if not await self.is_owner_or_admin(interaction):
            await interaction.response.send_message(
                embed=create_error_embed("Access Denied", "Only the bot owner or admins can use this command."),
                ephemeral=True
            )
            return

        try:
            server_id = int(server_id)
        except ValueError:
            await interaction.response.send_message(
                embed=create_error_embed("Invalid Server ID", "Please provide a valid server ID."),
                ephemeral=True
            )
            return

        # Get the server
        try:
            guild = self.bot.get_guild(server_id)
            if not guild:
                await interaction.response.send_message(
                    embed=create_error_embed("Server Not Found", f"Bot is not in a server with ID {server_id}."),
                    ephemeral=True
                )
                return
        except:
            await interaction.response.send_message(
                embed=create_error_embed("Invalid Server ID", "Please provide a valid server ID."),
                ephemeral=True
            )
            return

        if self.bot.database:
            await self.bot.database.add_server_command_ban(
                server_id, reason, interaction.user.id, limit
            )

            embed = create_success_embed(
                "🚫 Server Command Ban Applied", 
                f"**Server:** {guild.name} ({server_id})\n"
                f"**Reason:** {reason}\n"
                f"**Limit:** {limit if limit else 'No limit'}\n"
                f"**Moderator:** {interaction.user.mention}\n\n"
                "This server is now banned from using bot commands.\n"
                "Server members cannot use commands like `/commandban`."
            )
            await interaction.response.send_message(embed=embed)

            # DM the server owner
            try:
                owner = guild.owner
                if owner:
                    dm_embed = create_embed(
                        "🚫 Server Command Ban Notice",
                        f"Your server **{guild.name}** has been banned from using bot commands.\n\n"
                        f"**Reason:** {reason}\n"
                        f"**Limit:** {limit if limit else 'No limit'}\n"
                        f"**Banned by:** {interaction.user} ({interaction.user.mention})\n\n"
                        "**What this means:**\n"
                        "• Server members cannot use moderation commands like `/commandban`\n"
                        "• The bot will still function for basic commands\n"
                        "• This restriction affects all server members\n\n"
                        "If you believe this was done in error, please contact the bot administrators."
                    )
                    await owner.send(embed=dm_embed)
            except discord.Forbidden:
                pass  # Owner has DMs disabled

            # Log the action
            await self.bot.database.add_moderation_log(
                interaction.guild.id, 0, interaction.user.id, "server_command_ban", f"Server {guild.name} ({server_id}) - {reason}"
            )

    @app_commands.command(name="uncomandserverban", description="Unban a server from using bot commands (Admin only)")
    @app_commands.describe(server_id="The server ID to unban", reason="Reason for unbanning")
    async def slash_uncommand_server_ban(self, interaction: discord.Interaction, server_id: str, reason: str = "Ban lifted"):
        """Unban a server from using bot commands (Admin only)"""
        if not await self.is_owner_or_admin(interaction):
            await interaction.response.send_message(
                embed=create_error_embed("Access Denied", "Only the bot owner or admins can use this command."),
                ephemeral=True
            )
            return

        try:
            server_id = int(server_id)
        except ValueError:
            await interaction.response.send_message(
                embed=create_error_embed("Invalid Server ID", "Please provide a valid server ID."),
                ephemeral=True
            )
            return

        # Get the server
        try:
            guild = self.bot.get_guild(server_id)
            if not guild:
                await interaction.response.send_message(
                    embed=create_error_embed("Server Not Found", f"Bot is not in a server with ID {server_id}."),
                    ephemeral=True
                )
                return
        except:
            await interaction.response.send_message(
                embed=create_error_embed("Invalid Server ID", "Please provide a valid server ID."),
                ephemeral=True
            )
            return

        if self.bot.database:
            # Check if server is actually banned
            if not await self.bot.database.is_server_command_banned(server_id):
                await interaction.response.send_message(
                    embed=create_error_embed("Not Banned", f"Server {guild.name} is not currently command banned."),
                    ephemeral=True
                )
                return

            await self.bot.database.remove_server_command_ban(server_id)

            embed = create_success_embed(
                "✅ Server Command Ban Removed", 
                f"**Server:** {guild.name} ({server_id})\n"
                f"**Reason:** {reason}\n"
                f"**Moderator:** {interaction.user.mention}\n\n"
                "This server can now use bot commands again."
            )
            await interaction.response.send_message(embed=embed)

            # DM the server owner
            try:
                owner = guild.owner
                if owner:
                    dm_embed = create_embed(
                        "✅ Server Command Ban Lifted",
                        f"Your server **{guild.name}** command ban has been lifted.\n\n"
                        f"**Reason:** {reason}\n"
                        f"**Lifted by:** {interaction.user} ({interaction.user.mention})\n\n"
                        "**What this means:**\n"
                        "• Server members can now use all bot commands again\n"
                        "• Moderation commands like `/commandban` are available\n"
                        "• All restrictions have been removed\n\n"
                        "Thank you for your patience."
                    )
                    await owner.send(embed=dm_embed)
            except discord.Forbidden:
                pass  # Owner has DMs disabled

            # Log the action
            await self.bot.database.add_moderation_log(
                interaction.guild.id, 0, interaction.user.id, "server_command_unban", f"Server {guild.name} ({server_id}) - {reason}"
            )

    @commands.command(name="questionbyone")
    @has_permissions(manage_channels=True)
    async def question_by_one(self, ctx, *, ticket_name: str):
        """Create a ticket channel with specified name"""
        if not ticket_name:
            await ctx.send(embed=create_error_embed("Missing Ticket Name", "Please specify a name for the ticket."))
            return

        # Clean the ticket name for channel naming
        channel_name = ticket_name.lower().replace(" ", "-").replace("_", "-")
        channel_name = f"ticket-{channel_name}-{ctx.author.id}"

        # Check if bot has permissions
        if not ctx.guild.me.guild_permissions.manage_channels:
            await ctx.send(embed=create_error_embed("Missing Permissions", "I don't have permission to create channels."))
            return

        try:
            # Create the ticket channel
            overwrites = {
                ctx.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                ctx.author: discord.PermissionOverwrite(read_messages=True, send_messages=True),
                ctx.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True)
            }

            # Add permissions for staff roles if they exist
            for role in ctx.guild.roles:
                if role.name.lower() in ['staff', 'admin', 'administrator', 'moderator', 'mod', 'manager']:
                    overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)

            ticket_channel = await ctx.guild.create_text_channel(
                name=channel_name,
                overwrites=overwrites,
                topic=f"Ticket: {ticket_name} | Created by {ctx.author}",
                reason=f"Ticket created by {ctx.author}"
            )

            # Send confirmation in original channel
            embed = create_success_embed(
                "🎫 Ticket Created",
                f"**Ticket Name:** {ticket_name}\n"
                f"**Channel:** {ticket_channel.mention}\n"
                f"**Created by:** {ctx.author.mention}"
            )
            await ctx.send(embed=embed)

            # Send welcome message in ticket channel
            welcome_embed = create_embed(
                f"🎫 {ticket_name}",
                f"Welcome {ctx.author.mention}!\n\n"
                f"This ticket has been created for: **{ticket_name}**\n"
                "Please describe your request or question below.\n\n"
                "Staff will assist you shortly."
            )
            welcome_embed.add_field(
                name="📝 Instructions",
                value="• Clearly explain your request\n• Be patient while waiting for staff\n• Staff can close this ticket when resolved",
                inline=False
            )
            welcome_embed.set_footer(text=f"Ticket ID: {ctx.author.id}")

            await ticket_channel.send(embed=welcome_embed)

            # Log the ticket creation
            if self.bot.database:
                await self.bot.database.add_moderation_log(
                    ctx.guild.id, ctx.author.id, ctx.author.id, "ticket_created", f"Ticket: {ticket_name}"
                )

        except discord.Forbidden:
            await ctx.send(embed=create_error_embed("Permission Denied", "I don't have permission to create channels in this server."))
        except discord.HTTPException as e:
            await ctx.send(embed=create_error_embed("Channel Creation Failed", f"Failed to create ticket channel: {str(e)}"))
        except Exception as e:
            logger.error(f"Error creating ticket: {e}")
            await ctx.send(embed=create_error_embed("Ticket Creation Error", "An unexpected error occurred while creating the ticket."))


async def setup(bot):
    await bot.add_cog(ModerationCog(bot))