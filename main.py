import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from flask import Flask, render_template_string
import threading

TOKEN = "YOUR_BOT_TOKEN_HERE"

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
<html>
<head>
<title>Watch Ads</title>
<style>
body { font-family: Arial; text-align: center; background-color: #f9f9f9; padding: 30px; }
.tab { display: inline-block; width: 35px; height: 35px; margin: 5px; border-radius: 50%; background: #ccc; }
.active { background: #4CAF50; }
.btn { display: inline-block; background: #0088cc; color: white; padding: 10px 20px; margin-top: 20px;
       text-decoration: none; border-radius: 8px; font-weight: bold; }
</style>
</head>
<body>
<h2>🎁 Watch Ads to Unlock Gift</h2>
<div>
  {% for i in range(1,6) %}
    <div class="tab {% if i <= count %}active{% endif %}"></div>
  {% endfor %}
</div>
{% if count < 5 %}
  <p>Watch {{ 5 - count }} more ads to unlock your gift.</p>
  <a href="/watch/{{ user_id }}" class="btn">🎬 Watch Ad</a>
{% else %}
  <a href="{{ gift_url }}" class="btn">🎁 Access Gift</a>
  <a href="{{ join_url }}" class="btn" style="background: #25D366;">📢 Join Channel</a>
{% endif %}
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
                
