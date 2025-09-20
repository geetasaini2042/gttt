import os
import json
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from script import app
from filters.status_filters import StatusFilter
from common_data import MD_URI, pre_file, DELETED_PDF_FILE, BASE_PATH, pre_file, ADMINS_FILE, LIKED_FILE, DISLIKED_FILE, PDF_VIEWS_FILE, data_file  , status_user_file, WITHDRAW_FILE

def load_json(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

from pyrogram import Client, filters
from pyrogram.types import Message
import os
@app.on_message(filters.private & filters.command("add_pdf"))
async def add_pdf_handler(client: Client, message: Message):
    await message.reply_text("""Please Send Your File with following details:
1. COURSE 
2. YEAR/SEMESTER
3. SUBJECT 
4. CONTENT (BOOK , SHORT NOTES, IMPORTANT QUESTIONS, PREVIOUS YEAR PAPERS, OTHER)
5. Description (Message for students)

**PLEASE READ OUR TERMS AND CONDITIONS BEFORE ADDING A FILE**
Use Command /pdf_term_and_conditions""")

TERMS_TEXT = """
📄 **Terms and Conditions for Adding PDFs**

1. Ensure the content you upload is your own or you have the right to share it.
2. Do not upload copyrighted material without permission.
3. Avoid offensive or inappropriate content.
4. Provide accurate details (Course, Year/Semester, Subject, Content type, Description).
5. Admins have the right to remove any PDF violating rules without notice.
6. By uploading, you agree to allow your file to be shared with other students.

**Please read carefully before adding any files.**
"""

@app.on_message(filters.private & filters.command(["pdf_term_and_conditions", "term_and_conditions"]))
async def terms_handler(client, message):
    await message.reply_text(TERMS_TEXT)
# ---------- Recursive search for file ----------
def find_file_by_id(node, file_uuid):
    if isinstance(node, dict):
        if node.get("id") == file_uuid and node.get("type") == "file":
            return node
        if "items" in node:
            for item in node["items"]:
                found = find_file_by_id(item, file_uuid)
                if found:
                    return found
    elif isinstance(node, list):
        for item in node:
            found = find_file_by_id(item, file_uuid)
            if found:
                return found
    return None

# ---------- Command handler ----------
@app.on_message(filters.private & filters.command("my_pdf"))
async def my_pdf_handler(client, message):
    user_id = str(message.from_user.id)

    # uuid निकालो
    if len(message.command) < 2:
        await message.reply_text("Please Send `/my_pdf {uuid}`")
        return

    file_uuid = message.command[1].strip()

    # ---------- Deleted files check ----------
    try:
        with open(DELETED_PDF_FILE, "r") as f:
            deleted_data = json.load(f)
    except FileNotFoundError:
        deleted_data = {}

    # search deleted log
    for uid, files in deleted_data.items():
        for f in files:
            if f.get("uuid") == file_uuid:
                await message.reply_text(
                    f"🗑 यह file delete की जा चुकी है।\n\n"
                    f"🆔 UUID: {file_uuid}\n"
                    f"👤 Premium Owner: {f.get('premium_owner')}\n"
                    f"📎 File ID: {f.get('file_id')}"
                )
                return
    pre_files_data = load_json(pre_file)
    admins = load_json(ADMINS_FILE)
    liked_data = load_json(LIKED_FILE)
    disliked_data = load_json(DISLIKED_FILE)
    views_data = load_json(PDF_VIEWS_FILE)
    bot_data = load_json(data_file  )

    # admin list normalize
    if isinstance(admins, list):
        admin_ids = [str(a) for a in admins]
    else:
        admin_ids = []

    # ownership check
    allowed = False
    if user_id in pre_files_data and file_uuid in pre_files_data[user_id]:
        allowed = True
    elif user_id in admin_ids:
        allowed = True

    if not allowed:
        return

    # performance निकालो
    likes = len(liked_data.get(file_uuid, []))
    dislikes = len(disliked_data.get(file_uuid, []))
    views = len(views_data.get(file_uuid, []))

    # file details निकालो
    file_node = find_file_by_id(bot_data.get("data", {}), file_uuid)
    if not file_node:
        await message.reply_text("⚠️ File details नहीं मिली।")
        return

    file_name = file_node.get("name", "Unknown.pdf")
    file_type = file_node.get("sub_type", file_node.get("type", "unknown"))
    caption = file_node.get("caption", "N/A")
    visibility = file_node.get("visibility", "private")
    earning_on = "✅ True" if visibility == "vip" else "❌ False"

    # report text
    text = (
        f"📊 **Performance Report**\n\n"
        f"🆔 UUID: `{file_uuid}`\n"
        f"📄 File name: {file_name}\n"
        f"📂 File type: {file_type}\n"
        f"📝 Caption: {caption}\n"
        f"💰 Earning On: {earning_on}\n\n"
        f"👍 Likes: {likes}\n"
        f"👎 Dislikes: {dislikes}\n"
        f"👁 Views: {views}"
    )

    # buttons
    buttons = [
      [InlineKeyboardButton("FILE DESTINATION", callback_data=f"file_destination67:{file_uuid}")],
        [
            InlineKeyboardButton("💰 See earning", callback_data=f"see_earning:{file_uuid}"),
            InlineKeyboardButton("✏️ Edit file details", callback_data=f"edit67_file:{file_uuid}")
        ]
    ]

    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))

