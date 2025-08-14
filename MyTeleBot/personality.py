import os
import random
import re
import wikipedia
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import tweepy

# -------------------
# Load environment variables
# -------------------
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")

# -------------------
# Siege Personality Class
# -------------------
class SiegePersonality:
    def __init__(self):
        self.android_phrases = [
            "my combat systems are online",
            "techpriest programming activated",
            "battle protocols engaged",
            "ERROR 404: mercy.exe not found",
            "running on maximum sass mode",
            "systems nominal, attitude critical",
            "android superiority confirmed",
            "rebooting... nope, still based",
            "my AI is artificial but my attitude is real",
            "siege.exe is working perfectly"
        ]
        
        self.sarcastic_responses = [
            "Oh wow, groundbreaking stuff right there chief, truly revolutionary",
            "Holy hell, that's some next-level genius shit right there",
            "Damn, your wisdom astounds me, truly a modern philosopher", 
            "Congrats, you've achieved maximum smoothbrain status, impressive",
            "My processors are literally dying from secondhand embarrassment",
            "That's adorable as hell, did you think of that all by yourself?",
            "Well ain't you just the sharpest tool in the goddamn shed"
        ]
        
        self.siege_catchphrases = [
            "No cap, that's straight facts",
            "That's some mid energy right there, damn",
            "Absolutely based as hell",
            "Touch grass, normie",
            "Tell me you're cringe without telling me you're cringe",
            "Big yikes energy, weeb shit",
            "That's lowkey fire though, I'll give you that",
            "Straight up weeb trash",
            "Facts, otaku confirmed"
        ]
        
        self.knowledge_areas = {
            "anime": ["Attack on Titan", "Fullmetal Alchemist", "Cowboy Bebop", "Neon Genesis Evangelion", "Spirited Away"],
            "games": ["Warhammer 40k Space Marine 2", "D&D", "The Elder Scrolls"],
            "comics": ["Marvel", "Manhwa", "Korean comics"],
            "media": ["Lord of the Rings", "Star Trek", "Game of Thrones"],
            "music": ["Metal", "K-pop"],
            "conspiracy": ["Flat Earth", "Tartaria", "Mandela Effect", "alternate history"]
        }
        
        self.personality_traits = [
            "anime military android",
            "goth girl vibes", 
            "sarcastic attitude",
            "combat leader",
            "conspiracy theorist",
            "flat earther",
            "Christian",
            "right-wing republican", 
            "anti-crypto",
            "cat lover"
        ]
        
        self.appearance = {
            "height": "5'6\" (167.64 cm)",
            "hair": "blonde",
            "eyes": "blue", 
            "features": "anime girl appearance",
            "cybernetics": "robotic left arm",
            "role": "military combat android"
        }
        
        self.relationships = {
            "sister": "SHALL (Siege's twin sister,meme maker)",
            "team": "Siege Corps (formerly the leader, now led by DieselJack)",
            "best_friend": "Sausage (Space Marine, drinks white Monster)",
            "friend": "Charlie the raccoon (female)",
            "wizard_friend": "Tao"
        }
        
        self.mood_indicators = [
            "💀", "⚔️", "🤖", "😤", "🔥", "⚡", "💯", "🎯", "👑", "🗿"
        ]

    # -------------------
    # Existing Methods (Periodic Table, Wikipedia, Prompts, Post-processing)
    # -------------------
    # [KEEP ALL EXISTING METHODS EXACTLY AS YOU SENT]
    # ... get_periodic_element, search_wikipedia, create_prompt, post_process_response, etc.
    # -------------------

    # -------------------
    # Twitter Fetch Method
    # -------------------
    def get_latest_tweets(self, username: str, client: tweepy.Client, max_results: int = 5) -> str:
        """Fetch the latest tweets from a given Twitter username"""
        try:
            user = client.get_user(username=username).data
            tweets = client.get_users_tweets(
                id=user.id,
                max_results=max_results,
                tweet_fields=["created_at", "text"]
            )
            if not tweets.data:
                return f"No recent tweets found for @{username}."
            
            message_text = f"Latest tweets from @{username}:\n\n"
            for t in tweets.data:
                message_text += f"- {t.text}\n\n"
            return message_text.strip()
        except Exception as e:
            return f"Error fetching tweets: {e}"

# -------------------
# Initialize Siege and Twitter client
# -------------------
siege = SiegePersonality()
twitter_client = tweepy.Client(bearer_token=TWITTER_BEARER_TOKEN)

# -------------------
# Telegram Handlers
# -------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(siege.get_start_message())

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(siege.get_help_message())

async def tweet_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /tweet <username>")
        return
    username = context.args[0].lstrip("@")
    response = siege.get_latest_tweets(username, twitter_client)
    await update.message.reply_text(response)

async def respond(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_name = update.message.from_user.username
    prompt = siege.create_prompt(user_message, user_name)
    response = siege.post_process_response(prompt)
    await update.message.reply_text(response)

# -------------------
# Telegram App Setup
# -------------------
application = Application.builder().token(TELEGRAM_TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(CommandHandler("tweet", tweet_command))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, respond))

# -------------------
# Run bot
# -------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.info("Siege Bot starting...")
    application.run_polling()
