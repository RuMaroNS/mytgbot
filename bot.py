import os
import random
import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from g4f.client import Client

# Переменная с Bothost
TOKEN = os.getenv("BOT_TOKEN")
client = Client()

logging.basicConfig(level=logging.INFO)

async def get_ai_response(user_text, mood):
    """Генерация ответа через ИИ"""
    if mood == "evil":
        prompt = f"Ты — токсичный зумер по имени Бабон. Тебе написали: '{user_text}'. Ответь максимально жестко, используй современный сленг (скуф, альтушка, ливни, кринж, мать жива?, и т.д.). Будь агрессивным и неадекватным. Отвечай коротко."
    else:
        prompt = f"Ты — добрый, но странный челик Бабон. Тебе написали: '{user_text}'. Ответь по-доброму, используя молодежный сленг. Будь на чилле и на расслабоне. Отвечай коротко."

    try:
        response = client.chat.completions.create(
            model="gpt-4o", # Или gpt-3.5-turbo
            messages=[{"role": "user", "content": prompt}],
        )
        return response.choices[0].message.content
    except Exception as e:
        return "Бабон временно в тильте, попробуй позже."

async def babon_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Игнорим личку
    if update.effective_chat.type == "private":
        return

    if not update.message or not update.message.text:
        return

    text = update.message.text.lower()
    
    # Условия срабатывания
    is_called = any(name in text for name in ["бабон", "бобон"])
    random_trigger = random.random() < 0.15 # 15% шанс влезть самому

    if is_called or random_trigger:
        # 70% шанс что он будет злым, 30% что добрым
        mood = "evil" if random.random() < 0.7 else "good"
        
        # Показываем, что Бабон "печатает..."
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        ai_answer = await get_ai_response(text, mood)
        await update.message.reply_text(ai_answer)

if __name__ == '__main__':
    if not TOKEN:
        print("ОШИБКА: Забыли про BOT_TOKEN")
    else:
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), babon_logic))
        
        print("Бабон готов выдавать базу...")
        app.run_polling()
        
