import discord
from discord.ext import commands
import logging
import os
import asyncio
from pathlib import Path
from .database import DatabaseManager
from .utils import create_embed, create_error_embed

logger = logging.getLogger(__name__)

class DiscordBot(commands.Bot):
    def __init__(self):
        # Set up intents
        intents = discord.Intents.all()

        # Initialize bot with prefix and intents
        super().__init__(
            command_prefix='k!',
            intents=intents,
            case_insensitive=True,
            help_command=None
        )

        self.database = None
        self.initial_extensions = [
            'bot.cogs.template',
            'bot.cogs.moderation',
            'bot.cogs.general',
            'bot.cogs.afk',
            'bot.cogs.admin',
            'bot.cogs.verification',
            'bot.cogs.music',
            'bot.cogs.fun',
        ]

    async def get_prefix(self, message):
        """Get the command prefix for a guild"""
        if not message.guild:
            return 'k!'

        # Get prefix from database, default to 'k!'
        if self.database:
            prefix = await self.database.get_guild_prefix(message.guild.id)
            return prefix or 'k!'
        return 'k!'

    async def setup_hook(self):
        """Set up the bot"""
        logger.info("Initializing database...")
        self.database = DatabaseManager()
        await self.database.initialize()

        logger.info("Loading cogs...")
        for extension in self.initial_extensions:
            try:
                await self.load_extension(extension)
                logger.info(f"Loaded cog: {extension.split('.')[-1]}")
            except Exception as e:
                logger.error(f"Failed to load cog {extension}: {e}")

        logger.info("Bot setup complete!")

    async def on_ready(self):
        """Event that runs when bot is ready"""
        logger.info(f"Bot is ready! Logged in as {self.user}")
        logger.info(f"Bot ID: {self.user.id}")
        logger.info(f"Servers: {len(self.guilds)}")

        # Sync slash commands
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} slash commands")
        except Exception as e:
            logger.error(f"Failed to sync slash commands: {e}")

        # Log connected servers
        for guild in self.guilds:
            logger.info(f"Connected to: {guild.name} (ID: {guild.id})")

    async def on_app_command_completion(self, interaction: discord.Interaction, command):
        """Called when a slash command is completed"""
        pass

    async def on_interaction(self, interaction: discord.Interaction):
        """Handle all interactions including slash commands"""
        if interaction.type == discord.InteractionType.application_command:
            # Skip check for the bot owner
            if str(interaction.user) == "kh2.officialedits":
                return await super().on_interaction(interaction)

            # Allow appealcommandban command to bypass restrictions
            if interaction.data.get("name") == "appealcommandban":
                return await super().on_interaction(interaction)

            # Check if user has command restrictions for slash commands
            if self.database and interaction.guild:
                restriction = await self.database.get_command_restriction(interaction.guild.id, interaction.user.id)
                if restriction:
                    restriction_type = restriction["type"]
                    expires_at = restriction.get("expires_at")
                    
                    if restriction_type == "command_ban":
                        embed = create_error_embed(
                            "⛔ Command Banned",
                            f"Hello {interaction.user.mention}. You are banned. You can appeal at: /appealcommandban or k!appealcommandban"
                        )
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                        return
                    elif restriction_type == "command_mute":
                        # Calculate remaining duration for muted users
                        duration_text = "indefinitely"
                        if expires_at:
                            try:
                                from datetime import datetime
                                expires_datetime = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                                now = datetime.now()
                                remaining = expires_datetime - now
                                
                                if remaining.total_seconds() > 0:
                                    days = remaining.days
                                    hours, remainder = divmod(remaining.seconds, 3600)
                                    minutes, _ = divmod(remainder, 60)
                                    
                                    if days > 0:
                                        duration_text = f"{days}d {hours}h {minutes}m"
                                    elif hours > 0:
                                        duration_text = f"{hours}h {minutes}m"
                                    else:
                                        duration_text = f"{minutes}m"
                                else:
                                    # Restriction has expired, remove it
                                    await self.database.remove_command_restriction(interaction.guild.id, interaction.user.id)
                                    return await super().on_interaction(interaction)
                            except:
                                duration_text = "unknown duration"
                        
                        embed = create_error_embed(
                            "🔇 Command Muted",
                            f"Hello {interaction.user.mention}. You are muted for duration {duration_text}"
                        )
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                        return

        # Process the interaction normally
        return await super().on_interaction(interaction)

    async def on_guild_join(self, guild):
        """Called when the bot joins a new guild"""
        logger.info(f"Joined new guild: {guild.name} (ID: {guild.id})")
        if self.database:
            await self.database.create_guild_entry(guild.id)

    async def process_commands(self, message):
        """Override process_commands to handle command restrictions globally"""
        if message.author.bot:
            return

        # Get context
        ctx = await self.get_context(message)
        
        # If no valid command found, use default processing
        if not ctx.valid:
            await super().process_commands(message)
            return

        # Skip check for the bot owner
        if str(ctx.author) == "kh2.officialedits":
            await super().process_commands(message)
            return

        # Allow appealcommandban command to bypass restrictions
        if ctx.command and ctx.command.name == "appealcommandban":
            await super().process_commands(message)
            return

        # Check if user has command restrictions in database (global check for all cogs)
        if self.database and ctx.guild:
            restriction = await self.database.get_command_restriction(ctx.guild.id, ctx.author.id)
            if restriction:
                restriction_type = restriction["type"]
                expires_at = restriction.get("expires_at")
                
                if restriction_type == "command_ban":
                    embed = create_error_embed(
                        "⛔ Command Banned",
                        f"Hello {ctx.author.mention}. You are banned. You can appeal at: /appealcommandban"
                    )
                    await ctx.send(embed=embed)
                    return
                elif restriction_type == "command_mute":
                    # Calculate remaining duration for muted users
                    duration_text = "indefinitely"
                    if expires_at:
                        try:
                            from datetime import datetime
                            expires_datetime = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                            now = datetime.now()
                            remaining = expires_datetime - now
                            
                            if remaining.total_seconds() > 0:
                                days = remaining.days
                                hours, remainder = divmod(remaining.seconds, 3600)
                                minutes, _ = divmod(remainder, 60)
                                
                                if days > 0:
                                    duration_text = f"{days}d {hours}h {minutes}m"
                                elif hours > 0:
                                    duration_text = f"{hours}h {minutes}m"
                                else:
                                    duration_text = f"{minutes}m"
                            else:
                                # Restriction has expired, remove it
                                await self.database.remove_command_restriction(ctx.guild.id, ctx.author.id)
                                await super().process_commands(message)
                                return
                        except:
                            duration_text = "unknown duration"
                    
                    embed = create_error_embed(
                        "🔇 Command Muted",
                        f"Hello {ctx.author.mention}. You are muted for duration {duration_text}"
                    )
                    await ctx.send(embed=embed)
                    return

        # Process the command normally
        await super().process_commands(message)

    async def on_command_error(self, ctx, error):
        """Global error handler for commands"""
        if isinstance(error, commands.CheckFailure):
            # This will be handled by the cog_check, so we don't need to do anything
            return
        elif isinstance(error, commands.BotMissingPermissions):
            await ctx.send(embed=create_error_embed("Missing Permissions", "I don't have the required permissions to execute this command."))
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send(embed=create_error_embed("Missing Permissions", "You don't have the required permissions to use this command."))
        elif isinstance(error, commands.CommandNotFound):
            # Don't send anything for regular command not found
            return
        else:
            logger.error(f"Unhandled error in command {ctx.command}: {error}")
            await ctx.send(embed=create_error_embed("Error", "An unexpected error occurred."))

    async def close(self):
        """Clean shutdown of the bot"""
        logger.info("Bot is shutting down...")

        # Close database connection
        if self.database:
            await self.database.close()

        # Call the parent close method
        await super().close()