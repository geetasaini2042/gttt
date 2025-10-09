import json, os
from common_data import GROUP_WEL_FILE, status_user_file,is_termux
group_wel_file = GROUP_WEL_FILE
from script import app, save_group_settings_json_to_mongodb
from filters.status_filters import StatusFilter
from pyrogram.enums import ChatMembersFilter
from urllib.parse import urlparse
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup





DEFAULT_GROUP_SETTINGS = {
    "welcome_msg": "Welcome ${first_name} to ${group_name} 🎉",
    "welcome_enabled": True,
    "buttons": [],
    "buttons_enabled": False,
    "left_msg": "Nice knowing you 👋",
    "left_enabled": False,
    "delete_urls_from_grouo": True,
    "always_allowed_urls": {
      "domains": ["edumate.life", "singodiya.tech","mrsingodiya.me"],
      "urls": [],
      "usernames": ["@aks979"]
    }
  }


@app.on_message(filters.command("settings") & filters.group)
async def start_handler(client, message: Message):
    support_button = InlineKeyboardMarkup([
                [InlineKeyboardButton("💬 Support", callback_data="group_settings")]
            ])
    await message.reply_text(
                "To Manage this Group click on the below button👇👇",
                reply_markup=support_button
            )

def is_group_chat(callback_query):
    """सही तरीके से group/supergroup detection करता है (string आधारित)"""
    try:
        if callback_query.message and callback_query.message.chat:
            chat = callback_query.message.chat
            chat_type = str(chat.type).lower()
            #print(f"\n📡 Chat Info: {chat}\nType: {chat_type}\n")

            # group या supergroup दोनों को detect करो
            if "group" in chat_type:
                print("✅ Group detected")
                return True
    except Exception as e:
        print(f"⚠️ is_group_chat error: {e}")
        pass

    return False
