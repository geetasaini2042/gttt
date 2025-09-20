import os,json
from dotenv import load_dotenv
load_dotenv()
import requests
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
REQUIRED_CHANNELS = os.getenv("REQUIRED_CHANNELS", "")  # comma-separated
MD_URI = os.getenv("MONGODB_URI")
is_termux = os.getenv("is_termux", "false").lower() == "true"
DEPLOY_URL_UPLOAD = os.getenv("URL", "http://127.0.0.1:5000/upload-data")
OWNER = int(os.getenv("OWNER", 6150091802))
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
data_file = os.path.join(BASE_PATH, "bot_data.json")
BOT_DATA_FILE = data_file
DATA_FILE = data_file
data_file1 = os.path.join(BASE_PATH, "commands_data.json")
status_user_file = os.path.join(BASE_PATH, "status_user.json")
temp_folder_file = os.path.join(BASE_PATH, "tempfolder.json")
temp_url_file = os.path.join(BASE_PATH, "tempurl.json")
temp_webapp_file = os.path.join(BASE_PATH, "tempwebapp.json")
temp_file_json = os.path.join(BASE_PATH, "tempfile.json")
users_file = os.path.join(BASE_PATH, "users.json")
ADMINS_FILE = os.path.join(BASE_PATH, "ADMINS.json")
BLOCKED_FILE = os.path.join(BASE_PATH, "blocked_users.json")
FILE_LOGS = int(os.getenv("FILE_LOGS", -1002421086860))
PREMIUM_CHECK_LOG = int(os.getenv("PREMIUM_CHANNEL", -1002421086860))
DEPLOY_URL = os.getenv("URL", "http://127.0.0.1:5000").removesuffix("/upload-data")
LIKED_FILE  = os.path.join(BASE_PATH, "PRE/liked.json")
DISLIKED_FILE = os.path.join(BASE_PATH, "PRE/disliked.json")
PDF_VIEWS_FILE = os.path.join(BASE_PATH, "PRE/PDF_VIEWS_FILE.json")
pre_file = os.path.join(BASE_PATH, "pre_files_over.json")
DELETED_PDF_FILE = os.path.join(BASE_PATH, "deleted_user_files.json")
WITHDRAW_FILE = os.path.join(BASE_PATH, "user_withdrawal_details.json")
def ADMINS():
     try:
         with open(ADMINS_FILE, "r") as f:
             return json.load(f)
     except (FileNotFoundError, json.JSONDecodeError):
         return [6150091802]  # default fallback
FLAG_FILE = os.path.join(BASE_PATH, "ho.kuchhBhi")
STARTUP_MESSAGE = "🤖 Bot is now online! (via raw API)"

# Channel IDs from environment or hardcoded fallback
CHANNEL_IDS = [PREMIUM_CHECK_LOG, FILE_LOGS, REQUIRED_CHANNELS]

async def send_startup_message_once():
    if os.path.exists(FLAG_FILE):
        print("✅ Startup message already sent before.")
        return

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    for chat_id in CHANNEL_IDS:
        payload = {
            "chat_id": chat_id,
            "text": STARTUP_MESSAGE
        }

        try:
            response = requests.post(url, data=payload)
            result = response.json()
            if result.get("ok"):
                print(f"✅ Message sent to {chat_id}")
            else:
                print(f"❌ Failed for {chat_id}: {result}")
        except Exception as e:
            print(f"❌ Exception for {chat_id}: {e}")

    # Mark as done so it doesn't repeat
    with open(FLAG_FILE, "w") as f:
        f.write("done")
DEFAULT_JSON = {
    "data": {
        "id": "root",
        "name": "Root",
        "description": "Welcome to Singodiya Tech!",
        "type": "folder",
        "created_by": 6150091802,
        "parent_id": None,
        "user_allow": [],
        "items": []
    }
}
