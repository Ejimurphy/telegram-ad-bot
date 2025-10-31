# main.py
import os
import json
import threading
from flask import Flask, render_template_string, request, jsonify
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# ---------- CONFIG ----------
TOKEN = "8103309728:AAH-lGTT6KXIb9Qu5pMnA1qgiKottnugoKw"
ADMIN_ID = 5236441213  # your Telegram numeric ID

CONFIG_FILE = "config.json"
USER_FILE = "user_counts.json"

DEFAULT_CONFIG = {
    "mode": "monetag",  # "monetag" or "promo"
    "gift_link": "https://www.canva.com/brand/join?token=BrnBqEuFTwf7IgNrKWfy4A&br",
    "promo_link": "https://t.me/gsf8mqOl0atkMTM0",
    "zone_id": "10089898"
}

# ---------- Helpers ----------
def load_json(path, default):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        with open(path, "w") as f:
            json.dump(default, f, indent=2)
        return default

def save_json(path, obj):
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)

config = load_json(CONFIG_FILE, DEFAULT_CONFIG)
user_counts = load_json(USER_FILE, {})  # { "<user_id>": {"count": n} }

def get_count(uid):
    return user_counts.get(str(uid), {}).get("count", 0)

def increment_count(uid):
    key = str(uid)
    rec = user_counts.get(key, {"count":0})
    rec["count"] = rec.get("count", 0) + 1
    user_counts[key] = rec
    save_json(USER_FILE, user_counts)
    return rec["count"]

def reset_count(uid):
    key = str(uid)
    user_counts[key] = {"count": 0}
    save_json(USER_FILE, user_counts)

# ---------- Flask app (serves user pages) ----------
app = Flask(__name__)