def load_group_welcome():
    try:
        with open(GROUP_WEL_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def build_inline_keyboard(buttons_json):
    """Convert JSON buttons to InlineKeyboardMarkup"""
    buttons = []
    for row in buttons_json:
        button_row = []
        for btn in row:
            if "url" in btn:
                button_row.append(InlineKeyboardButton(btn["text"], url=btn["url"]))
            elif "callback_data" in btn:
                button_row.append(InlineKeyboardButton(btn["text"], callback_data=btn["callback_data"]))
        buttons.append(button_row)
    return InlineKeyboardMarkup(buttons) if buttons else None

def get_group_welcome(chat_id, user):
    """Return welcome text and markup"""
    group_wel = load_group_welcome()
    data = group_wel.get(str(chat_id), {"text": "👋 Welcome ${first_name}!", "buttons": []})
    
    text = data.get("text", "")
    text = text.replace("${first_name}", user.first_name or "")
    text = text.replace("${last_name}", user.last_name or "")
    text = text.replace("${full_name}", f"{user.first_name or ''} {user.last_name or ''}".strip())
    
    markup = build_inline_keyboard(data.get("buttons", []))
    return text, markup

# ➕ New member joins


# ❌ Left member → delete system left message

def load_group_welcome():
    try:
        with open(GROUP_WEL_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_group_welcome(data):
    with open(GROUP_WEL_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
@app.on_message(filters.new_chat_members)
async def bot_added_to_group(client, message):
    for user in message.new_chat_members:

        # 🔹 जब बॉट खुद ऐड हो
        if user.is_self:
            chat_id_str = str(message.chat.id)
            group_wel = load_group_welcome()

            # ✅ Default entry अगर group नहीं है
            if chat_id_str not in group_wel:
                group_wel[chat_id_str] = DEFAULT_GROUP_SETTINGS
                #msg = await message.reply("Please Wait...")
                if not is_termux :
                  save_group_settings_json_to_mongodb()
                save_group_welcome(group_wel)
                print(f"💾 Default welcome added for group: {message.chat.title} ({chat_id_str})")

            # 🔹 Common info से धन्यवाद संदेश
            common_info = group_wel.get("common_info", {})
            thanks_msg = common_info.get(
                "thanks_msg",
                "🤖 Thanks ${adder_name} for adding me in group ${group_name}"
            )

            # Placeholder replace
            adder_name = message.from_user.first_name if message.from_user else ""
            thanks_msg = (
                thanks_msg.replace("${adder_name}", adder_name or "")
                          .replace("${group_name}", message.chat.title or "")
            )

            # 🔹 सिर्फ “thanks” मैसेज में support बटन
            support_button = InlineKeyboardMarkup([
                [InlineKeyboardButton("💬 Support", callback_data="group_settings")]
            ])

            await message.reply_text(
                thanks_msg,
                reply_markup=support_button,
                disable_web_page_preview=True
            )

            # 🔹 Check admin privileges
            bot_member = await client.get_chat_member(message.chat.id, user.id)
            if not bot_member.privileges or not bot_member.privileges.can_manage_chat:
                admin_mentions = []
                async for admin in client.get_chat_members(message.chat.id, filter=ChatMembersFilter.ADMINISTRATORS):
                    if not admin.user.is_bot:
                        admin_mentions.append(f"[{admin.user.first_name}](tg://user?id={admin.user.id})")
                admin_text = ", ".join(admin_mentions) if admin_mentions else "Admin"
                await message.reply_text(
                    f"⚠️ Hi {admin_text}, I need admin privileges to work properly. "
                    "Please promote me to admin so I can manage messages and features!"
                )
            return

        # 🔹 जब कोई नया मेंबर जुड़ता है
        chat_id_str = str(message.chat.id)
        group_wel = load_group_welcome()
        group_data = group_wel.get(chat_id_str, {})

        if not group_data.get("welcome_enabled", False):
            continue

        # 🔹 वेलकम मैसेज placeholders के साथ
        welcome_text = group_data.get("welcome_msg", "👋 Welcome ${mention}!")
        welcome_text = (
            welcome_text.replace("${first_name}", user.first_name or "")
                        .replace("${last_name}", user.last_name or "")
                        .replace("${full_name}", f"{user.first_name or ''} {user.last_name or ''}".strip())
                        .replace("${id}", str(user.id))
                        .replace("${username}", f"@{user.username}" if user.username else "")
                        .replace("${mention}", f"[{user.first_name}](tg://user?id={user.id})")
                        .replace("${link}", f"https://t.me/{user.username}" if user.username else "")
                        .replace("${group_name}", message.chat.title or "")
        )

        # 🔹 URL Buttons (multi-row + multi-column सपोर्ट)
        welcome_buttons_data = []
        if group_data.get("buttons_enabled", False):
            url_buttons_raw = group_data.get("url_buttons", [])
            for raw in url_buttons_raw:
                row_buttons = []
                for part in raw.split("|"):
                    if " - " in part:
                        text, url = part.split(" - ", 1)
                        row_buttons.append(InlineKeyboardButton(text.strip(), url=url.strip()))
                if row_buttons:
                    welcome_buttons_data.append(row_buttons)

        welcome_markup = InlineKeyboardMarkup(welcome_buttons_data) if welcome_buttons_data else None

        await message.reply_text(
            welcome_text,
            reply_markup=welcome_markup,
            disable_web_page_preview=True
        )

@app.on_message(filters.left_chat_member)
async def handle_left_member(client, message: Message):
    chat_id_str = str(message.chat.id)
    left_user = message.left_chat_member

    # 🔹 Load group data
    group_wel = load_group_welcome()
    group_data = group_wel.get(chat_id_str, {})

    # 🔹 अगर left_enabled False है या डेटा नहीं है → message delete
    if not group_data.get("left_enabled", False):
        try:
            await message.delete()
        except Exception as e:
            print(f"⚠️ Failed to delete left message: {e}")
        return

    # 🔹 Left message text placeholders के साथ
    left_msg = group_data.get("left_msg", "👋 ${first_name} left the group.")
    left_msg = (
        left_msg.replace("${first_name}", left_user.first_name or "")
                .replace("${last_name}", left_user.last_name or "")
                .replace("${full_name}", f"{left_user.first_name or ''} {left_user.last_name or ''}".strip())
                .replace("${id}", str(left_user.id))
                .replace("${username}", f"@{left_user.username}" if left_user.username else "")
                .replace("${mention}", f"[{left_user.first_name}](tg://user?id={left_user.id})")
                .replace("${link}", f"https://t.me/{left_user.username}" if left_user.username else "")
                .replace("${group_name}", message.chat.title or "")
    )

    # 🔹 पुराना “user left” system message delete करो
    try:
        await message.delete()
    except Exception as e:
        print(f"⚠️ Failed to delete left message: {e}")

    # 🔹 Custom left message भेजो
    await client.send_message(
        chat_id=message.chat.id,
        text=left_msg,
        disable_web_page_preview=True
    )

from pyrogram import filters
from pyrogram.errors import ChatAdminRequired, UserNotParticipant

@app.on_callback_query(filters.regex(r"^group_settings$"))
async def group_settings_handler(client, callback_query):
    user = callback_query.from_user
    chat = callback_query.message.chat
    group_id = chat.id

    # 🔹 Ensure the callback comes from a group or supergroup
    if not is_group_chat:
        await callback_query.answer("❌ This button only works in groups.", show_alert=True)
        return

    # 🔹 Check if the bot is admin (always check this first)
    try:
        bot_member = await client.get_chat_member(group_id, client.me.id)
        if not bot_member.privileges or not bot_member.privileges.can_manage_chat:
            await callback_query.answer("⚠️ Please promote me to admin so I can open the group settings.", show_alert=True)
            return
    except ChatAdminRequired:
        await callback_query.answer("⚠️ I don’t have admin access in this group.", show_alert=True)
        return

    # 🔹 Check if the user is an admin
    try:
        user_member = await client.get_chat_member(group_id, user.id)
        if not user_member.privileges or not user_member.privileges.can_manage_chat:
            await callback_query.answer("❌ Only group admins can access settings.", show_alert=True)
            return
    except UserNotParticipant:
        await callback_query.answer("❌ You are not a member of this group.", show_alert=True)
        return
    except ChatAdminRequired:
        # Shouldn't normally happen, but handled just in case
        await callback_query.answer("⚠️ I don’t have permission to view member details.", show_alert=True)
        return

    # 🔹 All checks passed → open settings link
    g_settings = f"https://t.me/{(await client.get_me()).username}?start=group_settings_{group_id}"
    await callback_query.answer(url=g_settings)
    
import re
import json
import os
from pyrogram import filters
from pyrogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from pyrogram.enums import ChatMembersFilter


# ✅ JSON Functions
def load_group_welcome():
    if not os.path.exists(GROUP_WEL_FILE):
        return {}
    with open(GROUP_WEL_FILE, "r") as f:
        return json.load(f)

def save_group_welcome(data):
    with open(GROUP_WEL_FILE, "w") as f:
        json.dump(data, f, indent=2)

@app.on_message(filters.regex(r"^/start\s+group_settings_(-?\d+)$") & filters.private)
async def group_settings_handler(client, message: Message):
    match = re.match(r"^/start\s+group_settings_(-?\d+)$", message.text)
    if not match:
        return await message.reply_text("❌ Invalid format.")
    group_id = int(match.group(1))
    user = message.from_user

    # 🔹 Check if user is admin
    try:
        member = await client.get_chat_member(group_id, user.id)
        if not member.privileges or not member.privileges.can_manage_chat:
            return await message.reply_text("❌ केवल group admin ही settings बदल सकते हैं।")
    except Exception:
        return await message.reply_text("⚠️ Group तक पहुँच नहीं पाई।")

    # 🔹 Check if bot is admin
    bot_member = await client.get_chat_member(group_id, client.me.id)
    if not bot_member.privileges or not bot_member.privileges.can_manage_chat:
        return await message.reply_text("⚠️ मुझे group admin बनाइए ताकि मैं settings बदल सकूं।")

    # ✅ Load or set defaults
    group_data = load_group_welcome()
    if str(group_id) not in group_data:
        group_data[str(group_id)] = DEFAULT_GROUP_SETTINGS.copy()
        save_group_welcome(group_data)

    g = group_data[str(group_id)]

    # 🧩 Prepare toggle texts
    wel_t = "✅ ON" if g.get("welcome_enabled", True) else "❌ OFF"
    btn_t = "✅ ON" if g.get("buttons_enabled", True) else "❌ OFF"
    left_t = "✅ ON" if g.get("left_enabled", True) else "❌ OFF"

    # 🧩 Create inline keyboard
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📝 Welcome Message", callback_data=f"show_wel_{group_id}"),
            InlineKeyboardButton(wel_t, callback_data=f"toggle_wel_{group_id}")
        ],
        [
            InlineKeyboardButton("🔗 URL Buttons", callback_data=f"show_btn_{group_id}"),
            InlineKeyboardButton(btn_t, callback_data=f"toggle_btn_{group_id}")
        ],
        [
            InlineKeyboardButton("🚪 Left Message", callback_data=f"show_left_{group_id}"),
            InlineKeyboardButton(left_t, callback_data=f"toggle_left_{group_id}")
        ]
    ])

    await message.reply_text(
        f"⚙️ **Group Settings Panel**\n\n"
        f"Group ID: `{group_id}`\n\n"
        f"📝 Welcome Message: {wel_t}\n"
        f"🔗 URL Buttons: {btn_t}\n"
        f"🚪 Left Message: {left_t}",
        reply_markup=keyboard
    )
    
