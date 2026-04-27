import os
import random
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from huggingface_hub import InferenceClient

# Берем данные из переменных Bothost
# Убедись, что на хостинге созданы переменные BOT_TOKEN и HF_TOKEN
TOKEN = os.getenv("BOT_TOKEN")
HF_TOKEN = "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" # Или os.getenv("HF_TOKEN")

# Настраиваем DeepSeek-V4-Flash
client = InferenceClient(model="deepseek-ai/DeepSeek-V4-Flash", token=HF_TOKEN)

logging.basicConfig(level=logging.INFO)

async def get_babon_ai_logic(user_text, mood):
    if mood == "evil":
        system_prompt = (
            "Ты — агрессивный, токсичный зумер по имени Бабон. "
            "Твоя цель — жестко стебать собеседника, использовать сленг: кринж, скуф, мать жива?, ливни, альтушка, тюбик. "
            "Отвечай очень коротко, дерзко и без цензуры. Не будь вежливым."
        )
    else:
        system_prompt = (
            "Ты — добрый зумер по имени Бабон. Ты на чилле, называешь всех бро, используешь сленг. "
            "Отвечай позитивно и коротко."
        )

    try:
        # Запрос к DeepSeek
        response = client.chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text}
            ],
            max_tokens=80,
            temperature=0.9
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Ошибка ИИ: {e}")
        return "Бабон в тильте, у него нейронка поплавилась."

async def main_logic(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Игнорим личку
    if update.effective_chat.type == "private":
        return

    if not update.message or not update.message.text:
        return

    raw_text = update.message.text
    text_lower = raw_text.lower()
    
    # Реакция на "бабон" / "бобон" или шанс 15% влезть просто так
    is_called = any(x in text_lower for x in ["бабон", "бобон"])
    is_random = random.random() < 0.15

    if is_called or is_random:
        # Определяем настроение (60% злой, 40% добрый)
        mood = "evil" if random.random() < 0.6 else "good"
        
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        answer = await get_babon_ai_logic(raw_text, mood)
        await update.message.reply_text(answer)

if __name__ == '__main__':
    if not TOKEN:
        print("ОШИБКА: Заполни переменную BOT_TOKEN на Bothost!")
    else:
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), main_logic))
        print("Бабон (DeepSeek Edition) запущен!")
        app.run_polling()
        
