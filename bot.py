import json, os, threading, broadcast, blocked
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, WebAppInfo, User
from script import app, run_flask, run_bot,is_user_subscribed_requests, upload_users,save_data_file_to_mongo, save_data_file1_to_mongo
from common_data import data_file,data_file1, users_file, status_user_file, temp_folder_file,temp_url_file,temp_webapp_file,temp_file_json, DEFAULT_JSON,OWNER,ADMINS,REQUIRED_CHANNELS,send_startup_message_once,is_termux
import vip_from_user
from typing import Union
from collections import defaultdict

from filters.status_filters import StatusFilter
from uuid import uuid4

@app.on_message(filters.command("update") & filters.private)
def update_data_on_md(client, message):
    user_id = message.from_user.id
    if user_id not in ADMINS():
        return
    if not is_termux:
       a = message.reply_text("Please Wait.. Saving On MongoDB 2 Files :/n/n1. bot_data.json/n2. commands_data.json")
       save_data_file1_to_mongo()
       a.edit_text("1 File Processed. Starting 2nd...")
       save_data_file_to_mongo()
       a.edit_text("All Files Saved")

async def save_user(client, user_id: int):
    try:
        with open(users_file, "r") as f:
            data = json.load(f)
            if isinstance(data, dict):
                users = data.get("users", [])
            else:
                users = data
    except (FileNotFoundError, json.JSONDecodeError):
        users = []

    # Only act if it's a new user
    if user_id not in users:
        users.append(user_id)
        with open(users_file, "w") as f:
            json.dump(users, f, indent=2)

        try:
            user: User = await client.get_users(user_id)
            name = user.first_name or ""
            username = f"@{user.username}" if user.username else "N/A"
            mention = f"[{name}](tg://user?id={user_id})"

            # Message for Admins (plain)
            upload_users()
            admin_msg = (
                f"🆕 **New User Joined!**\n\n"
                f"👤 Name: {name}\n"
                f"🔗 Username: {username}\n"
                f"🆔 ID: `{user_id}`"
            )

            # Message for OWNER (with mention)
            owner_msg = (
                f"🆕 **New User Joined!**\n\n"
                f"👤 Name: {mention}\n"
                f"🔗 Username: {username}\n"
                f"🆔 ID: `{user_id}`"
            )

            for admin_id in ADMINS():
                if admin_id != OWNER:
                    try:
                        await client.send_message(admin_id, admin_msg)
                    except Exception as e:
                        print(f"❌ Could not notify admin {admin_id}: {e}")

            # Notify OWNER separately with mention
            try:
                await client.send_message(OWNER, owner_msg)
            except Exception as e:
                print(f"❌ Could not notify OWNER: {e}")

        except Exception as e:
            print(f"❌ Could not fetch new user info: {e}")