from pyrogram import filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

# ---------- Callback handler for pdf_anl_{uuid} ----------
@app.on_callback_query(filters.regex(r"^pdf_anl:(.+)$"))
async def pdf_anl_handler(client, callback_query: CallbackQuery):
    file_uuid = callback_query.data.split(":")[1]  # extract uuid
    user_id = str(callback_query.from_user.id)

    # ---------- Deleted files check ----------
    try:
        with open(DELETED_PDF_FILE, "r") as f:
            deleted_data = json.load(f)
    except FileNotFoundError:
        deleted_data = {}

    for uid, files in deleted_data.items():
        for f in files:
            if f.get("uuid") == file_uuid:
                await callback_query.answer()
                await callback_query.message.reply_text(
                    f"🗑 यह file delete की जा चुकी है।\n\n"
                    f"🆔 UUID: {file_uuid}\n"
                    f"👤 Premium Owner: {f.get('premium_owner')}\n"
                    f"📎 File ID: {f.get('file_id')}"
                )
                return
    pre_files_data = load_json(pre_file)
    admins = load_json(ADMINS_FILE)
    liked_data = load_json(LIKED_FILE)
    disliked_data = load_json(DISLIKED_FILE)
    views_data = load_json(PDF_VIEWS_FILE)
    bot_data = load_json(data_file  )

    # admin list normalize
    if isinstance(admins, list):
        admin_ids = [str(a) for a in admins]
    else:
        admin_ids = []

    # ownership check
    allowed = False
    if user_id in pre_files_data and file_uuid in pre_files_data[user_id]:
        allowed = True
    elif user_id in admin_ids:
        allowed = True

    if not allowed:
        await callback_query.answer("⚠️ आपको इस PDF का performance देखने की अनुमति नहीं है।", show_alert=True)
        return

    # performance
    likes = len(liked_data.get(file_uuid, []))
    dislikes = len(disliked_data.get(file_uuid, []))
    views = len(views_data.get(file_uuid, []))

    # file details
    file_node = find_file_by_id(bot_data.get("data", {}), file_uuid)
    if not file_node:
        await callback_query.answer("⚠️ File details नहीं मिली।", show_alert=True)
        return

    file_name = file_node.get("name", "Unknown.pdf")
    file_type = file_node.get("sub_type", file_node.get("type", "unknown"))
    caption = file_node.get("caption", "N/A")
    visibility = file_node.get("visibility", "private")
    earning_on = "✅ True" if visibility == "vip" else "❌ False"

    # report text
    text = (
        f"📊 **PDF Analysis**\n\n"
        f"🆔 UUID: `{file_uuid}`\n"
        f"📄 File name: {file_name}\n"
        f"📂 File type: {file_type}\n"
        f"📝 Caption: {caption}\n"
        f"💰 Earning On: {earning_on} \n\n"
        f"👍 Likes: {likes}\n"
        f"👎 Dislikes: {dislikes}\n"
        f"👁 Views: {views}"
    )

    # buttons
    buttons = [
       [InlineKeyboardButton("FILE DESTINATION", callback_data=f"file_destination67:{file_uuid}")],
        [
            InlineKeyboardButton("💰 See earning", callback_data=f"see_earning:{file_uuid}"),
            InlineKeyboardButton("✏️ Edit file details", callback_data=f"edit67_file:{file_uuid}")
        ]
    ]

    await callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons)
    )    
from pyrogram import filters
from pyrogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

