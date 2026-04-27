import asyncio
from aiogram import Bot, Dispatcher, types
from supabase import create_client, Client

# --- ТВОИ ДАННЫЕ ---
TOKEN = "8630026221:AAGfuIfKQPdxSkyhU3IVCnRtRkKrlzKD0nk"
URL = "https://wbkygibviddkdjxbahbg.supabase.co"
KEY = "sb_publishable_l5wIAt6RrAl4Uo8uZKerRQ_xBYDS-Kv"

bot = Bot(token=TOKEN)
dp = Dispatcher()
supabase: Client = create_client(URL, KEY)

# --- АВТО-ЗАПОМИНАЛКА (Лички, Группы, Каналы) ---
@dp.message()
@dp.my_chat_member()
@dp.channel_post()
async def register_any_chat(event):
    chat_id = None
    if hasattr(event, 'chat'):
        chat_id = event.chat.id
    elif hasattr(event, 'message'):
        chat_id = event.message.chat.id
        
    if chat_id:
        # Пихаем любой ID в одну таблицу. Supabase сам поймет, если он уже там есть.
        try:
            supabase.table("active_chats").upsert({"chat_id": chat_id}).execute()
        except:
            pass

# --- РАССЫЛКА ПО СПИСКУ ---
async def broadcast_loop():
    print("📡 Мониторинг запущен. База 'active_chats' в деле.")
    while True:
        try:
            # 1. Чекаем ивент
            res = supabase.table("game_events").select("*").eq("status", "new").execute()
            
            if res.data:
                # 2. Достаем ВООБЩЕ ВСЕ сохраненные ID
                chats_res = supabase.table("active_chats").select("chat_id").execute()
                targets = [c['chat_id'] for c in chats_res.data]

                for ev in res.data:
                    event_name = ev['event_name']
                    text = f"🚨 ЩЕЛЧОК ('{event_name}') БЫЛ ЗАПУЩЕН\n\nЗаходим в игру🎮"

                    print(f"📢 Рассылаю '{event_name}' на {len(targets)} чатов/личек...")
                    
                    for tid in targets:
                        try:
                            await bot.send_message(tid, text)
                        except:
                            continue # Если забанили — пофиг, идем дальше

                    # 3. Закрываем ивент
                    supabase.table("game_events").update({"status": "done"}).eq("id", ev['id']).execute()
                    print(f"🏁 Рассылка завершена.")

        except Exception as e:
            print(f"⚠️ Ошибка: {e}")
        
        await asyncio.sleep(5)

async def main():
    asyncio.create_task(broadcast_loop())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
