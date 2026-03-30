import os
import pytz
from datetime import datetime
from telethon import TelegramClient, events
from telethon.sessions import StringSession

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")
session = os.getenv("SESSION")

client = TelegramClient(StringSession(session), api_id, api_hash)

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
        await event.reply("reply pesan user")
        return

    msg = await event.get_reply_message()

    total = await hitung(event.chat_id, msg.sender_id)

    await event.reply(f"Total pesan hari ini: {total}")


print("BOT AKTIF")

client.start()
client.run_until_disconnected()
