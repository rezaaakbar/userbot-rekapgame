import asyncio
import os
from telethon import TelegramClient, events
from telethon.sessions import StringSession

try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION = os.getenv("SESSION")

client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)
wib = pytz.timezone("Asia/Jakarta")


async def hitung(chat_id, user_id):
    now = datetime.now(wib)
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    total = 0

    async for msg in client.iter_messages(chat_id):
        if msg.date.astimezone(wib) < start:
            break

        if msg.sender_id == user_id:
            total += 1

    return total


@client.on(events.NewMessage(pattern="/itungkata"))
async def handler(event):

    if not event.is_reply:
        await event.reply("Reply pesan user dulu.")
        return

    msg = await event.get_reply_message()

    total = await hitung(event.chat_id, msg.sender_id)

    await event.reply(f"Total pesan hari ini: {total}")


async def main():
    print("BOT AKTIF")
    await client.start()
    await client.run_until_disconnected()


asyncio.run(main())
