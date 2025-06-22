import json
import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from script import app, run_flask, run_bot
import callback_handler 
import threading

# Define Admin IDs
ADMINS = [6150091802, 2525267728]
data_file = "/opt/render/project/src/bot_data.json"

# Save user to users.json
import json
from typing import Union

def load_bot_data(data_file: str = "/opt/render/project/src/bot_data.json") -> Union[dict, list, None]:
    try:
        with open(data_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ File not found: {data_file}")
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON in file: {data_file}")
    except Exception as e:
        print(f"⚠ Unexpected error: {e}")
    return None

def save_user(user_id: int):
    try:
        with open("/opt/render/project/src/users.json", "r") as f:
            data = json.load(f)
            if isinstance(data, dict):
                users = data.get("users", [])
            else:
                users = data
    except (FileNotFoundError, json.JSONDecodeError):
        users = []

    if user_id not in users:
        users.append(user_id)

        with open("/opt/render/project/src/users.json", "w") as f:
            json.dump(users, f)

# Generate inline keyboard for root folder + admin buttons
from collections import defaultdict
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from collections import defaultdict
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from collections import defaultdict
import json

def get_root_inline_keyboard(user_id: int):
    try:
        with open("/opt/render/project/src/bot_data.json", "r") as f:
            root = json.load(f)["data"]
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
            icon = "📁"
            button = InlineKeyboardButton(f"{icon} {name}", callback_data=f"open:{item['id']}")
        elif item["type"] == "file":
            icon = "📄"
            button = InlineKeyboardButton(f"{icon} {name}", callback_data=f"file:{item['id']}")
        elif item["type"] == "url":
            icon = "🔗"
            url = item.get("url", "#")
            button = InlineKeyboardButton(f"{icon} {name}", url=url)
        elif item["type"] == "webapp":
            icon = "🧩"
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
@app.on_message(filters.command("start") & filters.private)
async def start_handler(client, message: Message):
    user_id = message.from_user.id
    save_user(user_id)

    welcome_text = "👋 **Welcome to PDF Hub!**\n\nयहाँ से आप अपनी ज़रूरत की PDF फाइल्स पा सकते हैं। नीचे से फ़ोल्डर या फाइल चुनें:"
    markup = get_root_inline_keyboard(user_id)

    await message.reply_text(welcome_text, reply_markup=markup)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    run_bot()