# ---------- Callback handler for edit file ----------
@app.on_callback_query(filters.regex(r"^edit67_file:(.+)$"))
async def edit_file_handler(client, callback_query: CallbackQuery):
    file_uuid = callback_query.data.split(":")[1]  # extract uuid
    #file_uuid = callback_query.data.split(":")[1]
    user_id = str(callback_query.from_user.id)

    # JSON load
    bot_data = load_json(data_file  )
    file_node = find_file_by_id(bot_data.get("data", {}), file_uuid)

    if not file_node:
        await callback_query.answer("⚠️ File details नहीं मिली।", show_alert=True)
        return

    # file details निकालो
    file_name = file_node.get("name", "Unknown.pdf")
    caption = file_node.get("caption", "N/A")
    visibility = file_node.get("visibility", "private")

    # Text message
    text = (
        f"✏️ **Edit File Details**\n\n"
        f"🆔 UUID: `{file_uuid}`\n"
        f"📄 File name: {file_name}\n"
        f"📝 Caption: {caption}\n"
        f"👁 Visibility: {visibility}\n\n"
        f"कृपया नीचे से कोई option चुनें 👇"
    )

    # Unique buttons
    buttons = [
        [InlineKeyboardButton("✏️ Rename", callback_data=f"edit_rename67:{file_uuid}")],
        [InlineKeyboardButton("📝 Edit Caption", callback_data=f"edit_caption67:{file_uuid}")],
        [InlineKeyboardButton(f"👁 Toggle Visibility ({visibility})", callback_data=f"edit_visibility67:{file_uuid}")],
        [InlineKeyboardButton("DELETE FILE", callback_data=f"delete67_file:{file_uuid}")],
        [InlineKeyboardButton("⬅️ Back", callback_data=f"pdf_anl:{file_uuid}")]
    ]

    await callback_query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons)
    )


def load_status():
    try:
        with open(status_user_file, "r") as f:
            return json.load(f)
    except:
        return {}

def save_status(data):
    with open(status_user_file, "w") as f:
        json.dump(data, f, indent=2)

@app.on_callback_query(filters.regex(r"^edit_rename67:(.+)$"))
async def edit_rename_callback(client, callback_query: CallbackQuery):
    file_uuid = callback_query.data.split(":")[1]
    user_id = str(callback_query.from_user.id)

    # load bot_data
    bot_data = load_json(data_file  )
    file_node = find_file_by_id(bot_data.get("data", {}), file_uuid)
    if not file_node:
        await callback_query.answer("⚠️ File details नहीं मिली।", show_alert=True)
        return

    current_name = file_node.get("name", "Unknown.pdf")

    # set user status
    status = load_status()
    status[user_id] = f"rename67_file:{file_uuid}"
    save_status(status)

    await callback_query.answer()
    await callback_query.message.edit_text(
        f"✏️ Rename File\nCurrent Name: {current_name}\n\nनया नाम भेजें:"
    )


@app.on_callback_query(filters.regex(r"^edit_caption67:(.+)$"))
async def edit_caption_callback(client, callback_query: CallbackQuery):
    file_uuid = callback_query.data.split(":")[1]
    user_id = str(callback_query.from_user.id)

    # load bot_data
    bot_data = load_json(data_file  )
    file_node = find_file_by_id(bot_data.get("data", {}), file_uuid)
    if not file_node:
        await callback_query.answer("⚠️ File details नहीं मिली।", show_alert=True)
        return

    current_caption = file_node.get("caption", "N/A")

    # set user status
    status = load_status()
    status[user_id] = f"edit67_caption:{file_uuid}"
    save_status(status)

    await callback_query.answer()
    await callback_query.message.edit_text(
        f"📝 Edit Caption\nCurrent Caption: {current_caption}\n\nनया caption भेजें:"
    )
