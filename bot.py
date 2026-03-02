import sqlite3, random, datetime, os, threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- 1. RENDER PORT FIX (Isse bot kabhi band nahi hoga) ---
flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "Aalsi Bot Status: 100% Active!", 200

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host='0.0.0.0', port=port)

# --- 2. CONFIGURATION ---
TOKEN = "8695922978:AAFr7SRrQX-ClMwxeXE2ym3GAUhLsOLO00s"
ADMIN_ID = 7515767909
CHANNELS = [-1002138873616, -1002103099519, -1002252271483] 
INVITE_LINKS = ["https://t.me/+gTZ_cjnU5GczNTg1", "https://t.me/+F9rY-oqYqqo3MjU1", "https://t.me/+cCC_JP8Q2f0zYjI0"]

# --- 3. DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('aalsiearns.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance REAL, referred_by INTEGER, last_bonus TEXT, joined INTEGER)')
    conn.commit(); conn.close()

init_db()

def get_user(user_id):
    conn = sqlite3.connect('aalsiearns.db')
    c = conn.cursor(); c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    res = c.fetchone(); conn.close()
    return res

# --- 4. FORCE JOIN LOGIC ---
async def is_subscribed(bot, user_id):
    for channel_id in CHANNELS:
        try:
            member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
            if member.status in ['left', 'kicked']: return False
        except: return False # Bot admin nahi hai toh fail hoga
    return True

# --- 5. BOT COMMANDS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    referrer = int(context.args[0]) if context.args else None
    
    # User entry in DB
    if not get_user(user_id):
        conn = sqlite3.connect('aalsiearns.db'); c = conn.cursor()
        c.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)", (user_id, 0.0, referrer, "None", 0))
        if referrer:
            try: c.execute("UPDATE users SET balance = balance + 3 WHERE user_id = ?", (referrer,))
            except: pass
        conn.commit(); conn.close()

    if await is_subscribed(context.bot, user_id):
        return await show_menu(update, context)

    # Force Join Buttons
    keyboard = [[InlineKeyboardButton(f"Join Channel {i+1} ⚡", url=l)] for i, l in enumerate(INVITE_LINKS)]
    keyboard.append([InlineKeyboardButton("✅ Verify & Start Loot", callback_data="verify")])
    text = "💰 **Aalsi Earns Loot**\n\nBhai, pehle teeno channels join kar lo, phir paise chhapna shuru!"
    
    if update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if await is_subscribed(context.bot, query.from_user.id):
        await show_menu(update, context)
    else:
        await query.answer("❌ Abe Aalsi! Pehle join kar, mazaak mat kar.", show_alert=True)

async def show_menu(update, context):
    menu = [[InlineKeyboardButton("💰 Wallet", callback_data="wallet"), InlineKeyboardButton("🤝 Refer", callback_data="refer")],
            [InlineKeyboardButton("🎁 Daily Shagun", callback_data="bonus")]]
    text = "🎯 **Aalsi Mode Active!**\nSote sote lootna shuru karein."
    if update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(menu))
    else:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(menu))

async def bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.callback_query.from_user.id
    if not await is_subscribed(context.bot, user_id): return await start(update, context)
    
    user = get_user(user_id); today = str(datetime.date.today())
    if user[3] == today:
        await update.callback_query.answer("Kal aana!", show_alert=True)
    else:
        amt = round(random.uniform(0.5, 2.0), 2)
        conn = sqlite3.connect('aalsiearns.db'); c = conn.cursor()
        c.execute("UPDATE users SET balance = balance + ?, last_bonus = ? WHERE user_id = ?", (amt, today, user_id))
        conn.commit(); conn.close()
        await update.callback_query.message.reply_text(f"🎊 Aapko aaj ₹{amt} ka Shagun mila!")

async def wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.callback_query.from_user.id
    if not await is_subscribed(context.bot, user_id): return await start(update, context)
    user = get_user(user_id)
    await update.callback_query.message.reply_text(f"💳 **Current Balance:** ₹{user[1]}")

async def refer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.callback_query.from_user.id
    if not await is_subscribed(context.bot, user_id): return await start(update, context)
    bot_un = (await context.bot.get_me()).username
    link = f"https://t.me/{bot_un}?start={user_id}"
    await update.callback_query.message.reply_text(f"🤝 **Per Refer: ₹3**\n\nShare Link:\n`{link}`", parse_mode="Markdown")

# --- 6. RUN EVERYTHING ---
if __name__ == '__main__':
    threading.Thread(target=run_flask).start() # Keep Render Awake
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(verify, pattern="verify"))
    app.add_handler(CallbackQueryHandler(wallet, pattern="wallet"))
    app.add_handler(CallbackQueryHandler(bonus, pattern="bonus"))
    app.add_handler(CallbackQueryHandler(refer, pattern="refer"))
    print("Bot is ready for Loot!")
    app.run_polling()
