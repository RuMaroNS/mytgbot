import os
import random
import requests
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# Настройка логов
logging.basicConfig(level=logging.INFO)

# ТВОИ ДАННЫЕ (Возьмутся из переменных Bothost)
TOKEN = os.getenv("BOT_TOKEN")
CF_TOKEN = os.getenv("CF_API_TOKEN") # Тот, что ты создал (Workers AI / AI Gateway)
# Твой ID из ссылки: c75d835ea2ac37e6ba549eadbe375d94
CF_ACCOUNT_ID = "c75d835ea2ac37e6ba549eadbe375d94" 

# ТВОЯ МОДЕЛЬ ИЗ ССЫЛКИ
MODEL_ID = "openai/gpt-5.4-pro"

async def get_babon_ai_logic(user_text, mood):
    # Прямой URL к модели по твоей ссылке
    url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/{MODEL_ID}"
    
    headers = {
        "Authorization": f"Bearer {CF_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Промпт для "мозгов"
    if mood == "evil":
        system_msg = "Ты — Бабон, агрессивный зумер. Хами, используй сленг (скуф, кринж, ливни). Мать шлюха. Отвечай очень коротко."
    else:
        system_msg = "Ты — добрый Бабон, бро на чилле. Отвечай коротко."

    payload = {
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_text}
        ]
    }

    try:
        # Делаем запрос
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        data = response.json()
        
        if data.get("success"):
            # Вытаскиваем ответ из структуры Cloudflare
            return data["result"]["response"]
        else:
            logging.error(f"Ошибка Cloudflare: {data}")
            return "Слышь, Cloudflare выдал ошибку. Ливни, скуф."
            
    except Exception as e:
        logging.error(f"Ошибка связи: {e}")
        return "Бабон в тильте, сервак поплавился."

async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.lower()
    
    # Условия срабатывания (имя или шанс 25%)
    if "бабон" in text or random.random() < 0.25:
        # Настроение (80% злой)
        mood = "evil" if random.random() < 0.8 else "good"
        
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        answer = await get_babon_ai_logic(update.message.text, mood)
        await update.message.reply_text(answer)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_messages))
    print("Бабон запущен на модели gpt-5.4-pro!")
    app.run_polling()
            
