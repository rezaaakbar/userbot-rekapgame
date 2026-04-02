import os
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

async def ambil_chat(event):
    return await event.get_chat()

# ================= PROSES REKAP =================

async def proses_rekap(chat, katas, start_time, end_time):

    wib = timezone(timedelta(hours=7))
    me = await client.get_me()

    data = {kata: defaultdict(int) for kata in katas}

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

        text = msg.text.lower()

        if text.startswith("/"):
            continue

        for kata in katas:
            if kata in text:
                data[kata][msg.sender_id] += 1

    return data

# ================= FORMAT USER =================

async def format_user(counts):

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

# ================= FORMAT HASIL =================

async def buat_hasil(event, katas, start, end, title):

    chat = await ambil_chat(event)

    data = await proses_rekap(chat, katas, start, end)

    hasil = f"📊 {title}\n\n"
    hasil += f"📝 PESAN YG DI CARI: {', '.join(katas)}\n\n"

    for kata in katas:

        hasil += f"KATA: {kata.upper()}\n"
        hasil += "👤 USER YG MENGIRIM:\n"

        list_user, total = await format_user(data[kata])

        hasil += list_user
        hasil += f"🏆 TOTAL: {total}\n\n"

    await event.reply(hasil)

# ================= REKAP HARI INI =================

@client.on(events.NewMessage(pattern=r'^/rekapkata(?:\s+(.+))?$'))
async def rekap_hari_ini(event):

    if not event.pattern_match.group(1):
        await event.reply("Format: /rekapkata kata")
        return

    args = event.pattern_match.group(1).split()

    if len(args) > 5:
        await event.reply("Maksimal 5 kata")
        return

    katas = [k.lower() for k in args]

    wib = timezone(timedelta(hours=7))
    now = datetime.now(wib)

    start = datetime(now.year, now.month, now.day, tzinfo=wib)

    await buat_hasil(event, katas, start, now, "JUMLAH PESAN HARI INI")

# ================= REKAP KEMARIN =================

@client.on(events.NewMessage(pattern=r'^/rekapkata1(?:\s+(.+))?$'))
async def rekap_kemarin(event):

    if not event.pattern_match.group(1):
        await event.reply("Format: /rekapkata1 kata")
        return

    args = event.pattern_match.group(1).split()

    if len(args) > 5:
        await event.reply("Maksimal 5 kata")
        return

    katas = [k.lower() for k in args]

    wib = timezone(timedelta(hours=7))
    now = datetime.now(wib)

    start = datetime(now.year, now.month, now.day, tzinfo=wib) - timedelta(days=1)
    end = datetime(now.year, now.month, now.day, tzinfo=wib)

    await buat_hasil(event, katas, start, end, "JUMLAH PESAN KEMARIN")

# ================= REKAP 7 HARI =================

@client.on(events.NewMessage(pattern=r'^/rekapkata7(?:\s+(.+))?$'))
async def rekap7(event):

    if not event.pattern_match.group(1):
        await event.reply("Format: /rekapkata7 kata")
        return

    args = event.pattern_match.group(1).split()

    if len(args) > 5:
        await event.reply("Maksimal 5 kata")
        return

    katas = [k.lower() for k in args]

    wib = timezone(timedelta(hours=7))
    now = datetime.now(wib)

    start = now - timedelta(days=6)

    await buat_hasil(event, katas, start, now, "JUMLAH PESAN 7 HARI TERAKHIR")

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