def escape_markdown(text: str) -> str:
    return text

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
    print(ADMINS())
    if user_id in ADMINS():
        buttons.append([
            InlineKeyboardButton("➕ Add File", callback_data="add_file:root"),
            InlineKeyboardButton("📁 Add Folder", callback_data="add_folder:root")
        ])
        buttons.append([
            InlineKeyboardButton("🧩 Add WebApp", callback_data="add_webapp:root"),
            InlineKeyboardButton("🔗 Add URL", callback_data="add_url:root")
        ])
        buttons.append([
            InlineKeyboardButton("✏️ Edit Folder Layout", callback_data="edit1_item1:root")
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
@app.on_message(filters.command("add_command") & filters.private)
async def add_command_handler(client, message):
    user_id = message.from_user.id
    if user_id not in ADMINS():
        await message.reply_text("❌ Only admins can use this.")
        return
    set_user_status(user_id, "awaiting_command")
    await message.reply_text("✅ Please send the **command name** (example: `/mycommand`)")
    
def get_users():
    try:
        with open(users_file, "r") as f:
            return json.load(f)
    except:
        return []

def remove_user(uid):
    try:
        with open(users_file, "r") as f:
            data = json.load(f)
        if uid in data:
            data.remove(uid)
            with open(users_file, "w") as f:
                json.dump(data, f, indent=2)
    except:
        pass


@app.on_message(filters.command("users") & filters.private)
async def users_command(client, message):
    user_id = message.from_user.id
    if user_id not in ADMINS():
        return

    users = get_users()
    page = 0
    per_page = 10
    start = page * per_page
    end = start + per_page
    buttons = []

    # पहले admin खुद को दिखाएं
    try:
        user = await client.get_users(user_id)
        name = f"{user.first_name} (You)"
        buttons.append([InlineKeyboardButton(name, callback_data=f"user_{user_id}")])
    except:
        pass  # Admin की जानकारी fetch नहीं हो पाई तो skip

    count = 0
    for uid in users:
        if uid == user_id:
            continue  # admin को skip करें क्योंकि already top पर add कर दिया
        if count >= per_page:
            break
        try:
            user = await client.get_users(uid)
            name = user.first_name
            buttons.append([InlineKeyboardButton(name, callback_data=f"user_{uid}")])
            count += 1
        except Exception as e:
            print(f"❌ Removed blocked user {uid}")
            remove_user(uid)

    nav_buttons = []
    if len(users) - int(user_id in users) > per_page:
        nav_buttons.append(InlineKeyboardButton("Next ⏭️", callback_data=f"users_page_1"))
    if nav_buttons:
        buttons.append(nav_buttons)

    if buttons:
        await message.reply_text("👥 Users List (Page 1)", reply_markup=InlineKeyboardMarkup(buttons))
    else:
        await message.reply_text("❌ No active users found.")
@app.on_callback_query(filters.regex(r"^users_page_(\d+)$"))
async def paginate_users(client, callback_query):
    user_id = callback_query.from_user.id
    if user_id not in ADMINS():
        await callback_query.answer("❌ Not allowed", show_alert=True)
        return

    page = int(callback_query.data.split("_")[-1])
    users = get_users()
    per_page = 10
    start = page * per_page
    end = start + per_page
    buttons = []

    if page == 0:
        # Page 1 पर admin को सबसे ऊपर दिखाएं
        try:
            user = await client.get_users(user_id)
            name = f"{user.first_name} (You)"
            buttons.append([InlineKeyboardButton(name, callback_data=f"user_{user_id}")])
        except:
            pass

    count = 0
    for uid in users:
        if page == 0 and uid == user_id:
            continue  # First page में admin को skip करें क्योंकि top में already add किया
        if count < per_page:
            try:
                user = await client.get_users(uid)
                name = user.first_name
                buttons.append([InlineKeyboardButton(name, callback_data=f"user_{uid}")])
                count += 1
            except:
                print(f"❌ Removed blocked user {uid}")
                remove_user(uid)

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("⏮️ Previous", callback_data=f"users_page_{page - 1}"))
    if (page + 1) * per_page < len(users) - int(user_id in users):
        nav_buttons.append(InlineKeyboardButton("Next ⏭️", callback_data=f"users_page_{page + 1}"))
    if nav_buttons:
        buttons.append(nav_buttons)

    if buttons:
        await callback_query.message.edit_text(
            f"👥 Users List (Page {page + 1})",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    else:
        await callback_query.message.edit_text("❌ No active users on this page.")

    await callback_query.answer()
@app.on_message(filters.command("start") & filters.regex(r"^/start$") & filters.private)
async def start_handler(client, message: Message):
    user = message.from_user
    user_id = user.id
    await save_user(client, user_id)
    await send_startup_message_once()
    from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    from common_data import REQUIRED_CHANNELS

    if not is_user_subscribed_requests(user_id):
        buttons = []
        channel_links_text = ""

        for channel in REQUIRED_CHANNELS.split(","):
            channel = channel.strip()
            if not channel:
                continue

            if channel.startswith("@"):
                link = f"https://t.me/{channel[1:]}"
            elif channel.startswith("-100"):
                link = f"https://t.me/c/{channel[4:]}"
            elif channel.startswith("https://t.me/"):
                link = channel
            else:
                link = f"https://t.me/{channel}"

            channel_links_text += f"🔗 {link}\n"
            buttons.append([InlineKeyboardButton("📢 Join Channel", url=link)])

        await message.reply_text(
            "Please Join Below Channels send /start again\n"
            "📢 कृपया नीचे दिए गए सभी चैनल्स को जॉइन करें फिर /start भेजें:\n\n"
            f"{channel_links_text}",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return
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
    try:
        await message.reply_text(welcome_text, reply_markup=markup)
    except:
        await message.reply_text(welcome_text)
@app.on_message(filters.private & filters.command("restart"))
async def handle_restart(client, message):
    user_id = str(message.from_user.id)
    from common_data import REQUIRED_CHANNELS
    if not is_user_subscribed_requests(user_id):
        buttons = []
        channel_links_text = ""

        for channel in REQUIRED_CHANNELS.split(","):
            channel = channel.strip()
            if not channel:
                continue

            if channel.startswith("@"):
                link = f"https://t.me/{channel[1:]}"
            elif channel.startswith("-100"):
                link = f"https://t.me/c/{channel[4:]}"
            elif channel.startswith("https://t.me/"):
                link = channel
            else:
                link = f"https://t.me/{channel}"

            channel_links_text += f"🔗 {link}\n"
            buttons.append([InlineKeyboardButton("📢 Join Channel", url=link)])

        await message.reply_text(
            "Please Join Below Channels send /start again\n"
            "📢 कृपया नीचे दिए गए सभी चैनल्स को जॉइन करें फिर /start भेजें:\n\n"
            f"{channel_links_text}",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return
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
    user = message.from_user
    user_id = user.id
    try:
        await message.reply("🔄 Your session has been reset. You can start fresh now.",reply_markup=get_root_inline_keyboard(user_id))
    except:
        await message.reply("🔄 Your session has been reset. You can /start fresh now.")

import admins
def load_commands_data():
    try:
        with open(data_file1, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        with open(data_file1, "w") as wf:
            json.dump(DEFAULT_JSON, wf, indent=2)
        return DEFAULT_JSON

def build_inline_keyboard(items: list, user_id: int, current_folder: dict) -> InlineKeyboardMarkup:
    layout = defaultdict(dict)

    for item in items:
        row = item.get("row", 0)
        col = item.get("column", 0)
        name = item.get("name", "❓")

        icon = ""
        button = None

        if item["type"] == "folder":
            icon = "📁"
            button = InlineKeyboardButton(
                f"{icon} {name}",
                callback_data=f"open1:{item['id']}"
            )
        elif item["type"] == "file":
            icon = "📄"
            button = InlineKeyboardButton(
                f"{icon} {name}",
                callback_data=f"file1:{item['id']}"
            )
        elif item["type"] == "url":
            icon = "🔗"
            url = item.get("url", "#")
            button = InlineKeyboardButton(
                f"{icon} {name}",
                url=url
            )
        elif item["type"] == "webapp":
            icon = "🌐"
            url = item.get("url", "#")
            button = InlineKeyboardButton(
                f"{icon} {name}",
                web_app=WebAppInfo(url=url)
            )

        if button:
            layout[row][col] = button

    # 📐 convert layout to button rows
    buttons = []
    for row in sorted(layout.keys()):
        cols = layout[row]
        button_row = [cols[col] for col in sorted(cols.keys())]
        buttons.append(button_row)

    # 🔧 Add Controls
    folder_id = current_folder.get("id", "root")
    allow = current_folder.get("user_allow", [])

    if user_id in ADMINS():
        buttons.append([
            InlineKeyboardButton("➕ Add File", callback_data=f"add_file1:{folder_id}"),
            InlineKeyboardButton("📁 Add Folder", callback_data=f"add_folder1:{folder_id}")
        ])
        buttons.append([
            InlineKeyboardButton("🧩 Add WebApp", callback_data=f"add_webapp1:{folder_id}"),
            InlineKeyboardButton("🔗 Add URL", callback_data=f"add_url1:{folder_id}")
        ])
        buttons.append([
            InlineKeyboardButton("✏️ Edit Folder Layout", callback_data=f"edit1_item12:{folder_id}")
        ])
    else:
        user_buttons = []

        if "add_file" in allow:
            user_buttons.append(InlineKeyboardButton("➕ Add File", callback_data=f"add_file:{folder_id}"))
        if "add_folder" in allow:
            user_buttons.append(InlineKeyboardButton("📁 Add Folder", callback_data=f"add_folder:{folder_id}"))
        if "add_webapp" in allow:
            user_buttons.append(InlineKeyboardButton("🧩 Add WebApp", callback_data=f"add_webapp1:{folder_id}"))
        if "add_url" in allow:
            user_buttons.append(InlineKeyboardButton("🔗 Add URL", callback_data=f"add_url1:{folder_id}"))

        for i in range(0, len(user_buttons), 2):
            buttons.append(user_buttons[i:i+2])
  
    return InlineKeyboardMarkup(buttons)
def set_user_status(user_id: int, status: str):
    try:
        with open(status_user_file, "r") as f:
            data = json.load(f)
    except:
        data = {}

    data[str(user_id)] = status

    with open(status_user_file, "w") as f:
        json.dump(data, f)
        

@app.on_message(filters.private & filters.text & StatusFilter("awaiting_command"))
async def receive_command_name(client, message):
    user_id = message.from_user.id

    if user_id not in ADMINS():
        await message.reply_text("❌ Only admins can add commands.")
        return

    cmd = message.text.strip().split()[0]
    if not cmd.startswith("/"):
        await message.reply_text("❌ Commands must start with `/`. Try again.")
        return
    set_user_status(user_id, f"awaiting_c_description:{cmd}")
    await message.reply_text("✅ Now send the **description** for this command.")
@app.on_message(filters.private & filters.text & StatusFilter("awaiting_c_description"))
async def receive_command_description(client, message):
    user_id = message.from_user.id
    with open(status_user_file, "r") as f:
        status_data = json.load(f)
    status = status_data.get(str(user_id), "")
    cmd = status.split(":", 1)[1]
    if message.entities:
        formatted = message.text.markdown
    else:
        formatted = escape_markdown(message.text)
    desc = formatted

    data = load_commands_data()
    items = data["data"].get("items", [])

    # naya folder
    new_folder = {
        "id": f"item_{uuid4().hex[:6]}",
        "command": cmd,
        "name": cmd.strip("/"),
        "description": desc,
        "type": "folder",
        "created_by": user_id,
        "parent_id": "root",
        "user_allow": [],
        "items": []
    }
    items.append(new_folder)
    data["data"]["items"] = items
    save_commands_data(data)

    clear_user_status(user_id)
    await message.reply_text(f"✅ Command *{cmd}* added successfully with description:\n\n`{desc}`")
@app.on_message(filters.regex(r"^/(\w+)") & filters.private)
async def handle_any_command(client, message: Message):
    user = message.from_user
    user_id = user.id
    command = message.text.strip().split()[0].lower()

    data = load_commands_data()
    root = data.get("data", {})  # dict
    found = None
    for folder in root.get("items", []):
        if folder.get("command", "").lower() == command:
            found = folder
            break

    if not found:
        return

    description = found.get("description", "No description.")
    items = found.get("items", [])

    # placeholder replace
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
        description = description.replace(f"${{{key}}}", value)

    markup = build_inline_keyboard(items, user_id, found)
    try:
        await message.reply_text(description, reply_markup=markup)
    except Exception:
        await message.reply_text(description)


def save_commands_data(data):
    with open(data_file1, "w") as f:
        json.dump(data, f, indent=2)

def clear_user_status(user_id):
    try:
        with open(status_user_file, "r") as f:
            statuses = json.load(f)
    except:
        statuses = {}
    statuses.pop(str(user_id), None)
    with open(status_user_file, "w") as f:
        json.dump(statuses, f)



import callback_handler,command
if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()
    run_bot()
