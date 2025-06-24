import json
import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from script import app, run_flask, run_bot
import threading
from common_data import data_file, users_file, status_user_file, temp_folder_file,temp_url_file,temp_webapp_file,temp_file_json, DEFAULT_JSON
# Define Admin IDs
ADMINS = [6150091802, 2525267728]
import json
from typing import Union
# Generate inline keyboard for root folder + admin buttons
from collections import defaultdict
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from collections import defaultdict
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from collections import defaultdict
import json

def save_user(user_id: int):
    try:
        with open(users_file, "r") as f:
            data = json.load(f)
            if isinstance(data, dict):
                users = data.get("users", [])
            else:
                users = data
    except (FileNotFoundError, json.JSONDecodeError):
        users = []

    if user_id not in users:
        users.append(user_id)

        with open(users_file, "w") as f:
            json.dump(users, f)


def get_root_inline_keyboard(user_id: int):
    try:
        with open(data_file, "r") as f:
            content = f.read().strip()
            if content == "{}":
                with open(data_file, "w") as wf:
                    json.dump(DEFAULT_JSON, wf, indent=2)
                root = DEFAULT_JSON["data"]
            else:
                root = json.loads(content)["data"]
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        return InlineKeyboardMarkup([[InlineKeyboardButton("❌ No Data", callback_data="no_data")]])

    layout = defaultdict(dict)

    for item in root.get("items", []):
        row = item.get("row", 0)
        col = item.get("column", 0)
        name = item.get("name", "❓")

        icon = ""
        button = None

        if item["type"] == "folder":
            icon = ""
            button = InlineKeyboardButton(f"{icon} {name}", callback_data=f"open:{item['id']}")
        elif item["type"] == "file":
            icon = ""
            button = InlineKeyboardButton(f"{icon} {name}", callback_data=f"file:{item['id']}")
        elif item["type"] == "url":
            icon = ""
            url = item.get("url", "#")
            button = InlineKeyboardButton(f"{icon} {name}", url=url)
        elif item["type"] == "webapp":
            icon = ""
            url = item.get("url", "#")
            button = InlineKeyboardButton(f"{icon} {name}", web_app=WebAppInfo(url=url))

        if button:
            layout[row][col] = button

    # 📐 Convert layout to button rows
    buttons = []
    for row in sorted(layout.keys()):
        cols = layout[row]
        button_row = [cols[col] for col in sorted(cols.keys())]
        buttons.append(button_row)

    # 🔧 Add Controls
    if user_id in ADMINS:
        buttons.append([
            InlineKeyboardButton("➕ Add File", callback_data="add_file:root"),
            InlineKeyboardButton("📁 Add Folder", callback_data="add_folder:root")
        ])
        buttons.append([
            InlineKeyboardButton("🧩 Add WebApp", callback_data="add_webapp:root"),
            InlineKeyboardButton("🔗 Add URL", callback_data="add_url:root")
        ])
        buttons.append([
            InlineKeyboardButton("✏️ Edit Folder Layout", callback_data="edit_menu:root")
        ])
    else:
        allow = root.get("user_allow", [])
        user_buttons = []

        if "add_file" in allow:
            user_buttons.append(InlineKeyboardButton("➕ Add File", callback_data="add_file:root"))
        if "add_folder" in allow:
            user_buttons.append(InlineKeyboardButton("📁 Add Folder", callback_data="add_folder:root"))
        if "add_webapp" in allow:
            user_buttons.append(InlineKeyboardButton("🧩 Add WebApp", callback_data="add_webapp:root"))
        if "add_url" in allow:
            user_buttons.append(InlineKeyboardButton("🔗 Add URL", callback_data="add_url:root"))

        for i in range(0, len(user_buttons), 2):
            buttons.append(user_buttons[i:i+2])

    return InlineKeyboardMarkup(buttons)

@app.on_message(filters.command("start") & filters.regex(r"^/start$") & filters.private)
async def start_handler(client, message: Message):
    user = message.from_user
    user_id = user.id
    save_user(user_id)

    try :
       with open(data_file, "r") as f:
           bot_data = json.load(f)
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        bot_data = DEFAULT_JSON
    root = bot_data.get("data", {})
    template = root.get("description", "👋 Welcome to **SingodiyaTech**!")

    # 🔄 Replace placeholders with actual values
    user_data = {
        "first_name": user.first_name or "",
        "last_name": user.last_name or "",
        "full_name": f"{user.first_name or ''} {user.last_name or ''}".strip(),
        "id": str(user.id),
        "username": user.username or "",
        "mention": f"[{user.first_name}](tg://user?id={user.id})",
        "link": f"tg://user?id={user.id}"
    }

    for key, value in user_data.items():
        template = template.replace(f"${{{key}}}", value)

    welcome_text = template
    markup = get_root_inline_keyboard(user_id)

    await message.reply_text(welcome_text, reply_markup=markup)
@app.on_message(filters.private & filters.command("restart"))
async def handle_restart(client, message):
    user_id = str(message.from_user.id)

    files_to_clean = [
        status_user_file,
        temp_file_json,
        temp_url_file,
        temp_webapp_file,
        temp_folder_file
    ]

    for file_path in files_to_clean:
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
        except:
            continue  # file not found or corrupted

        if user_id in data:
            data.pop(user_id, None)
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)

    await message.reply("🔄 Your session has been reset. You can start fresh now.",reply_markup=get_root_inline_keyboard(user_id))
import callback_handler 
if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    run_bot()