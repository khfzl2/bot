import discord
from discord.ext import commands
import asyncio
import os
import logging
import sys
from bot.bot import DiscordBot
from console.console import ConsoleManager

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Set discord.py logging to WARNING to reduce noise
logging.getLogger('discord').setLevel(logging.WARNING)
logging.getLogger('discord.gateway').setLevel(logging.INFO)

logger = logging.getLogger(__name__)

async def install_dependencies():
    """Install required dependencies if missing"""
    dependencies = [
        ('rich', 'rich'),
        ('psutil', 'psutil'),
        ('aiosqlite', 'aiosqlite')
    ]
    
    for module_name, package_name in dependencies:
        try:
            __import__(module_name)
        except ImportError:
            logger.info(f"Installing {package_name}...")
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])

async def main():
    """Main function to start both bot and console"""
    try:
        # Install dependencies first
        await install_dependencies()
        
        # Get token from environment
        token = os.getenv('DISCORD_TOKEN')
        if not token:
            logger.error("ERROR: Discord token not found in environment variables!")
            logger.error("Please set DISCORD_TOKEN environment variable")
            logger.error("Example: export DISCORD_TOKEN='your_bot_token_here'")
            return
        
        # Validate token format
        if len(token) < 50:
            logger.error("ERROR: Discord token appears to be invalid (too short)")
            return
        
        # Create bot instance
        bot = DiscordBot()
        
        logger.info("Starting Discord bot with enhanced features...")
        
        # Create tasks for both bot and console
        bot_task = asyncio.create_task(bot.start(token))
        console_task = asyncio.create_task(start_console(bot))
        
        try:
            # Wait for both tasks to complete
            await asyncio.gather(bot_task, console_task, return_exceptions=True)
        except Exception as e:
            logger.error(f"Task error: {e}")
        finally:
            # Ensure both tasks are cancelled if one fails
            if not bot_task.done():
                bot_task.cancel()
            if not console_task.done():
                console_task.cancel()
            
            # Wait for cancellation to complete
            try:
                await asyncio.gather(bot_task, console_task, return_exceptions=True)
            except Exception:
                pass
        
    except discord.LoginFailure:
        logger.error("ERROR: Failed to login - Invalid Discord token")
    except discord.HTTPException as e:
        logger.error(f"ERROR: HTTP Exception occurred: {e}")
    except Exception as e:
        logger.error(f"ERROR: Unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        logger.info("Bot shutdown complete")

async def start_console(bot):
    """Start the console interface"""
    try:
        # Wait for bot to be ready before starting console
        await bot.wait_until_ready()
        console_manager = ConsoleManager(bot)
        await console_manager.start()
        
        # If console manager exits normally, close the bot
        logger.info("Console manager stopped, shutting down bot")
        if not bot.is_closed():
            await bot.close()
    except Exception as e:
        logger.error(f"Console error: {e}")
        # If console fails, close the bot
        if not bot.is_closed():
            await bot.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()