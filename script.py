from pyrogram import Client
import os, json
from config import save_mongodb_data_to_file ,find_parent_of_parent,save_mongodb_users_to_file,is_user_subscribed_requests,upload_json_to_mongodb, download_from_mongodb
from pymongo import MongoClient
from flask import Flask, request, jsonify,abort
from bson import json_util
from common_data import data_file,data_file1, API_ID, API_HASH,BOT_TOKEN, MD_URI, BASE_PATH,DEPLOY_URL,users_file, LIKED_FILE, DISLIKED_FILE, PDF_VIEWS_FILE, DELETED_PDF_FILE, pre_file,WITHDRAW_FILE, GROUP_WEL_FILE
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
# 🔹 Logging setup

logger = logging.getLogger(__name__)


def safe_read_json(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        fcntl.flock(f, fcntl.LOCK_SH)  # shared lock for read
        data = json.load(f)
        fcntl.flock(f, fcntl.LOCK_UN)
    return data

def save_withdrawals_to_file():
    client = MongoClient(MD_URI)
    db = client["bot_database"]
    collection = db["withdrawals"]

    # MongoDB से सारे documents निकालो
    all_data = collection.find()

    # File format जैसा चाहिए वैसा dict बनाओ
    file_data = {}
    for doc in all_data:
        user_id = doc.get("user_id")
        if not user_id:
            continue

        file_data[user_id] = {
            "total_withdrawn": int(doc.get("total_withdrawn_inr", 0)),  # INR में total निकलेगा
            "requests": doc.get("requests", [])
        }

    # JSON file में save करो
    with open(WITHDRAW_FILE, "w") as f:
        json.dump(file_data, f, indent=2)

    logging.info(f"✅ Withdrawals data saved to {WITHDRAW_FILE}")
    
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

def save_group_settings_json_to_mongodb():
    """
    JSON फ़ाइल की पूरी content MongoDB में save करता है।
    हर group ID को अलग document की तरह insert/update करेगा।

    Args:
        json_file_path (str): JSON फ़ाइल का path
        MD_URI (str): MongoDB URI
        collection_name (str): Collection का नाम (default: "group_settings")
    """

    # 🔹 JSON फाइल पढ़ना
    json_file_path = GROUP_WEL_FILE
    collection_name = "group_settings"
    try:
        with open(json_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        logger.info("📁 JSON फ़ाइल सफलतापूर्वक पढ़ ली गई।")
    except Exception as e:
        logger.error(f"❌ JSON फ़ाइल पढ़ने में गलती: {e}")
        return

    # 🔹 MongoDB से कनेक्ट होना
    try:
        client = MongoClient(MD_URI)
        db = client["bot_database"]
        collection = db[collection_name]
        logger.info("✅ MongoDB से सफलतापूर्वक कनेक्ट हो गया।")
    except Exception as e:
        logger.error(f"❌ MongoDB से कनेक्ट नहीं हो पाया: {e}")
        return

    # 🔹 Common info सेव करना
    common_info = data.get("common_info", {})
    if common_info:
        collection.update_one(
            {"_id": "common_info"},
            {"$set": {"data": common_info}},
            upsert=True
        )
        logger.info("ℹ️ Common info MongoDB में सेव कर दिया गया।")

    # 🔹 बाकी groups सेव करना
    for group_id, group_data in data.items():
        if group_id == "common_info":
            continue
        try:
            collection.update_one(
                {"_id": group_id},
                {"$set": group_data},
                upsert=True
            )
            logger.info(f"✅ Group {group_id} का डेटा MongoDB में सेव किया गया।")
        except Exception as e:
            logger.warning(f"⚠️ Group {group_id} को सेव करते समय गलती: {e}")

    client.close()
    logger.info("🎯 सभी डेटा सफलतापूर्वक MongoDB में सेव हो गए।")


def export_group_settings_mongodb_to_json():
    """
    MongoDB collection से सभी data पढ़कर JSON फाइल में save करता है।

    Args:
        MD_URI (str): MongoDB URI
        json_file_path (str): Output JSON file path
        collection_name (str): Collection का नाम (default: "group_settings")
    """

    # 🔹 MongoDB से connect
    json_file_path = GROUP_WEL_FILE
    collection_name = "group_settings"
    try:
        client = MongoClient(MD_URI)
        db = client["bot_database"]
        collection = db[collection_name]
        logger.info("✅ MongoDB से सफलतापूर्वक कनेक्ट हो गया।")
    except Exception as e:
        logger.error(f"❌ MongoDB से कनेक्ट नहीं हो पाया: {e}")
        return

    # 🔹 सभी documents पढ़ना
    try:
        data = {}
        for doc in collection.find({}):
            _id = doc.get("_id")
            doc_copy = doc.copy()
            doc_copy.pop("_id", None)  # Remove MongoDB _id
            data[_id] = doc_copy
        logger.info(f"📁 {len(data)} documents MongoDB से पढ़ लिए गए।")
    except Exception as e:
        logger.error(f"❌ MongoDB से data पढ़ने में गलती: {e}")
        return
    finally:
        client.close()

    # 🔹 JSON फाइल में save करना
    try:
        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logger.info(f"🎯 सभी डेटा JSON फाइल '{json_file_path}' में सफलतापूर्वक save हो गए।")
    except Exception as e:
        logger.error(f"❌ JSON फाइल में save करते समय गलती: {e}")
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
    
def export_all_to_json():
    client = MongoClient(MD_URI)
    db = client["bot_database"]
    collection = db["reactions"]

    try:
        liked_data = {}
        disliked_data = {}
        pdf_views_data = {}

        for doc in collection.find():
            uuid = doc.get("uuid")
            likes = doc.get("likes", [])
            dislikes = doc.get("dislikes", [])
            views = doc.get("views", [])  # Assuming views stored as list in MongoDB

            liked_data[uuid] = likes
            disliked_data[uuid] = dislikes
            pdf_views_data[uuid] = views

        # Write liked.json
        os.makedirs(os.path.dirname(LIKED_FILE), exist_ok=True)
        with open(LIKED_FILE, "w", encoding="utf-8") as f:
            json.dump(liked_data, f, indent=4, ensure_ascii=False)
        logging.info("✅ liked.json saved successfully.")

        # Write disliked.json
        with open(DISLIKED_FILE, "w", encoding="utf-8") as f:
            json.dump(disliked_data, f, indent=4, ensure_ascii=False)
        logging.info("✅ disliked.json saved successfully.")

        # Write PDF_VIEWS_FILE.json
        with open(PDF_VIEWS_FILE, "w", encoding="utf-8") as f:
            json.dump(pdf_views_data, f, indent=4, ensure_ascii=False)
        logging.info("✅ PDF_VIEWS_FILE.json saved successfully.")

    except Exception as e:
        logging.error(f"❌ Failed to export reactions/views: {e}")

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

def load_json1_files_from_mongo():

    # MongoDB client
    client = MongoClient(MD_URI)
    db = client["bot_database"]

    # ---- pre_files_over.json load ----
    pre_data = {}
    for doc in db["pre_files_over"].find({}):
        owner_id = str(doc.get("owner_id"))
        file_ids = doc.get("file_ids", [])
        pre_data[owner_id] = file_ids

    with open(pre_file, "w") as f:
        json.dump(pre_data, f, indent=2)
    logging.info("✅ pre_files_over.json loaded from MongoDB")

    # ---- deleted_user_files.json load ----
    deleted_data = {}
    for doc in db["deleted_user_files"].find({}):
        user_id = str(doc.get("user_id"))
        file_ids = doc.get("file_ids", [])
        deleted_data[user_id] = file_ids

    with open(DELETED_PDF_FILE, "w") as f:
        json.dump(deleted_data, f, indent=2)
    logging.info("✅ deleted_user_files.json loaded from MongoDB")
    
def run_bot():
    is_termux = os.getenv("is_termux", "false").lower() == "true"

    if not is_termux:
        export_all_to_json()
        save_mongodb_users_to_file()
        save_mongodb_data_to_file()
        download_from_mongodb()
        load_json1_files_from_mongo()
        save_withdrawals_to_file()
        export_group_settings_mongodb_to_json()
    app.run()
    if not is_termux:
      requests.post(DEPLOY_URL)
      upload_users()
      upload_json_to_mongodb()
      save_json_files_to_mongo()
      save_group_settings_json_to_mongodb
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
