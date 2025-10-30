from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from flask import Flask, send_from_directory

app = Flask(__name__)

# Telegram Bot Token
TOKEN = "8103309728:AAH-lGTT6KXIb9Qu5pMnA1qgiKottnugoKw"

# Track user ad counts
user_clicks = {}

@app.route('/')
def home():
    return "Telegram Ad Bot is running!"

@app.route('/watch-ad')
def serve_ad_page():
    return send_from_directory('.', 'watch_ad.html')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    user_clicks[user_id] = 0
    await update.message.reply_text(
        "🎬 Welcome! Click the link below to start watching ads.\n\n"
        "👉 https://YOUR_DEPLOYED_LINK/watch-ad"
    )

async def check_ads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    count = user_clicks.get(user_id, 0)
    if count >= 5:
        await update.message.reply_text(
            "🎁 Congratulations! You’ve unlocked your gift:\n"
            "https://www.canva.com/brand/join?token=BrnBqEuFTwf7IgNrKWfy4A&br\n\n"
            "Join our Telegram Channel 👉 https://t.me/gsf8mqOl0atkMTM0"
        )
    else:
        await update.message.reply_text(
            f"✅ You’ve watched {count}/5 ads.\nKeep going to unlock your reward!"
        )

def main():
    bot = ApplicationBuilder().token(TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("check", check_ads))
    bot.run_polling()

if __name__ == '__main__':
    main()
