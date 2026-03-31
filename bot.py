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

@client.on(events.NewMessage(pattern=r"/rekapkata (.+)"))
async def rekap(event):

    args = event.pattern_match.group(1).split()

    kata = args[0].lower()

    if len(args) >= 2:
        chat_id = int(args[1])
    else:
        chat_id = event.chat_id

    # ===== jika dipakai di privat =====
    if not event.is_group:

        if len(args) < 2:
            await event.reply("Contoh:\n/rekapkata kata -100IDGRUP")
            return

        group_id = int(args[1])
        chat = await client.get_entity(group_id)

    else:
        chat = await event.get_chat()

    wib = timezone(timedelta(hours=7))
    now = datetime.now(wib)
    start_day = datetime(now.year, now.month, now.day, tzinfo=wib)

    counts = defaultdict(int)

    async for msg in client.iter_messages(chat):

        if msg.date < start_day:
            break

        if msg.text and msg.text.startswith("/"):
            continue

        if kata not in msg.text.lower():
            continue

        if msg.sender_id:
            counts[msg.sender_id] += 1

    today = datetime.now(wib).strftime("%d %B %Y")

    text = (
        "📊𝗝𝗨𝗠𝗟𝗔𝗛 𝗣𝗘𝗦𝗔𝗡 𝗛𝗔𝗥𝗜 𝗜𝗡𝗜\n"
        f"🗓️ {today}\n\n"
        f"📝𝗣𝗘𝗦𝗔𝗡 𝗬𝗚 𝗗𝗜 𝗖𝗔𝗥𝗜: {kata}\n\n"
        "👤𝗨𝗦𝗘𝗥 𝗬𝗚 𝗠𝗘𝗡𝗚𝗜𝗥𝗜𝗠:\n\n"
    )

    total = 0

    for uid, jumlah in counts.items():

        try:
            user = await client.get_entity(uid)
            username = f"@{user.username}" if user.username else user.first_name
        except:
            username = "user"

        text += f"{username} : {jumlah}\n"
        total += jumlah

    text += f"\n🏆𝗧𝗢𝗧𝗔𝗟: {total}"

    await event.reply(text)
    
# ================= REKAP7 =================

@client.on(events.NewMessage(pattern=r"/rekapkata7"))
async def rekapkata7(event):

    args = event.raw_text.split()

    if len(args) < 2:
        await event.reply("Contoh:\n/rekapkata7 kata\natau\n/rekapkata7 kata -100idgrup")
        return

    kata = args[1].lower()

    chat_id = event.chat_id

    # jika dipakai di privat
    if not event.is_group:
        if len(args) < 3:
            await event.reply("Kirim: /rekapkata7 kata -100idgrup")
            return

        group_id = int(args[2])
        chat = await client.get_entity(group_id)
    else:
        chat = await event.get_chat()

    wib = timezone(timedelta(hours=7))
    now = datetime.now(wib)

    start_day = now - timedelta(days=7)

    counts = defaultdict(int)

    async for msg in client.iter_messages(chat):

        if msg.date < start_day:
            break

        if msg.text and msg.text.startswith("/"):
            continue

        if not msg.text:
            continue

        if kata not in msg.text.lower():
            continue

        if msg.sender_id:
            counts[msg.sender_id] += 1

    start_text = start_day.strftime("%d %B %Y")
end_text = now.strftime("%d %B %Y")

    text = (
        f"📊 JUMLAH PESAN 7 HARI TERAKHIR\n"
        f"📅 {start_text} - {end_text}\n\n"
        f"📝 PESAN YG DI CARI: {kata}\n\n"
        f"👤 USER YG MENGIRIM:\n\n"
    )

    total = 0

    for user_id, jumlah in sorted(counts.items(), key=lambda x: x[1], reverse=True):

        user = await client.get_entity(user_id)

        username = f"@{user.username}" if user.username else user.first_name

        text += f"{username} : {jumlah}\n"

        total += jumlah

    text += f"\n🏆 TOTAL: {total}"

    await event.reply(text)
# ================= MAIN =================

async def main():
    await client.start()
    print("BOT TELEGRAM AKTIF")
    await client.run_until_disconnected()

if __name__ == "__main__":

    Thread(target=run_web).start()

    client.loop.run_until_complete(main())
