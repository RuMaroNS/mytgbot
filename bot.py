import asyncio
import random
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart

# Railway сам подставит это значение из настроек Variables
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    print("Ошибка: Токен BOT_TOKEN не найден в переменных окружения!")
    exit(1)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Данные игроков
users_data = {}

def get_user_data(user_id):
    if user_id not in users_data:
        users_data[user_id] = {"secret": None, "attempts": 0}
    return users_data[user_id]

@dp.message(CommandStart())
async def cmd_start(message: Message):
    user = get_user_data(message.from_user.id)
    user["secret"] = random.randint(1, 10)
    user["attempts"] = 0
    await message.answer("🎮 Игра началась! Я загадал число от 1 до 10. Попробуй угадать!")

@dp.message(F.text.regexp(r'^\d+$'))
async def game_logic(message: Message):
    user_id = message.from_user.id
    user = get_user_data(user_id)
    
    if user["secret"] is None:
        return # Игнорируем, если игра не начата

    guess = int(message.text)
    user["attempts"] += 1

    if guess < user["secret"]:
        await message.answer("⬆️ Бери выше!")
    elif guess > user["secret"]:
        await message.answer("⬇️ Слишком много, бери ниже!")
    else:
        await message.answer(
            f"🥳 Ура! Ты угадал число {user['secret']}!\n"
            f"Попыток потрачено: {user['attempts']}.\n"
            "Напиши /start, чтобы сыграть еще раз."
        )
        user["secret"] = None

async def main():
    print("Бот успешно запущен на хостинге!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

