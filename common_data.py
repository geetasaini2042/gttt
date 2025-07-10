import os,json
from dotenv import load_dotenv
load_dotenv()
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
REQUIRED_CHANNELS = os.getenv("REQUIRED_CHANNELS", "")  # comma-separated
MD_URI = os.getenv("MONGODB_URI")
DEPLOY_URL = os.getenv("URL", "http://127.0.0.1:5000/upload-data")
OWNER = int(os.getenv("OWNER", 6150091802))
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
data_file = os.path.join(BASE_PATH, "bot_data.json")
data_file1 = os.path.join(BASE_PATH, "commands_data.json")
status_user_file = os.path.join(BASE_PATH, "status_user.json")
temp_folder_file = os.path.join(BASE_PATH, "tempfolder.json")
temp_url_file = os.path.join(BASE_PATH, "tempurl.json")
temp_webapp_file = os.path.join(BASE_PATH, "tempwebapp.json")
temp_file_json = os.path.join(BASE_PATH, "tempfile.json")
users_file = os.path.join(BASE_PATH, "users.json")
ADMINS_FILE = os.path.join(BASE_PATH, "ADMINS.json")
try:
    with open(ADMINS_FILE, "r") as f:
        ADMINS = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    ADMINS = [6150091802]  # default fallback
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
