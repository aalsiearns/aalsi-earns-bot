import sqlite3, random, datetime, threading, os
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Flask setup for Render Port Binding
flask_app = Flask(__name__)
@flask_app.route('/')
def home(): return "Bot is Alive!", 200

def run_flask():
    # Render hamesha PORT environment variable deta hai
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host='0.0.0.0', port=port)

TOKEN = "8695922978:AAFr7SRrQX-ClMwxeXE2ym3GAUhLsOLO00s"
ADMIN_ID = 7515767909
CHANNELS = [-1002138873616, -1002103099519, -1002252271483] 
INVITE_LINKS = ["https://t.me/+gTZ_cjnU5GczNTg1", "https://t.me/+F9rY-oqYqqo3MjU1", "https://t.me/+cCC_JP8Q2f0zYjI0"]

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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    referrer = int(context.args[0]) if context.args else None
    if not get_user(user_id):
        conn = sqlite3.connect('aalsiearns.db')
        c = conn.cursor()
        c.execute("INSERT INTO users VALUES (?, ?, ?, ?, ?)", (user_id, 0.0, referrer, "None", 0))
        if referrer:
            try: c.execute("UPDATE users SET balance = balance + 3 WHERE user_id = ?", (referrer,))
            except: pass
        conn.commit(); conn.close()
    keyboard = [[InlineKeyboardButton(f"Join Channel {i+1} ⚡", url=l)] for i, l in enumerate(INVITE_LINKS)]
    keyboard.append([InlineKeyboardButton("✅ Verify & Start", callback_data="verify")])
    await update.message.reply_text(f"💰 **Aalsi Earns Loot**\nJoin all channels to start earning:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def verify(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    menu = [[InlineKeyboardButton("💰 Wallet", callback_data="wallet"), InlineKeyboardButton("🤝 Refer", callback_data="refer")],
            [InlineKeyboardButton("🎁 Daily Shagun", callback_data="bonus")]]
    await query.message.edit_text("🎯 **Aalsi Mode Active!**\nSote sote lootna shuru karein.", reply_markup=InlineKeyboardMarkup(menu))

# Bonus, Wallet, Refer functions same rahenge...

if __name__ == '__main__':
    threading.Thread(target=run_flask).start() # Render ko khush rakhne ke liye
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(verify, "verify"))
    # Baki handlers add kar dena...
    app.run_polling()
