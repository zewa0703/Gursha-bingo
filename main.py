import sqlite3
import random
import json
import logging
import asyncio
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# --- መረጃዎችዎን እዚህ ያስገቡ ---
TOKEN = '8785251489:AAGDdhN9Xy8fz6IZkpRjNzTvqYkZ9bCVSmM' 
ADMIN_ID =8878914399    # የእርስዎ Telegram ID
ENTRY_FEE = 10.0          # አንድ ጨዋታ ለመጫወት የሚከፈል
DB_FILE = 'bingo_game.db'

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ዳታቤዝ ማዘጋጃ
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, first_name TEXT, balance REAL DEFAULT 0.0)''')
    conn.commit()
    conn.close()

def get_user(user_id, name):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id=?", (user_id,))
    user = c.fetchone()
    if not user:
        c.execute("INSERT INTO users (id, first_name, balance) VALUES (?, ?, ?)", (user_id, name, 50.0)) # ለጅማሮ 50 ብር በነጻ
        conn.commit()
        user = (user_id, name, 50.0)
    conn.close()
    return user

def update_balance(user_id, amount):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET balance = balance + ? WHERE id=?", (amount, user_id))
    conn.commit()
    conn.close()

def generate_card():
    card = {
        'B': random.sample(range(1, 16), 5),
        'I': random.sample(range(16, 31), 5),
        'N': random.sample(range(31, 46), 5),
        'G': random.sample(range(46, 61), 5),
        'O': random.sample(range(61, 76), 5)
    }
    card['N'][2] = "FREE"
    return card

def format_card(card, marked=None):
    if marked is None: marked = []
    header = " B | I | N | G | O \n"
    rows = []
    for i in range(5):
        row = []
        for col in ['B', 'I', 'N', 'G', 'O']:
            val = card[col][i]
            if val == "FREE" or val in marked:
                row.append("✅")
            else:
                row.append(f"{val:2}")
        rows.append(" | ".join(row))
    return "```\n" + header + "\n".join(rows) + "\n```"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = get_user(update.effective_user.id, update.effective_user.first_name)
    await update.message.reply_text(
        f"እንኳን ወደ ቢንጎ መጡ {user[1]}! 🇪🇹\n\n"
        f"💰 ሂሳብዎ፦ {user[2]} ብር\n"
        f"🎮 ጨዋታ ለመጀመር /play ይበሉ።\n"
        f"💵 ሂሳብ ለመጨመር /add_money ይበሉ።"
    )

async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user = get_user(user_id, update.effective_user.first_name)
    
    if user[2] < ENTRY_FEE:
        await update.message.reply_text("በቂ ሂሳብ የለዎትም! መጀመሪያ /add_money ይበሉ።")
        return
    
    update_balance(user_id, -ENTRY_FEE)
    card = generate_card()
    marked = []
    
    msg = await update.message.reply_text(f"ጨዋታ ተጀምሯል! መግቢያ {ENTRY_FEE} ብር ተቀንሷል።\n\nየእርስዎ ካርድ፦\n{format_card(card)}")
    
    await asyncio.sleep(2)
    
    # ቁጥሮችን መጥራት
    numbers = list(range(1, 76))
    random.shuffle(numbers)
    
    drawn = []
    for i in range(15): # 15 ቁጥሮችን ይጥራል
        num = numbers[i]
        drawn.append(num)
        
        # ካርዱ ላይ ካለ ምልክት ያደርጋል
        for col in card:
            if num in card[col]:
                marked.append(num)
        
        status = f"🔢 የወጣው ቁጥር፦ {num}\n\nካርድዎ፦\n{format_card(card, marked)}"
        await msg.edit_text(status, parse_mode='Markdown')
        await asyncio.sleep(2.5) # በየ 2.5 ሰከንዱ ቁጥር ይወጣል

    await update.message.reply_text("ጨዋታው ተጠናቋል! በድጋሚ ለመጫወት /play ይበሉ።")

async def add_money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ለሙከራ 100 ብር እንዲጨምር
    update_balance(update.effective_user.id, 100)
    await update.message.reply_text("100 ብር በሙከራ መልክ ወደ ሂሳብዎ ተጨምሯል! 💰")

if __name__ == '__main__':
    init_db()
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('play', play))
    app.add_handler(CommandHandler('add_money', add_money))
    
    print("Bingo Bot is running... Type /play in Telegram")
    app.run_polling()
