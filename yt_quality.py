import os
import time
import asyncio

from yt_dlp import YoutubeDL

import config
from client import bot
from utils import progress_text, is_youtube_link
from downloaders import download_direct
from db import save_file_record

from pyrogram import enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton


async def extract_yt_info(url: str):
    loop = asyncio.get_running_loop()

    def _extract():
        headers = {"User-Agent": config.YT_USER_AGENT}
        ydl_opts = {
            "quiet": True,
            "skip_download": True,
            "noplaylist": True,
            "geo_bypass": True,
            "http_headers": headers,
        }
        if config.COOKIE_FILE:
            ydl_opts["cookiefile"] = config.COOKIE_FILE
        with YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)

    try:
        return await loop.run_in_executor(None, _extract)
    except Exception as e:
        msg = str(e)
        if "does not look like a Netscape format cookies file" in msg:
            raise Exception(
                "YT_COOKIES ka format galat hai (Netscape tab-separated chahiye)."
            )
        if ("Sign in to confirm you’re not a bot" in msg) or \
           ("Sign in to confirm you're not a bot" in msg):
            raise Exception(
                "Ye YouTube video strong 'not a bot' / login protection ke saath hai.\n"
                "Is type ke videos ko bot se reliably download nahi kiya ja sakta."
            )
        raise Exception(msg)


def pick_quality_formats(info: dict):
    formats = info.get("formats") or []
    best_for = {}

    for f in formats:
        if f.get("vcodec") == "none":
            continue
        url_f = f.get("url")
        if not url_f:
            continue

        h = f.get("height") or 0
        try:
            h = int(h)
        except Exception:
            continue
        if h <= 0:
            continue

        q = None
        if 240 <= h < 420:
            q = "360"
        elif 420 <= h < 560:
            q = "480"
        elif 560 <= h < 800:
            q = "720"
        else:
            continue

        score = 0
        if f.get("ext") == "mp4":
            score += 10
        if f.get("acodec") != "none":
            score += 20
        score += h / 1000

        cur = best_for.get(q)
        if (not cur) or (score > cur["_score"]):
            f2 = dict(f)
            f2["_score"] = score
            best_for[q] = f2

    return best_for


async def start_yt_flow(client, m, url: str):
    if not config.COOKIE_FILE:
        return await m.reply_text(
            "Owner ne YT_COOKIES set nahi kiya.\n"
            "YouTube quality download off hai."
        )

    await m.reply_chat_action(enums.ChatAction.TYPING)

    try:
        info = await extract_yt_info(url)
    except Exception as e:
        return await m.reply_text(f"❌ YouTube se info nahi mil paayi:\n`{e}`")

    title = info.get("title") or "YouTube Video"
    thumb = info.get("thumbnail")
    video_id = info.get("id")
    if not video_id:
        return await m.reply_text("❌ Is video ka ID nahi mil paya.")

    formats = pick_quality_formats(info)
    if not formats:
        return await m.reply_text(
            "❌ Is video ke liye 360p/480p/720p jaisa koi usable format nahi mila.\n"
            "Koi aur video try karo."
        )

    buttons = []
    row = []
    for q in ["360", "480", "720"]:
        if q in formats:
            row.append(InlineKeyboardButton(f"{q}p", callback_data=f"ytq|{video_id}|{q}"))
    if row:
        buttons.append(row)
    buttons.append(
        [InlineKeyboardButton("❌ Cancel", callback_data=f"ytq_cancel|{video_id}")]
    )
    kb = InlineKeyboardMarkup(buttons)

    caption = f"📺 **{title}**\n\nQuality select karo:"
    if thumb:
        await m.reply_photo(thumb, caption=caption, reply_markup=kb)
    else:
        await m.reply_text(caption, reply_markup=kb)


@bot.on_callback_query()
async def yt_callback(client, cq):
    data = cq.data

    if data.startswith("ytq_cancel|"):
        await cq.answer("Cancelled.", show_alert=False)
        try:
            await cq.message.delete()
        except Exception:
            pass
        return

    if data.startswith("ytq|"):
        try:
            _, video_id, q = data.split("|", 2)
        except ValueError:
            return await cq.answer("Invalid data.", show_alert=False)

        url = f"https://www.youtube.com/watch?v={video_id}"

        await cq.answer(f"{q}p selected, downloading…", show_alert=False)

        try:
            info = await extract_yt_info(url)
        except Exception as e:
            return await cq.message.reply_text(
                f"❌ YouTube se info nahi mil paayi (callback):\n`{e}`"
            )

        title = info.get("title") or "YouTube Video"
        formats = pick_quality_formats(info)
        if not formats or q not in formats:
            return await cq.message.reply_text(
                "❌ Is quality ka format ab available nahi hai.\n"
                "Ho sakta hai YouTube ne kuch block kar diya ho."
            )

        fmt = formats[q]
        fmt_url = fmt["url"]
        headers = fmt.get("http_headers") or {}
        ext = fmt.get("ext") or "mp4"
        safe_title = "".join(c for c in title if c not in r'\/:*?\"<>|')
        file_name = f"{safe_title}_{q}p.{ext}"
        dest = os.path.join(config.DOWNLOAD_DIR, file_name)
        full_title = f"{title} [{q}p]"

        status = await cq.message.reply_text("⬇️ Download shuru ho raha hai…")

        path = None
        try:
            path = await download_direct(fmt_url, dest, status, full_title, headers=headers)
            await status.edit_text("📤 Telegram pe upload ho raha hai…")

            start = time.time()

            async def up_progress(current, total):
                txt = progress_text(full_title, current, total, start, "to Telegram")
                try:
                    await status.edit_text(txt)
                except Exception:
                    pass

            sent = await cq.message.reply_video(
                path,
                caption=full_title,
                progress=up_progress,
            )

            try:
                await status.delete()
            except Exception:
                pass

            doc = sent.video or sent.document
            save_file_record(full_title, doc.file_id if doc else None, bool(sent.video))

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
