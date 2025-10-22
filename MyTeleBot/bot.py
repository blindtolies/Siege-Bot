import logging
import asyncio
import cohere
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from personality import SiegePersonality
from config import Config
from datetime import datetime, timedelta

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
        # New: Store history parameters
        self.history_duration = timedelta(days=self.config.history_duration_days)
        self.history_max_messages = self.config.history_max_messages

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
        await update.message.reply_text(self.personality.get_start_message(user_name))
        self._remember_user(update, user_name, update.message.chat_id)

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("My purpose is to serve, but don't get used to it. Ask me a question or tell me a command.")
        self._remember_user(update, self._get_user_name(update), update.message.chat_id)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.message is None or update.effective_user is None:
            return

        chat_id = update.message.chat_id
        user_id = update.effective_user.id
        user_name = self._get_user_name(update)

        # Update admin list (important for group chats)
        if update.message.chat.type != 'private':
            await self.update_admins(chat_id, context)

        is_admin = self.is_admin(chat_id, user_id)
        
        # 1. Remember/update user data and admin status
        self._remember_user(update, user_name, chat_id, is_admin)
        
        # 2. Add message to history
        if update.message.text:
            self._learn_from_conversation(user_id, update.message.text)
        
        # 3. Check for direct/instant sassy replies (bypasses LLM)
        direct_response = self.personality.direct_reply(update.message.text, user_name)
        if direct_response:
            await update.message.reply_text(direct_response)
            return

        # 4. Determine if the bot should use the LLM
        is_private = update.message.chat.type == 'private'
        is_mention = self.bot_username.lower() in update.message.text.lower() if update.message.text else False
        is_reply = update.message.reply_to_message and update.message.reply_to_message.from_user.id == context.bot.id

        if not is_private and not is_mention and not is_reply:
            # Not a private message, not a mention, and not a reply - ignore in group chats
            return

        # 5. Build prompt and generate response
        try:
            user_data = self.user_data.get(user_id, {})
            # Pass the history and admin status to the personality module
            prompt = self.personality.create_prompt(
                user_message=update.message.text, 
                user_name=user_name,
                is_admin=is_admin, # New: Pass admin status
                history=user_data.get("history", []) # History now contains dicts with timestamps
            )
            
            response = self.cohere_client.generate(
                model='command', # or command-r
                prompt=prompt,
                max_tokens=120,
                temperature=0.7,
                stop_sequences=["\n\n", "Human:", "User:"]
            )
            generated_text = response.generations[0].text.strip()
            final_response = self.personality.post_process_response(generated_text, user_name)
            await update.message.reply_text(final_response)

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await update.message.reply_text(f"@{user_name} Error in core systems. Try again.")


    def _learn_from_conversation(self, user_id, message):
        """
        Stores the message with a timestamp and cleans old messages based on time and count limits.
        """
        # Store message with a timestamp
        new_entry = {
            "timestamp": datetime.now(),
            "message": message
        }
        
        history = self.user_data[user_id]["history"]
        history.append(new_entry)
        
        # 1. Time-based cleanup
        threshold_time = datetime.now() - self.history_duration
        
        # Filter the history list to keep only entries newer than the threshold
        self.user_data[user_id]["history"] = [
            entry for entry in history 
            if entry["timestamp"] >= threshold_time
        ]

        # 2. Message count safety cleanup (if history is still too long after time cleanup)
        current_history = self.user_data[user_id]["history"]
        if len(current_history) > self.history_max_messages:
            self.user_data[user_id]["history"] = current_history[-self.history_max_messages:]
            logger.warning(f"User {user_id} history truncated by count limit.")


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
                "history": [] # History stores dicts with message and timestamp
            }
        self.user_data[user_id]["is_admin"] = is_admin
        # Always update username in case they change it
        self.user_data[user_id]["username"] = user_name