async def group_settings_reload(client, message, group_id):
    group_data = load_group_welcome()
    if str(group_id) not in group_data:
        group_data[str(group_id)] = DEFAULT_GROUP_SETTINGS.copy()
        save_group_welcome(group_data)

    g = group_data[str(group_id)]

    # 🧩 Prepare toggle texts
    wel_t = "✅ ON" if g.get("welcome_enabled", True) else "❌ OFF"
    btn_t = "✅ ON" if g.get("buttons_enabled", True) else "❌ OFF"
    left_t = "✅ ON" if g.get("left_enabled", True) else "❌ OFF"

    # 🧩 Create inline keyboard
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📝 Welcome Message", callback_data=f"show_wel_{group_id}"),
            InlineKeyboardButton(wel_t, callback_data=f"toggle_wel_{group_id}")
        ],
        [
            InlineKeyboardButton("🔗 URL Buttons", callback_data=f"show_btn_{group_id}"),
            InlineKeyboardButton(btn_t, callback_data=f"toggle_btn_{group_id}")
        ],
        [
            InlineKeyboardButton("🚪 Left Message", callback_data=f"show_left_{group_id}"),
            InlineKeyboardButton(left_t, callback_data=f"toggle_left_{group_id}")
        ]
    ])

    await message.edit_text(
        f"⚙️ **Group Settings Panel**\n\n"
        f"Group ID: `{group_id}`\n\n"
        f"📝 Welcome Message: {wel_t}\n"
        f"🔗 URL Buttons: {btn_t}\n"
        f"🚪 Left Message: {left_t}",
        reply_markup=keyboard
    )


