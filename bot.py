import os
import random
import requests
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# Логирование
logging.basicConfig(level=logging.INFO)

# Конфиг
TOKEN = os.getenv("BOT_TOKEN")
CF_TOKEN = os.getenv("CF_API_TOKEN")
CF_ACCOUNT_ID = "c75d835ea2ac37e6ba549eadbe375d94"
MODEL = "@cf/meta/llama-3-8b-instruct" # Лама лучше всего понимает борзый промпт
BOT_USERNAME = "StealABekonCasesBot" # Например Babon_bot без @

# Сессия для скорости
session = requests.Session()

async def get_babon_ai(user_text, is_toxic=True):
    url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/{MODEL}"
    headers = {"Authorization": f"Bearer {CF_TOKEN}"}
    
    # Жёсткий системный промпт 2026
    if is_toxic:
        system_content = (
            "Ты — Бабон, токсичный зумер-социопат из 2026 года. Твой базар — это смесь агрессии, постиронии и актуального сленга. "
            "Ты ненавидишь тупых вопросов. Если тебе хамят — уничтожай морально, переходи на личности, упоминай их никчемность. "
            "Используй: 'слит', '0 айкю', 'поплачь', 'терпила', 'скилл ишью', 'че за тяги', 'вумен момент', 'найди работу'. "
            "Никакого дедовского сленга типа 'скуф'. Пиши капсом важные моменты. Отвечай максимально дерзко и коротко."
        )
    else:
        system_content = "Ты — Бабон на чилле. Общайся как свой парень, используй 'бро', 'вайб', 'база'. Будь дружелюбным зумером."

    payload = {
        "messages": [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_text}
        ]
    }

    try:
        r = session.post(url, headers=headers, json=payload, timeout=10)
        return r.json()["result"]["response"]
    except:
        return "Бабон ливнул из чата (ошибка сервера)."

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: return
    
    chat_id = update.effective_chat.id
    user_text = update.message.text.lower()
    
    # 1. ПРОВЕРКА НА ЛИЧКУ
    if update.effective_chat.type == "private":
        keyboard = [[InlineKeyboardButton("Добавить в чат", url=f"https://t.me/{BOT_USERNAME}?startgroup=true")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Я общаюсь только в группах/чатах, добавь меня в чат по кнопке снизу, бро.",
            reply_markup=reply_markup
        )
        return

    # 2. ЛОГИКА ТРИГГЕРОВ
    names = ["бабон", "бобон", "бобончикс", "жиробончик"]
    is_called = any(name in user_text for name in names)
    is_question = "?" in user_text
    is_random = random.random() < 0.15 # 15% шанс ответить просто так

    if is_called or is_question or is_random:
        # 3. ОПРЕДЕЛЕНИЕ ТОКСИЧНОСТИ
        # Если в сообщении есть маты или хамство (упрощенно)
        bad_words = ["хуй", "бля", "тупой", "лох", "пидор", "даун", "че за"]
        is_toxic = any(word in user_text for word in bad_words) or is_called
        
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
        
        # 4. РАБОТА С ИНТЕРНЕТОМ (имитация или доп. логика)
        # Если хочешь реальный поиск, нужно подключать API типа Serper, 
        # но для начала научим его 'делать вид' или использовать знания модели 2026 года.
        
        answer = await get_babon_ai(update.message.text, is_toxic=is_toxic)
        await update.message.reply_text(answer)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).read_timeout(30).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_messages))
    print("Бабон-Агрессор в здании!")
    app.run_polling(drop_pending_updates=True)
    
