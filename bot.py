import os
import pytz
from datetime import datetime
from telethon import TelegramClient, events
from telethon.sessions import StringSession

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION = os.getenv("SESSION")

client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

wib = pytz.timezone("Asia/Jakarta")


async def hitung_pesan(chat_id, user_id):
    now = datetime.now(wib)

    start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    total = 0

    async for msg in client.iter_messages(chat_id):

        if msg.date.astimezone(wib) < start:
            break

        if msg.sender_id == user_id:
            total += 1

    return total


@client.on(events.NewMessage(pattern=r"/itungkata ?(.*)"))
async def handler(event):

    chat = await event.get_chat()

    target = event.pattern_match.group(1)

    if not target:

        await event.reply("contoh:\n/itungkata @username")
        return

    try:

        user = await client.get_entity(target)

    except:
        await event.reply("username tidak ditemukan")
        return

    total = await hitung_pesan(chat.id, user.id)

    await event.reply(
        f"""📊 HITUNG PESAN

User : {user.first_name}
Username : @{user.username}

Pesan hari ini :
{total}

⏰ dihitung dari 00:00 WIB"""
    )


print("BOT AKTIF...")

client.start()

client.run_until_disconnected()
