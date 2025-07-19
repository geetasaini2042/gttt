from common_data import BLOCKED_FILE,ADMINS,OWNER
import json
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from script import app
from pyrogram.filters import create
from pyrogram.types import Message
from pyrogram.types import Message, CallbackQuery
from config import upload_json_to_mongodb, download_from_mongodb
def get_blocked_users():
    try:
        with open(BLOCKED_FILE, "r") as f:
            return json.load(f)
    except:
        return []
def IsBlockedUser():
    async def func(_, __, update):  # update can be Message or CallbackQuery
        blocked = get_blocked_users()

        try:
            if isinstance(update, Message):
                if update.reply_to_message:
                    target_id = update.reply_to_message.from_user.id
                elif update.entities:
                    for entity in update.entities:
                        if entity.type == "text_mention" and entity.user:
                            target_id = entity.user.id
                            break
                    else:
                        target_id = update.from_user.id
                else:
                    target_id = update.from_user.id

            elif isinstance(update, CallbackQuery):
                target_id = update.from_user.id

            else:
                return False

            return target_id in blocked
        except:
            return False

    return create(func)
@app.on_callback_query(filters.regex(r"^req_(\d+)$"))
async def handle_unblock_request(client, callback_query):
    user_id = int(callback_query.data.split("_")[1])
    sender_id = callback_query.from_user.id
    sent_msg = await callback_query.message.edit_text("REQUEST SENT FOR UNBLOCK")
    if sender_id != user_id:
        await callback_query.answer("⛔ Invalid request.", show_alert=True)
        return

    try:
        user = await client.get_users(sender_id)
        name = user.first_name
        mention = f"{name} ({sender_id})"
    except:
        mention = f"User ID: {sender_id}"

    # Send message to all admins
    for admin_id in ADMINS():
        try:
            await client.send_message(
                admin_id,
                f"🔓 Unblock Request:\n👤 {mention} has requested to be unblocked.",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Unblock", callback_data=f"unblock_{sent_msg.id}_{user_id}")]
                ])
            )
        except Exception as e:
            print(f"❌ Couldn't notify admin {admin_id}: {e}")

    await callback_query.answer("📨 Request sent to admins!", show_alert=True)
@app.on_callback_query(filters.regex(r"^unblock_(\d+)_(\d+)$"))
async def handle_unblock_by_admin(client, callback_query):
    admin_id = callback_query.from_user.id
    if admin_id not in ADMINS():
        await callback_query.answer("⛔ Not allowed", show_alert=True)
        return

    user_msg_id = int(callback_query.data.split("_")[1])
    target_id = int(callback_query.data.split("_")[2])

    blocked_users = get_blocked_users()

    if target_id not in blocked_users:
        await callback_query.answer("⚠️ Already unblocked", show_alert=True)
        await callback_query.message.delete()
        return

    # Unblock user
    remove_blocked_user(target_id)

    # Delete the user's message (confirmation message)
    try:
        await client.delete_messages(chat_id=target_id, message_ids=user_msg_id)
    except Exception as e:
        print(f"❌ Couldn't delete message from user {target_id}: {e}")

    # Notify user
    try:
        await client.send_message(
            target_id,
            "✅ You have been unblocked. You can now use the bot."
        )
    except Exception as e:
        print(f"❌ Failed to notify user {target_id}: {e}")
    await callback_query.message.delete()
    await callback_query.answer("✅ User unblocked", show_alert=True)

@app.on_message(filters.private & IsBlockedUser())
async def handle_blocked_user(client, message):
    user_id = message.from_user.id
    buttons = [
        [InlineKeyboardButton("REQUEST FOR UNBLOCK", callback_data=f"req_{user_id}")]
    ]
    keyboard = InlineKeyboardMarkup(buttons)
    await message.reply_text("⛔ Access Denied!\n\nYou are currently blocked from using this service. Please contact the admin if you believe this is a mistake.",reply_markup=keyboard)
    
@app.on_callback_query(IsBlockedUser())
async def handle_blocked_callback(client, callback_query):
    await callback_query.answer("🚫 You are blocked", show_alert=True)

@app.on_callback_query(filters.regex(r"^user_(\d+)$"))
async def user_info_handler(client, callback_query):
    user_id = callback_query.from_user.id
    if user_id not in ADMINS():
        await callback_query.answer("⛔ Not allowed", show_alert=True)
        return

    target_id = int(callback_query.data.split("_")[1])
    blocked_users = get_blocked_users()

    try:
        user = await client.get_users(target_id)
        name = user.first_name or ""
        mention = f"[{name}](tg://user?id={target_id})"
        access = "Blocked 🚫" if target_id in blocked_users else "Non Blocked ✅"
    except:
        mention = f"[Unknown User](tg://user?id={target_id})"
        access = "Blocked 🚫"
        if target_id not in blocked_users:
            save_blocked_user(target_id)

    toggle_text = "Unblock ❌" if target_id in blocked_users else "Block ✅"
    toggle_callback = f"toggleblock_{target_id}"

    text = f"👤 User: {mention}\n🆔 ID: `{target_id}`\n🔐 Access: {access}"
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton(toggle_text, callback_data=toggle_callback)],
        [InlineKeyboardButton("⬅️ Back", callback_data="users_page_0")]
    ])

    await callback_query.message.edit_text(text, reply_markup=buttons, disable_web_page_preview=True)
    await callback_query.answer()

@app.on_callback_query(filters.regex(r"^toggleblock_(\d+)$"))
async def toggle_block_user(client, callback_query):
    admin_id = callback_query.from_user.id
    if admin_id not in ADMINS():
        await callback_query.answer("⛔ Not allowed", show_alert=True)
        return

    target_id = int(callback_query.data.split("_")[1])

    # ⛔ Prevent self-blocking or blocking OWNER
    if target_id == OWNER:
        await callback_query.answer("❌ Cannot block the OWNER", show_alert=True)
        return
    if target_id == admin_id:
        await callback_query.answer("❌ Cannot block yourself", show_alert=True)
        return

    blocked = get_blocked_users()

    if target_id in blocked:
        remove_blocked_user(target_id)
        await callback_query.answer("✅ Unblocked")

        # 🔔 Send message to unblocked user
        try:
            await client.send_message(
                target_id,
                """✅ Access Restored

You have been **Unblocked** and can now use the bot again.

Welcome back!"""
            )
        except Exception as e:
            print(f"❌ Failed to send unblock message to {target_id}: {e}")
    else:
        save_blocked_user(target_id)
        await callback_query.answer("🚫 Blocked")

        # 🔔 Send message to blocked user
        try:
            buttons = [
        [InlineKeyboardButton("REQUEST FOR UNBLOCK", callback_data=f"req_{target_id}")]
    ]
            keyboard = InlineKeyboardMarkup(buttons)
            await client.send_message(
                target_id,
                """🚫 Access Restricted

You have been **blocked** by the admin and can no longer use this bot.

If you believe this is a mistake, please contact support.""",reply_markup=keyboard
            )
        except Exception as e:
            print(f"❌ Failed to send block message to {target_id}: {e}")

    # Refresh the user info screen
    await user_info_handler(client, callback_query)
def get_blocked_users():
    try:
        with open(BLOCKED_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_blocked_user(uid):
    data = get_blocked_users()
    if uid not in data:
        data.append(uid)
        with open(BLOCKED_FILE, "w") as f:
            json.dump(data, f, indent=2)

def remove_blocked_user(uid):
    data = get_blocked_users()
    if uid in data:
        data.remove(uid)
        with open(BLOCKED_FILE, "w") as f:
            json.dump(data, f, indent=2)
            
