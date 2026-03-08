import asyncio
from telegram import Update, ReactionTypeEmoji
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime, timedelta
import random
import aiohttp
import logging
import json
from datetime import date

total_requests_count = 0
current_day = date.today()
MAX_DAILY_LIMIT = 5

#logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "8191607797:AAEC7N4SlC2mIZcuCWBKgKgAstGK1uSQ97k"

async def custom_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.message.sticker:
        await handle_sticker_reactions(update, context)
        return

    if not update.message.text or is_message_old(update):
        return

    message = update.message.text
    chat = update.effective_chat
    message_date = update.message.date 
    
    print(f"Получено сообщение из чата: {chat.id}, тип: {chat.type}, текст: {message}")
    
    if not message:
        return
    
    if message.lower().startswith("гв "):
        await process_gv_commands(update, context, message[3:].strip().lower())

async def process_gv_commands(update: Update, context: ContextTypes.DEFAULT_TYPE, command: str):
    chat_id = update.effective_chat.id

    if command == "хуй":
        sticker_id = "CAACAgIAAxkBAAECgzRppxgMyw2pRRTuQE2ewtzhA2EDwwACFmkAAo7ZyEjGsk1U4P9r4zoE"
        await context.bot.send_message(chat_id=chat_id, text="хуй")
        await context.bot.send_sticker(chat_id=chat_id, sticker=sticker_id)

    elif command == "кастом":
        await context.bot.send_message(chat_id=-5160768325, text="Ничего не делаю") #-1002380022509

    elif command.startswith("рул"):
        tags = command[3:].strip().replace(" ", "_")
        if not tags:
            await update.message.reply_text("❌ Введите теги!")
            return
        await get_rule34_post(update, tags, context)

    elif command.startswith("погода"):
        city = command[6:].strip()
        if not city:
            await update.message.reply_text("❌ Введите город!")
            return
        await get_weather(update, city, context)

    else:
        await context.bot.send_message(chat_id=chat_id, text=f"Неизвестная команда: {command}")

async def handle_sticker_reactions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_id = "CAACAgIAAxkBAAIB0GmprRn4W6u5b92a222Lm5mOPYPLAAKrmQAC9UXoS6VAy4587toFOgQ"
    
    if update.message.sticker.file_id == target_id:
        try:
            await context.bot.set_message_reaction(
                chat_id=update.effective_chat.id,
                message_id=update.message.message_id,
                reaction=[ReactionTypeEmoji("❤️")]
            )
        except Exception as e:
            logger.error(f"Ошибка реакции: {e}")

def is_message_old(update: Update, seconds=10) -> bool:
    message_date = update.message.date
    if datetime.now(message_date.tzinfo) - message_date > timedelta(seconds=seconds):
        print(f"Игнорирую старое сообщение от {message_date}")
        return True
    return False
    

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Ошибка: {context.error}")

async def get_rule34_post(update: Update, tags: str, context: ContextTypes.DEFAULT_TYPE):
    global total_requests_count, current_day
    
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

    session = context.bot_data.get('http_session')
    if not session:
        await wait_message.edit_text("🚨 Ошибка: HTTP-сессия не инициализирована.")
        return

    try:
        api_url = "https://api.rule34.xxx/index.php"
        params = {
            "page": "dapi", "q": "index", "s": "post",
            "json": 1, "tags": tags, "limit": 50,
            "user_id": USER_ID, "api_key": API_KEY
        }
        
        async with session.get(api_url, params=params, timeout=15) as resp:
                raw_text = await resp.text()
                posts = []

                if raw_text.strip().startswith("["):
                    posts = json.loads(raw_text)
                elif "<?xml" in raw_text or "<posts" in raw_text:
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(raw_text)
                    for child in root.findall('post'):
                        posts.append({'file_url': child.get('file_url'), 'id': child.get('id')})

                if posts:
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

async def get_weather(update: Update, city: str, context: ContextTypes.DEFAULT_TYPE):
    weather_api_key = "517f0dffb88450251a36c1ebcad986ef"
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={weather_api_key}&units=metric&lang=ru"

    session = context.bot_data['http_session']

    try:
        async with session.get(url) as resp:
            if resp.status == 200:
                data = await resp.json()
                    
                city_name = data["name"]
                temp = data["main"]["temp"]
                feels_like = data["main"]["feels_like"]
                description = data["weather"][0]["description"]
                humidity = data["main"]["humidity"]
                wind_speed = data["wind"]["speed"]

                text = (
                        f"🌍 **Погода в городе {city_name}**\n"
                        f"🌡 Температура: {temp}°C\n"
                        f"🤔 Ощущается как: {feels_like}°C\n"
                        f"☁️ Описание: {description.capitalize()}\n"
                        f"💧 Влажность: {humidity}%\n"
                        f"💨 Ветер: {wind_speed} м/с"
                    )
                await update.message.reply_text(text, parse_mode="Markdown")
            elif resp.status == 404:
                await update.message.reply_text(f"❌ Город `{city}` не найден.")
            else:
                await update.message.reply_text("❌ Ошибка при запросе к сервису погоды.")
    except Exception as e:
        logger.error(f"Weather error: {e}")
        await update.message.reply_text("🚨 Произошла ошибка при получении погоды.")

async def post_init(application: Application):
    application.bot_data['http_session'] = aiohttp.ClientSession()
    print("🌐 Единая HTTP-сессия создана")

async def post_shutdown(application: Application):
    session = application.bot_data.get('http_session')
    if session:
        await session.close()
        print("🌐 Сессия закрыта, бот спит крепко.")

def main():
    app = Application.builder().token(TOKEN).post_init(post_init).post_shutdown(post_shutdown).build()

    app.add_handler(MessageHandler(filters.TEXT | filters.Sticker.ALL, custom_command_handler))
    
    app.add_error_handler(error_handler)

    # Запускаем бота
    print("Бот запущен...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
