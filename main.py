from flask import Flask
from telegram.ext import ApplicationBuilder, CommandHandler
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Telegram Ad Bot is running on Render!"

def main():
    TOKEN = "YOUR_BOT_TOKEN"
    bot = ApplicationBuilder().token(TOKEN).build()
    # Example simple handler
    async def start(update, context):
        await update.message.reply_text("Hello! I’m alive on Render 🚀")
    bot.add_handler(CommandHandler("start", start))
    bot.run_polling()

if __name__ == "__main__":
    # ✅ Important: Bind to the correct port for Render
    port = int(os.environ.get("PORT", 10000))
    # Run the web server in a thread-safe way
    from threading import Thread
    Thread(target=main).start()
    app.run(host="0.0.0.0", port=port)
