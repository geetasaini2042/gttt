from pyrogram import Client
import os
from dotenv import load_dotenv
from config import save_mongodb_data_to_file
load_dotenv()
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
import os
import json
from pymongo import MongoClient
from flask import Flask, request, jsonify
# MongoDB Setup
client = MongoClient("mongodb+srv://pankajsainikishanpura02:SHivxQzJdLrvbA9M@cluster0.tftxnvm.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
db = client["bot_database"]
collection = db["bot_data_collection"]

# File Path
BOTES_DATA_FILE = "/storage/emulated/0/BotBuilder/PYTHON/botes_data.json"

# Default structure (same as earlier)
DEFAULT_JSON = {
    "data": {
        "id": "root",
        "name": "Root",
        "description": "Welcome to PDF Hub.",
        "type": "folder",
        "created_by": 6150091802,
        "parent_id": None,
        "user_allow": [
            "add_file",
            "add_folder",
            "add_url",
            "add_webapp"
        ],
        "items": []
    }
}
from flask import Flask
flask_app = Flask(__name__)

@flask_app.route("/upload-data", methods=["GET", "POST"])
def handle_data():
    # File check and creation if not exists
    if not os.path.exists(JSON_FILE_PATH):
        with open(JSON_FILE_PATH, "w") as f:
            json.dump(DEFAULT_JSON, f, indent=2)

    # Load data from file
    try:
        with open(JSON_FILE_PATH, "r") as f:
            file_data = json.load(f)
    except Exception as e:
        return jsonify({"status": "error", "message": "Failed to read local JSON", "error": str(e)}), 500

    if request.method == "GET":
        # Try to get from MongoDB
        try:
            db_data = collection.find_one({"data.id": "root"})
            if db_data:
                db_data["_id"] = str(db_data["_id"])  # Convert ObjectId to str
                return jsonify({"status": "success", "source": "mongodb", "data": db_data})
            else:
                return jsonify({"status": "success", "source": "file", "data": file_data})
        except Exception as e:
            return jsonify({"status": "error", "message": "MongoDB fetch failed", "error": str(e)}), 500

    elif request.method == "POST":
        # Save to MongoDB
        try:
            result = collection.update_one(
                {"data.id": file_data["data"]["id"]},
                {"$set": file_data},
                upsert=True
            )
            return jsonify({
                "status": "success",
                "message": "Data saved to MongoDB",
                "matched_count": result.matched_count,
                "modified_count": result.modified_count,
                "upserted_id": str(result.upserted_id) if result.upserted_id else None
            })
        except Exception as e:
            return jsonify({"status": "error", "message": "MongoDB insert failed", "error": str(e)}), 500
@flask_app.route("/")
def home():
    return "Flask server is running."
def run_flask():
    flask_app.run(host="0.0.0.0", port=5000)

def run_bot():
    save_mongodb_data_to_file
    app.run()
    print("Stopped\n")
    
