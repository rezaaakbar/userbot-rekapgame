import os
import json
import pytz
import asyncio
from datetime import datetime
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from flask import Flask
from threading import Thread

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION = os.getenv("SESSION")

client = TelegramClient(StringSession(SESSION), API_ID, API_HASH)

wib = pytz.timezone("Asia/Jakarta")
DATA_FILE = "data.json"

app = Flask(name)

@app.route("/")
def home():
    return "Bot aktif"

def run_web():
port = int(os.environ.get("PORT", 10000))
app.run(host="0.0.0.0", port=port)

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

@client.on(events.NewMessage)
async def count_message(event):
if not event.is_group:
return

check_reset()
data = load_data()

user_id = str(event.sender_id)

if user_id not in data["users"]:
    data["users"][user_id] = 0

data["users"][user_id] += 1
save_data(data)

@client.on(events.NewMessage(pattern="/rekap"))
async def rekap(event):
data = load_data()

if not data["users"]:
    await event.reply("Belum ada pesan hari ini")
    return

text = "📊 Rekap Pesan Hari Ini\n\n"

for user_id, jumlah in data["users"].items():
    try:
        user = await client.get_entity(int(user_id))
        name = user.first_name
    except:
        name = "User"

    text += f"{name} : {jumlah} pesan\n"

await event.reply(text)

async def main():
await client.start()
print("USERBOT BERJALAN...")
await client.run_until_disconnected()

if name == "main":
Thread(target=run_web).start()
asyncio.run(main())
