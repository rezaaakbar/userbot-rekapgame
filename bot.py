import os
import time
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from pymongo import MongoClient

logging.basicConfig(level=logging.INFO)

# ================= CONFIG =================

TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

OWNER_ID = 6818257079
OWNER_USERNAME = "@KINGZAAASLI"

client = MongoClient(MONGO_URI)
db = client["telegram_bot"]

# 🔥 BOT KE-2 (TEST DB)
groups_col = db["groups_test"]

pending_sewa = {}

# ================= RESPONSE =================

RESP = {
    "adduser": "𝗨𝗦𝗘𝗥 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡 𝗞𝗘𝗟𝗜𝗦𝗧✅",
    "deluser": "𝗨𝗦𝗘𝗥 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗛𝗔𝗣𝗨𝗦 𝗗𝗔𝗥𝗜 𝗟𝗜𝗦𝗧✅",
    "add": "𝗧𝗔𝗥𝗚𝗘𝗧 𝗕𝗘𝗥𝗛𝗔𝗦𝗜𝗟 𝗗𝗜 𝗧𝗔𝗠𝗕𝗔𝗛𝗞𝗔𝗡 𝗞𝗘𝗟𝗜𝗦𝗧✅",
    "delete_on": "𝗢𝗧𝗪 𝗞𝗘𝗥𝗝𝗔 𝗕𝗢𝗦🚀",
    "delete_off": "𝗗𝗔𝗛 𝗕𝗘𝗥𝗛𝗘𝗡𝗧𝗜 𝗕𝗢𝗦𝗦🥰",
}

# ================= DB =================

def get_group(chat_id):
    g = groups_col.find_one({"chat_id": str(chat_id)})

    if not g:
        g = {
            "chat_id": str(chat_id),
            "allowed_users": {},
            "targets": {},
            "delete_on": False,
            "premium_users": {}
        }
        groups_col.insert_one(g)

    return g


def save_group(g):
    groups_col.update_one(
        {"chat_id": g["chat_id"]},
        {"$set": g}
    )


def is_allowed(uid, g):
    return uid == OWNER_ID or str(uid) in g.get("allowed_users", {})


async def reject(msg):
    await msg.reply_text(
        f"𝗟𝗔𝗨 𝗦𝗜𝗔𝗣𝗘 𝗠𝗣𝗥𝗨𝗬? 𝗠𝗜𝗡𝗧𝗔 𝗜𝗭𝗜𝗡 𝗦𝗔𝗠𝗔 {OWNER_USERNAME}"
    )

# ================= ADD USER =================

async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    g = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, g):
        return await reject(msg)

    if not msg.reply_to_message:
        return await msg.reply_text("Reply user dulu")

    uid = str(msg.reply_to_message.from_user.id)
    name = context.args[0].lower()

    g["allowed_users"][uid] = name
    save_group(g)

    await msg.reply_text(RESP["adduser"])

# ================= DEL USER =================

async def deluser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if msg.chat.type != "private":
        return await msg.reply_text("PRIVATE ONLY")

    if msg.from_user.id != OWNER_ID:
        return await msg.reply_text("KHUSUS OWNER")

    if not context.args:
        return await msg.reply_text("Contoh: /deluser nama")

    name = context.args[0].lower()

    for g in groups_col.find():
        for uid, uname in list(g.get("allowed_users", {}).items()):
            if uname == name:
                del g["allowed_users"][uid]
                save_group(g)
                return await msg.reply_text(RESP["deluser"])

    await msg.reply_text("USER TIDAK DITEMUKAN")

# ================= LIST USER =================

async def listuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    text = "𝐋𝐈𝐒𝐓 𝐔𝐒𝐄𝐑:\n\n"

    for g in groups_col.find():
        for uid, name in g.get("allowed_users", {}).items():
            text += f"{name}\n{uid}\n{g['chat_id']}\n\n"

    await msg.reply_text(text)