# ---------- Callback: Toggle Visibility ----------
@app.on_callback_query(filters.regex(r"^edit_visibility67:(.+)$"))
async def edit_visibility_callback(client, callback_query: CallbackQuery):
    file_uuid = callback_query.data.split(":")[1]

    # load bot_data
    bot_data = load_json(data_file  )
    file_node = find_file_by_id(bot_data.get("data", {}), file_uuid)
    if not file_node:
        await callback_query.answer("⚠️ File details नहीं मिली।", show_alert=True)
        return

    # toggle visibility
    current = file_node.get("visibility", "private")
    new_visibility = "vip" if current != "vip" else "private"
    file_node["visibility"] = new_visibility

    # save back
    with open(data_file  , "w") as f:
        json.dump(bot_data, f, indent=2)

    await callback_query.answer(f"Visibility बदल दी गई: {new_visibility}")
    # refresh edit menu
    await edit_file_handler(client, callback_query)

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ---------- Handler for rename and caption using StatusFilter ----------
@app.on_message(filters.private & filters.text & StatusFilter("rename67_file"))
async def handle_rename(client, message):
    user_id = str(message.from_user.id)
    status_data = load_status()  # status_user.json
    file_uuid = status_data.get(user_id, "").split(":", 1)[-1]

    if not file_uuid:
        await message.reply_text("⚠️ File UUID नहीं मिला।")
        return

    # load bot_data
    bot_data = load_json(data_file  )
    file_node = find_file_by_id(bot_data.get("data", {}), file_uuid)
    if not file_node:
        await message.reply_text("⚠️ File details नहीं मिली।")
        return

    # rename apply
    file_node["name"] = message.text.strip()
    with open(data_file  , "w") as f:
        json.dump(bot_data, f, indent=2)

    # clear status
    status_data.pop(user_id, None)
    save_status(status_data)

    # reply with updated details
    await send_updated_file_details(client, message, file_uuid, caption="Name updated ✅")


@app.on_message(filters.private & filters.text & StatusFilter("edit67_caption"))
async def handle_caption(client, message):
    user_id = str(message.from_user.id)
    status_data = load_status()  # status_user.json
    file_uuid = status_data.get(user_id, "").split(":", 1)[-1]

    if not file_uuid:
        await message.reply_text("⚠️ File UUID नहीं मिला।")
        return

    # load bot_data
    bot_data = load_json(data_file  )
    file_node = find_file_by_id(bot_data.get("data", {}), file_uuid)
    if not file_node:
        await message.reply_text("⚠️ File details नहीं मिली।")
        return

    # caption apply
    file_node["caption"] = message.text.strip()
    with open(data_file  , "w") as f:
        json.dump(bot_data, f, indent=2)

    # clear status
    status_data.pop(user_id, None)
    save_status(status_data)

    # reply with updated details
    await send_updated_file_details(client, message, file_uuid, caption="Caption updated ✅")


# ---------- Function to show updated file details + buttons ----------
async def send_updated_file_details(client, message, file_uuid, caption=""):
    bot_data = load_json(data_file  )
    liked_data = load_json(LIKED_FILE)
    disliked_data = load_json(DISLIKED_FILE)
    views_data = load_json(PDF_VIEWS_FILE)

    file_node = find_file_by_id(bot_data.get("data", {}), file_uuid)
    if not file_node:
        await message.reply_text("⚠️ File details नहीं मिली।")
        return

    file_name = file_node.get("name", "Unknown.pdf")
    file_type = file_node.get("sub_type", file_node.get("type", "unknown"))
    file_caption = file_node.get("caption", "N/A")
    visibility = file_node.get("visibility", "private")
    earning_on = "✅ True" if visibility == "vip" else "❌ False"

    # performance
    likes = len(liked_data.get(file_uuid, []))
    dislikes = len(disliked_data.get(file_uuid, []))
    views = len(views_data.get(file_uuid, []))

    text = (
        f"{caption}\n\n"
        f"📊 **File Details**\n\n"
        f"🆔 UUID: `{file_uuid}`\n"
        f"📄 File name: {file_name}\n"
        f"📂 File type: {file_type}\n"
        f"📝 Caption: {file_caption}\n"
        f"💰 Earning On: {earning_on} \n\n"
        f"👍 Likes: {likes}\n"
        f"👎 Dislikes: {dislikes}\n"
        f"👁 Views: {views}"
    )

    # buttons
    buttons = [
        [
            InlineKeyboardButton("💰 See earning", callback_data=f"see_earning:{file_uuid}"),
            InlineKeyboardButton("✏️ Edit file details", callback_data=f"edit67_file:{file_uuid}")
        ]
    ]

    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@app.on_callback_query(filters.regex(r"^see_earning:(.+)$"))
