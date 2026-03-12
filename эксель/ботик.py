import asyncio
import asyncpg
from telegram import Update, ReactionTypeEmoji
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime, timedelta
import random
import aiohttp
import logging
import json
from datetime import date

DB_CONFIG = "postgresql://postgres:123123@localhost:5432/postgres"

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

    pool = context.bot_data.get('db_pool')
    if pool:
        await give_mmr(
            pool, 
            update.effective_user.id, 
            context, 
            update.effective_chat.id, 
            1
        )

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
        sticker_id = "CAACAgIAAxkBAAECqyVpsyLE9BVggzEPYwRTVaBfsceDGQACwGcAAuu_kEgISLE2EPhp8ToE"
        await context.bot.send_message(chat_id=-5160768325, text="📢 С данного момента бот активен 24/7\n☑️ Просьба пройти регистрацию с помощью Гв рег (ник)\n❗️ Без регистрации вам не доступно:\n- 🏆 Система рангов\n- 🇬🇹 Гражданство гватемалы\n- ❌ Вас не будет в топе пользователей (Гв топ)") #-1002380022509
        await context.bot.send_sticker(chat_id=chat_id, sticker=sticker_id)

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
    elif command.startswith("рег"):
        new_nickname = command[3:].strip()
        pool = context.bot_data.get('db_pool')

        if not pool:
            await update.message.reply_text("🚨 Ошибка: База данных не подключена.")
            return

        success, response_text = await register_user(pool, update.effective_user, new_nickname)
        
        parse_mode = "Markdown" if success or "Пример" in response_text else None
        await update.message.reply_text(response_text, parse_mode=parse_mode)
    elif command.startswith("ник"):
        new_nickname = command[3:].strip()
        pool = context.bot_data.get('db_pool')

        if not pool:
            await update.message.reply_text("🚨 Ошибка: База данных не подключена.")
            return

        success, response_text = await update_nickname(pool, update.effective_user.id, new_nickname)
        
        parse_mode = "Markdown" if success else None
        await update.message.reply_text(response_text, parse_mode=parse_mode)
    elif command in ['инфа','инфо']:
        pool = context.bot_data.get('db_pool')
        if not pool:
            await update.message.reply_text("🚨 Ошибка: База данных не подключена.")
            return

        success, response_text = await get_user_info(pool, update.effective_user.id)
        await update.message.reply_text(response_text, parse_mode="Markdown")
    elif command == "топ":
        pool = context.bot_data.get('db_pool')
        if not pool:
            await update.message.reply_text("🚨 Ошибка: База данных не подключена.")
            return
        
        response_text = await get_top_users(pool)
        await update.message.reply_text(response_text, parse_mode="Markdown", disable_web_page_preview=True)
    else:
        await context.bot.send_message(chat_id=chat_id, text=f"Неизвестная команда: {command}")

def calculate_rang(mmr: int) -> str:
    if mmr < 50:
        return "Рекрут I"
    elif mmr < 100:
        return "Рекрут II"
    elif mmr < 150:
        return "Рекрут III"
    elif mmr < 200:
        return "Рекрут IV"
    elif mmr < 250:
        return "Рекрут V"
  
    elif mmr < 300:
        return "Страж I"
    elif mmr < 375:
        return "Страж II"
    elif mmr < 450:
        return "Страж III"
    elif mmr < 525:
        return "Страж IV"
    elif mmr < 600:
        return "Страж V"

    elif mmr < 700:
        return "Рыцарь I"
    elif mmr < 800:
        return "Рыцарь II"
    elif mmr < 900:
        return "Рыцарь III"
    elif mmr < 1000:
        return "Рыцарь IV"
    elif mmr < 1100:
        return "Рыцарь V"

    elif mmr < 1200:
        return "Герой I"
    elif mmr < 1300:
        return "Герой II"
    elif mmr < 1400:
        return "Герой III"
    elif mmr < 1500:
        return "Герой IV"
    elif mmr < 1600:
        return "Герой V"

    elif mmr < 1700:
        return "Легенда I"
    elif mmr < 1800:
        return "Легенда II"
    elif mmr < 1900:
        return "Легенда III"
    elif mmr < 2000:
        return "Легенда IV"
    elif mmr < 2100:
        return "Легенда V"

    elif mmr < 2200:
        return "Властелин I"
    elif mmr < 2300:
        return "Властелин II"
    elif mmr < 2400:
        return "Властелин III"
    elif mmr < 2500:
        return "Властелин IV"
    elif mmr < 2600:
        return "Властелин V"

    elif mmr < 2800:
        return "Божество I"
    elif mmr < 3000:
        return "Божество II"
    elif mmr < 3200:
        return "Божество III"
    elif mmr < 3400:
        return "Божество IV"
    elif mmr < 3600:
        return "Божество V"

    else:
        return "Титан"

