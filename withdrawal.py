import os, json, datetime
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram import filters
from pdf_anlysis import calculate_user_earnings, get_total_withdrawn
from common_data import BASE_PATH
WITHDRAW_FILE = os.path.join(BASE_PATH, "user_withdrawal_details.json")
ADMINS_FILE = os.path.join(BASE_PATH, "admins.json")
from script import app
# Example function: user की withdrawal history fetch करने के लिए
import json, os
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
def load_json_file(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except Exception:
        return {}


def save_json_file(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


@app.on_callback_query(filters.regex(r"^confirm_withdraw$"))
async def confirm_withdraw_callback(client, callback_query):
    user = callback_query.from_user
    user_id = str(user.id)

    # earning data
    total_withdrawn = get_total_withdrawn(user_id)
    data = calculate_user_earnings(user_id)
    inr_balance = data["inr"] - total_withdrawn
    usd_balance = round(inr_balance / 82, 2)  # conversion example

    # withdrawal file
    withdraw_data = load_json_file(WITHDRAW_FILE)

    if user_id not in withdraw_data:
        withdraw_data[user_id] = {
            "total_withdrawn": 0,
            "requests": []
        }

    request_id = f"wd_{user_id}_{int(datetime.datetime.now().timestamp())}"

    new_request = {
        "id": request_id,
        "amount_usd": usd_balance,
        "amount_inr": inr_balance,
        "status": "pending",
        "time": str(datetime.datetime.now()),
    }

    withdraw_data[user_id]["requests"].append(new_request)
    save_json_file(WITHDRAW_FILE, withdraw_data)

    # notify user
    await callback_query.message.edit_text(
        "✅ Withdrawal request submitted successfully!\n"
        "Your request is pending admin approval."
    )

    # load admins
    admins = []
    try:
        with open(ADMINS_FILE, "r") as f:
            admins = json.load(f)
    except:
        pass

    # notify admins
    for admin_id in admins:
        try:
            text = (
                "⚡ **New Withdrawal Request** ⚡\n\n"
                f"👤 User: {user.first_name} (`{user.id}`)\n"
                f"💵 Requested: ${usd_balance} (~₹{inr_balance})\n"
                f"📄 PDFs: {data['pdf_count']}\n"
                f"👀 Views: {data['views']}\n"
                f"👍 Likes: {data['likes']}\n"
                f"👎 Dislikes: {data['dislikes']}\n\n"
                f"🆔 Request ID: {request_id}\n\n"
                "Please confirm or reject:"
            )

            buttons = [
                [
                    InlineKeyboardButton("✅ Complete", callback_data=f"wd_complete:{request_id}:{user_id}"),
                    InlineKeyboardButton("❌ Reject", callback_data=f"wd_reject:{request_id}:{user_id}")
                ]
            ]
            kb = InlineKeyboardMarkup(buttons)

            await client.send_message(admin_id, text, reply_markup=kb)

        except Exception as e:
            print(f"Failed to notify admin {admin_id}: {e}")

@app.on_callback_query(filters.regex(r"^wd_complete:(.+):(.+)$"))
async def withdrawal_complete_callback(client, callback_query):
    request_id, user_id = callback_query.data.split(":")[1:]
    withdraw_data = load_json_file(WITHDRAW_FILE)

    if user_id not in withdraw_data:
        await callback_query.answer("❌ User data not found.", show_alert=True)
        return

    for req in withdraw_data[user_id]["requests"]:
        if req["id"] == request_id and req["status"] == "pending":
            req["status"] = "completed"
            withdraw_data[user_id]["total_withdrawn"] += req["amount_inr"]
            save_json_file(WITHDRAW_FILE, withdraw_data)

            # Notify user
            try:
                await client.send_message(
                    int(user_id),
                    f"🎉 Your withdrawal request of ₹{req['amount_inr']} has been **completed successfully**!"
                )
            except:
                pass

            await callback_query.message.edit_text(
                f"✅ Withdrawal {request_id} marked as **completed**."
            )
            return

    await callback_query.answer("⚠️ Already processed.", show_alert=True)


@app.on_callback_query(filters.regex(r"^wd_reject:(.+):(.+)$"))
async def withdrawal_reject_callback(client, callback_query):
    request_id, user_id = callback_query.data.split(":")[1:]
    withdraw_data = load_json_file(WITHDRAW_FILE)

    if user_id not in withdraw_data:
        await callback_query.answer("❌ User data not found.", show_alert=True)
        return

    for req in withdraw_data[user_id]["requests"]:
        if req["id"] == request_id and req["status"] == "pending":
            req["status"] = "rejected"
            save_json_file(WITHDRAW_FILE, withdraw_data)

            # Notify user
            try:
                await client.send_message(
                    int(user_id),
                    f"❌ Your withdrawal request of ₹{req['amount_inr']} has been **rejected** by admin."
                )
            except:
                pass

            await callback_query.message.edit_text(
                f"❌ Withdrawal {request_id} has been **rejected**."
            )
            return

    await callback_query.answer("⚠️ Already processed.", show_alert=True)
    
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

@app.on_message(filters.private & filters.command("withdrawal"))
async def withdrawal_handler(client, message):
    user_id = str(message.from_user.id)
    
    # 🔹 User के earnings और withdrawn amount
    data = calculate_user_earnings(user_id)
    total_withdrawn = get_total_withdrawn(user_id)
    available_balance = data["inr"] - total_withdrawn

    # 🔹 User की withdrawal history
    withdrawals = get_user_withdrawals(user_id)  # List of dicts [{'amount': 100, 'status': 'Paid', 'date': '2025-09-20'}, ...]

    # अगर history empty है
    if not withdrawals:
        history_text = "आपने अभी तक कोई withdrawal request नहीं की है।"
    else:
        history_lines = []
        for w in withdrawals:
            history_lines.append(f"💵 ₹{w['amount']} | {w['status']} | {w['date']}")
        history_text = "\n".join(history_lines)

    text = (
        f"💰 **Your Withdrawal Summary** 💰\n\n"
        f"**Available Balance:** ₹{round(available_balance,2)}\n"
        f"**Total Withdrawn:** ₹{total_withdrawn}\n\n"
        f"📄 **Your Withdrawal History:**\n{history_text}"
    )

    buttons = [
        [InlineKeyboardButton("💵 Request New Withdrawal", callback_data="withdraw_request")],
        [InlineKeyboardButton("🔄 Refresh", callback_data="withdrawal")]
    ]
    kb = InlineKeyboardMarkup(buttons)

    await message.reply_text(text, reply_markup=kb)


# 📌 Callback Query Handler for withdrawal refresh
@app.on_callback_query(filters.regex("^withdrawal$"))
async def withdrawal_callback(client, callback_query):
    user_id = str(callback_query.from_user.id)
    
    data = calculate_user_earnings(user_id)
    total_withdrawn = get_total_withdrawn(user_id)
    available_balance = data["inr"] - total_withdrawn
    withdrawals = get_user_withdrawals(user_id)

    if not withdrawals:
        history_text = "आपने अभी तक कोई withdrawal request नहीं की है।"
    else:
        history_lines = [f"💵 ₹{w['amount']} | {w['status']} | {w['date']}" for w in withdrawals]
        history_text = "\n".join(history_lines)

    text = (
        f"💰 **Your Withdrawal Summary (Updated)** 💰\n\n"
        f"**Available Balance:** ₹{round(available_balance,2)}\n"
        f"**Total Withdrawn:** ₹{total_withdrawn}\n\n"
        f"📄 **Your Withdrawal History:**\n{history_text}"
    )

    buttons = [
        [InlineKeyboardButton("💵 Request New Withdrawal", callback_data="withdraw_request")],
        [InlineKeyboardButton("🔄 Refresh", callback_data="withdrawal")]
    ]
    kb = InlineKeyboardMarkup(buttons)

    await callback_query.message.edit_text(text, reply_markup=kb)
    await callback_query.answer("🔄 Withdrawal info refreshed!", show_alert=False)