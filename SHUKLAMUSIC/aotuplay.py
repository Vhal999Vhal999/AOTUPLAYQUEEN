"""
Aotuplay - Music Player Bot
"""

import os
import sys
from config import *

# Import essential modules
try:
    from pyrogram import Client, filters
    from pyrogram.types import Message
except ImportError:
    print("Please install pyrogram: pip install pyrogram")
    sys.exit()


class AotuplayBot:
    """Main Aotuplay Bot Class"""
    
    def __init__(self):
        self.bot = Client(
            "aotuplay_bot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN
        )
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup bot command handlers"""
        
        @self.bot.on_message(filters.command("start"))
        async def start_handler(client, message: Message):
            await message.reply_text(
                "🎵 **Welcome to Aotuplay!**\n\n"
                "This is your music player bot.\n\n"
                "Use /help to see available commands."
            )
        
        @self.bot.on_message(filters.command("help"))
        async def help_handler(client, message: Message):
            await message.reply_text(
                "📋 **Available Commands:**\n\n"
                "/start - Start the bot\n"
                "/help - Show this help message\n"
                "/play - Play music\n"
                "/stop - Stop playing\n"
                "/ping - Check bot status"
            )
        
        @self.bot.on_message(filters.command("ping"))
        async def ping_handler(client, message: Message):
            await message.reply_text("🏓 **Pong!** Bot is alive!")
    
    def run(self):
        """Start the bot"""
        print("🎵 Starting Aotuplay Bot...")
        self.bot.run()


if __name__ == "__main__":
    bot = AotuplayBot()
    bot.run()
