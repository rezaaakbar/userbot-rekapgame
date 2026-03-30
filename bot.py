from telethon import TelegramClient, events
from telethon.sessions import StringSession
import os

# ambil dari environment variable
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
STRING_SESSION = os.getenv("STRING_SESSION")

client = TelegramClient(StringSession(STRING_SESSION), API_ID, API_HASH)


@client.on(events.NewMessage(pattern=r"/itungkata"))
async def hitung(event):

    args = event.raw_text.split()

    if len(args) < 2:
        await event.reply("Format:\n/itungkata kata")
        return

    kata = args[1].lower()

    await event.reply("🔎 Menghitung pesan...")

    total = 0
    ranking = {}

    async for msg in client.iter_messages(event.chat_id):

        if not msg.text:
            continue

        if msg.text.lower() == kata:

            user = msg.sender_id

            if user not in ranking:
                ranking[user] = 0

            ranking[user] += 1
            total += 1

    text = f"📊 Total kata '{kata}' : {total}\n\n"

    urut = sorted(ranking.items(), key=lambda x: x[1], reverse=True)

    for i, (user, jumlah) in enumerate(urut[:10], start=1):
        text += f"{i}. {user} : {jumlah}\n"

    await event.reply(text)


import asyncio

async def main():
    print("Bot berjalan...")
    await client.start()
    await client.run_until_disconnected()

asyncio.run(main())
