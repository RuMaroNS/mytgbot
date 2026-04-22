import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from supabase import create_client, Client

# ДАННЫЕ ИЗ ТВОЕГО СКРИПТА
SB_URL = 'https://wbkygibviddkdjxbahbg.supabase.co'
SB_KEY = 'sb_publishable_l5wIAt6RrAl4Uo8uZKerRQ_xBYDS-Kv'
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 6176762600

# Инициализация Supabase и Бота
supabase: Client = create_client(SB_URL, SB_KEY)
bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user_tg = message.from_user.username

    if not user_tg:
        await message.answer("❌ **Ошибка:** У вас в настройках Telegram не установлен 'Username' (@username). Установите его, чтобы бот смог найти ваш аккаунт на сайте.")
        return

    try:
        # Ищем в таблице 'profiles', где в колонке 'TelegramUSER' записан юзернейм игрока
        # eq('TelegramUSER', user_tg) — это и есть поиск совпадения
        res = supabase.table("profiles").select("*").eq("TelegramUSER", user_tg).execute()
        
        if res.data and len(res.data) > 0:
            user_data = res.data[0]
            balance = user_data.get('score', 0)
            await message.answer(
                f"✅ **Аккаунт найден!**\n\n"
                f"👤 **Профиль:** {user_data.get('username')}\n"
                f"💰 **Баланс:** {balance} $\n\n"
                f"Теперь вы можете писать сюда любые вопросы, поддержка их получит!"
            )
        else:
            await message.answer(
                f"🔍 **Аккаунт не найден.**\n\n"
                f"Я искал юзера `@{user_tg}` в колонке `TelegramUSER`, но совпадений нет.\n"
                f"Убедитесь, что на сайте в профиле указан ваш верный ник Telegram."
            )
            
    except Exception as e:
        print(f"Ошибка Supabase: {e}")
        await message.answer("👋 Привет! Напиши свой вопрос, и я передам его администратору.")

@dp.message(F.text)
async def handle_msg(message: types.Message):
    # Игнорируем команду старт
    if message.text.startswith("/start"): 
        return

    # Пересылка сообщения админу (тебе)
    user = message.from_user
    report = (
        f"🆘 **НОВОЕ ОБРАЩЕНИЕ**\n\n"
        f"👤 От: @{user.username or 'скрыт'}\n"
        f"🆔 ID: `{user.id}`\n"
        f"💬 Сообщение: {message.text}"
    )

    try:
        await bot.send_message(ADMIN_ID, report, parse_mode="Markdown")
        await message.answer("🚀 Сообщение отправлено саппорту! Ожидайте ответа прямо здесь.")
    except Exception as e:
        await message.answer("❌ Ошибка отправки сообщения.")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
