from pyrogram import filters
from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from SHUKLAMUSIC import app
from config import BOT_USERNAME
from SHUKLAMUSIC.utils.errors import capture_err
import httpx

# ── emoji_2e47b_by_TgEmodziBot pack IDs ──
_E_STAR   = 6073519257637884127   # 🌟
_E_HEART  = 6071046056555058251   # ❤️
_E_SPARK  = 6073301180673430006   # ✨
_E_GLOW   = 6073456529640525999   # 🤩
_E_FLOWER = 6073145973440253945   # 🌸
_E_LOVE   = 6073518286975276048   # 💗
_E_RIBBON = 6070857967052263096   # 🎀
_E_ROSE   = 6073547170630341250   # 🌹
_E_RIGHT  = 6073261718513913664   # ➡️
_E_BOUQ   = 6073117703965511893   # 💐

def e(eid, fb):
    return f'<emoji id={eid}>{fb}</emoji>'

start_txt = (
    f"{e(_E_STAR,'🌟')} {e(_E_GLOW,'🤩')} <b>ʀᴀᴅʜᴀ ᴍᴜsɪᴄ | ᴍᴀᴅᴀʀᴀ</b> {e(_E_GLOW,'🤩')} {e(_E_STAR,'🌟')}\n\n"
    f"{e(_E_SPARK,'✨')} ʙᴀᴅᴀ ᴀᴀʏᴀ ʙᴏᴛ sᴛᴀᴛs ᴅᴇᴋʜɴᴇ,\n"
    f"{e(_E_LOVE,'💗')} ᴘᴀʜʟᴇ ᴀᴘɴɪ ʟɪɢᴇ ᴋᴇ sᴛᴀᴛs sᴜᴅʜᴀʀ ᴊᴀᴀᴋᴇ !\n\n"
    f"<pre>||{e(_E_RIGHT,'➡️')} ᴜᴩᴛɪᴍᴇ       :  𝟷ʜ:𝟹𝟺ᴍ:𝟻𝟺s\n"
    f"{e(_E_RIGHT,'➡️')} sᴛᴏʀᴀɢᴇ      :  𝟸𝟽.𝟺%\n"
    f"{e(_E_RIGHT,'➡️')} ᴄᴩᴜ ʟᴏᴀᴅ    :  𝟷𝟷.𝟸%\n"
    f"{e(_E_RIGHT,'➡️')} ʀᴀᴍ ᴜsᴇ     :  𝟷𝟽.𝟻%||</pre>\n\n"
    f"{e(_E_ROSE,'🌹')} ᴘᴏᴡєʀєᴅ ʙʏ» <a href=\"https://t.me/Egoist_Destroyer\">𝐌ᴀᴅᴀʀᴀ ⌯</a>\n"
    f"{e(_E_BOUQ,'💐')} {e(_E_FLOWER,'🌸')} {e(_E_RIBBON,'🎀')} {e(_E_HEART,'❤️')}"
)


@app.on_message(filters.command("repo"))
async def start(_, msg):
    buttons = [
        [
            InlineKeyboardButton(
                text="˹ηєᴛᴡᴏʀᴋ˼",
                url="https://t.me/+1NRRqUd1replNTM1",
                style=ButtonStyle.PRIMARY,
                icon_custom_emoji_id=_E_STAR,
            ),
            InlineKeyboardButton(
                text="˹ϻʏ ʜᴏϻє˼",
                url="https://t.me/MADARA_X_SUPPORT",
                style=ButtonStyle.SUCCESS,
                icon_custom_emoji_id=_E_FLOWER,
            ),
        ],
        [
            InlineKeyboardButton(
                text="˹ ϻʏ ϻᴧsᴛєʀ ˼ 👑",
                url="https://t.me/Egoist_Destroyer",
                style=ButtonStyle.DANGER,
                icon_custom_emoji_id=_E_GLOW,
            ),
        ],
    ]

    await msg.reply_photo(
        photo="https://i.ibb.co/rRXc8MGR/image.jpg",
        caption=start_txt,
        reply_markup=InlineKeyboardMarkup(buttons),
    )
