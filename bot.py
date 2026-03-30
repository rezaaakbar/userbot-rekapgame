from telethon import TelegramClient, events
from datetime import datetime, timedelta, timezone

# ================= API =================
api_id = 35841167
api_hash = "1ed1822dd3d2c98da0b56d6a890e48d3"

client = TelegramClient("session", api_id, api_hash)

# ================= WIB =================
WIB = timezone(timedelta(hours=7))

# ================= COMMAND =================
@client.on(events.NewMessage(pattern=r'^/itungkata (.+)'))
async def handler(event):

    args = event.pattern_match.group(1).split()

    # kata yang dihitung
    keyword = args[0].lower()

    # jika ada id grup
    if len(args) > 1:
        chat = int(args[1])
    else:
        chat = await event.get_chat()

    counts = {}
    total = 0
    today = datetime.now(WIB).date()

    async for msg in client.iter_messages(chat, limit=5000):

        if not msg.text:
            continue

        msg_date = msg.date.astimezone(WIB).date()

        if msg_date != today:
            continue

        text = msg.text.lower()
        jumlah = text.count(keyword)

        if jumlah > 0:
            sender = await msg.get_sender()

            if sender.username:
                name = f"@{sender.username}"
            else:
                name = sender.first_name

            counts[name] = counts.get(name, 0) + jumlah
            total += jumlah

    if total == 0:
        await event.reply("❌ kata tidak ditemukan hari ini")
        return

    result = f"📊 Statistik kata **{keyword}** hari ini\n\n"

    for user, j in sorted(counts.items(), key=lambda x: x[1], reverse=True):
        result += f"{user} = {j}\n"

    result += f"\nTOTAL = {total}"

    await event.reply(result)


print("Bot berjalan...")
client.start()
client.run_until_disconnected()