@app.on_callback_query(filters.regex(r"^show_(wel|btn|left)_(-?\d+)$"))
async def show_group_content(client, cq):
    match = cq.matches[0]
    key_type = match.group(1)   # wel / btn / left
    group_id = match.group(2)

    group_wel = load_group_welcome()
    group_data = group_wel.get(group_id, {})

    # 🔹 Key map for labels
    key_map = {
        "wel": "Welcome Message",
        "btn": "URL Buttons",
        "left": "Left Message"
    }

    # 🔹 Fetch current value
    if key_type == "wel":
        value = group_data.get("welcome_msg", "❌ No welcome message set.")
    elif key_type == "btn":
        if group_data.get("url_buttons"):
            buttons_list = group_data["url_buttons"]
            value = "\n".join(buttons_list)
        else:
            value = "❌ No buttons set."
    elif key_type == "left":
        value = group_data.get("left_msg", "❌ No left message set.")
    else:
        value = "❌ Invalid key."

    # 🔹 Prepare message text
    text = f"**📋 Current {key_map[key_type]}:**\n\n`{value}`"

    # 🔹 Add update button
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✏️ Update", callback_data=f"update_{key_type}_{group_id}"),
            InlineKeyboardButton("⬅️ Back", callback_data=f"back_to_group_menu_{group_id}")
        ]
    ])

    await cq.message.edit_text(
        text,
        reply_markup=keyboard,
        disable_web_page_preview=True
    )

@app.on_callback_query(filters.regex(r"^back_to_group_menu_(-?\d+)$"))
async def back_to_group_menu(client, cq):
    match = cq.matches[0]
    group_id = match.group(1)
    await group_settings_reload(client, cq.message, group_id)
