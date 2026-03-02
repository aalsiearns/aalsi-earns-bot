import random, datetime, os, threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from pymongo import MongoClient

# --- 1. RENDER SERVER (Uptime Fix) ---
flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "Aalsi Bot: All Clear!", 200

def run_flask():
    # Code ke andar hi port set kar diya hai
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host='0.0.0.0', port=port)

# --- 2. CONFIGURATION ---
# Yahan apna bilkul naya wala token dalo
NEW_TOKEN = "8695922978:AAEDgTfzv33sT3s7qsg858TO5DXXQBq87-k" 

ADMIN_ID = 7515767909
CHANNELS = [-1002138873616, -1002103099519, -1002252271483]
INVITE_LINKS = ["https://t.me/+gTZ_cjnU5GczNTg1", "https://t.me/+F9rY-oqYqqo3MjU1", "https://t.me/+cCC_JP8Q2f0zYjI0"]

# MongoDB Connection (Balance yahan safe hai)
MONGO_URL = "mongodb+srv://aalsiearns:momlover1998@cluster0.t6rky3s.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URL)
db = client['aalsiearns_db']
users_col = db['users']

# --- 3. HELPERS ---
async def is_subscribed(bot, user_id):
    for channel_id in CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
            if member.status in ['left', 'kicked']: return False
        except: return False
    return True

async def show_menu(update, context):
    menu = [[InlineKeyboardButton("💰 Wallet", callback_data="wallet"), InlineKeyboardButton("🤝 Refer", callback_data="refer")],
            [InlineKeyboardButton("🎁 Daily Shagun", callback_data="bonus")]]
    text = "🎯 **Aalsi Mode Active!**\nSote sote lootna shuru karein."
    if update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(menu))
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(menu))

# --- 4. COMMANDS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    referrer = int(context.args[0]) if context.args else None
    
    user = users_col.find_one({"user_id": user_id})
    if not user:
        users_col.insert_one({"user_id": user_id, "balance": 0.0, "referred_by": referrer, "last_bonus": "None"})
        if referrer:
            users_col.update_one({"user_id": referrer}, {"$inc": {"balance": 3.0}})

    if await is_subscribed(context.bot, user_id):
        return await show_menu(update, context)

    keyboard = [[InlineKeyboardButton(f"Join Channel {i+1} ⚡", url=l)] for i, l in enumerate(INVITE_LINKS)]
    keyboard.append([InlineKeyboardButton("✅ Verify & Start", callback_data="verify")])
    await update.message.reply_text("💰 **Aalsi Earns Loot**\nJoin channels to earn!", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await is_subscribed(context.bot, update.callback_query.from_user.id):
        await show_menu(update, context)
    else:
        await update.callback_query.answer("❌ Pehle join karo!", show_alert=True)

async def bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.callback_query.from_user.id
    user = users_col.find_one({"user_id": user_id})
    today = str(datetime.date.today())
    if user.get("last_bonus") == today:
        await update.callback_query.answer("Kal aana!", show_alert=True)
    else:
        amt = round(random.uniform(0.5, 2.0), 2)
        users_col.update_one({"user_id": user_id}, {"$inc": {"balance": amt}, "$set": {"last_bonus": today}})
        await update.callback_query.message.reply_text(f"🎊 Shagun mila: ₹{amt}")

async def wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = users_col.find_one({"user_id": update.callback_query.from_user.id})
    await update.callback_query.message.reply_text(f"💳 Wallet: ₹{user['balance']}")

async def refer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot_un = (await context.bot.get_me()).username
    link = f"https://t.me/{bot_un}?start={update.callback_query.from_user.id}"
    await update.callback_query.message.reply_text(f"🤝 Per Refer: ₹3\n\n`{link}`", parse_mode="Markdown")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        count = users_col.count_documents({})
        await update.message.reply_text(f"📊 Total Users: {count}")

# --- 5. MAIN ---
if __name__ == '__main__':
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Conflict aur purane updates saaf karne ke liye
    app = Application.builder().token(NEW_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CallbackQueryHandler(verify, "verify"))
    app.add_handler(CallbackQueryHandler(wallet, "wallet"))
    app.add_handler(CallbackQueryHandler(bonus, "bonus"))
    app.add_handler(CallbackQueryHandler(refer, "refer"))
    
    print("Bot is booting up...")
    # drop_pending_updates=True purane conflicts ko jad se khatam kar dega
    app.run_polling(drop_pending_updates=True)
