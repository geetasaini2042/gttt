import json
import base64
import itertools
import os
import asyncio
import aiohttp
import aiofiles
from pyrogram import filters, enums
from script import app
from common_data import tokens, CHAT_HISTODY_FILE, SYSTEM_MSG_FILE

# ---------------- CONFIGURATION ----------------
MAX_HISTORY_LENGTH = 20
TIMEOUT_SECONDS = 30
DEFAULT_PROMPT = "You are a helpful AI assistant."

# Global Flag to check if prompt is loaded
SYSTEM_PROMPT_LOADED = False 

# ---------------- TOKEN MANAGER ----------------
class TokenManager:
    def __init__(self, token_list):
        self._cycle = itertools.cycle(token_list)
        self._lock = asyncio.Lock()

    def _double_b64_decode(self, value: str) -> str | None:
        try:
            return base64.b64decode(base64.b64decode(value)).decode().strip()
        except Exception:
            return None

    async def get_next_credentials(self):
        async with self._lock:
            token_obj = next(self._cycle)
        
        encoded_key = None
        for k, v in token_obj.items():
            if k != "ap":
                encoded_key = v
                break
        
        encoded_api = token_obj.get("ap")
        api_key = self._double_b64_decode(encoded_key)
        api_url = self._double_b64_decode(encoded_api)
        
        return api_key, api_url

token_manager = TokenManager(tokens)

# ---------------- HELPER FUNCTIONS ----------------
async def fetch_system_prompt_from_url(client):
    """
    Sirf tab chalega jab SYSTEM_PROMPT_LOADED = False hoga.
    """
    try:
        me = await client.get_me()
        bot_username = me.username
        url = f"https://www.singodiya.tech/AI-SYSTEM/@{bot_username}.json"
        
        print(f"🔄 Updating System Prompt from: {url}")

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    # Data list hai ya string, handle karo
                    if isinstance(data, list) and len(data) > 0:
                        prompt_text = data[0]
                    else:
                        prompt_text = str(data)

                    # File me save karo
                    async with aiofiles.open(SYSTEM_MSG_FILE, "w", encoding="utf-8") as f:
                        await f.write(prompt_text)
                    print("✅ System Prompt Updated Successfully.")
                else:
                    print(f"⚠️ Failed to update prompt. Status: {response.status}")
    except Exception as e:
        print(f"❌ Error fetching prompt: {e}")

async def get_formatted_system_prompt(client, message):
    """File padh ke variables replace karega"""
    prompt_text = DEFAULT_PROMPT
    
    # File read karo
    if os.path.exists(SYSTEM_MSG_FILE):
        try:
            async with aiofiles.open(SYSTEM_MSG_FILE, "r", encoding="utf-8") as f:
                prompt_text = await f.read()
        except:
            pass
    
    # Dynamic Replacement logic
    user = message.from_user
    me = await client.get_me()
    
    replacements = {
        "₹{first_name}": user.first_name or "User",
        "₹{user_username}": f"@{user.username}" if user.username else "No Username",
        "₹{user_id}": str(user.id),
        "₹{bot_name}": me.first_name,
        "₹{bot_username}": f"@{me.username}"
    }
    
    for k, v in replacements.items():
        prompt_text = prompt_text.replace(k, v)
        
    return prompt_text

async def load_history(user_id: int) -> list:
    if not os.path.exists(CHAT_HISTODY_FILE): return []
    try:
        async with aiofiles.open(CHAT_HISTODY_FILE, "r", encoding="utf-8") as f:
            content = await f.read()
            return json.loads(content).get(str(user_id), []) if content else []
    except: return []

async def save_history(user_id: int, history: list):
    try:
        if os.path.exists(CHAT_HISTODY_FILE):
            async with aiofiles.open(CHAT_HISTODY_FILE, "r", encoding="utf-8") as f:
                content = await f.read()
                data = json.loads(content) if content else {}
        else: data = {}
        
        data[str(user_id)] = history[-MAX_HISTORY_LENGTH:]
        async with aiofiles.open(CHAT_HISTODY_FILE, "w", encoding="utf-8") as f:
            await f.write(json.dumps(data, ensure_ascii=False, indent=2))
    except: pass

# ---------------- CORE LOGIC ----------------
@app.on_message(filters.text & ~filters.command("start"))
async def ai_reply(client, message):
    global SYSTEM_PROMPT_LOADED  # Global variable use kar rahe hain
    
    # 1. Check kro: Kya system prompt load ho chuka hai?
    if not SYSTEM_PROMPT_LOADED:
        await fetch_system_prompt_from_url(client)
        SYSTEM_PROMPT_LOADED = True  # Ab true set kardo taaki bar-bar na chale
    
    # 2. Typing action bhejo
    try:
        await client.send_chat_action(chat_id=message.chat.id, action=enums.ChatAction.TYPING)
    except:
        pass

    # 3. AI Logic
    try:
        user_id = message.from_user.id
        # Prompt formatted way me nikalo
        system_prompt = await get_formatted_system_prompt(client, message)
        history = await load_history(user_id)

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": message.text})

        # Token & Request Loop
        reply = None
        for attempt in range(3):
            api_key, api_url = await token_manager.get_next_credentials()
            if not api_key: continue
            
            try:
                headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                payload = {"model": "nova-micro", "messages": messages}
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(api_url, json=payload, headers=headers, timeout=TIMEOUT_SECONDS) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            reply = data["choices"][0]["message"]["content"]
                            
                            # Success -> Save History & Break Loop
                            history.append({"role": "user", "content": message.text})
                            history.append({"role": "assistant", "content": reply})
                            await save_history(user_id, history)
                            break
                        elif resp.status in [401, 403]:
                            continue # Try next token
                        else:
                            break # Server error, stop trying
            except:
                continue # Network error, try next

        # 4. Send Reply (Only if successful)
        if reply:
            await message.reply_text(reply, quote=True)

    except Exception as e:
        print(f"Error in handler: {e}")
