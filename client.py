from pyrogram import Client, enums
import config

bot = Client(
    "url-uploader-bot",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    bot_token=config.BOT_TOKEN,
    parse_mode=enums.ParseMode.MARKDOWN,
)
