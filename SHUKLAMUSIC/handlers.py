"""
Music Handlers - Play, Pause, Skip, Queue Management
Added: autoplay (aotuplay) support and command
"""

from pyrogram import filters
from pyrogram.types import Message
from collections import deque
import asyncio


class MusicQueue:
    """Manage music queue"""
    
    def __init__(self):
        self.queue = deque()
        self.current_playing = None
        self.is_playing = False
        # autoplay feature: if True, replay last track when queue empties
        self.autoplay = False
        # keep reference to the last added/played track for autoplay
        self.last_track = None
    
    def add_to_queue(self, track):
        """Add track to queue"""
        # remember last track for autoplay
        self.last_track = track
        self.queue.append(track)
        return len(self.queue)
    
    def get_next(self):
        """Get next track from queue"""
        if self.queue:
            self.current_playing = self.queue.popleft()
            return self.current_playing
        return None
    
    def skip_track(self):
        """Skip current track"""
        self.current_playing = None
        return self.get_next()
    
    def clear_queue(self):
        """Clear entire queue"""
        self.queue.clear()
        self.current_playing = None
    
    def get_queue_list(self):
        """Get list of queued tracks"""
        return list(self.queue)
    
    def queue_size(self):
        """Get queue size"""
        return len(self.queue)


# Global queue instance
music_queue = MusicQueue()


