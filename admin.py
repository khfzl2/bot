import discord
from discord.ext import commands
import logging
import asyncio
from ..utils import create_embed, create_error_embed, create_success_embed, has_permissions, is_bot_owner, is_super_admin, BOT_OWNERS

logger = logging.getLogger(__name__)

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.automention_tasks = {} # Dictionary to store automention tasks per guild
        self.auto_mention_task = None # For the specific automention implementation in the changes

    @commands.command(name="prefix")
    @has_permissions(administrator=True)
    async def change_prefix(self, ctx, new_prefix: str = None):
        """Change the bot's command prefix for this server"""
        if not new_prefix:
            current_prefix = await self.bot.database.get_guild_prefix(ctx.guild.id)
            embed = create_embed("Current Prefix", f"The current prefix is: `{current_prefix}`")
            await ctx.send(embed=embed)
            return

        if len(new_prefix) > 5:
            await ctx.send(embed=create_error_embed("Invalid Prefix", "Prefix cannot be longer than 5 characters."))
            return

        await self.bot.database.set_guild_prefix(ctx.guild.id, new_prefix)
        await ctx.send(embed=create_success_embed("Prefix Changed", f"Prefix has been changed to: `{new_prefix}`"))

    @commands.command(name="reload")
    @has_permissions(administrator=True)
    async def reload_cog(self, ctx, *, cog_name: str):
        """Reload a cog"""
        try:
            # Unload the cog
            await self.bot.unload_extension(f'bot.cogs.{cog_name.lower()}')
            # Load the cog
            await self.bot.load_extension(f'bot.cogs.{cog_name.lower()}')

            embed = create_success_embed("✅ Cog Reloaded", f"Successfully reloaded `{cog_name.lower()}` cog.")
            await ctx.send(embed=embed)

        except Exception as e:
            embed = create_error_embed("❌ Reload Failed", f"Failed to reload cog: {str(e)}")
            await ctx.send(embed=embed)

    @commands.command(name="automention")
    # @has_permissions(administrator=True) # This decorator was removed in the changes, replaced by kh2_only() if that was intended
    async def auto_mention(self, ctx, status: str):
        """Enable/disable auto-mention every 3 minutes (bot owners only)"""
        if status.lower() not in ['online', 'offline']:
            await ctx.send(embed=create_error_embed("Invalid Status", "Use 'online' or 'offline'."))
            return

        if status.lower() == 'online':
            if self.auto_mention_task and not self.auto_mention_task.done():
                await ctx.send(embed=create_embed("Auto-mention", "Auto-mention is already running!"))
                return

            self.auto_mention_task = asyncio.create_task(self._automention_loop(ctx.channel))
            await ctx.send(embed=create_success_embed("Auto-mention Started", "Bot will now ping itself every 3 minutes."))
        else:
            if self.auto_mention_task:
                self.auto_mention_task.cancel()
                self.auto_mention_task = None
            await ctx.send(embed=create_success_embed("Auto-mention Stopped", "Auto-mention has been disabled."))




    async def _automention_loop(self, channel):
        """Internal loop for automention functionality"""
        try:
            while True:
                await asyncio.sleep(180)  # Wait 3 minutes (180 seconds)

                # Send a mention to the bot
                mention_message = f"{self.bot.user.mention} Automatic mention - keeping you active!"
                await channel.send(mention_message)

        except asyncio.CancelledError:
            # Task was cancelled, clean exit
            pass
        except Exception as e:
            logger.error(f"Error in automention loop: {e}")
            # Send error message to channel if possible
            try:
                embed = create_error_embed("Automention Error", "Automention stopped due to an error.")
                await channel.send(embed=embed)
            except:
                pass

    @commands.command(name="deleteall")
    @has_permissions(administrator=True)
    async def delete_all_channels(self, ctx, confirm: str = None):
        """Delete EVERYTHING in the server - channels, roles, categories, emojis, etc. (Administrator only). Use 'confirm' to execute."""
        # Check if deleteall is globally disabled
        global_status = await self.bot.database.get_global_setting("deleteall_global_status")
        if global_status == "offline":
            embed = create_error_embed(
                "⛔ Globally Disabled",
                "The `deleteall` command is globally disabled by the bot owner.\nThis cannot be overridden by server administrators."
            )
            await ctx.send(embed=embed)
            return

        # Check if deleteall is enabled for this server
        if not await self.bot.database.get_admin_setting(ctx.guild.id, "deleteall_enabled"):
            embed = create_error_embed(
                "Command Disabled",
                "The `deleteall` command is disabled for this server.\nUse `k!deleteall-toggle` to enable it."
            )
            await ctx.send(embed=embed)
            return

        # Check bot permissions
        bot_perms = ctx.guild.me.guild_permissions
        required_perms = [
            bot_perms.manage_channels,
            bot_perms.manage_roles,
            bot_perms.manage_emojis,
            bot_perms.manage_guild
        ]

        if not all(required_perms):
            missing = []
            if not bot_perms.manage_channels:
                missing.append("Manage Channels")
            if not bot_perms.manage_roles:
                missing.append("Manage Roles")
            if not bot_perms.manage_emojis:
                missing.append("Manage Emojis")
            if not bot_perms.manage_guild:
                missing.append("Manage Server")

            await ctx.send(embed=create_error_embed(
                "Missing Permissions",
                f"I don't have the required permissions: {', '.join(missing)}"
            ))
            return

        # Count everything that will be deleted
        text_channels = len([c for c in ctx.guild.text_channels])
        voice_channels = len([c for c in ctx.guild.voice_channels])
        categories = len([c for c in ctx.guild.categories])
        roles = len([r for r in ctx.guild.roles if r != ctx.guild.default_role and r != ctx.guild.me.top_role and not r.managed])
        emojis = len([e for e in ctx.guild.emojis])

        total_items = text_channels + voice_channels + categories + roles + emojis

        # Safety confirmation required
        if confirm != "confirm":
            embed = create_embed(
                "⚠️ DELETE EVERYTHING",
                f"**EXTREME WARNING:** This will delete **EVERYTHING** in this server:\n\n"
                f"📝 **{text_channels} text channels**\n"
                f"🔊 **{voice_channels} voice channels**\n"
                f"📁 **{categories} categories**\n"
                f"🏷️ **{roles} roles** (excluding @everyone and bot roles)\n"
                f"😀 **{emojis} custom emojis**\n\n"
                f"**Total: {total_items} items will be permanently deleted!**\n"
                f"**This action cannot be undone and will essentially nuke the server!**\n\n"
                f"To proceed, use: `k!deleteall confirm`"
            )
            embed.set_footer(text="Administrator permission required")
            await ctx.send(embed=embed)
            return

        # Final confirmation with reaction
        confirm_embed = create_embed(
            "🚨 FINAL CONFIRMATION - NUKE SERVER",
            f"You are about to **COMPLETELY NUKE** this server!\n\n"
            f"📝 {text_channels} text channels\n"
            f"🔊 {voice_channels} voice channels\n"
            f"📁 {categories} categories\n"
            f"🏷️ {roles} roles\n"
            f"😀 {emojis} emojis\n\n"
            f"**Total: {total_items} items will be permanently deleted!**\n\n"
            f"React with ✅ to **NUKE EVERYTHING** or ❌ to cancel.\n"
            f"This will timeout in 30 seconds."
        )

        confirm_msg = await ctx.send(embed=confirm_embed)
        await confirm_msg.add_reaction("✅")
        await confirm_msg.add_reaction("❌")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✅", "❌"] and reaction.message.id == confirm_msg.id

        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)

            if str(reaction.emoji) == "❌":
                await confirm_msg.edit(embed=create_embed("❌ Cancelled", "Server nuke cancelled."))
                return
            elif str(reaction.emoji) == "✅":
                # Proceed with complete deletion
                await confirm_msg.edit(embed=create_embed("🗑️ NUKING SERVER...", "Complete server deletion in progress..."))

                try:
                    deleted_text = 0
                    deleted_voice = 0
                    deleted_categories = 0
                    deleted_roles = 0
                    deleted_emojis = 0
                    failed_items = []

                    # Delete all custom emojis first
                    for emoji in ctx.guild.emojis:
                        try:
                            await emoji.delete(reason=f"DeleteAll command by {ctx.author}")
                            deleted_emojis += 1
                            await asyncio.sleep(0.3)
                        except discord.Forbidden:
                            failed_items.append(f"😀{emoji.name} (no permission)")
                        except discord.HTTPException as e:
                            failed_items.append(f"😀{emoji.name} (error: {e})")

                    # Delete all text channels (except current one for final message)
                    for text_channel in ctx.guild.text_channels:
                        if text_channel != ctx.channel:
                            try:
                                await text_channel.delete(reason=f"DeleteAll command by {ctx.author}")
                                deleted_text += 1
                                await asyncio.sleep(0.3)
                            except discord.Forbidden:
                                failed_items.append(f"#{text_channel.name} (no permission)")
                            except discord.HTTPException as e:
                                failed_items.append(f"#{text_channel.name} (error: {e})")

                    # Delete all voice channels
                    for voice_channel in ctx.guild.voice_channels:
                        try:
                            await voice_channel.delete(reason=f"DeleteAll command by {ctx.author}")
                            deleted_voice += 1
                            await asyncio.sleep(0.3)
                        except discord.Forbidden:
                            failed_items.append(f"🔊{voice_channel.name} (no permission)")
                        except discord.HTTPException as e:
                            failed_items.append(f"🔊{voice_channel.name} (error: {e})")

                    # Delete all categories
                    for category in ctx.guild.categories:
                        try:
                            await category.delete(reason=f"DeleteAll command by {ctx.author}")
                            deleted_categories += 1
                            await asyncio.sleep(0.3)
                        except discord.Forbidden:
                            failed_items.append(f"📁{category.name} (no permission)")
                        except discord.HTTPException as e:
                            failed_items.append(f"📁{category.name} (error: {e})")

                    # Delete all roles (except @everyone, bot roles, and roles higher than bot)
                    for role in reversed(ctx.guild.roles):  # Start from highest role
                        if (role != ctx.guild.default_role and 
                            role != ctx.guild.me.top_role and 
                            not role.managed and 
                            role < ctx.guild.me.top_role):
                            try:
                                await role.delete(reason=f"DeleteAll command by {ctx.author}")
                                deleted_roles += 1
                                await asyncio.sleep(0.3)
                            except discord.Forbidden:
                                failed_items.append(f"🏷️{role.name} (no permission)")
                            except discord.HTTPException as e:
                                failed_items.append(f"🏷️{role.name} (error: {e})")

                    # Create completion message
                    total_deleted = deleted_text + deleted_voice + deleted_categories + deleted_roles + deleted_emojis
                    completion_embed = create_success_embed(
                        "💥 SERVER NUKE COMPLETE",
                        f"Successfully deleted **{total_deleted}** items:\n\n"
                        f"📝 **{deleted_text}** text channels\n"
                        f"🔊 **{deleted_voice}** voice channels\n"
                        f"📁 **{deleted_categories}** categories\n"
                        f"🏷️ **{deleted_roles}** roles\n"
                        f"😀 **{deleted_emojis}** emojis"
                    )
                    completion_embed.add_field(
                        name="Executed by",
                        value=ctx.author.mention,
                        inline=True
                    )
                    completion_embed.add_field(
                        name="Server",
                        value=ctx.guild.name,
                        inline=True
                    )

                    if failed_items:
                        failed_list = "\n".join(failed_items[:10])  # Limit to 10 for embed space
                        if len(failed_items) > 10:
                            failed_list += f"\n... and {len(failed_items) - 10} more"
                        completion_embed.add_field(
                            name="⚠️ Failed to Delete",
                            value=failed_list,
                            inline=False
                        )

                    completion_embed.set_footer(text="Server has been completely nuked!")
                    await ctx.send(embed=completion_embed)

                    # Finally delete current channel if it's not the only one left
                    if len(ctx.guild.text_channels) > 1:
                        await asyncio.sleep(3)  # Give time to read the message
                        try:
                            await ctx.channel.delete(reason=f"DeleteAll command by {ctx.author}")
                        except:
                            pass  # If we can't delete current channel, just leave it

                except Exception as e:
                    await ctx.send(embed=create_error_embed(
                        "Deletion Error",
                        f"An error occurred during server nuke: {str(e)}"
                    ))

        except asyncio.TimeoutError:
            await confirm_msg.edit(embed=create_embed("⏰ Timeout", "Confirmation timed out. Server nuke cancelled."))

    @commands.command(name="deleteall-toggle", aliases=["deleteall_toggle"])
    @has_permissions(administrator=True)
    async def toggle_deleteall(self, ctx):
        """Enable or disable the deleteall command for this server"""
        current_status = await self.bot.database.get_admin_setting(ctx.guild.id, "deleteall_enabled")
        new_status = not current_status

        await self.bot.database.set_admin_setting(
            ctx.guild.id,
            "deleteall_enabled",
            new_status,
            ctx.author.id
        )

        status_text = "enabled" if new_status else "disabled"
        embed = create_success_embed(
            f"DeleteAll {status_text.title()}",
            f"The `deleteall` command has been **{status_text}** for this server."
        )

        if new_status:
            embed.add_field(
                name="⚠️ Warning",
                value="The deleteall command can permanently delete ALL channels in the server. Use with extreme caution.",
                inline=False
            )

        embed.set_footer(text=f"Changed by {ctx.author.display_name}")
        await ctx.send(embed=embed)

    @commands.command(name="deleteall-status")
    @has_permissions(administrator=True)
    async def deleteall_status(self, ctx):
        """Check if deleteall command is enabled"""
        is_enabled = await self.bot.database.get_admin_setting(ctx.guild.id, "deleteall_enabled")

        status = "Enabled ✅" if is_enabled else "Disabled ❌"
        embed = create_embed(
            "DeleteAll Status",
            f"**Status:** {status}\n\n"
            f"Use `k!deleteall-toggle` to change this setting."
        )
        await ctx.send(embed=embed)

    @commands.command(name="globaldeleteall-online")
    async def global_deleteall_online(self, ctx):
        """Enable deleteall globally (bot owners only)"""
        if not is_bot_owner(ctx.author):
            embed = create_error_embed("Access Denied", "This command is restricted to bot owners only.")
            await ctx.send(embed=embed)
            return

        await self.bot.database.set_global_setting("deleteall_global_status", "online", str(ctx.author))

        embed = create_success_embed(
            "🌐 Global Deleteall Online",
            "The `deleteall` command is now globally enabled.\nServers can enable/disable it locally with `k!deleteall-toggle`."
        )
        embed.add_field(name="Status", value="🟢 ONLINE", inline=True)
        embed.add_field(name="Set by", value=ctx.author.mention, inline=True)
        embed.set_footer(text="This affects all servers the bot is in")
        await ctx.send(embed=embed)

    @commands.command(name="globaldeleteall-offline")
    async def global_deleteall_offline(self, ctx):
        """Disable deleteall globally (bot owners only)"""
        if not is_bot_owner(ctx.author):
            embed = create_error_embed("Access Denied", "This command is restricted to bot owners only.")
            await ctx.send(embed=embed)
            return

        await self.bot.database.set_global_setting("deleteall_global_status", "offline", str(ctx.author))

        embed = create_success_embed(
            "🌐 Global Deleteall Offline",
            "The `deleteall` command is now globally disabled.\nNo server can use this command until re-enabled by the bot owner."
        )
        embed.add_field(name="Status", value="🔴 OFFLINE", inline=True)
        embed.add_field(name="Set by", value=ctx.author.mention, inline=True)
        embed.set_footer(text="This affects all servers the bot is in")
        await ctx.send(embed=embed)

    @commands.command(name="globaldeleteall-status")
    async def global_deleteall_status(self, ctx):
        """Check global deleteall status (bot owners only)"""
        if not is_bot_owner(ctx.author):
            embed = create_error_embed("Access Denied", "This command is restricted to bot owners only.")
            await ctx.send(embed=embed)
            return

        global_status = await self.bot.database.get_global_setting("deleteall_global_status")
        status = global_status if global_status else "online"  # Default to online

        if status == "online":
            status_emoji = "🟢"
            status_text = "ONLINE"
            description = "Servers can enable/disable deleteall locally"
        else:
            status_emoji = "🔴"
            status_text = "OFFLINE"
            description = "Deleteall is globally disabled for all servers"

        embed = create_embed(
            "🌐 Global Deleteall Status",
            f"Current global status: {status_emoji} **{status_text}**\n\n{description}"
        )
        embed.add_field(name="Command", value="`k!deleteall`", inline=True)
        embed.add_field(name="Global Control", value="Owner Only", inline=True)
        embed.set_footer(text="Use k!globaldeleteall-online/offline to change")
        await ctx.send(embed=embed)

    @commands.command(name="commandban")
    async def command_ban(self, ctx, user: discord.User, *, reason: str = "No reason provided"):
        """Globally ban a user from using bot commands (bot owners only)"""
        if not is_bot_owner(ctx.author):
            embed = create_error_embed("Access Denied", "This command is restricted to bot owners only.")
            await ctx.send(embed=embed)
            return

        # Add global command ban
        await self.bot.database.add_command_restriction(
            ctx.guild.id,
            user.id,
            "command_ban",
            reason,
            ctx.author.id,
            expires_at=None,
            is_global=True  # Make it global by default
        )

        # Log the action
        await self.bot.database.add_moderation_log(
            ctx.guild.id,
            user.id,
            ctx.author.id,
            "command_ban_global",
            reason
        )

        # Send DM to the user about the ban
        try:
            dm_embed = create_embed(
                "🚫 Moderation Action - Global Command Ban",
                f"**Action:** Global Command Ban\n**Reason:** {reason}\n**Moderator:** {ctx.author} ({ctx.author.mention})\n**Server:** {ctx.guild.name}\n\n"
                f"You have been banned from using bot commands across all servers.\n"
                f"You can appeal using: `k!appealcommandban <reason>`"
            )
            await user.send(embed=dm_embed)
        except discord.Forbidden:
            pass  # User has DMs disabled

        embed = create_success_embed(
            "⛔ Global Command Ban",
            f"**User:** {user.mention} ({user.id})\n"
            f"**Reason:** {reason}\n"
            f"**Moderator:** {ctx.author.mention}\n\n"
            f"This user is now **globally banned** from using any bot commands across all servers.\n"
            f"They can appeal using: `k!appealcommandban <reason>`"
        )
        embed.set_footer(text="Global ban applies to all servers")
        await ctx.send(embed=embed)

    @commands.command(name="commandmute")
    async def command_mute(self, ctx, user: discord.User, duration: str = None, *, reason: str = "No reason provided"):
        """Globally mute a user from using bot commands (bot owners only)"""
        if not is_bot_owner(ctx.author):
            embed = create_error_embed("Access Denied", "This command is restricted to bot owners only.")
            await ctx.send(embed=embed)
            return

        # Parse duration
        expires_at = None
        duration_text = "indefinitely"
        if duration:
            try:
                # Simple duration parsing (e.g., "1h", "30m", "2d")
                import re
                from datetime import datetime, timedelta

                match = re.match(r'(\d+)([hdm])', duration.lower())
                if match:
                    amount = int(match.group(1))
                    unit = match.group(2)

                    if unit == 'm':
                        delta = timedelta(minutes=amount)
                        duration_text = f"{amount} minute{'s' if amount != 1 else ''}"
                    elif unit == 'h':
                        delta = timedelta(hours=amount)
                        duration_text = f"{amount} hour{'s' if amount != 1 else ''}"
                    elif unit == 'd':
                        delta = timedelta(days=amount)
                        duration_text = f"{amount} day{'s' if amount != 1 else ''}"

                    expires_at = (datetime.now() + delta).isoformat()
            except:
                duration_text = "indefinitely"

        # Add global command mute
        await self.bot.database.add_command_restriction(
            ctx.guild.id,
            user.id,
            "command_mute",
            reason,
            ctx.author.id,
            expires_at=expires_at,
            is_global=True  # Make it global by default
        )

        # Log the action
        await self.bot.database.add_moderation_log(
            ctx.guild.id,
            user.id,
            ctx.author.id,
            "command_mute_global",
            f"{reason} (Duration: {duration_text})"
        )

        # Send DM to the user about the mute
        try:
            dm_embed = create_embed(
                "🔇 Moderation Action - Global Command Mute",
                f"**Action:** Global Command Mute\n**Duration:** {duration_text}\n**Reason:** {reason}\n**Moderator:** {ctx.author} ({ctx.author.mention})\n**Server:** {ctx.guild.name}\n\n"
                f"You have been muted from using bot commands across all servers for {duration_text}."
            )
            await user.send(embed=dm_embed)
        except discord.Forbidden:
            pass  # User has DMs disabled

        embed = create_success_embed(
            "🔇 Global Command Mute",
            f"**User:** {user.mention} ({user.id})\n"
            f"**Duration:** {duration_text}\n"
            f"**Reason:** {reason}\n"
            f"**Moderator:** {ctx.author.mention}\n\n"
            f"This user is now **globally muted** from using any bot commands across all servers."
        )
        embed.set_footer(text="Global mute applies to all servers")
        await ctx.send(embed=embed)

    @commands.command(name="commandunban")
    async def command_unban(self, ctx, user: discord.User):
        """Globally unban a user from using bot commands (bot owners only)"""
        if not is_bot_owner(ctx.author):
            embed = create_error_embed("Access Denied", "This command is restricted to bot owners only.")
            await ctx.send(embed=embed)
            return

        # Remove global command restriction
        await self.bot.database.remove_global_command_restriction(user.id)

        # Log the action
        await self.bot.database.add_moderation_log(
            ctx.guild.id,
            user.id,
            ctx.author.id,
            "command_unban_global",
            "Global command ban removed"
        )

        embed = create_success_embed(
            "✅ Global Command Unban",
            f"**User:** {user.mention} ({user.id})\n"
            f"**Moderator:** {ctx.author.mention}\n\n"
            f"This user can now use bot commands again across all servers."
        )
        embed.set_footer(text="Global unban applies to all servers")
        await ctx.send(embed=embed)

    @commands.command(name="commandunmute")
    async def command_unmute(self, ctx, user: discord.User):
        """Globally unmute a user from using bot commands (bot owners only)"""
        if not is_bot_owner(ctx.author):
            embed = create_error_embed("Access Denied", "This command is restricted to bot owners only.")
            await ctx.send(embed=embed)
            return

    @commands.command(name="addowner")
    async def add_owner(self, ctx, member: discord.Member, *, reason: str = "Added as bot owner"):
        """Add a user as a bot owner (can manage bot admins) - Original owners only"""
        if not is_bot_owner(ctx.author):
            embed = create_error_embed("Access Denied", "This command is restricted to the original bot owners only.")
            await ctx.send(embed=embed)
            return

        if member.id == ctx.author.id:
            embed = create_error_embed("Error", "You cannot add yourself as owner!")
            await ctx.send(embed=embed)
            return

        if member.bot:
            embed = create_error_embed("Error", "You cannot add bots as owners!")
            await ctx.send(embed=embed)
            return

        # Check if already a bot owner
        if is_bot_owner(member) or (self.bot.database and await self.bot.database.is_bot_owner_db(member.id)):
            embed = create_error_embed("Already Owner", f"{member.mention} is already a bot owner!")
            await ctx.send(embed=embed)
            return

        # Add to database
        if self.bot.database:
            await self.bot.database.add_bot_owner(member.id, reason, ctx.author.id)

        embed = create_success_embed(
            "✅ Bot Owner Added",
            f"**User:** {member.mention}\n**Reason:** {reason}\n**Added by:** {ctx.author.mention}\n\n"
            f"{member.mention} can now manage bot admins using `k!addadmin` and `k!removeadmin` commands."
        )
        await ctx.send(embed=embed)

    @commands.command(name="removeowner")
    async def remove_owner(self, ctx, member: discord.Member, *, reason: str = "Owner privileges revoked"):
        """Remove a user's bot owner privileges - Original owners only"""
        if not is_bot_owner(ctx.author):
            embed = create_error_embed("Access Denied", "This command is restricted to the original bot owners only.")
            await ctx.send(embed=embed)
            return

        if is_bot_owner(member):
            embed = create_error_embed("Error", "You cannot remove original bot owners!")
            await ctx.send(embed=embed)
            return

        # Check if they're a database bot owner
        if not (self.bot.database and await self.bot.database.is_bot_owner_db(member.id)):
            embed = create_error_embed("Not Owner", f"{member.mention} is not a bot owner!")
            await ctx.send(embed=embed)
            return

        # Remove from database
        await self.bot.database.remove_bot_owner(member.id)

        embed = create_success_embed(
            "✅ Bot Owner Removed",
            f"**User:** {member.mention}\n**Reason:** {reason}\n**Removed by:** {ctx.author.mention}\n\n"
            f"{member.mention} can no longer manage bot admins."
        )
        await ctx.send(embed=embed)

    @commands.command(name="owners")
    async def list_owners(self, ctx):
        """List all bot owners - Admin/Owner only"""
        if not (is_bot_owner(ctx.author) or (self.bot.database and await self.bot.database.is_admin_user(ctx.author.id))):
            embed = create_error_embed("Access Denied", "Only owners and admins can view the owner list.")
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title="🤴 Bot Owners",
            color=discord.Color.gold()
        )

        # Original owners
        # Get current bot owners from database and hardcoded list
        hardcoded_owners = []
        for owner_id in BOT_OWNERS:
            try:
                owner_user = await self.bot.fetch_user(owner_id)
                hardcoded_owners.append(f"• {owner_user} (Hardcoded)")
            except:
                hardcoded_owners.append(f"• <@{owner_id}> (Hardcoded)")

        original_owners = "\n".join(hardcoded_owners)
        embed.add_field(
            name="🔱 Original Owners",
            value=original_owners or "None",
            inline=False
        )

        # Database owners
        if self.bot.database:
            db_owners = await self.bot.database.get_all_bot_owners()
            if db_owners:
                owner_list = []
                for user_id, reason, granted_by, timestamp in db_owners:
                    try:
                        user = self.bot.get_user(user_id)
                        if user:
                            owner_list.append(f"• {user} - {reason}")
                        else:
                            owner_list.append(f"• User ID: {user_id} - {reason}")
                    except:
                        owner_list.append(f"• User ID: {user_id} - {reason}")

                embed.add_field(
                    name="👑 Added Owners",
                    value="\n".join(owner_list) or "None",
                    inline=False
                )
            else:
                embed.add_field(
                    name="👑 Added Owners",
                    value="None",
                    inline=False
                )

        await ctx.send(embed=embed)

        # Remove global command restriction
        await self.bot.database.remove_global_command_restriction(user.id)

        # Log the action
        await self.bot.database.add_moderation_log(
            ctx.guild.id,
            user.id,
            ctx.author.id,
            "command_unmute_global",
            "Global command mute removed"
        )

        embed = create_success_embed(
            "✅ Global Command Unmute",
            f"**User:** {user.mention} ({user.id})\n"
            f"**Moderator:** {ctx.author.mention}\n\n"
            f"This user can now use bot commands again across all servers."
        )
        embed.set_footer(text="Global unmute applies to all servers")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AdminCog(bot))