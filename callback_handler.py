from pyrogram import filters
from script import app
import json
from typing import Union
import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import json

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import json
from collections import defaultdict
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
ADMINS = [6150091802, 2525267728]

ADMINS = [6150091802, 2525267728]
data_file = "/storage/emulated/0/BotBuilder/PYTHON/bot_data.json"

from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Union
import json, os
from config import USE_MONGO, MONGO_URI, DB_NAME

if USE_MONGO:
    from motor.motor_asyncio import AsyncIOMotorClient
    mongo_client = AsyncIOMotorClient(MONGO_URI)
    db = mongo_client[DB_NAME]

def get_collection_name_from_path(path: str) -> str:
    return os.path.splitext(os.path.basename(path))[0]

async def load_bot_data(data_file: str = "/storage/emulated/0/BotBuilder/PYTHON/bot_data.json", query: dict = {}) -> Union[dict, list, None]:
    try:
        if USE_MONGO:
            collection_name = get_collection_name_from_path(data_file)
            result = await db[collection_name].find_one(query)
            return result or {}
        else:
            with open(data_file, "r", encoding="utf-8") as f:
                return json.load(f)
    except FileNotFoundError:
        print(f"❌ File not found: {data_file}")
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON in file: {data_file}")
    except Exception as e:
        print(f"⚠ Unexpected error: {e}")
    return None

from collections import defaultdict
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

@app.on_callback_query(filters.regex("^open:"))
async def open_folder_handler(client, callback_query):
    user_id = callback_query.from_user.id
    folder_id = callback_query.data.split(":", 1)[1]

    full_data = load_bot_data()
    if not full_data:
        await callback_query.message.edit_text("❌ Bot data not found.")
        return

    root_folder = full_data.get("data", {})
    folder = find_folder_by_id(root_folder, folder_id)

    if not folder:
        await callback_query.answer("❌ Folder not found.", show_alert=True)
        return

    # Folder Content Show
    text = f"📁 *{folder['name']}*\n_{folder.get('description', '')}_"
    markup = generate_folder_keyboard(folder, user_id)
    await callback_query.message.edit_text(text, reply_markup=markup)


from collections import defaultdict
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def generate_folder_keyboard(folder: dict, user_id: int):
    layout = defaultdict(dict)
    folder_id = folder.get("id", "unknown")

    for item in folder.get("items", []):
        row = item.get("row", 0)
        col = item.get("column", 0)
        name = item.get("name", "❓")

        icon = "❓"
        button = None

        if item["type"] == "folder":
            icon = "📁"
            cb_data = f"open:{item['id']}"
            button = InlineKeyboardButton(f"{icon} {name}", callback_data=cb_data)

        elif item["type"] == "file":
            icon = "📄"
            cb_data = f"file:{item['id']}"
            button = InlineKeyboardButton(f"{icon} {name}", callback_data=cb_data)

        elif item["type"] == "url":
            icon = "🔗"
            real_url = item.get("url", "#")
            button = InlineKeyboardButton(f"{icon} {name}", url=real_url)

        elif item["type"] == "webapp":
            icon = "🧩"
            real_url = item.get("url", "#")
            button = InlineKeyboardButton(
              f"{icon} {name}",
              web_app=WebAppInfo(url=real_url)
              )

        if button:
            layout[row][col] = button

    # ⬇️ Convert to sorted rows
    sorted_rows = []
    for row in sorted(layout.keys()):
        button_row = [layout[row][col] for col in sorted(layout[row].keys())]
        sorted_rows.append(button_row)

    # ➕ Add Buttons
    if user_id in ADMINS:
        sorted_rows.append([
            InlineKeyboardButton("➕ Add File", callback_data=f"add_file:{folder_id}"),
            InlineKeyboardButton("📁 Add Folder", callback_data=f"add_folder:{folder_id}")
        ])
        sorted_rows.append([
            InlineKeyboardButton("🧩 Add WebApp", callback_data=f"add_webapp:{folder_id}"),
            InlineKeyboardButton("🔗 Add URL", callback_data=f"add_url:{folder_id}")
        ])
    else:
        allow = folder.get("user_allow", [])
        user_buttons = []

        if "add_file" in allow:
            user_buttons.append(InlineKeyboardButton("➕ Add File", callback_data=f"add_file:{folder_id}"))
        if "add_folder" in allow:
            user_buttons.append(InlineKeyboardButton("📁 Add Folder", callback_data=f"add_folder:{folder_id}"))
        if "add_webapp" in allow:
            user_buttons.append(InlineKeyboardButton("🧩 Add WebApp", callback_data=f"add_webapp:{folder_id}"))
        if "add_url" in allow:
            user_buttons.append(InlineKeyboardButton("🔗 Add URL", callback_data=f"add_url:{folder_id}"))

        for i in range(0, len(user_buttons), 2):
            sorted_rows.append(user_buttons[i:i+2])

    # ✏️ Edit Button
    if user_id in ADMINS or folder.get("created_by") == user_id:
        sorted_rows.append([
            InlineKeyboardButton("✏️ Edit Folder Layout", callback_data=f"edit_menu:{folder_id}")
        ])

    # ⬅️ Back
    parent_id = folder.get("parent_id")
    if parent_id:
        sorted_rows.append([InlineKeyboardButton("⬅️ Back", callback_data=f"open:{parent_id}")])

    return InlineKeyboardMarkup(sorted_rows)
def find_folder_by_id(current_folder: dict, target_id: str):
    # खुद को compare करो
    if current_folder.get("id") == target_id and current_folder.get("type") == "folder":
        return current_folder

    # अगर उसके अंदर items हैं, तो हर एक item को चेक करो
    for item in current_folder.get("items", []):
        if item.get("type") == "folder":
            result = find_folder_by_id(item, target_id)
            if result:
                return result

    return None
