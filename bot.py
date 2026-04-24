import asyncio
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from supabase import create_client, Client

# --- КОНФИГУРАЦИЯ ---
SB_URL = 'https://wbkygibviddkdjxbahbg.supabase.co'
SB_KEY = 'sb_publishable_l5wIAt6RrAl4Uo8uZKerRQ_xBYDS-Kv'
BOT_TOKEN = '8241678987:AAHON1kT5rrqw6fxbsXLpnjdoLR0W6XTjxg'

supabase: Client = create_client(SB_URL, SB_KEY)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- ЛОГИКА ---
def get_user(tg_id):
    res = supabase.table("users").select("*").eq("TelegramUSER", str(tg_id)).execute()
    return res.data[0] if res.data else None

def get_case_loot(case_id):
    # Берем весь лут этого кейса, сортируем по шансам (от редких к частым)
    res = supabase.table("loot").select("*").eq("case_id", case_id).order("chance").execute()
    return res.data

@dp.callback_query(F.data.startswith("buy_"))
async def open_case_slots(callback: types.CallbackQuery):
    _, case_id, price = callback.data.split("_")
    price = int(price)
    user = get_user(callback.from_user.id)

    if not user or user['balance'] < price:
        return await callback.answer("Недостаточно 💰", show_alert=True)

    # 1. Списываем баланс сразу
    new_balance = user['balance'] - price
    supabase.table("users").update({"balance": new_balance}).eq("id", user['id']).execute()

    # 2. Отправляем системные СЛОТЫ
    # Эмодзи "🎰" выдает значения от 1 до 64
    msg = await callback.message.answer_dice(emoji="🎰")
    value = msg.dice.value 
    
    await callback.message.edit_text(f"🎰 Крутим кейс за {price}...")

    # Ждем пока анимация в ТГ закончится (обычно ~2 сек)
    await asyncio.sleep(2.5)

    # 3. Математика дропа (привязываем значение кубика к шансам)
    loot_pool = get_case_loot(case_id)
    if not loot_pool:
        return await callback.message.answer("Ошибка: в кейсе нет лута!")

    # Чем больше значение dice (до 64), тем лучше дроп (простая логика)
    # Или используем обычный рандом, так как dice.value — это просто визуал
    winning_item = random.choices(
        population=loot_pool,
        weights=[i['chance'] for i in loot_pool],
        k=1
    )[0]

    # 4. Выдача в БД
    supabase.table("inventory").insert({
        "user_id": user['id'],
        "item_name": winning_item['name']
    }).execute()

    # 5. Красивый финал
    result_text = (
        f"🎰 **РЕЗУЛЬТАТ СЛОТОВ: {value}**\n"
        f"━━━━━━━━━━━━━━\n"
        f"🎁 Вы получили: **{winning_item['name']}**\n"
        f"💎 Редкость: {winning_item.get('rarity', 'Обычное')}\n"
        f"💰 Баланс: {new_balance} 💎"
    )
    
    await callback.message.answer(result_text, parse_mode="Markdown")

# --- ОСТАЛЬНЫЕ КНОПКИ ---
@dp.message(F.text == "📦 Кейсы")
async def list_cases(message: types.Message):
    res = supabase.table("cases").select("*").execute()
    kb = InlineKeyboardBuilder()
    for c in res.data:
        kb.row(types.InlineKeyboardButton(text=f"Открыть {c['name']} ({c['price']})", callback_data=f"buy_{c['id']}_{c['price']}"))
    await message.answer("Выбери кейс для прокрутки:", reply_markup=kb.as_markup())

@dp.message(Command("start"))
async def start(message: types.Message):
    kb = ReplyKeyboardBuilder()
    kb.row(types.KeyboardButton(text="👤 Профиль"), types.KeyboardButton(text="📦 Кейсы"))
    await message.answer("Бот готов. Жми 'Кейсы' чтобы крутить слоты!", reply_markup=kb.as_markup(resize_keyboard=True))

if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
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
    
