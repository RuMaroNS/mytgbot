import asyncio
import random
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from supabase import create_client, Client

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# ========== КОНФИГУРАЦИЯ ==========
SB_URL = 'https://wbkygibviddkdjxbahbg.supabase.co'
SB_KEY = 'sb_publishable_l5wIAt6RrAl4Uo8uZKerRQ_xBYDS-Kv'
BOT_TOKEN = '8630026221:AAGfuIfKQPdxSkyhU3IVCnRtRkKrlzKD0nk'

supabase: Client = create_client(SB_URL, SB_KEY)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ========== ФУНКЦИЯ ВХОДА С ПОДСТАНОВКОЙ @ ==========

def get_profile_by_username(tg_user_obj):
    """
    Получает объект юзера из ТГ, берет его username,
    добавляет @ и ищет в таблице profiles.
    """
    if not tg_user_obj or not tg_user_obj.username:
        return None
    
    # Формируем строку с собакой: R0bONe -> @R0bONe
    username_with_dog = f"@{tg_user_obj.username}"
    
    res = supabase.table("profiles").select("*").eq("TelegramUSER", username_with_dog).execute()
    return res.data[0] if res.data else None

def get_item_details(item_name):
    """Берем инфу из items_meta"""
    res = supabase.table("items_meta").select("*").eq("name", item_name).execute()
    return res.data[0] if res.data else None

# ========== ОБРАБОТЧИКИ ==========

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user = get_profile_by_username(message.from_user)
    
    kb = ReplyKeyboardBuilder()
    kb.row(types.KeyboardButton(text="👤 Профиль"), types.KeyboardButton(text="📦 Кейсы"))
    
    if user:
        await message.answer(f"✅ Успешный вход! Твой аккаунт: **{user['username']}**", 
                             reply_markup=kb.as_markup(resize_keyboard=True),
                             parse_mode="Markdown")
    else:
        # Если не нашел, выводим что именно бот искал для проверки
        search_term = f"@{message.from_user.username}" if message.from_user.username else "нет юзернейма"
        await message.answer(f"❌ Аккаунт не найден.\nБот искал в БД текст: `{search_term}`\n\n"
                             f"Убедись, что в колонке TelegramUSER в Supabase написано именно так.",
                             parse_mode="Markdown")

@dp.message(F.text == "👤 Профиль")
async def cmd_profile(message: types.Message):
    user = get_profile_by_username(message.from_user)
    if not user:
        return await message.answer("Ошибка: профиль не найден. Нажми /start")
    
    score = user.get('score', 0)
    inv = user.get('inventory', [])
    inv_count = len(inv) if isinstance(inv, list) else 0
    
    await message.answer(
        f"👤 **Профиль: {user['username']}**\n"
        f"━━━━━━━━━━━━━━\n"
        f"💰 **Баланс:** {score} score\n"
        f"🎒 **Инвентарь:** {inv_count} шт.\n"
        f"🔑 **Юзер:** @{message.from_user.username}",
        parse_mode="Markdown"
    )

@dp.message(F.text == "📦 Кейсы")
async def cmd_cases(message: types.Message):
    res = supabase.table("cases_meta").select("*").execute()
    kb = InlineKeyboardBuilder()
    for c in res.data:
        kb.row(types.InlineKeyboardButton(
            text=f"{c['name']} — {c['price']} 💰", 
            callback_data=f"buy_{c['id']}_{c['price']}"
        ))
    await message.answer("🎁 Выбери кейс:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("buy_"))
async def handle_opening(callback: types.CallbackQuery):
    _, c_id, price = callback.data.split("_")
    price = int(price)
    user = get_profile_by_username(callback.from_user)

    if not user or user.get('score', 0) < price:
        return await callback.answer("Недостаточно score! ❌", show_alert=True)

    # 1. Списание
    new_score = user['score'] - price
    supabase.table("profiles").update({"score": new_score}).eq("id", user['id']).execute()

    # 2. Слоты
    dice_msg = await callback.message.answer_dice(emoji="🎰")
    await callback.message.edit_text(f"🎰 Открываем кейс ID:{c_id}...")
    await asyncio.sleep(3.5)

    # 3. Лут
    case_data = supabase.table("cases_meta").select("loot").eq("id", c_id).single().execute()
    loot_pool = case_data.data.get('loot', [])

    win = random.choices(loot_pool, weights=[float(i.get('chance', 1)) for i in loot_pool], k=1)[0]
    
    # 4. Подтягиваем инфу из items_meta
    details = get_item_details(win['name'])
    d_name = details.get('display_name', win['name']) if details else win['name']
    rarity = details.get('rarity', 'common') if details else 'common'

    # 5. Запись в инвентарь
    current_inv = user.get('inventory', [])
    if not isinstance(current_inv, list): current_inv = []
    
    current_inv.append({
        "id": str(random.randint(1111111111, 9999999999)), 
        "char": win['name']
    })
    
    supabase.table("profiles").update({"inventory": current_inv}).eq("id", user['id']).execute()

    await callback.message.answer(
        f"🎊 **ВЫПАЛО:** {d_name}\n"
        f"💎 Редкость: `{rarity.upper()}`\n"
        f"💰 Баланс: {new_score} score",
        parse_mode="Markdown"
    )

async def main():
    print("Бот запущен. Поиск по @username активен.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
