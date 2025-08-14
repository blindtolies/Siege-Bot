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
        self.bot_username = "@Siege_Chat_Bot"
        self.application = None

        # In-memory state
        self.user_data = {}         # user_id: {"username": ..., "is_admin": bool, "history": [..]}
        self.admins_per_chat = {}   # chat_id: set([admin_user_ids])

    async def start(self):
        token = self.config.telegram_token
        self.application = Application.builder().token(token).build()
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(MessageHandler(filters.ALL, self.handle_message))
        logger.info("Starting Siege Bot...")
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        await asyncio.Event().wait()

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_name = self._get_user_name(update)
        await update.message.reply_text(self.personality.get_start_message())
        self._remember_user(update, user_name, update.message.chat_id)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(self.personality.get_help_message())

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message or not update.message.text:
            return

        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        user_name = self._get_user_name(update)

        # Update admin list for this group if group chat
        if update.effective_chat.type in ("group", "supergroup"):
            await self.update_admins(chat_id, context)

        # Remember and learn from this user
        is_admin = self.is_admin(chat_id, user_id)
        self._remember_user(update, user_name, chat_id, is_admin)
        self._learn_from_conversation(user_id, update.message.text)

        # Generate and send response
        response = await self.generate_response(update.message.text, user_name)
        await update.message.reply_text(response)

    def _get_user_name(self, update: Update):
        return update.effective_user.username or update.effective_user.first_name or "stranger"

    async def update_admins(self, chat_id, context):
        # Only call this occasionally or on new members to avoid API spam
        try:
            admins = await context.bot.get_chat_administrators(chat_id)
            self.admins_per_chat[chat_id] = set(admin.user.id for admin in admins)
        except Exception as e:
            logger.error(f"Failed to fetch admin list: {e}")

    def is_admin(self, chat_id, user_id):
        return user_id in self.admins_per_chat.get(chat_id, set())

    def _remember_user(self, update, user_name, chat_id, is_admin=False):
        user_id = update.effective_user.id
        if user_id not in self.user_data:
            self.user_data[user_id] = {
                "username": user_name,
                "is_admin": is_admin,
                "history": []
            }
        self.user_data[user_id]["is_admin"] = is_admin

    def _learn_from_conversation(self, user_id, message):
        # Naive: store last 10 messages per user
        history = self.user_data[user_id]["history"]
        history.append(message)
        if len(history) > 10:
            self.user_data[user_id]["history"] = history[-10:]

    async def generate_response(self, user_message, user_name):
        # You could use the user's history here to improve the prompt
        prompt = self.personality.create_prompt(user_message, user_name)
        response = await asyncio.to_thread(
            self.cohere_client.generate,
            model='command',
            prompt=prompt,
            max_tokens=100,
            temperature=0.8,
            stop_sequences=["\n\n", "Human:", "User:"]
        )
        generated_text = response.generations[0].text.strip()
        final_response = self.personality.post_process_response(generated_text)
        return final_response
