import threading
from flask import Flask

from client import bot
import handlers  # noqa: F401  (imports handlers and attach decorators)
import yt_quality  # noqa: F401  (imports callback handler)

app = Flask(__name__)


@app.route("/")
def home():
    return "URL Uploader + YouTube Quality Bot is running"


def run_flask():
    import os
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.run()
