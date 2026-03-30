import os
import threading
import asyncio
from datetime import datetime, timedelta
import pytz
from flask import Flask
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# =====================
# WEB SERVER (RENDER)
# =====================

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot running"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_web).start()

# =====================
# ENV
# =====================

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION = os.getenv("SESSION")

client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

# =====================
# DATA RAM
# =====================

user_words = {}
message_words = {}

# =====================
# HITUNG KATA
# =====================

@client.on(events.NewMessage)
async def count_words(event):

    if event.raw_text.startswith("/"):
        return

    user = event.sender_id
    msg_id = event.id

    words = len(event.raw_text.split())

    user_words[user] = user_words.get(user, 0) + words
    message_words[msg_id] = (user, words)

# =====================
# PESAN DIHAPUS
# =====================

@client.on(events.MessageDeleted)
async def deleted(event):

    for msg_id in event.deleted_ids:

        if msg_id in message_words:

            user, words = message_words[msg_id]

            user_words[user] -= words

            del message_words[msg_id]

# =====================
# CEK JUMLAH KATA
# =====================

@client.on(events.NewMessage(pattern="/itungkata"))
async def check_words(event):

    total = user_words.get(event.sender_id, 0)

    await event.reply(f"Total kata kamu hari ini: {total}")

# =====================
# RESET 00:00 WIB
# =====================

async def reset_midnight():

    global user_words, message_words

    tz = pytz.timezone("Asia/Jakarta")

    while True:

        now = datetime.now(tz)

        tomorrow = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)

        wait = (tomorrow - now).total_seconds()

        await asyncio.sleep(wait)

        user_words = {}
        message_words = {}

        print("Reset harian 00:00 WIB")

# =====================
# RUN
# =====================

async def main():

    await client.start()

    asyncio.create_task(reset_midnight())

    print("Bot berjalan")

    await client.run_until_disconnected()

asyncio.run(main())
