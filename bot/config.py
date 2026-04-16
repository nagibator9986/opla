from decouple import config

BOT_TOKEN = config("TELEGRAM_BOT_TOKEN")
API_BASE_URL = config("API_BASE_URL", default="http://web:8000/api/v1")
BOT_API_SECRET = config("BOT_API_SECRET", default="dev-bot-secret")
REDIS_URL = config("AIOGRAM_REDIS_URL", default="redis://redis:6379/1")
SITE_URL = config("SITE_URL", default="https://baqsy.kz")
