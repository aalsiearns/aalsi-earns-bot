import sqlite3, random, datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- CONFIG (Details Pre-filled) ---
TOKEN = "8695922978:AAFr7SRrQX-ClMwxeXE2ym3GAUhLsOLO00s"
ADMIN_ID = 7515767909
CHANNELS = [-1002138873616, -1002103099519, -1002252271483] 
INVITE_LINKS = [
    "https://t.me/+gTZ_cjnU5GczNTg1", 
    "https://t.me/+F9rY-oqYqqo3MjU1", 
    "https://t.me/+cCC_JP8Q2f0zYjI0"
]

def init_db():
    conn = sqlite3.connect('aalsiearns.db')
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance REAL, referred_by INTEGER, last_bonus TEXT, joined INTEGER)')
    conn.commit()
    conn.close()

init_db()

def get_user(user_id):
    conn = sqlite3.connect('aalsiearns.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    res = c.fetchone()
    conn.close()
    return res

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    referrer = int(context.args[0]) if context.args else None
    if not get_user(user_id):
        conn = sqlite3.connect('aalsiearns.db')
        c = conn.cursor()
        c.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)", (user_id, 0.0, referrer, "None", 0))
        if referrer:
            try:
                c.execute("UPDATE users SET balance = balance + 3 WHERE user_id = ?", (referrer,))
            except: pass
        conn.commit()
        conn.close()
    
    keyboard = [[InlineKeyboardButton(f"Join Channel {i+1} ⚡", url=l)] for i, l in enumerate(INVITE_LINKS)]
    keyboard.append([InlineKeyboardButton("✅ Verify & Start", callback_data="verify")])
    await update.message.reply_text(f"💰 **Aalsi Earns Loot**\nJoin all channels to start earning:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    menu = [[InlineKeyboardButton("💰 Wallet", callback_data="wallet"), InlineKeyboardButton("🤝 Refer", callback_data="refer")],
            [InlineKeyboardButton("🎁 Daily Shagun", callback_data="bonus")]]
    await query.message.edit_text("🎯 **Aalsi Mode Active!**\nSote sote lootna shuru karein.", reply_markup=InlineKeyboardMarkup(menu))

async def bonus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.callback_query.from_user.id
    user = get_user(user_id)
    today = str(datetime.date.today())
    if user[3] == today:
        await update.callback_query.answer("Abe aalsi! Aaj ka shagun mil gaya. Kal aana!", show_alert=True)
    else:
        amt = round(random.uniform(0.5, 2.0), 2)
        conn = sqlite3.connect('aalsiearns.db')
        c = conn.cursor()
        c.execute("UPDATE users SET balance = balance + ?, last_bonus = ? WHERE user_id = ?", (amt, today, user_id))
        conn.commit()
        conn.close()
        await update.callback_query.message.reply_text(f"🎊 Aapko aaj ₹{amt} ka Shagun mila!")

async def wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.callback_query.from_user.id)
    await update.callback_query.message.reply_text(f"💳 **Wallet Balance:** ₹{user[1]}")

async def refer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.callback_query.from_user.id
    bot_un = (await context.bot.get_me()).username
    link = f"https://t.me/{bot_un}?start={user_id}"
    await update.callback_query.message.reply_text(f"🤝 **Per Refer: ₹3**\n\nLink share karein:\n`{link}`", parse_mode="Markdown")

async def sendall(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        msg = " ".join(context.args)
        conn = sqlite3.connect('aalsiearns.db')
        c = conn.cursor(); c.execute("SELECT user_id FROM users"); users = c.fetchall(); conn.close()
        for u in users:
            try: await context.bot.send_message(u[0], msg)
            except: pass
        await update.message.reply_text("Done!")

if __name__ == '__main__':
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("sendall", sendall))
    app.add_handler(CallbackQueryHandler(verify, pattern="verify"))
    app.add_handler(CallbackQueryHandler(wallet, pattern="wallet"))
    app.add_handler(CallbackQueryHandler(bonus, pattern="bonus"))
    app.add_handler(CallbackQueryHandler(refer, pattern="refer"))
    print("Aalsi Bot is alive...")
    app.run_polling()
