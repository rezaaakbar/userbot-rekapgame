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
    return "BOT REKAP GAME HIDUP"

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

# ================= CEK KATA =================

def cocok(kata, text):

    # lebih stabil buat username dan kata biasa
    kata = kata.lower()
    text = text.lower()

    return kata in text

# ================= FUNCTION REKAP =================

async def proses_rekap(chat, kata, start_time, end_time):

    wib = timezone(timedelta(hours=7))
    me = await client.get_me()

    counts = defaultdict(int)

    async for msg in client.iter_messages(chat):

        msg_time = msg.date.replace(tzinfo=timezone.utc).astimezone(wib)

        if msg_time < start_time:
            break

        if msg_time > end_time:
            continue

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

    return counts

# ================= FORMAT HASIL =================

async def format_hasil(counts):

    hasil = ""
    total = 0

    for uid, jumlah in sorted(counts.items(), key=lambda x: x[1], reverse=True):

        try:
            user = await client.get_entity(uid)
            name = f"@{user.username}" if user.username else user.first_name
        except:
            name = "user"

        hasil += f"{name} : {jumlah}\n"
        total += jumlah

    return hasil, total

# ================= REKAP HARI INI =================

@client.on(events.NewMessage(pattern=r'^/rekapkata(?:\s+(.+))?$'))
async def rekap_hari_ini(event):

    if not event.pattern_match.group(1):
        await event.reply("Format: /rekapkata kata")
        return

    args = event.pattern_match.group(1).split()
    kata = args[0].lower()

    chat = await ambil_chat(event, args)

    wib = timezone(timedelta(hours=7))
    now = datetime.now(wib)

    start = datetime(now.year, now.month, now.day, tzinfo=wib)

    counts = await proses_rekap(chat, kata, start, now)

    list_user, total = await format_hasil(counts)

    hasil = "📊 JUMLAH PESAN HARI INI\n\n"
    hasil += f"📝 PESAN YG DI CARI: {kata}\n\n"
    hasil += "👤 USER YG MENGIRIM:\n"
    hasil += list_user
    hasil += f"\n🏆 TOTAL: {total}"

    await event.reply(hasil)

# ================= REKAP KEMARIN =================

@client.on(events.NewMessage(pattern=r'^/rekapkata1(?:\s+(.+))?$'))
async def rekap_kemarin(event):

    if not event.pattern_match.group(1):
        await event.reply("Format: /rekapkata1 kata")
        return

    args = event.pattern_match.group(1).split()
    kata = args[0].lower()

    chat = await ambil_chat(event, args)

    wib = timezone(timedelta(hours=7))
    now = datetime.now(wib)

    start = datetime(now.year, now.month, now.day, tzinfo=wib) - timedelta(days=1)
    end = datetime(now.year, now.month, now.day, tzinfo=wib)

    counts = await proses_rekap(chat, kata, start, end)

    list_user, total = await format_hasil(counts)

    tanggal = start.strftime("%d %B %Y")

    hasil = "📊 JUMLAH PESAN KEMARIN\n\n"
    hasil += f"📅 {tanggal}\n\n"
    hasil += f"📝 PESAN YG DI CARI: {kata}\n\n"
    hasil += "👤 USER YG MENGIRIM:\n"
    hasil += list_user
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

    counts = await proses_rekap(chat, kata, start, now)

    list_user, total = await format_hasil(counts)

    start_text = start.strftime("%d %B %Y")
    now_text = now.strftime("%d %B %Y")

    hasil = "📊 JUMLAH PESAN 7 HARI TERAKHIR\n"
    hasil += f"📅 {start_text} - {now_text}\n\n"
    hasil += f"📝 PESAN YG DI CARI: {kata}\n\n"
    hasil += "👤 USER YG MENGIRIM:\n"
    hasil += list_user
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
