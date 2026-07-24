import json
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
import os
from common_data import users_file, OWNER
from script import app
USERS_FILE = users_file
def get_users():
    try:
        with open(USERS_FILE, "r") as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data.get("users", [])
            return data
    except:
        return []

def save_users(user_list):
    with open(USERS_FILE, "w") as f:
        json.dump(user_list, f, indent=2)

def remove_user_from_json(uid):
    users = get_users()
    if uid in users:
        users.remove(uid)
        save_users(users)
@app.on_message(filters.command("broadcast") & filters.user([OWNER, 5943119285]))
async def broadcast_handler(client: Client, message: Message):
    if not message.reply_to_message:
        await message.reply_text("ℹ️ Reply to a message to broadcast it.")
        return

    users = get_users()
    total = len(users)
    success = 0
    failed = 0

    status_msg = await message.reply_text(f"📣 Broadcast started...\nTotal users: {total}")

    for i, uid in enumerate(users.copy()):  # copy to avoid runtime mutation
        try:
            await message.reply_to_message.copy(chat_id=uid)
            success += 1
        except Exception as e:
            failed += 1
            remove_user_from_json(uid)
            print(f"❌ Failed to send to {uid}: {e}")

        # Update status every 10 users
        if (i + 1) % 10 == 0 or (i + 1) == total:
            await status_msg.edit_text(
                f"📤 Broadcasting...\n"
                f"✅ Sent: {success}\n"
                f"❌ Failed: {failed}\n"
                f"👥 Remaining: {total - (i + 1)}"
            )

        await asyncio.sleep(0.05)  # slight delay to avoid flooding

    await status_msg.edit_text(
        f"✅ Broadcast completed.\n\n"
        f"📬 Delivered: {success}\n"
        f"❌ Failed: {failed}\n"
        f"👤 Total Users: {total}"
    )
