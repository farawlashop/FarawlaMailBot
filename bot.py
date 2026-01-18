import logging
import requests
import random
import string
import time
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

# إعدادات البوت
TOKEN = "8536520622:AAGtyDYo-z97D8WSkEiQiPXVO7MDw1k6RN4"
API_URL = "https://api.mail.tm"

# إعداد التسجيل
logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
)

def generate_random_string(length=10):
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

async def get_domains():
        try:
                    response = requests.get(f"{API_URL}/domains")
                    if response.status_code == 200:
                                    domains = response.json().get('hydra:member', [])
                                    return [d['domain'] for d in domains if d['isActive']]
        except Exception as e:
                    logging.error(f"Error fetching domains: {e}")
                return []

async def create_account(address, password):
        try:
                    payload = {"address": address, "password": password}
                    response = requests.post(f"{API_URL}/accounts", json=payload)
                    return response.status_code == 201
except Exception as e:
        logging.error(f"Error creating account: {e}")
        return False

async def get_token(address, password):
        try:
                    payload = {"address": address, "password": password}
                    response = requests.post(f"{API_URL}/token", json=payload)
                    if response.status_code == 200:
                                    return response.json().get('token')
except Exception as e:
        logging.error(f"Error getting token: {e}")
    return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        welcome_text = (
            f"اهلا وسهلا بك بمنصة **Farawla Shop** 🍓\n\n"
            f"هذا البوت مخصص لإنشاء بريد إلكتروني مؤقت لاستقبال أكواد التحقق والرسائل بسرعة وسهولة.\n\n"
            f"إدارة وتصميم: **المهندس ناجي**\n"
            f"للتواصل: 0951232552\n\n"
            f"اضغط على الزر أدناه لإنشاء بريد جديد."
)

    keyboard = [[InlineKeyboardButton("Create Email 📧", callback_query_data='create_mail')]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    
