from pyrogram.filters import Filter
import json
import os

# ये imports बाहर config या main में भी हो सकते हैं
try:
    from config import USE_MONGO, db
except ImportError:
    USE_MONGO = False
    db = None

class StatusFilter(Filter):
    def __init__(self, status_prefix):
        self.status_prefix = status_prefix

    async def __call__(self, client, message):
        user_id = str(message.from_user.id)

        try:
            if USE_MONGO and db is not None:
                doc = await db["status_user"].find_one({"user_id": user_id})
                current_status = doc.get("status", "") if doc else ""
            else:
                path = "/storage/emulated/0/BotBuilder/PYTHON/status_user.json"
                if os.path.exists(path):
                    with open(path, "r", encoding="utf-8") as f:
                        status_data = json.load(f)
                    current_status = status_data.get(user_id, "")
                else:
                    current_status = ""
        except Exception as e:
            print(f"⚠️ StatusFilter error: {e}")
            return False

        return current_status.startswith(self.status_prefix)
