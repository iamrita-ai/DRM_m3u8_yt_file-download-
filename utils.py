import time
from urllib.parse import urlparse

def is_url(text: str) -> bool:
    return text.startswith("http://") or text.startswith("https://")


def is_youtube_link(text: str) -> bool:
    u = text.lower()
    return (
        "youtube.com/watch" in u
        or "youtu.be/" in u
        or "youtube.com/shorts" in u
    )


def classify_url(url: str) -> str:
    u = url.lower()
    path = urlparse(u).path
    if "youtube.com" in u or "youtu.be" in u:
        return "yt"
    if ".m3u8" in path or ".m3u8" in u:
        return "m3u8"
    return "direct"


def make_filename_from_url(url: str, default_ext="mp4") -> str:
    path = urlparse(url).path
    name = path.rsplit("/", 1)[-1].split("?")[0].split("#")[0]
    if not name:
        name = f"file_{int(time.time())}.{default_ext}"
    if "." not in name:
        name = f"{name}.{default_ext}"
    return name


def sizeof_fmt(num: int) -> str:
    if num <= 0:
        return "0 MB"
    return f"{num / (1024 * 1024):.2f} MB"


def time_fmt(sec: float) -> str:
    sec = int(sec)
    if sec <= 0:
        return "0s"
    m, s = divmod(sec, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}h, {m}m"
    if m > 0:
        return f"{m}m, {s}s"
    return f"{s}s"


def progress_text(title: str, current: int, total: int | None,
                  start_time: float, stage: str) -> str:
    now = time.time()
    elapsed = max(1e-3, now - start_time)
    speed = current / (1024 * 1024 * elapsed)

    if total and total > 0:
        pct = current * 100 / total
        bar_len = 20
        filled = int(bar_len * pct / 100)
        bar = "●" * filled + "○" * (bar_len - filled)
        done_str = f"{sizeof_fmt(current)} of  {sizeof_fmt(total)}"
        remain = max(0, total - current)
        eta = remain / max(1, current) * elapsed
        eta_str = time_fmt(eta)
    else:
        pct = 0
        bar = "●○" * 10
        done_str = f"{sizeof_fmt(current)} of  ?"
        eta_str = "calculating..."

    return (
        "➵⋆🪐ᴛᴇᴄʜɴɪᴄᴀʟ_sᴇʀᴇɴᴀ𓂃\n\n"
        f"{title}\n"
        f"{stage}\n"
        f" [{bar}] \n"
        f"◌Progress😉:〘 {pct:.2f}% 〙\n"
        f"Done: 〘{done_str}〙\n"
        f"◌Speed🚀:〘 {speed:.2f} MB/s 〙\n"
        f"◌Time Left⏳:〘 {eta_str} 〙"
    )
