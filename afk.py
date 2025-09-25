import discord
from discord.ext import commands
import logging
from datetime import datetime
from ..utils import create_embed, create_error_embed, create_success_embed

logger = logging.getLogger(__name__)

class AFKCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        """Check for AFK mentions and remove AFK status when user speaks"""
        if message.author.bot:
            return

        # Check if the user is AFK and remove their status
        if self.bot.database:
            afk_data = await self.bot.database.get_afk_user(message.author.id, message.guild.id)
            if afk_data:
                await self.bot.database.remove_afk(message.author.id, message.guild.id)
                
                # Calculate how long they were AFK
                afk_time = datetime.fromisoformat(afk_data[1])
                now = datetime.now()
                duration = now - afk_time
                
                hours, remainder = divmod(duration.total_seconds(), 3600)
                minutes, _ = divmod(remainder, 60)
                
                if hours > 0:
                    time_str = f"{int(hours)}h {int(minutes)}m"
                else:
                    time_str = f"{int(minutes)}m"
                
                embed = create_embed(
                    "Welcome Back!",
                    f"{message.author.mention}, you are no longer AFK. You were away for {time_str}.",
                    discord.Color.green()
                )
                await message.channel.send(embed=embed, delete_after=10)

        # Check for mentions of AFK users
        for user in message.mentions:
            if user.bot:
                continue
            
            if self.bot.database:
                afk_data = await self.bot.database.get_afk_user(user.id, message.guild.id)
                if afk_data:
                    afk_message, afk_time = afk_data
                    
                    # Calculate how long they've been AFK
                    afk_datetime = datetime.fromisoformat(afk_time)
                    now = datetime.now()
                    duration = now - afk_datetime
                    
                    hours, remainder = divmod(duration.total_seconds(), 3600)
                    minutes, _ = divmod(remainder, 60)
                    
                    if hours > 0:
                        time_str = f"{int(hours)}h {int(minutes)}m ago"
                    else:
                        time_str = f"{int(minutes)}m ago"
                    
                    embed = create_embed(
                        "User is AFK",
                        f"{user.display_name} is currently AFK: {afk_message}\n**Since:** {time_str}",
                        discord.Color.orange()
                    )
                    await message.channel.send(embed=embed, delete_after=15)

    @commands.command(name="afk")
    async def set_afk(self, ctx, *, message: str = "AFK"):
        """Set yourself as AFK with an optional message"""
        if len(message) > 200:
            await ctx.send(embed=create_error_embed("Message Too Long", "AFK message cannot be longer than 200 characters."))
            return

        await self.bot.database.set_afk(ctx.author.id, ctx.guild.id, message)
        
        embed = create_embed(
            "AFK Set",
            f"{ctx.author.mention} is now AFK: {message}",
            discord.Color.yellow()
        )
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AFKCog(bot))