# HTML template uses either Monetag or Promo depending on config["mode"]
PAGE_TEMPLATE = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Watch Ads</title>
<style>
  body{font-family:Segoe UI,Arial;background:#0b0b0b;color:#fff;display:flex;flex-direction:column;align-items:center;min-height:100vh;padding:24px}
  .container{max-width:420px;width:100%;background:#121217;border-radius:12px;padding:20px}
  h2{color:#fff;margin:6px 0 14px}
  .steps{display:flex;gap:8px;justify-content:center;margin-bottom:14px}
  .step{width:48px;height:36px;border-radius:10px;background:#333;display:flex;align-items:center;justify-content:center;font-weight:700}
  .step.done{background:linear-gradient(90deg,#f04,#6f4cff);box-shadow:0 8px 24px rgba(0,0,0,0.6);transform:translateY(-6px)}
  .btn{display:inline-block;padding:12px 18px;border-radius:10px;background:#6b00ff;color:#fff;text-decoration:none;font-weight:800;margin:6px 0;cursor:pointer}
  .btn disabled{opacity:.5;cursor:default}
  .gift{display:none;margin-top:12px}
  .gift a{display:inline-block;padding:10px 14px;background:#0abf7b;border-radius:10px;color:#fff;text-decoration:none;font-weight:800}
  .info{color:#cfd8dc;font-size:14px;margin-top:10px}
</style>
</head>
<body>
  <div class="container">
    <h2>🎬 Watch Ads / Complete Tasks</h2>

    <div class="steps" id="steps">
      {% for i in range(1,6) %}
        <div class="step {% if i <= count %}done{% endif %}" id="s{{i}}">{{ i }}</div>
      {% endfor %}
    </div>

    <div style="text-align:center;">
      {% if mode == 'monetag' %}
        <p class="info">Tap the button to open a Monetag ad. Wait until it finishes.</p>
        <button class="btn" id="watchBtn">▶ Watch Ad</button>
      {% else %}
        <p class="info">Tap the button to open the promo link. Close it and return here to confirm.</p>
        <a class="btn" id="promoBtn" href="{{ promo_link }}" target="_blank">👉 Open Promo Link</a>
      {% endif %}
    </div>

    <div class="gift" id="gift">
      <p style="margin:10px 0">🎁 Your reward is ready:</p>
      <a href="{{ gift_link }}" target="_blank">Open Gift</a>
      <div style="margin-top:10px"><a href="{{ join_channel }}" target="_blank" class="btn">📢 Join Channel</a></div>
    </div>

    <p class="info">Progress: <span id="countText">{{ count }}</span>/5</p>
  </div>

<!-- Monetag if mode == monetag -->
{% if mode == 'monetag' %}
<script src='//libtl.com/sdk.js' data-zone='{{ zone_id }}' data-sdk='show_{{ zone_id }}'></script>
{% endif %}

<script>
  const uid = {{ user_id }};
  let count = {{ count }};
  const required = 5;

  function updateUI(c){
    count = c;
    document.getElementById('countText').innerText = count;
    for(let i=1;i<=5;i++){
      const el = document.getElementById('s'+i);
      if(i <= count) el.classList.add('done'); else el.classList.remove('done');
    }
    if(count >= required){
      document.getElementById('gift').style.display = 'block';
    }
  }

  async function confirmToServer(){
    // call server to increment only when an ad/promo is actually completed
    const resp = await fetch('/ad_complete/' + uid, { method:'POST' });
    const j = await resp.json();
    if(j.status === 'ok') updateUI(j.count);
    else alert('Server error');
  }

  // Monetag mode: ensure SDK ready before enabling
  const watchBtn = document.getElementById('watchBtn');
  if(watchBtn){
    watchBtn.disabled = true;
    watchBtn.innerText = 'Loading ad...';
    // allow some time for SDK to load
    setTimeout(()=> {
      // if function available, enable button
      if(typeof window['show_{{ zone_id }}'] === 'function'){
        watchBtn.disabled = false;
        watchBtn.innerText = '▶ Watch Ad';
      } else {
        // still enable but show message
        watchBtn.disabled = false;
        watchBtn.innerText = '▶ Watch Ad';
      }
    }, 2500);

    watchBtn.addEventListener('click', async () => {
      watchBtn.disabled = true;
      watchBtn.innerText = 'Opening ad...';
      try {
        if(typeof window['show_{{ zone_id }}'] === 'function'){
          // call Monetag SDK and rely on user to close ad when done
          window['show_{{ zone_id }}']();
          // Wait a little, then confirm (best-effort)
          setTimeout(confirmToServer, 6000); // confirm after 6s — configurable
        } else {
          // fallback: open a new tab to Monetag zone (best-effort)
          window.open('https://libtl.com/zone/{{ zone_id }}','_blank');
          setTimeout(confirmToServer, 6000);
        }
      } catch(err){
        console.error(err);
        alert('Ad failed to open. Try again.');
      } finally {
        watchBtn.disabled = false;
        watchBtn.innerText = '▶ Watch Ad';
      }
    });
  }

  // Promo mode: user opens external link; we offer a "I returned" confirm click
  const promoBtn = document.getElementById('promoBtn');
  if(promoBtn){
    // add a small confirm button under promoBtn
    const confirmBtn = document.createElement('button');
    confirmBtn.className = 'btn';
    confirmBtn.style.display = 'block';
    confirmBtn.style.margin = '12px auto';
    confirmBtn.innerText = '✅ I returned — Confirm';
    confirmBtn.onclick = confirmToServer;
    promoBtn.parentNode.insertBefore(confirmBtn, promoBtn.nextSibling);
  }
</script>
</body>
</html>
"""

@app.route("/user/<int:user_id>")
def user_page(user_id):
    # render template with current count and config
    cnt = get_count(user_id)
    rendered = render_template_string(
        PAGE_TEMPLATE,
        user_id=user_id,
        count=cnt,
        mode=config.get("mode", "monetag"),
        gift_link=config.get("gift_link"),
        promo_link=config.get("promo_link"),
        zone_id=config.get("zone_id"),
        join_channel=config.get("promo_link")
    )
    return rendered

# Endpoint called by the page when an ad/promo is completed (client requests this)
@app.route("/ad_complete/<int:user_id>", methods=["POST"])
def ad_complete(user_id):
    newcount = increment_count(user_id)
    unlocked = newcount >= 5
    return jsonify({"status":"ok","count": newcount, "unlocked": unlocked})

@app.route("/gift")  # redirect to gift
def gift_redirect():
    return ("", 302, {"Location": config.get("gift_link")})

# ---------- Telegram Bot Handlers ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    reset_count(user_id)
    web = os.environ.get("RENDER_EXTERNAL_URL", f"http://localhost:{os.environ.get('PORT',5000)}")
    url = f"{web}/user/{user_id}"
    keyboard = [[InlineKeyboardButton("🎬 Open Ad / Promo Page", url=url)]]
    await update.message.reply_text("Welcome! Open the page below and follow the steps to unlock your gift.", reply_markup=InlineKeyboardMarkup(keyboard))

async def setadmode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Not authorized.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /setadmode monetag  OR  /setadmode promo")
        return
    m = context.args[0].lower()
    if m not in ("monetag","promo"):
        await update.message.reply_text("Mode must be 'monetag' or 'promo'.")
        return
    config["mode"] = m
    save_json(CONFIG_FILE, config)
    await update.message.reply_text(f"✅ Mode set to: {m}")

async def setgift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Not authorized.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /setgift https://example.com")
        return
    link = context.args[0]
    config["gift_link"] = link
    save_json(CONFIG_FILE, config)
    await update.message.reply_text(f"✅ Gift link updated:\n{link}")

async def setpromo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Not authorized.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /setpromo https://example.com")
        return
    link = context.args[0]
    config["promo_link"] = link
    save_json(CONFIG_FILE, config)
    await update.message.reply_text(f"✅ Promo link updated:\n{link}")

async def getmode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Current mode: {config.get('mode')}")

async def getgift(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Gift link: {config.get('gift_link')}")

# ---------- Run Flask and Bot ----------
def run_flask():
    port = int(os.environ.get("PORT", 5000))
    # bind to provided port
    app.run(host="0.0.0.0", port=port)

def main():
    # start flask in a thread so Render sees an open port
    threading.Thread(target=run_flask).start()

    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("setadmode", setadmode))
    application.add_handler(CommandHandler("setgift", setgift))
    application.add_handler(CommandHandler("setpromo", setpromo))
    application.add_handler(CommandHandler("getmode", getmode))
    application.add_handler(CommandHandler("getgift", getgift))

    application.run_polling()

if __name__ == "__main__":
    main()
    
