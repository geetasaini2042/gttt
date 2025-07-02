from pyrogram import Client
import os
from config import save_mongodb_data_to_file ,find_parent_of_parent,save_mongodb_users_to_file
import os
import json
from pymongo import MongoClient
from flask import Flask, request, jsonify,abort
from bson import json_util
from common_data import data_file,data_file1, API_ID, API_HASH,BOT_TOKEN, MD_URI, BASE_PATH,DEPLOY_URL,users_file
import requests 
app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
    # You can add filename='log.txt' if you want to save logs in a file
)
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

@flask_app.route("/upload-users", methods=["POST"])
def upload_users():
    try:
        # MongoDB
        client = MongoClient(MD_URI)
        db = client["bot_database"]
        users_collection = db["users_collection"]

        # load local file
        with open(users_file, "r") as f:
            users_data = json.load(f)

        # save to MongoDB
        result = users_collection.update_one(
            {"type": "userlist"},
            {"$set": {"type": "userlist", "users": users_data}},
            upsert=True
        )

        return jsonify({
            "status": "success",
            "message": "users.json data saved to MongoDB",
            "matched_count": result.matched_count,
            "modified_count": result.modified_count,
            "upserted_id": str(result.upserted_id) if result.upserted_id else None
        })
    except Exception as e:
        return jsonify({"status": "error", "message": "Failed to upload users.json to MongoDB", "error": str(e)}), 500
@flask_app.route("/upload-data", methods=["GET", "POST"])
def handle_data():
    # MongoDB client
    client = MongoClient(MD_URI)
    db = client["bot_database"]
    collection1 = db["bot_data_collection"]   # for data_file
    collection2 = db["bot_data_collection_1"] # for data_file1

    # Files check and create if missing
    if not os.path.exists(data_file):
        with open(data_file, "w") as f:
            json.dump(DEFAULT_JSON, f, indent=2)

    if not os.path.exists(data_file1):
        with open(data_file1, "w") as f:
            json.dump(DEFAULT_JSON, f, indent=2)

    # Load both files
    try:
        with open(data_file, "r") as f:
            file_data = json.load(f)
    except Exception as e:
        return jsonify({"status": "error", "message": "Failed to read local JSON (data_file)", "error": str(e)}), 500

    try:
        with open(data_file1, "r") as f:
            file_data1 = json.load(f)
    except Exception as e:
        return jsonify({"status": "error", "message": "Failed to read local JSON (data_file1)", "error": str(e)}), 500

    if request.method == "GET":
        try:
            db_data1 = collection1.find_one({"data.id": "root"})
            db_data2 = collection2.find_one({"data.id": "root"})

            # convert ObjectIds to string
            if db_data1:
                db_data1["_id"] = str(db_data1["_id"])
            if db_data2:
                db_data2["_id"] = str(db_data2["_id"])

            return jsonify({
                "status": "success",
                "source": "mongodb",
                "data_file": db_data1 if db_data1 else file_data,
                "data_file1": db_data2 if db_data2 else file_data1
            })
        except Exception as e:
            return jsonify({"status": "error", "message": "MongoDB fetch failed", "error": str(e)}), 500

    elif request.method == "POST":
        try:
            result1 = collection1.update_one(
                {"data.id": file_data["data"]["id"]},
                {"$set": file_data},
                upsert=True
            )
            result2 = collection2.update_one(
                {"data.id": file_data1["data"]["id"]},
                {"$set": file_data1},
                upsert=True
            )
            return jsonify({
                "status": "success",
                "message": "Data saved to MongoDB",
                "data_file": {
                    "matched_count": result1.matched_count,
                    "modified_count": result1.modified_count,
                    "upserted_id": str(result1.upserted_id) if result1.upserted_id else None
                },
                "data_file1": {
                    "matched_count": result2.matched_count,
                    "modified_count": result2.modified_count,
                    "upserted_id": str(result2.upserted_id) if result2.upserted_id else None
                }
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
    upload_users()
    return "Flask server is running."


def run_flask():
    flask_app.run(host="0.0.0.0", port=5000)

import os
from dotenv import load_dotenv

load_dotenv()  # यह .env फ़ाइल लोड करता है

def run_bot():
    is_termux = os.getenv("is_termux", "false").lower() == "true"

    if not is_termux:
        save_mongodb_users_to_file()
        save_mongodb_data_to_file()
    app.run()
    if not is_termux:
      requests.post(DEPLOY_URL)
      upload_users()
    logging.info("Stopped\n")
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
