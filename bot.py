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

# --- АВТО-ЗАПОМИНАЛКА ---
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
        try:
            supabase.table("active_chats").upsert({"chat_id": chat_id}).execute()
        except:
            pass

# --- РАССЫЛКА (ЧИСТЫЙ ТЕКСТ) ---
async def broadcast_loop():
    print("📡 Бот-ретранслятор запущен. Жду данные из Supabase...")
    while True:
        try:
            # 1. Получаем новые ивенты
            res = supabase.table("game_events").select("*").eq("status", "new").execute()
            
            if res.data:
                # 2. Получаем список всех чатов
                chats_res = supabase.table("active_chats").select("chat_id").execute()
                targets = [c['chat_id'] for c in chats_res.data]

                for ev in res.data:
                    # БЕРЕМ ТЕКСТ КАК ОН ЕСТЬ, БЕЗ ПРИПИСОК
                    raw_text = ev['event_name']
                    
                    print(f"📢 Отправляю: {raw_text}")
                    
                    for tid in targets:
                        try:
                            # Отправляем чистый текст из базы
                            await bot.send_message(tid, raw_text)
                        except Exception as e:
                            print(f"❌ Ошибка отправки в {tid}: {e}")
                            continue

                    # 3. Помечаем как выполненное
                    supabase.table("game_events").update({"status": "done"}).eq("id", ev['id']).execute()
                    print(f"✅ Готово.")

        except Exception as e:
            print(f"⚠️ Ошибка цикла: {e}")
        
        await asyncio.sleep(5)

async def main():
    # Запускаем цикл рассылки фоном
    asyncio.create_task(broadcast_loop())
    # Запускаем бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
