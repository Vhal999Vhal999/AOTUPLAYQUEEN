# -----------------------------------------------
# Autoplay admin plugin (extended)
# Adds commands for managing autoplay: /autoplay, /autoplaystatus, /autoplayowner, /playautoplay
# -----------------------------------------------
from SHUKLAMUSIC import app
from pyrogram import filters
from pyrogram.types import Message
from SHUKLAMUSIC.utils.decorators import AdminRightsCheck
from SHUKLAMUSIC.utils.database import (
    get_autoplay,
    set_autoplay,
    set_autoplay_owner,
    get_autoplay_owner,
    music_on,
    music_off,
)
from SHUKLAMUSIC.core.call import SHUKLA
from config import BANNED_USERS
import os
import subprocess
from SHUKLAMUSIC.misc import db
from SHUKLAMUSIC.utils.stream.autoclear import auto_clean


@app.on_message(filters.command(["autoplay", "ap"]) & filters.group & ~BANNED_USERS)
@AdminRightsCheck
async def autoplay_toggle(client, message: Message, _, chat_id):
    """Toggle or set autoplay for this chat.

    Usage:
      /autoplay            -> toggles current state
      /autoplay on|off     -> enable or disable autoplay
      /autoplay start|stop -> start or stop playback immediately
    """
    cmd = message.command
    try:
        if len(cmd) > 1:
            arg = cmd[1].lower()
            if arg in ("on", "1", "true"):
                await set_autoplay(chat_id, True)
                await set_autoplay_owner(chat_id, message.from_user.id)
                return await message.reply_text("🌟 Autoplay is now ON for this chat.")
            elif arg in ("off", "0", "false"):
                await set_autoplay(chat_id, False)
                return await message.reply_text("⏹ Autoplay is now OFF for this chat.")
            elif arg == "start":
                # enable autoplay and try to resume/start stream
                await set_autoplay(chat_id, True)
                await set_autoplay_owner(chat_id, message.from_user.id)
                try:
                    await music_on(chat_id)
                    await SHUKLA.resume_stream(chat_id)
                except Exception:
                    # fallback: attempt to resume only
                    try:
                        await SHUKLA.resume_stream(chat_id)
                    except Exception as e:
                        return await message.reply_text(f"Failed to start playback: {e}")
                return await message.reply_text("▶️ Playback started and autoplay enabled.")
            elif arg == "stop":
                # disable autoplay and stop stream
                await set_autoplay(chat_id, False)
                try:
                    await music_off(chat_id)
                    await SHUKLA.stop_stream(chat_id)
                except Exception as e:
                    return await message.reply_text(f"Failed to stop playback: {e}")
                return await message.reply_text("⏹ Playback stopped and autoplay disabled.")
            else:
                return await message.reply_text("Usage: /autoplay [on|off|start|stop]")

        # toggle
        state = await get_autoplay(chat_id)
        new_state = not state
        await set_autoplay(chat_id, new_state)
        if new_state:
            await set_autoplay_owner(chat_id, message.from_user.id)
            await message.reply_text("🌟 Autoplay turned ON for this chat.")
        else:
            await message.reply_text("⏹ Autoplay turned OFF for this chat.")
    except Exception as e:
        await message.reply_text(f"Error while toggling autoplay: {e}")


@app.on_message(filters.command(["autoplaystatus", "apstatus"]) & filters.group & ~BANNED_USERS)
@AdminRightsCheck
async def autoplay_status(client, message: Message, _, chat_id):
    """Show current autoplay status and owner."""
    try:
        state = await get_autoplay(chat_id)
        owner = await get_autoplay_owner(chat_id)
        owner_txt = f"Owner ID: <code>{owner}</code>" if owner else "No owner set"
        await message.reply_text(f"Autoplay is {'ON' if state else 'OFF'} for this chat.\n{owner_txt}")
    except Exception as e:
        await message.reply_text(f"Error fetching autoplay status: {e}")


@app.on_message(filters.command(["autoplayowner", "apowner"]) & filters.group & ~BANNED_USERS)
@AdminRightsCheck
async def autoplay_owner_cmd(client, message: Message, _, chat_id):
    """Show or set the autoplay owner. Use by replying to a user to set them as owner.

    Usage:
      /autoplayowner            -> show owner
      Reply to a user's message with /autoplayowner -> set that user as owner
      /autoplayowner clear      -> clear owner
      /autoplayowner <user_id>  -> set owner by user id
    """
    cmd = message.command
    try:
        if len(cmd) > 1:
            arg = cmd[1].lower()
            if arg == "clear":
                await set_autoplay_owner(chat_id, None)
                return await message.reply_text("✅ Autoplay owner cleared.")
            # try parse numeric id
            try:
                uid = int(arg)
                await set_autoplay_owner(chat_id, uid)
                return await message.reply_text(f"✅ Autoplay owner set to <code>{uid}</code>")
            except ValueError:
                return await message.reply_text("Usage: /autoplayowner [clear|<user_id>] or reply to a user message to set owner.")

        if message.reply_to_message and message.reply_to_message.from_user:
            uid = message.reply_to_message.from_user.id
            await set_autoplay_owner(chat_id, uid)
            return await message.reply_text(f"✅ Autoplay owner set to {message.reply_to_message.from_user.mention}")

        owner = await get_autoplay_owner(chat_id)
        if not owner:
            return await message.reply_text("No autoplay owner set for this chat.")
        return await message.reply_text(f"Current autoplay owner: <code>{owner}</code>")
    except Exception as e:
        await message.reply_text(f"Error managing autoplay owner: {e}")


@app.on_message(filters.command(["playautoplay"]) & filters.group & ~BANNED_USERS)
@AdminRightsCheck
async def play_autoplay_wrapper(client, message: Message, _, chat_id):
    """Attempt to run the repository's autoplay.py on the host where this bot runs.

    Note: This will only work if the bot process has permission to spawn subprocesses and
    the host environment has Python and required dependencies installed.
    """
    try:
        script = os.path.join(os.getcwd(), "autoplay.py")
        if not os.path.isfile(script):
            return await message.reply_text("autoplay.py not found on the server.")
        # Start the script in the background
        # Use python3 and detach
        subprocess.Popen(["python3", script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        await message.reply_text("▶️ autoplay.py started on the server (background process).")
    except Exception as e:
        await message.reply_text(f"Failed to start autoplay.py: {e}")


@app.on_message(filters.command(["skipnext", "skipn", "skip_next"]) & filters.group & ~BANNED_USERS)
@AdminRightsCheck
async def skip_next(client, message: Message, _, chat_id):
    """Remove the next queued track (skip the upcoming song) without stopping the current stream."""
    try:
        check = db.get(chat_id)
        if not check or len(check) < 2:
            return await message.reply_text("There is no next track in the queue to skip.")
        # pop the next item (index 1)
        skipped = check.pop(1)
        try:
            await auto_clean(skipped)
        except Exception:
            pass
        title = skipped.get("title") or str(skipped.get("file"))
        await message.reply_text(f"⏭️ Skipped next track: {title}")
    except Exception as e:
        await message.reply_text(f"Failed to skip next track: {e}")
