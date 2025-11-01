import os
import logging
import threading
from flask import Flask, render_template_string, request, Markup
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# -------------------- CONFIG --------------------
TOKEN = "8103309728:AAGKsck7UMUmfjucRRNoEcc3YFazhvz_u3I"
JOIN_CHANNEL_LINK = "https://t.me/gsf8mqOl0atkMTM0"
ADMIN_ID = 5236441213  # Sunday Kehinde Akinade

# -------------------- LOGGING --------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------- GLOBAL VARIABLES --------------------
ad_count = {}
verified_users = set()
current_mode = "monetag"  # Default mode
promo_text = "Watch 5 ads and get your gift 🎁"

# -------------------- GIFT LINK --------------------
def get_gift_link():
    try:
        with open("gift.txt", "r") as f:
            return f.read().strip()
    except:
        return "https://example.com"

def update_gift_link(new_link):
    with open("gift.txt", "w") as f:
        f.write(new_link.strip())

# -------------------- HTML PAGE --------------------
HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>🎬 Watch Ads to Unlock Your Gift</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; margin: 20px; }
        .btn { display: inline-block; margin: 10px; padding: 10px 15px; background: #007bff; color: white; border-radius: 5px; text-decoration: none; }
        .btn:disabled { background: gray; }
        .status { font-size: 18px; margin-top: 20px; }
    </style>
    <script>
        async function makeVerify(userId, adNumber) {
            const res = await fetch(`/verify_ad/${userId}/${adNumber}`, { method: 'POST' });
            const txt = await res.text();
            alert(txt);
            location.reload();
        }
    </script>
</head>
<body>
    <h2>🎬 Watch Ads to Unlock Your Gift</h2>
    <p>You have watched {{ watched }} of 5 required ads.</p>
    {{ buttons|safe }}
    <div class="status">{{ promo }}</div>
</body>
</html>
"""

# -------------------- FLASK SETUP --------------------
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Telegram Ad Bot is running successfully."

@app.route("/gift.txt")
def gift_file():
    return get_gift_link()

@app.route("/user/<int:user_id>")
def show_progress(user_id):
    user_progress = ad_count.get(user_id, 0)
    buttons_html = ""

    # Generate 5 ad buttons dynamically
    for i in range(1, 6):
        if i <= user_progress:
            buttons_html += f"<div><button class='btn' disabled>✅ Ad {i} Done</button></div>"
        else:
            buttons_html += f"""
            <div>
                <button class='btn' onclick="window.open('https://libtl.com/zone/10089898','_blank')">▶ Open Ad {i}</button>
                <button class='btn' onclick="makeVerify({user_id},{i})">✅ I finished Ad {i}</button>
            </div>
            """

    if user_progress >= 5:
        gift_link = get_gift_link()
        buttons_html += f"<div><a class='btn' href='{gift_link}'>🎁 Claim Your Gift</a></div>"

    return render_template_string(HTML_PAGE, watched=user_progress, buttons=Markup(buttons_html), promo=promo_text)

@app.route("/verify_ad/<int:user_id>/<int:ad_number>", methods=["POST"])
def verify_ad(user_id, ad_number):
    current = ad_count.get(user_id, 0)
    if ad_number == current + 1:
        ad_count[user_id] = ad_number
        return f"✅ Ad {ad_number} verified successfully!"
    return f"⚠ Invalid step! Please complete ads in order."

# -------------------- TELEGRAM COMMANDS --------------------
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

async def gift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🎁 Your gift link: {get_gift_link()}")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🧭 Available Commands:\n"
        "/start - Begin watching ads\n"
        "/gift - Get current gift link\n"
        "/status - View your ad progress\n"
        "/help - Show this help message\n\n"
        "👑 Admin Commands:\n"
        "/setmode <mode>\n"
        "/switchmode\n"
        "/currentmode\n"
        "/setpromo <text>\n"
        "/updategift <link>\n"
        "/status - View all user counts"
    )
    await update.message.reply_text(text)

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

async def setmode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_mode
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 Admins only.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /setmode <monetag|propeller>")
        return
    mode = context.args[0].lower()
    if mode in ["monetag", "propeller"]:
        current_mode = mode
        await update.message.reply_text(f"✅ Mode switched to: {mode}")
    else:
        await update.message.reply_text("⚠ Invalid mode. Choose 'monetag' or 'propeller'.")

async def switchmode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_mode
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 Admins only.")
        return
    current_mode = "propeller" if current_mode == "monetag" else "monetag"
    await update.message.reply_text(f"🔁 Mode switched to: {current_mode}")

async def currentmode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🧭 Current mode: {current_mode}")

async def setpromo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global promo_text
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 Admins only.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /setpromo <new promo text>")
        return
    promo_text = " ".join(context.args)
    await update.message.reply_text(f"✅ Promo text updated:\n{promo_text}")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        user_id = update.effective_user.id
        count = ad_count.get(user_id, 0)
        await update.message.reply_text(f"📊 You’ve watched {count}/5 ads.")
    else:
        text = "📊 User Progress Report:\n"
        for uid, count in ad_count.items():
            text += f"• User {uid}: {count}/5 ads\n"
        await update.message.reply_text(text or "No users yet.")

# -------------------- LOGGING MESSAGES --------------------
async def echo_logger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text
    logger.info(f"Message from {user.username} ({user.id}): {text}")
    await update.message.reply_text("✅ Message received.")

# -------------------- RUN FLASK --------------------
def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

# -------------------- MAIN --------------------
def main():
    threading.Thread(target=run_flask, daemon=True).start()
    logger.info("Flask server started in background thread.")

    application = ApplicationBuilder().token(TOKEN).build()

    # User Commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("gift", gift))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status))

    # Admin Commands
    application.add_handler(CommandHandler("updategift", updategift))
    application.add_handler(CommandHandler("setmode", setmode))
    application.add_handler(CommandHandler("switchmode", switchmode))
    application.add_handler(CommandHandler("currentmode", currentmode))
    application.add_handler(CommandHandler("setpromo", setpromo))

    # Log all text
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_logger))

    logger.info("Handlers registered. Starting polling...")
    application.run_polling()

if __name__ == "__main__":
    main()
    
