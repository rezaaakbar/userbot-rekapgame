import os
import asyncio
import pytz
from telethon import TelegramClient
from telethon.sessions import StringSession

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
session = os.getenv("SESSION")

client = TelegramClient(StringSession(session), api_id, api_hash)

# penyimpanan hitungan sementara
user_messages = {}

# zona waktu WIB
wib = pytz.timezone("Asia/Jakarta")

# reset setiap 00:00
async def reset_loop():
    global user_messages
    while True:
        now = datetime.now(wib)
        if now.hour == 0 and now.minute == 0:
            user_messages = {}
            print("RESET DATA HARIAN")
            await asyncio.sleep(60)
        await asyncio.sleep(10)

@client.on(events.NewMessage)
async def handler(event):
    if event.message.text.startswith("/"):
        return

    sender = await event.get_sender()
    user_id = sender.id

    if user_id not in user_messages:
        user_messages[user_id] = 0

    user_messages[user_id] += 1

@client.on(events.MessageDeleted)
async def deleted(event):
    # pesan dihapus tidak dihitung
    pass

@client.on(events.NewMessage(pattern="/rank"))
async def rank(event):
    text = "📊 Ranking Pesan Hari Ini\n\n"

    sorted_users = sorted(user_messages.items(), key=lambda x: x[1], reverse=True)

    for i, (user, count) in enumerate(sorted_users[:10], 1):
        text += f"{i}. {user} - {count} pesan\n"

    await event.reply(text)

# web server supaya render tidak mati
app = Flask("")

@app.route("/")
def home():
    return "Bot aktif"

def run():
    app.run(host="0.0.0.0", port=10000)

def keep_alive():
    t = threading.Thread(target=run)
    t.start()

async def main():
    keep_alive()
    asyncio.create_task(reset_loop())
    await client.start()
    print("Userbot aktif")
    await client.run_until_disconnected()

with client:
    client.loop.run_until_complete(main())
