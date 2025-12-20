import json
import base64
import itertools
import os
import asyncio
import aiohttp
import aiofiles
from pyrogram import filters, enums
from script import app
from common_data import tokens, CHAT_HISTODY_FILE

# ---------------- CONFIGURATION ----------------
MAX_HISTORY_LENGTH = 20
TIMEOUT_SECONDS = 30
SYSTEM_MSG_FILE = "CHAT_SYSTEM_MSG"

# Default fallback prompt (agar URL down ho aur file na mile)
DEFAULT_PROMPT = "You are a helpful AI assistant."

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

# ---------------- SYSTEM PROMPT MANAGEMENT ----------------
async def fetch_and_save_system_prompt(bot_username):
    """URL se prompt fetch karke file mein save karega"""
    url = f"https://www.singodiya.tech/AI-SYSTEM/@{bot_username}.json"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    # Maan lete hain JSON ek list hai ["You are..."]
                    if isinstance(data, list) and len(data) > 0:
                        prompt_text = data[0]
                    else:
                        prompt_text = str(data)

                    # File mein save karein
                    async with aiofiles.open(SYSTEM_MSG_FILE, "w", encoding="utf-8") as f:
                        await f.write(prompt_text)
                    print(f"System Prompt Updated from {url}")
                else:
                    print(f"Failed to fetch prompt. Status: {response.status}")
    except Exception as e:
        print(f"Error updating system prompt: {e}")

async def get_formatted_system_prompt(client, message):
    """File se prompt padh kar dynamic values replace karega"""
    # 1. File se prompt load karo
    prompt_text = DEFAULT_PROMPT
    if os.path.exists(SYSTEM_MSG_FILE):
        try:
            async with aiofiles.open(SYSTEM_MSG_FILE, "r", encoding="utf-8") as f:
                prompt_text = await f.read()
        except:
            pass
    
    # 2. User aur Bot ki details nikalo
    user = message.from_user
    bot = await client.get_me()
    
    first_name = user.first_name if user.first_name else "User"
    user_username = f"@{user.username}" if user.username else "No Username"
    user_id = str(user.id)
    
    bot_name = bot.first_name
    bot_username = f"@{bot.username}"

    # 3. Replacements (Dynamic Values)
    # Syntax: ₹{variable_name}
    replacements = {
        "₹{first_name}": first_name,
        "₹{user_username}": user_username,
        "₹{user_id}": user_id,
        "₹{bot_name}": bot_name,
        "₹{bot_username}": bot_username
    }
    
    final_prompt = prompt_text
    for key, value in replacements.items():
        final_prompt = final_prompt.replace(key, value)
        
    return final_prompt

# ---------------- ASYNC CHAT HISTORY ----------------
async def load_history(user_id: int) -> list:
    if not os.path.exists(CHAT_HISTODY_FILE):
        return []
    try:
        async with aiofiles.open(CHAT_HISTODY_FILE, "r", encoding="utf-8") as f:
            content = await f.read()
            data = json.loads(content) if content else {}
            return data.get(str(user_id), [])
    except Exception:
        return []

async def save_history(user_id: int, history: list):
    try:
        if os.path.exists(CHAT_HISTODY_FILE):
            async with aiofiles.open(CHAT_HISTODY_FILE, "r", encoding="utf-8") as f:
                content = await f.read()
                data = json.loads(content) if content else {}
        else:
            data = {}

        data[str(user_id)] = history[-MAX_HISTORY_LENGTH:]

        async with aiofiles.open(CHAT_HISTODY_FILE, "w", encoding="utf-8") as f:
            await f.write(json.dumps(data, ensure_ascii=False, indent=2))
    except Exception:
        pass

# ---------------- AI ENGINE (SILENT) ----------------
async def ask_ai(client, message) -> str | None:
    user_id = message.from_user.id
    user_text = message.text
    
    # Dynamic System Prompt Generate karo
    system_prompt = await get_formatted_system_prompt(client, message)
    
    history = await load_history(user_id)

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_text})

    for attempt in range(3):
        api_key, api_url = await token_manager.get_next_credentials()

        if not api_key or not api_url:
            continue

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "nova-micro",
            "messages": messages
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    api_url, 
                    json=payload, 
                    headers=headers, 
                    timeout=TIMEOUT_SECONDS
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        reply = data["choices"][0]["message"]["content"]
                        
                        history.append({"role": "user", "content": user_text})
                        history.append({"role": "assistant", "content": reply})
                        await save_history(user_id, history)
                        
                        return reply
                    
                    elif response.status in [401, 403]:
                        print(f"Token failed (Attempt {attempt+1}), rotating...")
                        continue 
                    
                    else:
                        return None

        except Exception as e:
            print(f"Connection error: {e}")
            continue

    return None

# ---------------- STARTUP HOOK ----------------
# Bot start hone par ye function chalega
@app.on_start
async def on_bot_start(client):
    me = await client.get_me()
    print(f"Bot Started: {me.username}")
    # System prompt URL se fetch karo
    await fetch_and_save_system_prompt(me.username)


# ---------------- MESSAGE HANDLER ----------------
@app.on_message(filters.text & ~filters.command("start"))
async def ai_reply(client, message):
    user_id = message.from_user.id
    
    try:
        await client.send_chat_action(chat_id=message.chat.id, action=enums.ChatAction.TYPING)
    except:
        pass

    try:
        # Note: Ab hum 'client' aur 'message' dono pass kar rahe hain ask_ai ko
        reply = await ask_ai(client, message)
        
        if reply:
            await message.reply_text(reply, quote=True)
            
    except Exception:
        pass
