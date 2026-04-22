import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Вытягиваем токен, который ты прописал на сайте
TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

def get_keyboard():
    kb = InlineKeyboardBuilder()
    
    # Первая полоска с эмодзи (все 6 штук в один ряд)
    kb.row(
        types.InlineKeyboardButton(text="🏀", callback_data="g_basket"),
        types.InlineKeyboardButton(text="⚽", callback_data="g_soccer"),
        types.InlineKeyboardButton(text="🎯", callback_data="g_darts"),
        types.InlineKeyboardButton(text=" bowling", callback_data="g_bowling"),
        types.InlineKeyboardButton(text="🎲", callback_data="g_dice"),
        types.InlineKeyboardButton(text="🎰", callback_data="g_slots")
    )
    
    # Остальные кнопки
    kb.row(
        types.InlineKeyboardButton(text="🚀 Быстрые", callback_data="fast"),
        types.InlineKeyboardButton(text="Режимы 💣", callback_data="modes")
    )
    kb.row(types.InlineKeyboardButton(text="🕹 Играть в WEB", url="https://t.me/your_bot_link"))
    kb.row(types.InlineKeyboardButton(text="✏️ Изменить ставку", callback_data="bet"))
    
    return kb.as_markup()

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        "🎮 **ДАВАЙ НАЧНЕМ ИГРАТЬ!**\n\n💰 **Баланс:** 0 m₵\n💸 **Ставка:** 10 m₵",
        reply_markup=get_keyboard(),
        parse_mode="Markdown"
    )

@dp.callback_query(lambda c: c.data.startswith('g_'))
async def play(callback: types.CallbackQuery):
    emoji_dict = {
        "g_basket": "🏀", "g_soccer": "⚽", "g_darts": "🎯",
        "g_bowling": "🎳", "g_dice": "🎲", "g_slots": "🎰"
    }
    # Кидает кубик в ответ на нажатие эмодзи
    await callback.message.answer_dice(emoji=emoji_dict[callback.data])
    await callback.answer()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    
