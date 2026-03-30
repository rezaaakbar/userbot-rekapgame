import asyncio
import os
from telethon import TelegramClient, events
from dotenv import load_dotenv

# ambil data dari .env
load_dotenv()

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
phone = os.getenv("PHONE")

client = TelegramClient("session", api_id, api_hash)

kata_db = {}

@client.on(events.NewMessage)
async def handler(event):

    if not event.raw_text:
        return

    chat_id = event.chat_id
    text = event.raw_text.lower()

    if chat_id not in kata_db:
        kata_db[chat_id] = {}

    words = text.split()

    for w in words:
        kata_db[chat_id][w] = kata_db[chat_id].get(w, 0) + 1

    if text.startswith("/itungkata"):

        args = text.split()

        if len(args) < 2:
            await event.reply("contoh:\n/itungkata anjay")
            return

        word = args[1]

        jumlah = kata_db[chat_id].get(word, 0)

        await event.reply(
            f"📊 Kata '{word}' sudah dikirim\n"
            f"➡️ {jumlah} kali di grup ini"
        )


async def main():
    await client.start(phone)
    print("BOT AKTIF")
    await client.run_until_disconnected()

asyncio.run(main())
