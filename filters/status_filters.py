from pyrogram.filters import Filter
import json

class StatusFilter(Filter):
    def __init__(self, status_prefix):
        self.status_prefix = status_prefix

    async def __call__(self, client, message):
        user_id = str(message.from_user.id)

        try:
            with open("/opt/render/project/src/status_user.json", "r") as f:
                status_data = json.load(f)
        except:
            return False

        current_status = status_data.get(user_id, "")
        return current_status.startswith(self.status_prefix)
