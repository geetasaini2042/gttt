import requests
import json
import os
from script import flask_app     
from flask import Flask, request, jsonify
from flask_cors import CORS
from common_data import data_file,BOT_TOKEN
CORS(flask_app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
def find_item_by_id(folder, target_id):
    for item in folder.get("items", []):
        if item.get("id") == target_id:
            return item
        if item.get("type") == "folder":
            result = find_item_by_id(item, target_id)
            if result:
                return result
    return None

@flask_app.route("/unlock_file", methods=["GET"])
def unlock_and_send_file():
    user_id = request.args.get("user_id")
    uuid = request.args.get("uuid")

    if not user_id or not uuid:
        return jsonify({"status": "error", "message": "Missing user_id or uuid"}), 400

    try:
        with open(data_file) as f:
            bot_data = json.load(f)
    except Exception as e:
        return jsonify({"status": "error", "message": f"Data file error: {e}"}), 500

    root = bot_data.get("data", {})
    file_data = find_item_by_id(root, uuid)

    if not file_data or file_data.get("type") != "file":
        return jsonify({"status": "error", "message": "File not found"}), 404

    file_id = file_data["file_id"]
    name = file_data.get("name", "Unnamed")
    caption = file_data.get("caption", name)
    sub_type = file_data.get("sub_type", "document")

    # Choose right Telegram API method
    if sub_type in ["photo", "video", "audio"]:
        method = f"send{sub_type.capitalize()}"
        media_type = sub_type
    else:
        method = "sendDocument"
        media_type = "document"

    # Send file using Telegram Bot API
    try:
        res = requests.post(
            f"{TELEGRAM_API_URL}/{method}",
            json={
                "chat_id": int(user_id),
                media_type: file_id,
                "caption": caption
            }
        )
        if res.status_code != 200 or not res.json().get("ok"):
            return jsonify({"status": "error", "message": f"Telegram API error: {res.text}"}), 500

    except Exception as e:
        return jsonify({"status": "error", "message": f"Telegram send error: {e}"}), 500

    return jsonify({"status": "success", "message": f"✅ File sent to user {user_id}."})
