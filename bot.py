import os
import asyncio
from telethon import TelegramClient, events
from telethon.sessions import StringSession

# ambil env
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
session = os.getenv("SESSION")

# buat event loop (fix python 3.14)
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# client
client = TelegramClient(StringSession(session), api_id, api_hash)

# penyimpanan pesan
data = {}

@client.on(events.NewMessage)
async def count(event):

    if event.text.startswith("/"):
        return

    uid = event.sender_id

    if uid not in data:
        data[uid] = 0

    data[uid] += 1


@client.on(events.NewMessage(pattern="/itungkata"))
async def cek(event):

    if not event.is_reply:
        await event.reply("reply pesan user")
        return

    msg = await event.get_reply_message()
    uid = msg.sender_id

    total = data.get(uid, 0)

    await event.reply(f"total pesan hari ini: {total}")


async def main():
    await client.start()
    print("BOT AKTIF")
    await client.run_until_disconnected()

loop.run_until_complete(main())
