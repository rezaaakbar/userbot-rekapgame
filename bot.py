import os
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

    if len(args) >= 1:
        try:
            if args[-1].startswith("-100"):
                return await client.get_entity(int(args[-1]))
        except:
            pass

    return await event.get_chat()

# ================= CARI KATA =================

def cocok(katas, text):

    text = (text or "").lower()

    hasil = set()

    for kata in katas:
        if kata in text:
            hasil.add(kata)

    return list(hasil)

# ================= FORMAT USER =================

async def get_name(uid):

    try:
        user = await client.get_entity(uid)
        return f"@{user.username}" if user.username else user.first_name
    except:
        return "user"

# ================= PROSES REKAP =================

async def proses_rekap(chat, katas, start, end):

    wib = timezone(timedelta(hours=7))
    me = await client.get_me()

    user_counts = defaultdict(int)
    kata_counts = defaultdict(int)

    async for msg in client.iter_messages(chat, reverse=True):

        if not msg.date:
            continue

        msg_time = msg.date.astimezone(wib)

        if msg_time < start:
            break

        if msg_time > end:
            continue

        text = (msg.text or "").lower().strip()

        if not text:
            continue

        if msg.sender_id == me.id:
            continue

        if text.startswith("/"):
            continue

        ketemu = cocok(katas, text)

        if not ketemu:
            continue

        # user dihitung 1 kali per pesan
        user_counts[msg.sender_id] += 1

        # kata tidak double dalam 1 pesan
        for k in set(ketemu):
            kata_counts[k] += 1

    return user_counts, kata_counts

# ================= FORMAT HASIL =================

async def format_hasil(title, tanggal, katas, user_counts, kata_counts):

    hasil = f"{title}\n{tanggal}\n\n"

    hasil += "📝 PESAN YG DICARI:\n"
    hasil += " ".join(katas) + "\n\n"

    hasil += "📌 KATA:\n"

    for k in katas:
        hasil += f"{k} : {kata_counts[k]}\n"

    hasil += "\n👤 USER:\n"

    if not user_counts:
        hasil += "Tidak ada data\n"
    else:
        for uid, jumlah in sorted(user_counts.items(), key=lambda x: x[1], reverse=True):

            name = await get_name(uid)
            hasil += f"{name} : {jumlah}\n"

    hasil += "\n🏆 TOTAL:\n"

    for k in katas:
        hasil += f"{k} : {kata_counts[k]}\n"

    return hasil

# ================= VALIDASI KATA =================

async def ambil_kata(event):

    text = event.pattern_match.group(1)

    if not text:
        await event.reply("❌ Minimal 1 kata")
        return None

    args = text.split()

    katas = []

    for a in args:
        if not a.startswith("-100"):
            katas.append(a.lower())

    if len(katas) < 1:
        await event.reply("❌ Minimal 1 kata")
        return None

    if len(katas) > 5:
        await event.reply("❌ Maksimal 5 kata")
        return None

    return args, katas

# ================= REKAP HARI INI =================

@client.on(events.NewMessage(pattern=r'^/rekapkata(?:\s+(.+))?$'))
async def rekap(event):

    data = await ambil_kata(event)
    if not data:
        return

    args, katas = data
    chat = await ambil_chat(event, args)

    wib = timezone(timedelta(hours=7))
    now = datetime.now(wib)
    start = datetime(now.year, now.month, now.day, tzinfo=wib)

    user_counts, kata_counts = await proses_rekap(chat, katas, start, now)

    hasil = await format_hasil(
        "📊 REKAP HARI INI",
        now.strftime("%d %B %Y"),
        katas,
        user_counts,
        kata_counts
    )

    await event.reply(hasil)

# ================= REKAP KEMARIN =================

@client.on(events.NewMessage(pattern=r'^/rekapkata1(?:\s+(.+))?$'))
async def rekap1(event):

    data = await ambil_kata(event)
    if not data:
        return

    args, katas = data
    chat = await ambil_chat(event, args)

    wib = timezone(timedelta(hours=7))
    now = datetime.now(wib)

    start = datetime(now.year, now.month, now.day, tzinfo=wib) - timedelta(days=1)
    end = datetime(now.year, now.month, now.day, tzinfo=wib)

    user_counts, kata_counts = await proses_rekap(chat, katas, start, end)

    hasil = await format_hasil(
        "📊 REKAP KEMARIN",
        (now - timedelta(days=1)).strftime("%d %B %Y"),
        katas,
        user_counts,
        kata_counts
    )

    await event.reply(hasil)

# ================= REKAP 7 HARI =================

@client.on(events.NewMessage(pattern=r'^/rekapkata7(?:\s+(.+))?$'))
async def rekap7(event):

    data = await ambil_kata(event)
    if not data:
        return

    args, katas = data
    chat = await ambil_chat(event, args)

    wib = timezone(timedelta(hours=7))
    now = datetime.now(wib)

    start = now - timedelta(days=6)

    user_counts, kata_counts = await proses_rekap(chat, katas, start, now)

    hasil = await format_hasil(
        "📊 REKAP 7 HARI",
        now.strftime("%d %B %Y"),
        katas,
        user_counts,
        kata_counts
    )

    await event.reply(hasil)

# ================= START BOT =================

async def main():
    await client.start()
    print("BOT AKTIF")
    await client.run_until_disconnected()

if __name__ == "__main__":
    Thread(target=run_web).start()
    client.loop.run_until_complete(main())
