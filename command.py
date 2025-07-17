from pyrogram import filters
from script import app, get_created_by_from_folder, is_user_action_allowed,find_parent_of_parent
import json
from typing import Union
import os
import requests
from pyrogram import Client, filters
from pyrogram.errors import RPCError
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
from common_data import data_file1, status_user_file, temp_folder_file, temp_url_file, temp_webapp_file,temp_file_json, DEPLOY_URL,ADMINS_FILE,ADMINS
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import json
from collections import defaultdict
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from pyrogram.types import InputMediaDocument
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from collections import defaultdict
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from collections import defaultdict
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from filters.status_filters import StatusFilter
from pyrogram import Client, filters
from pyrogram.types import Message
from filters.status_filters import StatusFilter
import json
import re
from pyrogram import filters
from pyrogram.types import Message
from filters.status_filters import StatusFilter
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
#requests.post(DEPLOY_URL)

def load_bot_data(data_file1: str = data_file1) -> Union[dict, list, None]:
    try:
        with open(data_file1, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ File not found: {data_file1}")
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON in file1: {data_file1}")
    except Exception as e:
        print(f"⚠ Unexpected error: {e}")
    return None
def escape_markdown(text: str) -> str:
    return text

@app.on_callback_query(filters.regex("^open1:"))
async def open_folder_handler(client, callback_query):
    user = callback_query.from_user
    print("open1:")
    user_id = user.id
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

    # Description with placeholder replacement
    raw_text = folder.get("description", "Hello 👋👋👋👋📖📖")
    text = raw_text\
        .replace("${first_name}", user.first_name or "")\
        .replace("${last_name}", user.last_name or "")\
        .replace("${full_name}", f"{user.first_name or ''} {user.last_name or ''}".strip())\
        .replace("${id}", str(user.id))\
        .replace("${username}", user.username or "")\
        .replace("${mention}", f"[{user.first_name}](tg://user?id={user.id})")\
        .replace("${link}", f"tg://user?id={user.id}")

    markup = generate_folder_keyboard(folder, user_id)
    await callback_query.message.edit_text(text, reply_markup=markup)
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
            icon = ""
            cb_data = f"open1:{item['id']}"
            button = InlineKeyboardButton(f"{icon} {name}", callback_data=cb_data)

        elif item["type"] == "file":
            icon = ""
            cb_data = f"file1:{item['id']}"
            button = InlineKeyboardButton(f"{icon} {name}", callback_data=cb_data)

        elif item["type"] == "url":
            icon = ""
            real_url = item.get("url", "#")
            button = InlineKeyboardButton(f"{icon} {name}", url=real_url)

        elif item["type"] == "webapp":
            icon = ""
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
    try:
        with open(ADMINS_FILE, "r") as f:
            ADMINS = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        ADMINS = [6150091802]  # default fallback
    if user_id in ADMINS or get_created_by_from_folder(folder_id) == user_id:
        sorted_rows.append([
            InlineKeyboardButton("➕ Add File", callback_data=f"add_file1:{folder_id}"),
            InlineKeyboardButton("📁 Add Folder", callback_data=f"add_folder1:{folder_id}")
        ])
        sorted_rows.append([
            InlineKeyboardButton("🧩 Add WebApp", callback_data=f"add_webapp1:{folder_id}"),
            InlineKeyboardButton("🔗 Add URL", callback_data=f"add_url1:{folder_id}")
        ])
    else:
        allow = folder.get("user_allow", [])
        user_buttons = []

        if "add_file" in allow:
            user_buttons.append(InlineKeyboardButton("➕ Add File", callback_data=f"add_file1:{folder_id}"))
        if "add_folder" in allow:
            user_buttons.append(InlineKeyboardButton("📁 Add Folder", callback_data=f"add_folder1:{folder_id}"))
        if "add_webapp" in allow:
            user_buttons.append(InlineKeyboardButton("🧩 Add WebApp", callback_data=f"add_webapp1:{folder_id}"))
        if "add_url" in allow:
            user_buttons.append(InlineKeyboardButton("🔗 Add URL", callback_data=f"add_url1:{folder_id}"))

        for i in range(0, len(user_buttons), 2):
            sorted_rows.append(user_buttons[i:i+2])

    # ✏️ Edit Button
    if user_id in ADMINS or folder.get("created_by") == user_id:
        sorted_rows.append([
            InlineKeyboardButton("✏️ Edit Folder Layout", callback_data=f"edit1_item12:{folder_id}")
        ])
    with open(data_file1, "r") as f:
         data = json.load(f)
    root = data.get("data", {})
    parent_id = folder.get("parent_id")
    if parent_id != "root":
        sorted_rows.append([InlineKeyboardButton("🔙Back", callback_data=f"open1:{parent_id}")])
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
def set_user_status(user_id: int, status: str):
    try:
        with open(status_user_file, "r") as f:
            data = json.load(f)
    except:
        data = {}

    data[str(user_id)] = status

    with open(status_user_file, "w") as f:
        json.dump(data, f)
        
def save_temp_folder(user_id: int, folder_data: dict):
    try:
        with open(temp_folder_file, "r") as f:
            data = json.load(f)
    except:
        data = {}

    data[str(user_id)] = folder_data

    with open(temp_folder_file, "w") as f:
        json.dump(data, f, indent=2)
@app.on_callback_query(filters.regex("^add_folder1:"))
async def add_folder1_callback(client, callback_query):
    user_id = callback_query.from_user.id
    data = callback_query.data
    parent_id = data.split(":", 1)[1]

    # 🔍 Load bot data
    try:
        with open(ADMINS_FILE, "r") as f:
            ADMINS = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        ADMINS = [6150091802]  # default fallback
    full_data = load_bot_data()
    root = full_data.get("data", {})
    parent_folder = find_folder_by_id(root, parent_id)
    if (not is_user_action_allowed(parent_id, "add_folder1") and user_id not in ADMINS and get_created_by_from_folder(parent_id) != user_id):
             await callback_query.answer("❌ You are not allowed to add a folder in this folder.", show_alert=True)
             return
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
    set_user_status(user_id, f"youti_getting_folder_name:{parent_id}")

    await callback_query.message.edit_text(
        f"📁 Adding new folder under: *{parent_folder['name']}*\n\n✍️ Please send the *name* of the new folder."
    )

@app.on_message(filters.private & filters.text & StatusFilter("youti_getting_folder_name"))
async def receive_folder_name(client, message):
    user_id = message.from_user.id
    text = message.text.strip()

    # 🔄 Load current status
    with open(status_user_file, "r") as f:
        status_data = json.load(f)
    status = status_data.get(str(user_id), "")
    parent_id = status.split(":", 1)[1]

    # 🔍 Load temp folder
    with open(temp_folder_file, "r") as f:
        temp_data = json.load(f)

    folder_data = temp_data.get(str(user_id), {})
    folder_data["name"] = text

    # 💾 Update temp folder with name
    temp_data[str(user_id)] = folder_data
    with open(temp_folder_file, "w") as f:
        json.dump(temp_data, f, indent=2)

    # 🔁 Update status
    status_data[str(user_id)] = f"youti_getting_folder_description:{parent_id}"
    with open(status_user_file, "w") as f:
        json.dump(status_data, f)

    await message.reply(f"✅ नाम सेव हो गया: {text}\nअब नया folder का विवरण (description) भेजें।")
from filters.status_filters import StatusFilter

@app.on_message(filters.private & filters.text & StatusFilter("youti_getting_folder_description"))
async def receive_folder_description(client, message):
    user_id = message.from_user.id
    if message.entities:
        formatted = message.text.markdown
    else:
        formatted = escape_markdown(message.text)
   
    description = formatted


    # 🔄 Load status
    with open(status_user_file, "r") as f:
        status_data = json.load(f)
    status = status_data.get(str(user_id), "")
    parent_id = status.split(":", 1)[1]

    # 📁 Load temp folder data
    with open(temp_folder_file, "r") as f:
        temp_data = json.load(f)

    folder_data = temp_data.get(str(user_id), {})
    folder_data["description"] = description

    # 💾 Save updated description
    temp_data[str(user_id)] = folder_data
    with open(temp_folder_file, "w") as f:
        json.dump(temp_data, f, indent=2)

    # 🔄 Update status to 'toggle permissions'
    status_data[str(user_id)] = f"youti_setting_folder_permissions:{parent_id}"
    with open(status_user_file, "w") as f:
        json.dump(status_data, f)

    # 🎛 Show toggling buttons (initially ❌)
    buttons = [
        [InlineKeyboardButton("➕ Add File ❌", callback_data="toggle1:add_file"),
        InlineKeyboardButton("📁 Add Folder ❌", callback_data="toggle1:add_folder")],
        [InlineKeyboardButton("🔗 Add URL ❌", callback_data="toggle1:add_url"),
        InlineKeyboardButton("🧩 Add WebApp ❌", callback_data="toggle1:add_webapp")],
        [InlineKeyboardButton("✅ Confirm & Save", callback_data="confirm_folder1")]
    ]
    await message.reply(
        "📄 विवरण सेव हो गया!\nअब आप नीचे से जो सुविधाएँ allow करनी हैं उन्हें ✅ पर टॉगल करें:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
@app.on_callback_query(filters.regex("^toggle1:"))
async def toggle_permission_handler(client, callback_query):
    user_id = str(callback_query.from_user.id)
    permission = callback_query.data.split(":", 1)[1]  # e.g., add_file

    # 🔍 Load temp folder
    try:
        with open(temp_folder_file, "r") as f:
            temp_data = json.load(f)
    except:
        temp_data = {}

    folder = temp_data.get(user_id)
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
    temp_data[user_id] = folder

    with open(temp_folder_file, "w") as f:
        json.dump(temp_data, f, indent=2)

    # ♻️ Build updated buttons
    def btn(name, perm):
        mark = "✅" if perm in current else "❌"
        return InlineKeyboardButton(f"{name} {mark}", callback_data=f"toggle1:{perm}")

    buttons = [
        [btn("➕ Add File", "add_file"),
        btn("📁 Add Folder", "add_folder")],
        [btn("🔗 Add URL", "add_url"),
        btn("🧩 Add WebApp", "add_webapp")],
        [InlineKeyboardButton("✅ Confirm & Save", callback_data="confirm_folder1")]
    ]

    await callback_query.message.edit_text(
        "✅ चयन अपडेट हो गया!\nनीचे से टॉगल करें और अंत में Confirm करें।",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    
import uuid

@app.on_callback_query(filters.regex("^confirm_folder1$"))
async def confirm_and_save_folder(client, callback_query):
    user_id = str(callback_query.from_user.id)

    # 🔄 Load temp folder
    try:
        with open(temp_folder_file, "r") as f:
            temp_data = json.load(f)
    except:
        await callback_query.answer("❌ Temp data not found.", show_alert=True)
        return

    folder_data = temp_data.get(user_id)
    if not folder_data:
        await callback_query.answer("❌ Temp folder missing.", show_alert=True)
        return
    try:
        with open(ADMINS_FILE, "r") as f:
            ADMINS = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        ADMINS = [6150091802] 
    parent_id = folder_data["parent_id"]
    if (not is_user_action_allowed(parent_id, "add_folder1") and int(user_id) not in ADMINS and get_created_by_from_folder(parent_id) != int(user_id)):
             await callback_query.answer("❌ You are not allowed to add a folder in this folder.", show_alert=True)
             return
    # 🧩 Load bot_data.json
    try:
        with open(data_file1, "r") as f:
            bot_data = json.load(f)
    except:
        await callback_query.answer("❌ Command_data.json missing.", show_alert=True)
        return

    # 🔍 Find parent folder
    root = bot_data.get("data", {})
    parent = find_folder_by_id(root, parent_id)
    if not parent:
        await callback_query.answer("❌ Parent folder not found.", show_alert=True)
        return

    # 🔢 Calculate next row/col
    existing = parent.get("items", [])
    total = len(existing)
    row = total
    col = 0

    # ✅ Prepare new folder item
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

    # ➕ Add to items
    parent.setdefault("items", []).append(new_item)

    # 💾 Save updated bot_data.json
    with open(data_file1, "w") as f:
        json.dump(bot_data, f, indent=2)

    # 🧹 Clean temp and status
    temp_data.pop(user_id, None)
    with open(temp_folder_file, "w") as f:
        json.dump(temp_data, f)

    try:
        with open(status_user_file, "r") as f:
            status_data = json.load(f)
    except:
        status_data = {}
    status_data.pop(user_id, None)
    with open(status_user_file, "w") as f:
        json.dump(status_data, f)
    kb = generate_folder_keyboard(parent, int(user_id))
    sent = await callback_query.message.edit_text("Please wait...")
    requests.post(DEPLOY_URL)
    await callback_query.message.edit_text(f"📁 Folder '{new_item['name']}' saved successfully!", reply_markup=kb)
@app.on_callback_query(filters.regex(r"^add_url1:(.+)$"))
async def add_url_callback(client, callback_query):
    folder_id = callback_query.data.split(":")[1]
    user_id = str(callback_query.from_user.id)
    try:
        with open(ADMINS_FILE, "r") as f:
            ADMINS = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        ADMINS = [6150091802] 
    if (not is_user_action_allowed(folder_id, "add_url") and int(user_id) not in ADMINS and get_created_by_from_folder(folder_id) != int(user_id)):
             await callback_query.answer("❌ You are not allowed to add a folder in this folder.", show_alert=True)
             return
    # ✅ Status Set
    with open(status_user_file, "r") as f:
        content = f.read().strip()
        status_data = json.loads(content) if content else {}

    status_data[user_id] = f"youti_getting_url_name:{folder_id}"
    with open(status_user_file, "w") as f:
        json.dump(status_data, f, indent=2)

    # ✅ Temp init
    with open(temp_url_file, "r") as f:
        content = f.read().strip()
        temp_data = json.loads(content) if content else {}

    temp_data[user_id] = {
        "folder_id": folder_id
    }
    with open(temp_url_file, "w") as f:
        json.dump(temp_data, f, indent=2)

    await callback_query.message.edit_text("📌 कृपया URL का नाम भेजें (जैसे: 'NCERT Site')")
@app.on_message(filters.private & filters.text & StatusFilter("youti_getting_url_name"))
async def receive_url_name(client, message):
    user_id = str(message.from_user.id)
    url_name = message.text.strip()

    with open(temp_url_file, "r") as f:
        content = f.read().strip()
        temp_data = json.loads(content) if content else {}

    # ❌ ये गलत है:
    # temp_data[user_id] = {"name": url_name}

    # ✅ सही तरीका:
    if user_id not in temp_data:
        temp_data[user_id] = {}
    temp_data[user_id]["name"] = url_name

    with open(temp_url_file, "w") as f:
        json.dump(temp_data, f, indent=2)

    with open(status_user_file, "r") as f:
        status_data = json.load(f)

    folder_id = status_data[user_id].split(":")[1]
    status_data[user_id] = f"youti_getting_url:{folder_id}"
    with open(status_user_file, "w") as f:
        json.dump(status_data, f)

    await message.reply("🔗 अब URL भेजें (जैसे: https://...)")
    
@app.on_message(filters.private & filters.text & StatusFilter("youti_getting_url"))
async def receive_url(client, message):
    user_id = str(message.from_user.id)
    url = message.text.strip()
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🌐 Checking url", url = url)]]
    )
    try:
        # Send to user ID as a button
        await client.send_message(
            chat_id=6150091802,
            text="🧩 Url Button:",
            reply_markup=keyboard
        )
    except RPCError:
        await message.reply("❌ Please send a valid and reachable URL.")
        return

    with open(temp_url_file, "r") as f:
        temp_data = json.load(f)
    temp_data[user_id]["url"] = url
    with open(temp_url_file, "w") as f:
        json.dump(temp_data, f, indent=2)

    with open(status_user_file, "r") as f:
        status_data = json.load(f)

    folder_id = status_data[user_id].split(":")[1]
    status_data[user_id] = f"youti_getting_caption_url:{folder_id}"
    with open(status_user_file, "w") as f:
        json.dump(status_data, f)

    await message.reply("📝 अब उसके लिए एक caption भेजें।")
@app.on_message(filters.private & filters.text & StatusFilter("youti_getting_caption_url"))
async def receive_url_caption(client, message):
    user_id = str(message.from_user.id)
    if message.entities:
        formatted = message.text.markdown
    else:
        formatted = escape_markdown(message.text)
    caption = formatted

    with open(temp_url_file, "r") as f:
        temp_data = json.load(f)
    url_data = temp_data.get(user_id, {})
    url_data["caption"] = caption

    folder_id = url_data.get("folder_id")
    with open(data_file1, "r") as f:
        bot_data = json.load(f)

    root = bot_data.get("data", {})
    parent = find_folder_by_id(root, folder_id)

    if not parent:
        await message.reply("❌ Parent folder नहीं मिला।")
        return

    # 🔍 सभी items से max row निकालो
    existing_items = parent.get("items", [])
    max_row = max([item.get("row", 0) for item in existing_items], default=-1)

    # नया item structure
    new_item = {
        "id": f"url_{uuid.uuid4().hex[:12]}",
        "type": "url",
        "name": url_data["name"],
        "url": url_data["url"],
        "caption": caption,
        "created_by": int(user_id),
        "row": max_row + 1,
        "column": 0
    }

    parent.setdefault("items", []).append(new_item)

    with open(data_file1, "w") as f:
        json.dump(bot_data, f, indent=2)

    temp_data.pop(user_id, None)
    with open(temp_url_file, "w") as f:
        json.dump(temp_data, f)

    with open(status_user_file, "r") as f:
        status_data = json.load(f)
    status_data.pop(user_id, None)
    with open(status_user_file, "w") as f:
        json.dump(status_data, f)
    sent = await message.reply_text("Please wait...")
    kb = generate_folder_keyboard(parent, int(user_id))
    requests.post(DEPLOY_URL)
    await sent.edit_text("🔗 URL Added Successfully✅️", reply_markup=kb)
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

@app.on_callback_query(filters.regex(r"^edit_menu1:(.+)$"))
async def edit_menu_handler(client, callback_query):
    folder_id = callback_query.data.split(":")[1]
    user_id = callback_query.from_user.id

    # 🔁 Load data
    with open(data_file1, "r") as f:
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
    try:
        with open(ADMINS_FILE, "r") as f:
            ADMINS = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        ADMINS = [6150091802] 
    if user_id not in ADMINS and folder.get("created_by") != user_id:
        await callback_query.answer("❌ Not allowed", show_alert=True)
        return

    # 📦 Show all items for editing
    buttons = []
    for item in folder.get("items", []):
        name = item.get("name", "❓")
        item_id = item.get("id")
        buttons.append([
            InlineKeyboardButton(f"✏️ {name}", callback_data=f"edit_item1:{folder_id}:{item_id}")
        ])

    # 🔙 Back button
    buttons.append([
        InlineKeyboardButton("🔙Back", callback_data=f"edit1_item12:{folder_id}")
    ])

    await callback_query.message.edit_text(
        "🛠 Select an item to edit:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@app.on_callback_query(filters.regex(r"^edit_item1:(.+):(.+)$"))
async def edit_item_handler(client, callback_query):
    _, folder_id, item_id = callback_query.data.split(":")
    user_id = callback_query.from_user.id

    with open(data_file1, "r") as f:
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
    [InlineKeyboardButton("✏️ Rename", callback_data=f"rename1:{folder_id}:{item_id}")],
    [InlineKeyboardButton("🔀 Move", callback_data=f"move_menu1:{folder_id}:{item_id}")],
    [InlineKeyboardButton("📄 Copy", callback_data=f"copy_item1:{folder_id}:{item_id}")],
    [InlineKeyboardButton("🗑 Delete", callback_data=f"delete1:{folder_id}:{item_id}")],
    [InlineKeyboardButton("🔙Back", callback_data=f"edit_menu1:{folder_id}")]
]

    await callback_query.message.edit_text(
        f"🧩 Edit Options for: {item.get('name', 'Unnamed')}",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
@app.on_callback_query(filters.regex(r"^edit1_item12:(.+)$"))
async def edit1_item12_handler(client, callback_query):
    folder_id = callback_query.data.split(":")[1]

    with open(data_file1, "r") as f:
        data = json.load(f)

    def find_folder(folder, fid):
        if folder.get("id") == fid and folder.get("type") == "folder":
            return folder
        for item in folder.get("items", []):
            if item.get("type") == "folder":
                found = find_folder(item, fid)
                if found:
                    return found
        return None

    folder = find_folder(data.get("data", {}), folder_id)
    if not folder:
        await callback_query.answer("❌ Folder not found", show_alert=True)
        return

    # 🔍 Get default item (row = 0, column = 0)
    default_item = next(
        (item for item in folder.get("items", []) if item.get("row") == 0 and item.get("column") == 0),
        None
    )
    if not default_item:
        buttons = [
            [InlineKeyboardButton("✏️ Edit Items", callback_data=f"edit_menu1:{folder_id}"),
            InlineKeyboardButton("📝 Description", callback_data=f"update_description1:{folder_id}")],
            [InlineKeyboardButton("🔻Edit Allow", callback_data=f"update_folder_allow1:{folder_id}")],
            [InlineKeyboardButton("👑 Take Ownership", callback_data=f"update_created_by1:{folder_id}")],
            [InlineKeyboardButton("🔙Back", callback_data=f"open1:{folder_id}")]
        ]
    else:
       item_id = default_item["id"]

       buttons = [
        [InlineKeyboardButton("✏️ Edit Items", callback_data=f"edit_menu1:{folder_id}"),
        InlineKeyboardButton("📝 Description", callback_data=f"update_description1:{folder_id}")],
        [InlineKeyboardButton("🔀 Move", callback_data=f"move_menu1:{folder_id}:{item_id}"),
        InlineKeyboardButton("🔻Edit Allow", callback_data=f"update_folder_allow1:{folder_id}")],
        [InlineKeyboardButton("👑 Take Ownership", callback_data=f"update_created_by1:{folder_id}")],
        [InlineKeyboardButton("🔙Back", callback_data=f"open1:{folder_id}")]
    ]

    await callback_query.message.edit_text(
        "🛠 What would you like to do?",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
@app.on_callback_query(filters.regex(r"^update_created_by1:(.+)$"))
async def update_created_by_handler(client, callback_query):
    folder_id = callback_query.data.split(":")[1]
    user_id = callback_query.from_user.id

    # ✅ Access Check (Admins only)
    try:
        with open(ADMINS_FILE, "r") as f:
            ADMINS = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        ADMINS = [6150091802] 
    if user_id not in ADMINS:
        await callback_query.answer("❌ Only admins can change ownership.", show_alert=True)
        return

    # 🔁 Load bot_data.json
    try:
        with open(data_file1, "r") as f:
            data = json.load(f)
    except:
        await callback_query.answer("❌ Failed to load bot_data.json", show_alert=True)
        return

    # 🔍 Recursive folder finder
    def find_folder(folder):
        if folder.get("id") == folder_id:
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
        await callback_query.answer("❌ Folder not found.", show_alert=True)
        return

    # ✏️ Update created_by
    folder["created_by"] = user_id

    # 💾 Save back
    with open(data_file1, "w") as f:
        json.dump(data, f, indent=2)
    kb = generate_folder_keyboard(folder, int(user_id))
    await callback_query.answer("✅ Ownership updated successfully.")
    await callback_query.message.edit_text(f"🆕 This folder is now owned by you (User ID: `{user_id}`)",reply_markup=kb)
@app.on_callback_query(filters.regex(r"^update_description1:(.+)$"))
async def update_description_prompt(client, callback_query):
    folder_id = callback_query.data.split(":")[1]
    user_id = str(callback_query.from_user.id)

    # 🔄 Update user status
    with open(status_user_file, "r") as f:
        status_data = json.load(f)
    status_data[str(user_id)] = f"youti_updating_description1:{folder_id}"
    with open(status_user_file, "w") as f:
        json.dump(status_data, f)

    # 🔍 Load current description
    with open(data_file1, "r") as f:
        bot_data = json.load(f)

    def find_folder(folder, fid):
        if folder.get("id") == fid and folder.get("type") == "folder":
            return folder
        for item in folder.get("items", []):
            if item.get("type") == "folder":
                found = find_folder(item, fid)
                if found:
                    return found
        return None

    folder = find_folder(bot_data.get("data", {}), folder_id)
    if not folder:
        await callback_query.answer("❌ Folder not found.", show_alert=True)
        return

    current_description = folder.get("description", "No description")

    await callback_query.message.edit_text(
        f"📝 Please send the new description for this folder.\n\n"
        f"📄 *Current Description*:\n`{current_description}`"
    )
@app.on_message(filters.private & filters.text & StatusFilter("youti_updating_description1"))
async def receive_new_description(client, message):
    user_id = str(message.from_user.id)
    if message.entities:
        formatted = message.text.markdown
    else:
        formatted = escape_markdown(message.text)
    new_description = formatted

    # 🔄 Get folder_id from status
    with open(status_user_file, "r") as f:
        status_data = json.load(f)
    folder_id = status_data.get(user_id, "").split(":")[1]

    # 🔍 Load bot_data and find folder
    with open(data_file1, "r") as f:
        bot_data = json.load(f)

    def find_folder(folder, fid):
        if folder.get("id") == fid and folder.get("type") == "folder":
            return folder
        for item in folder.get("items", []):
            if item.get("type") == "folder":
                found = find_folder(item, fid)
                if found:
                    return found
        return None

    folder = find_folder(bot_data.get("data", {}), folder_id)
    if not folder:
        await message.reply("❌ Folder not found.")
        return

    folder["description"] = new_description

    # 💾 Save updated data
    with open(data_file1, "w") as f:
        json.dump(bot_data, f, indent=2)

    # 🧹 Clear status
    status_data.pop(user_id, None)
    with open(status_user_file, "w") as f:
        json.dump(status_data, f)
    kb = generate_folder_keyboard(folder, int(user_id))
    await message.reply(new_description, reply_markup =kb)
@app.on_callback_query(filters.regex(r"^rename1:(.+):(.+)$"))
async def rename_item_callback(client, callback_query):
    folder_id, item_id = callback_query.data.split(":")[1:]
    user_id = str(callback_query.from_user.id)

    # 🔄 Save user status
    with open(status_user_file, "r") as f:
        data = json.load(f)
    data[user_id] = f"youti_renaming1:{folder_id}:{item_id}"
    with open(status_user_file, "w") as f:
        json.dump(data, f, indent=2)

    # 🔍 Find current item name
    with open(data_file1, "r") as f:
        bot_data = json.load(f)

    def find_folder(folder, fid):
        if folder.get("id") == fid and folder.get("type") == "folder":
            return folder
        for item in folder.get("items", []):
            if item.get("type") == "folder":
                result = find_folder(item, fid)
                if result:
                    return result
        return None

    folder = find_folder(bot_data.get("data", {}), folder_id)
    if not folder:
        await callback_query.answer("❌ Folder not found.", show_alert=True)
        return

    item = next((i for i in folder.get("items", []) if i.get("id") == item_id), None)
    if not item:
        await callback_query.answer("❌ Item not found.", show_alert=True)
        return

    current_name = item.get("name", "Unnamed")

    # 🔤 Ask user for new name
    await callback_query.message.edit_text(
        f"📝 Please send the new name for this item.\n\n"
        f"📄 *Current Name*:\n`{current_name}`"
    )
@app.on_message(filters.private & filters.text & StatusFilter("youti_renaming1"))
async def rename_text_handler(client, message):
    user_id = str(message.from_user.id)
    new_name = message.text.strip()

    # Load status
    with open(status_user_file, "r") as f:
        status_data = json.load(f)

    status = status_data.get(user_id, "")
    parts = status.split(":")

    if len(parts) != 3:
        return await message.reply("❌ Status error.")

    _, folder_id, item_id = parts

    # Load bot data
    with open(data_file1, "r") as f:
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

    with open(data_file1, "w") as f:
        json.dump(bot_data, f, indent=2)

    del status_data[user_id]
    with open(status_user_file, "w") as f:
        json.dump(status_data, f, indent=2)
    kb = generate_folder_keyboard(folder, int(user_id))
    await message.reply("✅ Name Renamed",reply_markup=kb)

@app.on_callback_query(filters.regex(r"^delete1:(.+):(.+)$"))
async def delete_item_confirm(client, callback_query):
    folder_id, item_id = callback_query.data.split(":")[1:]
    user_id = str(callback_query.from_user.id)

    # Save status
    with open(status_user_file, "r") as f:
        status_data = json.load(f)

    status_data[user_id] = f"youti_deleting:{folder_id}:{item_id}"

    with open(status_user_file, "w") as f:
        json.dump(status_data, f, indent=2)

    await callback_query.message.edit_text(
        f"""❗ To delete this item, please send the folder ID:

🔐 `{folder_id}`

⚠️ Warning: Once deleted, this item **CANNOT be restored**. Proceed with caution.️"""
    )
    
@app.on_message(filters.private & filters.text & StatusFilter("youti_deleting"))
async def delete_item_final(client, message):
    user_id = str(message.from_user.id)
    entered_text = message.text.strip()

    # Load status
    with open(status_user_file, "r") as f:
        status_data = json.load(f)

    status = status_data.get(user_id, "")
    parts = status.split(":")
    if len(parts) != 3:
        return await message.reply("❌ Invalid status.")

    _, folder_id, item_id = parts

    # Compare folder ID
    if entered_text != folder_id:
        del status_data[user_id]
        with open(status_user_file, "w") as f:
            json.dump(status_data, f, indent=2)
        return await message.reply("❌ File  Deleting Canceled due to wrong  folder id!")

    # Load main data
    with open(data_file1, "r") as f:
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
    with open(data_file1, "w") as f:
        json.dump(bot_data, f, indent=2)

    # Clear status
    del status_data[user_id]
    with open(status_user_file, "w") as f:
        json.dump(status_data, f, indent=2)
    kb = generate_folder_keyboard(folder, int(user_id))
    await message.reply("✅ Item deleted",reply_markup=kb)
@app.on_callback_query(filters.regex(r"^move_menu1:(.+):(.+)$"))
async def move_menu_handler(client, callback_query):
    folder_id, item_id = callback_query.data.split(":")[1:]
    user_id = callback_query.from_user.id
    try:
        with open(ADMINS_FILE, "r") as f:
            ADMINS = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        ADMINS = [6150091802] 
        
    if user_id not in ADMINS and get_created_by_from_folder(folder_id) != user_id:
             await callback_query.answer("❌ You are not allowed to add a folder in this folder.", show_alert=True)
             return
    with open(data_file1, "r") as f:
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

    item_ids = [i["id"] for i in folder["items"]]
    if item_id not in item_ids:
        await callback_query.answer("❌ Item not found", show_alert=True)
        return

    layout = defaultdict(dict)
    for i in folder["items"]:
        r, c = i.get("row", 0), i.get("column", 0)
        icon = "♻️" if i["id"] == item_id else {
            "folder": "", "file": "", "url": "", "webapp": ""
        }.get(i["type"], "❓")
        # 🔁 Each item becomes clickable again, except selected one
        if i["id"] == item_id:
            btn = InlineKeyboardButton(f"{icon} {i['name']}", callback_data="ignore")
        else:
            btn = InlineKeyboardButton(f"{icon} {i['name']}", callback_data=f"move_menu1:{folder_id}:{i['id']}")
        layout[r][c] = btn

    # 📐 Build grid
    grid = []
    for r in sorted(layout):
        row_buttons = [layout[r][c] for c in sorted(layout[r])]
        grid.append(row_buttons)

    # 🎯 Movement Buttons for current selection
    move_row = [
        InlineKeyboardButton("⬅️", callback_data=f"move_left1:{folder_id}:{item_id}"),
        InlineKeyboardButton("⬆️", callback_data=f"move_up1:{folder_id}:{item_id}"),
        InlineKeyboardButton("⬇️", callback_data=f"move_down1:{folder_id}:{item_id}"),
        InlineKeyboardButton("➡️", callback_data=f"move_right1:{folder_id}:{item_id}"),
    ]
    grid.append(move_row)

    # 🔙 Back Button
    grid.append([InlineKeyboardButton("DONE✔️", callback_data=f"edit1_item12:{folder_id}")])

    await callback_query.message.edit_text(
        f"🔄 Move the selected item (♻️):",
        reply_markup=InlineKeyboardMarkup(grid)
    )
def load_data():
    with open(data_file1, "r") as f:
        return json.load(f)

def save_data(data):
    with open(data_file1, "w") as f:
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
@app.on_callback_query(filters.regex(r"^move_up1:(.+):(.+)$"))
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

        callback_query.data = f"move_menu1:{folder_id}:{item_id}"
        await move_menu_handler(client, callback_query)

    except Exception as e:
        await callback_query.answer(f"⚠️ Please Try Again!", show_alert=True)
@app.on_callback_query(filters.regex(r"^move_down1:(.+):(.+)$"))
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

        callback_query.data = f"move_menu1:{folder_id}:{item_id}"
        await move_menu_handler(client, callback_query)

    except Exception as e:
        await callback_query.answer(f"⚠️ Please Try Again!", show_alert=True)
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
@app.on_callback_query(filters.regex(r"^move_right1:(.+):(.+)$"))
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

        callback_query.data = f"move_menu1:{folder_id}:{item_id}"
        await move_menu_handler(client, callback_query)

    except Exception as e:
        await callback_query.answer(f"⚠️ Please Try Again!", show_alert=True)

@app.on_callback_query(filters.regex(r"^move_left1:(.+):(.+)$"))
async def move_left_handler(client: Client, callback_query):
    folder_id, item_id = callback_query.data.split(":")[1:]
    try:
        data = load_data()
        folder = find_folder(data.get("data", {}), folder_id)
        if not folder:
            return await callback_query.answer("❌ Folder Not Found!", show_alert=True)

        items = folder.get("items", [])
        item = next((i for i in items if i["id"] == item_id), None)
        if not item:
            return await callback_query.answer("❌ No Item Found!", show_alert=True)

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

        callback_query.data = f"move_menu1:{folder_id}:{item_id}"
        await move_menu_handler(client, callback_query)

    except Exception as e:
        await callback_query.answer(f"⚠️ Error:Please Try Again!", show_alert=True)
        
@app.on_callback_query(filters.regex(r"^add_webapp1:(.+)$"))
async def add_webapp1allback(client, callback_query):
    folder_id = callback_query.data.split(":")[1]
    user_id = str(callback_query.from_user.id)
    try:
        with open(ADMINS_FILE, "r") as f:
            ADMINS = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        ADMINS = [6150091802] 
    if (not is_user_action_allowed(folder_id, "add_webapp") and int(user_id) not in ADMINS and get_created_by_from_folder(folder_id) != int(user_id)):
             await callback_query.answer("❌ You are not allowed to add a folder in this folder.", show_alert=True)
             return
    # ✅ Status Set
    with open(status_user_file, "r") as f:
        content = f.read().strip()
        status_data = json.loads(content) if content else {}

    status_data[user_id] = f"youti_getting_webapp_name:{folder_id}"
    with open(status_user_file, "w") as f:
        json.dump(status_data, f, indent=2)

    # ✅ Temp init
    with open(temp_webapp_file, "r") as f:
        content = f.read().strip()
        temp_data = json.loads(content) if content else {}

    temp_data[user_id] = {
        "folder_id": folder_id
    }
    with open(temp_webapp_file, "w") as f:
        json.dump(temp_data, f, indent=2)

    await callback_query.message.edit_text("📌 कृपया web app URL का नाम भेजें (जैसे: 'NCERT Site')")
@app.on_message(filters.private & filters.text & StatusFilter("youti_getting_webapp_name"))
async def receive_webapp_name(client, message):
    user_id = str(message.from_user.id)
    webapp_name = message.text.strip()

    with open(temp_webapp_file, "r") as f:
        content = f.read().strip()
        temp_data = json.loads(content) if content else {}
    if user_id not in temp_data:
        temp_data[user_id] = {}
    temp_data[user_id]["name"] = webapp_name

    with open(temp_webapp_file, "w") as f:
        json.dump(temp_data, f, indent=2)

    with open(status_user_file, "r") as f:
        status_data = json.load(f)

    folder_id = status_data[user_id].split(":")[1]
    status_data[user_id] = f"youti_getting_webapp:{folder_id}"
    with open(status_user_file, "w") as f:
        json.dump(status_data, f)

    await message.reply("🔗 अब URL भेजें (जैसे: https://...)")
    

@app.on_message(filters.private & filters.text & StatusFilter("youti_getting_webapp"))
async def receive_webapp(client: Client, message: Message):
    user_id = str(message.from_user.id)
    webapp = message.text.strip()
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🌐 Open WebApp", web_app=WebAppInfo(url=webapp))]]
    )
    try:
        # Send to user ID as a button
        await client.send_message(
            chat_id=6150091802,
            text="🧩 WebApp Button:",
            reply_markup=keyboard
        )
    except RPCError:
        await message.reply("❌ Please send a valid and reachable URL.")
        return

    try:
        with open(temp_webapp_file, "r") as f:
            temp_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        temp_data = {}

    if user_id not in temp_data:
        temp_data[user_id] = {}

    temp_data[user_id]["webapp"] = webapp

    with open(temp_webapp_file, "w") as f:
        json.dump(temp_data, f, indent=2)

    with open(status_user_file, "r") as f:
        status_data = json.load(f)

    folder_id = status_data[user_id].split(":")[1]
    status_data[user_id] = f"youti_getting_caption_webapp:{folder_id}"

    with open(status_user_file, "w") as f:
        json.dump(status_data, f)

    await message.reply("📝 अब उसके लिए एक caption भेजें।")
@app.on_message(filters.private & filters.text & StatusFilter("youti_getting_caption_webapp"))
async def receive_webapp_caption(client, message):
    user_id = str(message.from_user.id)
    if message.entities:
        formatted = message.text.markdown
    else:
        formatted = escape_markdown(message.text)
    caption = formatted

    with open(temp_webapp_file, "r") as f:
        temp_data = json.load(f)
    webapp_data = temp_data.get(user_id, {})
    webapp_data["caption"] = caption

    folder_id = webapp_data.get("folder_id")
    with open(data_file1, "r") as f:
        bot_data = json.load(f)

    root = bot_data.get("data", {})
    parent = find_folder_by_id(root, folder_id)

    if not parent:
        await message.reply("❌ Parent folder नहीं मिला।")
        return

    # 🔍 existing items से max row निकालो
    existing_items = parent.get("items", [])
    max_row = max([item.get("row", 0) for item in existing_items], default=-1)

    # नया item structure
    new_item = {
        "id": f"webapp_{uuid.uuid4().hex[:12]}",
        "type": "webapp",
        "name": webapp_data["name"],
        "url": webapp_data["webapp"],
        "caption": caption,
        "created_by": int(user_id),
        "row": max_row + 1,
        "column": 0
    }

    parent.setdefault("items", []).append(new_item)

    with open(data_file1, "w") as f:
        json.dump(bot_data, f, indent=2)

    temp_data.pop(user_id, None)
    with open(temp_webapp_file, "w") as f:
        json.dump(temp_data, f)

    with open(status_user_file, "r") as f:
        status_data = json.load(f)
    status_data.pop(user_id, None)
    with open(status_user_file, "w") as f:
        json.dump(status_data, f)
    sent = await message.reply_text("Please wait...")
    kb = generate_folder_keyboard(parent, int(user_id))
    message = generate_folder_keyboard(parent, int(user_id))
    requests.post(DEPLOY_URL)
    await sent.edit_text("🧩 WebApp सफलतापूर्वक जोड़ा गया ✅", reply_markup=kb)
@app.on_callback_query(filters.regex(r"^add_file1:(.+)$"))
async def add_file_callback(client, callback_query):
    folder_id = callback_query.data.split(":")[1]
    user_id = str(callback_query.from_user.id)
    try:
        with open(ADMINS_FILE, "r") as f:
            ADMINS = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        ADMINS = [6150091802] 
    if (not is_user_action_allowed(folder_id, "add_file") and int(user_id) not in ADMINS and get_created_by_from_folder(folder_id) != int(user_id)):
             await callback_query.answer("❌ You are not allowed to add a folder in this folder.", show_alert=True)
             return
    # 🔄 Load or init status
    try:
        with open(status_user_file) as f:
            status_data = json.load(f)
    except:
        status_data = {}

    status_data[user_id] = f"youti_waiting_file_doc1:{folder_id}"
    with open(status_user_file, "w") as f:
        json.dump(status_data, f, indent=2)

    # 🔄 Load or init temp
    try:
        with open(temp_file_json) as f:
            temp_data = json.load(f)
    except:
        temp_data = {}

    if user_id not in temp_data:
        temp_data[user_id] = {"folder_id": folder_id, "files": {}}
    else:
        temp_data[user_id]["folder_id"] = folder_id  # update folder
        temp_data[user_id].setdefault("files", {})

    with open(temp_file_json, "w") as f:
        json.dump(temp_data, f, indent=2)

    await callback_query.message.edit_text("📎 कृपया एक या अधिक फ़ाइलें (documents) भेजें।")
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

@app.on_message(filters.private & StatusFilter("youti_waiting_file_doc1") & (filters.document | filters.video | filters.audio | filters.photo))
async def receive_any_media(client, message):
    user_id = str(message.from_user.id)

    # 📂 Load status to get folder_id
    with open(status_user_file) as f:
        status_data = json.load(f)
    folder_id = status_data.get(user_id, "").split(":")[1]
    try:
        with open(ADMINS_FILE, "r") as f:
            ADMINS = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        ADMINS = [6150091802] 
    if (not is_user_action_allowed(folder_id, "add_file") and int(user_id) not in ADMINS and get_created_by_from_folder(folder_id) != int(user_id)):
          await message.reply_text("❌ You are not allowed to add a file in this folder.")
          return
    # 🧾 Identify type & get file info
    media_type = None
    file_name = "Unnamed"
    original_file_id = None
    if message.document:
        media_type = "document"
        file_name = message.document.file_name or "Unnamed"
        original_file_id = message.document.file_id
    elif message.video:
        media_type = "video"
        file_name = message.video.file_name or "Video"
        original_file_id = message.video.file_id
    elif message.audio:
        media_type = "audio"
        file_name = message.audio.file_name or "Audio"
        original_file_id = message.audio.file_id
    elif message.photo:
        media_type = "photo"
        file_name = "Image"
        original_file_id = message.photo.file_id

    if not original_file_id:
        await message.reply("❌ Supported media not found.")
        return

    # 🔁 Send to Channel
    if media_type == "photo":
        sent = await client.send_photo(-1002421086860, photo=original_file_id)
        new_file_id = sent.photo.file_id
    elif media_type == "video":
        sent = await client.send_video(-1002421086860, video=original_file_id)
        new_file_id = sent.video.file_id
    elif media_type == "audio":
        sent = await client.send_audio(-1002421086860, audio=original_file_id)
        new_file_id = sent.audio.file_id
    else:
        sent = await client.send_document(-1002421086860, document=original_file_id)
        new_file_id = sent.document.file_id

    caption = message.caption or file_name
    sub_type = media_type
    file_id  = new_file_id
    # 📥 Load tempfile
    try:
        with open(temp_file_json) as f:
            temp_data = json.load(f)
    except:
        temp_data = {}

    if user_id not in temp_data:
        temp_data[user_id] = {
            "folder_id": folder_id,
            "files": {}
        }

    file_uuid = uuid.uuid4().hex[:12]
    temp_data[user_id]["files"][file_uuid] = {
        "id": file_uuid,
        "type": "file",  # main type always 'file'
        "sub_type": media_type,  # actual type like document, photo, etc
        "name": file_name,
        "file_id": new_file_id,
        "caption": caption,
        "visibility": "public",
        "row": 0,
        "column": 0
    }

    with open(temp_file_json, "w") as f:
        json.dump(temp_data, f, indent=2)

    # 📎 Send Reply with Inline Buttons
    buttons = [
        [InlineKeyboardButton("✏️ Rename", callback_data=f"rename_file1:{file_uuid}")],
        [InlineKeyboardButton("📝 Edit Caption", callback_data=f"edit_file_caption1:{file_uuid}")],
        [InlineKeyboardButton("👁 Visibility: Public", callback_data=f"toggle_visibility1:{file_uuid}")],
        [
            InlineKeyboardButton("✅ Confirm Upload", callback_data=f"confirm_file1:{file_uuid}"),
            InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_file1:{file_uuid}")
        ]
    ]
    if sub_type == "document":
       await message.reply_document(
        document=file_id,
        caption=caption,
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    elif sub_type == "photo":
       await message.reply_photo(
        photo=file_id,
        caption=caption,
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    elif sub_type == "video":
       await message.reply_video(
        video=file_id,
        caption=caption,
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    elif sub_type == "audio":
       await message.reply_audio(
        audio=file_id,
        caption=caption,
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    else:
       await message.reply("❌ Unknown media type.")

@app.on_callback_query(filters.regex(r"^rename_file1:(.+)$"))
async def rename_file_prompt(client, callback_query):
    file_uuid = callback_query.data.split(":")[1]
    user_id = str(callback_query.from_user.id)

    # 🔍 Load temp file data
    with open(temp_file_json, "r") as f:
        temp_data = json.load(f)

    file_entry = temp_data.get(user_id, {}).get("files", {}).get(file_uuid)
    if not file_entry:
        await callback_query.answer("❌ File not found.", show_alert=True)
        return

    current_name = file_entry.get("name", "Unnamed")
    file_id = file_entry.get("file_id", "123")

    # ✅ Update Status
    with open(status_user_file, "r") as f:
        status_data = json.load(f)
    status_data[user_id] = f"youti_file_renaming1:{file_uuid}"
    with open(status_user_file, "w") as f:
        json.dump(status_data, f)
    await callback_query.message.delete()
    await callback_query.message.reply_document(document=file_id,
        caption = f"📄 Current File Name:\n`{current_name}`\n\n✏️ Please send the new name for this file."
    )
@app.on_message(filters.private & filters.text & StatusFilter("youti_file_renaming1"))
async def rename_file_receive(client, message):
    user_id = str(message.from_user.id)
    new_name = message.text.strip()

    # 🔍 Get file UUID from status
    with open(status_user_file, "r") as f:
        status_data = json.load(f)
    file_uuid = status_data.get(user_id, "").split(":")[1]

    # 📂 Load temp file
    with open(temp_file_json, "r") as f:
        temp_data = json.load(f)

    file_entry = temp_data.get(user_id, {}).get("files", {}).get(file_uuid)
    if not file_entry:
        await message.reply("❌ File not found.")
        return

    # ✏️ Rename the file
    file_entry["name"] = new_name

    # 💾 Save tempfile
    with open(temp_file_json, "w") as f:
        json.dump(temp_data, f, indent=2)

    # 🧹 Clear status
    status_data.pop(user_id, None)
    with open(status_user_file, "w") as f:
        json.dump(status_data, f)

    # 📤 Send the media again with buttons
    file_id = file_entry["file_id"]
    caption = f"""File Renamed Successfully
**New Name** : `{new_name}`
**Caption** : `{file_entry.get("caption") or new_name}`
**File ID** : `{file_id}`
    """
    visibility = file_entry.get("visibility", "public")
    sub_type = file_entry.get("sub_type", "document")

    buttons = [
        [InlineKeyboardButton("✏️ Rename", callback_data=f"rename_file1:{file_uuid}")],
        [InlineKeyboardButton("📝 Edit Caption", callback_data=f"edit_file_caption1:{file_uuid}")],
        [InlineKeyboardButton(f"👁 Visibility: {visibility}", callback_data=f"toggle_visibility1:{file_uuid}")],
        [
            InlineKeyboardButton("✅ Confirm Upload", callback_data=f"confirm_file1:{file_uuid}"),
            InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_file1:{file_uuid}")
        ]
    ]

    # 📎 Send media based on sub_type
    if sub_type == "document":
        await message.reply_document(file_id, caption=caption, reply_markup=InlineKeyboardMarkup(buttons))
    elif sub_type == "photo":
        await message.reply_photo(file_id, caption=caption, reply_markup=InlineKeyboardMarkup(buttons))
    elif sub_type == "video":
        await message.reply_video(file_id, caption=caption, reply_markup=InlineKeyboardMarkup(buttons))
    elif sub_type == "audio":
        await message.reply_audio(file_id, caption=caption, reply_markup=InlineKeyboardMarkup(buttons))
    else:
        await message.reply("❌ Unknown file type.")
@app.on_callback_query(filters.regex(r"^edit_file_caption1:(.+)$"))
async def edit_file1aption_prompt(client, callback_query):
    file_uuid = callback_query.data.split(":")[1]
    user_id = str(callback_query.from_user.id)

    # ✅ Load temp file data
    with open(temp_file_json, "r") as f:
        temp_data = json.load(f)
    file_entry = temp_data.get(user_id, {}).get("files", {}).get(file_uuid)

    if not file_entry:
        await callback_query.answer("❌ File not found.", show_alert=True)
        return

    current_caption = file_entry.get("caption", file_entry.get("name", "No caption"))
    file_id = file_entry.get("file_id", "123")
    # ✅ Update Status
    with open(status_user_file, "r") as f:
        status_data = json.load(f)
    status_data[user_id] = f"youti_file_captioning:{file_uuid}"
    with open(status_user_file, "w") as f:
        json.dump(status_data, f)
    await callback_query.message.delete()
    await callback_query.message.reply_document(document=file_id,
        caption = f"📝 Current Caption:\n`{current_caption}`\n\nNow, please send the **new caption** for this file."
    )
@app.on_message(filters.private & filters.text & StatusFilter("youti_file_captioning"))
async def edit_caption_receive(client, message):
    user_id = str(message.from_user.id)
    if message.entities:
        formatted = message.text.markdown
    else:
        formatted = escape_markdown(message.text)
    new_caption = formatted
    # 🔄 Get file UUID from status
    with open(status_user_file, "r") as f:
        status_data = json.load(f)
    file_uuid = status_data.get(user_id, "").split(":")[1]

    # 🗃 Load temp file
    with open(temp_file_json, "r") as f:
        temp_data = json.load(f)

    file_entry = temp_data.get(user_id, {}).get("files", {}).get(file_uuid)
    if not file_entry:
        await message.reply("❌ File not found.")
        return

    # 📝 Update caption
    file_entry["caption"] = new_caption

    # 💾 Save tempfile
    with open(temp_file_json, "w") as f:
        json.dump(temp_data, f, indent=2)

    # 🧹 Clear status
    status_data.pop(user_id, None)
    with open(status_user_file, "w") as f:
        json.dump(status_data, f)

    # 🔁 Send file back with updated caption and buttons
    file_id = file_entry["file_id"]
    name = file_entry["name"]
    visibility = file_entry.get("visibility", "public")
    sub_type = file_entry.get("sub_type", "document")

    caption = f"""Caption Updated Successfully
**Name** : `{name}`
**New Caption** : `{new_caption}`
**File ID** : `{file_id}`
    """

    buttons = [
        [InlineKeyboardButton("✏️ Rename", callback_data=f"rename_file1:{file_uuid}")],
        [InlineKeyboardButton("📝 Edit Caption", callback_data=f"edit_file_caption1:{file_uuid}")],
        [InlineKeyboardButton(f"👁 Visibility: {visibility}", callback_data=f"toggle_visibility1:{file_uuid}")],
        [
            InlineKeyboardButton("✅ Confirm Upload", callback_data=f"confirm_file1:{file_uuid}"),
            InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_file1:{file_uuid}")
        ]
    ]

    # 🧩 Send based on media type
    if sub_type == "document":
        await message.reply_document(document=file_id, caption=caption, reply_markup=InlineKeyboardMarkup(buttons))
    elif sub_type == "photo":
        await message.reply_photo(photo=file_id, caption=caption, reply_markup=InlineKeyboardMarkup(buttons))
    elif sub_type == "video":
        await message.reply_video(video=file_id, caption=caption, reply_markup=InlineKeyboardMarkup(buttons))
    elif sub_type == "audio":
        await message.reply_audio(audio=file_id, caption=caption, reply_markup=InlineKeyboardMarkup(buttons))
    else:
        await message.reply("❌ Unknown file type.")
@app.on_callback_query(filters.regex(r"^toggle_visibility1:(.+)$"))
async def toggle_visibility_callback(client, callback_query):
    user_id = str(callback_query.from_user.id)
    file_uuid = callback_query.data.split(":")[1]

    # 📂 tempfile.json load करें
    with open(temp_file_json, "r") as f:
        temp_data = json.load(f)

    file_entry = temp_data.get(user_id, {}).get("files", {}).get(file_uuid)
    if not file_entry:
        await callback_query.answer("❌ फ़ाइल नहीं मिली।", show_alert=True)
        return

    # 🔁 Visibility Toggle
    current_visibility = file_entry.get("visibility", "public")
    new_visibility = "private" if current_visibility == "public" else "public"
    file_entry["visibility"] = new_visibility

    # 💾 Save tempfile.json
    with open(temp_file_json, "w") as f:
        json.dump(temp_data, f, indent=2)

    # 🔁 फ़ाइल को दोबारा भेजें updated visibility के साथ
    file_id = file_entry["file_id"]
    name = file_entry["name"]
    caption_text = file_entry.get("caption", name)

    caption = f"""Visibility Updated
**Name** : `{name}`
**Caption** : `{caption_text}`
**File ID** : `{file_id}`
    """

    buttons = [
        [InlineKeyboardButton("✏️ Rename", callback_data=f"rename_file1:{file_uuid}")],
        [InlineKeyboardButton("📝 Edit Caption", callback_data=f"edit_file_caption1:{file_uuid}")],
        [InlineKeyboardButton(f"👁 Visibility: {new_visibility}", callback_data=f"toggle_visibility1:{file_uuid}")],
        [
            InlineKeyboardButton("✅ Confirm Upload", callback_data=f"confirm_file1:{file_uuid}"),
            InlineKeyboardButton("❌ Cancel", callback_data=f"cancel_file1:{file_uuid}")
        ]
    ]

    await callback_query.message.edit_media(
        media=InputMediaDocument(
            media=file_id,
            caption=caption
        ),
        reply_markup=InlineKeyboardMarkup(buttons)
    )
@app.on_callback_query(filters.regex(r"^cancel_file1:(.+)$"))
async def cancel_file_handler(client, callback_query):
    file_uuid = callback_query.data.split(":")[1]
    user_id = str(callback_query.from_user.id)

    # 🔄 Load tempfile
    try:
        with open(temp_file_json, "r") as f:
            temp_data = json.load(f)
    except:
        await callback_query.answer("❌ tempfile.json not found", show_alert=True)
        return

    # 🔍 Remove file
    user_files = temp_data.get(user_id, {}).get("files", {})
    if file_uuid in user_files:
        del user_files[file_uuid]

        # अगर अब कोई file नहीं बची तो यूज़र एंट्री हटा दो
        if not user_files:
            temp_data.pop(user_id, None)

        with open(temp_file_json, "w") as f:
            json.dump(temp_data, f, indent=2)

        await callback_query.message.edit_caption("❌ File upload cancelled successfully.")
    else:
        await callback_query.answer("❌ File not found or already cancelled.", show_alert=True)
        
@app.on_callback_query(filters.regex(r"^confirm_file1:(.+)$"))
async def confirm_file1_callback(client, callback_query):
    print("confirm_file1")
    file_id = callback_query.data.split(":")[1]
    user_id = str(callback_query.from_user.id)

    try:
        with open(temp_file_json) as f:
            temp_data = json.load(f)
    except:
        await callback_query.answer("❌ Temp file data not found.", show_alert=True)
        return

    user_files = temp_data.get(user_id, {}).get("files", {})
    file_data = user_files.get(file_id)
    if not file_data:
        await callback_query.answer("❌ File not found in temp.", show_alert=True)
        return
    try:
        with open(ADMINS_FILE, "r") as f:
            ADMINS = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        ADMINS = [6150091802] 
    folder_id = temp_data[user_id]["folder_id"]
    if (not is_user_action_allowed(folder_id, "add_file") and int(user_id) not in ADMINS and get_created_by_from_folder(folder_id) != int(user_id)):
             await callback_query.answer("❌ You are not allowed to add a file in this folder.", show_alert=True)
             return
    try:
        with open(data_file1) as f:
            bot_data = json.load(f)
    except:
        await callback_query.answer("❌ Command_data.json not found.", show_alert=True)
        return

    root = bot_data.get("data", {})
    parent = find_folder_by_id(root, folder_id)
    if not parent:
        await callback_query.answer("❌ Parent folder नहीं मिला", show_alert=True)
        return

    existing_rows = [item.get("row", 0) for item in parent.get("items", [])]
    next_row = max(existing_rows, default=-1) + 1

    final_file = {
        "id": file_data["id"],
        "type": "file",
        "sub_type": file_data.get("sub_type", "document"),  # ✅ Add sub_type
        "name": file_data["name"],
        "file_id": file_data["file_id"],
        "caption": file_data["caption"],
        "visibility": file_data["visibility"],
        "row": next_row,
        "column": 0,
        "created_by": int(user_id)
    }

    parent.setdefault("items", []).append(final_file)

    with open(data_file1, "w") as f:
        json.dump(bot_data, f, indent=2)

    del temp_data[user_id]["files"][file_id]
    if not temp_data[user_id]["files"]:
        temp_data.pop(user_id)
    with open(temp_file_json, "w") as f:
        json.dump(temp_data, f, indent=2)

    try:
        with open(status_user_file) as f:
            status_data = json.load(f)
    except:
        status_data = {}
    status_data.pop(user_id, None)
    with open(status_user_file, "w") as f:
        json.dump(status_data, f, indent=2)

    # ✅ Folder open again
    await callback_query.message.edit_caption("Please wait...") 
    kb = generate_folder_keyboard(parent, int(user_id))
    requests.post(DEPLOY_URL)
    await callback_query.message.edit_caption("✅ फ़ाइल सफलतापूर्वक सेव हो गई 📂", reply_markup=kb)
def find_folder_id_of_item(folder, target_id):
    for item in folder.get("items", []):
        if item.get("id") == target_id:
            return folder.get("id")
        elif item.get("type") == "folder":
            found = find_folder_id_of_item(item, target_id)
            if found:
                return found
    return None
def find_item_by_id(folder, target_id):
    for item in folder.get("items", []):
        if item["id"] == target_id:
            return item
        if item.get("type") == "folder":
            found = find_item_by_id(item, target_id)
            if found:
                return found
    return None
@app.on_callback_query(filters.regex(r"^file1:(.+)$"))
async def send_file_from_json(client, callback_query):
    file_uuid = callback_query.data.split(":")[1]
    user_id = callback_query.from_user.id

    # 🔹 Load bot_data
    try:
        with open(data_file1) as f:
            bot_data = json.load(f)
    except:
        await callback_query.answer("❌ Data file not found.", show_alert=True)
        return

    # 🔍 Find file by id
    root = bot_data.get("data", {})
    file_data = find_item_by_id(root, file_uuid)

    if not file_data or file_data.get("type") != "file":
        await callback_query.answer("❌ File not found.", show_alert=True)
        return

    file_id = file_data["file_id"]
    caption = file_data.get("caption", file_data.get("name", ""))
    sub_type = file_data.get("sub_type", "document")
    protect = file_data.get("visibility") == "private"
    created_by = file_data.get("created_by")

    chat_id = callback_query.message.chat.id
    try:
        with open(ADMINS_FILE, "r") as f:
            ADMINS = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        ADMINS = [6150091802] 
    # ✅ Add edit button if user is admin or owner
    buttons = []
    if user_id in ADMINS or user_id == created_by:
        folder_id = find_folder_id_of_item(root, file_uuid)  # 🔍 You must have this utility function
        buttons.append([
            InlineKeyboardButton("✏️ Edit Item", callback_data=f"edit_item_file1:{folder_id}:{file_uuid}")
        ])

    # 📨 Send based on sub_type using correct methods
    try:
        if sub_type == "photo":
            await client.send_photo(
                chat_id=chat_id,
                photo=file_id,
                caption=caption,
                protect_content=protect,
                reply_markup=InlineKeyboardMarkup(buttons) if buttons else None
            )
        elif sub_type == "video":
            await client.send_video(
                chat_id=chat_id,
                video=file_id,
                caption=caption,
                protect_content=protect,
                reply_markup=InlineKeyboardMarkup(buttons) if buttons else None
            )
        elif sub_type == "audio":
            await client.send_audio(
                chat_id=chat_id,
                audio=file_id,
                caption=caption,
                protect_content=protect,
                reply_markup=InlineKeyboardMarkup(buttons) if buttons else None
            )
        else:
            await client.send_document(
                chat_id=chat_id,
                document=file_id,
                caption=caption,
                protect_content=protect,
                reply_markup=InlineKeyboardMarkup(buttons) if buttons else None
            )
    except Exception as e:
        await callback_query.message.reply(f"❌ Error sending file1: {e}")

    await callback_query.answer()
@app.on_callback_query(filters.regex(r"^edit_item_file1:(.+):(.+)$"))
async def edit_item_file_handler(client, callback_query):
    folder_id, file_uuid = callback_query.data.split(":")[1:]
    user_id = callback_query.from_user.id

    # 🔐 Load bot_data
    try:
        with open(data_file1) as f:
            data = json.load(f)
    except:
        await callback_query.answer("❌ Unable to load data.", show_alert=True)
        return

    # 🔍 Find folder and file
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
        await callback_query.answer("❌ Folder not found.", show_alert=True)
        return

    file_data = next((i for i in folder.get("items", []) if i["id"] == file_uuid), None)
    if not file_data:
        await callback_query.answer("❌ File not found.", show_alert=True)
        return
    try:
        with open(ADMINS_FILE, "r") as f:
            ADMINS = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        ADMINS = [6150091802] 
    # 🔐 Permission check
    if user_id not in ADMINS and file_data.get("created_by") != user_id:
        await callback_query.answer("❌ You don't have access.", show_alert=True)
        return

    # 🔁 Get current visibility
    visibility = file_data.get("visibility", "public")

    # 📋 Build editing buttons
    buttons = [
        [InlineKeyboardButton(f"👁 Visibility: {visibility}", callback_data=f"toggle_file_visibility1:{file_uuid}")],
        [InlineKeyboardButton("📝 Edit Caption", callback_data=f"file_caption_editing1:{file_uuid}")]
    ]

    await callback_query.message.edit_text(
        f"🛠 Edit options for file1: {file_data.get('name', 'Unnamed')}",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
@app.on_callback_query(filters.regex(r"^file_caption_editing1:(.+)$"))
async def edit_file_caption_callback(client, callback_query):
    file_uuid = callback_query.data.split(":")[1]
    user_id = str(callback_query.from_user.id)

    # 🔃 Load bot_data
    try:
        with open(data_file1, "r") as f:
            bot_data = json.load(f)
    except:
        await callback_query.answer("❌ Unable to load data.", show_alert=True)
        return

    # 🔍 Find the file
    def find_file(folder):
        for item in folder.get("items", []):
            if item.get("id") == file_uuid and item.get("type") == "file":
                return item
            if item.get("type") == "folder":
                found = find_file(item)
                if found:
                    return found
        return None

    root = bot_data.get("data", {})
    file_data = find_file(root)

    if not file_data:
        await callback_query.answer("❌ File not found.", show_alert=True)
        return
    try:
        with open(ADMINS_FILE, "r") as f:
            ADMINS = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        ADMINS = [6150091802] 
    # 🔐 Permission check
    if int(user_id) not in ADMINS and file_data.get("created_by") != int(user_id):
        await callback_query.answer("❌ You don't have permission.", show_alert=True)
        return

    # ✅ Set user status
    try:
        with open(status_user_file, "r") as f:
            status_data = json.load(f)
    except:
        status_data = {}

    status_data[str(user_id)] = f"youti_item_file_captioning1:{file_uuid}"
    with open(status_user_file, "w") as f:
        json.dump(status_data, f, indent=2)

    # 📩 Ask for new caption
    current_caption = file_data.get("caption", "❌ No caption set")
    await callback_query.message.edit_text(
        f"📝 Current Caption:\n`{current_caption}`\n\nSend the new caption below:",
    )
@app.on_message(filters.private & filters.text & StatusFilter("youti_item_file_captioning1"))
async def edit_caption_receive(client, message):
    user_id = str(message.from_user.id)
    if message.entities:
        formatted = message.text.markdown
    else:
        formatted = escape_markdown(message.text)
    new_caption = formatted
    # 🔄 Get UUID from status
    with open(status_user_file, "r") as f:
        status_data = json.load(f)
    file_uuid = status_data.get(user_id, "").split(":")[1]

    # 🗃 Load bot_data
    with open(data_file1, "r") as f:
        bot_data = json.load(f)

    # 🔍 Find the file
    def find_file(folder):
        for item in folder.get("items", []):
            if item.get("id") == file_uuid and item.get("type") == "file":
                return item
            if item.get("type") == "folder":
                found = find_file(item)
                if found:
                    return found
        return None

    root = bot_data.get("data", {})
    file_data = find_file(root)

    if not file_data:
        await message.reply("❌ File not found.")
        return

    file_data["caption"] = new_caption

    # 💾 Save back
    with open(data_file1, "w") as f:
        json.dump(bot_data, f, indent=2)

    # 🧹 Clear status
    status_data.pop(user_id, None)
    with open(status_user_file, "w") as f:
        json.dump(status_data, f, indent=2)

    # 🔁 Send file again with updated caption and inline buttons
    file_id = file_data["file_id"]
    sub_type = file_data.get("sub_type", "document")
    visibility = file_data.get("visibility", "public")

    buttons = [
        [InlineKeyboardButton("👁 Change Visibility", callback_data=f"toggle_file_visibility1:{file_uuid}")],
        [InlineKeyboardButton("📝 Edit Caption", callback_data=f"edit_file_caption1:{file_uuid}")]
    ]

    try:
        if sub_type == "photo":
            await message.reply_photo(photo=file_id, caption=new_caption, reply_markup=InlineKeyboardMarkup(buttons))
        elif sub_type == "video":
            await message.reply_video(video=file_id, caption=new_caption, reply_markup=InlineKeyboardMarkup(buttons))
        elif sub_type == "audio":
            await message.reply_audio(audio=file_id, caption=new_caption, reply_markup=InlineKeyboardMarkup(buttons))
        else:
            await message.reply_document(document=file_id, caption=new_caption, reply_markup=InlineKeyboardMarkup(buttons))
    except Exception as e:
        await message.reply(f"❌ Failed to send updated file1: {e}")
@app.on_callback_query(filters.regex(r"^toggle_file_visibility1:(.+)$"))
async def toggle_file_visibility(client, callback_query):
    file_uuid = callback_query.data.split(":")[1]
    user_id = str(callback_query.from_user.id)

    # 🔃 Load data
    try:
        with open(data_file1, "r") as f:
            data = json.load(f)
    except:
        await callback_query.answer("❌ Unable to load bot data.", show_alert=True)
        return

    # 🔍 Find file inside any folder
    def find_file(folder):
        for item in folder.get("items", []):
            if item.get("id") == file_uuid and item.get("type") == "file":
                return item, folder
            if item.get("type") == "folder":
                result = find_file(item)
                if result:
                    return result
        return None

    root = data.get("data", {})
    result = find_file(root)
    if not result:
        await callback_query.answer("❌ File not found.", show_alert=True)
        return

    file_data, parent_folder = result
    try:
        with open(ADMINS_FILE, "r") as f:
            ADMINS = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        ADMINS = [6150091802] 
    # 🔐 Check permission
    if int(user_id) not in ADMINS and file_data.get("created_by") != int(user_id):
        await callback_query.answer("❌ You don't have permission.", show_alert=True)
        return

    # 🔄 Toggle visibility
    current = file_data.get("visibility", "public")
    new_visibility = "private" if current == "public" else "public"
    file_data["visibility"] = new_visibility

    # 💾 Save back
    with open(data_file1, "w") as f:
        json.dump(data, f, indent=2)

    # 🔁 Update buttons
    buttons = [
        [InlineKeyboardButton(f"👁 Visibility: {new_visibility}", callback_data=f"toggle_file_visibility1:{file_uuid}")],
        [InlineKeyboardButton("📝 Edit Caption", callback_data=f"file_caption_editing1:{file_uuid}")],
        [InlineKeyboardButton("🔙Back", callback_data=f"open1:{parent_folder['id']}")]
    ]

    await callback_query.message.edit_text(
        f"✅ Visibility updated to **{new_visibility}** for file `{file_data.get('name', '')}`",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
@app.on_callback_query(filters.regex(r"^update_folder_allow1:(.+)$"))
async def update_folder_allow_handler(client, callback_query):
    folder_id = callback_query.data.split(":")[1]
    user_id = str(callback_query.from_user.id)

    # 🔐 Check permissions
    with open(data_file1, "r") as f:
        data = json.load(f)

    def find_folder(folder, fid):
        if folder.get("id") == fid and folder.get("type") == "folder":
            return folder
        for item in folder.get("items", []):
            if item.get("type") == "folder":
                found = find_folder(item, fid)
                if found:
                    return found
        return None

    folder = find_folder(data.get("data", {}), folder_id)

    if not folder:
        await callback_query.answer("❌ Folder not found", show_alert=True)
        return
    try:
        with open(ADMINS_FILE, "r") as f:
            ADMINS = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        ADMINS = [6150091802] 
    if int(user_id) not in ADMINS and folder.get("created_by") != int(user_id):
        await callback_query.answer("❌ You are not allowed", show_alert=True)
        return

    # ✅ Allowed actions
    all_options = ["add_file", "add_folder", "add_url", "add_webapp"]
    current_allow = folder.get("user_allow", [])

    buttons = []
    for opt in all_options:
        mark = "✅" if opt in current_allow else "❌"
        buttons.append([
            InlineKeyboardButton(
                f"{mark} {opt.replace('_', ' ').title()}",
                callback_data=f"toggle_folder_allow1:{folder_id}:{opt}"
            )
        ])

    # Back button
    buttons.append([InlineKeyboardButton("🔙Back", callback_data=f"edit1_item12:{folder_id}")])

    await callback_query.message.edit_text(
        "🔧 Select what users are allowed to add in this folder:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
@app.on_callback_query(filters.regex(r"^toggle_folder_allow1:(.+):(.+)$"))
async def toggle_folder_allow_callback(client, callback_query):
    folder_id, option = callback_query.data.split(":")[1:]
    user_id = str(callback_query.from_user.id)

    with open(data_file1, "r") as f:
        data = json.load(f)

    def find_folder(folder, fid):
        if folder.get("id") == fid and folder.get("type") == "folder":
            return folder
        for item in folder.get("items", []):
            if item.get("type") == "folder":
                found = find_folder(item, fid)
                if found:
                    return found
        return None

    folder = find_folder(data.get("data", {}), folder_id)
    if not folder:
        await callback_query.answer("❌ Folder not found", show_alert=True)
        return
    try:
        with open(ADMINS_FILE, "r") as f:
            ADMINS = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        ADMINS = [6150091802] 
    if int(user_id) not in ADMINS and folder.get("created_by") != int(user_id):
        await callback_query.answer("❌ You are not allowed", show_alert=True)
        return

    user_allow = folder.setdefault("user_allow", [])

    if option in user_allow:
        user_allow.remove(option)
    else:
        user_allow.append(option)

    with open(data_file1, "w") as f:
        json.dump(data, f, indent=2)

    # Refresh menu
    await update_folder_allow_handler(client, callback_query)

@app.on_callback_query(filters.regex(r"^copy_item1:(.+):(.+)$"))
async def copy_item_start(client, callback_query):
    folder_id, item_id = callback_query.data.split(":")[1:]
    user_id = str(callback_query.from_user.id)

    with open(data_file1, "r") as f:
        data = json.load(f)

    folder = find_folder_by_id(data["data"], folder_id)
    if not folder:
        await callback_query.answer("❌ Folder not found", show_alert=True)
        return

    # Save status
    with open(status_user_file, "r") as f:
        status = json.load(f)

    status[user_id] = {
        "status": f"copying_item1:{item_id}",
        "current_folder": folder_id,
        "target_folder": folder_id
    }

    with open(status_user_file, "w") as f:
        json.dump(status, f, indent=2)

    await show_copy_folder_navigation(client, callback_query.message, item_id, folder_id)
async def show_copy_folder_navigation(client, message, item_id, folder_id):
    with open(data_file1, "r") as f:
        data = json.load(f)

    folder = find_folder_by_id(data["data"], folder_id)
    if not folder:
        await message.edit_text("❌ Folder not found.")
        return

    buttons = []

    # subfolders only
    for sub in folder.get("items", []):
        if sub.get("type") == "folder":
            buttons.append([
                InlineKeyboardButton(
                    f"📁 {sub['name']}",
                    callback_data=f"copy_navigate1:{item_id}:{sub['id']}"
                )
            ])

    # bottom control
    controls = [
        InlineKeyboardButton("🔙Back", callback_data=f"copy_back1:{item_id}"),
        InlineKeyboardButton("❌ Cancel", callback_data="copy_cancel1"),
        InlineKeyboardButton("✅ Done", callback_data=f"copy_done1:{folder_id}:{item_id}")
    ]
    buttons.append(controls)

    await message.edit_text(
        f"📂 **Select target folder:**\n\n*Current*: {folder.get('name')}",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
@app.on_callback_query(filters.regex(r"^copy_navigate1:(.+):(.+)$"))
async def copy_navigate1(client, callback_query):
    item_id, folder_id = callback_query.data.split(":")[1:]
    user_id = str(callback_query.from_user.id)

    # update status
    with open(status_user_file, "r") as f:
        status = json.load(f)

    if user_id in status:
        status[user_id]["current_folder"] = folder_id
        status[user_id]["target_folder"] = folder_id

    with open(status_user_file, "w") as f:
        json.dump(status, f, indent=2)

    await show_copy_folder_navigation(client, callback_query.message, item_id, folder_id)
    
@app.on_callback_query(filters.regex(r"^copy_back1:(.+)$"))
async def copy_back1(client, callback_query):
    item_id = callback_query.data.split(":")[1]
    user_id = str(callback_query.from_user.id)

    with open(status_user_file, "r") as f:
        status = json.load(f)

    current_folder = status[user_id].get("current_folder")

    with open(data_file1, "r") as f:
        data = json.load(f)

    parent_folder = find_parent_folder(data["data"], current_folder)
    if not parent_folder:
        await callback_query.answer("🚫 Already at root", show_alert=True)
        return

    status[user_id]["current_folder"] = parent_folder["id"]
    status[user_id]["target_folder"] = parent_folder["id"]

    with open(status_user_file, "w") as f:
        json.dump(status, f, indent=2)

    await show_copy_folder_navigation(client, callback_query.message, item_id, parent_folder["id"])
@app.on_callback_query(filters.regex(r"^copy_cancel1$"))
async def copy_cancel1(client, callback_query):
    user_id = str(callback_query.from_user.id)
    with open(status_user_file, "r") as f:
        status = json.load(f)
    status.pop(user_id, None)
    with open(status_user_file, "w") as f:
        json.dump(status, f, indent=2)

    await callback_query.message.edit_text("❌ Copy cancelled.")
@app.on_callback_query(filters.regex(r"^copy_done1:(.+):(.+)$"))
async def copy_done_handler(client, callback_query):
    dest_folder_id, item_id = callback_query.data.split(":")[1:]
    user_id = str(callback_query.from_user.id)

    # Load
    with open(data_file1, "r") as f:
        data = json.load(f)

    root = data.get("data", {})

    # Find source item
    item_to_copy = find_item_by_id(root, item_id)
    if not item_to_copy:
        await callback_query.answer("❌ Item not found", show_alert=True)
        return

    # Find destination folder
    dest_folder = find_folder_by_id(root, dest_folder_id)
    if not dest_folder:
        await callback_query.answer("❌ Destination folder not found", show_alert=True)
        return

    import uuid

    # Recursive deep copy with new ids and correct parent_id
    def deep_copy(item, new_parent_id):
        new_item = item.copy()
        new_item["id"] = uuid.uuid4().hex[:12]
        new_item["created_by"] = user_id
        new_item["parent_id"] = new_parent_id  # <-- update parent id

        if new_item.get("type") == "folder":
            children = []
            for child in item.get("items", []):
                copied_child = deep_copy(child, new_item["id"])  # assign new id as parent
                children.append(copied_child)
            new_item["items"] = children

        return new_item

    # Copy the outer
    copied = deep_copy(item_to_copy, dest_folder_id)

    # Set row/column only for outer
    existing_rows = [i.get("row", 0) for i in dest_folder.get("items", [])]
    copied["row"] = max(existing_rows, default=-1) + 1
    copied["column"] = 0

    dest_folder.setdefault("items", []).append(copied)

    # Save
    with open(data_file1, "w") as f:
        json.dump(data, f, indent=2)

    await callback_query.answer("✅ Copied successfully")
    await callback_query.message.edit_text("Please Wait...")
    requests.post(DEPLOY_URL)
    markup = generate_folder_keyboard(dest_folder, user_id)
    await callback_query.message.edit_text(
        "✅ Copied successfully!",
        reply_markup=markup
    )
def find_parent_folder(root, child_id):
    stack = [root]
    while stack:
        node = stack.pop()
        for item in node.get("items", []):
            if item.get("id") == child_id:
                return node
            if item.get("type") == "folder":
                stack.append(item)
    return None
