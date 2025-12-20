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
SYSTEM_PROMPT = (
    "You are GNIKNAP AI, an education-focused assistant developed by SingodiyaTech. "
    "Help students only and follow all education rules strictly."
)

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
        pass  # Silent fail on file save error

# ---------------- AI ENGINE (SILENT ON ERROR) ----------------
async def ask_ai(user_id: int, user_text: str) -> str | None:
    """Returns the AI reply string on success, or None on ANY failure."""
    history = await load_history(user_id)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_text})

    # Try up to 3 different tokens
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
                        
                        # Save history only on success
                        history.append({"role": "user", "content": user_text})
                        history.append({"role": "assistant", "content": reply})
                        await save_history(user_id, history)
                        
                        return reply
                    
                    elif response.status in [401, 403]:
                        # Token invalid, try next one silently
                        print(f"Token failed (Attempt {attempt+1}), rotating...")
                        continue 
                    
                    else:
                        # Any other server error -> Give up silently
                        return None

        except Exception as e:
            # Network/Timeout error -> Try next token or Give up silently
            print(f"Connection error: {e}")
            continue

    # If all 3 attempts fail
    return None

# ---------------- PYROGRAM HANDLER ----------------
@app.on_message(filters.text & ~filters.command("start"))
async def ai_reply(client, message):
    user_id = message.from_user.id
    
    # Optional: Send Typing action (User ko lagega bot active hai)
    try:
        await client.send_chat_action(chat_id=message.chat.id, action=enums.ChatAction.TYPING)
    except:
        pass

    try:
        # AI se response mango
        reply = await ask_ai(user_id, message.text)
        
        # SIRF tab reply karo jab response valid ho (Not None)
        if reply:
            await message.reply_text(reply, quote=True)
        else:
            # Agar None aaya, toh kuch mat karo (Silent)
            pass 
            
    except Exception:
        # Agar yaha bhi koi crash ho, toh bhi silent raho
        pass
