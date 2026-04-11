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

client.parse_mode = "html"

# ================= WEB SERVER =================
app = Flask(__name__)

@app.route("/")
def home():
    return "BOT AKTIF"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ================= HAPUS PESAN =================
async def hapus_pesan(chat_id, msg_id, delay=180):
    await asyncio.sleep(delay)
    try:
        await client.delete_messages(chat_id, msg_id)
    except:
        pass

async def hapus_cmd(chat_id, msg_ids, delay=2):
    await asyncio.sleep(delay)
    try:
        await client.delete_messages(chat_id, msg_ids)
    except:
        pass

# ================= AMBIL CHAT =================
async def ambil_chat_dan_kata(event, text):
    match = re.search(r"(-?\d+)", text)
    chat_id = None

    if match:
        chat_id = int(match.group(1))
        text = re.sub(r"(-?\d+)", "", text)

    kata_list = text.split()[:10]

    if chat_id:
        chat = await client.get_entity(chat_id)
    else:
        chat = await event.get_chat()

    return chat, kata_list

# ================= PROSES REKAP =================
async def proses_rekap(chat, kata_list, start_time, end_time):
    wib = timezone(timedelta(hours=7))
    counts = {kata: defaultdict(int) for kata in kata_list}

    async for msg in client.iter_messages(chat):
        msg_time = msg.date.replace(tzinfo=timezone.utc).astimezone(wib)

        if msg_time < start_time:
            break

        if msg_time > end_time:
            continue

        if not msg.text:
            continue

        text = msg.text.lower().strip()

        if text.startswith("/"):
            continue

        for kata in kata_list:
            if kata.lower() in text:
                counts[kata][msg.sender_id] += 1

    return counts

# ================= FORMAT =================
async def format_hasil_kata(counts):
    hasil = ""
    for kata in counts:
        hasil += f"\n🔥 <b>KATA: {kata.upper()}</b>\n"
        total = 0

        for uid, jumlah in sorted(counts[kata].items(), key=lambda x: x[1], reverse=True):
            try:
                user = await client.get_entity(uid)
                name = f"@{user.username}" if user.username else user.first_name
            except:
                name = "user"

            hasil += f"{name} : <code>{jumlah}</code>\n"
            total += jumlah

        hasil += f"📊 TOTAL: <code>{total}</code>\n"

    return hasil

# ================= REKAP =================
@client.on(events.NewMessage(pattern=r'^/rekapkata(?:\s+(.+))?$'))
async def rekap_hari_ini(event):
    if not event.pattern_match.group(1):
        await event.reply("Format: /rekapkata kata1 kata2")
        return

    text = event.pattern_match.group(1)
    chat, kata_list = await ambil_chat_dan_kata(event, text)

    wib = timezone(timedelta(hours=7))
    now = datetime.now(wib)
    start = datetime(now.year, now.month, now.day, tzinfo=wib)

    counts = await proses_rekap(chat, kata_list, start, now)
    hasil = f"📊 JUMLAH PESAN HARI INI\n📅 {now.strftime('%d-%m-%Y')}\n\n"
    hasil += await format_hasil_kata(counts)

    await event.reply(hasil)

@client.on(events.NewMessage(pattern=r'^/rekapkata1(?:\s+(.+))?$'))
async def rekap_kemarin(event):
    if not event.pattern_match.group(1):
        return

    text = event.pattern_match.group(1)
    chat, kata_list = await ambil_chat_dan_kata(event, text)

    wib = timezone(timedelta(hours=7))
    now = datetime.now(wib)
