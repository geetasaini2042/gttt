import os
from dotenv import load_dotenv
load_dotenv()
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
MD_URI = os.getenv("MONGODB_URI")
WELCOME_MSG = os.getenv("WELCOME_MSG")
DEPLOY_URL = os.getenv("URL")
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
data_file = os.path.join(BASE_PATH, "bot_data.json")
status_user_file = os.path.join(BASE_PATH, "status_user.json")
temp_folder_file = os.path.join(BASE_PATH, "tempfolder.json")
temp_url_file = os.path.join(BASE_PATH, "tempurl.json")
temp_webapp_file = os.path.join(BASE_PATH, "tempwebapp.json")
temp_file_json = os.path.join(BASE_PATH, "tempfile.json")
users_file = os.path.join(BASE_PATH, "users.json")
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
