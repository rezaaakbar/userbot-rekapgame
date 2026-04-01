import os
import re
import asyncio
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from flask import Flask
from threading import Thread

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION = os.getenv("SESSION")

client = TelegramClient(
    StringSession(SESSION),
    API_ID,
    API_HASH,
    auto_reconnect=True,
    connection_retries=None
)

# ================= WEB SERVER =================

app = Flask(__name__)

@app.route("/")
def home():
    return "BOT HIDUP"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ================= AMBIL CHAT =================

async def ambil_chat(event, args):

    if len(args) >= 2:
        try:
            return await client.get_entity(int(args[1]))
        except:
            return await event.get_chat()
    else:
        return await event.get_chat()

# ================= FILTER PESAN =================

def cocok(kata, text):

    pattern = rf'(?<!\w){re.escape(kata)}(?!\w)'
    return re.search(pattern, text)

# ================= REKAP HARI INI =================

@client.on(events.NewMessage(pattern=r'^/rekapkata(?:\s+(.+))?$'))
async def rekap(event):

    if not event.pattern_match.group(1):
        await event.reply("Format: /rekapkata kata")
        return

    args = event.pattern_match.group(1).split()
    kata = args[0].lower()

    chat = await ambil_chat(event, args)

    wib = timezone(timedelta(hours=7))
    now = datetime.now(wib)

    start_day = datetime(now.year, now.month, now.day, tzinfo=wib)

    me = await client.get_me()

    counts = defaultdict(int)

    async for msg in client.iter_messages(chat, reverse=True):

        if msg.date.replace(tzinfo=timezone.utc).astimezone(wib) < start_day:
            break

        if not msg.text:
            continue

        if msg.sender_id == me.id:
            continue

        text = msg.text.lower().strip()

        if text.startswith("/"):
            continue

        if not cocok(kata, text):
            continue

        counts[msg.sender_id] += 1

    hasil = "📊 JUMLAH PESAN HARI INI\n\n"
    hasil += f"📝 PESAN YG DI CARI: {kata}\n\n"
    hasil += "👤 USER YG MENGIRIM:\n"

    total = 0

    for uid, jumlah in sorted(counts.items(), key=lambda x: x[1], reverse=True):

        try:
            user = await client.get_entity(uid)
            name = f"@{user.username}" if user.username else user.first_name
        except:
            name = "user"

        hasil += f"{name} : {jumlah}\n"
        total += jumlah

    hasil += f"\n🏆 TOTAL: {total}"

    await event.reply(hasil)

# ================= REKAP 7 HARI =================

@client.on(events.NewMessage(pattern=r'^/rekapkata7(?:\s+(.+))?$'))
async def rekap7(event):

    if not event.pattern_match.group(1):
        await event.reply("Format: /rekapkata7 kata")
        return

    args = event.pattern_match.group(1).split()
    kata = args[0].lower()

    chat = await ambil_chat(event, args)

    wib = timezone(timedelta(hours=7))
    now = datetime.now(wib)

    start = now - timedelta(days=6)

    me = await client.get_me()

    counts = defaultdict(int)

    async for msg in client.iter_messages(chat, reverse=True):

        msg_time = msg.date.replace(tzinfo=timezone.utc).astimezone(wib)

        if msg_time < start:
            break

        if not msg.text:
            continue

        if msg.sender_id == me.id:
            continue

        text = msg.text.lower().strip()

        if text.startswith("/"):
            continue

        if not cocok(kata, text):
            continue

        counts[msg.sender_id] += 1

    start_text = start.strftime("%d %B %Y")
    now_text = now.strftime("%d %B %Y")

    hasil = "📊 JUMLAH PESAN 7 HARI TERAKHIR\n"
    hasil += f"📅 {start_text} - {now_text}\n\n"
    hasil += f"📝 PESAN YG DI CARI: {kata}\n\n"
    hasil += "👤 USER YG MENGIRIM:\n"

    total = 0

    for uid, jumlah in sorted(counts.items(), key=lambda x: x[1], reverse=True):

        try:
            user = await client.get_entity(uid)
            name = f"@{user.username}" if user.username else user.first_name
        except:
            name = "user"

        hasil += f"{name} : {jumlah}\n"
        total += jumlah

    hasil += f"\n🏆 TOTAL: {total}"

    await event.reply(hasil)

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
