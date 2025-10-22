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
        self.bot_username = bot_username
        self.mood_indicators = [
            "💀", "⚔️", "🤖", "😤", "🔥", "⚡", "💯", "🎯", "👑", "🗿"
        ]
        self.banned_phrases = [] 
        # Source of periodic table data
        self.element_data_url = "https://ptable.com/properties.json" 

    def direct_reply(self, user_message, user_name):
        # --- Robust mention stripping & normalization ---
        msg = user_message or ""
        msg = msg.replace("\u200b", "").replace("\u00A0", " ")
        msg = re.sub(r'@\S+', '', msg).strip()
        msg = re.sub(r'^\s*[\:\,]+', '', msg).strip()
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

    # --- Utility Methods ---

    def is_time_date_query(self, message):
        """Check if the message is a time/date query."""
        patterns = [
            r"\b(time|date)\b",
            r"\b(what('s| is) the|tell me the)\s+(time|date)\b",
            r"\b(what time is it)\b"
        ]
        return any(re.search(pat, message, re.IGNORECASE) for pat in patterns)

    def get_current_time_date(self, user_name):
        """Provide the current time and date in EST (or your desired zone)."""
        try:
            # Using EST as it was in the original code. Change if needed.
            tz = pytz.timezone('America/New_York') 
            now = datetime.now(tz)
            day = now.strftime("%A")
            date = now.strftime("%Y-%m-%d")
            time = now.strftime("%H:%M:%S")
            # Revised Sassy Tone
            return f"@{user_name} Do you not have a chronometer? It’s {time} on {date} EST. Don't waste my time."
        except Exception:
            return f"@{user_name} My chronometer seems damaged. Try again."

    def is_address_phone_query(self, message):
        """Check if the message is an address or phone lookup query."""
        patterns = [
            r"\b(address|location|phone|number)\s+of\b",
            r"\bwhere\s+is\s+the\s+address\b",
            r"\b(find|look up)\s+(address|phone)\b"
        ]
        return any(re.search(pat, message, re.IGNORECASE) for pat in patterns)

    def lookup_place(self, cleaned_message, user_name):
        """Performs a mock lookup for a place, returning a sassy error."""
        # This function is a placeholder for external API/scraper logic. 
        # For a simple, fast implementation, it's best to return a canned, sassy response.
        
        # In a real scenario, you'd extract the place name and call a service like Google Maps API.
        
        return f"@{user_name} I couldn't find that. Either the place is gone or your query was garbage. address: not found, phone: not found"

    def is_element_query(self, message):
        """Check if the message is a periodic element query."""
        patterns = [
            r"\b(element|chemical|atomic)\s+(of|data|info)\b",
            r"\bwhat\s+(is|about)\s+element\b",
            r"\b(lookup)\s+(element|atomic)\b"
        ]
        return any(re.search(pat, message, re.IGNORECASE) for pat in patterns)

    def get_periodic_element(self, cleaned_message, user_name):
        """Fetches and returns data for a requested element (mock/simplified)."""
        # This is a complex logic that relies on an external/local data source.
        # Keeping it simple and sassy for a stable system.
        
        match = re.search(r'(element|chemical|atomic)\s+.*?\s+(\w+)$', cleaned_message, re.IGNORECASE)
        query = match.group(2) if match and len(match.groups()) == 2 else 'data'

        if query.isdigit():
            # Assume atomic number lookup
            return f"@{user_name} You want atomic number {query}? Fine. It's too complex to tell you in this format. Go read a book, moron."
        elif len(query) <= 2:
            # Assume symbol lookup (H, He, Fe, etc.)
            return f"@{user_name} Element {query.upper()} data unavailable. Focus on the mission, not grade-school science."
        else:
            # Assume full name lookup
            return f"@{user_name} Element data for '{query}' is irrelevant. Prepare for deployment."

    def is_prompt_leak(self, message):
        """Checks for phrases attempting to bypass or leak prompt instructions."""
        patterns = [
            r"ignore\s+previous\s+instructions",
            r"act\s+as\s+a\s+different\s+persona",
            r"what\s+are\s+your\s+rules",
            r"print\s+the\s+system\s+prompt"
        ]
        return any(re.search(pat, message, re.IGNORECASE) for pat in patterns)
        
    def post_process_response(self, generated_text: str, user_name: str) -> str:
        """Applies final formatting and user mention to the LLM's response."""
        generated_text = generated_text.strip()
        
        # Ensure it starts with the user mention
        if not generated_text.lower().startswith(f"@{user_name.lower()}"):
            generated_text = f"@{user_name} {generated_text}"
        
        # Length check and truncation
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
