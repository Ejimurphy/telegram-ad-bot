import os
import json
import threading
from flask import Flask, render_template_string
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# === CONFIG ===
TOKEN = "8103309728:AAH-lGTT6KXIb9Qu5pMnA1qgiKottnugoKw"
ADMIN_ID = 590000000  # replace with your Telegram numeric ID

CONFIG_FILE = "bot_config.json"

# === DEFAULT SETTINGS ===
DEFAULT_CONFIG = {
    "mode": "monetag",  # can be "monetag" or "promo"
    "gift_link": "https://example.com",
    "promo_links": []
}

# === CONFIG HANDLERS ===
def load_config():
    if not os.path.exists(CONFIG_FILE):
        save_config(DEFAULT_CONFIG)
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

config = load_config()

# === FLASK APP FOR ADS PAGE ===
app = Flask(__name__)

@app.route("/")
def index():
    if config["mode"] == "monetag":
        return render_template_string(MONETAG_HTML)
    else:
        return render_template_string(PROMO_HTML, promo_links=config["promo_links"], gift_link=config["gift_link"])

# Monetag HTML
MONETAG_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Watch Ads to Unlock Gift</title>
<style>
body { text-align: center; font-family: Arial; background: #f4f4f4; padding: 20px; }
.btn { background: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 8px; cursor: pointer; }
</style>
</head>
<body>
<h2>🎥 Watch Ads to Unlock Your Gift</h2>
<script src='//libtl.com/sdk.js' data-zone='10089898' data-sdk='show_10089898'></script>
<button class="btn" onclick="show_10089898()">Watch Ad</button>
<p>After 5 ads, your reward will unlock!</p>
<a href="/gift" id="gift" style="display:none;">🎁 Claim Gift</a>
<script>
let count = 0;
function show_10089898(){
    count++;
    if (count >= 5){
        document.getElementById('gift').style.display='block';
    }
}
</script>
</body>
</html>
"""

# Promo HTML
PROMO_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Complete Tasks to Unlock Gift</title>
<style>
body { text-align: center; font-family: Arial; background: #f4f4f4; padding: 20px; }
a { display:block; margin:10px auto; background:#4CAF50; color:#fff; padding:10px; border-radius:8px; width:80%; text-decoration:none; }
</style>
</head>
<body>
<h2>📢 Complete all tasks to unlock your gift</h2>
{% for link in promo_links %}
<a href="{{ link }}" target="_blank">Visit Task {{ loop.index }}</a>
{% endfor %}
<a href="{{ gift_link }}" style="display:block;margin-top:20px;background:#2196F3;">🎁 Claim Gift</a>
</body>
</html>
"""

@app.route("/gift")
def gift():
    return f"<meta http-equiv='refresh' content='0;url={config['gift_link']}'>"

# === TELEGRAM BOT ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = config["mode"]
    web_link = os.environ.get("RENDER_EXTERNAL_URL", "http://localhost:5000")
    keyboard = [[InlineKeyboardButton("🎬 Open Ad Page", url=web_link)]]
    await update.message.reply_text(
        f"Welcome! 🎁\n\nCurrent mode: *{mode.upper()}*\n\n"
        "Click below to start and unlock your reward.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

# === ADMIN COMMANDS ===
async def mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You’re not authorized.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /mode monetag or /mode promo")
        return
    new_mode = context.args[0].lower()
    if new_mode not in ["monetag", "promo"]:
        await update.message.reply_text("❌ Invalid mode. Choose 'monetag' or 'promo'.")
        return
    config["mode"] = new_mode
    save_config(config)
    await update.message.reply_text(f"✅ Mode changed to: {new_mode.upper()}")

async def giftlink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You’re not authorized.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /giftlink https://yourlink.com")
        return
    config["gift_link"] = context.args[0]
    save_config(config)
    await update.message.reply_text(f"🎁 Gift link updated to:\n{config['gift_link']}")

async def promolinks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You’re not authorized.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /promolinks link1 link2 link3 ...")
        return
    config["promo_links"] = context.args
    save_config(config)
    await update.message.reply_text(f"✅ Promo links updated:\n" + "\n".join(config["promo_links"]))

# === APP RUN ===
def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

def main():
    threading.Thread(target=run_flask).start()
    bot = ApplicationBuilder().token(TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("mode", mode))
    bot.add_handler(CommandHandler("giftlink", giftlink))
    bot.add_handler(CommandHandler("promolinks", promolinks))
    bot.run_polling()

if __name__ == "__main__":
    main()
    
