import requests
import json
import os
from script import flask_app     
from flask import Flask, request, jsonify
from flask_cors import CORS
from common_data import data_file,BOT_TOKEN, ADMINS
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

# 🔍 Utility to find parent folder of item
def find_folder_id_of_item(folder, target_id, parent_id=None):
    for item in folder.get("items", []):
        if item.get("id") == target_id:
            return folder.get("id", parent_id)
        if item.get("type") == "folder":
            result = find_folder_id_of_item(item, target_id, item.get("id"))
            if result:
                return result
    return None

@flask_app.route("/unlock_file", methods=["GET"])
def unlock_and_send_file():
    user_id = request.args.get("user_id", type=int)
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
    visibility = file_data.get("visibility", "public")
    created_by = file_data.get("created_by")

    # 📌 Prepare inline keyboard buttons
    buttons = []

    if user_id in ADMINS() or user_id == created_by:
        folder_id = find_folder_id_of_item(root, uuid)
        buttons.append([
            {
                "text": "✏️ Edit Item",
                "callback_data": f"edit_item_file:{folder_id}:{uuid}"
            }
        ])

    reply_markup = {"inline_keyboard": buttons} if buttons else None

    # 📤 Send file
    media_type = sub_type if sub_type in ["photo", "video", "audio"] else "document"
    method = f"send{sub_type.capitalize()}" if sub_type in ["photo", "video", "audio"] else "sendDocument"

    try:
        res = requests.post(
            f"{TELEGRAM_API_URL}/{method}",
            json={
                "chat_id": user_id,
                media_type: file_id,
                "caption": caption,
                "protect_content" : True,
                "reply_markup": reply_markup
            }
        )
        if res.status_code != 200 or not res.json().get("ok"):
            return jsonify({"status": "error", "message": f"Telegram API error: {res.text}"}), 500

    except Exception as e:
        return jsonify({"status": "error", "message": f"Telegram send error: {e}"}), 500

    return jsonify({"status": "success", "message": f"✅ File sent with button to {user_id}."})
