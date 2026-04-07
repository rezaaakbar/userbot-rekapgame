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
    return "BOT REKAP + NABUNG AKTIF"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# ================= FUNGSI AMBIL PIN =================

async def ambil_pin(chat_id):

    try:

        chat = await client.get_entity(chat_id)

        if not getattr(chat, "pinned_msg_id", None):
            return None

        msg = await client.get_messages(chat_id, ids=chat.pinned_msg_id)

        return msg

    except Exception as e:

        print("PIN ERROR:", e)

        return None

# ================= REKAP SYSTEM =================

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

        text = msg.text.lower()

        if text.startswith("/"):
            continue

        for kata in kata_list:

            if kata.lower() in text:

                counts[kata][msg.sender_id] += 1

    return counts


async def format_hasil(counts):

    hasil = ""

    for kata in counts:

        hasil += f"\n🔥 <b>KATA: {kata.upper()}</b>\n"

        nomor = 1

        total = 0

        for uid, jumlah in sorted(counts[kata].items(), key=lambda x: x[1], reverse=True):

            try:

                user = await client.get_entity(uid)

                name = f"@{user.username}" if user.username else user.first_name

            except:

                name = "user"

            hasil += f"┣ {nomor}. <b>{name}</b> : <code>{jumlah}</code>\n"

            nomor += 1

            total += jumlah

        hasil += f"┗ 📊 <b>TOTAL:</b> <code>{total}</code>\n"

    return hasil

# ================= REKAP COMMAND =================

@client.on(events.NewMessage(pattern=r'^/rekapkata'))
async def rekap_hari_ini(event):

    text = event.raw_text.replace("/rekapkata", "").strip()

    if not text:

        await event.reply("Format: /rekapkata kata1 kata2 (IDGRUP)")

        return

    chat, kata_list = await ambil_chat_dan_kata(event, text)

    wib = timezone(timedelta(hours=7))

    now = datetime.now(wib)

    start = datetime(now.year, now.month, now.day, tzinfo=wib)

    counts = await proses_rekap(chat, kata_list, start, now)

    hasil = await format_hasil(counts)

    await event.reply("📊 <b>JUMLAH PESAN HARI INI</b>\n\n" + hasil)


@client.on(events.NewMessage(pattern=r'^/rekapkata1'))
async def rekap_kemarin(event):

    text = event.raw_text.replace("/rekapkata1", "").strip()

    if not text:

        await event.reply("Format: /rekapkata1 kata1 kata2")

        return

    chat, kata_list = await ambil_chat_dan_kata(event, text)

    wib = timezone(timedelta(hours=7))

    now = datetime.now(wib)

    start = datetime(now.year, now.month, now.day, tzinfo=wib) - timedelta(days=1)

    end = datetime(now.year, now.month, now.day, tzinfo=wib)

    counts = await proses_rekap(chat, kata_list, start, end)

    hasil = await format_hasil(counts)

    await event.reply("📊 <b>JUMLAH PESAN KEMARIN</b>\n\n" + hasil)


# ================= NABUNG SYSTEM =================

def tambah_data(text, nama, jumlah):

    lines = text.split("\n")

    hasil = []

    ditemukan = False

    for line in lines:

        if line.lower().startswith(nama.lower() + ":"):

            ditemukan = True

            line = line + f"{jumlah},"

        hasil.append(line)

    if not ditemukan:

        hasil.append(f"{nama}:{jumlah},")

    return "\n".join(hasil)


@client.on(events.NewMessage(pattern=r'^/tambah'))
async def tambah(event):

    if not event.is_group:

        await event.reply("❌ Command hanya di grup")

        return

    args = event.raw_text.split()

    if len(args) < 3:

        await event.reply("Format:\n/tambah nama jumlah")

        return

    nama = args[1]

    try:

        jumlah = int(args[2])

    except:

        await event.reply("Jumlah harus angka")

        return

    pin = await ambil_pin(event.chat_id)

    if not pin:

        await event.reply("❌ Pesan PIN tidak ditemukan")

        return

    text = pin.text or ""

    text_baru = tambah_data(text, nama, jumlah)

    await client.edit_message(event.chat_id, pin.id, text_baru)

    await event.reply("✅ Data ditambahkan")


@client.on(events.NewMessage(pattern=r'^/total'))
async def total(event):

    if not event.is_group:

        await event.reply("❌ Command hanya di grup")

        return

    pin = await ambil_pin(event.chat_id)

    if not pin:

        await event.reply("❌ PIN tidak ditemukan")

        return

    angka = re.findall(r'-?\d+', pin.text)

    total = sum(map(int, angka))

    await event.reply(f"💰 TOTAL: {total}")

# ================= START BOT =================

def start_bot():

    print("BOT STARTING...")

    client.start()

    print("BOT AKTIF")

    client.run_until_disconnected()

# ================= MAIN =================

if __name__ == "__main__":

    Thread(target=run_web).start()

    start_bot()
