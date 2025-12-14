import os
import asyncio

from pyrogram import filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from client import bot
import config
from db import files, save_file_record
from utils import is_url, is_youtube_link, classify_url, make_filename_from_url
from downloaders import download_direct, download_m3u8
from yt_quality import start_yt_flow


def main_buttons():
    rows = []
    if config.FORCE_LINK or config.FORCE_CH:
        rows.append(
            [InlineKeyboardButton(
                "📢 Join Channel",
                url=config.FORCE_LINK or f"https://t.me/{config.FORCE_CH}"
            )]
        )
    if config.OWNER_CONTACT:
        rows.append([InlineKeyboardButton("💬 Contact Owner", url=config.OWNER_CONTACT)])
    return InlineKeyboardMarkup(rows) if rows else None


async def ensure_subscribed(client, m):
    if not config.FORCE_CH:
        return True
    if m.chat.type != enums.ChatType.PRIVATE:
        return True
    try:
        member = await client.get_chat_member(config.FORCE_CH, m.from_user.id)
        if member.status in (
            enums.ChatMemberStatus.LEFT,
            enums.ChatMemberStatus.BANNED,
        ):
            raise Exception("not joined")
        return True
    except Exception:
        kb = main_buttons()
        await m.reply_text(
            "⚠️ Bot use karne se pehle hamare channel ko join karein.",
            reply_markup=kb,
        )
        return False


@bot.on_message(filters.command("start") & filters.private)
async def start_cmd(client, m):
    if not await ensure_subscribed(client, m):
        return
    await m.reply_text(
        "🌸 **URL Uploader Bot**\n\n"
        "Mujhe koi bhi direct URL bhejo (mp4/zip/etc.) ya `.m3u8` stream link,\n"
        "main usse download karke Telegram file/video bana dungi.\n\n"
        "YouTube links (video/Shorts) bhi bhej sakte ho – main tumse "
        "360p/480p/720p quality poochungi.\n\n"
        "Saved files ko `/file` se search kar sakte ho.",
        reply_markup=main_buttons(),
    )


@bot.on_message(filters.command("help") & filters.private)
async def help_cmd(client, m):
    if not await ensure_subscribed(client, m):
        return
    await m.reply_text(
        "🧿 **How to use**\n\n"
        "• Direct: `https://example.com/video.mp4`\n"
        "• m3u8: `https://example.com/hls/index.m3u8`\n"
        "• YouTube: `https://youtu.be/abc123` ya `https://www.youtube.com/watch?v=abc123`\n\n"
        "Main file download karke Telegram pe bhejungi aur DB me save karungi.\n"
        "`/file Avengers` se saved files search kar sakte ho."
    )


@bot.on_message(filters.command(["file", "files"]) & filters.private)
async def file_cmd(client, m):
    if not await ensure_subscribed(client, m):
        return
    if len(m.command) < 2:
        return await m.reply_text("Use: `/file Avengers`")
    query = " ".join(m.command[1:]).strip()
    if not query:
        return await m.reply_text("Use: `/file Avengers`")

    results = list(
        files.find({"title": {"$regex": query, "$options": "i"}}).limit(30)
    )
    if not results:
        return await m.reply_text(
            "❌ File not found in database.\n\n"
            "Try:\n"
            "• Aur chhota / alag keyword\n"
            "• Spelling check karo"
        )

    await m.reply_text(f"📂 {len(results)} file(s) mili, bhej raha hoon…")

    for doc in results:
        fid = doc.get("file_id")
        if not fid:
            continue
        cap = doc.get("title", "")
        try:
            if doc.get("is_video"):
                await m.reply_video(fid, caption=cap)
            else:
                await m.reply_document(fid, caption=cap)
        except Exception as e:
            print("send db error:", e)
        await asyncio.sleep(1)


@bot.on_message(
    filters.private
    & filters.text
    & ~filters.command(["start", "help", "file", "files"])
)
async def url_handler(client, m):
    if not await ensure_subscribed(client, m):
        return

    text = m.text.strip()

    # Apne error messages ko ignore karo (spam se bacho)
    if text.startswith("❌"):
        return

    if not is_url(text):
        return await m.reply_text(
            "❌ Yeh URL nahi lag raha.\n"
            "Example: `https://example.com/video.mp4`"
        )

    kind = classify_url(text)
    if kind == "yt":
        # YouTube link: quality selection flow
        return await start_yt_flow(client, m, text)

    # Direct / m3u8 download flow
    filename = make_filename_from_url(text)
    dest = os.path.join(config.DOWNLOAD_DIR, filename)
    title = filename

    status = await m.reply_text("⬇️ Download shuru ho raha hai…")

    path = None
    try:
        if kind == "m3u8":
            path = os.path.join(config.DOWNLOAD_DIR, f"m3u8_{int(time.time())}.mp4")
            path = await download_m3u8(text, path, status, title)
            is_video = True
            title = os.path.basename(path)
        else:
            path = dest
            path = await download_direct(text, path, status, title)
            ext = os.path.splitext(path)[1].lower()
            is_video = ext in [".mp4", ".mkv", ".webm", ".mov"]

        await status.edit_text("📤 Telegram pe upload ho raha hai…")

        start = time.time()

        async def up_progress(current, total):
            from utils import progress_text
            txt = progress_text(title, current, total, start, "to Telegram")
            try:
                await status.edit_text(txt)
            except Exception:
                pass

        if is_video:
            sent = await m.reply_video(path, caption=title, progress=up_progress)
        else:
            sent = await m.reply_document(path, caption=title, progress=up_progress)

        try:
            await status.delete()
        except Exception:
            pass

        doc = sent.video or sent.document
        save_file_record(title, doc.file_id if doc else None, bool(sent.video))

    except Exception as e:
        try:
            await status.edit_text(f"❌ Error: `{e}`")
        except Exception:
            pass
    finally:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass
