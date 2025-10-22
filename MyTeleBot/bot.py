import logging
import asyncio
from typing import Optional
import cohere
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from functools import lru_cache
from personality import SiegePersonality
from config import Config

logger = logging.getLogger(__name__)

class SiegeBot:
    def __init__(self):
        self.config = Config()
        self.personality = SiegePersonality()
        self.cohere_client = cohere.AsyncClient(self.config.cohere_api_key)  # Use async client
        self.bot_username = "@Siege_Chat_Bot"
        self.application = None
        # Use sets for faster lookups
        self.admins_cache = {}  # chat_id -> set of admin user_ids
        self.admin_cache_time = {}  # chat_id -> timestamp
        self.cache_duration = 300  # 5 minutes

    async def start(self):
        """Initialize and start the bot"""
        self.application = Application.builder().token(self.config.telegram_token).build()
        
        # Register handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        
        logger.info("Starting Siege Bot...")
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        await asyncio.Event().wait()

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_name = self._get_user_name(update)
        await update.message.reply_text(self.personality.get_start_message(user_name))

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        await update.message.reply_text(self.personality.get_help_message())

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Main message handler with optimized flow"""
        if not update.message or not update.message.text:
            return

        user_name = self._get_user_name(update)
        message_text = update.message.text

        # Check direct replies first (fastest path)
        direct_reply = self.personality.direct_reply(message_text, user_name)
        if direct_reply:
            await update.message.reply_text(direct_reply)
            return

        # Generate AI response
        try:
            response = await self._generate_ai_response(message_text, user_name)
            await update.message.reply_text(response)
        except Exception as e:
            logger.error(f"Error generating response: {e}", exc_info=True)
            await update.message.reply_text(
                f"@{user_name} System hiccup. Try again in a moment."
            )

    async def _generate_ai_response(self, message_text: str, user_name: str) -> str:
        """Generate AI response using Cohere"""
        prompt = self.personality.create_prompt(message_text, user_name)
        
        # Use async client for better performance
        response = await self.cohere_client.generate(
            model='command',
            prompt=prompt,
            max_tokens=120,
            temperature=0.7,
            stop_sequences=["\n\n", "Human:", "User:"],
            return_likelihoods='NONE'
        )
        
        generated_text = response.generations[0].text.strip()
        return self.personality.post_process_response(generated_text, user_name)

    @staticmethod
    def _get_user_name(update: Update) -> str:
        """Extract user name from update"""
        user = update.effective_user
        return user.username or user.first_name or "stranger"

    async def _get_cached_admins(self, chat_id: int, context: ContextTypes.DEFAULT_TYPE) -> set:
        """Get admin list with caching to reduce API calls"""
        import time
        current_time = time.time()
        
        # Check if cache is valid
        if (chat_id in self.admins_cache and 
            chat_id in self.admin_cache_time and 
            current_time - self.admin_cache_time[chat_id] < self.cache_duration):
            return self.admins_cache[chat_id]
        
        # Fetch fresh admin list
        try:
            admins = await context.bot.get_chat_administrators(chat_id)
            self.admins_cache[chat_id] = {admin.user.id for admin in admins}
            self.admin_cache_time[chat_id] = current_time
            return self.admins_cache[chat_id]
        except Exception as e:
            logger.error(f"Failed to fetch admin list: {e}")
            return self.admins_cache.get(chat_id, set())