@app.on_callback_query(filters.regex(r"^toggle_(wel|btn|left)_(-?\d+)$"))
async def toggle_group_settings(client, cq):
    match = cq.matches[0]
    key_type = match.group(1)   # wel / btn / left
    group_id = match.group(2)

    group_wel = load_group_welcome()
    group_data = group_wel.get(group_id, {})

    # 🔹 key mapping
    key_map = {
        "wel": "welcome_enabled",
        "btn": "buttons_enabled",
        "left": "left_enabled"
    }
    label_map = {
        "wel": "Welcome Message",
        "btn": "URL Buttons",
        "left": "Left Message"
    }

    # 🔹 Toggle value
    current = group_data.get(key_map[key_type], False)
    new_value = not current
    group_data[key_map[key_type]] = new_value

    # Save back
    group_wel[group_id] = group_data
    save_group_welcome(group_wel)

    # 🔹 Status text
    status_icon = "✅ Enabled" if new_value else "🚫 Disabled"
    #await cq.answer(f"{label_map[key_type]} {status_icon}", show_alert=True)

    # 🔹 Refresh main settings keyboard
    wel_t = "✅" if group_data.get("welcome_enabled", False) else "❌"
    btn_t = "✅" if group_data.get("buttons_enabled", False) else "❌"
    left_t = "✅" if group_data.get("left_enabled", False) else "❌"

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📝 Welcome Message", callback_data=f"show_wel_{group_id}"),
            InlineKeyboardButton(wel_t, callback_data=f"toggle_wel_{group_id}")
        ],
        [
            InlineKeyboardButton("🔗 URL Buttons", callback_data=f"show_btn_{group_id}"),
            InlineKeyboardButton(btn_t, callback_data=f"toggle_btn_{group_id}")
        ],
        [
            InlineKeyboardButton("🚪 Left Message", callback_data=f"show_left_{group_id}"),
            InlineKeyboardButton(left_t, callback_data=f"toggle_left_{group_id}")
        ]
    ])

    await group_settings_reload(client, cq.message, group_id)
def load_status():
    if not os.path.exists(status_user_file):
        return {}
    with open(status_user_file, "r") as f:
        return json.load(f)


def save_status(data):
    with open(status_user_file, "w") as f:
        json.dump(data, f, indent=2)


def set_user_status(user_id: int, status: str):
    try:
        with open(status_user_file, "r") as f:
            data = json.load(f)
    except:
        data = {}

    data[str(user_id)] = status

    with open(status_user_file, "w") as f:
        json.dump(data, f)

def get_user_status(user_id: int):
    try:
        with open(status_user_file, "r") as f:
            data = json.load(f)
        return data.get(str(user_id))
    except:
        return None
@app.on_callback_query(filters.regex(r"^update_(wel|btn|left)_(-?\d+)$"))
async def update_group_content(client, cq):
    match = cq.matches[0]
    key_type = match.group(1)   # wel / btn / left
    group_id = match.group(2)
    user_id = cq.from_user.id

    # 🔹 Load group data
    group_wel = load_group_welcome()
    group_data = group_wel.get(group_id, {})

    # 🔹 Key mapping for labels
    key_map = {
        "wel": "Welcome Message",
        "btn": "URL Buttons",
        "left": "Left Message"
    }

    # 🔹 Fetch current value
    if key_type == "wel":
        current_value = group_data.get("welcome_msg", "❌ No welcome message set.")
        help_text = (
            "Send a new Welcome Message.\n\n"
            "You can use placeholders:\n"
            "`${first_name}` → User's first name\n"
            "`${last_name}` → User's last name\n"
            "`${full_name}` → User's full name\n"
            "`${username}` → User's username\n"
            "`${mention}` → Mention the user\n"
            "`${id}` → User ID\n"
            "`${link}` → Telegram profile link\n"
            "`${group_name}` → Group name"
        )
    elif key_type == "btn":
        current_value = "\n".join(group_data.get("url_buttons", [])) or "❌ No buttons set."
        help_text = (
            "Send new URL Buttons.\n\n"
            "Format:\n"
            "`Button Text - URL` → one button per line\n"
            "Use `|` to create multiple buttons in same row.\n"
            "Example:\n"
            "Click Here - https://example.com | Google - https://google.com\n"
            "YouTube - https://youtube.com"
        )
    elif key_type == "left":
        current_value = group_data.get("left_msg", "❌ No left message set.")
        help_text = (
            "Send a new Left Message.\n\n"
            "You can use placeholders same as Welcome Message."
        )
    else:
        await cq.answer("Invalid key.", show_alert=True)
        return

    # 🔹 Send current value + instructions
    text = f"**📌 Current {key_map[key_type]}:**\n\n`{current_value}`\n\n**📝 Instruction:**\n{help_text}"

    await cq.message.edit_text(
        text,
        disable_web_page_preview=True
    )

    # 🔹 Set user status for next message input
    set_user_status(user_id, f"new_group_{key_type}:{group_id}")

    # 🔹 Notify user
    await cq.answer(f"Send me the new {key_map[key_type]} now.", show_alert=True)
    
  
