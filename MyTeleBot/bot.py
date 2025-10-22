import logging
import asyncio
import cohere
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from personality import SiegePersonality
from config import Config

logger = logging.getLogger(__name__)

class SiegeBot:
    def __init__(self):
        self.config = Config()
        self.personality = SiegePersonality()
        self.cohere_client = cohere.Client(self.config.cohere_api_key)
        self.cohere_client = cohere.ClientV2(self.config.cohere_api_key)
        self.application = None
        self.bot_username = "@Siege_Chat_Bot"

@@ -145,7 +145,7 @@
        return (has_question and has_topic) or has_periodic_table_format

    async def generate_response(self, user_message: str, user_name: str, is_private=False, is_mention=False, is_reply=False):
        """Generate AI response using Cohere API"""
        """Generate AI response using Cohere Chat API"""
        try:
            # Check if this is a science/history question
            wiki_info = ""
@@ -155,30 +155,38 @@
                    wiki_info = f"\n\nWikipedia info: {wiki_result}"

            # Create context-aware prompt
            prompt = self.personality.create_prompt(
            system_prompt = self.personality.create_prompt(
                user_message + wiki_info, 
                user_name, 
                is_private=is_private, 
                is_mention=is_mention, 
                is_reply=is_reply
            )

            # Generate response with Cohere
            response = self.cohere_client.generate(
                model='command',
                prompt=prompt,
                max_tokens=100,
            # Generate response with Cohere Chat API
            response = self.cohere_client.chat(
                model='command-r-08-2024',
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_message + wiki_info
                    }
                ],
                max_tokens=150,
                temperature=0.8,
                stop_sequences=["\n\n", "Human:", "User:"]
            )

            generated_text = response.generations[0].text.strip()
            generated_text = response.message.content[0].text.strip()

            # Post-process the response to ensure it fits Harley's personality
            final_response = self.personality.post_process_response(generated_text)

            return final_response

        except Exception as e:
            logger.error(f"Error generating response with Cohere: {e}")
            return self.personality.get_fallback_response()
