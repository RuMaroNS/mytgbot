import asyncio
import random
import sqlite3
import datetime
import os
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command, CommandStart, CommandObject
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# Берем данные из панели Bothost
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0")) 

# Инициализация для aiogram 3.7.0+
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
DB_NAME = "dick_game.db"

# --- БАЗА ДАННЫХ ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
        (user_id INTEGER PRIMARY KEY, username TEXT, dick_size INTEGER DEFAULT 0, balance INTEGER DEFAULT 0, last_grow TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS promo_codes 
        (code TEXT PRIMARY KEY, reward_size INTEGER, reward_balance INTEGER, uses INTEGER)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS used_promos 
        (user_id INTEGER, code TEXT, PRIMARY KEY (user_id, code))''')
    conn.commit()
    conn.close()

def get_user(user_id, username="👤 Неизвестный"):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    if not user:
        cursor.execute('INSERT INTO users (user_id, username) VALUES (?, ?)', (user_id, username))
        conn.commit()
        return (user_id, username, 0, 0, None)
    conn.close()
    return user

def update_user(user_id, **kwargs):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    for key, value in kwargs.items():
        cursor.execute(f'UPDATE users SET {key} = ? WHERE user_id = ?', (value, user_id))
    conn.commit()
    conn.close()

# --- ОБРАБОТКА ---

@dp.message(CommandStart())
async def start_handler(message: Message):
    user = get_user(message.from_user.id, message.from_user.username)
    if message.chat.type in ['group', 'supergroup']:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📏 Вырастить!", callback_query_data="grow")],
            [InlineKeyboardButton(text="🏆 Топ игроков", callback_query_data="top")]
        ])
        await message.answer(f"💪 Привет чату! Кто тут самый длинный?", reply_markup=kb)
    else:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎁 Промокод", callback_query_data="promo_info")],
            [InlineKeyboardButton(text="🛒 Магазин", callback_query_data="shop_menu")]
        ])
        await message.answer(f"👋 Привет! Твой размер: <b>{user[2]} см</b>.\nВыращивать можно только в группах!", reply_markup=kb)

@dp.callback_query(F.data == "grow")
async def grow_callback(callback: CallbackQuery):
    if callback.message.chat.type == 'private':
        await callback.answer("❌ В личке не растет! Иди в группу.", show_alert=True)
        return
    
    user = get_user(callback.from_user.id, callback.from_user.username)
    now = datetime.datetime.now()
    
    if user[4]:
        last_grow = datetime.datetime.strptime(user[4], '%Y-%m-%d %H:%M:%S.%f')
        if (now - last_grow).total_seconds() < 86400:
            await callback.answer("⏳ Только раз в сутки!", show_alert=True)
            return

    change = random.randint(-4, 12)
    new_size = max(0, user[2] + change)
    update_user(user_id=callback.from_user.id, dick_size=new_size, balance=user[3]+30, last_grow=str(now))
    
    res = "+" if change >= 0 else ""
    await callback.message.answer(f"📈 @{callback.from_user.username}, {res}{change} см!\nТеперь: <b>{new_size} см</b>")
    await callback.answer()

@dp.callback_query(F.data == "top")
async def top_callback(callback: CallbackQuery):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT username, dick_size FROM users ORDER BY dick_size DESC LIMIT 10')
    rows = cursor.fetchall()
    conn.close()
    
    text = "🏆 <b>ТОП-10 ГИГАНТОВ:</b>\n\n"
    for i, r in enumerate(rows, 1):
        text += f"{i}. @{r[0]} — {r[1]} см\n"
    await callback.message.answer(text)
    await callback.answer()

async def main():
    init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
