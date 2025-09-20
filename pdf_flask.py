import os
import json
from flask import Flask, request, jsonify
from script import flask_app
from common_data import BASE_PATH, pre_file, PDF_VIEWS_FILE, LIKED_FILE, DISLIKED_FILE, BOT_DATA_FILE, PDF_VIEWS_FILE, LIKED_FILE, DISLIKED_FILE, WITHDRAW_FILE

def calculate_user_earnings(user_id):
    # Load JSON files safely
    try:
        with open(pre_file, "r") as f:
            pre_data = json.load(f)
    except:
        pre_data = {}

    try:
        with open(PDF_VIEWS_FILE, "r") as f:
            views_data = json.load(f)
    except:
        views_data = {}

    try:
        with open(LIKED_FILE, "r") as f:
            liked_data = json.load(f)
    except:
        liked_data = {}

    try:
        with open(DISLIKED_FILE, "r") as f:
            disliked_data = json.load(f)
    except:
        disliked_data = {}

    file_ids = pre_data.get(str(user_id), [])
    total_usd = 0
    total_inr = 0
    total_views = 0
    total_likes = 0
    total_dislikes = 0

    for fid in file_ids:
        # Count views / likes / dislikes safely
        views_count = len(views_data.get(fid, []))
        likes_count = len(liked_data.get(fid, []))
        dislikes_count = len(disliked_data.get(fid, []))

        earning_usd = (0.005 * views_count) + (0.01 * likes_count) - (0.008 * dislikes_count)
        earning_inr = earning_usd * 82

        total_usd += earning_usd
        total_inr += earning_inr
        total_views += views_count
        total_likes += likes_count
        total_dislikes += dislikes_count

    return {
        "usd": round(total_usd, 4),
        "inr": round(total_inr, 2),
        "pdf_count": len(file_ids),
        "views": total_views,
        "likes": total_likes,
        "dislikes": total_dislikes,
        "file_ids": file_ids
    }

# 🔹 Get user withdrawals
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

    requests = user_data.get("requests", [])
    formatted_requests = []
    for r in requests:
        formatted_requests.append({
            "amount_inr": r.get("amount_inr", 0),
            "amount_usd": r.get("amount_usd", 0),
            "status": r.get("status", "Pending"),
            "date": r.get("time", "Unknown")
        })
    return formatted_requests

# 🔹 Get total withdrawn (only completed)
def get_total_withdrawn(user_id, currency="inr"):
    withdrawals = get_user_withdrawals(user_id)
    total = 0
    for w in withdrawals:
        if w.get("status", "").lower() == "completed":
            if currency.lower() == "usd":
                total += w.get("amount_usd", 0)
            else:
                total += w.get("amount_inr", 0)
    return total

# 🔹 API route to get user details
@flask_app.route("/user/<int:user_id>", methods=["GET"])
def get_user_details(user_id):
    user_id = str(user_id)
    earnings = calculate_user_earnings(user_id)

    total_withdrawn_inr = get_total_withdrawn(user_id, "inr")
    total_withdrawn_usd = get_total_withdrawn(user_id, "usd")

    available_inr = earnings["inr"] - total_withdrawn_inr
    available_usd = round(earnings["usd"] - total_withdrawn_usd, 3)

    withdrawals = get_user_withdrawals(user_id)

    return jsonify({
        "user_id": user_id,
        "earnings": earnings,
        "total_withdrawn": {
            "inr": total_withdrawn_inr,
            "usd": total_withdrawn_usd
        },
        "available_balance": {
            "inr": available_inr,
            "usd": available_usd
        },
        "withdrawal_history": withdrawals
    })


def load_json(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        return {}
def find_pdf(folder, uuid):
    """
    folder: ek dict jisme 'items' list hoti hai
    uuid: jis file ka id dhundhna hai
    """
    if not isinstance(folder, dict):
        return None

    items = folder.get("items", [])
    for item in items:
        if not isinstance(item, dict):
            continue

        # agar yahi file hai
        if item.get("id") == uuid and item.get("type") == "file":
            return item

        # agar nested folder mila to recursion
        if item.get("type") == "folder":
            res = find_pdf(item, uuid)
            if res:
                return res
    return None

@flask_app.route("/file-anl/", methods=["GET"])
def file_analysis():
    pdf_uuid = request.args.get("uuid")
    if not pdf_uuid:
        return jsonify({"error": "uuid parameter is required"}), 400

    bot_data = load_json(BOT_DATA_FILE)
    views_data = load_json(PDF_VIEWS_FILE)
    liked_data = load_json(LIKED_FILE)
    disliked_data = load_json(DISLIKED_FILE)

    root_folder = bot_data.get("data", {})
    pdf_data = find_pdf(root_folder, pdf_uuid)

    if not pdf_data:
        return jsonify({"error": "PDF not found"}), 404

    # Safe copy + analytics
    pdf_data_copy = dict(pdf_data)
    pdf_data_copy["views_count"] = len(views_data.get(pdf_uuid, []))
    pdf_data_copy["likes_count"] = len(liked_data.get(pdf_uuid, []))
    pdf_data_copy["dislikes_count"] = len(disliked_data.get(pdf_uuid, []))

    return jsonify(pdf_data_copy), 200