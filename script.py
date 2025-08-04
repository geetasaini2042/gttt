from pyrogram import Client
import os, json
from config import save_mongodb_data_to_file ,find_parent_of_parent,save_mongodb_users_to_file,is_user_subscribed_requests,upload_json_to_mongodb, download_from_mongodb
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
from flask import Flask, request, render_template_string, redirect, url_for
flask_app = Flask(__name__)


import fcntl

def safe_read_json(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        fcntl.flock(f, fcntl.LOCK_SH)  # shared lock for read
        data = json.load(f)
        fcntl.flock(f, fcntl.LOCK_UN)
    return data

@flask_app.route("/get-file/<path:filename>")
def get_json_file(filename):
    if not filename.endswith(".json"):
        return abort(400, "Only .json files are allowed.")

    file_path = os.path.join(BASE_PATH, filename)

    if not os.path.abspath(file_path).startswith(BASE_PATH):
        return abort(403, "Access Denied.")

    if not os.path.exists(file_path):
        return abort(404, "File not found.")

    try:
        data = safe_read_json(file_path)
        return jsonify(data)
    except Exception as e:
        return abort(500, f"Error reading file: {str(e)}")
@flask_app.route("/upload-users", methods=["POST"])
def upload_users():
    try:
        client = MongoClient(MD_URI)
        db = client["bot_database"]
        users_collection = db["users_collection"]

        with open(users_file, "r") as f:
            users_data = json.load(f)

        result = users_collection.update_one(
            {"type": "userlist"},
            {"$set": {"type": "userlist", "users": users_data}},
            upsert=True
        )

        return {
            "status": "success",
            "message": "users.json data saved to MongoDB",
            "matched_count": result.matched_count,
            "modified_count": result.modified_count,
            "upserted_id": str(result.upserted_id) if result.upserted_id else None
        }, 200

    except Exception as e:
        return {
            "status": "error",
            "message": "Failed to upload users.json to MongoDB",
            "error": str(e)
        }, 500
#Safe file write ---
def safe_write_json(filepath, data):
    with open(filepath, "w") as f:
        fcntl.flock(f, fcntl.LOCK_EX)  # exclusive lock
        json.dump(data, f, indent=2)
        fcntl.flock(f, fcntl.LOCK_UN)
import os
import json
import fcntl
import logging
from pymongo import MongoClient

logger = logging.getLogger("mongo_sync")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

def save_data_file_to_mongo():
    client = MongoClient(MD_URI)
    db = client["bot_database"]
    collection1 = db["bot_data_collection"]

    # अगर फ़ाइल नहीं है तो safe create करना है (with lock)
    if not os.path.exists(data_file):
        try:
            with open(data_file, "w") as f:
                fcntl.flock(f, fcntl.LOCK_EX)
                json.dump(DEFAULT_JSON, f, indent=2, ensure_ascii=False)
                fcntl.flock(f, fcntl.LOCK_UN)
            logger.info("✅ Created default JSON file: %s", data_file)
        except Exception as e:
            logger.error("❌ Failed to create/write default JSON: %s | Error: %s", data_file, str(e))
            return

    try:
        with open(data_file, "r") as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            file_data = json.load(f)
            fcntl.flock(f, fcntl.LOCK_UN)
        logger.info("📥 Read local JSON file: %s", data_file)
    except Exception as e:
        logger.error("❌ Failed to read JSON: %s | Error: %s", data_file, str(e))
        return

    try:
        existing = collection1.find_one({"data.id": file_data["data"]["id"]})
        update_fields = {}

        if existing:
            existing_copy = dict(existing)
            existing_copy.pop("_id", None)

            for key in file_data:
                if key not in existing_copy or file_data[key] != existing_copy[key]:
                    update_fields[key] = file_data[key]
        else:
            update_fields = file_data

        if not update_fields:
            logger.info("🟡 No changes detected for ID %s — nothing updated.", file_data["data"]["id"])
            return

        result = collection1.update_one(
            {"data.id": file_data["data"]["id"]},
            {"$set": update_fields},
            upsert=True
        )

        logger.info(
            "✅ MongoDB updated for ID %s | Updated fields: %s | Matched: %d | Modified: %d | Upserted ID: %s",
            file_data["data"]["id"],
            list(update_fields.keys()),
            result.matched_count,
            result.modified_count,
            str(result.upserted_id) if result.upserted_id else "None"
        )

    except Exception as e:
        logger.error("❌ MongoDB update failed for ID %s | Error: %s", file_data["data"]["id"], str(e))
def save_data_file1_to_mongo():
    client = MongoClient(MD_URI)
    db = client["bot_database"]
    collection2 = db["bot_data_collection_1"]

    if not os.path.exists(data_file1):
        safe_write_json(data_file1, DEFAULT_JSON)

    try:
        file_data1 = safe_read_json(data_file1)
    except Exception as e:
        return {
            "status": "error",
            "message": "Failed to read local JSON (data_file1)",
            "error": str(e)
        }

    try:
        result = collection2.update_one(
            {"data.id": file_data1["data"]["id"]},
            {"$set": file_data1},
            upsert=True
        )
        return {
            "status": "success",
            "message": "data_file1 saved to MongoDB",
            "result": {
                "matched_count": result.matched_count,
                "modified_count": result.modified_count,
                "upserted_id": str(result.upserted_id) if result.upserted_id else None
            }
        }
    except Exception as e:
        return {
            "status": "error",
            "message": "MongoDB insert failed (data_file1)",
            "error": str(e)
        }
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
import vip_file
@flask_app.route("/upload_app123")
def upload_app123():
  is_termux = os.getenv("is_termux", "false").lower() == "true"
  if not is_termux:
    upload_users()
    upload_json_to_mongodb()
    return "uploded"


BASE_PATH = os.path.dirname(os.path.abspath(__file__))

HTML_TEMPLATE = '''
<h2>Edit JSON File: {{ filename }}</h2>
<form method="POST">
    <textarea name="json_data" rows="20" cols="100">{{ json_data }}</textarea><br><br>
    <input type="submit" value="Save Changes">
</form>
'''

@flask_app.route('/edit-data/<filename>', methods=['GET', 'POST'])
def edit_data(filename):
    filepath = os.path.join(BASE_PATH, filename)

    if not os.path.exists(filepath):
        return f"File {filename} does not exist.", 404

    if request.method == 'POST':
        try:
            # Parse and write JSON
            new_data = json.loads(request.form['json_data'])
            with open(filepath, 'w') as f:
                json.dump(new_data, f, indent=4)
            return redirect(url_for('edit_data', filename=filename))
        except json.JSONDecodeError:
            return "Invalid JSON format!", 400

    with open(filepath, 'r') as f:
        data = json.load(f)

    return render_template_string(HTML_TEMPLATE, json_data=json.dumps(data, indent=4), filename=filename)

@flask_app.route("/")
def home():
    return "Flask server is running."



import os
from dotenv import load_dotenv

load_dotenv()  # यह .env फ़ाइल लोड करता है

def run_bot():
    is_termux = os.getenv("is_termux", "false").lower() == "true"

    if not is_termux:
        save_mongodb_users_to_file()
        save_mongodb_data_to_file()
        download_from_mongodb()
    app.run()
    if not is_termux:
      requests.post(DEPLOY_URL)
      upload_users()
      upload_json_to_mongodb()
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
@flask_app.route("/save-admin-to-mongodb-data", methods=["GET"])
def upload_json_admin_blocked_to_md():
  upload_json_to_mongodb()
  
def run_flask():
    flask_app.run(host="0.0.0.0", port=5000)
