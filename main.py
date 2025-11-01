import os
import logging
import threading
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from flask import Flask, render_template_string, request
from markupsafe import Markup

# -------------------- CONFIG --------------------
TOKEN = "8103309728:AAGKsck7UMUmfjucRRNoEcc3YFazhvz_u3I"
JOIN_CHANNEL_LINK = "https://t.me/gsf8mqOl0atkMTM0"
ADMIN_ID = 5236441213  # Sunday Kehinde Akinade

# -------------------- LOGGING --------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------- FILES --------------------
MODE_FILE = "mode.txt"
PROMO_FILE = "promo.txt"
GIFT_FILE = "gift.txt"

# -------------------- STORAGE --------------------
ad_count = {}            # { user_id: ads_watched }
verified_users = set()   # users who finished all 5 ads
user_list = set()        # track all users

# -------------------- MODE MANAGEMENT --------------------
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

def update_promo_link(link):
    with open(PROMO_FILE, "w") as f:
        f.write(link.strip())

def get_gift_link():
    if os.path.exists(GIFT_FILE):
        return open(GIFT_FILE).read().strip()
    return "https://fonpay.com.ng"

def update_gift_link(link):
    with open(GIFT_FILE, "w") as f:
        f.write(link.strip())

# -------------------- HTML PAGE --------------------
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Watch Ads to Unlock Your Gift</title>
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
  <div id="actionArea">
    {{buttons}}
  </div>

<script>
let current = {{watched}};
function showNextAd() {
  if (current >= 5) return;
  current++;
  fetch(`/verify_ad/{{user_id}}/${current}`, { method: "POST" })
    .then(r => r.text())
    .then(t => {
      if (current < 5) {
        setTimeout(()=> location.reload(), 1000);
      } else {
        setTimeout(()=> location.reload(), 800);
      }
    }).catch(console.error);
}
setTimeout(()=>{
  if (current < 5) {
    document.getElementById('openAd').click();
    setTimeout(showNextAd, 10000); // 10s delay before verify
  }
}, 1000);
</script>
</body>
</html>
"""

# -------------------- FLASK --------------------
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Telegram Ad Bot is running successfully."

@app.route("/user/<int:user_id>")
def user_page(user_id):
    mode = get_mode()
    promo = get_promo_link()
    gift = get_gift_link()
    watched = ad_count.get(user_id, 0)
    total = 5

    if watched >= total:
        buttons_html = f'<a href="{gift}" target="_blank"><button class="btn complete">🎁 Claim Your Gift</button></a>'
    else:
        ad_link = "https://otieu.com/4/10060305" if mode == "monetag" else promo
        buttons_html = f'<button id="openAd" class="btn" onclick="window.open(\'{ad_link}\', \'_blank\')">▶ Watch Ad {watched+1}</button>'

    return render_template_string(HTML_PAGE, watched=watched, buttons=Markup(buttons_html), user_id=user_id)

@app.route("/verify_ad/<int:user_id>/<int:count>", methods=["POST"])
def verify_ad(user_id, count):
    prev = ad_count.get(user_id, 0)
    if count == prev + 1 and count <= 5:
        ad_count[user_id] = count
        if count >= 5:
            verified_users.add(user_id)
        logger.info(f"User {user_id} watched ad {count}/5")
    return "ok"

# -------------------- TELEGRAM --------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ad_count.setdefault(user_id, 0)
    user_list.add(user_id)
    mode = get_mode()
    web = os.environ.get('RENDER_EXTERNAL_URL', f"http://localhost:{os.environ.get('PORT', 5000)}")
    link = f"{web}/user/{user_id}"
    keyboard = [[InlineKeyboardButton("🎬 Start Watching Ads", url=link)]]
    await update.message.reply_text(
        f"Welcome! Current Mode: *{mode}*\n\nWatch 5 ads to unlock your gift 🎁",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )

async def updategift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("🚫 Admin only.")
    if not context.args:
        return await update.message.reply_text("Usage: /updategift <link>")
    update_gift_link(context.args[0])
    await update.message.reply_text("✅ Gift link updated.")

async def getgift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        await update.message.reply_text(f"🎁 Gift link:\n{get_gift_link()}")

async def resetads(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == ADMIN_ID:
        ad_count.clear()
        verified_users.clear()
        await update.message.reply_text("✅ All ad progress reset.")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        return await update.message.reply_text("Usage: /broadcast <message>")
    message = " ".join(context.args)
    sent = 0
    for uid in list(user_list):
        try:
            await context.bot.send_message(uid, message)
            sent += 1
        except Exception:
            pass
    await update.message.reply_text(f"✅ Sent to {sent} users.")

async def setmode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        return await update.message.reply_text("Usage: /setmode <monetag|promo>")
    mode = context.args[0].lower()
    if mode not in ["monetag", "promo"]:
        return await update.message.reply_text("Invalid mode.")
    set_mode(mode)
    ad_count.clear()
    await update.message.reply_text(f"✅ Mode set to {mode}")

async def switchmode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    current = get_mode()
    new_mode = "promo" if current == "monetag" else "monetag"
    set_mode(new_mode)
    ad_count.clear()
    await update.message.reply_text(f"🔁 Switched from {current} to {new_mode}")

async def setpromo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    if not context.args:
        return await update.message.reply_text("Usage: /setpromo <link>")
    update_promo_link(context.args[0])
    await update.message.reply_text("✅ Promo link updated.")

async def currentmode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"🧭 Current mode: {get_mode()}")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    msg = (
        f"📊 Status:\nUsers: {len(user_list)}\n"
        f"Completed: {len(verified_users)}"
    )
    await update.message.reply_text(msg)

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🤖 Bot Commands\n"
        "/start - Begin watching ads\n"
        "/help - Show this help\n\n"
        "Admin only:\n"
        "/updategift <link>\n/getgift\n/resetads\n"
        "/broadcast <msg>\n/setmode <monetag|promo>\n"
        "/switchmode\n/setpromo <link>\n/currentmode\n/status"
    )
    await update.message.reply_text(text)

async def echo_logger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"{update.effective_user.id}: {update.message.text}")
    await update.message.reply_text("✅ Received.")

# -------------------- RUN FLASK --------------------
def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

# -------------------- MAIN --------------------
def main():
    threading.Thread(target=run_flask, daemon=True).start()
    logger.info("Flask running.")
    app_tg = ApplicationBuilder().token(TOKEN).build()

    app_tg.add_handler(CommandHandler("start", start))
    app_tg.add_handler(CommandHandler("updategift", updategift))
    app_tg.add_handler(CommandHandler("getgift", getgift))
    app_tg.add_handler(CommandHandler("resetads", resetads))
    app_tg.add_handler(CommandHandler("broadcast", broadcast))
    app_tg.add_handler(CommandHandler("setmode", setmode))
    app_tg.add_handler(CommandHandler("switchmode", switchmode))
    app_tg.add_handler(CommandHandler("setpromo", setpromo))
    app_tg.add_handler(CommandHandler("currentmode", currentmode))
    app_tg.add_handler(CommandHandler("status", status))
    app_tg.add_handler(CommandHandler("help", help_cmd))
    app_tg.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo_logger))

    logger.info("Bot polling...")
    app_tg.run_polling()

if __name__ == "__main__":
    main()
    
