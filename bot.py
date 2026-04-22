import os
import random
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest

TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Временное хранилище игр (в продакшене лучше использовать Redis)
user_games = {}

def get_main_keyboard():
    builder = InlineKeyboardBuilder()
    # Эмодзи-игры из вашего первого запроса
    builder.row(
        *[types.InlineKeyboardButton(text=em, callback_data=f"game_{i}") 
          for i, em in enumerate(["🏀", "⚽", "🎯", " bowling", "🎲", "🎰"])]
    )
    builder.row(
        types.InlineKeyboardButton(text="🚀 Быстрые", callback_data="fast"),
        types.InlineKeyboardButton(text="Режимы 💣", callback_data="modes"),
    )
    builder.row(types.InlineKeyboardButton(text="🕹 Играть в WEB", url="https://google.com"))
    builder.row(types.InlineKeyboardButton(text="✏️ Изменить ставку", callback_data="edit_bet"))
    return builder.as_markup()

def get_modes_keyboard():
    builder = InlineKeyboardBuilder()
    modes = [
        ("💣 Мины", "start_mines"), ("💎 Алмазы", "none"),
        ("⛰ Башня", "none"), ("💰 Золото", "none"),
        ("🐸 Квак", "none"), ("📈 HiLo", "none"),
        ("🃏 21(Очко)", "none"), ("🛶 Пирамида", "none")
    ]
    for i in range(0, len(modes), 2):
        builder.row(
            types.InlineKeyboardButton(text=modes[i][0], callback_data=modes[i][1]),
            types.InlineKeyboardButton(text=modes[i+1][0], callback_data=modes[i+1][1])
        )
    builder.row(types.InlineKeyboardButton(text="⬅️ Назад", callback_data="main_menu"))
    return builder.as_markup()

# --- Логика игры МИНЫ ---

def create_mines_keyboard(user_id):
    game = user_games[user_id]
    builder = InlineKeyboardBuilder()
    
    for i in range(15): # Поле 3x5 как в видео
        if i in game['opened']:
            text = "💎" if i not in game['mines'] else "💥"
            cb_data = "ignore"
        else:
            text = "❓"
            cb_data = f"mine_{i}"
        builder.add(types.InlineKeyboardButton(text=text, callback_data=cb_data))
    
    builder.adjust(5)
    builder.row(types.InlineKeyboardButton(text="💰 Забрать выигрыш", callback_data="cashout"))
    return builder.as_markup()

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "🎮 **ДАВАЙ НАЧНЕМ ИГРАТЬ!**\n\n💰 **Баланс:** 190 m₵\n💸 **Ставка:** 10 m₵",
        reply_markup=get_main_keyboard(),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data == "modes")
async def show_modes(callback: types.CallbackQuery):
    await callback.message.edit_text("Выбери игру и начинай!", reply_markup=get_modes_keyboard())

@dp.callback_query(F.data == "start_mines")
async def start_mines(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    # Генерируем 3 мины на 15 клеток
    mines = random.sample(range(15), 3)
    user_games[user_id] = {
        'mines': mines,
        'opened': [],
        'win_step': 0,
        'bet': 10
    }
    
    await callback.message.edit_text(
        "💣 **Мины - игра идет**\n\nСтавка: 10 m₵\nВыигрыш: 0 m₵",
        reply_markup=create_mines_keyboard(user_id),
        parse_mode="Markdown"
    )

@dp.callback_query(F.data.startswith("mine_"))
async def process_mine(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id not in user_games: return
    
    cell = int(callback.data.split("_")[1])
    game = user_games[user_id]
    
    if cell in game['mines']:
        # Проигрыш
        game['opened'] = list(range(15)) # Открываем всё
        await callback.message.edit_text(
            "💥 **Мины - Проигрыш!**\n\nВы попали на мину!",
            reply_markup=None
        )
        await asyncio.sleep(3)
        await show_modes(callback)
        del user_games[user_id]
    else:
        # Успешный ход
        game['opened'].append(cell)
        game['win_step'] += 1
        win_amount = game['bet'] * (1.2 ** game['win_step'])
        
        try:
            await callback.message.edit_text(
                f"💣 **Мины - игра идет**\n\nСтавка: {game['bet']} m₵\nВыигрыш: {win_amount:.2f} m₵",
                reply_markup=create_mines_keyboard(user_id),
                parse_mode="Markdown"
            )
        except TelegramBadRequest:
            pass # Если сообщение не изменилось
    await callback.answer()

@dp.callback_query(F.data == "cashout")
async def cashout(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    if user_id in user_games:
        game = user_games[user_id]
        win = game['bet'] * (1.2 ** game['win_step'])
        await callback.answer(f"✅ Вы забрали {win:.2f} m₵!", show_alert=True)
        del user_games[user_id]
        await show_modes(callback)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
