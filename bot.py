import os
import time
import logging
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from pymongo import MongoClient

# ================= CONFIG =================
TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

WEBHOOK_URL = "https://userbot-rekapgame-gq2v.onrender.com"

OWNER_ID = 6818257079
OWNER_USERNAME = "@KINGZAAASLI"

if not TOKEN or not MONGO_URI:
    print("❌ ENV belum lengkap!")
    exit()

logging.basicConfig(level=logging.INFO)

# ================= DB =================
client = MongoClient(MONGO_URI)
db = client["telegram_bot"]
col = db["groups"]

# ================= FLASK =================
app = Flask(__name__)

# ================= BOT =================
tg_app = ApplicationBuilder().token(TOKEN).build()

# ================= GROUP =================
def get_group(chat_id):
    g = col.find_one({"chat_id": str(chat_id)})
    if not g:
        g = {
            "chat_id": str(chat_id),
            "allowed_users": {},
            "targets": {},
            "delete_on": False
        }
        col.insert_one(g)
    return g

def save_group(g):
    col.update_one({"chat_id": g["chat_id"]}, {"$set": g})

def is_allowed(uid, g):
    return uid == OWNER_ID or str(uid) in g.get("allowed_users", {})

async def reject(msg):
    await msg.reply_text(f"𝗠𝗜𝗡𝗧𝗔 𝗜𝗭𝗜𝗡 𝗦𝗔𝗠𝗔 {OWNER_USERNAME}")

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("BOT WEBHOOK AKTIF ✅")

# ================= ADD TARGET =================
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    g = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, g):
        return await reject(msg)

    if not msg.reply_to_message:
        return await msg.reply_text("REPLY USER DULU")

    uid = str(msg.reply_to_message.from_user.id)
    name = context.args[0].lower()

    g["targets"][uid] = name
    save_group(g)

    await msg.reply_text("TARGET DITAMBAH")

# ================= DELETE TARGET =================
async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    g = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, g):
        return await reject(msg)

    name = context.args[0].lower()

    for uid, n in list(g["targets"].items()):
        if n == name:
            del g["targets"][uid]
            save_group(g)
            return await msg.reply_text("TARGET DIHAPUS")

# ================= ADD USER =================
async def adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    g = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, g):
        return await reject(msg)

    uid = str(msg.reply_to_message.from_user.id)
    name = context.args[0].lower()

    g["allowed_users"][uid] = name
    save_group(g)

    await msg.reply_text("USER DITAMBAH")

# ================= DEL USER (PRIVATE ONLY) =================
async def deluser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    if msg.chat.type != "private":
        return await msg.reply_text("PRIVATE ONLY")

    if msg.from_user.id != OWNER_ID:
        return await msg.reply_text("OWNER ONLY")

    name = context.args[0].lower()

    for g in col.find():
        for uid, n in list(g.get("allowed_users", {}).items()):
            if n == name:
                del g["allowed_users"][uid]
                save_group(g)
                return await msg.reply_text("USER DIHAPUS")

# ================= LIST USER =================
async def listuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message

    text = "📌 LIST USER:\n\n"
    for g in col.find():
        for uid, name in g.get("allowed_users", {}).items():
            text += f"{name} | {uid} | {g['chat_id']}\n"

    await msg.reply_text(text)

# ================= DELETE PESAN =================
async def deletepesan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    g = get_group(msg.chat.id)

    if not is_allowed(msg.from_user.id, g):
        return await reject(msg)

    if context.args[0] == "on":
        g["delete_on"] = True
    else:
        g["delete_on"] = False

    save_group(g)
    await msg.reply_text("UPDATE DELETE PESAN")

# ================= AUTO DELETE =================
async def auto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        msg = update.message
        if not msg or msg.chat.type == "private":
            return

        g = get_group(msg.chat.id)

        if g.get("delete_on") and str(msg.from_user.id) in g.get("targets", {}):
            await msg.delete()

    except:
        pass

# ================= REGISTER HANDLER =================
tg_app.add_handler(CommandHandler("start", start))
tg_app.add_handler(CommandHandler("add", add))
tg_app.add_handler(CommandHandler("delete", delete))
tg_app.add_handler(CommandHandler("adduser", adduser))
tg_app.add_handler(CommandHandler("deluser", deluser))
tg_app.add_handler(CommandHandler("listuser", listuser))
tg_app.add_handler(CommandHandler("deletepesan", deletepesan))
tg_app.add_handler(MessageHandler(~filters.COMMAND, auto))

# ================= WEBHOOK =================
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), tg_app.bot)
    tg_app.update_queue.put_nowait(update)
    return "ok"

@app.route("/")
def home():
    return "BOT RUNNING ✅"

# ================= SET WEBHOOK =================
async def set_webhook():
    bot = Bot(TOKEN)
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")

# ================= RUN =================
if __name__ == "__main__":
    import asyncio

    asyncio.get_event_loop().run_until_complete(set_webhook())

    print("FULL BOT WEBHOOK AKTIF")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