async def see_earning_callback(client, callback_query: CallbackQuery):
    file_uuid = callback_query.data.split(":")[1]

    # Load JSON data
    bot_data = load_json(data_file  )
    liked_data = load_json(LIKED_FILE)
    disliked_data = load_json(DISLIKED_FILE)
    views_data = load_json(PDF_VIEWS_FILE)

    # Get file details
    file_node = find_file_by_id(bot_data.get("data", {}), file_uuid)
    if not file_node:
        await callback_query.answer("⚠️ File details नहीं मिली।", show_alert=True)
        return

    file_name = file_node.get("name", "Unknown.pdf")
    premium_owner = file_node.get("premium_owner", "N/A")

    # Raw stats
    total_views = len(views_data.get(file_uuid, []))
    likes = len(liked_data.get(file_uuid, []))
    dislikes = len(disliked_data.get(file_uuid, []))

    # Adjusted stats
    only_views = max(total_views - likes, 0)  # negative ना हो इसलिए max
    final_likes = likes
    final_dislikes = dislikes

    # Earning formula
    earning_usd = (0.005 * only_views) + (0.01 * final_likes) - (0.008 * final_dislikes)
    earning_inr = earning_usd * 82

    # Build report text
    text = (
        f"📊 **Earnings Report**\n\n"
        f"📄 File Name: {file_name}\n"
        f"👤 Premium Owner ID: {premium_owner}\n"
        f"🆔 UUID: `{file_uuid}`\n\n"
        f"👁 Total Views : {total_views}\n"
        f"👍 Likes: {final_likes}\n"
        f"👎 Dislikes: {final_dislikes}\n\n"
        f"💰 Total Earning: **${earning_usd:.3f}**  (₹{earning_inr:.2f})\n\n"
        f"If you want to withdraw please use /withdrawal command"
    )

    # Inline Keyboard with Back
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("⬅️ Back", callback_data=f"pdf_anl:{file_uuid}")]]
    )

    await callback_query.message.edit_text(text, reply_markup=keyboard)
    await callback_query.answer()
    
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
import json, os


# ---------- Step 1: Delete Confirmation ----------
@app.on_callback_query(filters.regex(r"^delete67_file:(.+)$"))
async def delete67_file_callback(client, callback_query: CallbackQuery):
    file_uuid = callback_query.data.split(":")[1]

    buttons = [
        [
            InlineKeyboardButton("✅ Confirm", callback_data=f"delete_file671:{file_uuid}"),
            InlineKeyboardButton("⬅️ Back", callback_data=f"edit67_file:{file_uuid}")
        ]
    ]

    await callback_query.answer()
    await callback_query.message.edit_text(
        f"⚠️ क्या आप सच में इस file को delete करना चाहते हैं?\n\n🆔 UUID: {file_uuid}",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
# ---------- Step 1: Delete Confirmation ----------
@app.on_callback_query(filters.regex(r"^delete_file671:(.+)$"))
async def delete67_file_callback(client, callback_query: CallbackQuery):
    file_uuid = callback_query.data.split(":")[1]

    buttons = [
        [
            InlineKeyboardButton("⬅️ Back", callback_data=f"edit67_file:{file_uuid}"),
            InlineKeyboardButton("✅ Confirm", callback_data=f"delete_file67:{file_uuid}")
            
        ]
    ]

    await callback_query.answer()
    await callback_query.message.edit_text(
        f"Do you Really Want to delete this file?\n\n🆔 UUID: {file_uuid}",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# ---------- Step 2: Actual Delete ----------
@app.on_callback_query(filters.regex(r"^delete_file67:(.+)$"))
async def delete_file67_callback(client, callback_query: CallbackQuery):
    file_uuid = callback_query.data.split(":")[1]

    try:
        with open(data_file  , "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {}

    # Recursive function to delete file by uuid
    def delete_from_items(items, uuid):
        for i, item in enumerate(items):
            if item.get("id") == uuid and item.get("type") == "file":
                deleted_item = items.pop(i)
                return deleted_item
            elif item.get("type") == "folder":
                result = delete_from_items(item.get("items", []), uuid)
                if result:
                    return result
        return None

    deleted_item = delete_from_items(data.get("data", {}).get("items", []), file_uuid)

    if deleted_item:
        # Save updated data
        with open(data_file  , "w") as f:
            json.dump(data, f, indent=2)

        # Load deleted file log
        try:
            with open(DELETED_PDF_FILE, "r") as f:
                deleted_log = json.load(f)
        except FileNotFoundError:
            deleted_log = {}

        user_id = str(deleted_item.get("premium_owner", "unknown"))
        file_id = deleted_item.get("file_id", "")

        # Append deleted entry
        if user_id not in deleted_log:
            deleted_log[user_id] = []

        deleted_log[user_id].append({
            "uuid": file_uuid,
            "file_id": file_id,
            "premium_owner": user_id
        })

        # Save log
        with open(DELETED_PDF_FILE, "w") as f:
            json.dump(deleted_log, f, indent=2)

        await callback_query.answer("File deleted ✅", show_alert=True)
        await callback_query.message.edit_text(
            f"🗑 File {file_uuid} deleted SUCCESSFULLY ✔️"
        )
    else:
        await callback_query.answer("File नहीं मिली ❌", show_alert=True)
        
@app.on_callback_query(filters.regex(r"^file_destination67:(.+)$"))
async def file_destination67_handler(client, callback_query: CallbackQuery):
    file_uuid = callback_query.data.split(":")[1]

    try:
        with open(data_file  , "r") as f:
            bot_data = json.load(f)
    except FileNotFoundError:
        await callback_query.message.reply_text("❌ bot_data.json missing है।")
        return

    # Recursive search with path trace
    def find_file_with_path(items, uuid, path):
        for item in items:
            if item.get("id") == uuid and item.get("type") == "file":
                return path + [item.get("name", "Unknown")]
            elif item.get("type") == "folder":
                res = find_file_with_path(item.get("items", []), uuid, path + [item.get("name", "Unnamed Folder")])
                if res:
                    return res
        return None

    path_list = find_file_with_path(bot_data.get("data", {}).get("items", []), file_uuid, [bot_data.get("data", {}).get("name", "Root")])

    if not path_list:
        await callback_query.message.reply_text("❌ File नहीं मिली।")
        return

    full_path = " / ".join(path_list)
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("⬅️ Back", callback_data=f"pdf_anl:{file_uuid}")]]
    )
    await callback_query.answer()
    await callback_query.message.reply_text(f"📂 File Destination:\n`{full_path}`", reply_markup=keyboard)
    
