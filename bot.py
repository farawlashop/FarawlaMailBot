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
    user = update.effective_user
    welcome_text = (
        f"اهلا وسهلا بك بمنصة **Farawla Shop** 🍓\n\n"
        f"هذا البوت مخصص لإنشاء بريد إلكتروني مؤقت لاستقبال أكواد التحقق والرسائل بسرعة وسهولة.\n\n"
        f"إدارة وتصميم: **المهندس ناجي**\n"
        f"للتواصل: 0951232552\n\n"
        f"اضغط على الزر أدناه لإنشاء بريد جديد."
    )
    
    keyboard = [[InlineKeyboardButton("Create Mail 📧", callback_query_data='create_mail')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup, parse_mode='Markdown')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == 'create_mail':
        await query.edit_message_text("جاري إنشاء بريد إلكتروني جديد... ⏳")
        
        domains = await get_domains()
        if not domains:
            await query.edit_message_text("عذراً، فشل الاتصال بخدمة البريد حالياً. حاول مرة أخرى.")
            return
        
        domain = domains[0]
        username = generate_random_string(8)
        address = f"{username}@{domain}"
        password = generate_random_string(12)
        
        success = await create_account(address, password)
        if success:
            token = await get_token(address, password)
            if token:
                # حفظ البيانات في context المستخدم
                context.user_data['mail'] = address
                context.user_data['token'] = token
                
                mail_info = (
                    f"✅ تم إنشاء البريد بنجاح!\n\n"
                    f"📧 **البريد:** `{address}`\n"
                    f"🔑 **كلمة السر:** `{password}`\n\n"
                    f"سيتم تحديث الرسائل الواردة تلقائياً كل 10 ثوانٍ. يمكنك أيضاً الضغط على الزر أدناه للتحديث اليدوي."
                )
                keyboard = [[InlineKeyboardButton("Check Inbox 📥", callback_query_data='check_inbox')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(mail_info, reply_markup=reply_markup, parse_mode='Markdown')
                
                # بدء مهمة التحديث التلقائي
                asyncio.create_task(auto_refresh_inbox(query, context, address, token))
            else:
                await query.edit_message_text("فشل الحصول على رمز الدخول للبريد.")
        else:
            await query.edit_message_text("فشل إنشاء الحساب. حاول مرة أخرى.")

    elif query.data == 'check_inbox':
        address = context.user_data.get('mail')
        token = context.user_data.get('token')
        if not address or not token:
            await query.edit_message_text("انتهت صلاحية الجلسة. يرجى إنشاء بريد جديد.")
            return
        
        await check_inbox(query, address, token)

async def check_inbox(query, address, token):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(f"{API_URL}/messages", headers=headers)
        if response.status_code == 200:
            messages = response.json().get('hydra:member', [])
            if not messages:
                # لا نغير الرسالة إذا كانت فارغة لتجنب الإزعاج، فقط نحدث الوقت
                current_time = time.strftime("%H:%M:%S")
                text = (
                    f"📧 **البريد:** `{address}`\n\n"
                    f"📭 لا توجد رسائل جديدة حتى الآن.\n"
                    f"🔄 آخر تحديث: {current_time}"
                )
                keyboard = [[InlineKeyboardButton("Check Inbox 📥", callback_query_data='check_inbox')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                try:
                    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
                except:
                    pass # لتجنب خطأ "Message is not modified"
            else:
                msg_list = "📥 **الرسائل الواردة:**\n\n"
                for msg in messages[:5]: # عرض آخر 5 رسائل
                    msg_id = msg['id']
                    # جلب محتوى الرسالة
                    msg_detail = requests.get(f"{API_URL}/messages/{msg_id}", headers=headers).json()
                    subject = msg_detail.get('subject', 'بدون عنوان')
                    intro = msg_detail.get('intro', '')
                    msg_list += f"🔹 **من:** {msg['from']['address']}\n**العنوان:** {subject}\n**المحتوى:** {intro}\n---\n"
                
                keyboard = [[InlineKeyboardButton("Check Inbox 📥", callback_query_data='check_inbox')]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text(msg_list, reply_markup=reply_markup, parse_mode='Markdown')
    except Exception as e:
        logging.error(f"Error checking inbox: {e}")

async def auto_refresh_inbox(query, context, address, token):
    # تحديث تلقائي لمدة 10 دقائق
    for _ in range(60): 
        await asyncio.sleep(10)
        # التأكد من أن المستخدم لم يغير البريد
        if context.user_data.get('mail') != address:
            break
        await check_inbox(query, address, token)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    
    print("Bot is running...")
    app.run_polling()
