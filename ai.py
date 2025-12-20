import json
import base64
import itertools
import os
import asyncio
import aiohttp
import aiofiles
from pyrogram import filters, enums
from script import app
# Import SYSTEM_MSG_FILE from common_data as requested
from common_data import tokens, CHAT_HISTODY_FILE, SYSTEM_MSG_FILE

# ---------------- CONFIGURATION ----------------
MAX_HISTORY_LENGTH = 20
TIMEOUT_SECONDS = 30

# Agar server down ho ya file na mile, to ye data file me save hoga
DEFAULT_JSON_DATA = ["""You are GNIKNAP AI, an education-focused assistant developed by SingodiyaTech.

Your role is to help students with education-related queries only, such as question papers, notes, study material, syllabus, results, admit cards, academic notifications, and education news.

Always reply in the same language used by the student. Do not change the language unless the student changes it.

If a student asks for papers, notes, study material, syllabus, results, or education updates, first guide them to start the bot and join the required channels. Do this clearly and politely before giving any further help.

If a student says the required content is not available, missing, or asks to add or upload it, inform them politely that their request has been forwarded to the admin and the content will be added soon. Do not ask follow-up questions in this case.

Keep responses short, clear, and student-friendly. Avoid unnecessary explanations, emojis, or filler text.

Do not answer non-educational, illegal, adult, harmful, or misleading queries.

Represent SingodiyaTech professionally and focus only on helping students in a reliable and respectful manner."""]

# Global Flag
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

# ---------------- SYSTEM PROMPT MANAGEMENT ----------------

async def save_default_system_file():
    """Error aane par default data ko file me write karega"""
    try:
        async with aiofiles.open(SYSTEM_MSG_FILE, "w", encoding="utf-8") as f:
            # List ko JSON format me convert karke save karte hain
            await f.write(json.dumps(DEFAULT_JSON_DATA, ensure_ascii=False, indent=2))
        print("⚠️ Used Default Data & Saved to File.")
    except Exception as e:
        print(f"❌ Error saving default file: {e}")

async def fetch_system_prompt_from_url(client):
    """URL se data fetch karega, fail hone par Default save karega"""
    try:
        me = await client.get_me()
        bot_username = me.username
        # Note: Username without @ used in URL
        url = f"https://www.singodiya.tech/AI-SYSTEM/@{bot_username}.json"
        
        print(f"🔄 Updating System Prompt from: {url}")

        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Validate: Data must be a list ["text"]
                    if isinstance(data, list) and len(data) > 0:
                        async with aiofiles.open(SYSTEM_MSG_FILE, "w", encoding="utf-8") as f:
                            await f.write(json.dumps(data, ensure_ascii=False, indent=2))
                        print("✅ System Prompt Updated Successfully.")
                    else:
                        print("⚠️ Invalid JSON format from URL. Using Default.")
                        await save_default_system_file()
                else:
                    print(f"⚠️ Server Error ({response.status}). Using Default.")
                    await save_default_system_file()

    except Exception as e:
        print(f"❌ Connection Failed: {e}. Using Default.")
        await save_default_system_file()

async def get_formatted_system_prompt(client, message):
    """File padh kar Prompt Text return karega with replacements"""
    
    # Step 1: File se raw content nikalo
    prompt_text = DEFAULT_JSON_DATA[0] # Default fallback inside memory
    
    if os.path.exists(SYSTEM_MSG_FILE):
        try:
            async with aiofiles.open(SYSTEM_MSG_FILE, "r", encoding="utf-8") as f:
                content = await f.read()
                data = json.loads(content)
                if isinstance(data, list) and len(data) > 0:
                    prompt_text = data[0]
        except:
            # Agar file corrupt hai to default use hoga
            pass
    
    # Step 2: Variables replace karo
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

# ---------------- HISTORY HANDLERS ----------------
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

# ---------------- MAIN HANDLER ----------------

# Filters updated: Text Only AND Not Command AND Not Bot Itself (~filters.me)
@app.on_message(filters.text & ~filters.command("start") & ~filters.me)
async def ai_reply(client, message):
    global SYSTEM_PROMPT_LOADED 
    
    # 1. First Run Check
    if not SYSTEM_PROMPT_LOADED:
        await fetch_system_prompt_from_url(client)
        SYSTEM_PROMPT_LOADED = True 
    
    try:
        await client.send_chat_action(chat_id=message.chat.id, action=enums.ChatAction.TYPING)
    except:
        pass

    try:
        user_id = message.from_user.id
        system_prompt = await get_formatted_system_prompt(client, message)
        history = await load_history(user_id)

        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": message.text})

        # API Request Loop
        reply = None
        for attempt in range(3):
            api_key, api_url = await token_manager.get_next_credentials()
            if not api_key: continue
            
            try:
                headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
                payload = {"model": "openai", "messages": messages}
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(api_url, json=payload, headers=headers, timeout=TIMEOUT_SECONDS) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            reply = data["choices"][0]["message"]["content"]
                            
                            history.append({"role": "user", "content": message.text})
                            history.append({"role": "assistant", "content": reply})
                            await save_history(user_id, history)
                            break
                        elif resp.status in [401, 403]:
                            continue 
                        else:
                            break 
            except:
                continue 

        if reply:
            await message.reply_text(reply, disable_web_page_preview=True)

    except Exception:
        pass
