import telebot
import json
import os
from datetime import datetime, timedelta

TOKEN = "ISI_TOKEN_BOT_KAMU"
bot = telebot.TeleBot(TOKEN)

DATA_FILE = "data.json"

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

data = load_data()


# ==============================
# SIMPAN PESAN
# ==============================

@bot.message_handler(func=lambda message: True)
def handle_message(message):

    if not message.text:
        return

    # ❗ Abaikan command
    if message.text.startswith("/"):
        return

    chat_id = str(message.chat.id)
    user = message.from_user.username

    if not user:
        user = message.from_user.first_name

    text = message.text.lower()
    date = datetime.now().strftime("%Y-%m-%d")

    words = text.split()

    if chat_id not in data:
        data[chat_id] = {}

    if date not in data[chat_id]:
        data[chat_id][date] = {}

    for word in words:

        if word not in data[chat_id][date]:
            data[chat_id][date][word] = {}

        if user not in data[chat_id][date][word]:
            data[chat_id][date][word][user] = 0

        data[chat_id][date][word][user] += 1

    save_data(data)


# ==============================
# REKAP HARI INI
# ==============================

@bot.message_handler(commands=["rekapkata"])
def rekap_kata(message):

    args = message.text.split()

    if len(args) < 2:
        bot.reply_to(message, "contoh: /rekapkata anjay")
        return

    kata = args[1].lower()

    if len(args) == 3:
        chat_id = args[2]
    else:
        chat_id = str(message.chat.id)

    today = datetime.now().strftime("%Y-%m-%d")

    result = {}

    if chat_id in data and today in data[chat_id]:

        if kata in data[chat_id][today]:

            for user, jumlah in data[chat_id][today][kata].items():
                result[user] = jumlah

    total = sum(result.values())

    text = "📊𝗝𝗨𝗠𝗟𝗔𝗛 𝗣𝗘𝗦𝗔𝗡 𝗛𝗔𝗥𝗜 𝗜𝗡𝗜\n"
    text += f"🗓️ {today}\n\n"

    text += f"📝𝗣𝗘𝗦𝗔𝗡 𝗬𝗚 𝗗𝗜 𝗖𝗔𝗥𝗜: {kata}\n\n"

    text += "𝗨𝗦𝗘𝗥 𝗬𝗚 𝗠𝗘𝗡𝗚𝗜𝗥𝗜𝗠:\n"

    for user, jumlah in result.items():
        text += f"@{user} : {jumlah}\n"

    text += f"\n🏆𝗧𝗢𝗧𝗔𝗟: {total}"

    bot.reply_to(message, text)


# ==============================
# REKAP 7 HARI
# ==============================

@bot.message_handler(commands=["rekapkata7"])
def rekap_kata7(message):

    args = message.text.split()

    if len(args) < 2:
        bot.reply_to(message, "contoh: /rekapkata7 anjay")
        return

    kata = args[1].lower()

    if len(args) == 3:
        chat_id = args[2]
    else:
        chat_id = str(message.chat.id)

    today = datetime.now()

    result = {}

    for i in range(7):

        date = (today - timedelta(days=i)).strftime("%Y-%m-%d")

        if chat_id in data and date in data[chat_id]:

            if kata in data[chat_id][date]:

                for user, jumlah in data[chat_id][date][kata].items():

                    if user not in result:
                        result[user] = 0

                    result[user] += jumlah

    total = sum(result.values())

    start = (today - timedelta(days=6)).strftime("%Y-%m-%d")
    end = today.strftime("%Y-%m-%d")

    text = "📊𝗥𝗘𝗞𝗔𝗣 𝗞𝗔𝗧𝗔 𝟳 𝗛𝗔𝗥𝗜\n"
    text += f"🗓️ {start} s/d {end}\n\n"

    text += f"📝𝗣𝗘𝗦𝗔𝗡 𝗬𝗚 𝗗𝗜 𝗖𝗔𝗥𝗜: {kata}\n\n"

    text += "𝗨𝗦𝗘𝗥 𝗬𝗚 𝗠𝗘𝗡𝗚𝗜𝗥𝗜𝗠:\n"

    for user, jumlah in result.items():
        text += f"@{user} : {jumlah}\n"

    text += f"\n🏆𝗧𝗢𝗧𝗔𝗟: {total}"

    bot.reply_to(message, text)


# ==============================
# START
# ==============================

@bot.message_handler(commands=["start"])
def start(message):
    bot.reply_to(message, "Bot Rekap Kata Aktif.")


print("BOT AKTIF...")
bot.infinity_polling()
