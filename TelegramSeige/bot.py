import os
import telegram
import cohere

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
COHERE_API_KEY = os.environ.get("COHERE_API_KEY")

bot = telegram.Bot(token=TELEGRAM_TOKEN)
co = cohere.Client(COHERE_API_KEY)

# ...rest of your code...