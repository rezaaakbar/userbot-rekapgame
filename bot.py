import os
import json
import pytz
from datetime import datetime
from telethon import TelegramClient, events
from telethon.sessions import StringSession

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION = os.getenv("SESSION")

client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

wib = pytz.timezone("Asia/Jakarta")

DATA_FILE = "data.json"

# buat file kalau belum ada
if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({"date": "", "users": {}}, f)


def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)


def check_reset():
    data = load_data()
    today = datetime.now(wib).strftime("%Y-%m-%d")

    if data["date"] != today:
        data["date"] = today
        data["users"] = {}
        save_data(data)

check_reset()


@client.on(events.NewMessage)
async def count_message(event):
    if not event.is_group:
        return

    data = load_data()
    check_reset()

    user_id = str(event.sender_id)

    if user_id not in data["users"]:
        data["users"][user_id] = 0

    data["users"][user_id] += 1

    save_data(data)


@client.on(events.MessageDeleted)
async def minus_deleted(event):
    data = load_data()

    for msg_id in event.deleted_ids:
        # tidak bisa tahu siapa pengirimnya
        # jadi kita hanya mengurangi total global
        pass


@client.on(events.NewMessage(pattern="/rekap"))
async def rekap(event):

    if not event.is_group:
        return

    data = load_data()

    if not data["users"]:
        await event.reply("Belum ada pesan hari ini.")
        return

    text = "📊 Rekap Pesan Hari Ini\n\n"

    sorted_users = sorted(
        data["users"].items(),
        key=lambda x: x[1],
        reverse=True
    )

    for i, (user_id, total) in enumerate(sorted_users, start=1):
        try:
            user = await client.get_entity(int(user_id))
            name = user.first_name
        except:
            name = "User"

        text += f"{i}. {name} — {total} pesan\n"

    await event.reply(text)


import asyncio

async def main():
    await client.start()
    print("USERBOT BERJALAN...")
    await client.run_until_disconnected()

asyncio.run(main())
