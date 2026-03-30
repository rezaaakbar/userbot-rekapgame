import os
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from flask import Flask
import threading

# env
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
session = os.getenv("SESSION")

# telegram client
client = TelegramClient(StringSession(session), api_id, api_hash)

# penyimpanan pesan
data = {}

@client.on(events.NewMessage)
async def count(event):

    if not event.text:
        return

    if event.text.startswith("/"):
        return

    uid = event.sender_id
    data[uid] = data.get(uid, 0) + 1


@client.on(events.NewMessage(pattern="/itungkata"))
async def cek(event):

    if not event.is_reply:
        await event.reply("reply pesan user")
        return

    msg = await event.get_reply_message()
    uid = msg.sender_id
    total = data.get(uid, 0)

    await event.reply(f"total pesan hari ini: {total}")


# ===== server kecil supaya render detect port =====

app = Flask(__name__)

@app.route("/")
def home():
    return "bot hidup"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ===== main =====

async def main():
    await client.start()
    print("BOT AKTIF")
    await client.run_until_disconnected()


def start():
    threading.Thread(target=run_web).start()
    asyncio.run(main())


start()
