import random
import json
import logging
import xml.etree.ElementTree as ET
from datetime import date
from config import R34_USER_ID, R34_API_KEY, WEATHER_API_KEY, MAX_DAILY_LIMIT

logger = logging.getLogger(__name__)
total_requests_count = 0
current_day = date.today()

async def get_rule34_post(update, tags: str, context):
    global total_requests_count, current_day
    today = date.today()
    if today != current_day:
        total_requests_count = 0
        current_day = today

    if total_requests_count >= MAX_DAILY_LIMIT:
        await update.message.reply_text(f"🛑 Лимит исчерпан ({total_requests_count}/{MAX_DAILY_LIMIT}). Завтра обновится!")
        return

    wait_message = await update.message.reply_text(f"🔍 Ищу: {tags}... ({total_requests_count + 1}/{MAX_DAILY_LIMIT})")
    session = context.bot_data.get('http_session')

    try:
        params = {"page": "dapi", "q": "index", "s": "post", "json": 1, "tags": tags, "limit": 50, "user_id": R34_USER_ID, "api_key": R34_API_KEY}
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
        await wait_message.edit_text("🚨 Ошибка при поиске.")

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