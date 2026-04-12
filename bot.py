import os
import re
import asyncio
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from flask import Flask
from threading import Thread
import traceback

# ================= ENV SAFE =================
API_ID = os.getenv("API_ID")
API_HASH = os.getenv("API_HASH")
SESSION = os.getenv("SESSION")

if not API_ID or not API_HASH or not SESSION:
    print("❌ ENV belum lengkap!")
    exit()

API_ID = int(API_ID)

client = TelegramClient(
    StringSession(SESSION),
    API_ID,
    API_HASH,
    auto_reconnect=True,
    connection_retries=5
)

client.parse_mode = "html"

# ================= WEB =================
app = Flask(__name__)

@app.route("/")
def home():
    return "BOT AKTIF"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ================= HELPER =================
async def hapus_pesan(chat_id, msg_id, delay=2):
    await asyncio.sleep(delay)
    try:
        await client.delete_messages(chat_id, msg_id)
    except:
        pass

async def balas_sukses(event, text):
    try:
        msg = await event.reply(f"<b>{text}</b>")
        asyncio.create_task(hapus_pesan(event.chat_id, msg.id))
        await event.delete()
    except:
        pass

# ================= PINNED / REPLY =================
async def get_target_message(event):
    if event.is_reply:
        return await event.get_reply_message()

    try:
        return await client.get_pinned_message(event.chat_id)
    except:
        return None

# ================= AMBIL CHAT =================
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


# ================= REKAP CORE =================
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


# ================= /REKAPKATA HARI INI =================
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
    list_user = await format_hasil_kata(counts)

    hasil = f"📊 JUMLAH PESAN HARI INI\n📅 {now.strftime('%d-%m-%Y')}\n\n"
    hasil += f"📝 PESAN DICARI: {', '.join(kata_list)}\n"
    hasil += list_user

    await event.reply(hasil)


# ================= /REKAPKATA1 (KEMARIN) =================
@client.on(events.NewMessage(pattern=r'^/rekapkata1(?:\s+(.+))?$'))
async def rekap_kemarin(event):
    if not event.pattern_match.group(1):
        await event.reply("Format: /rekapkata1 kata1 kata2")
        return

    text = event.pattern_match.group(1)
    chat, kata_list = await ambil_chat_dan_kata(event, text)

    wib = timezone(timedelta(hours=7))
    now = datetime.now(wib)

    start = datetime(now.year, now.month, now.day, tzinfo=wib) - timedelta(days=1)
    end = datetime(now.year, now.month, now.day, tzinfo=wib)

    counts = await proses_rekap(chat, kata_list, start, end)
    list_user = await format_hasil_kata(counts)

    hasil = f"📊 JUMLAH PESAN KEMARIN\n📅 {(now - timedelta(days=1)).strftime('%d-%m-%Y')}\n\n"
    hasil += f"📝 PESAN DICARI: {', '.join(kata_list)}\n"
    hasil += list_user

    await event.reply(hasil)


# ================= /REKAPKATA7 (7 HARI) =================
@client.on(events.NewMessage(pattern=r'^/rekapkata7(?:\s+(.+))?$'))
async def rekap7(event):
    if not event.pattern_match.group(1):
        await event.reply("Format: /rekapkata7 kata1 kata2")
        return

    text = event.pattern_match.group(1)
    chat, kata_list = await ambil_chat_dan_kata(event, text)

    wib = timezone(timedelta(hours=7))
    now = datetime.now(wib)

    start = now - timedelta(days=6)

    counts = await proses_rekap(chat, kata_list, start, now)
    list_user = await format_hasil_kata(counts)

    hasil = f"📊 JUMLAH PESAN 7 HARI\n📅 {start.strftime('%d-%m-%Y')} s/d {now.strftime('%d-%m-%Y')}\n\n"
    hasil += f"📝 PESAN DICARI: {', '.join(kata_list)}\n"
    hasil += list_user

    await event.reply(hasil)


# ================= NABUNG (REPLY + PINNED) =================
@client.on(events.NewMessage(pattern=r'^/tambah\s+'))
async def tambah(event):
    msg_target = await get_target_message(event)
    if not msg_target:
        return

    args = event.raw_text.split()
    try:
        jumlah = int(args[-1])
    except:
        return

    nama = " ".join(args[1:-1]).lower()
    lines = (msg_target.text or "").split("\n")

    hasil = []
    bagian = "pemasukan"

    for line in lines:
        if "pengeluaran" in line.lower():
            bagian = "pengeluaran"

        if line.lower().startswith(nama + ":"):
            value = jumlah if bagian != "pengeluaran" else -abs(jumlah)
            line = line.strip() + f"{value},"

        hasil.append(line)

    await client.edit_message(event.chat_id, msg_target.id, "\n".join(hasil))
    await balas_sukses(event, "BERHASIL DI TAMBAH✅")


@client.on(events.NewMessage(pattern=r'^/tambahlist\s+'))
async def tambahlist(event):
    msg_target = await get_target_message(event)
    if not msg_target:
        return

    args = event.raw_text.split()
    if len(args) < 4:
        return

    bagian = args[1].lower()
    nama = " ".join(args[2:-1])

    try:
        jumlah = int(args[-1])
    except:
        return

    if bagian == "pengeluaran":
        jumlah = -abs(jumlah)

    lines = (msg_target.text or "").split("\n")

    hasil = []
    inserted = False

    for line in lines:
        hasil.append(line)

        if bagian in line.lower() and not inserted:
            hasil.append(f"{nama}:{jumlah},")
            inserted = True

    await client.edit_message(event.chat_id, msg_target.id, "\n".join(hasil))
    await balas_sukses(event, "BERHASIL DI TAMBAHLIST✅")


# ================= TOTAL =================
@client.on(events.NewMessage(pattern=r'^/total'))
async def total(event):
    if not event.is_reply:
        return

    reply = await event.get_reply_message()

    lines = (reply.text or "").split("\n")
    angka = re.findall(r'-?\d+', reply.text or "")
    total = sum(map(int, angka))

    hasil = []
    updated = False

    for line in lines:
        if "total:" in line.lower():
            line = f"📊 TOTAL: {total}"
            updated = True
        hasil.append(line)

    # kalau tidak ada TOTAL: tambahkan di bawah
    if not updated:
        hasil.append(f"📊 TOTAL: {total}")

    await client.edit_message(event.chat_id, reply.id, "\n".join(hasil))

    await event.delete()


# ================= START =================
async def start_bot():
    while True:
        try:
            print("🚀 BOT START")
            await client.start()
            await client.run_until_disconnected()
        except:
            traceback.print_exc()
            await asyncio.sleep(5)


if __name__ == "__main__":
    Thread(target=run_web, daemon=True).start()
    client.loop.run_until_complete(start_bot())
