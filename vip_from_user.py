import requests
from script import flask_app , app    
from flask import Flask, request, jsonify
from flask_cors import CORS
from common_data import data_file, BOT_TOKEN, ADMINS,LIKED_FILE,DISLIKED_FILE,PDF_VIEWS_FILE, DEPLOY_URL, PREMIUM_CHECK_LOG, is_termux, MD_URI
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
import json, os
from pymongo import MongoClient
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
import  pytz, urllib.parse
from datetime import datetime
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


CORS(flask_app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)
TELEGRAM_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# 🔍 Find item by ID
def find_item_by_id(folder, target_id):
    for item in folder.get("items", []):
        if item.get("id") == target_id:
            return item
        if item.get("type") == "folder":
            result = find_item_by_id(item, target_id)
            if result:
                return result
    return None

# 🔍 Find parent folder of item
def find_folder_id_of_item(folder, target_id, parent_id=None):
    for item in folder.get("items", []):
        if item.get("id") == target_id:
            return folder.get("id", parent_id)
        if item.get("type") == "folder":
            result = find_folder_id_of_item(item, target_id, item.get("id"))
            if result:
                return result
    return None


import json, os, tempfile, shutil

def safe_load_json(file):
    """Safe JSON load (अगर file corrupt हो तो empty dict return करेगा)."""
    try:
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except Exception:
        return {}

def load_json(file):
    """Alias of safe_load_json (read-only)."""
    return safe_load_json(file)

def safe_save_json(file, data):
    """Safe JSON save बिना portalocker (Termux compatible)."""
    # temp file बनाकर atomic replace करना
    temp_fd, temp_path = tempfile.mkstemp(dir=os.path.dirname(file))
    try:
        with os.fdopen(temp_fd, "w", encoding="utf-8") as tmp_file:
            json.dump(data, tmp_file, indent=2, ensure_ascii=False)
            tmp_file.flush()
            os.fsync(tmp_file.fileno())
        shutil.move(temp_path, file)
    except Exception:
        try:
            os.remove(temp_path)
        except FileNotFoundError:
            pass
        raise

@flask_app.route("/unlock_users_file", methods=["GET"])
def unlock_and_send_user_file():
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
    created_by = file_data.get("created_by")
    premium_owner = file_data.get("premium_owner", "")

    # 📂 Load like & dislike counts
    likes_data = safe_load_json(LIKED_FILE)
    dislikes_data = safe_load_json(DISLIKED_FILE)

    like_count = len(likes_data.get(uuid, []))
    dislike_count = len(dislikes_data.get(uuid, []))

    # 📌 Prepare inline keyboard buttons
    buttons = []
    if user_id in ADMINS() or user_id == created_by or user_id == premium_owner:
        folder_id = find_folder_id_of_item(root, uuid)
        buttons.append([
            {"text": "✏️ Edit Item","callback_data": f"edit_item_file:{folder_id}:{uuid}"}
         ])
    buttons.append([
        {"text": f"👍 Like ({like_count})", "callback_data": f"like:{uuid}"},
        {"text": "🔗 Share", "callback_data": f"share:{uuid}"},
        {"text": f"👎 Dislike ({dislike_count})", "callback_data": f"dislike:{uuid}"}
    ])
    reply_markup = {"inline_keyboard": buttons} if buttons else None

    # Determine media type and method
    media_type = sub_type if sub_type in ["photo", "video", "audio"] else "document"
    method = f"send{sub_type.capitalize()}" if sub_type in ["photo", "video", "audio"] else "sendDocument"

    # 📤 Prepare payload
    payload = {
        "chat_id": user_id,
        media_type: file_id,
        "caption": caption,
        "protect_content": True
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)

    # 📤 Send file
    try:
        res = requests.post(f"{TELEGRAM_API_URL}/{method}", json=payload)
        if res.status_code != 200 or not res.json().get("ok"):
            return jsonify({
                "status": "error",
                "message": f"Telegram API error: {res.text}"
            }), 500
    except Exception as e:
        return jsonify({"status": "error", "message": f"Telegram send error: {e}"}), 500

    # ✅ Save user in pdf_views.json
    views = safe_load_json(PDF_VIEWS_FILE)
    if uuid not in views:
        views[uuid] = []
    if user_id not in views[uuid]:
        views[uuid].append(user_id)
        safe_save_json(PDF_VIEWS_FILE, views)
    if not is_termux:
        client = MongoClient(MD_URI)
        db = client["bot_database"]
        collection = db["reactions"]

        collection.update_one(
            {"uuid": uuid},
            {"$addToSet": {"views": user_id}},  # Add user_id to views array if not exists
            upsert=True
        )

    return jsonify({"status": "success", "message": f"✅ File sent with button to {user_id}."})