def load_status():
    if not os.path.exists(status_user_file):
        return {}
    with open(status_user_file, "r") as f:
        return json.load(f)

def save_status(data):
    with open(status_user_file, "w") as f:
        json.dump(data, f, indent=2)

def load_group_welcome():
    if not os.path.exists(group_wel_file):
        return {}
    with open(group_wel_file, "r") as f:
        return json.load(f)

def save_group_welcome(data):
    with open(group_wel_file, "w") as f:
        json.dump(data, f, indent=2)


@app.on_message(filters.private & filters.text & StatusFilter("new_group_"))
async def handle_new_content(client, message):
    user_id = message.from_user.id
    text = message.text.strip()
    if text == "/cancle":
      clear_user_status(user_id)
      await message.reply("Cancled successfully!")
      return
    if text in ["/start", "restart", "/clear"]:
      clear_user_status(user_id)
      await message.reply("Please /start again")
      return
    # 🔹 Get user status
    status = get_user_status(user_id)  # assume function returns e.g. "new_group_wel:<group_id>"
    if not status:
        return

    parts = status.split(":")
    key_type = parts[0].replace("new_group_", "")  # wel / btn / left
    group_id = parts[1]

    group_wel = load_group_welcome()
    group_data = group_wel.get(group_id, {})

    if key_type in ["wel", "left"]:
        # Save directly
        if key_type == "wel":
            group_data["welcome_msg"] = text
        else:
            group_data["left_msg"] = text

        group_wel[group_id] = group_data
        save_group_welcome(group_wel)

        await message.reply(f"✅ {key_type.capitalize()} message updated successfully!")
    
    elif key_type == "btn":
        # 🔹 Format check
        lines = text.split("\n")
        valid_lines = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Multiple buttons in same row
            row_buttons = line.split("|")
            valid_row = []
            for btn in row_buttons:
                if " - " not in btn:
                    await message.reply(f"❌ Invalid format: `{btn}`\nUse `Button Text - URL`")
                    return
                text_part, url_part = btn.split(" - ", 1)
                text_part, url_part = text_part.strip(), url_part.strip()
                # Simple URL validation
                parsed = urlparse(url_part)
                if parsed.scheme not in ["http", "https"]:
                    await message.reply(f"❌ Invalid URL: `{url_part}`")
                    return
                valid_row.append(f"{text_part} - {url_part}")
            valid_lines.append(" | ".join(valid_row))
        
        # Save validated buttons
        group_data["url_buttons"] = valid_lines
        group_wel[group_id] = group_data
        msg = await message.reply("Please Wait...")
        if not is_termux :
           save_group_settings_json_to_mongodb()
        save_group_welcome(group_wel)
        back_button = InlineKeyboardMarkup([
                [InlineKeyboardButton("🔙 Back", callback_data=f"back_to_group_menu_{group_id}")]
            ])
        await msg.edit_text("✅ URL Buttons updated successfully!", reply_markup=back_button)

    # 🔹 Clear user status
    clear_user_status(user_id)
    
def clear_user_status(user_id: int):
    try:
        with open(status_user_file, "r") as f:
            data = json.load(f)
    except:
        data = {}

    if str(user_id) in data:
        del data[str(user_id)]

        with open(status_user_file, "w") as f:
            json.dump(data, f)

        print(f"🗑️ Cleared status for user {user_id}")
