import os
import logging
import threading
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from flask import Flask, render_template_string

TOKEN = "8103309728:AAGKsck7UMUmfjucRRNoEcc3YFazhvz_u3I"
JOIN_CHANNEL_LINK = "https://t.me/gsf8mqOl0atkMTM0"
ADMIN_ID = 5236441213  # Sunday Kehinde Akinade (Your Telegram user ID)

# -------------------- Logging --------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------- Gift Management --------------------
def get_gift_link():
    try:
        with open("gift.txt", "r") as f:
            return f.read().strip()
    except:
        return "https://example.com"

def update_gift_link(new_link):
    with open("gift.txt", "w") as f:
        f.write(new_link.strip())

# -------------------- Tracking --------------------
ad_count = {}
verified_users = set()

# -------------------- HTML --------------------
HTML_PAGE = """(your HTML remains unchanged here)"""

# -------------------- Flask Setup --------------------
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Telegram Ad Bot is running successfully."

@app.route("/gift.txt")
def gift_file():
    return get_gift_link()

@app.route("/user/<int:user_id>")
def show_progress(user_id):
    return render_template_string(HTML_PAGE)

@app.route("/verify_ad/<int:count>", methods=["POST"])
def verify_ad(count):
    return "ok"

# -------------------- Telegram Commands --------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ad_count[user_id] = 0
    keyboard = [[
        InlineKeyboardButton("🎬 Start Watching Ads",
            url=f"{os.environ.get('RENDER_EXTERNAL_URL','http://localhost:5000')}/user/{user_id}")
    ]]
    await update.message.reply_text(
        "Welcome! Watch ads to unlock your gift 🎁",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def updategift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 You don’t have permission to use this command.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /updategift <new_link>")
        return

    new_link = context.args[0]
    update_gift_link(new_link)
    await update.message.reply_text(f"✅ Gift link updated to:\n{new_link}")

async def currentmode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 Admins only.")
        return

    await update.message.reply_text("🧭 Current mode: monetag")

async def echo_logger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    logger.info(f"Incoming message from {user.username} ({user.id}): {text}")
    await update.message.reply_text("✅ Message received and logged.")

# -------------------- Run Flask --------------------
def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

# -------------------- Main Function --------------------
def main():
    threading.Thread(target=run_flask, daemon=True).start()
    logger.info("Flask server started in background thread.")

    application = ApplicationBuilder().token(TOKEN).build()

    # ✅ Register Commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("updategift", updategift))
    application.add_handler(CommandHandler("currentmode", currentmode))

    # ✅ Log all messages (non-command)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_logger))

    logger.info("Handlers registered. Starting polling...")
    application.run_polling()
    logger.info("Polling stopped.")

if __name__ == "__main__":
    main()
    