def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)



@app.on_callback_query(filters.regex(r"^like:"))
async def handle_like(_, query: CallbackQuery):
    # Helper functions for JSON
    def load_json(path):
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_json(path, data):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    user_id = query.from_user.id
    uuid = query.data.split(":", 1)[1]

    likes_data = load_json(LIKED_FILE)
    dislikes_data = load_json(DISLIKED_FILE)

    if uuid not in likes_data:
        likes_data[uuid] = []
    if uuid not in dislikes_data:
        dislikes_data[uuid] = []

    message_text = ""

    # Toggle logic
    if user_id in likes_data[uuid]:
        likes_data[uuid].remove(user_id)
        message_text = "❌ Like removed!"
    else:
        # अगर Dislike था तो हटाओ
        if user_id in dislikes_data[uuid]:
            dislikes_data[uuid].remove(user_id)
        message_text = "👍 You liked this file!"
        likes_data[uuid].append(user_id)

    # Save JSON files
    save_json(LIKED_FILE, likes_data)
    save_json(DISLIKED_FILE, dislikes_data)

    # ✅ MongoDB Update
    if not is_termux:
        client = MongoClient(MD_URI)
        db = client["bot_database"]
        collection = db["reactions"]
        collection.update_one(
        {"uuid": uuid},
        {
            "$set": {
                "likes": likes_data[uuid],
                "dislikes": dislikes_data[uuid]
            }
        },
        upsert=True
    )
    logging.info(f"MongoDB updated for uuid {uuid}: likes={len(likes_data[uuid])}, dislikes={len(dislikes_data[uuid])}")

    # Update keyboard
    like_count = len(likes_data.get(uuid, []))
    dislike_count = len(dislikes_data.get(uuid, []))

    new_keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(f"👍 Like ({like_count})", callback_data=f"like:{uuid}"),
                InlineKeyboardButton("🔗 Share", callback_data=f"share:{uuid}"),
                InlineKeyboardButton(f"👎 Dislike ({dislike_count})", callback_data=f"dislike:{uuid}")
            ]
        ]
    )

    try:
        await query.message.edit_reply_markup(reply_markup=new_keyboard)
    except Exception as e:
        logging.error("Edit reply_markup error: %s", e)

    await query.answer(message_text, show_alert=False)
    
