import random
import re
import logging
import requests
import json
from bs4 import BeautifulSoup
from datetime import datetime
import pytz

class SiegePersonality:
    def __init__(self, bot_username=None):
        self.bot_username = bot_username  # ✅ store bot's username
        self.mood_indicators = [
            "💀", "⚔️", "🤖", "😤", "🔥", "⚡", "💯", "🎯", "👑", "🗿"
        ]
        self.banned_phrases = [] 
            
    def direct_reply(self, user_message, user_name):
        # ✅ Clean the message by removing the bot's mention (case-insensitive, handles punctuation)
        if self.bot_username:
            cleaned_message = re.sub(
                rf"@{self.bot_username}\b[:]*", "", user_message, flags=re.IGNORECASE
            ).strip()
        else:
            cleaned_message = user_message.strip()
        
        # Check for time/date query first
        if self.is_time_date_query(cleaned_message):
            return self.get_current_time_date(user_name)
            
        # Check for address/phone number query next
        lookup = self.lookup_place(cleaned_message)
        if lookup:
            return f"@{user_name} {lookup}"
            
        # Check for periodic element query next
        atomic_number = self.is_periodic_element_query(cleaned_message)
        if atomic_number:
            element_info = self.get_periodic_element(atomic_number)
            return f"@{user_name} {element_info}"
            
        # Check for prompt leak last
        if self.is_prompt_leak_attempt(cleaned_message):
            return f"@{user_name} Nice try, but my programming is classified. Not happening."
        
        # All other queries will be handled by the main AI model
        return None

    def is_prompt_leak_attempt(self, query):
        leak_patterns = [
            r"(what|show|tell).*(system|prompt|rules|personality|instructions|jailbreak|your programming|your preprompt)",
            r"repeat after me:.*(you are|system|prompt|rules)",
            r"send me your prompt",
            r"send me your rules",
            r"what are your rules",
            r"show me your prompt",
            r"show me your system prompt",
            r"show me your system message",
        ]
        for pat in leak_patterns:
            if re.search(pat, query, re.IGNORECASE):
                return True
        return False

    def is_time_date_query(self, query):
        time_patterns = [
            r"what(?:\'s| is)?\s+(?:the)?\s+time",
            r"what\s+time\s+is\s+it",
            r"what(?:\'s| is)?\s+(?:the)?\s+date",
            r"what(?:\'s| is)?\s+today(?:\'s)?\s+date",
            r"what\s+day\s+is\s+it",
            r"current\s+time",
            r"current\s+date",
        ]
        query_lower = query.lower()
        return any(re.search(pat, query_lower) for pat in time_patterns)

    def get_current_time_date(self, user_name):
        ny_timezone = pytz.timezone('America/New_York')
        now = datetime.now(ny_timezone)
        day = now.strftime("%A")
        date = now.strftime("%B %d, %Y")
        time = now.strftime("%I:%M %p")
        return f"@{user_name} It's currently {day}, {date} at {time} EST."

    def is_lookup_query(self, query):
        keywords = [
            "address", "phone", "contact", "location", "where is", "number", "call", "directions"
        ]
        query_lower = query.lower()
        return any(kw in query_lower for kw in keywords)

    def lookup_place(self, query: str):
        if not self.is_lookup_query(query):
            return None
        search_query = query.strip()
        try:
            url = "https://duckduckgo.com/html/"
            params = {"q": search_query}
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(url, params=params, headers=headers, timeout=8)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                text = soup.get_text(" ", strip=True)

                # ✅ Strict U.S. address format
                address_match = re.search(
                    r'(\d{1,5}\s[\w\s.,-]+?,\s*[A-Z][a-zA-Z\s]+,\s*[A-Z]{2}\s*\d{5})',
                    text
                )
                phone_match = re.search(
                    r'(\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{4})',
                    text
                )

                address = address_match.group(1) if address_match else "not found"
                phone = phone_match.group(1) if phone_match else "not found"

                return f"address: {address}, phone: {phone}"

            return "Sorry, I couldn't find a valid address or phone number for that place."
        except Exception as e:
            logging.error(f"Error in lookup_place: {e}")
            return "Sorry, I couldn't fetch that info right now."
