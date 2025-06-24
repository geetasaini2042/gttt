from pyrogram import Client
import os
from config import save_mongodb_data_to_file
import os
import json
from pymongo import MongoClient
from flask import Flask, request, jsonify,abort
from bson import json_util
from common_data import data_file, API_ID, API_HASH,BOT_TOKEN, MD_URI, BASE_PATH
import requests 
app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

flask_app = Flask(__name__)


@flask_app.route("/get-file/<path:filename>")
def get_json_file(filename):
    # Ensure file ends with .json
    if not filename.endswith(".json"):
        return abort(400, "Only .json files are allowed.")

    file_path = os.path.join(BASE_PATH, filename)

    # Security: prevent path traversal (../../etc/passwd)
    if not os.path.abspath(file_path).startswith(BASE_PATH):
        return abort(403, "Access Denied.")

    if not os.path.exists(file_path):
        return abort(404, "File not found.")

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return abort(500, f"Error reading file: {str(e)}")


@flask_app.route("/upload-data", methods=["GET", "POST"])
def handle_data():
    # File check and creation if not exists
    client = MongoClient(MD_URI)
    db = client["bot_database"]
    collection = db["bot_data_collection"]
    if not os.path.exists(data_file):
        with open(data_file, "w") as f:
            json.dump(DEFAULT_JSON, f, indent=2)

    # Load data from file
    try:
        with open(data_file, "r") as f:
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
@flask_app.route("/save-to-mongodb-from-file", methods=["GET"])
def save_to_mongodb():
    try:
        # JSON फाइल से डेटा पढ़ना
        with open(data_file, "r", encoding="utf-8") as f:
            file_data = json.load(f)

        # MongoDB कनेक्शन
        client = MongoClient(MD_URI)
        db = client["bot_database"]
        collection = db["bot_data_collection"]

        # MongoDB में सेव करना
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
        return jsonify({
            "status": "error",
            "message": "MongoDB insert failed",
            "error": str(e)
        }), 500
@flask_app.route("/save-from-mongodb-to-file")
def savindtogilr():
  save_mongodb_data_to_file()
  return "Saved Successfully"

@flask_app.route("/get-mongodb-data", methods=["GET"])
def get_all_data():
    client = MongoClient(MD_URI)
    db = client["bot_database"]
    collection = db["bot_data_collection"]
    try:
        # सभी डॉक्स को लाओ
        data = list(collection.find({}))
        return json_util.dumps({"status": "success", "data": data}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@flask_app.route("/")
def home():
    return "Flask server is running."


def run_flask():
    flask_app.run(host="0.0.0.0", port=5000)

import os
from dotenv import load_dotenv

load_dotenv()  # यह .env फ़ाइल लोड करता है

def run_bot():
    is_termux = os.getenv("is_termux", "false").lower() == "true"

    if not is_termux:
        save_mongodb_data_to_file()
    app.run()
    if not is_termux:
      requests.post("https://botbuilder-6861.onrender.com/upload-data")
    print("Stopped\n")
def get_created_by_from_folder(folder_id):
    try:
        with open(data_file) as f:
            bot_data = json.load(f)
    except:
        return None

    def find_created_by(folder):
        if folder.get("id") == folder_id and folder.get("type") == "folder":
            return folder.get("created_by")
        for item in folder.get("items", []):
            if item.get("type") == "folder":
                result = find_created_by(item)
                if result is not None:
                    return result
        return None

    root = bot_data.get("data", {})
    return find_created_by(root)

def is_user_action_allowed(folder_id, action):
    try:
        with open(data_file) as f:
            data = json.load(f)
    except:
        return False

    def find_folder(folder):
        if folder.get("id") == folder_id and folder.get("type") == "folder":
            return folder
        for item in folder.get("items", []):
            if item.get("type") == "folder":
                result = find_folder(item)
                if result:
                    return result
        return None

    root = data.get("data", {})
    folder = find_folder(root)
    if not folder:
        return False

    return action in folder.get("user_allow", [])
