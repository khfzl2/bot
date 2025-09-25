import discord
from discord.ext import commands
import logging
import os
import asyncio
import aiohttp
from pathlib import Path
from .database import DatabaseManager
from .utils import create_embed, create_error_embed, is_bot_owner

logger = logging.getLogger(__name__)

class DiscordBot(commands.Bot):
    def __init__(self):
        # Set up intents
        intents = discord.Intents.all()

        # Initialize bot with prefix and intents
        super().__init__(
            command_prefix=self.get_prefix,  # Use the method as callable
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
            'bot.cogs.ai',
            'bot.cogs.utility',
            'bot.cogs.image'
        ]

    async def get_prefix(self, message):
        """Get the command prefix for a guild - FIXED METHOD SIGNATURE"""
        if not message.guild:
            return 'k!'

        # Get prefix from database, default to 'k!'
        if self.database:
            try:
                prefix = await self.database.get_guild_prefix(message.guild.id)
                return prefix or 'k!'
            except Exception as e:
                logger.error(f"Error getting prefix for guild {message.guild.id}: {e}")
                return 'k!'
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

        # No slash commands - only k! prefix commands
        logger.info("Using k! prefix commands only - no slash commands")

        # Log connected servers
        for guild in self.guilds:
            logger.info(f"Connected to: {guild.name} (ID: {guild.id})")

    async def on_app_command_completion(self, interaction: discord.Interaction, command):
        """Called when a slash command is completed"""
        pass

    async def on_interaction(self, interaction: discord.Interaction):
        """Handle all interactions including slash commands"""
        if interaction.type == discord.InteractionType.application_command:
            # Skip check for bot owners
            if is_bot_owner(interaction.user):
                return await self.process_application_commands(interaction)

            # Allow appealcommandban command to bypass restrictions
            if interaction.data.get("name") == "appealcommandban":
                return await self.process_application_commands(interaction)

            # Check if user has command restrictions
            if self.database and interaction.guild:
                # Check if user is owner or admin (they can bypass server bans but not personal bans)
                is_admin = is_bot_owner(interaction.user) or await self.database.is_admin_user(interaction.user.id)

                # Check for server command ban first (admins can bypass this)
                if not is_admin and await self.database.is_server_command_banned(interaction.guild.id):
                    embed = create_error_embed(
                        "🚫 Server Command Banned",
                        f"This server is banned from using bot commands. Contact the bot administrators for more information."
                    )
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                    return

                restriction = await self.database.get_command_restriction(interaction.guild.id, interaction.user.id)
                if restriction:
                    restriction_type = restriction["type"]
                    expires_at = restriction.get("expires_at")

                    if restriction_type == "command_ban":
                        embed = create_error_embed(
                            "⛔ Command Banned",
                            f"Hello {interaction.user.mention}. You are banned. You can appeal at: /appealcommandban"
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
                                    # Mute has expired, remove it
                                    await self.database.remove_command_restriction(interaction.guild.id, interaction.user.id)
                                    return await self.process_application_commands(interaction)
                            except:
                                pass

                        embed = create_error_embed(
                            "🔇 Command Muted",
                            f"Hello {interaction.user.mention}. You are muted from using commands for {duration_text}."
                        )
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                        return

            # Process the interaction normally
            return await self.process_application_commands(interaction)

        # Handle other interaction types normally
        await self.dispatch('interaction', interaction)

    async def on_guild_join(self, guild):
        """Called when the bot joins a new guild"""
        logger.info(f"Joined new guild: {guild.name} (ID: {guild.id})")
        if self.database:
            await self.database.create_guild_entry(guild.id)

    async def process_commands(self, message):
        """Override process_commands to handle command restrictions only for actual commands"""
        if message.author.bot:
            return

        # Get context to see if this is actually a command
        ctx = await self.get_context(message)
        
        # Only check restrictions if this is a valid command
        if ctx.valid and ctx.command and self.database and message.guild:
            # Skip check for bot owners
            if not is_bot_owner(message.author):
                # Allow appealcommandban command to bypass restrictions
                if ctx.command.name == "appealcommandban":
                    return await super().process_commands(message)
                
                # Check if user is owner or admin (they can bypass server bans but not personal bans)
                is_admin = is_bot_owner(message.author) or await self.database.is_admin_user(message.author.id)

                # Check for server command ban first (admins can bypass this)
                if not is_admin and await self.database.is_server_command_banned(message.guild.id):
                    embed = create_error_embed(
                        "🚫 Server Command Banned",
                        f"This server is banned from using bot commands. Contact the bot administrators for more information."
                    )
                    await message.channel.send(embed=embed)
                    return

                restriction = await self.database.get_command_restriction(message.guild.id, message.author.id)
                if restriction:
                    restriction_type = restriction["type"]
                    expires_at = restriction.get("expires_at")

                    if restriction_type == "command_ban":
                        embed = create_error_embed(
                            "⛔ Command Banned",
                            f"Hello {message.author.mention}. You are banned from using commands. You can appeal at: `k!appealcommandban <reason>`"
                        )
                        await message.channel.send(embed=embed)
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
                                    await self.database.remove_command_restriction(message.guild.id, message.author.id)
                                    return await super().process_commands(message)
                            except:
                                duration_text = "unknown duration"

                        embed = create_error_embed(
                            "🔇 Command Muted",
                            f"Hello {message.author.mention}. You are muted from using commands for {duration_text}"
                        )
                        await message.channel.send(embed=embed)
                        return

        # Check if bot is mentioned and respond with AI
        if self.user in message.mentions and not message.author.bot:
            # Remove the mention from the message to get the actual question
            content = message.content
            for mention in message.mentions:
                content = content.replace(f'<@{mention.id}>', '').replace(f'<@!{mention.id}>', '')
            content = content.strip()

            if content:  # Only respond if there's actual content after removing mentions
                await self.handle_ai_mention(message, content)
                return

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

    async def handle_ai_mention(self, message, question):
        """Handle AI responses when bot is mentioned"""
        # Get API key from environment
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            embed = create_error_embed("AI Unavailable", "AI service is currently unavailable.")
            await message.channel.send(embed=embed)
            return

        embed = create_embed("🤖 Thinking...", f"Processing your question: `{question}`")
        response_message = await message.channel.send(embed=embed)

        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://replit.com",
                    "X-Title": "Discord Bot"
                }

                payload = {
                    "model": "deepseek/deepseek-chat",
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant in a Discord server. Keep responses concise and friendly. You were mentioned in a message and should respond naturally."},
                        {"role": "user", "content": question}
                    ],
                    "max_tokens": 500,
                    "temperature": 0.7
                }

                async with session.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        answer = data["choices"][0]["message"]["content"]

                        embed = discord.Embed(
                            title="🤖 AI Response (DeepSeek)",
                            color=discord.Color.blue()
                        )
                        embed.add_field(name="Question", value=question, inline=False)
                        embed.add_field(name="Answer", value=answer, inline=False)
                        embed.set_footer(text=f"Asked by {message.author.display_name}")

                        await response_message.edit(embed=embed)
                    else:
                        error_text = await response.text()
                        logger.error(f"OpenRouter API error: {response.status} - {error_text}")
                        await response_message.edit(embed=create_error_embed("AI Response Failed", "Sorry, I couldn't process your question. Please try again later."))

        except Exception as e:
            logger.error(f"Error processing mention question: {e}")
            await response_message.edit(embed=create_error_embed("AI Response Failed", "Sorry, I couldn't process your question. Please try again later."))