import os
import logging
import threading
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from flask import Flask, render_template_string, request
from markupsafe import Markup

# -------------------- Configuration --------------------
TOKEN = "8103309728:AAGKsck7UMUmfjucRRNoEcc3YFazhvz_u3I"
JOIN_CHANNEL_LINK = "https://t.me/gsf8mqOl0atkMTM0"
ADMIN_ID = 5236441213  # Sunday Kehinde Akinade

# -------------------- Logging --------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------- File Constants --------------------
MODE_FILE = "mode.txt"
PROMO_FILE = "promo.txt"
GIFT_FILE = "gift.txt"

# -------------------- Helpers --------------------
def get_gift_link():
    if os.path.exists(GIFT_FILE):
        return open(GIFT_FILE).read().strip()
    return "https://fonpay.com.ng"

def update_gift_link(new_link):
    with open(GIFT_FILE, "w") as f:
        f.write(new_link.strip())

def get_mode():
    if os.path.exists(MODE_FILE):
        return open(MODE_FILE).read().strip()
    return "monetag"

def set_mode(mode):
    with open(MODE_FILE, "w") as f:
        f.write(mode.strip())

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
user_list = set()

# -------------------- Flask HTML --------------------
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Watch Ads</title>
<style>
  body{font-family:Arial,Helvetica,sans-serif;text-align:center;padding:24px;background:#f9f9f9}
  .btn{padding:12px 20px;border-radius:8px;border:none;background:#0088cc;color:#fff;font-size:16px;margin:8px;cursor:pointer}
  .btn:disabled{opacity:0.6;cursor:not-allowed}
  .complete{background:#28a745}
  .steps{display:flex;gap:8px;justify-content:center;margin:12px 0}
  .step{width:36px;height:36px;border-radius:50%;background:#ddd;display:flex;align-items:center;justify-content:center;font-weight:700}
  .step.done{background:linear-gradient(90deg,#6f4cff,#f04);color:#fff;transform:translateY(-4px)}
</style>
</head>
<body>
  <h2>🎬 Watch Ads to Unlock Your Gift</h2>
  <p>You have watched <b>{{watched}}</b> of <b>5</b> required ads.</p>
  <div class="steps">
    {% for i in range(1,6) %}
      <div class="step {% if i <= watched %}done{% endif %}">{{i}}</div>
    {% endfor %}
  </div>
  <div id="actionArea">{{buttons}}</div>

<script>
function makeVerify(user, idx){
  fetch(`/verify_ad/${user}/${idx}`, { method: "POST" })
    .then(r => r.text())
    .then(t => {
      setTimeout(()=> location.reload(), 500);
    }).catch(console.error);
}
</script>
</body>
</html>
"""

# -------------------- Flask Setup --------------------
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Telegram Ad Bot is running successfully."

@app.route("/user/<int:user_id>")
def show_progress(user_id):
    current_mode = get_mode()
    promo_link = get_promo_link()
    monetag_link = "https://libtl.com/zone/10089898"
    user_progress = ad_count.get(user_id, 0)
    total_ads = 5

    buttons_html = ""
    if user_progress < total_ads:
        next_idx = user_progress + 1
        if current_mode == "monetag":
            buttons_html = f"""
            <div>
              <iframe src="{monetag_link}" width="100%" height="450" frameborder="0"></iframe>
              <button class="btn" onclick="makeVerify({user_id},{next_idx})">✅ Continue to Ad {next_idx + 1}</button>
            </div>
            """
        else:
            buttons_html = f"""
            <div>
              <a href="{promo_link}" target="_blank">
                <button class="btn">▶ Open Promo Link</button>
              </a>
              <button class="btn" onclick="makeVerify({user_id},{next_idx})">✅ Confirm Visit {next_idx}</button>
            </div>
            """
    else:
        gift_link = get_gift_link()
        buttons_html = f"""
        <div>
          <a href="{gift_link}" target="_blank">
            <button class="btn complete">🎁 Claim Your Gift</button>
          </a>
        </div>
        """

    return render_template_string(HTML_PAGE, watched=user_progress, buttons=Markup(buttons_html))

@app.route("/verify_ad/<int:user_id>/<int:count>", methods=["POST"])
def verify_ad(user_id, count):
    prev = ad_count.get(user_id, 0)
    if count == prev + 1:
        ad_count[user_id] = prev + 1
        logger.info(f"User {user_id} verified ad #{count} (now {ad_count[user_id]})")
        if ad_count[user_id] >= 5:
            verified_users.add(user_id)
    return "ok"

# -------------------- Telegram Bot Commands --------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ad_count.setdefault(user_id, 0)
    user_list.add(user_id)
    web = os.environ.get('RENDER_EXTERNAL_URL', f'http://localhost:{os.environ.get("PORT",5000)}')
    keyboard = [[InlineKeyboardButton("🎬 Start Watching Ads", url=f"{web}/user/{user_id}")]]
    await update.message.reply_text(
        f"Welcome! Current Mode: *{get_mode()}*\n\nWatch 5 ads to unlock your gift 🎁",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def updategift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("🚫 Permission denied.")
    if not context.args:
        return await update.message.reply_text("Usage: /updategift <link>")
    link = context.args[0]
    update_gift_link(link)
    await update.message.reply_text(f"✅ Gift link updated to:\n{link}")

async def getgift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("🚫 Admin only.")
    await update.message.reply_text(f"🎁 Current Gift Link:\n{get_gift_link()}")

async def resetads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("🚫 Admin only.")
    ad_count.clear()
    verified_users.clear()
    await update.message.reply_text("✅ All ad progress reset.")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("🚫 Admin only.")
    if not context.args:
        return await update.message.reply_text("Usage: /broadcast <message>")
    message = " ".join(context.args)
    sent = 0
    for uid in list(user_list):
        try:
            await context.bot.send_message(chat_id=uid, text=message)
            sent += 1
        except:
            pass
    await update.message.reply_text(f"✅ Message sent to {sent} users.")

async def setmode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("🚫 Admin only.")
    if not context.args:
        return await update.message.reply_text("Usage: /setmode <monetag|promo>")
    mode = context.args[0].lower()
    if mode not in ["monetag", "promo"]:
        return await update.message.reply_text("⚠️ Invalid mode.")
    set_mode(mode)
    await update.message.reply_text(f"✅ Mode set to: {mode}")

async def switchmode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("🚫 Admin only.")
    current = get_mode()
    new = "promo" if current == "monetag" else "monetag"
    set_mode(new)
    await update.message.reply_text(f"🔁 Switched from *{current}* to *{new}*", parse_mode="Markdown")

async def setpromo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("🚫 Admin only.")
    if not context.args:
        return await update.message.reply_text("Usage: /setpromo <link>")
    update_promo_link(context.args[0])
    await update.message.reply_text(f"✅ Promo link updated.")

async def currentmode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🧭 Current Mode: {get_mode()}")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("🚫 Admin only.")
    msg = f"📊 Users: {len(user_list)} | Completed: {len(verified_users)}"
    await update.message.reply_text(msg)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🤖 Bot Commands\n\n"
        "/start - Start ad watching\n"
        "/help - Show this help\n\n"
        "Admin:\n"
        "/updategift <link>\n"
        "/getgift\n"
        "/resetads\n"
        "/broadcast <msg>\n"
        "/setmode <monetag|promo>\n"
        "/switchmode\n"
        "/setpromo <link>\n"
        "/currentmode\n"
        "/status\n"
    )
    await update.message.reply_text(text)

async def echo_logger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    logger.info(f"{user.id} sent: {update.message.text}")
    await update.message.reply_text("✅ Received.")

# -------------------- Run Flask --------------------
def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

# -------------------- Main --------------------
def main():
    threading.Thread(target=run_flask, daemon=True).start()
    application = ApplicationBuilder().token(TOKEN).build()

    # Register Commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("updategift", updategift))
    application.add_handler(CommandHandler("getgift", getgift))
    application.add_handler(CommandHandler("resetads", resetads))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("setmode", setmode))
    application.add_handler(CommandHandler("switchmode", switchmode))
    application.add_handler(CommandHandler("setpromo", setpromo))
    application.add_handler(CommandHandler("currentmode", currentmode))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_logger))

    logger.info("🚀 Bot started. Flask running in background.")
    application.run_polling()

if __name__ == "__main__":
    main()
