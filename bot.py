import asyncio
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from supabase import create_client, Client

# --- ТВОИ КОНФИГ ПАРАМЕТРЫ ---
SB_URL = 'https://wbkygibviddkdjxbahbg.supabase.co'
SB_KEY = 'sb_publishable_l5wIAt6RrAl4Uo8uZKerRQ_xBYDS-Kv'
BOT_TOKEN = '8241678987:AAHON1kT5rrqw6fxbsXLpnjdoLR0W6XTjxg'

supabase: Client = create_client(SB_URL, SB_KEY)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ---
def get_user(tg_id):
    res = supabase.table("users").select("*").eq("TelegramUSER", str(tg_id)).execute()
    return res.data[0] if res.data else None

def get_loot(case_id):
    res = supabase.table("loot").select("*").eq("case_id", case_id).execute()
    return res.data

# --- ОБРАБОТЧИКИ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user = get_user(message.from_user.id)
    kb = ReplyKeyboardBuilder()
    kb.row(types.KeyboardButton(text="👤 Профиль"), types.KeyboardButton(text="📦 Кейсы"))
    
    text = "👋 Система готова!" if user else f"⚠️ Привяжи ID: `{message.from_user.id}` в БД"
    await message.answer(text, reply_markup=kb.as_markup(resize_keyboard=True), parse_mode="Markdown")

@dp.message(F.text == "👤 Профиль")
async def cmd_profile(message: types.Message):
    user = get_user(message.from_user.id)
    if not user:
        return await message.answer("Сначала привяжи аккаунт в Supabase!")
    
    balance = user.get('balance', 0)
    # ЗДЕСЬ БЫЛА ОШИБКА ОТСТУПА:
    msg_text = (
        f"👤 **Твой профиль**\n"
        f"━━━━━━━━━━━━━━\n"
        f"💰 **Баланс:** {balance} $\n\n"
        f"Колонка TelegramUSER: `{message.from_user.id}`"
    )
    
    kb = InlineKeyboardBuilder()
    kb.row(types.InlineKeyboardButton(text="🎒 Инвентарь", callback_data="view_inv"))
    await message.answer(msg_text, reply_markup=kb.as_markup(), parse_mode="Markdown")

@dp.message(F.text == "📦 Кейсы")
async def cmd_cases(message: types.Message):
    res = supabase.table("cases").select("*").execute()
    kb = InlineKeyboardBuilder()
    for c in res.data:
        kb.row(types.InlineKeyboardButton(text=f"{c['name']} — {c['price']}$", callback_data=f"buy_{c['id']}_{c['price']}"))
    await message.answer("🎁 Выбери кейс для прокрутки:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("buy_"))
async def handle_buy(callback: types.CallbackQuery):
    _, c_id, price = callback.data.split("_")
    price = int(price)
    user = get_user(callback.from_user.id)

    if not user or user['balance'] < price:
        return await callback.answer("Недостаточно денег!", show_alert=True)

    # Списываем бабки
    new_balance = user['balance'] - price
    supabase.table("users").update({"balance": new_balance}).eq("id", user['id']).execute()

    # СЛОТЫ ТГ
    msg = await callback.message.answer_dice(emoji="🎰")
    await callback.message.edit_text(f"🎰 Крутим кейс {c_id}...")
    
    await asyncio.sleep(3.0) # Ждем анимацию

    loot_pool = get_loot(c_id)
    if not loot_pool:
        return await callback.message.answer("Кейс пустой в БД!")

    # Рандом по шансам
    win = random.choices(loot_pool, weights=[i['chance'] for i in loot_pool], k=1)[0]

    # В инвентарь
    supabase.table("inventory").insert({"user_id": user['id'], "item_name": win['name']}).execute()

    await callback.message.answer(
        f"🎊 **ВЫПАЛО:** {win['name']}\n"
        f"💰 Остаток: {new_balance} $\n"
        f"🎰 Значение слотов: {msg.dice.value}",
        parse_mode="Markdown"
    )

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
