import os,json
from common_data import ADMINS_FILE,OWNER,status_user_file
from script import app,upload_json_to_mongodb
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from filters.status_filters import StatusFilter
import re
def set_user_status(user_id: int, status: str):
    try:
        with open(status_user_file, "r") as f:
            data = json.load(f)
    except:
        data = {}

    data[str(user_id)] = status

    with open(status_user_file, "w") as f:
        json.dump(data, f)
        

@app.on_message(filters.command("admin") & filters.private)
async def admin_handler(client, message):
    user_id = message.from_user.id
    if user_id != OWNER:
        await message.reply_text("❌ Only owner can use this command.")
        return

    buttons = [
        [InlineKeyboardButton("👥 Show Admins", callback_data="own_admins")]
    ]
    markup = InlineKeyboardMarkup(buttons)

    await message.reply_text(
        "⚙️ **Admin Control Panel**",
        reply_markup=markup
    )


@app.on_callback_query(filters.regex("^own_admins"))
async def show_admins_callback(client, callback_query):
    user_id = callback_query.from_user.id
    if user_id != OWNER:
        await callback_query.answer("❌ Only owner can do this.", show_alert=True)
        return

    try:
        with open(ADMINS_FILE, "r") as f:
            admins = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        admins = []

    # har admin id se user ka naam lana
    buttons = []
    for admin_id in admins:
        try:
            user = await client.get_users(admin_id)
            first_name = user.first_name
        except:
            first_name = "Unknown"
        buttons.append([
            InlineKeyboardButton(
    text=f"{first_name} => {admin_id}",
    callback_data=f"show_admin_options:{admin_id}"
)
        ])

    # ➕ Add Admin button
    buttons.append([
        InlineKeyboardButton("➕ Add Admin", callback_data="add_admin")
    ])

    markup = InlineKeyboardMarkup(buttons)

    await callback_query.message.edit_text(
        "👥 **Admins List:**",
        reply_markup=markup
    )
    
@app.on_callback_query(filters.regex("^add_admin$"))
async def add_admin_options(client, callback_query):
    user_id = callback_query.from_user.id
    if user_id != OWNER:
        await callback_query.answer("❌ Only owner can do this.", show_alert=True)
        return

    buttons = [
        [
            InlineKeyboardButton("📩 Forward Message", callback_data="add_admin_forward"),
            InlineKeyboardButton("🆔 Send ID", callback_data="add_admin_id")
        ]
    ]
    markup = InlineKeyboardMarkup(buttons)

    await callback_query.message.edit_text(
        "🛠️ *Add New Admin*\n\nChoose how you want to add:",
        reply_markup=markup
    )
    
@app.on_callback_query(filters.regex("^add_admin_forward$"))
async def add_admin_forward_callback(client, callback_query):
    user_id = callback_query.from_user.id
    if user_id != OWNER:
        await callback_query.answer("❌ Only owner can do this.", show_alert=True)
        return

    # status set
    set_user_status(user_id, "awaiting_admin_forward")

    await callback_query.message.edit_text(
        "📩 Please **forward** a message from the user you want to add as admin."
    )
    
@app.on_message(filters.private & filters.forwarded & StatusFilter("awaiting_admin_forward"))
async def receive_forwarded_admin(client, message):
    user_id = message.from_user.id
    if user_id != OWNER:
        await message.reply_text("❌ Only owner can do this.")
        return

    # forwarded user id
    if not message.forward_from:
        await message.reply_text("❌ Could not detect forwarded user. Try again.")
        return

    new_admin_id = message.forward_from.id

    # load admins
    try:
        with open(ADMINS_FILE, "r") as f:
            admins = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        admins = []

    if new_admin_id in admins:
        await message.reply_text("✅ This user is already an admin.")
        clear_user_status(user_id)
        return

    admins.append(new_admin_id)
    with open(ADMINS_FILE, "w") as f:
        json.dump(admins, f, indent=2)

    clear_user_status(user_id)
    msg = await message.reply_text(f"Please Wait...")
    upload_json_to_mongodb()
    await msg.edit_text(f"✅ Added new admin: `{new_admin_id}`")
