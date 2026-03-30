from telethon import TelegramClient, events
from telethon.sessions import StringSession
import os

api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")

STRING_SESSION = "1BVtsOKIBuyqNkrXEyCQQAV8D7Wl90FdQ2erfqhVR6Od-M7J8vxkLV7rbCo9YU154ZzLVSv8TBuQT6d2JQTtsiAyyKxDn5aZKOp7H8KBbvHFe9HhvPngg9nzMCdoiWffmJunXboRcMZlZv8_rAymJdgLK55NAhMbrZsmGITfENzRcC2IP20XL4sbS7LbhwTqEs6peuTtb9LB6doJfRdrT8klR2iLFGhiwSHLeup80siwqb0m-PuvfisqrUcsclHKWYPYvntqa-TT0ePNfGIyRA5syT9GEzPOHwHmkHivOWiFDmDuQuZW8AvoC9eQyTvwDAPppb7GN1jvuppq3J2MOeY-tTWMyNLo="

client = TelegramClient(StringSession(STRING_SESSION), api_id, api_hash)


@client.on(events.NewMessage(pattern=r"/itungkata"))
async def hitung(event):

    args = event.raw_text.split()

    if len(args) < 2:
        await event.reply("Format:\n/itungkata kata")
        return

    kata = args[1].lower()

    await event.reply("Menghitung pesan...")

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


client.start()
client.run_until_disconnected()
