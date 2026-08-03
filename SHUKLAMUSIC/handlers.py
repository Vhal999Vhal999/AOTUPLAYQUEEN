"""
Music Handlers - Play, Pause, Skip, Queue Management
Integrate playback with SHUKLA (pytgcalls) so /play actually streams to group voice chat.
"""

from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from collections import deque
import asyncio
import os
import re

# Import SHUKLA core player
from SHUKLAMUSIC import SHUKLA, app


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


def _ensure_download_dir():
    d = os.path.join(os.getcwd(), "downloads")
    if not os.path.isdir(d):
        os.makedirs(d)
    return d


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
        """Play music command — supports reply-audio, same-message audio, or /play <file_id>

        Integrates with SHUKLA (pytgcalls) to stream into the voice chat of the current chat.
        """
        audio = None
        chat_id = message.chat.id

        # 1) Reply to a message with audio
        if message.reply_to_message and getattr(message.reply_to_message, "audio", None):
            audio = message.reply_to_message.audio
        # 2) Audio sent in the same message
        elif getattr(message, "audio", None):
            audio = message.audio
        else:
            # 3) Try to parse file_id from command argument
            parts = message.text.strip().split(maxsplit=1)
            if len(parts) > 1:
                arg = parts[1].strip()
                # Accept file_id — but we'll try to download/play it directly
                audio = type("A", (), {"file_id": arg, "title": None, "performer": None, "duration": 0})()
            else:
                await message.reply_text(
                    "❌ कोई ऑडियो फ़ाइल नहीं मिली।\nकृपया ऑडियो संदेश को रिप्लाई करें या ऑडियो उसी संदेश में भेजें या /play <file_id> का उपयोग करें।",
                )
                return

        # Ensure downloads dir
        dl_dir = _ensure_download_dir()

        # Try downloading the media locally so PyTgCalls can stream it
        try:
            file_path = await client.download_media(audio.file_id, file_name=os.path.join(dl_dir, f"{audio.file_id}.mp3"))
        except Exception as e:
            await message.reply_text(f"❌ फ़ाइल डाउनलोड करने में त्रुटि: {e}")
            return

        # Build track metadata
        track_info = {
            "title": getattr(audio, "title", None) or "Unknown Track",
            "artist": getattr(audio, "performer", None) or "Unknown Artist",
            "duration": getattr(audio, "duration", 0) or 0,
            "file_path": file_path,
            "file_id": getattr(audio, "file_id", None),
        }

        # Add to local queue
        music_queue.add_to_queue(track_info)

        # If not playing, attempt to join voice chat and play using SHUKLA
        if not music_queue.is_playing:
            # Try to start streaming into the chat's voice chat
            try:
                # SHUKLA.join_call(chat_id, original_chat_id, link, video=False)
                await SHUKLA.join_call(chat_id, chat_id, track_info["file_path"], video=False)
                music_queue.is_playing = True
                music_queue.get_next()
                await message.reply_text(
                    f"🎵 अब चल रहा है:\n\n🎼 शीर्षक: {track_info['title']}\n🎤 कलाकार: {track_info['artist']}\n⏱️ अवधि: {track_info['duration']}s"
                )
            except Exception as e:
                # Common reasons: no active group call, no assistant sessions configured
                await message.reply_text(
                    "❌ प्लेबैक शुरू नहीं हो सका। कृपया सुनिश्चित करें कि: \n"
                    "1) आपने सहायक सत्र (STRING_SESSION) कॉन्फ़िगर किए हैं।\n"
                    "2) लक्षित समूह में वॉइस चैट गतिविधि (voice chat) चालू है।\n"
                    f"त्रुटि: {e}",
                )
                # reset playing state
                music_queue.is_playing = False
                return
        else:
            queue_position = music_queue.queue_size()
            await message.reply_text(
                f"➕ कतार में जोड़ा (स्थिति #{queue_position}):\n🎼 {track_info['title']}\n🎤 {track_info['artist']}"
            )

    # other handlers remain unchanged (pause/resume/skip/stop/queue/current/clear/music_help/aotuplay etc.)
    # For brevity, import the rest of the file's existing handlers below (kept unchanged)

    @bot.on_message(filters.command("pause"))
    async def pause_handler(client, message: Message):
        if not music_queue.is_playing:
            await message.reply_text("❌ फिलहाल कोई संगीत चल नहीं रहा है।")
            return
        music_queue.is_playing = False
        await message.reply_text(f"⏸️ संगीत रोक दिया गया।\n\nरुको हुआ: {music_queue.current_playing['title']}")

    @bot.on_message(filters.command("resume"))
    async def resume_handler(client, message: Message):
        if music_queue.current_playing is None:
            await message.reply_text("❌ रिस्यूम करने के लिए कोई ट्रैक नहीं है।")
            return
        music_queue.is_playing = True
        await message.reply_text(f"▶️ संगीत फिर से चालू हुआ: {music_queue.current_playing['title']}")

    @bot.on_message(filters.command("skip"))
    async def skip_handler(client, message: Message):
        if not music_queue.current_playing:
            await message.reply_text("❌ फिलहाल कोई संगीत नहीं चल रहा है।")
            return
        skipped_track = music_queue.current_playing
        next_track = music_queue.skip_track()
        if not next_track and music_queue.autoplay and music_queue.last_track:
            music_queue.add_to_queue(music_queue.last_track)
            next_track = music_queue.get_next()
            music_queue.is_playing = True
        if next_track:
            # attempt to play next_track via SHUKLA
            try:
                await SHUKLA.join_call(message.chat.id, message.chat.id, next_track['file_path'], video=False)
                await message.reply_text(f"⏭️ अब चल रहा है: {next_track['title']} - {next_track['artist']}")
            except Exception as e:
                await message.reply_text(f"❌ अगला ट्रैक प्ले नहीं हो सका: {e}")
        else:
            music_queue.is_playing = False
            await message.reply_text(f"⏭️ स्किप किया गया: {skipped_track['title']}\n\n📭 कतार अब खाली है।")

    @bot.on_message(filters.command("stop"))
    async def stop_handler(client, message: Message):
        if not music_queue.is_playing and not music_queue.current_playing:
            await message.reply_text("❌ फिलहाल कोई संगीत नहीं चल रहा है।")
            return
        stopped_track = music_queue.current_playing
        music_queue.clear_queue()
        music_queue.is_playing = False
        # ask SHUKLA to leave the call
        try:
            await SHUKLA.stop_stream(message.chat.id)
        except Exception:
            pass
        await message.reply_text(f"⏹️ संगीत बंद किया गया।\n\nरुका हुआ: {stopped_track['title']}\n🗑️ कतार साफ़ की गई।")

    @bot.on_message(filters.command("queue"))
    async def queue_handler(client, message: Message):
        queue_list = music_queue.get_queue_list()
        if not queue_list and not music_queue.current_playing:
            await message.reply_text("📭 कतार खाली है।")
            return
        response = "📋 वर्तमान कतार:\n\n"
        if music_queue.current_playing:
            response += f"🎵 अब चल रहा है:\n{music_queue.current_playing['title']} - {music_queue.current_playing['artist']}\n\n"
        if queue_list:
            response += "**आगामी:**\n"
            for idx, track in enumerate(queue_list, 1):
                response += f"{idx}. {track['title']} - {track['artist']}\n"
        else:
            response += "कतार में कोई ट्रैक नहीं है।"
        await message.reply_text(response)

    @bot.on_message(filters.command("current"))
    async def current_handler(client, message: Message):
        if not music_queue.current_playing:
            await message.reply_text("❌ फिलहाल कोई संगीत नहीं चल रहा है।")
            return
        track = music_queue.current_playing
        status = "▶️ चल रहा है" if music_queue.is_playing else "⏸️ रुका हुआ"
        await message.reply_text(f"{status}\n\n🎼 शीर्षक: {track['title']}\n🎤 कलाकार: {track['artist']}\n⏱️ अवधि: {track['duration']}s")

    @bot.on_message(filters.command("clear"))
    async def clear_handler(client, message: Message):
        queue_size = music_queue.queue_size()
        music_queue.clear_queue()
        music_queue.is_playing = False
        try:
            await SHUKLA.stop_stream(message.chat.id)
        except Exception:
            pass
        await message.reply_text(f"🗑️ कतार साफ़ की गई।\n\nनिकाले गए ट्रैक्स: {queue_size}")

    @bot.on_message(filters.command("music_help"))
    async def music_help_handler(client, message: Message):
        await message.reply_text(
            "🎵 म्यूजिक कमांड्स:\n\n"
            "/play - ऑडियो प्ले/क्यू (रिप्लाई करें या उसी संदेश में ऑडियो भेजें या /play <file_id>)\n"
            "/pause - वर्तमान संगीत रोकें\n"
            "/resume - रुका हुआ संगीत फिर से चालू करें\n"
            "/skip - अगले ट्रैक पर जाएं\n"
            "/stop - संगीत बंद करें और कतार साफ़ करें\n"
            "/queue - वर्तमान कतार दिखाएँ\n"
            "/current - वर्तमान चल रहा ट्रैक दिखाएँ\n"
            "/clear - पूरी कतार साफ़ करें\n"
            "/aotuplay - ऑटोप्ले टॉगल (या /autoplay)\n"
            "/playmsg या /playlink - किसी संदेश लिंक या chat_id + message_id से प्ले करें\n"
            "/music_help - यह मदद संदेश"
        )

    @bot.on_message(filters.command(["aotuplay", "autoplay"]))
    async def aotuplay_handler(client, message: Message):
        parts = message.text.strip().split()
        if len(parts) > 1:
            arg = parts[1].lower()
            if arg in ("on", "true", "1"):
                music_queue.autoplay = True
                await message.reply_text("🔁 Autoplay सक्षम कर दिया गया है।")
                return
            if arg in ("off", "false", "0"):
                music_queue.autoplay = False
                await message.reply_text("🔁 Autoplay अक्षम कर दिया गया है।")
                return
            if arg in ("status", "state"):
                status = "सक्षम" if music_queue.autoplay else "अक्षम"
                await message.reply_text(f"🔁 Autoplay वर्तमान स्थिति: {status}.")
                return
            await message.reply_text("❌ अज्ञात तर्क। उपयोग: on, off, status या खली छोड़ें बटन दिखाने के लिए।")
            return
        status = "सक्षम" if music_queue.autoplay else "अक्षम"
        await message.reply_text(f"🔁 Autoplay वर्तमान में *{status}* है।", reply_markup=_autoplay_keyboard())

    @bot.on_callback_query(filters.regex(r"^autoplay:(on|off|toggle|status)$"))
    async def autoplay_callback(client, callback_query: CallbackQuery):
        try:
            print("DEBUG: autoplay callback received:", callback_query.from_user.id, callback_query.data)
        except Exception:
            print("DEBUG: autoplay callback received (no user info)")
        data = callback_query.data or ""
        action = data.split(":", 1)[1] if ":" in data else data
        if action == "on":
            music_queue.autoplay = True
            text = "🔁 Autoplay सक्षम कर दिया गया है।"
        elif action == "off":
            music_queue.autoplay = False
            text = "🔁 Autoplay अक्षम कर दिया गया है।"
        elif action == "toggle":
            music_queue.autoplay = not music_queue.autoplay
            state = "सक्षम" if music_queue.autoplay else "अक्षम"
            text = f"🔁 Autoplay टॉगल किया गया — अब {state}."
        else:
            state = "सक्षम" if music_queue.autoplay else "अक्षम"
            text = f"🔁 Autoplay वर्तमान स्थिति: {state}."
        try:
            await callback_query.answer(text, show_alert=True)
        except Exception:
            pass
        try:
            if callback_query.message:
                await callback_query.message.edit_text(f"🔁 Autoplay अब *{'सक्षम' if music_queue.autoplay else 'अक्षम'}* है।", reply_markup=_autoplay_keyboard())
        except Exception:
            try:
                await callback_query.message.reply_text(text)
            except Exception:
                pass
