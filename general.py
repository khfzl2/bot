import discord
from discord.ext import commands
import time
import psutil
import platform
from ..utils import create_embed, is_bot_owner

def is_kh2_official(ctx):
    """Check if user is one of the bot owners"""
    return is_bot_owner(ctx.author)

class GeneralCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()

    @commands.command(name="ping")
    async def ping(self, ctx):
        """Check the bot's latency"""
        latency = round(self.bot.latency * 1000)
        embed = create_embed("🏓 Pong!", f"Latency: {latency}ms")
        await ctx.send(embed=embed)

    @commands.command(name="info", aliases=["botinfo"])
    async def info_command(self, ctx):
        """Display information about the bot"""
        uptime = time.time() - self.start_time
        hours, remainder = divmod(uptime, 3600)
        minutes, seconds = divmod(remainder, 60)

        embed = discord.Embed(
            title="🤖 Bot Information",
            description="A powerful Discord bot with moderation and utility features",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="📊 Statistics",
            value=f"**Servers:** {len(self.bot.guilds)}\n**Users:** {len(self.bot.users)}\n**Commands:** {len(self.bot.commands)}",
            inline=True
        )

        embed.add_field(
            name="⏱️ Uptime",
            value=f"{int(hours)}h {int(minutes)}m {int(seconds)}s",
            inline=True
        )

        embed.add_field(
            name="💻 System",
            value=f"**Python:** {platform.python_version()}\n**discord.py:** {discord.__version__}\n**CPU:** {psutil.cpu_percent()}%",
            inline=True
        )

        embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        embed.set_footer(text=f"Bot ID: {self.bot.user.id}")

        await ctx.send(embed=embed)

    @commands.command(name="commandcount", aliases=["cmdcount", "commands"])
    async def command_count(self, ctx):
        """Display detailed command count statistics"""
        embed = discord.Embed(
            title="📊 Command Statistics",
            description="Detailed breakdown of all available commands",
            color=discord.Color.blue()
        )

        # Category mappings with emojis
        category_emojis = {
            'template': '📋',
            'moderation': '🔨', 
            'general': '🔧',
            'admin': '⚙️',
            'utility': '🛠️',
            'afk': '💤',
            'verification': '✅',
            'fun': '🎮',
            'music': '🎵',
            'ai': '🤖',
            'image': '🖼️'
        }
        
        # Get all commands organized by cog
        cog_commands = {}
        total_commands = 0
        hidden_commands = 0
        
        for command in self.bot.commands:
            if command.hidden:
                hidden_commands += 1
                continue
                
            total_commands += 1
            cog_name = command.cog_name.lower() if command.cog_name else 'other'
            if 'cog' in cog_name:
                cog_name = cog_name.replace('cog', '')
            
            if cog_name not in cog_commands:
                cog_commands[cog_name] = 0
            cog_commands[cog_name] += 1
        
        # Add total counts
        embed.add_field(
            name="🎯 Total Commands",
            value=f"**Available:** {total_commands}\n**Hidden:** {hidden_commands}\n**Total:** {total_commands + hidden_commands}",
            inline=True
        )
        
        # Add cog breakdown
        cog_stats = []
        for cog_name, count in sorted(cog_commands.items()):
            emoji = category_emojis.get(cog_name, '🔸')
            category_name = cog_name.replace('_', ' ').title()
            cog_stats.append(f"{emoji} **{category_name}:** {count}")
        
        embed.add_field(
            name="📂 Commands by Category",
            value="\n".join(cog_stats[:8]),  # Show first 8 categories
            inline=True
        )
        
        if len(cog_stats) > 8:
            embed.add_field(
                name="📂 More Categories",
                value="\n".join(cog_stats[8:]),
                inline=True
            )
        
        # Add usage info
        embed.add_field(
            name="📖 Usage",
            value="• Use `k!help` to see all commands\n• Use `k!help <command>` for details\n• Commands update as new features are added",
            inline=False
        )
        
        embed.set_footer(text=f"Bot has {len(self.bot.cogs)} loaded modules")
        await ctx.send(embed=embed)

    @commands.command(name="serverinfo", aliases=["guildinfo"])
    async def server_info(self, ctx):
        """Display information about the current server"""
        guild = ctx.guild

        embed = discord.Embed(
            title=f"🏛️ {guild.name}",
            description=guild.description or "No description set",
            color=discord.Color.green()
        )

        embed.add_field(
            name="📊 Members",
            value=f"**Total:** {guild.member_count}\n**Humans:** {len([m for m in guild.members if not m.bot])}\n**Bots:** {len([m for m in guild.members if m.bot])}",
            inline=True
        )

        embed.add_field(
            name="📝 Channels",
            value=f"**Text:** {len(guild.text_channels)}\n**Voice:** {len(guild.voice_channels)}\n**Categories:** {len(guild.categories)}",
            inline=True
        )

        embed.add_field(
            name="🎭 Other",
            value=f"**Roles:** {len(guild.roles)}\n**Emojis:** {len(guild.emojis)}\n**Boost Level:** {guild.premium_tier}",
            inline=True
        )

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        embed.set_footer(text=f"Server ID: {guild.id} • Created: {guild.created_at.strftime('%B %d, %Y')}")

        await ctx.send(embed=embed)

    @commands.command(name="rules")
    async def rules_command(self, ctx):
        """Display the command rules"""
        embed = discord.Embed(
            title="📋 Da Command Rules",
            color=discord.Color.blue()
        )

        rules_text = """
_ _
1. No begging for special permissions.
_ _
2. No spamming with commands
_ _
3. Be respectful
_ _
4. No NSFW content with any commands
_ _
5. Don't leak any private information
_ _
6. No scamming
_ _
7. Follow Discords ToS (you must be 11+ to use this bot :) )
_ _
8. No advertising with the commands
_ _
9. No self promoting people without permission
_ _
10. If you're not banned please do not use the appealcommand ban command.
_ _
11. Do not use the bot for your server, like let it type something then kick the bot.
_ _
**Note: You may get punished for breaking these rules.**
        """

        embed.description = rules_text
        embed.set_footer(text=f"Requested by {ctx.author.display_name}")

        await ctx.send(embed=embed)

    @commands.command(name="help")
    async def help_command(self, ctx, *, command_name=None):
        """Show help information for commands"""
        if command_name:
            # Show help for specific command
            command = self.bot.get_command(command_name.lower())
            if not command:
                embed = create_embed("❌ Command Not Found", f"No command named `{command_name}` found.")
                await ctx.send(embed=embed)
                return

            embed = discord.Embed(
                title=f"Help: k!{command.name}",
                description=command.help or "No description available",
                color=discord.Color.blue()
            )

            if command.aliases:
                embed.add_field(
                    name="Aliases",
                    value=", ".join([f"k!{alias}" for alias in command.aliases]),
                    inline=False
                )

            embed.add_field(
                name="Usage",
                value=f"k!{command.name} {command.signature}",
                inline=False
            )

            await ctx.send(embed=embed)
        else:
            # Show all commands organized by category
            embed = discord.Embed(
                title="🤖 Bot Commands Help",
                description="Here are all available commands organized by category:",
                color=discord.Color.blue()
            )

            # General Commands
            general_cmds = [
                "k!ping", "k!info", "k!serverinfo", "k!help", "k!commandcount", 
                "k!rules", "k!invite", "k!credits", "k!howtousebot"
            ]
            embed.add_field(
                name="🔧 General Commands",
                value="\n".join([f"• {cmd}" for cmd in general_cmds[:8]]),
                inline=True
            )

            # Moderation Commands
            mod_cmds = [
                "k!kick", "k!ban", "k!unban", "k!timeout", "k!untimeout", 
                "k!warn", "k!purge", "k!say", "k!sayembed", "k!setuplogs"
            ]
            embed.add_field(
                name="🔨 Moderation Commands",
                value="\n".join([f"• {cmd}" for cmd in mod_cmds[:8]]),
                inline=True
            )

            # Fun Commands (first 8)
            fun_cmds_1 = [
                "k!8ball", "k!coinflip", "k!dice", "k!joke", "k!choose", 
                "k!love", "k!rps", "k!dadjoke"
            ]
            embed.add_field(
                name="🎮 Fun Commands (Part 1)",
                value="\n".join([f"• {cmd}" for cmd in fun_cmds_1]),
                inline=True
            )

            # Fun Commands (next 8)
            fun_cmds_2 = [
                "k!meme", "k!fortune", "k!transform", "k!scream", 
                "k!facepalm", "k!shrug", "k!clap", "k!wave"
            ]
            embed.add_field(
                name="🎮 Fun Commands (Part 2)",
                value="\n".join([f"• {cmd}" for cmd in fun_cmds_2]),
                inline=True
            )

            # Fun Commands (remaining)
            fun_cmds_3 = [
                "k!pet", "k!boop", "k!zombie", "k!dance", "k!hug", 
                "k!slap", "k!kiss", "k!punch"
            ]
            embed.add_field(
                name="🎮 Fun Commands (Part 3)",
                value="\n".join([f"• {cmd}" for cmd in fun_cmds_3]),
                inline=True
            )

            # More Fun Commands
            fun_cmds_4 = [
                "k!cry", "k!laugh", "k!sleep", "k!eat", "k!magic", "k!superhero"
            ]
            embed.add_field(
                name="🎮 Fun Commands (Part 4)",
                value="\n".join([f"• {cmd}" for cmd in fun_cmds_4]),
                inline=True
            )

            # Utility Commands
            utility_cmds = [
                "k!avatar", "k!userinfo", "k!weather", "k!quote", 
                "k!randomfact", "k!urbandict"
            ]
            embed.add_field(
                name="🛠️ Utility Commands",
                value="\n".join([f"• {cmd}" for cmd in utility_cmds[:6]]),
                inline=True
            )

            # Template & Admin Commands
            template_cmds = [
                "k!template", "k!temproles", "k!deleteall", "k!addappealbanlink", 
                "k!promoteservercmd", "k!viewpromotionserver"
            ]
            embed.add_field(
                name="📋 Template & Admin Commands",
                value="\n".join([f"• {cmd}" for cmd in template_cmds[:6]]),
                inline=True
            )

            # Special Owner Commands (only show to authorized users)
            if is_kh2_official(ctx):
                owner_cmds = [
                    "/commandban", "/commandmute", "/commandwarn", 
                    "/commandunban", "/commandunmute", "k!addadmin", "k!removeadmin"
                ]
                embed.add_field(
                    name="👑 Owner Special Commands",
                    value="\n".join([f"• {cmd}" for cmd in owner_cmds]),
                    inline=False
                )

            # Usage instructions
            embed.add_field(
                name="📖 Usage Information",
                value=(
                    "• Use `k!help <command>` for detailed help on a specific command\n"
                    "• Commands with `/` are slash commands (owner only)\n"
                    "• Some commands require specific permissions\n"
                    "• All regular commands use the `k!` prefix"
                ),
                inline=False
            )

            total_commands = len([cmd for cmd in self.bot.commands if not cmd.hidden])
            embed.set_footer(text=f"Total available commands: {total_commands}")
            await ctx.send(embed=embed)

    @commands.command(name="invite")
    async def invite_command(self, ctx):
        """Get the bot invite link"""
        invite_url = "https://discord.com/oauth2/authorize?client_id=1401261269432144045&permissions=1513962695871&integration_type=0&scope=bot"
        
        embed = discord.Embed(
            title="🔗 Invite Bot to Your Server! [NOW!]",
            description=f"Click the link below to invite me to your server!\n\n[**Invite Bot**]({invite_url})",
            color=discord.Color.blue()
        )
        
        embed.add_field(
            name="📋 What I can do:",
            value="• Moderation commands\n• AI chat & image generation\n• Utility commands\n• Fun commands\n• Server templates\n• And much more!",
            inline=False
        )
        
        embed.set_footer(text=f"Requested by {ctx.author.display_name}")
        embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        
        await ctx.send(embed=embed)

    @commands.command(name="credits")
    async def credits_command(self, ctx):
        """Display bot credits and acknowledgments"""
        embed = discord.Embed(
            title="🎖️ Bot Credits",
            description="Special thanks to those who helped make this bot possible!",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="🤖 AI Integration Credits",
            value="**Credits to:**\n• **Omxr**\n• **Roquallian**\n\nFor giving me the AI I needed!",
            inline=False
        )
        
        embed.add_field(
            name="🔧 Bot Developer",
            value="Developed by **kh2.officialeditz & r3act0r_editzofficial**",
            inline=False
        )
        
        embed.set_footer(text=f"Requested by {ctx.author.display_name}")
        embed.set_thumbnail(url=self.bot.user.avatar.url if self.bot.user.avatar else None)
        
        await ctx.send(embed=embed)

    @commands.command(name="howtousebot", aliases=["howto", "guide"])
    async def how_to_use_bot(self, ctx):
        """Learn how to use the bot effectively"""
        embed = discord.Embed(
            title="📖 How to Use the Bot",
            description="Here's a quick guide to get you started with the bot!",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="🚀 Getting Started",
            value="• All commands start with `k!`\n• Type `k!help` to see all commands\n• Use `k!help <command>` for specific help",
            inline=False
        )
        
        embed.add_field(
            name="🔧 Basic Commands",
            value="• `k!ping` - Check bot response time\n• `k!info` - View bot information\n• `k!serverinfo` - See server details",
            inline=False
        )
        
        embed.add_field(
            name="🎮 Fun Commands",
            value="• `k!8ball <question>` - Ask the magic 8-ball\n• `k!joke` - Get a random joke\n• `k!coinflip` - Flip a coin",
            inline=False
        )
        
        embed.add_field(
            name="🤖 AI Commands",
            value="• `k!question <your question>` - Ask AI anything\n• `k!createimage <description>` - Generate AI images",
            inline=False
        )
        
        embed.add_field(
            name="🔨 Admin Commands",
            value="• Need admin permissions for moderation\n• `k!template` - Create server templates\n• `k!say` - Make bot speak",
            inline=False
        )
        
        embed.add_field(
            name="📋 Important Notes",
            value="• Follow the bot rules (`k!rules`)\n• Be respectful when using commands\n• Some commands require permissions",
            inline=False
        )
        
        embed.set_footer(text="Need more help? Use k!help or ask an admin!")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(GeneralCog(bot))