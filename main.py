import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from flask import Flask, render_template_string
import threading

TOKEN = "8103309728:AAH-lGTT6KXIb9Qu5pMnA1qgiKottnugoKw"

# Read gift link from gift.txt
def get_gift_link():
    try:
        with open("gift.txt", "r") as f:
            return f.read().strip()
    except:
        return "https://example.com"

JOIN_CHANNEL_LINK = "https://t.me/gsf8mqOl0atkMTM0"
ad_count = {}  # user_id: count

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
            background: #f4f4f4;
            text-align: center;
            padding: 20px;
        }
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
            background-color: #ddd;
        }
        .circle.active {
            background-color: #4CAF50;
        }
        .btn {
            background: #4CAF50;
            color: #fff;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
        }
        .gift {
            display: none;
            margin-top: 20px;
        }
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
        <div class="circle"></div>
        <div class="circle"></div>
        <div class="circle"></div>
        <div class="circle"></div>
        <div class="circle"></div>
    </div>

    <button class="btn" id="watchAd">Watch Ad</button>
    <div class="gift" id="giftSection">
        <p>🎁 Congratulations! You’ve unlocked your reward!</p>
        <a id="giftLink" href="#" target="_blank">Get Gift</a>
        <br><br>
        <a href="https://t.me/gsf8mqOl0atkMTM0" target="_blank">📢 Join our Telegram Channel</a>
    </div>

    <!-- Monetag Ad Script -->
    <script src='//libtl.com/sdk.js' data-zone='10089898' data-sdk='show_10089898'></script>

    <script>
        let count = 0;
        const circles = document.querySelectorAll('.circle');
        const giftSection = document.getElementById('giftSection');
        const giftLink = document.getElementById('giftLink');

        // This loads the gift URL dynamically from gift.txt on your server
        async function getGiftLink() {
            const response = await fetch('/gift.txt');
            const link = await response.text();
            giftLink.href = link.trim();
        }

        document.getElementById('watchAd').addEventListener('click', async () => {
            // Show Monetag Ad
            if (typeof show_10089898 === "function") {
                show_10089898();
            } else {
                alert("Ad is loading... please wait a few seconds and try again.");
                return;
            }

            count++;
            circles[count - 1].classList.add('active');

            if (count >= 5) {
                await getGiftLink();
                giftSection.style.display = 'block';
            }
        });
    </script>
</body>
</html>
"""

# Flask app for the webpage
app = Flask(__name__)

@app.route('/user/<int:user_id>')
def show_progress(user_id):
    count = ad_count.get(user_id, 0)
    return render_template_string(HTML_PAGE, count=count, user_id=user_id,
                                  gift_url=get_gift_link(), join_url=JOIN_CHANNEL_LINK)

@app.route('/watch/<int:user_id>')
def watch_ad(user_id):
    ad_count[user_id] = ad_count.get(user_id, 0) + 1
    return f"<meta http-equiv='refresh' content='2;url=/user/{user_id}'>Watching ad... (mock)"

# Telegram Bot logic
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ad_count[user_id] = 0
    keyboard = [[InlineKeyboardButton("🎬 Start Watching Ads", url=f"{os.environ.get('RENDER_EXTERNAL_URL','http://localhost:5000')}/user/{user_id}")]]
    await update.message.reply_text("Welcome! Watch ads to unlock your gift 🎁", reply_markup=InlineKeyboardMarkup(keyboard))

def run_flask():
    app.run(host='0.0.0.0', port=5000)

def main():
    threading.Thread(target=run_flask).start()
    bot = ApplicationBuilder().token(TOKEN).build()
    bot.add_handler(CommandHandler("start", start))
    bot.run_polling()

if __name__ == "__main__":
    main()
                