# ================= ADD TARGET =================

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    g = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, g):
        return await reject(msg)

    if not msg.reply_to_message:
        return await msg.reply_text("Reply target dulu")

    uid = str(msg.reply_to_message.from_user.id)
    name = context.args[0].lower()

    g["targets"][uid] = name
    save_group(g)

    await msg.reply_text(RESP["add"])

# ================= DELETE PESAN =================

async def deletepesan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    g = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, g):
        return await reject(msg)

    if not context.args:
        return await msg.reply_text("Contoh: /deletepesan on/off")

    mode = context.args[0].lower()

    if mode == "on":
        g["delete_on"] = True
        save_group(g)
        return await msg.reply_text(RESP["delete_on"])

    elif mode == "off":
        g["delete_on"] = False
        save_group(g)
        return await msg.reply_text(RESP["delete_off"])

# ================= AUTO DELETE =================

async def auto_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        msg = update.message

        if not msg or msg.chat.type == "private":
            return

        g = get_group(msg.chat.id)

        if not g.get("delete_on"):
            return

        uid = str(msg.from_user.id)

        if uid in g.get("targets", {}):
            await msg.delete()

    except:
        pass

# ================= SEWA SYSTEM =================

async def sewabot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if msg.chat.type == "private":
        return await msg.reply_text("GUNAKAN DI GRUP")

    user = msg.from_user

    pending_sewa[user.id] = {
        "name": user.first_name,
        "user_id": str(user.id),
        "group_id": str(msg.chat.id),
    }

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("TERIMA", callback_data=f"accept_{user.id}"),
            InlineKeyboardButton("TOLAK", callback_data=f"reject_{user.id}")
        ]
    ])

    await context.bot.send_message(
        chat_id=OWNER_ID,
        text=(
            f"📥 SEWA MASUK\n\n"
            f"NAMA: {user.first_name}\n"
            f"USERID: {user.id}\n"
            f"GRUP: {msg.chat.id}"
        ),
        reply_markup=keyboard
    )

    await msg.reply_text("SEWA DIKIRIM KE OWNER")

# ================= CALLBACK =================

async def callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.from_user.id != OWNER_ID:
        return

    data = query.data

    if data.startswith("accept_"):
        uid = int(data.split("_")[1])

        if uid not in pending_sewa:
            return await query.edit_message_text("DATA TIDAK ADA")

        context.user_data["waiting_days"] = uid

        await query.edit_message_text("KIRIM JUMLAH HARI AKTIF")

    elif data.startswith("reject_"):
        uid = int(data.split("_")[1])

        if uid in pending_sewa:
            del pending_sewa[uid]

        await query.edit_message_text("DITOLAK")

# ================= SET DAYS =================

async def set_days(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if msg.chat.type != "private":
        return

    if msg.from_user.id != OWNER_ID:
        return

    if "waiting_days" not in context.user_data:
        return

    if not msg.text.isdigit():
        return await msg.reply_text("HARUS ANGKA")

    days = int(msg.text)
    uid = context.user_data["waiting_days"]

    if uid not in pending_sewa:
        return await msg.reply_text("DATA HILANG")

    data = pending_sewa[uid]
    g = get_group(data["group_id"])

    g["premium_users"][data["user_id"]] = {
        "name": data["name"],
        "expire": time.time() + (days * 86400)
    }

    g["allowed_users"][data["user_id"]] = data["name"]

    save_group(g)

    del pending_sewa[uid]
    del context.user_data["waiting_days"]

    await msg.reply_text("BERHASIL MASUK PREMIUM")

# ================= MAIN =================

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("adduser", adduser))
app.add_handler(CommandHandler("deluser", deluser))
app.add_handler(CommandHandler("listuser", listuser))

app.add_handler(CommandHandler("add", add))
app.add_handler(CommandHandler("deletepesan", deletepesan))
app.add_handler(CommandHandler("sewabot", sewabot))

app.add_handler(CallbackQueryHandler(callback))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, set_days))
app.add_handler(MessageHandler(~filters.COMMAND, auto_delete))

print("BOT TEST RUNNING...")
app.run_polling(drop_pending_updates=True)
