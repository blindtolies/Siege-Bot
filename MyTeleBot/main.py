#!/usr/bin/env python3
"""
Main entry point for the Siege Telegram Bot (Cohere-powered)
"""
import asyncio
import logging
import sys
from bot import SiegeBot
from config import Config

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('siege_bot.log')
    ]
)
logger = logging.getLogger(__name__)

async def main():
    """Main function to start the bot"""
    try:
        # Validate configuration first
        config = Config()
        config.validate()
        logger.info("Configuration validated successfully")
        
        # Initialize and start bot
        bot = SiegeBot()
        logger.info("Bot initialized, starting...")
        await bot.start()
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Failed to start bot: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
        sys.exit(0)
