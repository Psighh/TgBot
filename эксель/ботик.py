import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import time
from datetime import datetime, timedelta
import random
import aiohttp
import logging
from telegram import ReactionTypeEmoji

#logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "8191607797:AAEC7N4SlC2mIZcuCWBKgKgAstGK1uSQ97k"

async def custom_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message.text
    chat = update.effective_chat
    message_date = update.message.date 
    
    # Игнорируем сообщения старше 10 секунд
    if datetime.now(message_date.tzinfo) - message_date > timedelta(seconds=10):
        print(f"Игнорирую старое сообщение от {message_date}")
        return

    print(f"Получено сообщение из чата: {chat.id}, тип: {chat.type}, текст: {message}")
    
    if not message:
        return
    
    if message.lower().startswith("гв "):

        command = message[3:].strip().lower()
        
        if command == "хуй1":
            sticker_file_id = "CAACAgIAAxkBAAECgzRppxgMyw2pRRTuQE2ewtzhA2EDwwACFmkAAo7ZyEjGsk1U4P9r4zoE"
            await context.bot.send_message(chat_id=chat.id, text="хуй")
            await context.bot.send_sticker(chat_id=chat.id, sticker=sticker_file_id)
        elif command == "блядища":
            wait_message = await update.message.reply_text("🔄 Загружаю 18+ арт...")
            
            image_url = None
            caption = "🔞 представляю твою сладкую чиксу"
            
            try:
                async with aiohttp.ClientSession(headers={"User-Agent": "TelegramBot/1.0"}) as session:
                    async with session.get("https://api.waifu.pics/nsfw/waifu", timeout=10) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            image_url = data.get("url")
                        else:
                            logger.error(f"waifu.pics вернул статус {resp.status}")
                            await wait_message.edit_text(f"❌ Ошибка API: {resp.status}")
                            return
            except asyncio.TimeoutError:
                logger.error("Таймаут при запросе к waifu.pics")
                await wait_message.edit_text("❌ Превышено время ожидания")
                return
            except Exception as e:
                logger.error(f"Ошибка при запросе: {e}")
                await wait_message.edit_text("❌ Произошла неизвестная ошибка")
                return
            
            if image_url:
                try:
                    await update.message.reply_photo(photo=image_url, caption=caption)
                    await wait_message.delete()
                except Exception as e:
                    logger.error(f"Ошибка отправки фото: {e}")
                    await wait_message.edit_text("❌ Не удалось отправить изображение")
            else:
                await wait_message.edit_text("❌ Не удалось получить ссылку на изображение")
        elif command == "лайк":
            #await context.bot.send_sticker(chat_id=-1002380022509, sticker="CAACAgIAAxkBAAECjCNpqa0kWKUoLpLXV7xT_5CTkt3HqAACq5kAAvVF6EulQMuOfO7aBToE")
            #await context.bot.send_message(chat_id=-1002380022509, text="Джанго)")
            try:
                await context.bot.set_message_reaction(
                    chat_id=-1002380022509,
                    message_id=50486,
                    reaction=[ReactionTypeEmoji("💩")]
                )
                print('Лайк поставлен!')
            except Exception as e:
                logger.error(f"Ошибка при установке реакции: {e}")
        else:
            await context.bot.send_message(chat_id=chat.id, text=f"Неизвестная команда: {command}")
    

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Ошибка: {context.error}")

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, custom_command_handler))
    
    app.add_error_handler(error_handler)

    # Запускаем бота
    print("Бот запущен...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
