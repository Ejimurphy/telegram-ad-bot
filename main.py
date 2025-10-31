import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from flask import Flask, render_template_string
import threading

TOKEN = "8103309728:AAH-lGTT6KXIb9Qu5pMnA1qgiKottnugoKw"
JOIN_CHANNEL_LINK = "https://t.me/gsf8mqOl0atkMTM0"
ADMIN_ID = 5236441213  # your Telegram ID

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
HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Watch Ads to Unlock Gift</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      background: #0f0f0f;
      color: #fff;
      text-align: center;
      padding: 30px;
    }
    h2 { color: #FFD700; }
    .progress {
      display: flex;
      justify-content: center;
      gap: 10px;
      margin: 20px 0;
    }
    .circle {
      width: 30px;
      height: 30px;
      border-radius: 50%;
      background-color: #333;
    }
    .circle.active { background-color: #00FF88; }
    .btn {
      background: #6200ea;
      color: #fff;
      border: none;
      padding: 14px 26px;
      border-radius: 10px;
      cursor: pointer;
      font-size: 18px;
      transition: 0.3s;
    }
    .btn:hover { background: #7b1ffa; }
    .gift { display: none; margin-top: 20px; }
    .gift a {
      background: #2196F3;
      color: #fff;
      padding: 10px 20px;
      border-radius: 8px;
      text-decoration: none;
    }
  </style>
</head>
<body>
  <h2>🎥 Watch 5 Ads to Unlock Your Gift!</h2>
  <div class="progress" id="progress">
    <div class="circle"></div><div class="circle"></div><div class="circle"></div><div class="circle"></div><div class="circle"></div>
  </div>

  <button class="btn" id="watchAd">🎬 Watch Ad</button>
  <div class="gift" id="giftSection">
    <p>🎁 Congratulations! You’ve unlocked your reward!</p>
    <a id="giftLink" href="#" target="_blank">Get Gift</a>
    <br><br>
    <a href="https://t.me/gsf8mqOl0atkMTM0" target="_blank">📢 Join our Telegram Channel</a>
  </div>

  <!-- Monetag Script -->
  <script src='//libtl.com/sdk.js' data-zone='10089898' data-sdk='show_10089898'></script>

  <script>
    let count = 0;
    const circles = document.querySelectorAll('.circle');
    const giftSection = document.getElementById('giftSection');
    const giftLink = document.getElementById('giftLink');
    const watchBtn = document.getElementById('watchAd');

    async function getGiftLink() {
      const res = await fetch('/gift.txt');
      const text = await res.text();
      giftLink.href = text.trim();
    }

    watchBtn.addEventListener('click', async () => {
      if (typeof show_10089898 === "function") {
        show_10089898();
      } else {
        alert("⏳ Please wait, ad still loading...");
        return;
      }

      watchBtn.disabled = true;
      watchBtn.textContent = "⏳ Watching Ad...";

      setTimeout(async () => {
        count++;
        circles[count - 1].classList.add('active');
        await fetch(`/verify_ad/${count}`, { method: "POST" });

        if (count >= 5) {
          await getGiftLink();
          giftSection.style.display = "block";
        }
        watchBtn.disabled = false;
        watchBtn.textContent = "🎬 Watch Ad";
      }, 10000);
    });
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
    return render_template_string(HTML_PAGE)

@app.route("/verify_ad/<int:count>", methods=["POST"])
def verify_ad(count):
    return "ok"

# -------------------- Telegram Commands --------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ad_count[user_id] = 0
    verified_users.discard(user_id)
    web_url = f"{os.environ.get('RENDER_EXTERNAL_URL', 'http://localhost:5000')}/user/{user_id}"
    keyboard = [[InlineKeyboardButton("🎬 Watch Ads", url=web_url)]]
    await update.message.reply_text("Welcome! Watch ads to unlock your gift 🎁", reply_markup=InlineKeyboardMarkup(keyboard))

async def updategift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to perform this action.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /updategift <new_link>")
        return

    new_link = context.args[0]
    update_gift_link(new_link)
    await update.message.reply_text(f"✅ Gift link updated to:\n{new_link}")

# -------------------- Run Both Flask & Bot --------------------
def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

def main():
    threading.Thread(target=run_flask).start()
    bot = ApplicationBuilder().token(TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.add_handler(CommandHandler("updategift", updategift))
    bot.run_polling()

if __name__ == "__main__":
    main()
