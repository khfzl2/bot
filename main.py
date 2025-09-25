#!/usr/bin/env python3
"""
Discord Bot Main Entry Point
"""
import os
import asyncio
import logging
from bot.bot import DiscordBot

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

async def main():
    """Main function to run the bot"""
    # Discord bot token
    TOKEN = os.getenv("DISCORD_TOKEN", "MTQwMTI2MTI2OTQzMjE0NDA0NQ.Gptlm8.lPvjpPsVUfAZIdWIrRfK5hhi7OUNh1EKOua6-Y")
    
    if not TOKEN:
        logger.error("Discord token not found! Please set DISCORD_TOKEN environment variable.")
        return
    
    # Create and run the bot
    bot = DiscordBot()
    
    try:
        logger.info("Starting Discord bot...")
        await bot.start(TOKEN)
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested by user")
    except Exception as e:
        logger.error(f"Bot encountered an error: {e}")
    finally:
        await bot.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Program interrupted by user")
