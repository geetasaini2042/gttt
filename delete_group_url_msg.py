import re, os, json
from urllib.parse import urlparse
from pyrogram.enums import ChatMemberStatus
#from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram import filters
from script import app
from common_data import GROUP_WEL_FILE, status_user_file
group_wel_file = GROUP_WEL_FILE

def load_group_welcome():
    if not os.path.exists(group_wel_file):
        return {}
    with open(group_wel_file, "r") as f:
        return json.load(f)
import re
from urllib.parse import urlparse
from pyrogram.enums import ChatMemberStatus

async def check_and_delete_urls_or_usernames(client, message):
    chat_id = str(message.chat.id)
    group_data = load_group_welcome().get(chat_id, {})

    if not group_data.get("delete_urls_from_grouo", False):
        return

    always_allowed = group_data.get("always_allowed_urls", {})
    allowed_domains = always_allowed.get("domains", [])
    allowed_urls = always_allowed.get("urls", [])
    allowed_usernames = [u.lower() for u in always_allowed.get("usernames", [])]

    if not message.text:
        return

    # ✅ Admin Skip
    try:
        member = await client.get_chat_member(message.chat.id, message.from_user.id)
        if member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER]:
            return
    except Exception as e:
        print(f"⚠️ Could not check member role: {e}")

    text = message.text

    # 🔹 Find URLs
    urls = re.findall(r'(https?://[^\s]+)', text)
    # 🔹 Find @usernames
    mentions = re.findall(r'@([A-Za-z0-9_]{5,32})', text)

    # -----------------------
    # ✅ URL Check
    # -----------------------
    if urls:
        for url in urls:
            try:
                parsed = urlparse(url)
                domain = parsed.hostname or ""

                # ✅ Exact URL allowed
                if url in allowed_urls:
                    continue

                # ✅ Domain/subdomain allowed
                allowed = False
                for d in allowed_domains:
                    if domain == d or domain.endswith("." + d):
                        allowed = True
                        break

                # 🚫 If any URL not allowed → delete
                if not allowed:
                    await message.delete()
                    print(f"🚫 Deleted message (bad URL): {url}")
                    return

            except Exception as e:
                print(f"❌ URL Parse Error: {e}")
                return

    # -----------------------
    # 🚫 Username mention check
    # -----------------------
    if mentions:
        for uname in mentions:
            if uname.lower() in allowed_usernames:
                continue  # ✅ allowed username skip
            else:
                await message.delete()
                print(f"🚫 Deleted message (unauthorized username): @{uname}")
                return


# 🆕 Normal messages
@app.on_message(filters.group)
async def handle_new_message(client, message):
    await check_and_delete_urls_or_usernames(client, message)

# ✏️ Edited messages
@app.on_edited_message(filters.group)
async def handle_edited_message(client, message):
    await check_and_delete_urls_or_usernames(client, message)