@app.on_callback_query(filters.regex("^add_admin_id$"))
async def add_admin_id_callback(client, callback_query):
    user_id = callback_query.from_user.id
    if user_id != OWNER:
        await callback_query.answer("❌ Only owner can do this.", show_alert=True)
        return

    # status set
    set_user_status(user_id, "awaiting_admin_id")

    await callback_query.message.edit_text(
        "🆔 Please *send the Telegram user ID* of the user you want to add as admin."
    )
@app.on_message(filters.private & filters.text & StatusFilter("awaiting_admin_id"))
async def receive_admin_id(client, message):
    user_id = message.from_user.id
    if user_id != OWNER:
        await message.reply_text("❌ Only owner can do this.")
        return

    try:
        new_admin_id = int(message.text.strip())
    except ValueError:
        await message.reply_text("❌ Invalid ID. Please send a numeric Telegram ID.")
        return

    # load existing admins
    try:
        with open(ADMINS_FILE, "r") as f:
            admins = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        admins = []

    if new_admin_id in admins:
        await message.reply_text("✅ This user is already an admin.")
        clear_user_status(user_id)
        return

    admins.append(new_admin_id)
    with open(ADMINS_FILE, "w") as f:
        json.dump(admins, f, indent=2)

    clear_user_status(user_id)
    msg = await message.reply_text(f"Please Wait...")
    upload_json_to_mongodb()
    await msg.edit_text(f"✅ Added new admin: `{new_admin_id}`")
@app.on_callback_query(filters.regex(r"^show_admin_options:(\d+)$"))
async def show_admin_options(client, callback_query):
    user_id = callback_query.from_user.id
    if user_id != OWNER:
        await callback_query.answer("❌ Only owner can do this.", show_alert=True)
        return

    admin_id = int(callback_query.data.split(":")[1])

    buttons = [
        [InlineKeyboardButton("🗑 Delete Admin", callback_data=f"delete_admin:{admin_id}")],
        [InlineKeyboardButton("🔙 Back", callback_data="own_admins")]
    ]

    await callback_query.message.edit_text(
        f"⚙️ Manage admin: `{admin_id}`",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=None
    )
    
@app.on_callback_query(filters.regex(r"^delete_admin:(\d+)$"))
async def delete_admin_confirm(client, callback_query):
    user_id = callback_query.from_user.id
    if user_id != OWNER:
        await callback_query.answer("❌ Only owner can do this.", show_alert=True)
        return

    admin_id = int(callback_query.data.split(":")[1])

    set_user_status(user_id, f"12awaiting_delete_confirm:{admin_id}")

    await callback_query.message.edit_text(
        f"⚠️ Please **send the ID** `{admin_id}` again to confirm removal."
    )
@app.on_message(filters.private & filters.text & StatusFilter("12awaiting_delete_confirm"))
async def confirm_delete_admin(client, message):
    user_id = message.from_user.id
    if user_id != OWNER:
        await message.reply_text("❌ Only owner can do this.")
        return

    # get expected id
    with open(status_user_file, "r") as f:
        status_data = json.load(f)
    status = status_data.get(str(user_id), "")
    match = re.match(r"12awaiting_delete_confirm:(\d+)", status)
    if not match:
        await message.reply_text("⚠️ Unexpected error. Try again.")
        return

    expected_admin_id = int(match.group(1))

    try:
        typed_id = int(message.text.strip())
    except ValueError:
        await message.reply_text("❌ Invalid ID. Please send a numeric ID.")
        return

    if typed_id != expected_admin_id:
        await message.reply_text("❌ ID mismatch. Deletion canceled.")
        clear_user_status(user_id)
        return

    # proceed with deletion
    try:
        with open(ADMINS_FILE, "r") as f:
            admins = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        admins = []

    if expected_admin_id not in admins:
        await message.reply_text("❌ This ID is not in the admins list.")
        clear_user_status(user_id)
        return

    admins.remove(expected_admin_id)
    with open(ADMINS_FILE, "w") as f:
        json.dump(admins, f, indent=2)

    clear_user_status(user_id)

    await message.reply_text(f"✅ Admin `{expected_admin_id}` removed successfully.", parse_mode=None)
    
def clear_user_status(user_id: int):
    try:
        with open(status_user_file, "r") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}

    data.pop(str(user_id), None)

    with open(status_user_file, "w") as f:
        json.dump(data, f, indent=2)