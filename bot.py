from telethon import TelegramClient, events
from telethon.sessions import StringSession
import os
import json
import datetime
import asyncio

# ambil dari environment
api_id = int(os.getenv("API_ID"))
api_hash = os.getenv("API_HASH")

# session langsung di script
STRING_SESSION = "1BVtsOKIBuyqNkrXEyCQQAV8D7Wl90FdQ2erfqhVR6Od-M7J8vxkLV7rbCo9YU154ZzLVSv8TBuQT6d2JQTtsiAyyKxDn5aZKOp7H8KBbvHFe9HhvPngg9nzMCdoiWffmJunXboRcMZlZv8_rAymJdgLK55NAhMbrZsmGITfENzRcC2IP20XL4sbS7LbhwTqEs6peuTtb9LB6doJfRdrT8klR2iLFGhiwSHLeup80siwqb0m-PuvfisqrUcsclHKWYPYvntqa-TT0ePNfGIyRA5syT9GEzPOHwHmkHivOWiFDmDuQuZW8AvoC9eQyTvwDAPppb7GN1jvuppq3J2MOeY-tTWMyNLo="

client = TelegramClient(StringSession(STRING_SESSION), api_id, api_hash)

data_file = "data.json"

try:
    with open(data_file, "r") as f:
        data = json.load(f)
except:
    data = {}

target_word = None
target_group = None


@client.on(events.NewMessage(pattern="/itungkata"))
async def start_count(event):
    global target_word, target_group

    args = event.raw_text.split()

    if len(args) < 3:
        await event.reply("Format:\n/itungkata kata idgroup")
        return

    target_word = args[1].lower()
    target_group = int(args[2])

    await event.reply(f"✅ Menghitung kata **{target_word}** di grup {target_group}")


@client.on(events.NewMessage)
async def count_word(event):
    global target_word, target_group

    if target_word is None:
        return

    if event.chat_id != target_group:
        return

    if event.raw_text.lower() == target_word:

        user = str(event.sender_id)

        if user not in data:
            data[user] = 0

        data[user] += 1

        with open(data_file, "w") as f:
            json.dump(data, f)


@client.on(events.NewMessage(pattern="/top"))
async def ranking(event):

    if not data:
        await event.reply("Belum ada data.")
        return

    ranking = sorted(data.items(), key=lambda x: x[1], reverse=True)

    text = "🏆 Ranking Kata:\n\n"

    for i, (user, count) in enumerate(ranking[:10], start=1):
        text += f"{i}. {user} : {count}\n"

    await event.reply(text)


async def auto_reset():
    global data

    while True:

        now = datetime.datetime.utcnow() + datetime.timedelta(hours=7)

        if now.hour == 0 and now.minute == 0:
            data = {}

            with open(data_file, "w") as f:
                json.dump(data, f)

            print("Data di reset")
            await asyncio.sleep(60)

        await asyncio.sleep(10)


async def main():
    asyncio.create_task(auto_reset())
    await client.run_until_disconnected()


with client:
    client.loop.run_until_complete(main())
