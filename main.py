import os
import logging
import threading
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from flask import Flask, render_template_string, request

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
ad_count = {}            # { user_id: num_ads_watched }
verified_users = set()   # user ids that reached >=5
user_list = set()        # seen users (for broadcast)

# -------------------- HTML Template --------------------
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
  <p id="statusText">You have watched <b>{{watched}}</b> of <b>5</b> required ads.</p>
  <div class="steps" id="steps">
    {% for i in range(1,6) %}
      <div class="step {% if i <= watched %}done{% endif %}">{{i}}</div>
    {% endfor %}
  </div>
  <div id="actionArea">
    {{buttons}}
  </div>

<script>
function makeVerify(user, idx){
  // POST to server to verify one ad watched
  fetch(`/verify_ad/${user}/${idx}`, { method: "POST" })
    .then(r => r.text())
    .then(t => {
      // reload page to reflect updated progress
      setTimeout(()=> location.reload(), 300);
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

@app.route("/gift.txt")
def gift_file():
    return get_gift_link()

@app.route("/user/<int:user_id>")
def show_progress(user_id):
    current_mode = get_mode()
    promo_link = get_promo_link()
    user_progress = ad_count.get(user_id, 0)
    total_ads = 5

    # Build buttons HTML:
    buttons_html = ""
    if user_progress < total_ads:
        # show just the next required button to avoid duplicate increments
        next_idx = user_progress + 1
        if current_mode == "monetag":
            # Monetag: show a watch ad button — the SDK may open a popup,
            # here we rely on user to close the ad, then click the verify button (best-effort).
            # We'll display a button that opens Monetag zone (or triggers SDK if loaded)
            buttons_html += f"""
            <div>
              <button class="btn" onclick="window.open('https://libtl.com/zone/10089898','_blank')">▶ Open Monetag Ad</button>
              <button class="btn" onclick="makeVerify({user_id},{next_idx})">✅ I finished Ad {next_idx}</button>
            </div>
            """
        else:
            # Promo mode: direct promo link and verify button
            buttons_html += f"""
            <div>
              <a href="{promo_link}" target="_blank"><button class="btn">▶ Open Promo Link</button></a>
              <button class="btn" onclick="makeVerify({user_id},{next_idx})">✅ I returned — Confirm {next_idx}</button>
            </div>
            """
    else:
        gift_link = get_gift_link()
        buttons_html = f"""
          <div>
            <a href="{gift_link}" target="_blank"><button class="btn complete">🎁 Claim Your Gift</button></a>
          </div>
        """

    from markupsafe import Markup
return render_template_string(HTML_PAGE, watched=user_progress, buttons=Markup(buttons_html))


@app.route("/verify_ad/<int:user_id>/<int:count>", methods=["POST"])
def verify_ad(user_id, count):
    # Ensure user has an entry
    prev = ad_count.get(user_id, 0)
    # Only increment if count == prev+1 to avoid out-of-order/manual calls
    if count == prev + 1:
        ad_count[user_id] = prev + 1
        logger.info(f"Verified user {user_id} ad #{count} (total now {ad_count[user_id]})")
        if ad_count[user_id] >= 5:
            verified_users.add(user_id)
    else:
        logger.info(f"Ignored verify for user {user_id} count={count} prev={prev}")
    return "ok"

# -------------------- Telegram Commands --------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # initialize if missing
    ad_count.setdefault(user_id, 0)
    user_list.add(user_id)
    current_mode = get_mode()
    web = os.environ.get('RENDER_EXTERNAL_URL', f'http://localhost:{os.environ.get("PORT",5000)}')
    keyboard = [[InlineKeyboardButton("🎬 Start Watching Ads", url=f"{web}/user/{user_id}")]]
    await update.message.reply_text(
        f"Welcome! Current Mode: *{current_mode}*\n\nWatch 5 ads to unlock your gift 🎁",
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
    verified_users.clear()
    await update.message.reply_text("✅ All ad progress has been reset.")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("🚫 Admins only.")
    if not context.args:
        return await update.message.reply_text("Usage: /broadcast <message>")
    message = " ".join(context.args)
    sent = 0
    for uid in list(user_list):
        try:
            await context.bot.send_message(chat_id=uid, text=message)
            sent += 1
        except Exception as e:
            logger.info(f"Broadcast failed to {uid}: {e}")
    await update.message.reply_text(f"✅ Broadcast attempted to {sent} users.")

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

# New switchmode - toggles between monetag and promo (admin only)
async def switchmode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("🚫 Admins only.")
    current = get_mode()
    new = "promo" if current == "monetag" else "monetag"
    set_mode(new)
    await update.message.reply_text(f"🔁 Mode switched from *{current}* to *{new}*", parse_mode="Markdown")

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

# New /status - show users and counts summary (admin only)
async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("🚫 Admins only.")
    total_users = len(user_list)
    total_verified = len(verified_users)
    # top users by count
    top = sorted(ad_count.items(), key=lambda x: x[1], reverse=True)[:20]
    top_lines = "\n".join([f"{uid}: {cnt}" for uid, cnt in top]) if top else "No data yet."
    msg = f"📊 Status\nTotal seen users: {total_users}\nUsers completed (>=5): {total_verified}\n\nTop users (id:count):\n{top_lines}"
    await update.message.reply_text(msg)

# /help shows available commands (public)
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🤖 Bot Commands\n\n"
        "/start - Open ad page link\n"
        "/help - Show this message\n\n"
        "Admin commands (you must be admin):\n"
        "/updategift <link> - Update gift link\n"
        "/getgift - View current gift link\n"
        "/resetads - Reset all user progress\n"
        "/broadcast <message> - Send message to all users\n"
        "/setmode <monetag|promo> - Set mode explicitly\n"
        "/switchmode - Toggle between monetag and promo\n"
        "/setpromo <link> - Update promo link\n"
        "/currentmode - Show current mode\n"
        "/status - Show users and view counts\n"
    )
    await update.message.reply_text(text)

async def echo_logger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text or ""
    logger.info(f"Incoming message from {user.username} ({user.id}): {text}")
    # keep a minimal reply to acknowledge
    await update.message.reply_text("✅ Received.")

# -------------------- Run Flask --------------------
def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

# -------------------- Main Function --------------------
def main():
    threading.Thread(target=run_flask, daemon=True).start()
    logger.info("Flask server started in background thread.")
    application = ApplicationBuilder().token(TOKEN).build()

    # Register Commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("updategift", updategift))
    application.add_handler(CommandHandler("getgift", getgift))
    application.add_handler(CommandHandler("resetads", resetads))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("setmode", setmode))
    application.add_handler(CommandHandler("switchmode", switchmode))  # new
    application.add_handler(CommandHandler("setpromo", setpromo))
    application.add_handler(CommandHandler("currentmode", currentmode))
    application.add_handler(CommandHandler("status", status))          # new
    application.add_handler(CommandHandler("help", help_cmd))         # new

    # Log all messages (non-command)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_logger))

    logger.info("Handlers registered. Starting polling...")
    application.run_polling()
    logger.info("Polling stopped.")

if __name__ == "__main__":
    main()

