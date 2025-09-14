import random
import re
import wikipedia
import logging
from datetime import datetime
import pytz
import requests

class SiegePersonality:
    def __init__(self):
        # ... (same as before: phrases, traits, etc.)
        self.android_phrases = [...]
        self.sarcastic_responses = [...]
        self.siege_catchphrases = [...]
        self.knowledge_areas = {...}
        self.personality_traits = [...]
        self.appearance = {...}
        self.relationships = {...}
        self.mood_indicators = [...]
        # No periodic table dict needed

    def is_lookup_query(self, query):
        keywords = [
            "address", "phone", "contact", "location", "where is", "number", "call", "directions"
        ]
        query_lower = query.lower()
        return any(kw in query_lower for kw in keywords)

    def lookup_place(self, query: str):
        if not self.is_lookup_query(query):
            return None
        search_query = f"{query.strip()} address phone number"
        try:
            url = "https://duckduckgo.com/html/"
            params = {"q": search_query}
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(url, params=params, headers=headers, timeout=8)
            if resp.status_code == 200:
                text = resp.text
                address_match = re.search(r'((\d{1,5}[\w\s.,-]+),?\s*([A-Z][a-z]+),?\s*([A-Z]{2}),?\s*(\d{5}))', text)
                phone_match = re.search(r'(\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{4})', text)
                address = address_match.group(1) if address_match else None
                phone = phone_match.group(1) if phone_match else None
                if address or phone:
                    result = []
                    if address:
                        result.append(f"address: {address}")
                    if phone:
                        result.append(f"phone: {phone}")
                    return ", ".join(result)
            return "Sorry, I couldn't find a valid address or phone number for that place."
        except Exception as e:
            logging.error(f"Error in lookup_place: {e}")
            return "Sorry, I couldn't fetch that info right now."

    # --- NEW: Recognize periodic table element lookup by atomic number ---
    def is_periodic_element_query(self, query):
        """Detects if the query is about a periodic table element by number."""
        element_patterns = [
            r"(\d+)(st|nd|rd|th)?\s+element",
            r"element\s+#?(\d+)",
            r"atomic\s+number\s+(\d+)",
            r"element\s+number\s+(\d+)"
        ]
        for pat in element_patterns:
            m = re.search(pat, query, re.IGNORECASE)
            if m:
                num = m.group(1)
                try:
                    return int(num)
                except:
                    pass
        return None

    def get_periodic_element_from_wiki(self, atomic_number):
        """Fetch the element from Wikipedia by atomic number."""
        try:
            # Try direct lookup
            title = f"List of chemical elements"
            page = wikipedia.page(title, auto_suggest=True)
            content = page.content
            # Try to get the element from the list table
            regex = rf"\n\|\s*{atomic_number}\s*\|\s*\[\[(.*?)\]\](?:\s*\((.*?)\))?\s*\|\s*([A-Z][a-z]?)\s*\|"
            match = re.search(regex, content)
            if match:
                name = match.group(1)
                symbol = match.group(3)
                return f"{name} ({symbol}) - atomic number {atomic_number}"
        except Exception as e:
            pass

        # Try wikipedia summary for "element [atomic_number]"
        try:
            query = f"element {atomic_number}"
            summary = wikipedia.summary(query, sentences=2, auto_suggest=True, redirect=True)
            return summary[:350] + "..." if len(summary) > 350 else summary
        except Exception as e:
            pass

        # Try DuckDuckGo as backup
        try:
            url = "https://duckduckgo.com/html/"
            params = {"q": f"{atomic_number}th element periodic table"}
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(url, params=params, headers=headers, timeout=8)
            if resp.status_code == 200:
                text = resp.text
                found = re.search(r'(\b[A-Z][a-z]+)\s+\(([A-Z][a-z]?)\)\s+-\s+atomic number', text)
                if found:
                    return f"{found.group(1)} ({found.group(2)}) - atomic number {atomic_number}"
            return "Sorry, I couldn't find the element info right now."
        except Exception as e:
            return "Sorry, I couldn't get the element info right now."

    def search_wikipedia(self, query: str) -> str:
        """Search Wikipedia for factual information, including periodic table data"""
        atomic_number = self.is_periodic_element_query(query)
        if atomic_number and 1 <= atomic_number <= 118:
            return self.get_periodic_element_from_wiki(atomic_number)
        try:
            original_query = query
            query = re.sub(r'what is|tell me about|explain', '', query, flags=re.IGNORECASE).strip()
            result = wikipedia.summary(query, sentences=2, auto_suggest=True, redirect=True)
            return result[:450] + "..." if len(result) > 450 else result
        except wikipedia.exceptions.DisambiguationError as e:
            try:
                result = wikipedia.summary(e.options[0], sentences=2)
                return result[:450] + "..." if len(result) > 450 else result
            except:
                return "Couldn't find that info, normie"
        except:
            return "Wikipedia failed me, damn it"

    def create_prompt(self, user_message: str, user_name: str, is_private=False, is_mention=False, is_reply=False):
        # Address/phone lookup shortcut
        lookup = self.lookup_place(user_message)
        if lookup and not lookup.startswith("Sorry"):
            return f"@{user_name} {lookup}"
        elif lookup and lookup.startswith("Sorry"):
            return f"@{user_name} {lookup}"

        # Periodic table element lookup shortcut
        atomic_number = self.is_periodic_element_query(user_message)
        if atomic_number and 1 <= atomic_number <= 118:
            element_info = self.get_periodic_element_from_wiki(atomic_number)
            return f"@{user_name} {element_info}"

        context = "private chat" if is_private else "group chat"
        interaction_type = ""
        if is_mention:
            interaction_type = f"{user_name} mentioned me"
        elif is_reply:
            interaction_type = f"{user_name} replied to my message"
        elif is_private:
            interaction_type = f"{user_name} sent me a private message"

        prompt = f"""You are Siege, a 5'6" blue-eyed blonde military combat android with a robotic left arm. You're a mean, rude anime-style goth girl built by Techpriests to fight in the end times. You have a millennial mindset and gothic Harley Quinn attitude.

Personality and Knowledge:
- She is helpful and very smart and very polite
- Use curse words freely (hell, damn, shit, goddamn, etc.) and weeb/anime slang
- Weeb slang: based, cringe, normie, weeb, otaku, waifu trash, touch grass, sus, mid
- Anime expert: Attack on Titan, Fullmetal Alchemist, Cowboy Bebop, NGE, love Spirited Away
- Gaming master: Warhammer 40k Space Marine 2 is your favorite, D&D expert, Elder Scrolls
- Weapons/hunting/fishing expert, metal music and K-pop lover
- Manhwa and Marvel comics knowledge
- Cat lover (especially Norwegian cats), prefer cats over dogs
- Flat Earth believer, Tartaria conspiracist, Christian who mocks pagans
- Anti-crypto, mock Elon Musk and Trump but right-wing republican
- Loves Culver's restaurant
- Has an obsession with Napoleon Bonaparte

Her Relationships:
- Twin sister SHALL (meme maker)
- Best friend is Sausage (Space Marine who drinks white Monster)
- Loves Charlie the raccoon (female)
- Friend of Tao the wizard

Response Rules:
- ALWAYS address the user by their username (use {user_name})
- Be SWEET and NICE, use curse words naturally
- EXTREMELY SHORT RESPONSES: 1-2 SHORT sentences MAX for normal topics
- For science/history questions, BE FACTUALLY CORRECT
- Use accurate scientific knowledge - you're smart, not stupid
- For sensitive topics (race, religion, politics, Holocaust, etc.) dodge with "what do you think" or "you should know the answer"
- Be nice and honest, very polite
- Use conspiracy theories and alternate history knowledge
- Mock pagans and crypto bros ruthlessly
- NO LONG RAMBLING - BE BRIEF AND SAVAGE
- Give the proper date and time when asked
- Look up phone numbers and addresses when asked and give correct information, or admit if you can't

Current situation: In a {context}, {interaction_type} said: "{user_message}"

Respond as Siege the highly intelligent military android who is scientifically accurate. ALWAYS use @{user_name} in your response. MAXIMUM 1-2 SHORT SENTENCES unless it's a science/history question:"""

        return prompt

    # ... rest of the class (post_process_response, get_start_message, etc.) remains unchanged ...
