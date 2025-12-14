import time
import aiohttp
import config
from utils import progress_text

async def download_direct(url: str, dest: str, status_msg, title: str, headers=None):
    start = time.time()
    session_headers = headers.copy() if headers else {}
    # YT + normal links ke liye ek hi UA rakhna safe hai
    session_headers.setdefault("User-Agent", config.YT_USER_AGENT)

    async with aiohttp.ClientSession(headers=session_headers) as sess:
        async with sess.get(url) as resp:
            if resp.status == 403:
                raise Exception(
                    "Direct link HTTP 403 (forbidden) – server ne access block kiya.\n"
                    "Yeh ho sakta hai anti-bot / login / geo restriction ki wajah se ho."
                )
            if resp.status != 200:
                raise Exception(f"HTTP {resp.status}")
            total = int(resp.headers.get("Content-Length", 0))
            done = 0
            last = 0
            with open(dest, "wb") as f:
                async for chunk in resp.content.iter_chunked(1024 * 1024):
                    if not chunk:
                        continue
                    f.write(chunk)
                    done += len(chunk)
                    now = time.time()
                    if total and now - last > 2:
                        txt = progress_text(title, done, total, start, "to my server")
                        try:
                            await status_msg.edit_text(txt)
                        except Exception:
                            pass
                        last = now
    if total:
        txt = progress_text(title, total, total, start, "to my server")
        try:
            await status_msg.edit_text(txt)
        except Exception:
            pass
    return dest
