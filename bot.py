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
    return "BOT REKAP KATA AKTIF"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ================= AMBIL CHAT & KATA =================

async def ambil_chat_dan_kata(event, text):

    match = re.search(r"\((-?\d+)\)", text)

    chat_id = None

    if match:
        chat_id = int(match.group(1))
        text = re.sub(r"\((-?\d+)\)", "", text)

    kata_list = text.split()[:10]

    if chat_id:
        chat = await client.get_entity(chat_id)
    else:
        chat = await event.get_chat()

    return chat, kata_list

# ================= PROSES REKAP =================

async def proses_rekap(chat, kata_list, start_time, end_time):

    wib = timezone(timedelta(hours=7))
    me = await client.get_me()

    counts = {kata: defaultdict(int) for kata in kata_list}

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

        for kata in kata_list:
            if kata.lower() in text:
                counts[kata][msg.sender_id] += 1

    return counts

# ================= FORMAT HASIL =================

async def format_hasil_kata(counts):

    hasil = ""

    for kata in counts:

        hasil += f"\nKATA: {kata.upper()}\n"

        total = 0

        for uid, jumlah in sorted(counts[kata].items(), key=lambda x: x[1], reverse=True):

            try:
                user = await client.get_entity(uid)
                name = f"@{user.username}" if user.username else user.first_name
            except:
                name = "user"

            hasil += f"{name} : {jumlah}\n"
            total += jumlah

        hasil += f"TOTAL: {total}\n"

    return hasil

# ================= REKAP HARI INI =================

@client.on(events.NewMessage(pattern=r'^/rekapkata(?:\s+(.+))?$'))
async def rekap_hari_ini(event):

    if not event.pattern_match.group(1):
        await event.reply("Format: /rekapkata kata1 kata2 (IDGRUP)")
        return

    text = event.pattern_match.group(1)

    chat, kata_list = await ambil_chat_dan_kata(event, text)

    wib = timezone(timedelta(hours=7))
    now = datetime.now(wib)

    start = datetime(now.year, now.month, now.day, tzinfo=wib)

    counts = await proses_rekap(chat, kata_list, start, now)

    list_user = await format_hasil_kata(counts)

    hasil = "📊 JUMLAH PESAN HARI INI\n\n"
    hasil += f"📝 PESAN YG DI CARI: {', '.join(kata_list)}\n"
    hasil += list_user

    await event.reply(hasil)

# ================= REKAP KEMARIN =================

@client.on(events.NewMessage(pattern=r'^/rekapkata1(?:\s+(.+))?$'))
async def rekap_kemarin(event):

    if not event.pattern_match.group(1):
        await event.reply("Format: /rekapkata1 kata1 kata2 (IDGRUP)")
        return

    text = event.pattern_match.group(1)

    chat, kata_list = await ambil_chat_dan_kata(event, text)

    wib = timezone(timedelta(hours=7))
    now = datetime.now(wib)

    start = datetime(now.year, now.month, now.day, tzinfo=wib) - timedelta(days=1)
    end = datetime(now.year, now.month, now.day, tzinfo=wib)

    counts = await proses_rekap(chat, kata_list, start, end)

    list_user = await format_hasil_kata(counts)

    tanggal = start.strftime("%d %B %Y")

    hasil = "📊 JUMLAH PESAN KEMARIN\n\n"
    hasil += f"📅 {tanggal}\n\n"
    hasil += f"📝 PESAN YG DI CARI: {', '.join(kata_list)}\n"
    hasil += list_user

    await event.reply(hasil)

# ================= REKAP 7 HARI =================

@client.on(events.NewMessage(pattern=r'^/rekapkata7(?:\s+(.+))?$'))
async def rekap7(event):

    if not event.pattern_match.group(1):
        await event.reply("Format: /rekapkata7 kata1 kata2 (IDGRUP)")
        return

    text = event.pattern_match.group(1)

    chat, kata_list = await ambil_chat_dan_kata(event, text)

    wib = timezone(timedelta(hours=7))
    now = datetime.now(wib)

    start = now - timedelta(days=6)

    counts = await proses_rekap(chat, kata_list, start, now)

    list_user = await format_hasil_kata(counts)

    start_text = start.strftime("%d %B %Y")
    now_text = now.strftime("%d %B %Y")

    hasil = "📊 JUMLAH PESAN 7 HARI TERAKHIR\n"
    hasil += f"📅 {start_text} - {now_text}\n\n"
    hasil += f"📝 PESAN YG DI CARI: {', '.join(kata_list)}\n"
    hasil += list_user

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
