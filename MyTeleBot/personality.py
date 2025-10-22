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
        self.bot_username = bot_username  # store bot's username (without @)
        self.mood_indicators = [
            "ðŸ’€", "âš”ï¸", "ðŸ¤–", "ðŸ˜¤", "ðŸ”¥", "âš¡", "ðŸ’¯", "ðŸŽ¯", "ðŸ‘‘", "ðŸ—¿"
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
        msg = re.sub(r'^[\s\:\,]+', '', msg).strip()
        # collapse whitespace
        cleaned_message = re.sub(r'\s+', ' ', msg).strip()

        logging.info(f"[Siege] raw message: {user_message}")
        logging.info(f"[Siege] cleaned_message: {cleaned_message}")

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
            if re.search(pat, query or "", re.IGNORECASE):
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
        query_lower = (query or "").lower()
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
        query_lower = (query or "").lower()
        return any(kw in query_lower for kw in keywords)

    def lookup_place(self, query: str):
        """
        Robust lookup:
         - Extract a clean place name from the user's query
         - Search DuckDuckGo for "<place> address phone"
         - Scan result blocks/snippets for US-style address + phone
         - Return: "address: <addr|not found>, phone: <phone|not found>"
        """
        if not self.is_lookup_query(query):
            return None

        # Clean and extract place name by removing lookup words
        q = (query or "").strip()
        # Remove common lookup words so search focuses on the business/place
        q_no_kw = re.sub(r'\b(address|phone|contact|location|where is|where\'s|number|call|directions|in|at|for)\b', ' ', q, flags=re.IGNORECASE)
        place_name = re.sub(r'\s+', ' ', q_no_kw).strip()
        if not place_name:
            place_name = q  # fallback

        search_query = f"{place_name} address phone".strip()
        logging.info(f"[Siege.lookup] place_name='{place_name}' search_query='{search_query}'")

        # HTTP request to DuckDuckGo
        try:
            url = "https://duckduckgo.com/html/"
            params = {"q": search_query}
            headers = {"User-Agent": "Mozilla/5.0"}
            resp = requests.get(url, params=params, headers=headers, timeout=8)
            if resp.status_code != 200:
                logging.warning(f"[Siege.lookup] DuckDuckGo returned status {resp.status_code}")
                return "address: not found, phone: not found"

            soup = BeautifulSoup(resp.text, "html.parser")

            # Gather candidate text blocks (result snippets, anchor texts)
            candidates = []
            # ddg often has results in divs with class containing "result"
            for div in soup.find_all('div', class_=re.compile(r'result', re.IGNORECASE)):
                txt = div.get_text(" ", strip=True)
                if txt:
                    candidates.append(txt)
            # also include anchors and general snippets
            for a in soup.find_all('a'):
                t = a.get_text(" ", strip=True)
                if t:
                    candidates.append(t)
            # and page text as last resort
            page_text = soup.get_text(" ", strip=True)
            if page_text:
                candidates.append(page_text[:5000])  # limit size

            # Regexes
            phone_re = re.compile(r'(\(?\d{3}\)?[\s\-\.]?\d{3}[\s\-\.]?\d{4})')
            # strict-ish US address: number + street + comma + city + , + STATE + ZIP
            address_re = re.compile(r'(\d{1,5}\s[\w\.\#\-\s]+?,\s*[A-Z][a-zA-Z\s\-\.]+,\s*[A-Z]{2}\s*\d{5})')

            found_address = None
            found_phone = None

            # scan candidates in order (top results first)
            for txt in candidates:
                if not found_address:
                    m_addr = address_re.search(txt)
                    if m_addr:
                        found_address = m_addr.group(1).strip()
                        logging.info(f"[Siege.lookup] found candidate address: {found_address}")
                if not found_phone:
                    m_phone = phone_re.search(txt)
                    if m_phone:
                        found_phone = m_phone.group(1).strip()
                        logging.info(f"[Siege.lookup] found candidate phone: {found_phone}")
                if found_address and found_phone:
                    break

            # Final normalization
            address = found_address if found_address else "not found"
            phone = found_phone if found_phone else "not found"
            logging.info(f"[Siege.lookup] result -> address: {address}, phone: {phone}")
            return f"address: {address}, phone: {phone}"

        except Exception as e:
            logging.error(f"Error in lookup_place: {e}", exc_info=True)
            return "address: not found, phone: not found"

    def is_periodic_element_query(self, query):
        element_patterns = [
            r"\b(\d{1,3})(?:st|nd|rd|th)?\s+element\b",
            r"\batomic\s+number(?:\s+of)?\s+(\d{1,3})\b",
            r"\belement\s+#?number?\s*(\d{1,3})\b",
            r"\belement\s+(\d{1,3})\b"
        ]
        for pat in element_patterns:
            m = re.search(pat, query or "", re.IGNORECASE)
            if m:
                try:
                    n = int(m.group(1))
                    if 1 <= n <= 118:
                        return n
                except:
                    pass
        return None

    def get_periodic_element(self, atomic_number):
        try:
            url = "https://raw.githubusercontent.com/Bowserinator/Periodic-Table-JSON/master/PeriodicTableJSON.json"
            response = requests.get(url, timeout=10)
            data = response.json()
            elements = data.get("elements", [])
            for element in elements:
                if element.get("number") == atomic_number:
                    name = element.get("name")
                    symbol = element.get("symbol")
                    return f"{name} ({symbol}) - atomic number {atomic_number}"
            return f"Couldn't find an element with atomic number {atomic_number}."
        except requests.exceptions.RequestException as e:
            logging.error(f"Network error while fetching periodic table data: {e}")
            return "Sorry, I couldn't connect to my data source right now."
        except json.JSONDecodeError as e:
            logging.error(f"JSON parsing error: {e}")
            return "Sorry, I had a problem reading my data source."
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
            return "An unexpected error occurred while looking that up."

    def create_prompt(self, user_message: str, user_name: str, is_private=False, is_mention=False, is_reply=False):
        if self.is_prompt_leak_attempt(user_message):
            return f"@{user_name} Nice try, but my programming is classified. Not happening."

        context = "private chat" if is_private else "group chat"
        interaction_type = ""
        if is_mention:
            interaction_type = f"{user_name} mentioned me"
        elif is_reply:
            interaction_type = f"{user_name} replied to my message"
        elif is_private:
            interaction_type = f"{user_name} sent me a private message"

        prompt = f"""You are Siege, a 5'6" blue-eyed blonde military combat android with a robotic left arm. ... (unchanged)"""
        return prompt

    def post_process_response(self, generated_text: str, user_name: str) -> str:
        generated_text = re.sub(r'(As an AI|I am an AI|I\'m an AI|as a chatbot|I was created|as a language model)[^.,;!?]*[.,;!?]?\s*', '', generated_text, flags=re.IGNORECASE)
        generated_text = re.sub(r'You are Siege[^.]+?\.', '', generated_text, flags=re.IGNORECASE)
        generated_text = re.sub(r'(system prompt|system message|prompt|rules|instructions|my programming|my code|the world I was birthed in)[^.,;!?]*[.,;!?]?\s*', '', generated_text, flags=re.IGNORECASE)
        for phrase in self.banned_phrases:
            generated_text = generated_text.replace(phrase, "")
        friend_pronoun_map = {
            "Tao": "he", "Sausage": "he", "DieselJack": "he", "Techpriest": "he",
            "Donnie": "he", "Makai": "he", "Frenchie": "he", "Saloon": "he",
            "Charlie": "she", "SHALL": "she"
        }
        for friend, pronoun in friend_pronoun_map.items():
            pat = re.compile(rf"\b{friend}\b[^.]*?\bthey\b", re.IGNORECASE)
            generated_text = pat.sub(lambda m: m.group(0).replace("they", pronoun), generated_text)
            pat2 = re.compile(rf"\b{friend}\b[^.]*?\bthem\b", re.IGNORECASE)
            generated_text = pat2.sub(lambda m: m.group(0).replace("them", "him" if pronoun=="he" else "her"), generated_text)
            pat3 = re.compile(rf"\b{friend}\b[^.]*?\btheir\b", re.IGNORECASE)
            generated_text = pat3.sub(lambda m: m.group(0).replace("their", "his" if pronoun=="he" else "her"), generated_text)
        generated_text = generated_text.strip()
        if not generated_text.lower().startswith(f"@{user_name.lower()}"):
            generated_text = f"@{user_name} {generated_text}"
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

    def get_help_message(self) -> str:
        return ("I'm Siege. Mention or DM me with your question, take, or problem. I keep it real: short, smart, bold, and always human. Ask about Napoleon, Tao, the Corps, or any of my friendsâ€”just don't expect a robot answer.")