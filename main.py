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

# -------------------- File Constants --------------------
MODE_FILE = "mode.txt"
PROMO_FILE = "promo.txt"

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

# -------------------- Mode & Promo Management --------------------
def get_mode():
    if os.path.exists(MODE_FILE):
        return open(MODE_FILE).read().strip()
    return "monetag"

def set_mode(mode):
    with open(MODE_FILE, "w") as f:
        f.write(mode)

def get_promo_link():
    if os.path.exists(PROMO_FILE):
        return open(PROMO_FILE).read().strip()
    return "https://fonpay.com.ng"

def update_promo_link(new_link):
    with open(PROMO_FILE, "w") as f:
        f.write(new_link.strip())

# -------------------- Tracking --------------------
ad_count = {}
verified_users = set()
user_list = set()  # for broadcast

# -------------------- HTML Template --------------------
HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Watch Ads</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }
        .btn { padding: 10px 20px; font-size: 16px; background: #0088cc; color: white; border: none; border-radius: 5px; }
        .btn:hover { background: #005f8a; }
    </style>
</head>
<body>
    <h2>🎬 Watch Ads to Unlock Your Gift</h2>
    <!-- Dynamic Ad Section -->
</body>
</html>
"""

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
    # Get current mode and promo link
    current_mode = get_mode()
    promo_link = get_promo_link()

    # Dynamic switch between Monetag and Promo modes
    if current_mode == "monetag":
        ad_section = "<script src='//libtl.com/sdk.js' data-zone='10089898' data-sdk='show_10089898'></script>"
    else:
        ad_section = f"<a href='{promo_link}' target='_blank'><button class='btn'>🎯 View Promo</button></a>"

    html = HTML_PAGE.replace("<!-- Dynamic Ad Section -->", ad_section)
    return render_template_string(html)

@app.route("/verify_ad/<int:count>", methods=["POST"])
def verify_ad(count):
    return "ok"

# -------------------- Telegram Commands --------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ad_count[user_id] = 0
    user_list.add(user_id)
    current_mode = get_mode()

    keyboard = [[
        InlineKeyboardButton("🎬 Start Watching Ads",
            url=f"{os.environ.get('RENDER_EXTERNAL_URL','http://localhost:5000')}/user/{user_id}")
    ]]
    await update.message.reply_text(
        f"Welcome! Current Mode: *{current_mode}*\nWatch ads to unlock your gift 🎁",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def updategift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("🚫 You don’t have permission to use this command.")
    if not context.args:
        return await update.message.reply_text("Usage: /updategift <new_link>")
    new_link = context.args[0]
    update_gift_link(new_link)
    await update.message.reply_text(f"✅ Gift link updated to:\n{new_link}")

async def getgift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("🚫 Admins only.")
    await update.message.reply_text(f"🎁 Current Gift Link:\n{get_gift_link()}")

async def resetads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("🚫 Admins only.")
    ad_count.clear()
    await update.message.reply_text("✅ All ad progress has been reset.")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("🚫 Admins only.")
    if not context.args:
        return await update.message.reply_text("Usage: /broadcast <message>")
    message = " ".join(context.args)
    for uid in user_list:
        try:
            await context.bot.send_message(chat_id=uid, text=message)
        except:
            continue
    await update.message.reply_text("✅ Broadcast sent to all users.")

async def setmode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("🚫 Admins only.")
    if not context.args:
        return await update.message.reply_text("Usage: /setmode <monetag/promo>")
    mode = context.args[0].lower()
    if mode not in ["monetag", "promo"]:
        return await update.message.reply_text("⚠️ Invalid mode. Use 'monetag' or 'promo'.")
    set_mode(mode)
    await update.message.reply_text(f"✅ Mode updated to: {mode}")

async def setpromo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("🚫 Admins only.")
    if not context.args:
        return await update.message.reply_text("Usage: /setpromo <promo_link>")
    new_link = context.args[0]
    update_promo_link(new_link)
    await update.message.reply_text(f"✅ Promo link updated to:\n{new_link}")

async def currentmode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("🚫 Admins only.")
    await update.message.reply_text(f"🧭 Current mode: {get_mode()}")

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
    application.add_handler(CommandHandler("getgift", getgift))
    application.add_handler(CommandHandler("resetads", resetads))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("setmode", setmode))
    application.add_handler(CommandHandler("setpromo", setpromo))
    application.add_handler(CommandHandler("currentmode", currentmode))

    # ✅ Log all messages (non-command)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_logger))

    logger.info("Handlers registered. Starting polling...")
    application.run_polling()
    logger.info("Polling stopped.")

if __name__ == "__main__":
    main()
    
