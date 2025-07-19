import os
import json
import logging
from pymongo import MongoClient
from flask import Flask, request, jsonify
from common_data import data_file,data_file1, MD_URI, DEFAULT_JSON,users_file,BOT_TOKEN,REQUIRED_CHANNELS,OWNER ,BLOCKED_FILE, ADMINS_FILE

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
    # You can add filename='log.txt' if you want to save logs in a file
)

import requests


def is_user_subscribed_requests(user_id):
    if not REQUIRED_CHANNELS.strip():
        return True

    channels = [ch.strip() for ch in REQUIRED_CHANNELS.split(",") if ch.strip()]
    if not channels:
        return True

    for channel in channels:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getChatMember"
        params = {
            "chat_id": channel,
            "user_id": user_id
        }

        try:
            res = requests.get(url, params=params)
            data = res.json()

            if not data.get("ok"):
                # ❗️Notify OWNER to add bot
                try:
                    notify_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                    text = f"❗️ Please add me to channel: {channel}"
                    requests.get(notify_url, params={"chat_id": OWNER, "text": text})
                except Exception as notify_err:
                    print("⚠️ Failed to notify owner:", notify_err)

                continue  # skip this channel but do not block user

            status = data["result"]["status"]
            if status in ["left", "kicked"]:
                return False  # user not subscribed

        except Exception as e:
            print(f"❌ Exception checking {channel}:", e)
            continue

    return True
    
def get_channel_invite_link(channel_id):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/exportChatInviteLink"
    params = {
        "chat_id": channel_id
    }

    try:
        response = requests.get(url, params=params)
        data = response.json()

        if data.get("ok"):
            return data["result"]  # ✅ Invite link
        else:
            print("❌ Error:", data.get("description"))
            return None
    except Exception as e:
        print("❌ Exception:", e)
        return None
def save_mongodb_users_to_file():
    try:
        # MongoDB
        client = MongoClient(MD_URI)
        db = client["bot_database"]
        users_collection = db["users_collection"]

        # fetch from MongoDB
        db_data = users_collection.find_one({"type": "userlist"})
        if db_data and "users" in db_data:
            data_to_save = db_data["users"]
            logging.info("✅ MongoDB users loaded successfully.")
        else:
            data_to_save = [1, 2, 3]
            logging.warning("⚠️ MongoDB में users नहीं मिले, default [1,2,3] इस्तेमाल किया गया।")

        # write to file
        with open(users_file, "w") as f:
            json.dump(data_to_save, f, indent=2)

        logging.info(f"✅ users.json saved successfully at {users_file}")

    except Exception as e:
        logging.error("❌ Error while saving MongoDB users to file: %s", e)

def save_mongodb_data_to_file():
    try:
        # MongoDB setup
        client = MongoClient(MD_URI)
        db = client["bot_database"]
        collection1 = db["bot_data_collection"]
        collection2 = db["bot_data_collection_1"]

        # ---- For data_file ----
        db_data1 = collection1.find_one({"data.id": "root"})
        if db_data1:
            db_data1.pop("_id", None)
            data_to_save1 = db_data1
            logging.info("✅ MongoDB data_file loaded successfully.")
        else:
            data_to_save1 = DEFAULT_JSON
            logging.warning("⚠️ MongoDB data_file में data नहीं मिला, default JSON इस्तेमाल किया गया।")

        os.makedirs(os.path.dirname(data_file), exist_ok=True)
        with open(data_file, "w") as f:
            json.dump(data_to_save1, f, indent=2)
        logging.info(f"✅ Data saved to file: {data_file}")

        # ---- For data_file1 ----
        db_data2 = collection2.find_one({"data.id": "root"})
        if db_data2:
            db_data2.pop("_id", None)
            data_to_save2 = db_data2
            logging.info("✅ MongoDB data_file1 loaded successfully.")
        else:
            data_to_save2 = DEFAULT_JSON
            logging.warning("⚠️ MongoDB data_file1 में data नहीं मिला, default JSON इस्तेमाल किया गया।")

        os.makedirs(os.path.dirname(data_file1), exist_ok=True)
        with open(data_file1, "w") as f:
            json.dump(data_to_save2, f, indent=2)
        logging.info(f"✅ Data saved to file: {data_file1}")

    except Exception as e:
        logging.error("❌ Error while saving MongoDB data to file: %s", e)
def find_parent_of_parent(root, folder_id):
    """
    kisi folder_id ka parent_id ka parent_id dhoondhe
    """
    if not root:
        return None

    # helper function
    def dfs(folder):
        for item in folder.get("items", []):
            if item.get("id") == folder_id:
                # ye current folder iska parent hai
                return folder.get("parent_id")
            found = dfs(item)
            if found:
                return found
        return None

    return dfs(root)
    
def upload_json_to_mongodb():
    try:
        client = MongoClient(MD_URI)
        db = client["bot_database"]

        # Collections
        collection1 = db["blocked_users"]
        collection2 = db["admins"]

        # --- Upload blocked_users.json ---
        try:
            with open(BLOCKED_FILE, "r") as f:
                blocked = json.load(f)

            collection1.delete_many({})  # Clear old data

            if isinstance(blocked, list):
                collection1.insert_many([{"user_id": uid} for uid in blocked])
                logging.info(f"✅ Uploaded {len(blocked)} blocked users to MongoDB.")
            else:
                logging.warning("⚠️ blocked_users.json format is invalid (not list)")

        except Exception as e:
            logging.error(f"❌ Error uploading blocked_users.json: {e}")

        # --- Upload admins.json ---
        try:
            with open(ADMINS_FILE, "r") as f:
                admins = json.load(f)

            collection2.delete_many({})

            if isinstance(admins, list):
                collection2.insert_many([{"admin_id": aid} for aid in admins])
                logging.info(f"✅ Uploaded {len(admins)} admins to MongoDB.")
            else:
                logging.warning("⚠️ admins.json format is invalid (not list)")

        except Exception as e:
            logging.error(f"❌ Error uploading admins.json: {e}")

    except Exception as e:
        logging.error(f"❌ MongoDB connection failed: {e}")


def download_from_mongodb():
    try:

        client = MongoClient(MD_URI)
        db = client["bot_database"]

        # Collections
        collection1 = db["blocked_users"]
        collection2 = db["admins"]

        # --- Blocked Users Sync ---
        try:
            blocked_cursor = collection1.find({})
            blocked_list = [doc["user_id"] for doc in blocked_cursor if "user_id" in doc]

            with open(BLOCKED_FILE, "w") as f:
                json.dump(blocked_list, f, indent=2)

            logging.info(f"✅ blocked_users.json saved with {len(blocked_list)} users.")

        except Exception as e:
            logging.error(f"❌ Failed to save blocked_users.json: {e}")

        # --- Admins Sync ---
        try:
            admins_cursor = collection2.find({})
            admins_list = [doc["admin_id"] for doc in admins_cursor if "admin_id" in doc]

            with open(ADMINS_FILE, "w") as f:
                json.dump(admins_list, f, indent=2)

            logging.info(f"✅ admins.json saved with {len(admins_list)} admins.")

        except Exception as e:
            logging.error(f"❌ Failed to save admins.json: {e}")

    except Exception as e:
        logging.error(f"❌ MongoDB connection failed: {e}")