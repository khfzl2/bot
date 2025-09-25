import discord
from discord.ext import commands
import aiohttp
import json
import asyncio
import base64
import random
import datetime
import re
from ..utils import create_embed, create_error_embed, create_success_embed

class UtilityCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="avatar", aliases=["av", "pfp"])
    async def avatar(self, ctx, member: discord.Member | None = None):
        """Get someone's avatar"""
        if member is None:
            member = ctx.author

        embed = discord.Embed(
            title=f"🖼️ {member.display_name}'s Avatar",
            color=discord.Color.blue()
        )
        avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
        embed.set_image(url=avatar_url)
        
        if member.avatar:
            embed.add_field(name="Download Links", 
                           value=f"[PNG]({member.avatar.with_format('png').url}) | [JPG]({member.avatar.with_format('jpg').url}) | [WEBP]({member.avatar.url})", 
                           inline=False)
        else:
            embed.add_field(name="Download Links", 
                           value="Default avatar - no custom download links available", 
                           inline=False)
        await ctx.send(embed=embed)

    @commands.command(name="userinfo", aliases=["ui", "whois"])
    async def user_info(self, ctx, member: discord.Member | None = None):
        """Get information about a user"""
        if member is None:
            member = ctx.author

        embed = discord.Embed(
            title=f"👤 {member.display_name}",
            color=member.color if member.color != discord.Color.default() else discord.Color.blue()
        )

        embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)

        embed.add_field(name="Username", value=str(member), inline=True)
        embed.add_field(name="ID", value=member.id, inline=True)
        embed.add_field(name="Status", value=str(member.status).title(), inline=True)

        embed.add_field(name="Account Created", value=member.created_at.strftime("%B %d, %Y"), inline=True)
        embed.add_field(name="Joined Server", value=member.joined_at.strftime("%B %d, %Y") if member.joined_at else "Unknown", inline=True)
        embed.add_field(name="Roles", value=f"{len(member.roles)} roles", inline=True)

        if member.premium_since:
            embed.add_field(name="Boosting Since", value=member.premium_since.strftime("%B %d, %Y"), inline=True)

        await ctx.send(embed=embed)

    @commands.command(name="weather")
    async def weather(self, ctx, *, city: str | None = None):
        """Get weather information (mock command - you'd need a weather API)"""
        if not city:
            await ctx.send(embed=create_error_embed("Missing City", "Please specify a city name!"))
            return

        # Mock weather data
        weather_conditions = ["Sunny", "Cloudy", "Rainy", "Snowy", "Windy", "Foggy"]
        temperature = random.randint(-10, 35)
        condition = random.choice(weather_conditions)

        embed = create_embed(
            f"🌤️ Weather in {city.title()}",
            f"**Temperature:** {temperature}°C\n**Condition:** {condition}\n\n*Note: This is mock data for demonstration*"
        )
        await ctx.send(embed=embed)

    @commands.command(name="quote")
    async def random_quote(self, ctx):
        """Get a random inspirational quote"""
        quotes = [
            "The only way to do great work is to love what you do. - Steve Jobs",
            "Innovation distinguishes between a leader and a follower. - Steve Jobs",
            "Life is what happens to you while you're busy making other plans. - John Lennon",
            "The future belongs to those who believe in the beauty of their dreams. - Eleanor Roosevelt",
            "It is during our darkest moments that we must focus to see the light. - Aristotle",
            "Success is not final, failure is not fatal: it is the courage to continue that counts. - Winston Churchill",
            "The only impossible journey is the one you never begin. - Tony Robbins"
        ]

        quote = random.choice(quotes)
        embed = create_embed("💭 Random Quote", f"*{quote}*")
        await ctx.send(embed=embed)

    @commands.command(name="color", aliases=["colour"])
    async def color_info(self, ctx, *, color_code: str | None = None):
        """Get information about a color (hex code)"""
        if not color_code:
            # Generate random color
            color_code = f"#{random.randint(0, 0xFFFFFF):06x}"

        # Remove # if present
        color_code = color_code.replace("#", "")

        try:
            color_int = int(color_code, 16)
            color = discord.Color(color_int)

            embed = discord.Embed(
                title=f"🎨 Color: #{color_code.upper()}",
                color=color
            )
            embed.add_field(name="Hex", value=f"#{color_code.upper()}", inline=True)
            embed.add_field(name="RGB", value=f"({color.r}, {color.g}, {color.b})", inline=True)
            embed.add_field(name="Integer", value=str(color_int), inline=True)

            await ctx.send(embed=embed)
        except ValueError:
            await ctx.send(embed=create_error_embed("Invalid Color", "Please provide a valid hex color code (e.g., #FF0000 or FF0000)"))

    @commands.command(name="reminder", aliases=["remindme"])
    async def reminder(self, ctx, time: str, *, message: str):
        """Set a reminder (format: 1m, 1h, 1d)"""
        time_units = {"s": 1, "m": 60, "h": 3600, "d": 86400}

        try:
            if time[-1] in time_units:
                duration = int(time[:-1]) * time_units[time[-1]]
                unit = time[-1]
            else:
                raise ValueError("Invalid time format")

            if duration > 604800:  # 7 days max
                await ctx.send(embed=create_error_embed("Time Too Long", "Reminders can only be set for up to 7 days."))
                return

            embed = create_success_embed("⏰ Reminder Set", f"I'll remind you about: `{message}` in {time}")
            await ctx.send(embed=embed)

            await asyncio.sleep(duration)

            reminder_embed = create_embed("⏰ Reminder", f"You asked me to remind you about: `{message}`")
            try:
                await ctx.author.send(embed=reminder_embed)
            except discord.Forbidden:
                await ctx.send(f"{ctx.author.mention}", embed=reminder_embed)

        except (ValueError, IndexError):
            await ctx.send(embed=create_error_embed("Invalid Format", "Use format like: `1m`, `2h`, `1d` (minutes, hours, days)"))

    @commands.command(name="urban", aliases=["define"])
    async def urban_dictionary(self, ctx, *, term: str):
        """Get definition from Urban Dictionary (mock - you'd need the actual API)"""
        # Mock definition for demonstration
        definitions = [
            f"**{term.title()}**: A very cool and awesome thing that everyone should know about!",
            f"**{term.title()}**: Something mysterious and wonderful that defies explanation.",
            f"**{term.title()}**: The ultimate expression of awesomeness in the modern world."
        ]

        definition = random.choice(definitions)
        embed = create_embed(f"📚 Definition: {term.title()}", f"{definition}\n\n*Note: This is mock data for demonstration*")
        await ctx.send(embed=embed)

    @commands.command(name="binary")
    async def text_to_binary(self, ctx, *, text: str):
        """Convert text to binary"""
        if len(text) > 100:
            await ctx.send(embed=create_error_embed("Text Too Long", "Please keep text under 100 characters."))
            return

        binary = ' '.join(format(ord(char), '08b') for char in text)
        embed = create_embed("🔢 Text to Binary", f"**Original:** {text}\n**Binary:** `{binary}`")
        await ctx.send(embed=embed)

    @commands.command(name="base64")
    async def text_to_base64(self, ctx, *, text: str):
        """Convert text to base64"""
        if len(text) > 500:
            await ctx.send(embed=create_error_embed("Text Too Long", "Please keep text under 500 characters."))
            return

        encoded = base64.b64encode(text.encode()).decode()
        embed = create_embed("🔐 Text to Base64", f"**Original:** {text}\n**Base64:** `{encoded}`")
        await ctx.send(embed=embed)

    @commands.command(name="countdown")
    async def countdown(self, ctx, seconds: int):
        """Start a countdown timer"""
        if seconds > 60 or seconds < 1:
            await ctx.send(embed=create_error_embed("Invalid Time", "Countdown must be between 1 and 60 seconds."))
            return

        embed = create_embed("⏰ Countdown", f"Starting countdown from {seconds} seconds...")
        message = await ctx.send(embed=embed)

        for i in range(seconds, 0, -1):
            embed = create_embed("⏰ Countdown", f"**{i}** seconds remaining...")
            await message.edit(embed=embed)
            await asyncio.sleep(1)

        embed = create_success_embed("⏰ Countdown Complete", "Time's up! 🎉")
        await message.edit(embed=embed)

    @commands.command(name="poll")
    async def poll(self, ctx, question: str, *options):
        """Create a poll with reactions"""
        if len(options) < 2:
            await ctx.send(embed=create_error_embed("Not Enough Options", "Please provide at least 2 options for the poll."))
            return

        if len(options) > 10:
            await ctx.send(embed=create_error_embed("Too Many Options", "Please provide at most 10 options for the poll."))
            return

        reactions = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

        embed = discord.Embed(title="📊 Poll", description=question, color=discord.Color.blue())

        for i, option in enumerate(options):
            embed.add_field(name=f"{reactions[i]} Option {i+1}", value=option, inline=False)

        embed.set_footer(text=f"Poll created by {ctx.author.display_name}")

        poll_message = await ctx.send(embed=embed)

        for i in range(len(options)):
            await poll_message.add_reaction(reactions[i])



async def setup(bot):
    await bot.add_cog(UtilityCog(bot))