async def set_user_status(user_id: int, status: str | None):
    user_key = str(user_id)
    if USE_MONGO:
        if status is None:
            await db["status_user"].delete_one({"user_id": user_key})
        else:
            await db["status_user"].update_one(
                {"user_id": user_key},
                {"$set": {"status": status}},
                upsert=True
            )
    else:
        path = "/storage/emulated/0/BotBuilder/PYTHON/status_user.json"
        try:
            with open(path, "r") as f:
                data = json.load(f)
        except:
            data = {}

        if status is None:
            data.pop(user_key, None)
        else:
            data[user_key] = status

        with open(path, "w") as f:
            json.dump(data, f, indent=2)
async def get_temp_folder(user_id: int) -> dict:
    user_key = str(user_id)
    if USE_MONGO:
        doc = await db["tempfolder"].find_one({"user_id": user_key})
        return doc["folder_data"] if doc else {}
    else:
        try:
            with open("/storage/emulated/0/BotBuilder/PYTHON/tempfolder.json", "r") as f:
                data = json.load(f)
            return data.get(user_key, {})
        except:
            return {}
async def save_temp_folder(user_id: int, folder_data: dict | None):
    user_key = str(user_id)
    if USE_MONGO:
        if folder_data is None:
            await db["tempfolder"].delete_one({"user_id": user_key})
        else:
            await db["tempfolder"].update_one(
                {"user_id": user_key},
                {"$set": {"folder_data": folder_data}},
                upsert=True
            )
    else:
        path = "/storage/emulated/0/BotBuilder/PYTHON/tempfolder.json"
        try:
            with open(path, "r") as f:
                data = json.load(f)
        except:
            data = {}

        if folder_data is None:
            data.pop(user_key, None)
        else:
            data[user_key] = folder_data

        with open(path, "w") as f:
            json.dump(data, f, indent=2)
async def load_temp_folder(user_id: int) -> dict:
    if USE_MONGO:
        doc = await db["tempfolder"].find_one({"user_id": str(user_id)})
        return doc["folder_data"] if doc else {}
    else:
        try:
            with open("/storage/emulated/0/BotBuilder/PYTHON/tempfolder.json", "r") as f:
                data = json.load(f)
            return data.get(str(user_id), {})
        except:
            return {}
@app.on_callback_query(filters.regex("^add_folder:"))
async def add_folder_callback(client, callback_query):
    user_id = callback_query.from_user.id
    data = callback_query.data
    parent_id = data.split(":", 1)[1]

    # 🔍 Load bot data
    full_data = load_bot_data()
    root = full_data.get("data", {})
    parent_folder = find_folder_by_id(root, parent_id)

    if not parent_folder:
        await callback_query.answer("❌ Parent folder not found.", show_alert=True)
        return

    # 🔖 Save temp folder draft
    temp_data = {
        "user_id": user_id,
        "parent_id": parent_id,
        "parent_name": parent_folder["name"],
        "name": "",
        "description": "",
        "user_allow": []
    }

    save_temp_folder(user_id, temp_data)
    set_user_status(user_id, f"getting_folder_name:{parent_id}")

    await callback_query.message.edit_text(
        f"📁 Adding new folder under: *{parent_folder['name']}*\n\n✍️ Please send the *name* of the new folder."
    )


from filters.status_filters import StatusFilter

async def get_user_status(user_id: int) -> str:
    if USE_MONGO:
        doc = await db["status_user"].find_one({"user_id": str(user_id)})
        return doc["status"] if doc else ""
    else:
        try:
            with open("/storage/emulated/0/BotBuilder/PYTHON/status_user.json", "r") as f:
                data = json.load(f)
            return data.get(str(user_id), "")
        except:
            return ""
            

from filters.status_filters import StatusFilter

from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

