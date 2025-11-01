import os
import logging
import threading
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from flask import Flask, render_template_string, request
from markupsafe import Markup

TOKEN = "8103309728:AAGKsck7UMUmfjucRRNoEcc3YFazhvz_u3I"
JOIN_CHANNEL_LINK = "https://t.me/gsf8mqOl0atkMTM0"
ADMIN_ID = 5236441213  # Sunday Kehinde Akinade

# -------------------- Logging --------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# -------------------- Files --------------------
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

# -------------------- Flask App --------------------
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Telegram Ad Bot is running successfully."

@app.route("/user/<int:user_id>")
def show_progress(user_id):
    current_mode = get_mode()
    promo_link = get_promo_link()
    user_progress = ad_count.get(user_id, 0)
    total_ads = 5
    monet
