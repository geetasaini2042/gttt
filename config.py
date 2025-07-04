import os
import json
import logging
from pymongo import MongoClient
from flask import Flask, request, jsonify
from common_data import data_file,data_file1, MD_URI, DEFAULT_JSON,users_file

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
    # You can add filename='log.txt' if you want to save logs in a file
)

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