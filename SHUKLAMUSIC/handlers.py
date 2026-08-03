"""
Music Handlers - Play, Pause, Skip, Queue Management
Added: support to play from a Telegram message link or message id (/playmsg, /playlink)
"""

from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from collections import deque
import asyncio
import re


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
        """Play music command — supports reply-audio, same-message audio, or /play <file_id>"""
        audio = None
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
                # If looks like a file_id (very long string) accept as file_id
                track_info = {
                    "title": "Unknown Track",
                    "artist": "Unknown Artist",
                    "duration": 0,
                    "file_id": arg,
                }
                music_queue.add_to_queue(track_info)
                queue_position = music_queue.queue_size()
                await message.reply_text(
                    f"➕ कतार में जोड़ा (स्थिति #{queue_position}):\n🎼 {track_info['title']}\n🎤 {track_info['artist']}\n\n(फ़ाइल आईडी से जोड़ा गया)",
                )
                return
            # no audio found
            await message.reply_text(
                "❌ कोई ऑडियो फ़ाइल नहीं मिली।\nकृपया ऑडियो संदेश को रिप्लाई करें या ऑडियो उसी संदेश में भेजें या /play <file_id> का उपयोग करें।",
            )
            return

        # If we have a pyrogram Audio object, extract metadata
        if audio:
            track_info = {
                "title": getattr(audio, "title", None) or "Unknown Track",
                "artist": getattr(audio, "performer", None) or "Unknown Artist",
                "duration": getattr(audio, "duration", 0),
                "file_id": getattr(audio, "file_id", None),
            }

            music_queue.add_to_queue(track_info)

            if not music_queue.is_playing:
                music_queue.is_playing = True
                music_queue.get_next()
                await message.reply_text(
                    f"🎵 अब चल रहा है:\n\n🎼 शीर्षक: {track_info['title']}\n🎤 कलाकार: {track_info['artist']}\n⏱️ अवधि: {track_info['duration']}s"
                )
            else:
                queue_position = music_queue.queue_size()
                await message.reply_text(
                    f"➕ कतार में जोड़ा (स्थिति #{queue_position}):\n🎼 {track_info['title']}\n🎤 {track_info['artist']}",
                )

    @bot.on_message(filters.command("pause"))
    async def pause_handler(client, message: Message):
        """Pause music command"""
        if not music_queue.is_playing:
            await message.reply_text("❌ फिलहाल कोई संगीत चल नहीं रहा है।")
            return

        music_queue.is_playing = False
        await message.reply_text(
            f"⏸️ संगीत रोक दिया गया।\n\nरुको हुआ: {music_queue.current_playing['title']}",
        )

    @bot.on_message(filters.command("resume"))
    async def resume_handler(client, message: Message):
        """Resume music command"""
        if music_queue.current_playing is None:
            await message.reply_text("❌ रिस्यूम करने के लिए कोई ट्रैक नहीं है।")
            return

        music_queue.is_playing = True
        await message.reply_text(f"▶️ संगीत फिर से चालू हुआ: {music_queue.current_playing['title']}")

    @bot.on_message(filters.command("skip"))
    async def skip_handler(client, message: Message):
        """Skip to next track command"""
        if not music_queue.current_playing:
            await message.reply_text("❌ फिलहाल कोई संगीत नहीं चल रहा है।")
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
                f"⏭️ स्किप किया गया: {skipped_track['title']}\n\n🎵 अब चल रहा है: {next_track['title']} - {next_track['artist']}",
            )
        else:
            music_queue.is_playing = False
            await message.reply_text(f"⏭️ स्किप किया गया: {skipped_track['title']}\n\n📭 कतार अब खाली है।")

    @bot.on_message(filters.command("stop"))
    async def stop_handler(client, message: Message):
        """Stop music command"""
        if not music_queue.is_playing and not music_queue.current_playing:
            await message.reply_text("❌ फिलहाल कोई संगीत नहीं चल रहा है।")
            return

        stopped_track = music_queue.current_playing
        music_queue.clear_queue()
        music_queue.is_playing = False

        await message.reply_text(
            f"⏹️ संगीत बंद किया गया।\n\nरुका हुआ: {stopped_track['title']}\n🗑️ कतार साफ़ की गई।"
        )

    @bot.on_message(filters.command("queue"))
    async def queue_handler(client, message: Message):
        """Show current queue command"""
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
        """Show current playing track command"""
        if not music_queue.current_playing:
            await message.reply_text("❌ फिलहाल कोई संगीत नहीं चल रहा है।")
            return

        track = music_queue.current_playing
        status = "▶️ चल रहा है" if music_queue.is_playing else "⏸️ रुका हुआ"

        await message.reply_text(
            f"{status}\n\n🎼 शीर्षक: {track['title']}\n🎤 कलाकार: {track['artist']}\n⏱️ अवधि: {track['duration']}s"
        )

    @bot.on_message(filters.command("clear"))
    async def clear_handler(client, message: Message):
        """Clear queue command"""
        queue_size = music_queue.queue_size()
        music_queue.clear_queue()
        music_queue.is_playing = False

        await message.reply_text(f"🗑️ कतार साफ़ की गई।\n\nनिकाले गए ट्रैक्स: {queue_size}")

    @bot.on_message(filters.command("music_help"))
    async def music_help_handler(client, message: Message):
        """Show music commands help (Hindi)"""
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

    @bot.on_message(filters.command(["playmsg", "playlink"]))
    async def playmsg_handler(client, message: Message):
        """Play from a telegram message link or chat_id + message_id

        Usage:
        /playlink https://t.me/username/123
        /playlink https://t.me/c/1234567890/123
        /playmsg @username 123
        /playmsg -1001234567890 123
        """
        parts = message.text.strip().split(maxsplit=1)
        if len(parts) < 2:
            await message.reply_text(
                "उपयोग: /playmsg <chat_username_or_id> <message_id>\nया /playlink <t.me लिंक>"
            )
            return

        arg = parts[1].strip()

        chat = None
        msg_id = None

        # t.me link parsing
        m = re.match(r"https?://t.me/(?:(c)/)?(?P<chat>[^/]+)/(?P<msgid>\d+)", arg)
        if m:
            if m.group(1):
                # t.me/c/<chat>/<msgid> -> internal id, need to prefix -100
                raw = m.group('chat')
                try:
                    chat = int(f"-100{raw}")
                except Exception:
                    await message.reply_text("❌ अवैध लिंक: चैट आईडी पार्स नहीं हो पाई।")
                    return
            else:
                chat_name = m.group('chat')
                chat = chat_name if chat_name.startswith('@') else f"@{chat_name}"
            msg_id = int(m.group('msgid'))
        else:
            # try: /playmsg @username 123  OR /playmsg -100123... 123
            toks = arg.split()
            if len(toks) == 2:
                chat_tok, msg_tok = toks[0], toks[1]
                try:
                    msg_id = int(msg_tok)
                except Exception:
                    await message.reply_text("❌ अवैध message_id।")
                    return
                # chat id or username
                if (chat_tok.lstrip('-').isdigit()):
                    try:
                        chat = int(chat_tok)
                    except Exception:
                        await message.reply_text("❌ अवैध चैट आईडी।")
                        return
                else:
                    chat = chat_tok if chat_tok.startswith('@') else f"@{chat_tok}"
            else:
                await message.reply_text(
                    "उपयोग: /playmsg <chat_username_or_id> <message_id>\nया /playlink <t.me लिंक>"
                )
                return

        # Fetch the message
        try:
            target_msg = await client.get_messages(chat, msg_id)
        except Exception as e:
            await message.reply_text(f"❌ संदेश प्राप्त करने में त्रुटि: {e}")
            return

        if not target_msg:
            await message.reply_text("❌ संदेश नहीं मिला।")
            return

        # Find audio in the fetched message
        audio_obj = getattr(target_msg, 'audio', None) or getattr(target_msg, 'voice', None)
        if not audio_obj:
            doc = getattr(target_msg, 'document', None)
            if doc and getattr(doc, 'mime_type', '').startswith('audio'):
                audio_obj = doc

        if not audio_obj:
            await message.reply_text("❌ उस संदेश में ऑडियो नहीं मिला।")
            return

        track_info = {
            "title": getattr(audio_obj, 'title', None) or 'Unknown Track',
            "artist": getattr(audio_obj, 'performer', None) or 'Unknown Artist',
            "duration": getattr(audio_obj, 'duration', 0) or 0,
            "file_id": getattr(audio_obj, 'file_id', None) or getattr(audio_obj, 'file_unique_id', None),
        }

        music_queue.add_to_queue(track_info)

        if not music_queue.is_playing:
            music_queue.is_playing = True
            music_queue.get_next()
            await message.reply_text(
                f"🎵 अब चल रहा है (message से):\n\n🎼 शीर्षक: {track_info['title']}\n🎤 कलाकार: {track_info['artist']}"
            )
        else:
            queue_position = music_queue.queue_size()
            await message.reply_text(
                f"➕ कतार में जोड़ा (स्थिति #{queue_position}):\n🎼 {track_info['title']}\n🎤 {track_info['artist']}\n\n(संदेश से जोड़ा गया)"
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
            # unknown argument
            await message.reply_text("❌ अज्ञात तर्क। उपयोग: on, off, status या खली छोड़ें बटन दिखाने के लिए।")
            return

        # No args: show inline buttons to toggle autoplay
        status = "सक्षम" if music_queue.autoplay else "अक्षम"
        await message.reply_text(
            f"🔁 Autoplay वर्तमान में *{status}* है।",
            reply_markup=_autoplay_keyboard(),
        )

    @bot.on_callback_query(filters.regex(r"^autoplay:(on|off|toggle|status)$"))
    async def autoplay_callback(client, callback_query: CallbackQuery):
        """Handle autoplay inline button presses"""
        # Debug print to console
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
        else:  # status
            state = "सक्षम" if music_queue.autoplay else "अक्षम"
            text = f"🔁 Autoplay वर्तमान स्थिति: {state}."

        # Acknowledge the callback to remove loading state and show alert so user notices
        try:
            await callback_query.answer(text, show_alert=True)
        except Exception:
            pass

        # Edit original message to reflect new state and keep buttons
        try:
            if callback_query.message:
                await callback_query.message.edit_text(
                    f"🔁 Autoplay अब *{'सक्षम' if music_queue.autoplay else 'अक्षम'}* है।",
                    reply_markup=_autoplay_keyboard(),
                )
        except Exception:
            # If edit fails (message deleted or too old), send a small follow-up message
            try:
                await callback_query.message.reply_text(text)
            except Exception:
                # last resort: ignore
                pass