from pymongo import MongoClient
import json
import os

def save_json_files_to_mongo():
    # File paths
    # MongoDB client
    client = MongoClient(MD_URI)
    db = client["bot_database"]

    # ---- pre_files_over.json save ----
    if os.path.exists(pre_file):
        with open(pre_file, "r") as f:
            pre_data = json.load(f)
        # Replace existing collection with new data
        db["pre_files_over"].delete_many({})  # clear old data
        if pre_data:
            # Convert to list of documents
            pre_docs = [{"owner_id": k, "file_ids": v} for k, v in pre_data.items()]
            db["pre_files_over"].insert_many(pre_docs)
        print("✅ pre_files_over.json saved to MongoDB")

    # ---- deleted_user_files.json save ----
    if os.path.exists(DELETED_PDF_FILE):
        with open(DELETED_PDF_FILE, "r") as f:
            deleted_data = json.load(f)
        db["deleted_user_files"].delete_many({})  # clear old data
        if deleted_data:
            deleted_docs = [{"user_id": k, "file_ids": v} for k, v in deleted_data.items()]
            db["deleted_user_files"].insert_many(deleted_docs)
        print("✅ deleted_user_files.json saved to MongoDB")

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import os

# ----------------- Paths ----------------

# ----------------- Helper function -----------------
def calculate_user_earnings(user_id):
    # Load JSON
    with open(pre_file, "r") as f:
        pre_data = json.load(f)
    with open(DISLIKED_FILE, "r") as f:
        disliked_data = json.load(f)
    with open(LIKED_FILE, "r") as f:
        liked_data = json.load(f)
    with open(PDF_VIEWS_FILE, "r") as f:
        views_data = json.load(f)

    file_ids = pre_data.get(str(user_id), [])
    total_usd = 0
    total_views = 0
    total_likes = 0
    total_dislikes = 0

    for fid in file_ids:
        total_views1 = len(views_data.get(fid, []))
        final_likes = len(liked_data.get(fid, []))
        only_views = total_views1 - final_likes
        final_dislikes = len(disliked_data.get(fid, []))

        earning_usd = (0.005 * only_views) + (0.01 * final_likes) - (0.008 * final_dislikes)
        total_usd += earning_usd
        total_views += total_views1
        total_likes += final_likes
        total_dislikes += final_dislikes

    total_inr = total_usd * 82
    return {
        "usd": round(total_usd, 4),
        "inr": round(total_inr),
        "pdf_count": len(file_ids),
        "views": total_views,
        "likes": total_likes,
        "dislikes": total_dislikes,
        "file_ids": file_ids
    }

# ----------------- /my_earnings handler -----------------


import json, os


