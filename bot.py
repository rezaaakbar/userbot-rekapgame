import os
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from flask import Flask
from threading import Thread
import asyncio

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION = os.getenv("SESSION")

client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

# ================= WEB SERVER =================

app = Flask(__name__)

@app.route("/")
def home():
    return "BOT HIDUP"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ================= FUNCTION AMBIL CHAT =================

async def ambil_chat(event, args):

    if len(args) >= 2:
        try:
            return await client.get_entity(int(args[1]))
        except:
            return await event.get_chat()
    else:
        return await event.get_chat()

# ================= REKAP HARI INI =================

@client.on(events.NewMessage(pattern=r"/rekapkata (.+)"))
async def rekap(event):

    args = event.pattern_match.group(1).split()
    kata = args[0].lower()

    chat = await ambil_chat(event, args)

    wib = timezone(timedelta(hours=7))
    now = datetime.now(wib)
    start_day = datetime(now.year, now.month, now.day, tzinfo=wib)

    counts = defaultdict(int)

    async for msg in client.iter_messages(chat):

        if msg.date < start_day:
            break

        if not msg.text:
            continue

        if msg.text.startswith("/"):
            continue

        if kata not in msg.text.lower():
            continue

        counts[msg.sender_id] += 1

    text = "📊 JUMLAH PESAN HARI INI\n\n"
    text += f"📝 PESAN YG DI CARI: {kata}\n\n"
    text += "👤 USER YG MENGIRIM:\n"

    total = 0

    for uid, jumlah in sorted(counts.items(), key=lambda x: x[1], reverse=True):

        try:
            user = await client.get_entity(uid)
            name = f"@{user.username}" if user.username else user.first_name
        except:
            name = "user"

        text += f"{name} : {jumlah}\n"
        total += jumlah

    text += f"\n🏆 TOTAL: {total}"

    await event.reply(text)

# ================= REKAP 7 HARI =================

@client.on(events.NewMessage(pattern=r"/rekapkata7 (.+)"))
async def rekap7(event):

    args = event.pattern_match.group(1).split()
    kata = args[0].lower()

    chat = await ambil_chat(event, args)

    wib = timezone(timedelta(hours=7))
    now = datetime.now(wib)
    start = now - timedelta(days=7)

    counts = defaultdict(int)

    async for msg in client.iter_messages(chat):

        if msg.date < start:
            break

        if not msg.text:
            continue

        if msg.text.startswith("/"):
            continue

        if kata not in msg.text.lower():
            continue

        counts[msg.sender_id] += 1

    start_text = start.strftime("%d %B %Y")
    now_text = now.strftime("%d %B %Y")

    text = "📊 JUMLAH PESAN 7 HARI TERAKHIR\n"
    text += f"📅 {start_text} - {now_text}\n\n"
    text += f"📝 PESAN YG DI CARI: {kata}\n\n"
    text += "👤 USER YG MENGIRIM:\n"

    total = 0

    for uid, jumlah in sorted(counts.items(), key=lambda x: x[1], reverse=True):

        try:
            user = await client.get_entity(uid)
            name = f"@{user.username}" if user.username else user.first_name
        except:
            name = "user"

        text += f"{name} : {jumlah}\n"
        total += jumlah

    text += f"\n🏆 TOTAL: {total}"

    await event.reply(text)

# ================= AUTO RECONNECT =================

async def start_bot():

    while True:

        try:
            print("BOT STARTING...")
            await client.start()
            print("BOT AKTIF")
            await client.run_until_disconnected()

        except Exception as e:
            print("ERROR:", e)
            await asyncio.sleep(10)

# ================= MAIN =================

if __name__ == "__main__":

    Thread(target=run_web).start()

    client.loop.run_until_complete(start_bot())
