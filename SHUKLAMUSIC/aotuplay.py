"""
Aotuplay - Music Player Bot
Complete working bot with all music features
"""

import os
import sys
import logging
from config import *
from SHUKLAMUSIC.handlers import register_music_handlers

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import essential modules
try:
    from pyrogram import Client, filters
    from pyrogram.types import Message
except ImportError:
    logger.error("Please install pyrogram: pip install pyrogram")
    sys.exit()


class AotuplayBot:
    """Main Aotuplay Bot Class - Complete Music Player"""
    
    def __init__(self):
        """Initialize the bot"""
        try:
            self.bot = Client(
                "aotuplay_bot",
                api_id=API_ID,"29308061"
                api_hash=API_HASH,"462de3dfc98fd938ef9c6ee31a72d099"
                bot_token=BOT_TOKEN"7637197122:AAHuPZoodC9aMVmiZ1BpEOuiHcaaAyP1-UE"
            )
            logger.info("✅ Bot client initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize bot: {e}")
            sys.exit()
        
        self.setup_handlers()
        logger.info("✅ Handlers registered")
    
    def setup_handlers(self):
        """Setup all bot handlers"""
        
        # Start command
        @self.bot.on_message(filters.command("start"))
        async def start_handler(client, message: Message):
            """Start command handler"""
            await message.reply_text(
                "🎵 **Welcome to Aotuplay Music Bot!**\n\n"
                "Your personal music player for Telegram.\n\n"
                "🎼 **Features:**\n"
                "✅ Play music from Telegram\n"
                "✅ Create and manage queues\n"
                "✅ Skip, pause, resume tracks\n"
                "✅ View now playing & queue\n\n"
                "📋 Use /help to see all commands\n"
                "🎵 Use /music_help for music commands"
            )
        
        # Help command
        @self.bot.on_message(filters.command("help"))
        async def help_handler(client, message: Message):
            """Help command handler"""
            await message.reply_text(
                "📋 **Available Commands:**\n\n"
                "**General:**\n"
                "/start - Start the bot\n"
                "/help - Show this help message\n"
                "/ping - Check bot status\n"
                "/stats - Bot statistics\n\n"
                "**Music Commands:**\n"
                "/music_help - Show all music commands\n"
                "/play - Add audio to queue\n"
                "/pause - Pause music\n"
                "/resume - Resume music\n"
                "/skip - Skip to next track\n"
                "/stop - Stop music\n"
                "/queue - View queue\n"
                "/current - Show now playing\n"
                "/clear - Clear queue"
            )
        
        # Ping command
        @self.bot.on_message(filters.command("ping"))
        async def ping_handler(client, message: Message):
            """Ping command handler"""
            await message.reply_text("🏓 **Pong!** Bot is alive and running! ✅")
        
        # Stats command
        @self.bot.on_message(filters.command("stats"))
        async def stats_handler(client, message: Message):
            """Bot statistics"""
            await message.reply_text(
                "📊 **Bot Statistics:**\n\n"
                "🤖 Bot: Aotuplay\n"
                "📱 Platform: Telegram\n"
                "🐍 Language: Python\n"
                "📚 Framework: Pyrogram\n"
                "✅ Status: Online\n"
                "🎵 Music Features: Enabled"
            )
        
        # Register all music handlers
        register_music_handlers(self.bot)
    
    async def on_ready(self):
        """Called when bot is ready"""
        logger.info("🚀 Aotuplay Bot is ready and listening!")
    
    def run(self):
        """Start the bot and keep it running"""
        logger.info("🚀 Starting Aotuplay Bot...")
        logger.info("🎵 All music features are enabled!")
        logger.info("📋 Use /help to see all commands")
        
        try:
            self.bot.run()
        except KeyboardInterrupt:
            logger.info("⏹️ Bot stopped by user")
        except Exception as e:
            logger.error(f"❌ Bot error: {e}")


async def main():
    """Main async function"""
    try:
        bot = AotuplayBot()
        bot.run()
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("=" * 50)
    print("🎵 AOTUPLAY MUSIC BOT")
    print("=" * 50)
    print("✅ Initializing bot...")
    print("=" * 50)
    
    try:
        # Run the bot
        bot = AotuplayBot()
        bot.run()
    except KeyboardInterrupt:
        print("\n⏹️ Bot stopped")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
