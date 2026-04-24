import os
import logging
from telegram import Update, Bot
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from pymongo import MongoClient

# ================= LOG =================
logging.basicConfig(level=logging.INFO)

# ================= ENV =================
TOKEN = os.getenv("BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

# ================= SAFETY CHECK =================
if not TOKEN or not MONGO_URI:
    print("❌ ENV belum lengkap!")
    exit()

# ================= FORCE RESET WEBHOOK (ANTI CONFLICT) =================
bot = Bot(TOKEN)
bot.delete_webhook(drop_pending_updates=True)

# ================= DB =================
client = MongoClient(MONGO_URI)
db = client["telegram_bot"]
col = db["groups"]

# ================= SIMPLE GROUP GET =================
def get_group(chat_id):
    g = col.find_one({"chat_id": str(chat_id)})
    if not g:
        g = {
            "chat_id": str(chat_id),
            "delete_on": False,
            "targets": {}
        }
        col.insert_one(g)
    return g

def save_group(g):
    col.update_one({"chat_id": g["chat_id"]}, {"$set": g})

# ================= COMMAND =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("BOT AKTIF ✅")

async def deletepesan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    g = get_group(msg.chat.id)

    if not context.args:
        return await msg.reply_text("on/off")

    if context.args[0] == "on":
        g["delete_on"] = True
    else:
        g["delete_on"] = False

    save_group(g)
    await msg.reply_text("UPDATED")

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

# ================= APP =================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("deletepesan", deletepesan))
app.add_handler(MessageHandler(~filters.COMMAND, auto))

print("BOT RUNNING...")
app.run_polling(drop_pending_updates=True)
