import json
import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
import callback_handler 
import threading
from script import app, run_flask, run_bot
ADMINS = [6150091802, 2525267728]
data_file = "/storage/emulated/0/BotBuilder/PYTHON/bot_data.json"

# Save user to users.json
import json
from typing import Union

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

async def save_user(user_id: int):
    if USE_MONGO:
        collection = db["users"]
        existing = await collection.find_one({"user_id": user_id})
        if not existing:
            await collection.insert_one({"user_id": user_id})
    else:
        path = "/storage/emulated/0/BotBuilder/PYTHON/users.json"
        try:
            with open(path, "r") as f:
                data = json.load(f)
                users = data.get("users", []) if isinstance(data, dict) else data
        except (FileNotFoundError, json.JSONDecodeError):
            users = []

        if user_id not in users:
            users.append(user_id)
            with open(path, "w") as f:
                json.dump(users, f)
# Generate inline keyboard for root folder + admin buttons
from collections import defaultdict
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from collections import defaultdict
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from collections import defaultdict
import json

async def get_root_inline_keyboard(user_id: int):
    try:
        data = await load_bot_data("/storage/emulated/0/BotBuilder/PYTHON/bot_data.json")
        root = data.get("data", {}) or {}
    except Exception as e:
        print("Error loading root:", e)
        root = {}

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
    await save_user(user_id)

    welcome_text = "👋 **Welcome to PDF Hub!**\n\nयहाँ से आप अपनी ज़रूरत की PDF फाइल्स पा सकते हैं। नीचे से फ़ोल्डर या फाइल चुनें:"
    markup = await get_root_inline_keyboard(user_id)

    await message.reply_text(welcome_text, reply_markup=markup)

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    run_bot()
