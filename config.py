import os
import json
from pymongo import MongoClient
from flask import Flask, request, jsonify
# 
# File Path
BOTES_DATA_FILE = "/opt/render/project/src/bot_data.json"
MD_URI = os.getenv("MONGODB_URI")
# Default structure (same as earlier)
DEFAULT_JSON = {
    "data": {
        "id": "root",
        "name": "Root",
        "description": "Welcome to PDF Hub.",
        "type": "folder",
        "created_by": 6150091802,
        "parent_id": None,
        "user_allow": [],
        "items": []
    }
}
def save_mongodb_data_to_file():
    try:
        # 1. Get data from MongoDB
        #MongoDB Setup
        client = MongoClient(MD_URI)
        db = client["bot_database"]
        collection = db["bot_data_collection"]
        db_data = collection.find_one({"data.id": "root"})
        if db_data:
            if "_id" in db_data:
                del db_data["_id"]  # Remove MongoDB ObjectId if exists
            data_to_save = db_data
            print("✅ MongoDB data loaded")
        else:
            data_to_save = DEFAULT_JSON
            print("⚠️ MongoDB में data नहीं मिला, default JSON इस्तेमाल किया गया")

        # 2. Create file if not exists
        os.makedirs(os.path.dirname(BOTES_DATA_FILE), exist_ok=True)
        with open(BOTES_DATA_FILE, "w") as f:
            json.dump(data_to_save, f, indent=2)
        print(f"✅ Data saved to: {BOTES_DATA_FILE}")

    except Exception as e:
        print(f"❌ Error: {e}")