async def give_mmr(pool, user_id: int, context: ContextTypes.DEFAULT_TYPE, chat_id: int, amount: int = 1):
    try:
        async with pool.acquire() as conn:
            current_data = await conn.fetchrow(
                "SELECT rating, rang, custom_nickname FROM users WHERE user_id = $1", 
                user_id
            )
            
            if not current_data:
                return False

            old_rang = current_data['rang']
            new_mmr = int(current_data['rating']) + amount
            new_rang = calculate_rang(new_mmr)
            nickname = current_data['custom_nickname']

            await conn.execute("""
                UPDATE users 
                SET rating = $1, rang = $2 
                WHERE user_id = $3
            """, new_mmr, new_rang, user_id)
            
            if old_rang != new_rang:
                user_link = f"[{nickname}](tg://user?id={user_id})"
                congrats_text = (
                    f"🎉 **Повышение!**\n"
                    f"🎖 {user_link}, твой ранг теперь: **{new_rang}**!\n"
                    f"📈 Текущий рейтинг: {new_mmr} ммр."
                )
                await context.bot.send_message(chat_id=chat_id, text=congrats_text, parse_mode="Markdown")

            return True
    except Exception as e:
        logger.error(f"Ошибка в give_mmr: {e}")
        return False

async def get_top_users(pool):
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT user_id, custom_nickname, rang, rating 
                FROM users 
                ORDER BY rating DESC 
                LIMIT 10
            """)

            if not rows:
                return "📈 Список пуст. Никто еще не зарегистрировался!"

            text = "🏆 **Топ пользователей по рейтингу:**\n\n"
            
            for i, row in enumerate(rows, start=1):
                user_link = f"[{row['custom_nickname']}](tg://user?id={row['user_id']})"
                
                text += f"{i}. {user_link} [[{row['rang']}]] — {row['rating']} ммр.\n"
            
            return text

    except Exception as e:
        logger.error(f"Ошибка в get_top_users: {e}")
        return "🚨 Произошла ошибка при получении списка лидеров."

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

async def get_user_info(pool, user_id: int):
    try:
        async with pool.acquire() as conn:
            user_data = await conn.fetchrow("""
                SELECT custom_nickname, rang, rating, registered_at 
                FROM users 
                WHERE user_id = $1
            """, user_id)

            if not user_data:
                return False, "⚠️ Ты еще не зарегистрирован! Используй: гв рег (ник)"

            # Форматируем дату (если она есть)
            reg_date = user_data['registered_at']
            reg_date_str = reg_date.strftime("%d.%m.%Y") if reg_date else "Неизвестно"
            user_link = f"[{user_data['custom_nickname']}](tg://user?id={user_id})"
            info_text = (
                f"👤 **Твой профиль:**\n"
                f"🏷 **Ник:** {user_link}\n"
                f"🎖 **Ранг:** {user_data['rang']}\n"
                f"🏆 **Рейтинг:** {user_data['rating']} ммр.\n"
                f"📅 **Дата регистрации:** {reg_date_str}"
            )
            return True, info_text

    except Exception as e:
        logger.error(f"Ошибка в get_user_info: {e}")
        return False, "🚨 Произошла ошибка при получении данных из базы."

def is_message_old(update: Update, seconds=10) -> bool:
    message_date = update.message.date
    if datetime.now(message_date.tzinfo) - message_date > timedelta(seconds=seconds):
        print(f"Игнорирую старое сообщение от {message_date}")
        return True
    return False
    
async def register_user(pool, user, nickname: str):
    if not nickname:
        return False, "❌ Введи ник! напрмер: адскийДрочила228"

    if len(nickname) > 100:
        return False, "❌ Слишком длинный никнейм"

    try:
        async with pool.acquire() as conn:
            existing = await conn.fetchrow("SELECT user_id FROM users WHERE user_id = $1", user.id)
            if existing:
                return False, "✨ Ты уже зарегистрирован в боте!"

            username = f"@{user.username}" if user.username else "NoUsername"
            await conn.execute("""
                INSERT INTO users (user_id, username, custom_nickname)
                VALUES ($1, $2, $3)
            """, user.id, username, nickname)
            
            user_link = f"[{nickname}](tg://user?id={user.id})"
            
            return True, f"✅ Регистрация прошла успешно, {user_link}! \nТвои данные переданы в пентагон."
            
    except Exception as e:
        logger.error(f"Ошибка в register_user: {e}")
        return False, "🚨 Произошла ошибка при попытке занести тебя в списки."
            
async def update_nickname(pool, user_id: int, new_nickname: str):
    if not new_nickname:
        return False, "❌ Введи новый ник! Пример: гв ник дрочила228"

    if len(new_nickname) > 100:
        return False, "❌ Слишком длинный никнейм (макс. 100 символов)."

    try:
        async with pool.acquire() as conn:
            existing = await conn.fetchrow("SELECT custom_nickname FROM users WHERE user_id = $1", user_id)
            
            if not existing:
                return False, "⚠️ Ты еще не зарегистрирован! Сначала используй команду гв рег (ник)"

            await conn.execute("""
                UPDATE users 
                SET custom_nickname = $1 
                WHERE user_id = $2
            """, new_nickname, user_id)
            
            user_link = f"[{new_nickname}](tg://user?id={user_id})"
            return True, f"✅ Ник успешно изменен! Теперь ты {user_link}."
            
    except Exception as e:
        logger.error(f"Ошибка в update_nickname: {e}")
        return False, "🚨 Произошла ошибка при смене ника."

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Ошибка: {context.error}")

async def get_rule34_post(update: Update, tags: str, context: ContextTypes.DEFAULT_TYPE):
    global total_requests_count, current_day
    
    USER_ID = "6008643"
    API_KEY = "f3c359dc8d4921981db6be0d99f7cd3eeb298baede968b20f7b2c188bf72d03c77dadb06739e78ffbfb1b1e88061d3b713ae900d8daad6d322740c3e20d179b8"
    MAX_DAILY_LIMIT = 5

    today = date.today()
    if today != current_day:
        total_requests_count = 0
        current_day = today

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
    application.bot_data['db_pool'] = await asyncpg.create_pool(DB_CONFIG)
    print("🐘 Пул PostgreSQL инициализирован")

async def post_shutdown(application: Application):
    session = application.bot_data.get('http_session')
    if session:
        await session.close()
        print("🌐 Сессия закрыта, бот спит крепко.")
    pool = application.bot_data.get('db_pool')
    if pool: await pool.close()

def main():
    app = Application.builder().token(TOKEN).post_init(post_init).post_shutdown(post_shutdown).build()

    app.add_handler(MessageHandler(filters.TEXT | filters.Sticker.ALL, custom_command_handler))
    
    app.add_error_handler(error_handler)

    print("Бот запущен...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
