"""
Music Handlers - Play, Pause, Skip, Queue Management
Fixed: reliable autoplay inline buttons + callback handling and autoplay state
"""

from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
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


def _autoplay_keyboard():
    """Return an InlineKeyboardMarkup reflecting current autoplay state"""
    state = music_queue.autoplay
    status_text = "ON ✅" if state else "OFF ❌"
    buttons = [
        [InlineKeyboardButton(f"Autoplay: {status_text}", callback_data="autoplay:status")],
        [
            InlineKeyboardButton("Enable 🔁", callback_data="autoplay:on"),
            InlineKeyboardButton("Disable ⛔", callback_data="autoplay:off"),
        ],
        [InlineKeyboardButton("Toggle ↩️", callback_data="autoplay:toggle")]
    ]
    return InlineKeyboardMarkup(buttons)


def register_music_handlers(bot):
    """Register all music command handlers"""

    @bot.on_message(filters.command("play"))
    async def play_handler(client, message: Message):
        """Play music command"""
        if not message.reply_to_message:
            await message.reply_text("❌ Please reply to an audio file to play it.")
            return

        audio = message.reply_to_message.audio
        if not audio:
            await message.reply_text("❌ The replied message doesn't contain an audio file.")
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
            queue_position = music_queue.queue_size()  # position after add
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
        await message.reply_text(f"▶️ **Music Resumed**\n\nResumed: {music_queue.current_playing['title']}")

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
            # Re-add last track and play it
            music_queue.add_to_queue(music_queue.last_track)
            next_track = music_queue.get_next()
            music_queue.is_playing = True

        if next_track:
            await message.reply_text(
                f"⏭️ **Skipped**\n\nSkipped: {skipped_track['title']}\n\n🎵 **Now Playing:**\n{next_track['title']} - {next_track['artist']}"
            )
        else:
            music_queue.is_playing = False
            await message.reply_text(f"⏭️ **Skipped**\n\nSkipped: {skipped_track['title']}\n\n📭 Queue is now empty.")

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
            f"⏹️ **Music Stopped**\n\nStopped: {stopped_track['title']}\n🗑️ Queue cleared."
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
            response += f"🎵 **Now Playing:**\n{music_queue.current_playing['title']} - {music_queue.current_playing['artist']}\n\n"

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
            f"{status}\n\n🎼 Title: {track['title']}\n🎤 Artist: {track['artist']}\n⏱️ Duration: {track['duration']}s"
        )

    @bot.on_message(filters.command("clear"))
    async def clear_handler(client, message: Message):
        """Clear queue command"""
        queue_size = music_queue.queue_size()
        music_queue.clear_queue()
        music_queue.is_playing = False

        await message.reply_text(f"🗑️ **Queue Cleared**\n\nRemoved {queue_size} tracks from queue.")

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
        /aotuplay - shows a button UI to toggle autoplay on/off
        /aotuplay on - enable autoplay
        /aotuplay off - disable autoplay
        /aotuplay status - show current status
        """
        # parse arguments
        parts = message.text.strip().split()
        # If user provides text arguments, keep existing textual behavior
        if len(parts) > 1:
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
            await message.reply_text("❌ Unknown argument. Use: on, off, status or nothing to open buttons.")
            return

        # No args: show inline buttons to toggle autoplay
        status = "enabled" if music_queue.autoplay else "disabled"
        await message.reply_text(
            f"🔁 Autoplay is currently *{status}*.",
            reply_markup=_autoplay_keyboard()
        )

    @bot.on_callback_query(filters.regex(r"^autoplay:(on|off|toggle|status)$"))
    async def autoplay_callback(client, callback_query: CallbackQuery):
        """Handle autoplay inline button presses"""
        data = callback_query.data or ""
        action = data.split(":", 1)[1] if ":" in data else data

        if action == "on":
            music_queue.autoplay = True
            text = "🔁 Autoplay enabled."
        elif action == "off":
            music_queue.autoplay = False
            text = "🔁 Autoplay disabled."
        elif action == "toggle":
            music_queue.autoplay = not music_queue.autoplay
            state = "enabled" if music_queue.autoplay else "disabled"
            text = f"🔁 Autoplay toggled — now {state}."
        else:  # status
            state = "enabled" if music_queue.autoplay else "disabled"
            text = f"🔁 Autoplay is currently {state}."

        # Acknowledge the callback to remove loading state and show alert so user notices
        try:
            await callback_query.answer(text, show_alert=True)
        except Exception:
            pass

        # Edit original message to reflect new state and keep buttons
        try:
            if callback_query.message:
                await callback_query.message.edit_text(
                    f"🔁 Autoplay is now *{'enabled' if music_queue.autoplay else 'disabled'}*.",
                    reply_markup=_autoplay_keyboard()
                )
        except Exception:
            # If edit fails (message deleted or too old), send a small follow-up message
            try:
                await callback_query.message.reply_text(text)
            except Exception:
                # last resort: ignore
                pass
