import os
from datetime import datetime
from collections import defaultdict
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from flask import Flask
from threading import Thread

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION = os.getenv("SESSION")

client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

# ================= WEB SERVER =================

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot aktif"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ================= REKAP =================

@client.on(events.NewMessage(pattern="/rekap"))
async def rekap(event):

    if not event.is_group:
        return

    chat = await event.get_chat()

    now = datetime.now()
    start_day = datetime(now.year, now.month, now.day)

    counts = defaultdict(int)

    async for msg in client.iter_messages(chat.id):

        if msg.date.replace(tzinfo=None) < start_day:
            break

        if msg.sender_id:
            counts[msg.sender_id] += 1

    if not counts:
        await event.reply("📊 Belum ada pesan hari ini")
        return

    text = "📊 Rekap Pesan Hari Ini\n\n"

    sorted_users = sorted(counts.items(), key=lambda x: x[1], reverse=True)

    for uid, total in sorted_users:

        try:
            user = await client.get_entity(uid)
            name = user.first_name
        except:
            name = "User"

        text += f"{name} : {total} pesan\n"

    await event.reply(text)

# ================= MAIN =================

async def main():
    await client.start()
    print("BOT TELEGRAM AKTIF")
    await client.run_until_disconnected()

if __name__ == "__main__":

    Thread(target=run_web).start()

    client.loop.run_until_complete(main())
