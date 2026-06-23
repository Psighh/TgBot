import random
import json
import logging
import xml.etree.ElementTree as ET
from datetime import date
from config import R34_USER_ID, R34_API_KEY, WEATHER_API_KEY, MAX_DAILY_LIMIT
import database as db
import html
import io
import os
from PIL import Image, ImageDraw, ImageFont
from config import OWNER_USER_ID

logger = logging.getLogger(__name__)
total_requests_count = 0
current_day = date.today()

async def get_rule34_post(update, tags: str, context):
    user_id = update.effective_user.id
    pool = context.bot_data.get('db_pool')
    session = context.bot_data.get('http_session')

    user_nick = await db.get_nickname(pool, user_id)
    if not user_nick:
        await update.message.reply_text("⚠️ Ты еще не зарегистрирован!")
        return

    safe_nick = html.escape(user_nick)
    user_link = f'<a href="tg://user?id={user_id}">{safe_nick}</a>'
    safe_tags = html.escape(tags)

    total_requests_count = await db.get_r34_count(pool)
    if total_requests_count >= MAX_DAILY_LIMIT:
        await update.message.reply_text(
            f"Общий лимит исчерпан ({total_requests_count}/{MAX_DAILY_LIMIT}).",
            parse_mode="HTML"
        )
        return

    can_use, time_left = await db.check_r34_cooldown(pool, user_id)
    if not can_use:
        await update.message.reply_text(
            f"⏳ {user_link}, подожди еще {time_left} мин.",
            parse_mode="HTML"
        )
        return

    wait_message = await update.message.reply_text(
        f"🔍 Ищу: <b>{safe_tags}</b>... ({total_requests_count + 1}/{MAX_DAILY_LIMIT})",
        parse_mode="HTML"
    )

    try:
        params = {
            "page": "dapi",
            "q": "index",
            "s": "post",
            "json": 1,
            "tags": tags,
            "limit": 50,
            "user_id": R34_USER_ID,
            "api_key": R34_API_KEY
        }

        async with session.get("https://api.rule34.xxx/index.php", params=params, timeout=15) as resp:
            raw_text = await resp.text()
            posts = []

            if raw_text.strip().startswith("["):
                posts = json.loads(raw_text)
            elif "<?xml" in raw_text or "<posts" in raw_text:
                root = ET.fromstring(raw_text)
                for child in root.findall('post'):
                    posts.append({
                        'file_url': child.get('file_url'), 
                        'id': child.get('id')
                    })

            if posts:
                post = random.choice(posts)
                image_url = post.get("file_url")
                
                if image_url.startswith("//"):
                    image_url = "https:" + image_url
                
                new_count = total_requests_count + 1
                caption = (
                    f"{user_link}, ваш запрос по тегу <b>{safe_tags}</b>\n"
                    f"📊 Лимит: {new_count}/{MAX_DAILY_LIMIT}"
                )

                if any(image_url.lower().endswith(ext) for ext in ['.mp4', '.webm']):
                    await update.message.reply_video(
                        video=image_url,
                        caption=caption,
                        parse_mode="HTML"
                    )
                else:
                    await update.message.reply_photo(
                        photo=image_url,
                        caption=caption,
                        parse_mode="HTML"
                    )

                await db.increment_r34_count(pool)
                await db.update_r34_last_time(pool, user_id)
                
                await wait_message.delete()
                
            else:
                await wait_message.edit_text(
                    f"{user_link}, по запросу <b>{safe_tags}</b> ничего не найдено.",
                    parse_mode="HTML"
                )

    except Exception as e:
        logger.error(f"Ошибка в R34: {e}")
        try:
            await wait_message.edit_text("Произошла ошибка при поиске.")
        except:
            pass

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

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

async def create_top_image(rows, admin_ids=None) -> io.BytesIO:
    
    admin_ids = [OWNER_USER_ID]

    template_path = os.path.join(BASE_DIR, "assets", "top_template.png") 
    img = Image.open(template_path)
    draw = ImageDraw.Draw(img)
    
    font_path = os.path.join(BASE_DIR, "assets", "PressStart2P-Regular.ttf")
    font_path2 = os.path.join(BASE_DIR, "assets", "Russische Elsevier.ttf")
    
    try:
        title_font = ImageFont.truetype(font_path, 23)  
        font = ImageFont.truetype(font_path2, 18)        
    except IOError:
        title_font = ImageFont.load_default()
        font = ImageFont.load_default()

    title_text = "Топ пользователей чата"
    title_width = draw.textlength(title_text, font=title_font)
    title_x = int((img.width - title_width) // 2)
    title_y = 40  
    draw.text((title_x, title_y), title_text, fill="lime", font=title_font)

    # Настройки для списка игроков
    start_x = 40      
    start_y = 140      
    line_height = 55   

    for i, row in enumerate(rows, start=1):
        user_id = row.get('user_id') 
        nickname = row['custom_nickname']
        rang = row['rang']
        rating = row['rating']
        
        text = f"{i}. {nickname} [{rang}] — {rating} ммр"
        current_y = start_y + (i - 1) * line_height
        
        # Рисуем строку игрока
        draw.text((start_x, current_y), text, fill="red", font=font, stroke_width=0.5, stroke_fill="red")
        
        text_width = draw.textlength(text, font=font)
        current_icon_x = int(start_x + text_width + 8)
        
        # --- 1. ОТРИСОВКА МЕДАЛИ ---
        rang_base = rang.split()[0] if rang else "Рекрут"
        medal_path = os.path.join(BASE_DIR, "assets", "medals", f"{rang_base}.png")
        
        if os.path.exists(medal_path):
            try:
                medal = Image.open(medal_path)
                medal_size = (30, 30)
                if medal.size != medal_size:
                    medal = medal.resize(medal_size, Image.Resampling.LANCZOS)
                
                medal_y = current_y - 4 
                img.paste(medal, (current_icon_x, medal_y), medal)
                
                current_icon_x += 35
            except Exception as e:
                print(f"Не удалось отрисовать медаль для {rang_base}: {e}")

        # --- 2. ОТРИСОВКА ЗНАЧКА АДМИНИСТРАТОРА ---
        if user_id in admin_ids:
            admin_icon_path = os.path.join(BASE_DIR, "assets", "medals", "Админ.png")
            if os.path.exists(admin_icon_path):
                try:
                    admin_icon = Image.open(admin_icon_path)
                    admin_size = (30, 30)  
                    if admin_icon.size != admin_size:
                        admin_icon = admin_icon.resize(admin_size, Image.Resampling.LANCZOS)
                    
                    admin_y = current_y - 4
                    img.paste(admin_icon, (current_icon_x, admin_y), admin_icon)
                    
                    current_icon_x += 35
                except Exception as e:
                    print(f"Не удалось отрисовать значок админа: {e}")

    image_buffer = io.BytesIO()
    image_buffer.name = 'top_leaderboard.png'
    img.save(image_buffer, format='PNG')
    image_buffer.seek(0)
    
    return image_buffer