@app.on_callback_query(filters.regex(r"^dislike:"))
async def handle_dislike(_, query: CallbackQuery):
    def load_json(path):
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_json(path, data):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    user_id = query.from_user.id
    uuid = query.data.split(":", 1)[1]

    likes_data = load_json(LIKED_FILE)
    dislikes_data = load_json(DISLIKED_FILE)

    if uuid not in likes_data:
        likes_data[uuid] = []
    if uuid not in dislikes_data:
        dislikes_data[uuid] = []

    message_text = ""

    # Toggle logic
    if user_id in dislikes_data[uuid]:
        dislikes_data[uuid].remove(user_id)
        message_text = "❌ Dislike removed!"
    else:
        # अगर Like था तो हटाओ
        if user_id in likes_data[uuid]:
            likes_data[uuid].remove(user_id)
        dislikes_data[uuid].append(user_id)
        message_text = "👎 You disliked this file!"

    # Save JSON files
    save_json(LIKED_FILE, likes_data)
    save_json(DISLIKED_FILE, dislikes_data)

    # ✅ MongoDB Update
    if not is_termux:
        client = MongoClient(MD_URI)
        db = client["bot_database"]
        collection = db["reactions"]
        collection.update_one(
        {"uuid": uuid},
        {
            "$set": {
                "likes": likes_data[uuid],
                "dislikes": dislikes_data[uuid]
            }
        },
        upsert=True
    )
    logging.info(f"MongoDB updated for uuid {uuid}: likes={len(likes_data[uuid])}, dislikes={len(dislikes_data[uuid])}")

    # Update keyboard
    like_count = len(likes_data.get(uuid, []))
    dislike_count = len(dislikes_data.get(uuid, []))

    new_keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(f"👍 Like ({like_count})", callback_data=f"like:{uuid}"),
                InlineKeyboardButton("🔗 Share", callback_data=f"share:{uuid}"),
                InlineKeyboardButton(f"👎 Dislike ({dislike_count})", callback_data=f"dislike:{uuid}")
            ]
        ]
    )

    try:
        await query.message.edit_reply_markup(reply_markup=new_keyboard)
    except Exception as e:
        logging.error("Edit reply_markup error: %s", e)

    await query.answer(message_text, show_alert=False)
@app.on_callback_query(filters.regex(r"^share:(.+)$"))
async def share_file_handler(client, callback_query):
    uuid_code = callback_query.matches[0].group(1)

    # Bot का username fetch करना (runtime पर)
    bot_username = (await client.get_me()).username
    deep_link = f"https://t.me/{bot_username}?start={uuid_code}"

    keyboard = InlineKeyboardMarkup(
        [[
            InlineKeyboardButton("📤 Share Link", url=deep_link)
        ]]
    )

    await callback_query.message.reply_text(
        f"Your Link is Ready Share it to Your Friends:\n{deep_link}",
        reply_markup=keyboard
    )

    await callback_query.answer("✅ Share link generated!")
    
def find_item_by_id(root, uuid):
    if isinstance(root, dict):
        if root.get("id") == uuid:
            return root
        for k, v in root.items():
            result = find_item_by_id(v, uuid)
            if result:
                return result
    elif isinstance(root, list):
        for item in root:
            result = find_item_by_id(item, uuid)
            if result:
                return result
    return None

def find_folder_id_of_item(root, uuid):
    if isinstance(root, dict):
        if root.get("type") == "folder":
            for child in root.get("children", []):
                if child.get("id") == uuid:
                    return root.get("id")
                found = find_folder_id_of_item(child, uuid)
                if found:
                    return found
    elif isinstance(root, list):
        for item in root:
            found = find_folder_id_of_item(item, uuid)
            if found:
                return found
    return None