def get_total_withdrawn(user_id, currency="inr"):
    """
    Calculate total withdrawn for user.
    Only 'completed' requests count towards total.
    currency: 'inr' or 'usd'
    """
    if not os.path.exists(WITHDRAW_FILE):
        return 0

    with open(WITHDRAW_FILE, "r") as f:
        try:
            all_data = json.load(f)
        except json.JSONDecodeError:
            return 0

    user_data = all_data.get(str(user_id))
    if not user_data:
        return 0

    total = 0
    for r in user_data.get("requests", []):
        if r.get("status", "").lower() == "completed":
            if currency.lower() == "usd":
                total += r.get("amount_usd", 0)
            else:
                total += r.get("amount_inr", 0)

    return total

from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# 📌 Earnings Command
@app.on_message(filters.private & filters.command("my_earnings"))
async def my_earnings_handler(client, message):
    user_id = str(message.from_user.id)
    data = calculate_user_earnings(user_id)

    withdrawn = get_total_withdrawn(user_id)   # ✅ actual withdrawn amount
    available_balance = data["inr"] - withdrawn  # INR में बैलेंस

    text = (
        f"💰 **Your Earnings Summary** 💰\n\n"
        f"**Available Balance:** ₹{round(available_balance,2)}\n"
        f"**Total Earning Was:** ₹{data['inr']}\n"
        f"**Withdrawal:** ₹{withdrawn}\n\n"
        f"📄 **Your PDFs:** {data['pdf_count']}\n"
        f"👀 **Total Views:** {data['views']}\n"
        f"👍 **Total Likes:** {data['likes']}\n"
        f"👎 **Total Dislikes:** {data['dislikes']}"
    )

    buttons = [
        [InlineKeyboardButton("See Your PDFs Details", callback_data="show_my_pdfs")],
        [InlineKeyboardButton("💵 Withdraw", callback_data="withdraw_request")],
        [InlineKeyboardButton("🔄 Refresh Earnings", callback_data=f"my_earnings")]
    ]
    kb = InlineKeyboardMarkup(buttons)

    await message.reply_text(text, reply_markup=kb)

# 📌 Callback Query Handler for my_earnings
@app.on_callback_query(filters.regex("^my_earnings$"))
async def my_earnings_callback(client, callback_query):
    user_id = str(callback_query.from_user.id)  # ✅ Directly callback से लिया
    data = calculate_user_earnings(user_id)

    withdrawn = get_total_withdrawn(user_id)
    available_balance = data["inr"] - withdrawn

    text = (
        f"💰 **Your Earnings Summary (Updated)** 💰\n\n"
        f"**Available Balance:** ₹{round(available_balance,2)}\n"
        f"**Total Earning Was:** ₹{data['inr']}\n"
        f"**Withdrawal:** ₹{withdrawn}\n\n"
        f"📄 **Your PDFs:** {data['pdf_count']}\n"
        f"👀 **Total Views:** {data['views']}\n"
        f"👍 **Total Likes:** {data['likes']}\n"
        f"👎 **Total Dislikes:** {data['dislikes']}"
    )

    buttons = [
        [InlineKeyboardButton("See Your PDFs Details", callback_data="show_my_pdfs")],
        [InlineKeyboardButton("💵 Withdraw", callback_data="withdraw_request")],
        [InlineKeyboardButton("🔄 Refresh Earnings", callback_data="my_earnings")]
    ]
    kb = InlineKeyboardMarkup(buttons)

    await callback_query.message.edit_text(text, reply_markup=kb)
    await callback_query.answer("🔄 Earnings refreshed!", show_alert=False)
# 📌 Callback Query Handler for my_earnings
# ----------------- Callback Handlers -----------------
import math
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# ----------------- Pagination Helper -----------------
def get_file_name_by_uuid(file_uuid):
    try:
        with open(os.path.join(BASE_PATH, "bot_data.json"), "r") as f:
            bot_data = json.load(f)
    except FileNotFoundError:
        return "📛 DELETED FILE"  # fallback

    def search(items, uuid):
        for item in items:
            if item.get("id") == uuid and item.get("type") == "file":
                return item.get("name", "📛 DELETED FILE")
            elif item.get("type") == "folder":
                res = search(item.get("items", []), uuid)
                if res:
                    return res
        return None

    return search(bot_data.get("data", {}).get("items", []), file_uuid) or  "📛 DELETED FILE"


def build_pdfs_keyboard(file_ids, page=1, per_page=10):
    total = len(file_ids)
    total_pages = math.ceil(total / per_page)
    start = (page - 1) * per_page
    end = start + per_page
    page_files = file_ids[start:end]

    buttons = []
    for fid in page_files:
        file_name = get_file_name_by_uuid(fid)
        buttons.append([InlineKeyboardButton(file_name, callback_data=f"pdf_anl:{fid}")])

    # Pagination controls
    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"show_my_pdfs:{page-1}"))
    if page < total_pages:
        nav_buttons.append(InlineKeyboardButton("Next ➡️", callback_data=f"show_my_pdfs:{page+1}"))

    if nav_buttons:
        buttons.append(nav_buttons)

    return InlineKeyboardMarkup(buttons), total, total_pages
