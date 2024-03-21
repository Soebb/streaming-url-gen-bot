import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

app_url = os.environ.get("DOPRAX_APP_URL")
Bot = Client(
    "vidstBot",
    bot_token = os.environ["BOT_TOKEN"],
    api_id = int(os.environ["API_ID"]),
    api_hash = os.environ["API_HASH"]
)


START_TXT = """
Hi {}, I'm streaming link gen bot.

Send a YouTube video url or a direct download link of a video."
"""

START_BTN = InlineKeyboardMarkup(
        [[
        InlineKeyboardButton('Source Code', url='https://github.com/soebb'),
        ]]
    )


@Bot.on_message(filters.command(["start"]))
async def start(bot, update):
    text = START_TXT.format(update.from_user.mention)
    reply_markup = START_BTN
    await update.reply_text(
        text=text,
        disable_web_page_preview=True,
        reply_markup=reply_markup
    )


@Bot.on_message(filters.private & filters.text)
async def st(_, m):
    vid_url = m.text
    if
        url = https://{app_url}/play?id=" + vid_url
    else:
        url = https://{app_url}/play?id=" + vid_url

    await m.reply(url)
    


Bot.run()
