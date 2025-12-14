import os

# Telegram API credentials (Render env me set karo)
API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]

# MongoDB URL (Render env: MONGO_URL)
MONGO_URL = os.environ["MONGO_URL"]

# Force-sub (optional)
FORCE_CH = os.environ.get("FORCE_CH")      # e.g. "serenaunzipbot"
FORCE_LINK = os.environ.get("FORCE_LINK")  # e.g. "https://t.me/serenaunzipbot"

# Logging (optional, agar nahi chahiye to None rehne do)
LOGS_CHANNEL = int(os.environ.get("LOGS_CHANNEL", "0"))  # e.g. -100123456789

# Owner contact (button ke liye)
OWNER_CONTACT = os.environ.get("OWNER_CONTACT", "https://t.me/technicalserena")

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ==== YouTube cookies (Netscape format) ====
# YT_COOKIES env me poora cookie file paste karo (tabs ke saath)
YT_COOKIES = os.environ.get("YT_COOKIES", "").strip()
COOKIE_FILE = None
if YT_COOKIES:
    COOKIE_FILE = "yt_cookies.txt"
    with open(COOKIE_FILE, "w", encoding="utf-8") as f:
        f.write(YT_COOKIES)

# Simple browser-like User-Agent
YT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
