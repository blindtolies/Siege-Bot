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
        self.user_data = {}
        self.admins_per_chat = {}

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
        is_private = (update.effective_chat.type == "private")
        await update.message.reply_text(self.personality.get_start_message(user_name, is_private=is_private))
        await update.message.reply_text(self.personality.get_start_message(user_name))
        self._remember_user(update, user_name, update.message.chat_id)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
@@ -46,7 +45,6 @@
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        user_name = self._get_user_name(update)
        is_private = (update.effective_chat.type == "private")

        if update.effective_chat.type in ("group", "supergroup"):
            await self.update_admins(chat_id, context)
@@ -55,13 +53,13 @@
        self._remember_user(update, user_name, chat_id, is_admin)
        self._learn_from_conversation(user_id, update.message.text)

        # FIRST: Check for element queries or company number queries
        direct_reply = self.personality.direct_reply(update.message.text, user_name)
        if direct_reply is not None:
            await update.message.reply_text(direct_reply)
            return

        prompt = self.personality.create_prompt(update.message.text, user_name, is_private=is_private)
        # For everything else, send the prompt to the LLM and reply with its output
        prompt = self.personality.create_prompt(update.message.text, user_name)
        response = await asyncio.to_thread(
            self.cohere_client.generate,
            model='command',
@@ -71,34 +69,34 @@
            stop_sequences=["\n\n", "Human:", "User:"]
        )
        generated_text = response.generations[0].text.strip()
        final_response = self.personality.post_process_response(generated_text, user_name, is_private=is_private)
        final_response = self.personality.post_process_response(generated_text, user_name)
        await update.message.reply_text(final_response)

    def _get_user_name(self, update: Update):
        return update.effective_user.username or update.effective_user.first_name or "stranger"

    async def update_admins(self, chat_id, context):
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
        history = self.user_data[user_id]["history"]
        history.append(message)
        if len(history) > 10:
            self.user_data[user_id]["history"] = history[-10:]