async def send_file_from_json(client, message, file_uuid):
    user_id = message.from_user.id

    # Load bot_data.json
    try:
        with open(data_file) as f:
            bot_data = json.load(f)
    except:
        await message.reply("❌ Data file not found.")
        return

    root = bot_data.get("data", {})
    file_data = find_item_by_id(root, file_uuid)

    if not file_data or file_data.get("type") != "file":
        await message.reply("❌ File not found.")
        return

    file_id = file_data["file_id"]
    name = file_data.get("name", "Unnamed")
    caption = file_data.get("caption", name)
    sub_type = file_data.get("sub_type", "document")
    visibility = file_data.get("visibility", "public")
    created_by = file_data.get("created_by")
    protect = visibility == "private"
    premium_owner = file_data.get("premium_owner", "")

    chat_id = message.chat.id
    unlock_base_url = DEPLOY_URL.rstrip("/") + f"/unlock_file"

    # ---------------- VIP file ----------------
    if visibility == "vip":
        try:
            temp_method = getattr(client, f"send_{sub_type}", client.send_document)
            media_arg = {sub_type if sub_type in ["photo", "video", "audio"] else "document": file_id}

            user = message.from_user
            full_name = (user.first_name or "") + (" " + user.last_name if user.last_name else "")
            username = f"@{user.username}" if user.username else "N/A"
            india_time = datetime.now(pytz.timezone("Asia/Kolkata")).strftime('%Y-%m-%d %H:%M:%S')

            user_info = f"👤 **Name:** {full_name}\n🆔 **User ID:** `{user.id}`\n🔗 **Username:** {username}\n🕒 **Time:** {india_time}"
            file_info = f"📁 **File Name:** {name}\n📝 **Description:** {caption}"
            combined_caption = f"🔐 **VIP File Access Attempt**\n\n{user_info}\n\n{file_info}"

            sent_msg = await temp_method(
                chat_id=PREMIUM_CHECK_LOG,
                caption=combined_caption,
                **media_arg
            )

            file_size = None
            if sub_type == "document" and sent_msg.document:
                file_size = sent_msg.document.file_size
            elif sub_type == "video" and sent_msg.video:
                file_size = sent_msg.video.file_size
            elif sub_type == "audio" and sent_msg.audio:
                file_size = sent_msg.audio.file_size
            readable_size = f"{round(file_size / (1024 * 1024), 2)} MB" if file_size else "Unknown"

           # base_unlock = "https://geetasaini2042.github.io/Ru/Premium/unlock.html?"
            base_unlock = "https://reward.edumate.life/Premium/unlock.html?"
            if premium_owner:
                unlock_base_url = DEPLOY_URL.rstrip("/") + f"/unlock_users_file"

            unlock_params = (
                f"uuid={urllib.parse.quote_plus(file_uuid)}"
                f"&file_name={urllib.parse.quote_plus(name)}"
                f"&file_des={urllib.parse.quote_plus(caption)}"
                f"&file_size={urllib.parse.quote_plus(readable_size)}"
                f"&url={urllib.parse.quote_plus(unlock_base_url)}"
            )
            unlock_url = base_unlock + unlock_params

            unlock_msg = f"""🔐 **Exclusive Premium File**

**📁 Name:** `{name}`  
**📝 Description:** `{caption}`  
**📦 Size:** `{readable_size}`

This is a premium file with valuable content, available only to exclusive users.

💡 To unlock this file, simply tap the button below and view a short ad.  
👇 Tap **Unlock Now** to continue.
"""
            buttons = [[InlineKeyboardButton("🔓 Unlock this file", web_app=WebAppInfo(url=unlock_url))]]
            await message.reply(unlock_msg, reply_markup=InlineKeyboardMarkup(buttons))
        except Exception as e:
            await message.reply(f"❌ Failed to prepare VIP file: {e}")
        return

    # ---------------- Non-VIP file ----------------
    buttons = []
    if user_id in ADMINS() or user_id == created_by:
        folder_id = find_folder_id_of_item(root, file_uuid)
        buttons.append([InlineKeyboardButton("✏️ Edit Item", callback_data=f"edit_item_file:{folder_id}:{file_uuid}")])

    try:
        method = getattr(client, f"send_{sub_type}", client.send_document)
        media_arg = {sub_type if sub_type in ["photo", "video", "audio"] else "document": file_id}
        await method(
            chat_id=chat_id,
            caption=caption,
            protect_content=protect,
            reply_markup=InlineKeyboardMarkup(buttons) if buttons else None,
            **media_arg
        )
    except Exception as e:
        await message.reply(f"❌ Error sending file: {e}")

@app.on_message(filters.regex(r"^/start\s+([A-Za-z0-9]+)"))
async def start_with_uuid(client, message):
    uuid = message.matches[0].group(1)
    await send_file_from_json(client, message, uuid)