@app.on_message(filters.private & filters.text & StatusFilter("getting_folder_description"))
async def receive_folder_description(client, message):
    user_id = message.from_user.id
    description = message.text.strip()

    # 🔄 Load current status
    status = await get_user_status(user_id)
    parent_id = status.split(":", 1)[1]

    # 📁 Load temp folder data using helper
    folder_data = await get_temp_folder(user_id)
    folder_data["description"] = description

    # 💾 Save updated folder using helper
    await save_temp_folder(user_id, folder_data)

    # 🔄 Update status to 'setting_folder_permissions'
    await set_user_status(user_id, f"setting_folder_permissions:{parent_id}")

    # 🎛 Show toggling buttons (initially ❌)
    buttons = [
        [InlineKeyboardButton("➕ Add File ❌", callback_data="toggle:add_file")],
        [InlineKeyboardButton("📁 Add Folder ❌", callback_data="toggle:add_folder")],
        [InlineKeyboardButton("🔗 Add URL ❌", callback_data="toggle:add_url")],
        [InlineKeyboardButton("🧩 Add WebApp ❌", callback_data="toggle:add_webapp")]
    ]
    await message.reply(
        "📄 विवरण सेव हो गया!\nअब आप नीचे से जो सुविधाएँ allow करनी हैं उन्हें ✅ पर टॉगल करें:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
@app.on_callback_query(filters.regex("^toggle:"))
async def toggle_permission_handler(client, callback_query):
    user_id = str(callback_query.from_user.id)
    permission = callback_query.data.split(":", 1)[1]  # e.g., add_file

    # 🔍 Load temp folder using helper
    folder = await get_temp_folder(user_id)
    if not folder:
        await callback_query.answer("❌ कोई फोल्डर डेटा नहीं मिला।", show_alert=True)
        return

    # 🔄 Toggle permission in user_allow
    current = folder.get("user_allow", [])
    if permission in current:
        current.remove(permission)
    else:
        current.append(permission)
    folder["user_allow"] = current

    # 💾 Save updated folder using helper
    await save_temp_folder(user_id, folder)

    # ♻️ Build updated buttons
    def btn(name, perm):
        mark = "✅" if perm in current else "❌"
        return InlineKeyboardButton(f"{name} {mark}", callback_data=f"toggle:{perm}")

    buttons = [
        [btn("➕ Add File", "add_file")],
        [btn("📁 Add Folder", "add_folder")],
        [btn("🔗 Add URL", "add_url")],
        [btn("🧩 Add WebApp", "add_webapp")],
        [InlineKeyboardButton("✅ Confirm & Save", callback_data="confirm_folder")]
    ]

    await callback_query.message.edit_text(
        "✅ चयन अपडेट हो गया!\nनीचे से टॉगल करें और अंत में Confirm करें।",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
import uuid

@app.on_callback_query(filters.regex("^confirm_folder$"))
async def confirm_and_save_folder(client, callback_query):
    user_id = str(callback_query.from_user.id)

    # 🔄 Load temp folder
    folder_data = await get_temp_folder(user_id)
    if not folder_data:
        await callback_query.answer("❌ Temp folder missing.", show_alert=True)
        return

    parent_id = folder_data.get("parent_id")

    # 📦 Load root bot_data from MongoDB or file
    if USE_MONGO:
        root_doc = await db["bot_data"].find_one({"id": "root"})
        if not root_doc:
            await callback_query.answer("❌ Root data missing.", show_alert=True)
            return
        root = root_doc.get("data", {})
    else:
        try:
            with open("/storage/emulated/0/BotBuilder/PYTHON/bot_data.json", "r") as f:
                root_data = json.load(f)
            root = root_data.get("data", {})
        except:
            await callback_query.answer("❌ bot_data.json missing.", show_alert=True)
            return

    # 🔍 Find parent folder
    parent = find_folder_by_id(root, parent_id)
    if not parent:
        await callback_query.answer("❌ Parent folder not found.", show_alert=True)
        return

    # 🔢 Calculate row/col
    existing = parent.get("items", [])
    row = len(existing)
    col = 0

    new_item = {
        "id": f"item_{uuid.uuid4().hex[:6]}",
        "name": folder_data["name"],
        "description": folder_data["description"],
        "type": "folder",
        "created_by": int(user_id),
        "parent_id": parent_id,
        "user_allow": folder_data.get("user_allow", []),
        "items": [],
        "row": row,
        "column": col
    }

    parent.setdefault("items", []).append(new_item)

    # 💾 Save updated bot_data
    if USE_MONGO:
        await db["bot_data"].update_one(
            {"id": "root"},
            {"$set": {"data": root}}
        )
    else:
        with open("/storage/emulated/0/BotBuilder/PYTHON/bot_data.json", "w") as f:
            json.dump({"data": root}, f, indent=2)

    # 🧹 Clear temp and status
    await save_temp_folder(user_id, None)
    await set_user_status(user_id, None)

    await callback_query.message.edit_text(f"📁 Folder '{new_item['name']}' saved successfully!")
@app.on_callback_query(filters.regex(r"^add_url:(.+)$"))
async def add_url_callback(client, callback_query):
    folder_id = callback_query.data.split(":")[1]
    user_id = str(callback_query.from_user.id)

    # ✅ Status Set
    with open("/storage/emulated/0/BotBuilder/PYTHON/status_user.json", "r") as f:
        content = f.read().strip()
        status_data = json.loads(content) if content else {}

    status_data[user_id] = f"getting_url_name:{folder_id}"
    with open("/storage/emulated/0/BotBuilder/PYTHON/status_user.json", "w") as f:
        json.dump(status_data, f, indent=2)

    # ✅ Temp init
    with open("/storage/emulated/0/BotBuilder/PYTHON/tempurl.json", "r") as f:
        content = f.read().strip()
        temp_data = json.loads(content) if content else {}

    temp_data[user_id] = {
        "folder_id": folder_id
    }
    with open("/storage/emulated/0/BotBuilder/PYTHON/tempurl.json", "w") as f:
        json.dump(temp_data, f, indent=2)

    await callback_query.message.edit_text("📌 कृपया URL का नाम भेजें (जैसे: 'NCERT Site')")
@app.on_message(filters.private & filters.text & StatusFilter("getting_url_name"))
async def receive_url_name(client, message):
    user_id = str(message.from_user.id)
    url_name = message.text.strip()

    with open("/storage/emulated/0/BotBuilder/PYTHON/tempurl.json", "r") as f:
        content = f.read().strip()
        temp_data = json.loads(content) if content else {}

    # ❌ ये गलत है:
    # temp_data[user_id] = {"name": url_name}

    # ✅ सही तरीका:
    if user_id not in temp_data:
        temp_data[user_id] = {}
    temp_data[user_id]["name"] = url_name

    with open("/storage/emulated/0/BotBuilder/PYTHON/tempurl.json", "w") as f:
        json.dump(temp_data, f, indent=2)

    with open("/storage/emulated/0/BotBuilder/PYTHON/status_user.json", "r") as f:
        status_data = json.load(f)

    folder_id = status_data[user_id].split(":")[1]
    status_data[user_id] = f"getting_url:{folder_id}"
    with open("/storage/emulated/0/BotBuilder/PYTHON/status_user.json", "w") as f:
        json.dump(status_data, f)

    await message.reply("🔗 अब URL भेजें (जैसे: https://...)")
    
@app.on_message(filters.private & filters.text & StatusFilter("getting_url"))
async def receive_url(client, message):
    user_id = str(message.from_user.id)
    url = message.text.strip()

    if not url.startswith("http://") and not url.startswith("https://"):
        await message.reply("❌ कृपया एक मान्य URL भेजें।")
        return

    with open("/storage/emulated/0/BotBuilder/PYTHON/tempurl.json", "r") as f:
        temp_data = json.load(f)
    temp_data[user_id]["url"] = url
    with open("/storage/emulated/0/BotBuilder/PYTHON/tempurl.json", "w") as f:
        json.dump(temp_data, f, indent=2)

    with open("/storage/emulated/0/BotBuilder/PYTHON/status_user.json", "r") as f:
        status_data = json.load(f)

    folder_id = status_data[user_id].split(":")[1]
    status_data[user_id] = f"getting_caption_url:{folder_id}"
    with open("/storage/emulated/0/BotBuilder/PYTHON/status_user.json", "w") as f:
        json.dump(status_data, f)

    await message.reply("📝 अब उसके लिए एक caption भेजें।")
@app.on_message(filters.private & filters.text & StatusFilter("getting_caption_url"))
async def receive_url_caption(client, message):
    user_id = str(message.from_user.id)
    caption = message.text.strip()

    with open("/storage/emulated/0/BotBuilder/PYTHON/tempurl.json", "r") as f:
        temp_data = json.load(f)
    url_data = temp_data.get(user_id, {})
    url_data["caption"] = caption

    folder_id = url_data.get("folder_id")
    with open("/storage/emulated/0/BotBuilder/PYTHON/bot_data.json", "r") as f:
        bot_data = json.load(f)

    root = bot_data.get("data", {})
    parent = find_folder_by_id(root, folder_id)

    if not parent:
        await message.reply("❌ Parent folder नहीं मिला।")
        return

    # नया item structure
    new_item = {
        "id": f"url_{uuid.uuid4().hex[:12]}",
        "type": "url",
        "name": url_data["name"],
        "url": url_data["url"],
        "caption": caption,
        "created_by": int(user_id),
        "row": 0,
        "column": 0
    }

    parent.setdefault("items", []).append(new_item)

    with open("/storage/emulated/0/BotBuilder/PYTHON/bot_data.json", "w") as f:
        json.dump(bot_data, f, indent=2)

    temp_data.pop(user_id, None)
    with open("/storage/emulated/0/BotBuilder/PYTHON/tempurl.json", "w") as f:
        json.dump(temp_data, f)

    with open("/storage/emulated/0/BotBuilder/PYTHON/status_user.json", "r") as f:
        status_data = json.load(f)
    status_data.pop(user_id, None)
    with open("/storage/emulated/0/BotBuilder/PYTHON/status_user.json", "w") as f:
        json.dump(status_data, f)

    await message.reply("🔗 URL सफलतापूर्वक जोड़ दिया गया ✅")
def find_folder_by_id(folder, folder_id):
    if folder.get("id") == folder_id and folder.get("type") == "folder":
        return folder
    for item in folder.get("items", []):
        if item.get("type") == "folder":
            if item.get("id") == folder_id:
                return item
            found = find_folder_by_id(item, folder_id)
            if found:
                return found
    return None
import re
from pyrogram import filters
from pyrogram.types import Message
from filters.status_filters import StatusFilter

# 🔎 URL Validity Checker Function
def is_valid_url(url: str) -> bool:
    # बहुत ही साधारण सा regex pattern है
    pattern = re.compile(
        r'^(https?://)'           # http:// या https:// से शुरू हो
        r'([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'  # डोमेन नाम
        r'(/[^\s]*)?$',           # बाकी path optional
        re.IGNORECASE
    )
    return re.match(pattern, url) is not None

@app.on_callback_query(filters.regex(r"^edit_menu:(.+)$"))
async def edit_menu_handler(client, callback_query):
    folder_id = callback_query.data.split(":")[1]
    user_id = callback_query.from_user.id

    # 🔁 Load data
    with open("/storage/emulated/0/BotBuilder/PYTHON/bot_data.json", "r") as f:
        data = json.load(f)

    # 🔍 Recursive function to find any folder
    def find_folder(folder, fid):
        if folder.get("id") == fid and folder.get("type") == "folder":
            return folder
        for item in folder.get("items", []):
            if item.get("type") == "folder":
                found = find_folder(item, fid)
                if found:
                    return found
        return None

    root = data.get("data", {})
    folder = find_folder(root, folder_id)

    if not folder:
        await callback_query.answer("❌ Folder not found", show_alert=True)
        return

    # 🔐 Access Check
    if user_id not in ADMINS and folder.get("created_by") != user_id:
        await callback_query.answer("❌ Not allowed", show_alert=True)
        return

    # 📦 Show all items for editing
    buttons = []
    for item in folder.get("items", []):
        name = item.get("name", "❓")
        item_id = item.get("id")
        buttons.append([
            InlineKeyboardButton(f"✏️ {name}", callback_data=f"edit_item:{folder_id}:{item_id}")
        ])

    # 🔙 Back button
    buttons.append([
        InlineKeyboardButton("⬅️ Back", callback_data=f"open:{folder_id}")
    ])

    await callback_query.message.edit_text(
        "🛠 Select an item to edit:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

@app.on_callback_query(filters.regex(r"^edit_item:(.+):(.+)$"))
async def edit_item_handler(client, callback_query):
    _, folder_id, item_id = callback_query.data.split(":")
    user_id = callback_query.from_user.id

    with open("/storage/emulated/0/BotBuilder/PYTHON/bot_data.json", "r") as f:
        data = json.load(f)

    # ✅ Corrected recursive folder finder
    def find_folder(folder, fid):
        if folder.get("id") == fid and folder.get("type") == "folder":
            return folder
        for item in folder.get("items", []):
            if item.get("type") == "folder":
                found = find_folder(item, fid)
                if found:
                    return found
        return None

    root = data.get("data", {})
    folder = find_folder(root, folder_id)

    if not folder:
        await callback_query.answer("❌ Folder not found", show_alert=True)
        return

    # 🔎 Find the selected item inside that folder
    item = next((i for i in folder.get("items", []) if i["id"] == item_id), None)
    if not item:
        await callback_query.answer("❌ Item not found", show_alert=True)
        return

    # 🔐 Access check
    if user_id not in ADMINS and item.get("created_by") != user_id:
        await callback_query.answer("❌ Not allowed", show_alert=True)
        return

    # 🧰 Show edit options
    buttons = [
        [InlineKeyboardButton("✏️ Rename", callback_data=f"rename:{folder_id}:{item_id}")],
        [InlineKeyboardButton("🔀 Move", callback_data=f"move_menu:{folder_id}:{item_id}")],
        [InlineKeyboardButton("🗑 Delete", callback_data=f"delete:{folder_id}:{item_id}")],
        [InlineKeyboardButton("⬅️ Back", callback_data=f"edit_menu:{folder_id}")]
    ]

    await callback_query.message.edit_text(
        f"🧩 Edit Options for: {item.get('name', 'Unnamed')}",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
@app.on_callback_query(filters.regex(r"^rename:(.+):(.+)$"))
async def rename_item_callback(client, callback_query):
    folder_id, item_id = callback_query.data.split(":")[1:]
    user_id = str(callback_query.from_user.id)

    # Save as: renaming:<folder_id>:<item_id>
    with open("/storage/emulated/0/BotBuilder/PYTHON/status_user.json", "r") as f:
        data = json.load(f)

    data[user_id] = f"renaming:{folder_id}:{item_id}"

    with open("/storage/emulated/0/BotBuilder/PYTHON/status_user.json", "w") as f:
        json.dump(data, f, indent=2)

    await callback_query.message.edit_text("📝 नया नाम भेजिए:")


@app.on_message(filters.private & filters.text & StatusFilter("renaming"))
async def rename_text_handler(client, message):
    user_id = str(message.from_user.id)
    new_name = message.text.strip()

    # Load status
    with open("/storage/emulated/0/BotBuilder/PYTHON/status_user.json", "r") as f:
        status_data = json.load(f)

    status = status_data.get(user_id, "")
    parts = status.split(":")

    if len(parts) != 3:
        return await message.reply("❌ Status error.")

    _, folder_id, item_id = parts

    # Load bot data
    with open("/storage/emulated/0/BotBuilder/PYTHON/bot_data.json", "r") as f:
        bot_data = json.load(f)

    def find_folder(folder, fid):
        if folder["id"] == fid:
            return folder
        for item in folder.get("items", []):
            if item.get("type") == "folder":
                found = find_folder(item, fid)
                if found:
                    return found
        return None

    folder = find_folder(bot_data["data"], folder_id)
    if not folder:
        return await message.reply("❌ Folder not found.")

    item = next((i for i in folder.get("items", []) if i["id"] == item_id), None)
    if not item:
        return await message.reply("❌ Item not found.")

    item["name"] = new_name

    with open("/storage/emulated/0/BotBuilder/PYTHON/bot_data.json", "w") as f:
        json.dump(bot_data, f, indent=2)

    del status_data[user_id]
    with open("/storage/emulated/0/BotBuilder/PYTHON/status_user.json", "w") as f:
        json.dump(status_data, f, indent=2)

    await message.reply("✅ नाम बदल दिया गया।")

@app.on_callback_query(filters.regex(r"^delete:(.+):(.+)$"))
async def delete_item_confirm(client, callback_query):
    folder_id, item_id = callback_query.data.split(":")[1:]
    user_id = str(callback_query.from_user.id)

    # Save status
    with open("/storage/emulated/0/BotBuilder/PYTHON/status_user.json", "r") as f:
        status_data = json.load(f)

    status_data[user_id] = f"deleting:{folder_id}:{item_id}"

    with open("/storage/emulated/0/BotBuilder/PYTHON/status_user.json", "w") as f:
        json.dump(status_data, f, indent=2)

    await callback_query.message.edit_text(
        f"❗ इस item को हटाने के लिए इस folder की ID भेजिए:\n\n🔐 `{folder_id}`\n\n⚠️ कोई और भेजने पर delete नहीं होगा।"
    )
    
@app.on_message(filters.private & filters.text & StatusFilter("deleting"))
async def delete_item_final(client, message):
    user_id = str(message.from_user.id)
    entered_text = message.text.strip()

    # Load status
    with open("/storage/emulated/0/BotBuilder/PYTHON/status_user.json", "r") as f:
        status_data = json.load(f)

    status = status_data.get(user_id, "")
    parts = status.split(":")
    if len(parts) != 3:
        return await message.reply("❌ Invalid status.")

    _, folder_id, item_id = parts

    # Compare folder ID
    if entered_text != folder_id:
        del status_data[user_id]
        with open("/storage/emulated/0/BotBuilder/PYTHON/status_user.json", "w") as f:
            json.dump(status_data, f, indent=2)
        return await message.reply("❌ Folder ID गलत है। Delete नहीं किया गया।")

    # Load main data
    with open("/storage/emulated/0/BotBuilder/PYTHON/bot_data.json", "r") as f:
        bot_data = json.load(f)

    def find_folder(folder, fid):
        if folder["id"] == fid:
            return folder
        for item in folder.get("items", []):
            if item.get("type") == "folder":
                found = find_folder(item, fid)
                if found:
                    return found
        return None

    folder = find_folder(bot_data["data"], folder_id)
    if not folder:
        return await message.reply("❌ Folder not found.")

    # Remove the item
    folder["items"] = [i for i in folder.get("items", []) if i["id"] != item_id]

    # Save
    with open("/storage/emulated/0/BotBuilder/PYTHON/bot_data.json", "w") as f:
        json.dump(bot_data, f, indent=2)

    # Clear status
    del status_data[user_id]
    with open("/storage/emulated/0/BotBuilder/PYTHON/status_user.json", "w") as f:
        json.dump(status_data, f, indent=2)

    await message.reply("✅ Item delete कर दिया गया।")
@app.on_callback_query(filters.regex(r"^move_menu:(.+):(.+)$"))
async def move_menu_handler(client, callback_query):
    folder_id, item_id = callback_query.data.split(":")[1:]
    user_id = callback_query.from_user.id

    with open("/storage/emulated/0/BotBuilder/PYTHON/bot_data.json", "r") as f:
        data = json.load(f)

    def find_folder(folder, fid):
        if folder["id"] == fid:
            return folder
        for item in folder.get("items", []):
            if item.get("type") == "folder":
                found = find_folder(item, fid)
                if found:
                    return found
        return None

    folder = find_folder(data["data"], folder_id)
    if not folder:
        await callback_query.answer("❌ Folder not found", show_alert=True)
        return

    item = next((i for i in folder["items"] if i["id"] == item_id), None)
    if not item:
        await callback_query.answer("❌ Item not found", show_alert=True)
        return

    layout = defaultdict(dict)
    for i in folder["items"]:
        r, c = i.get("row", 0), i.get("column", 0)
        icon = "💠" if i["id"] == item_id else {
            "folder": "📁", "file": "📄", "url": "🔗", "webapp": "🧩"
        }.get(i["type"], "❓")
        layout[r][c] = InlineKeyboardButton(f"{icon} {i['name']}", callback_data="ignore")

    grid = []
    for r in sorted(layout):
        row_buttons = [layout[r][c] for c in sorted(layout[r])]
        grid.append(row_buttons)

    # Movement Buttons (all in one row)
    move_row = [
        InlineKeyboardButton("⬅️", callback_data=f"move_left:{folder_id}:{item_id}"),
        InlineKeyboardButton("⬆️", callback_data=f"move_up:{folder_id}:{item_id}"),
        InlineKeyboardButton("⬇️", callback_data=f"move_down:{folder_id}:{item_id}"),
        InlineKeyboardButton("➡️", callback_data=f"move_right:{folder_id}:{item_id}"),
    ]
    grid.append(move_row)
    grid.append([InlineKeyboardButton("⬅️ Back", callback_data=f"edit_menu:{folder_id}")])

    await callback_query.message.edit_text(
        "🔄 Move the selected item (💠):",
        reply_markup=InlineKeyboardMarkup(grid)
    )

def load_data():
    with open("/storage/emulated/0/BotBuilder/PYTHON/bot_data.json", "r") as f:
        return json.load(f)

def save_data(data):
    with open("/storage/emulated/0/BotBuilder/PYTHON/bot_data.json", "w") as f:
        json.dump(data, f, indent=2)

def find_folder(folder, fid):
    if folder.get("id") == fid:
        return folder
    for i in folder.get("items", []):
        if i.get("type") == "folder":
            found = find_folder(i, fid)
            if found:
                return found
    return None

def reassign_column_first(items, moved_item=None, max_columns=2):
    if moved_item:
        items_copy = [i for i in items if i["id"] != moved_item["id"]]
        reordered = [moved_item] + items_copy
    else:
        reordered = sorted(items, key=lambda x: (x["row"], x["column"]))

    row, col = 0, 0
    final_items = []
    for item in reordered:
        item["row"] = row
        item["column"] = col
        final_items.append(item)
        row += 1
        if row >= max_columns:
            row = 0
            col += 1

    # Update the array in-place with new order
    items.clear()
    items.extend(final_items)
# 🔧 Compact utility function
def compact_items(items):
    # Row और column के अनुसार sort
    items = sorted(items, key=lambda x: (x["row"], x["column"]))
    new_items = []
    row_map = {}
    row_counter = 0

    # Unique row नंबर को 0,1,2... में remap करो
    for row in sorted(set(i["row"] for i in items)):
        row_map[row] = row_counter
        row_counter += 1

    for item in items:
        item["row"] = row_map[item["row"]]
        new_items.append(item)

    # Final sorted compact list वापस भेजो
    return sorted(new_items, key=lambda x: (x["row"], x["column"]))
# ⬆️ Move UP handler
@app.on_callback_query(filters.regex(r"^move_up:(.+):(.+)$"))
async def move_up_handler(client: Client, callback_query):
    folder_id, item_id = callback_query.data.split(":")[1:]
    try:
        data = load_data()
        folder = find_folder(data.get("data", {}), folder_id)
        if not folder:
            return await callback_query.answer("❌ फोल्डर नहीं मिला!", show_alert=True)

        items = folder.get("items", [])
        item = next((i for i in items if i.get("id") == item_id), None)
        if not item:
            return await callback_query.answer("❌ आइटम नहीं मिला!", show_alert=True)

        current_row = item["row"]
        current_col = item["column"]

        same_row_items = [i for i in items if i["row"] == current_row and i["id"] != item_id]

        if same_row_items:
            # बाकियों को push नीचे
            for i in items:
                if i["id"] != item_id and i["row"] >= current_row:
                    i["row"] += 1

            item["column"] = 0

            # Column conflict avoid
            by_position = {}
            for i in items:
                key = (i["row"], i["column"])
                while key in by_position:
                    i["column"] += 1
                    key = (i["row"], i["column"])
                by_position[key] = i["id"]

        else:
            if current_row > 0:
                # ऊपर वाली row में shift
                above_items = [i for i in items if i["row"] == current_row - 1]
                existing_cols = [i["column"] for i in above_items]
                item["row"] = current_row - 1
                item["column"] = max(existing_cols, default=-1) + 1
            else:
                # row == 0 और अकेला
                max_row = max(i["row"] for i in items if i["id"] != item_id)
                old_row = item["row"]
                item["row"] = max_row + 1
                item["column"] = 0

                # ऊपर वालों को -1 करो
                for i in items:
                    if i["id"] != item_id and i["row"] < old_row:
                        i["row"] -= 1

        # 🔄 Compact final layout
        folder["items"] = compact_items(items)

        save_data(data)

        callback_query.data = f"move_menu:{folder_id}:{item_id}"
        await move_menu_handler(client, callback_query)

    except Exception as e:
        await callback_query.answer(f"⚠️ त्रुटि: {str(e)}", show_alert=True)
@app.on_callback_query(filters.regex(r"^move_down:(.+):(.+)$"))
async def move_down_handler(client: Client, callback_query):
    folder_id, item_id = callback_query.data.split(":")[1:]
    try:
        data = load_data()
        folder = find_folder(data.get("data", {}), folder_id)
        if not folder:
            return await callback_query.answer("❌ फोल्डर नहीं मिला!", show_alert=True)

        items = folder.get("items", [])
        item = next((i for i in items if i["id"] == item_id), None)
        if not item:
            return await callback_query.answer("❌ आइटम नहीं मिला!", show_alert=True)

        current_row = item["row"]
        current_col = item["column"]

        # उसी row के अन्य buttons
        same_row_others = [i for i in items if i["row"] == current_row and i["id"] != item_id]
        max_row = max(i["row"] for i in items)

        if same_row_others:
            # ✅ Same row में और buttons हैं
            for i in items:
                if i["row"] > current_row:
                    i["row"] += 1  # नीचे की rows shift

            item["row"] = current_row + 1
            item["column"] = 0  # नीचे नई row की col 0

            # अगर current_col = 0 है, तो बाकी को shift करो
            if current_col == 0:
                for i in items:
                    if i["row"] == current_row and i["column"] > 0:
                        i["column"] -= 1

        else:
            # ✅ अकेला है row में
            if current_row < max_row:
                # नीचे row में last col निकालो
                below_items = [i for i in items if i["row"] == current_row + 1]
                cols = [i["column"] for i in below_items]
                item["row"] = current_row + 1
                item["column"] = max(cols, default=-1) + 1
            else:
                # ✅ already last row
                for i in items:
                    if i["id"] != item_id:
                        i["row"] += 1  # सबको नीचे करो
                item["row"] = 0
                item["column"] = 0

        # 🔄 Compact layout
        folder["items"] = compact_items(items)

        save_data(data)

        callback_query.data = f"move_menu:{folder_id}:{item_id}"
        await move_menu_handler(client, callback_query)

    except Exception as e:
        await callback_query.answer(f"⚠️ त्रुटि: {str(e)}", show_alert=True)
def compact_items(items):
    items = sorted(items, key=lambda x: (x["row"], x["column"]))
    new_items = []
    row_map = {}
    row_counter = 0
    for row in sorted(set(i["row"] for i in items)):
        row_map[row] = row_counter
        row_counter += 1
    for item in items:
        item["row"] = row_map[item["row"]]
        new_items.append(item)
    return sorted(new_items, key=lambda x: (x["row"], x["column"]))
@app.on_callback_query(filters.regex(r"^move_right:(.+):(.+)$"))
async def move_right_handler(client: Client, callback_query):
    folder_id, item_id = callback_query.data.split(":")[1:]
    try:
        data = load_data()
        folder = find_folder(data.get("data", {}), folder_id)
        if not folder:
            return await callback_query.answer("❌ फोल्डर नहीं मिला!", show_alert=True)

        items = folder.get("items", [])
        item = next((i for i in items if i["id"] == item_id), None)
        if not item:
            return await callback_query.answer("❌ आइटम नहीं मिला!", show_alert=True)

        row = item["row"]
        col = item["column"]

        # उसी row में सभी items
        row_items = [i for i in items if i["row"] == row]
        max_col = max(i["column"] for i in row_items)

        if col == max_col:
            return await callback_query.answer("❌ No space on the right", show_alert=True)

        # Right वाले item को ढूंढो
        right_item = next((i for i in row_items if i["column"] == col + 1), None)

        if right_item:
            right_item["column"] -= 1  # उसको left भेजो
        item["column"] += 1           # खुद right आओ

        # Final compact and save
        folder["items"] = compact_items(items)
        save_data(data)

        callback_query.data = f"move_menu:{folder_id}:{item_id}"
        await move_menu_handler(client, callback_query)

    except Exception as e:
        await callback_query.answer(f"⚠️ त्रुटि: {str(e)}", show_alert=True)

@app.on_callback_query(filters.regex(r"^move_left:(.+):(.+)$"))
async def move_left_handler(client: Client, callback_query):
    folder_id, item_id = callback_query.data.split(":")[1:]
    try:
        data = load_data()
        folder = find_folder(data.get("data", {}), folder_id)
        if not folder:
            return await callback_query.answer("❌ फोल्डर नहीं मिला!", show_alert=True)

        items = folder.get("items", [])
        item = next((i for i in items if i["id"] == item_id), None)
        if not item:
            return await callback_query.answer("❌ आइटम नहीं मिला!", show_alert=True)

        row = item["row"]
        col = item["column"]

        if col == 0:
            return await callback_query.answer("❌ No Space on the left", show_alert=True)

        # 🔍 Left वाले item को ढूंढो
        left_item = next((i for i in items if i["row"] == row and i["column"] == col - 1), None)

        if left_item:
            left_item["column"] += 1  # left वाले को right भेजो
        item["column"] -= 1          # खुद left आओ

        # ✅ Compact करके Save करो
        folder["items"] = compact_items(items)
        save_data(data)

        callback_query.data = f"move_menu:{folder_id}:{item_id}"
        await move_menu_handler(client, callback_query)

    except Exception as e:
        await callback_query.answer(f"⚠️ Error: {str(e)}", show_alert=True)
        
@app.on_callback_query(filters.regex(r"^add_webapp:(.+)$"))
async def add_webapp_callback(client, callback_query):
    folder_id = callback_query.data.split(":")[1]
    user_id = str(callback_query.from_user.id)

    # ✅ Status Set
    with open("/storage/emulated/0/BotBuilder/PYTHON/status_user.json", "r") as f:
        content = f.read().strip()
        status_data = json.loads(content) if content else {}

    status_data[user_id] = f"getting_webapp_name:{folder_id}"
    with open("/storage/emulated/0/BotBuilder/PYTHON/status_user.json", "w") as f:
        json.dump(status_data, f, indent=2)

    # ✅ Temp init
    with open("/storage/emulated/0/BotBuilder/PYTHON/tempwebapp.json", "r") as f:
        content = f.read().strip()
        temp_data = json.loads(content) if content else {}

    temp_data[user_id] = {
        "folder_id": folder_id
    }
    with open("/storage/emulated/0/BotBuilder/PYTHON/tempwebapp.json", "w") as f:
        json.dump(temp_data, f, indent=2)

    await callback_query.message.edit_text("📌 कृपया web app URL का नाम भेजें (जैसे: 'NCERT Site')")
@app.on_message(filters.private & filters.text & StatusFilter("getting_webapp_name"))
async def receive_webapp_name(client, message):
    user_id = str(message.from_user.id)
    webapp_name = message.text.strip()

    with open("/storage/emulated/0/BotBuilder/PYTHON/tempwebapp.json", "r") as f:
        content = f.read().strip()
        temp_data = json.loads(content) if content else {}
    if user_id not in temp_data:
        temp_data[user_id] = {}
    temp_data[user_id]["name"] = webapp_name

    with open("/storage/emulated/0/BotBuilder/PYTHON/tempwebapp.json", "w") as f:
        json.dump(temp_data, f, indent=2)

    with open("/storage/emulated/0/BotBuilder/PYTHON/status_user.json", "r") as f:
        status_data = json.load(f)

    folder_id = status_data[user_id].split(":")[1]
    status_data[user_id] = f"getting_webapp:{folder_id}"
    with open("/storage/emulated/0/BotBuilder/PYTHON/status_user.json", "w") as f:
        json.dump(status_data, f)

    await message.reply("🔗 अब URL भेजें (जैसे: https://...)")
    
from pyrogram import Client, filters
from pyrogram.types import Message
from filters.status_filters import StatusFilter
import json

@app.on_message(filters.private & filters.text & StatusFilter("getting_webapp"))
async def receive_webapp(client: Client, message: Message):
    user_id = str(message.from_user.id)
    webapp = message.text.strip()

    if not webapp.startswith("http://") and not webapp.startswith("https://"):
        await message.reply("❌ कृपया एक मान्य URL भेजें।")
        return

    # Telegram URL domains block list
    telegram_domains = ["t.me", "telegram.me", "telegram.dog", "telegram.org"]

    # Check if URL contains any blocked domain
    for domain in telegram_domains:
        if domain in webapp.lower():
            await message.reply("❌ Telegram URLs स्वीकार नहीं किए जाते। कृपया किसी अन्य वेबऐप लिंक भेजें।")
            return

    try:
        with open("/storage/emulated/0/BotBuilder/PYTHON/tempwebapp.json", "r") as f:
            temp_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        temp_data = {}

    if user_id not in temp_data:
        temp_data[user_id] = {}

    temp_data[user_id]["webapp"] = webapp

    with open("/storage/emulated/0/BotBuilder/PYTHON/tempwebapp.json", "w") as f:
        json.dump(temp_data, f, indent=2)

    with open("/storage/emulated/0/BotBuilder/PYTHON/status_user.json", "r") as f:
        status_data = json.load(f)

    folder_id = status_data[user_id].split(":")[1]
    status_data[user_id] = f"getting_caption_webapp:{folder_id}"

    with open("/storage/emulated/0/BotBuilder/PYTHON/status_user.json", "w") as f:
        json.dump(status_data, f)

    await message.reply("📝 अब उसके लिए एक caption भेजें।")
@app.on_message(filters.private & filters.text & StatusFilter("getting_caption_webapp"))
async def receive_webapp_caption(client, message):
    user_id = str(message.from_user.id)
    caption = message.text.strip()

    with open("/storage/emulated/0/BotBuilder/PYTHON/tempwebapp.json", "r") as f:
        temp_data = json.load(f)
    webapp_data = temp_data.get(user_id, {})
    webapp_data["caption"] = caption

    folder_id = webapp_data.get("folder_id")
    with open("/storage/emulated/0/BotBuilder/PYTHON/bot_data.json", "r") as f:
        bot_data = json.load(f)

    root = bot_data.get("data", {})
    parent = find_folder_by_id(root, folder_id)

    if not parent:
        await message.reply("❌ Parent folder नहीं मिला।")
        return

    # नया item structure
    new_item = {
        "id": f"webapp_{uuid.uuid4().hex[:12]}",
        "type": "webapp",
        "name": webapp_data["name"],
        "url": webapp_data["webapp"],
        "caption": caption,
        "created_by": int(user_id),
        "row": 0,
        "column": 0
    }

    parent.setdefault("items", []).append(new_item)

    with open("/storage/emulated/0/BotBuilder/PYTHON/bot_data.json", "w") as f:
        json.dump(bot_data, f, indent=2)

    temp_data.pop(user_id, None)
    with open("/storage/emulated/0/BotBuilder/PYTHON/tempwebapp.json", "w") as f:
        json.dump(temp_data, f)

    with open("/storage/emulated/0/BotBuilder/PYTHON/status_user.json", "r") as f:
        status_data = json.load(f)
    status_data.pop(user_id, None)
    with open("/storage/emulated/0/BotBuilder/PYTHON/status_user.json", "w") as f:
        json.dump(status_data, f)

    await message.reply("🔗 URL सफलतापूर्वक जोड़ दिया गया ✅")