# ----------------- Callback Handler -----------------
@app.on_callback_query(filters.regex(r"^show_my_pdfs(?:[:](\d+))?$"))
async def show_my_pdfs_callback(client, callback_query):
    user_id = callback_query.from_user.id
    match = callback_query.matches[0].group(1)
    page = int(match) if match else 1

    data = calculate_user_earnings(user_id)
    file_ids = data["file_ids"]

    if not file_ids:
        await callback_query.answer("❌ You have no PDFs yet.", show_alert=True)
        return

    kb, total, total_pages = build_pdfs_keyboard(file_ids, page=page)

    text = f"📄 **Total PDFs:** {total}\n📑 Page {page}/{total_pages}"

    await callback_query.message.edit_text(text, reply_markup=kb)

def get_user_withdrawals(user_id):
    if not os.path.exists(WITHDRAW_FILE):
        return []

    with open(WITHDRAW_FILE, "r") as f:
        try:
            all_data = json.load(f)
        except json.JSONDecodeError:
            return []

    user_data = all_data.get(str(user_id))
    if not user_data:
        return []

    # requests list
    requests = user_data.get("requests", [])
    formatted_requests = []
    for r in requests:
        formatted_requests.append({
            "amount": r.get("amount_inr", 0),
            "status": r.get("status", "Pending"),
            "date": r.get("time", "Unknown")
        })

    return formatted_requests

# 🔹 Withdraw request callback
@app.on_callback_query(filters.regex(r"^withdraw_request$"))
async def withdraw_request_callback(client, callback_query):
    user_id = str(callback_query.from_user.id)
    data = calculate_user_earnings(user_id)

    total_withdrawn_inr = get_total_withdrawn(user_id, "inr")
    total_withdrawn_usd = get_total_withdrawn(user_id, "usd")
    usd_balance = round(data["usd"] - total_withdrawn_usd, 3)
    inr_balance = data["inr"] - total_withdrawn_inr

    # 🔹 Check for pending request
    withdrawals = get_user_withdrawals(user_id)
    for w in withdrawals:
        if w.get("status", "").lower() == "pending":
            await callback_query.answer(
                f"❌ You already have a pending withdrawal request!\nAmount: ₹{w.get('amount_inr',0)} / ${w.get('amount_usd',0)}",
                show_alert=True
            )
            return

    # 🔹 Minimum $1 check
    if usd_balance < 1.0:
        await callback_query.answer(
            f"❌ Minimum $1 required to withdraw.\nYour current balance: ${usd_balance} (~₹{inr_balance})",
            show_alert=True
        )
        return

    # 🔹 Withdrawal page
    text = (
        "💵 **Your Withdrawal Status** 💵\n\n"
        f"✅ Available Balance: ${usd_balance} (~₹{inr_balance})\n"
        f"⚡ Minimum withdrawal reached!\n\n"
        "🔔 Please proceed with withdrawal request."
    )

    buttons = [
        [InlineKeyboardButton("📤 Request Withdrawal", callback_data="confirm_withdraw")],
        [InlineKeyboardButton("⬅️ Back", callback_data="withdrawal")]
    ]
    kb = InlineKeyboardMarkup(buttons)
    await callback_query.message.edit_text(text, reply_markup=kb)
    




# 🔹 Function 1: JSON file से withdrawal data MongoDB में save/update करो
def save_withdrawals_to_mongo():
    json_file=WITHDRAW_FILE
    client = MongoClient(MD_URI)
    db = client["bot_database"]
    withdrawals_col = db["withdrawals"]
    with open(json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    for user_id, details in data.items():
        # total_withdrawn auto calculate करो सिर्फ completed से
        total_usd = sum(req["amount_usd"] for req in details["requests"] if req["status"] == "completed")
        total_inr = sum(req["amount_inr"] for req in details["requests"] if req["status"] == "completed")

        details["total_withdrawn_usd"] = round(total_usd, 2)
        details["total_withdrawn_inr"] = total_inr

        withdrawals_col.update_one(
            {"user_id": user_id},
            {"$set": details},
            upsert=True
        )
    print("✅ Withdrawals saved/updated in MongoDB")
