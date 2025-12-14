import os
import time
import asyncio

import aiohttp
import m3u8

import config
from utils import progress_text

async def download_direct(url: str, dest: str, status_msg, title: str):
    start = time.time()
    async with aiohttp.ClientSession() as sess:
        async with sess.get(url) as resp:
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


async def download_m3u8(url: str, dest: str, status_msg, title: str):
    start = time.time()
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                raise Exception(f"m3u8 HTTP {resp.status}")
            text = await resp.text()

    if "#EXTM3U" not in text:
        raise Exception("Yeh valid .m3u8 playlist nahi lagti.")

    pl = m3u8.loads(text)
    base_url = url

    if pl.is_variant and pl.playlists:
        best = max(pl.playlists, key=lambda p: (p.stream_info.bandwidth or 0))
        media_url = best.absolute_uri or media_url
        async with aiohttp.ClientSession() as session:
            async with session.get(media_url) as resp:
                if resp.status != 200:
                    raise Exception(f"variant m3u8 HTTP {resp.status}")
                text = await resp.text()
        pl = m3u8.loads(text)
        base_url = media_url

    segments = list(pl.segments)
    if not segments:
        raise Exception("Is m3u8 file me koi segments nahi mile.")

    total_seg = len(segments)
    downloaded = 0
    last = 0

    with open(dest, "wb") as out:
        async with aiohttp.ClientSession() as session:
            for idx, seg in enumerate(segments, start=1):
                seg_url = seg.absolute_uri or seg.uri
                async with session.get(seg_url) as resp:
                    if resp.status != 200:
                        raise Exception(f"segment HTTP {resp.status}")
                    async for chunk in resp.content.iter_chunked(512 * 1024):
                        if not chunk:
                            continue
                        out.write(chunk)
                        downloaded += len(chunk)
                now = time.time()
                if now - last > 2:
                    pct = idx * 100 / total_seg
                    txt = progress_text(
                        title, downloaded, None, start, "to my server"
                    ) + f"\n(segments: {idx}/{total_seg}, ~{pct:.1f}%)"
                    try:
                        await status_msg.edit_text(txt)
                    except Exception:
                        pass
                    last = now

    return dest
