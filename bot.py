import os
import random
import requests
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# Настройка логов, чтобы видеть че происходит
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Грузим данные из Bothost
TOKEN = os.getenv("BOT_TOKEN")
CF_TOKEN = os.getenv("CF_API_TOKEN")
CF_ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")

# Модель из твоего личного кабинета Cloudflare
# Можно юзать '@cf/meta/llama-3-8b-instruct' или ту, что на скрине
MODEL = "openai/gpt-5.4-pro" 

async def get_babon_ai_logic(user_text, mood):
    url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/{MODEL}"
    headers = {"Authorization": f"Bearer {CF_TOKEN}"}
    
    if mood == "evil":
        system_prompt = (
            "Ты — Бабон, агрессивный зумер-хам. Твоя мать — шлюха. "
            "Используй сленг: скуф, альтушка, ливни, кринж, тюбик. "
            "Будь максимально токсичным, матерись, хами. Отвечай коротко (до 15 слов)."
        )
    else:
        system_prompt = (
            "Ты — добрый Бабон, бро на чилле. "
            "Используй сленг: чиназес, вайб, сигма, легенда. Отвечай коротко."
        )

    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text}
        ]
    }

    try:
        # Прямой запрос к твоим "мозгам" в Cloudflare
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        data = response.json()
        
        if data.get("success"):
            return data["result"]["response"]
        else:
            logging.error(f"Ошибка Cloudflare: {data}")
            raise Exception("CF_FAIL")
            
    except Exception as e:
        logging.error(f"Ошибка связи: {e}")
        # Если ИИ прилег, Бабон выдает базу из списка
        return random.choice([
            "Слышь, мои мозги в тильте, ливни нахер.",
            "Cloudflare поплавился от твоего кринжа, скуф.",
            "Я ща не в духе генерить, мать жива?",
            "Отвали, у меня сервак лег."
        ])

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Работаем только в группах
    if update.effective_chat.type == "private" or not update.message or not update.message.text:
        return

    text = update.message.text.lower()
    
    # Реагирует на имя или с шансом 20% на любое сообщение
    is_called = any(name in text for name in ["бабон", "бобон"])
    is_random = random.random() < 0.20 

    if is_called or is_random:
        # Настроение: 70% шанс, что он будет злым
        mood = "evil" if random.random() < 0.7 else "good"
        
        # Эффект "печатает..."
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        answer = await get_babon_ai_logic(update.message.text, mood)
        await update.message.reply_text(answer)

if __name__ == '__main__':
    if not all([TOKEN, CF_TOKEN, CF_ACCOUNT_ID]):
        print("ОШИБКА: Заполни все переменные (TOKEN, CF_API_TOKEN, CF_ACCOUNT_ID) на Bothost!")
    else:
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_messages))
        print("Бабон официально запущен на мозгах Cloudflare!")
        app.run_polling()
    
