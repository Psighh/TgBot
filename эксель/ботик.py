import asyncio
from doctest import master
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import time
from datetime import datetime, timedelta
import random
import aiohttp
import logging
from telegram import ReactionTypeEmoji
import json
from datetime import date

total_requests_count = 0
current_day = date.today()
MAX_DAILY_LIMIT = 5

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
        
        if command == "хуй":
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
        elif command == "кастом":
            #await context.bot.send_sticker(chat_id=-1002380022509, sticker="CAACAgIAAxkBAAECjCNpqa0kWKUoLpLXV7xT_5CTkt3HqAACq5kAAvVF6EulQMuOfO7aBToE")
            await context.bot.send_message(chat_id=-1002380022509, text="") #-5160768325
            await context.bot.send_photo(chat_id=-1002380022509, photo="")
            # try:
            #     await context.bot.set_message_reaction(
            #         chat_id=-1002380022509,
            #         message_id=50486,
            #         reaction=[ReactionTypeEmoji("💩")]
            #     )
            #     print('Лайк поставлен!')
            # except Exception as e:
            #     logger.error(f"Ошибка при установке реакции: {e}")
        elif command.startswith("рул"):
            tags = command[3:].strip().replace(" ", "_").lower()
            if not tags:
                await update.message.reply_text("❌ Введите теги!")
                return
            await get_rule34_post(update, tags)
        else:
            await context.bot.send_message(chat_id=chat.id, text=f"Неизвестная команда: {command}")
    

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Ошибка: {context.error}")

async def get_rule34_post(update: Update, tags: str):
    global total_requests_count, current_day
    
    # Константы (можно вынести в начало файла)
    USER_ID = "6008643"
    API_KEY = "f3c359dc8d4921981db6be0d99f7cd3eeb298baede968b20f7b2c188bf72d03c77dadb06739e78ffbfb1b1e88061d3b713ae900d8daad6d322740c3e20d179b8"
    MAX_DAILY_LIMIT = 5

    # 1. Проверка на новый день
    today = date.today()
    if today != current_day:
        total_requests_count = 0
        current_day = today

    # 2. Проверка лимита
    if total_requests_count >= MAX_DAILY_LIMIT:
        await update.message.reply_text(
            f"🛑 Лимит исчерпан ({total_requests_count}/{MAX_DAILY_LIMIT}). Завтра обновится!"
        )
        return

    wait_message = await update.message.reply_text(
        f"🔍 Ищу: {tags}... ({total_requests_count + 1}/{MAX_DAILY_LIMIT})"
    )

    try:
        api_url = "https://api.rule34.xxx/index.php"
        params = {
            "page": "dapi", "q": "index", "s": "post",
            "json": 1, "tags": tags, "limit": 50,
            "user_id": USER_ID, "api_key": API_KEY
        }
        
        async with aiohttp.ClientSession(headers={"User-Agent": "Mozilla/5.0"}) as session:
            async with session.get(api_url, params=params, timeout=15) as resp:
                raw_text = await resp.text()
                posts = []

                if raw_text.strip().startswith("["):
                    import json
                    posts = json.loads(raw_text)
                elif "<?xml" in raw_text or "<posts" in raw_text:
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(raw_text)
                    for child in root.findall('post'):
                        posts.append({'file_url': child.get('file_url'), 'id': child.get('id')})

                if posts:
                    import random
                    post = random.choice(posts)
                    image_url = post.get("file_url")
                    if image_url and image_url.startswith("//"):
                        image_url = "https:" + image_url
                    
                    caption = f"🔞 Тег: {tags}\n📊 Лимит: {total_requests_count + 1}/{MAX_DAILY_LIMIT}"
                    
                    if any(image_url.lower().endswith(ext) for ext in ['.mp4', '.webm']):
                        await update.message.reply_video(video=image_url, caption=caption)
                    else:
                        await update.message.reply_photo(photo=image_url, caption=caption)
                    
                    total_requests_count += 1
                    await wait_message.delete()
                else:
                    await wait_message.edit_text(f"😔 По запросу `{tags}` ничего не найдено.")
    except Exception as e:
        print(f"ОШИБКА: {e}")
        await wait_message.edit_text("🚨 Ошибка при поиске.")

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, custom_command_handler))
    
    app.add_error_handler(error_handler)

    # Запускаем бота
    print("Бот запущен...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
