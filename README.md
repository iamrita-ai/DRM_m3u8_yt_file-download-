# URL Uploader + YouTube Quality Bot

Features:

- Direct HTTP/HTTPS links download (mp4/zip/etc.)
- `.m3u8` HLS links download to MP4 (non‑DRM)
- Files saved in MongoDB → `/file <query>` se search
- YouTube links (videos + Shorts):
  - Title + thumbnail show
  - 360p / 480p / 720p quality buttons
  - Selected quality me video Telegram pe

## Env vars (Render / .env)

Required:

- `API_ID`
- `API_HASH`
- `BOT_TOKEN`
- `MONGO_URL`

Optional:

- `FORCE_CH` – channel username (without `@`)
- `FORCE_LINK` – join link
- `LOGS_CHANNEL` – int chat id (not used in this minimal version)
- `OWNER_CONTACT` – owner contact URL

YouTube cookies (recommended for some videos):

- `YT_COOKIES` – full Netscape cookie file content (tab‑separated)

Example Netscape format (one per line):

```text
.youtube.com	TRUE	/	TRUE	1765358320	GPS	1
...

Deploy (Render Web Service)
Build Command: (empty)
Start Command: python bot.py
Limitations
Some YouTube videos are:
age‑restricted,
region‑locked,
or use “not a bot” JavaScript challenge.
Even with cookies, such videos may still fail with 403/429 or n challenge warnings.
Ye YouTube/IP level ka protection hai; Python code se reliable fix possible nahi.

text


---

Is structure se:

- Direct/m3u8 + `/file` bilkul simple, stable.  
- YouTube ke liye quality select + cookies support add ho gaya.  
- Agar YouTube 429 / n‑challenge kare, error clearly dikhega (aur tum jaaoge ki restriction YouTube side se hai, cookies se nahi).
