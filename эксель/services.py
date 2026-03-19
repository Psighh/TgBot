import random
import json
import logging
import xml.etree.ElementTree as ET
from datetime import date
from config import R34_USER_ID, R34_API_KEY, WEATHER_API_KEY, MAX_DAILY_LIMIT
import database as db

logger = logging.getLogger(__name__)
total_requests_count = 0
current_day = date.today()

async def get_rule34_post(update, tags: str, context):
    pool = context.bot_data.get('db_pool')
    
    total_requests_count = await db.get_r34_count(pool)

    if total_requests_count >= MAX_DAILY_LIMIT:
        await update.message.reply_text(f"🛑 Лимит исчерпан ({total_requests_count}/{MAX_DAILY_LIMIT}). Завтра обновится!")
        return

    wait_message = await update.message.reply_text(f"🔍 Ищу: {tags}... ({total_requests_count + 1}/{MAX_DAILY_LIMIT})")
    session = context.bot_data.get('http_session')

    try:
        params = {
            "page": "dapi", "q": "index", "s": "post", "json": 1, 
            "tags": tags, "limit": 50, "user_id": R34_USER_ID, "api_key": R34_API_KEY
        }
        async with session.get("https://api.rule34.xxx/index.php", params=params, timeout=15) as resp:
            raw_text = await resp.text()
            posts = []
            if raw_text.strip().startswith("["):
                posts = json.loads(raw_text)
            elif "<?xml" in raw_text or "<posts" in raw_text:
                root = ET.fromstring(raw_text)
                for child in root.findall('post'):
                    posts.append({'file_url': child.get('file_url'), 'id': child.get('id')})

            if posts:
                post = random.choice(posts)
                image_url = post.get("file_url")
                if image_url.startswith("//"): image_url = "https:" + image_url
                
                await db.increment_r34_count(pool)
                new_count = total_requests_count + 1
                
                caption = f"🔞 Тег: {tags}\n📊 Лимит: {new_count}/{MAX_DAILY_LIMIT}"
                
                if any(image_url.lower().endswith(ext) for ext in ['.mp4', '.webm']):
                    await update.message.reply_video(video=image_url, caption=caption)
                else:
                    await update.message.reply_photo(photo=image_url, caption=caption)
                
                await wait_message.delete()
            else:
                await wait_message.edit_text(f"😔 По запросу `{tags}` ничего не найдено.")
    except Exception as e:
        logger.error(f"Ошибка в R34: {e}")
        await wait_message.edit_text("Ошибка при поиске.")

async def get_weather(update, city: str, context):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    session = context.bot_data['http_session']
    try:
        async with session.get(url) as resp:
            if resp.status == 200:
                data = await resp.json()
                text = (
                    f"🌍 **Погода в городе {data['name']}**\n"
                    f"🌡 Температура: {data['main']['temp']}°C\n"
                    f"🤔 Ощущается как: {data['main']['feels_like']}°C\n"
                    f"☁️ Описание: {data['weather'][0]['description'].capitalize()}\n"
                    f"💧 Влажность: {data['main']['humidity']}%\n"
                    f"💨 Ветер: {data['wind']['speed']} м/с"
                )
                await update.message.reply_text(text, parse_mode="Markdown")
            elif resp.status == 404:
                await update.message.reply_text(f"❌ Город `{city}` не найден.")
            else:
                await update.message.reply_text("❌ Ошибка при запросе к сервису погоды.")
    except Exception as e:
        await update.message.reply_text("🚨 Произошла ошибка при получении погоды.")

async def handle_intim_command(update, pool):
    if not update.message.reply_to_message:
        await update.message.reply_text("❌ Эту команду нужно использовать в ответ на чье-то сообщение!")
        return

    user = update.effective_user
    target_user = update.message.reply_to_message.from_user

    if user.id == target_user.id:
        await update.message.reply_text("🤔 Самолайк не считается.")
        return

    sender_nick = await db.get_nickname(pool, user.id)
    target_nick = await db.get_nickname(pool, target_user.id)

    if not sender_nick:
        await update.message.reply_text("⚠️ Ты еще не зарегистрирован! Используй: `гв рег (ник)`")
        return

    final_target_name = target_nick if target_nick else target_user.first_name
    
    sender_link = f"[{sender_nick}](tg://user?id={user.id})"
    target_link = f"[{final_target_name}](tg://user?id={target_user.id})"

    intim_text=['сделал(а) королевский минет пользователю',
                'сладко трахнул(а) во все дырочки пользователя',
                'смачно отсосал(а) пользователю',
                'отымел пальчиками пользователя',
                'занялся жарким сексом с',
                'легонько погладил пузико пользователю']

    text = f"👄 {sender_link} {random.choice(intim_text)} {target_link}! ✨"
    await update.message.reply_text(text, parse_mode="Markdown")