def register_music_handlers(bot):
    """Register all music command handlers"""
    
    @bot.on_message(filters.command("play"))
    async def play_handler(client, message: Message):
        """Play music command"""
        if not message.reply_to_message:
            await message.reply_text(
                "❌ Please reply to an audio file to play it."
            )
            return
        
        audio = message.reply_to_message.audio
        if not audio:
            await message.reply_text(
                "❌ The replied message doesn't contain an audio file."
            )
            return
        
        track_info = {
            "title": audio.title or "Unknown Track",
            "artist": audio.performer or "Unknown Artist",
            "duration": audio.duration,
            "file_id": audio.file_id
        }
        
        music_queue.add_to_queue(track_info)
        
        if not music_queue.is_playing:
            music_queue.is_playing = True
            music_queue.get_next()
            await message.reply_text(
                f"🎵 **Now Playing:**\n\n"
                f"🎼 Title: {track_info['title']}\n"
                f"🎤 Artist: {track_info['artist']}\n"
                f"⏱️ Duration: {track_info['duration']}s"
            )
        else:
            queue_position = music_queue.queue_size() + 1
            await message.reply_text(
                f"➕ **Added to Queue (Position #{queue_position}):**\n\n"
                f"🎼 Title: {track_info['title']}\n"
                f"🎤 Artist: {track_info['artist']}"
            )
    
    
    @bot.on_message(filters.command("pause"))
    async def pause_handler(client, message: Message):
        """Pause music command"""
        if not music_queue.is_playing:
            await message.reply_text("❌ No music is currently playing.")
            return
        
        music_queue.is_playing = False
        await message.reply_text(
            f"⏸️ **Music Paused**\n\n"
            f"Currently paused: {music_queue.current_playing['title']}"
        )
    
    
    @bot.on_message(filters.command("resume"))
    async def resume_handler(client, message: Message):
        """Resume music command"""
        if music_queue.current_playing is None:
            await message.reply_text("❌ No music to resume.")
            return
        
        music_queue.is_playing = True
        await message.reply_text(
            f"▶️ **Music Resumed**\n\n"
            f"Resumed: {music_queue.current_playing['title']}"
        )
    
    
    @bot.on_message(filters.command("skip"))
    async def skip_handler(client, message: Message):
        """Skip to next track command"""
        if not music_queue.current_playing:
            await message.reply_text("❌ No music is playing.")
            return
        
        skipped_track = music_queue.current_playing
        next_track = music_queue.skip_track()
        
        # If there's no next track but autoplay is enabled, re-add last track
        if not next_track and music_queue.autoplay and music_queue.last_track:
            # Re-add last track and get it as next
            music_queue.add_to_queue(music_queue.last_track)
            next_track = music_queue.get_next()
            music_queue.is_playing = True
        
        if next_track:
            await message.reply_text(
                f"⏭️ **Skipped**\n\n"
                f"Skipped: {skipped_track['title']}\n\n"
                f"🎵 **Now Playing:**\n"
                f"🎼 {next_track['title']}\n"
                f"🎤 {next_track['artist']}"
            )
        else:
            music_queue.is_playing = False
            await message.reply_text(
                f"⏭️ **Skipped**\n\n"
                f"Skipped: {skipped_track['title']}\n\n"
                f"📭 Queue is now empty."
            )
    
    
    @bot.on_message(filters.command("stop"))
    async def stop_handler(client, message: Message):
        """Stop music command"""
        if not music_queue.is_playing and not music_queue.current_playing:
            await message.reply_text("❌ No music is currently playing.")
            return
        
        stopped_track = music_queue.current_playing
        music_queue.clear_queue()
        music_queue.is_playing = False
        
        await message.reply_text(
            f"⏹️ **Music Stopped**\n\n"
            f"Stopped: {stopped_track['title']}\n"
            f"🗑️ Queue cleared."
        )
    
    
    @bot.on_message(filters.command("queue"))
    async def queue_handler(client, message: Message):
        """Show current queue command"""
        queue_list = music_queue.get_queue_list()
        
        if not queue_list and not music_queue.current_playing:
            await message.reply_text("📭 Queue is empty.")
            return
        
        response = "📋 **Current Queue:**\n\n"
        
        if music_queue.current_playing:
            response += f"🎵 **Now Playing:**\n"
            response += f"🎼 {music_queue.current_playing['title']}\n"
            response += f"🎤 {music_queue.current_playing['artist']}\n\n"
        
        if queue_list:
            response += "**Upcoming:**\n"
            for idx, track in enumerate(queue_list, 1):
                response += f"{idx}. {track['title']} - {track['artist']}\n"
        else:
            response += "No tracks in queue."
        
        await message.reply_text(response)
    
    
    @bot.on_message(filters.command("current"))
    async def current_handler(client, message: Message):
        """Show current playing track command"""
        if not music_queue.current_playing:
            await message.reply_text("❌ No music is currently playing.")
            return
        
        track = music_queue.current_playing
        status = "▶️ Playing" if music_queue.is_playing else "⏸️ Paused"
        
        await message.reply_text(
            f"{status}\n\n"
            f"🎼 Title: {track['title']}\n"
            f"🎤 Artist: {track['artist']}\n"
            f"⏱️ Duration: {track['duration']}s"
        )
    
    
    @bot.on_message(filters.command("clear"))
    async def clear_handler(client, message: Message):
        """Clear queue command"""
        queue_size = music_queue.queue_size()
        music_queue.clear_queue()
        music_queue.is_playing = False
        
        await message.reply_text(
            f"🗑️ **Queue Cleared**\n\n"
            f"Removed {queue_size} tracks from queue."
        )
    
    
    @bot.on_message(filters.command("music_help"))
    async def music_help_handler(client, message: Message):
        """Show music commands help"""
        await message.reply_text(
            "🎵 **Music Commands:**\n\n"
            "/play - Add audio to queue (reply to audio file)\n"
            "/pause - Pause current music\n"
            "/resume - Resume paused music\n"
            "/skip - Skip to next track\n"
            "/stop - Stop music and clear queue\n"
            "/queue - Show current queue\n"
            "/current - Show currently playing track\n"
            "/clear - Clear entire queue\n"
            "/aotuplay - Toggle autoplay mode (also /autoplay)\n"
            "/music_help - Show this help message"
        )

    
    @bot.on_message(filters.command(["aotuplay", "autoplay"]))
    async def aotuplay_handler(client, message: Message):
        """Toggle or set autoplay mode.

        Usage:
        /aotuplay - toggles autoplay on/off
        /aotuplay on - enable autoplay
        /aotuplay off - disable autoplay
        /aotuplay status - show current status
        """
        # parse arguments
        parts = message.text.strip().split()
        # default: toggle
        if len(parts) == 1:
            music_queue.autoplay = not music_queue.autoplay
            status = "enabled" if music_queue.autoplay else "disabled"
            await message.reply_text(f"🔁 Autoplay {status}.")
            return
        arg = parts[1].lower()
        if arg in ("on", "true", "1"):
            music_queue.autoplay = True
            await message.reply_text("🔁 Autoplay enabled.")
            return
        if arg in ("off", "false", "0"):
            music_queue.autoplay = False
            await message.reply_text("🔁 Autoplay disabled.")
            return
        if arg in ("status", "state"):
            status = "enabled" if music_queue.autoplay else "disabled"
            await message.reply_text(f"🔁 Autoplay is currently {status}.")
            return
        # unknown argument
        await message.reply_text("❌ Unknown argument. Use: on, off, status or nothing to toggle.")
