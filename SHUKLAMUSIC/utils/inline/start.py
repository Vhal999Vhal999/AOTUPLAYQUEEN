# -----------------------------------------------
# 🔸 StrangerMusic Project
# 🔹 Developed & Maintained by: Shashank Shukla (https://github.com/itzshukla)
# 📅 Copyright © 2022 – All Rights Reserved
#
# 📖 License:
# This source code is open for educational and non-commercial use ONLY.
# You are required to retain this credit in all copies or substantial portions of this file.
# Commercial use, redistribution, or removal of this notice is strictly prohibited
# without prior written permission from the author.
#
# ❤️ Made with dedication and love by ItzShukla
# -----------------------------------------------

from pyrogram.types import InlineKeyboardButton

import config
from pyrogram.enums import ButtonStyle
from SHUKLAMUSIC import app

# ── Premium emoji IDs (Emoji_fan37_by_TgEmodziBot pack) ──
_E_SPARK   = 5425103595374669922   # ✨
_E_STAR    = 5422666648110793395   # ⭐️
_E_CROWN   = 6172408388547252980   # 👑
_E_SUPPORT = 5409078930659357770   # 💬
_E_BULB    = 6264574504068978591  # 💡
_E_UPDATE  = 6267185268659328609   # 🔝
_E_DIAMOND = 6089198946285001105  # 💎
_E_BELL    = 6030656587830399914  # 🔔


def _clean_username(username: str) -> str:
    return username.lstrip("@")


def start_panel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["S_B_1"],
                url=f"https://t.me/{app.username}?startgroup=true",
                style=ButtonStyle.PRIMARY,
                icon_custom_emoji_id=_E_SPARK
            ),
            InlineKeyboardButton(
                text=_["S_B_2"],
                url=config.SUPPORT_CHAT,
                style=ButtonStyle.DANGER,
                icon_custom_emoji_id=_E_SUPPORT
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["S_B_4"],
                url=f"https://t.me/{app.username}?start=help",
                style=ButtonStyle.SUCCESS,
                icon_custom_emoji_id=_E_BULB
            ),
        ],
    ]
    return buttons


def private_panel(_):
    buttons = [
        [
            InlineKeyboardButton(
                text=_["S_B_3"],
                url=f"https://t.me/{app.username}?startgroup=true",
                style=ButtonStyle.PRIMARY,
                icon_custom_emoji_id=_E_SPARK
            )
        ],
        [
            InlineKeyboardButton(
                text=_["S_B_6"],
                url=config.SUPPORT_CHANNEL,
                style=ButtonStyle.SUCCESS,
                icon_custom_emoji_id=_E_UPDATE
            ),
            InlineKeyboardButton(
                text=_["S_B_2"],
                url=config.SUPPORT_CHAT,
                style=ButtonStyle.DANGER,
                icon_custom_emoji_id=_E_SUPPORT
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["S_B_4"],
                callback_data="settings_back_helper",
                style=ButtonStyle.SUCCESS,
                icon_custom_emoji_id=_E_BULB
            ),
        ],
        [
            InlineKeyboardButton(
                text=_["S_B_5"],
                url=f"https://t.me/{_clean_username(config.OWNER_USERNAME)}",
                style=ButtonStyle.DANGER,
                icon_custom_emoji_id=_E_CROWN
            ),
        ],
    ]
    return buttons
