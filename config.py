import os
import json
import logging
from pymongo import MongoClient
from flask import Flask, request, jsonify
from common_data import data_file, MD_URI, DEFAULT_JSON

# Setup logging (This can be moved to a central location if reused)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
    # You can add filename='log.txt' if you want to save logs in a file
)

def save_mongodb_data_to_file():
    try:
        # MongoDB Setup
        client = MongoClient(MD_URI)
        db = client["bot_database"]
        collection = db["bot_data_collection"]

        # Get root data
        db_data = collection.find_one({"data.id": "root"})

        if db_data:
            db_data.pop("_id", None)  # Remove MongoDB _id if exists
            data_to_save = db_data
            logging.info("✅ MongoDB data loaded successfully.")
        else:
            data_to_save = DEFAULT_JSON
            logging.warning("⚠️ MongoDB में data नहीं मिला, default JSON इस्तेमाल किया गया।")

        # Ensure directory exists
        os.makedirs(os.path.dirname(data_file), exist_ok=True)

        # Write to file
        with open(data_file, "w") as f:
            json.dump(data_to_save, f, indent=2)
        logging.info(f"✅ Data saved to file: {data_file}")

    except Exception as e:
        logging.error("❌ Error while saving MongoDB data to file: %s", e)