# script.py
from pyrogram import Client
import os
from dotenv import load_dotenv

load_dotenv()
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Flask setup
from flask import Flask
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "Flask server is running."

def run_flask():
    flask_app.run(host="0.0.0.0", port=5000)

def run_bot():
    app.run()
    print("Stopped\n")
