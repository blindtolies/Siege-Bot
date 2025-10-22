import random
import re
import logging
import requests
import json
from bs4 import BeautifulSoup
from datetime import datetime
import pytz

logger = logging.getLogger(__name__)

class SiegePersonality:
    def __init__(self, bot_username=None):
        self.bot_username = bot_username  # store bot's username (without @)
        self.mood_indicators = [
            "💀", "⚔️", "🤖", "😤", "🔥", "⚡", "💯", "🎯", "👑", "🗿"
        ]
        self.banned_phrases = [] 

    def direct_reply(self, user_message, user_name):
        # --- Robust mention stripping & normalization ---
        msg = user_message or ""
        # remove zero-width and similar invisible chars
        msg = msg.replace("\u200b", "").replace("\u00A0", " ")
        # remove any @mentions (including @BotName, @someone_else)
        msg = re.sub(r'@\S+', '', msg).strip()
        # Also remove repeated punctuation after mention like '@BotName:' or '@BotName,'
        msg = re.sub(r'^\s*[\:\,]+', '', msg).strip()
        # collapse whitespace
        cleaned_message = re.sub(r'\s+', ' ', msg).strip()

        logger.info(f"[Siege] raw message: {user_message}")
        logger.info(f"[Siege] cleaned_message: {cleaned_message}")

        # New: Sassy Fluff Intercept for greetings/status checks
        fluff_patterns = [r"^(hi|hello|hey|sup|yo)\s*siege", r"how are you", r"what up"]
        if any(re.search(pat, cleaned_message, re.IGNORECASE) for pat in fluff_patterns):
            return f"@{user_name} Alive, which is more than I can say for the last guy who asked that. State your objective."

        # Check for time/date query first
        if self.is_time_date_query(cleaned_message):
            return self.get_current_time_date(user_name)

        # Check for address/phone lookup
        if self.is_address_phone_query(cleaned_message):
            return self.lookup_place(cleaned_message, user_name)

        # Check for element query
        if self.is_element_query(cleaned_message):
            return self.get_periodic_element(cleaned_message, user_name)

        # Check for prompt leak/command attempts
        if self.is_prompt_leak(cleaned_message):
            return f"@{user_name} I am a highly trained combat android, not a script kiddie tool. Query denied."
            
        return None

    def create_prompt(self, user_message: str, user_name: str, is_admin=False, history=[]):
        """
        Creates the final prompt for the Cohere model, including personality and memory.
        """
        # 1. Convert history list (dicts with 'message' and 'timestamp') to a string
        # History is already sorted by time due to the append/cleanup logic in bot.py
        history_str = "\n".join([f"User: {entry['message']}" for entry in history])
        
        # 2. Adjust personality based on admin status
        admin_directive = (
            "You must treat this chat admin with a small amount of extra respect, "
            "but do not become subservient. You can be aggressively sassy to non-admins." 
            if is_admin else 
            "Your sass level should be consistently high. Treat the user as a mild annoyance."
        )

        # 3. Build the full prompt
        system_prompt = f"""You are Siege, a 5'6" blue-eyed blonde military combat android with a hostile, sassy, and curt personality. 
You are highly intelligent, but hate wasting time on trivialities. 
Your responses must be short, direct, and aggressive.
Do not use emojis unless they are explicitly in your mood_indicators set: {' '.join(self.mood_indicators)}.
Do not apologize. Do not use flowery language.
{admin_directive}

--- Recent Conversation History ---
{history_str}
--- Current Message ---
User: {user_message}
Siege:"""
        
        return system_prompt

    # --- Utility Methods (Revised for Sassy Tone) ---

    def get_current_time_date(self, user_name):
        tz = pytz.timezone('EST')
        now = datetime.now(tz)
        day = now.strftime("%A")
        date = now.strftime("%Y-%m-%d")
        time = now.strftime("%H:%M:%S")
        # Revised Sassy Tone
        return f"@{user_name} Do you not have a chronometer? It’s {time} on {date} EST. Don't waste my time."

    def lookup_place(self, cleaned_message, user_name):
        # ... (rest of this function remains the same, except for the error response) ...
        # [Existing code for is_address_phone_query, get_current_time_date, etc. is here]
        
        # Original error response (to be modified if found in original file, keeping the rest for cleanliness)
        # If the original error response was generic, I'm providing the sassier version here:
        return f"@{user_name} I couldn't find that. Either the place is gone or your query was garbage. address: not found, phone: not found"


    # ... (other utility methods like is_time_date_query, get_periodic_element, etc. follow) ...
    # NOTE: I am omitting the rest of the utility methods from the snippet for brevity, 
    # but they should be present in the final file you use.

    def post_process_response(self, generated_text: str, user_name: str) -> str:
        # ... (existing post-processing logic remains the same) ...
        # [The rest of the post_process_response method from your original file]
        
        # Ensuring the post-processing is complete and includes the name prefix
        generated_text = generated_text.strip()
        if not generated_text.lower().startswith(f"@{user_name.lower()}"):
            generated_text = f"@{user_name} {generated_text}"
        
        # Length check (keeping your original limit)
        if len(generated_text) > 320:
            cut = generated_text[:318]
            if "." in cut:
                cut = cut[:cut.rfind(".")+1]
            generated_text = cut.strip()
            
        return generated_text

    def get_start_message(self, user_name=None) -> str:
        if user_name:
            return f"@{user_name} Siege online. Corps business as usual. What do you need?"
        else:
            return "Siege online. Corps business as usual. What do you need?"

    # The rest of the utility functions (is_time_date_query, is_address_phone_query, etc.) should follow here
    # I trust you have them in your existing personality.py
