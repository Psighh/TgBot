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
    """
    Генерирует изображение лидерборда на основе чистого шаблона.
    Цвета: ТОП-1 (Золото), ТОП-2 (Серебро), ТОП-3 (Медь). ТОП 4-10 (Белый).
    Ранги и ММР у всех позиций — бирюзовые. ТОП 1-3 выделены жирным.
    """
    # Если список админов не передан, берем по умолчанию OWNER_USER_ID
    admin_ids = [OWNER_USER_ID]

    # Путь к шаблону top_template.png
    template_path = os.path.join(BASE_DIR, "assets", "top_template.png") 
    img = Image.open(template_path)
    draw = ImageDraw.Draw(img)
    
    font_path_regular = os.path.join(BASE_DIR, "assets", "PoppinsCyr-Regular.otf")
    
    try:
        font = ImageFont.truetype(font_path_regular, 25)   
    except IOError:
        logger.warning("Не удалось найти шрифт Poppins-Regular.ttf в папки assets. Используется стандартный.")
        font = ImageFont.load_default()

    # Исходные отступы и размеры (оставлены без изменений)
    start_x = 80      
    start_y = 275     
    line_height = 65  

    # Палитра цветов
    color_white = "white"
    color_gold = "gold"
    color_silver = "#B5B8B1"     # Насыщенный серебряный
    color_bronze = "#CD7F32"     # Медный / Бронзовый
    color_turquoise = "#00E5FF"  # Яркий бирюзовый

    for i, row in enumerate(rows, start=1):
        user_id = row.get('user_id') 
        nickname = row['custom_nickname']
        rang = row['rang']
        rating = row['rating']
        
        # Формируем кусочки текста для раздельной раскраски
        idx_text = f"{i}. "
        nick_text = f"{nickname} "
        rang_text = f"[{rang}] "
        mmr_text = f"— {rating} ммр"
        
        current_y = start_y + (i - 1) * line_height
        current_x = start_x
        
        # Динамически определяем цвет ника/номера и толщину шрифта (жирность)
        if i == 1:
            main_color = color_gold
            stroke = 1
        elif i == 2:
            main_color = color_silver
            stroke = 1
        elif i == 3:
            main_color = color_bronze
            stroke = 1
        else:
            main_color = color_white
            stroke = 0
        
        # 1. Рисуем Номер позиции
        draw.text((current_x, current_y), idx_text, fill=main_color, font=font, stroke_width=stroke, stroke_fill=main_color)
        current_x += draw.textlength(idx_text, font=font)
        
        # 2. Рисуем Никнейм
        draw.text((current_x, current_y), nick_text, fill=main_color, font=font, stroke_width=stroke, stroke_fill=main_color)
        current_x += draw.textlength(nick_text, font=font)
        
        # 3. Рисуем Ранг (Бирюзовый для всех, жирный для 1-3 мест)
        draw.text((current_x, current_y), rang_text, fill=color_turquoise, font=font, stroke_width=stroke, stroke_fill=color_turquoise)
        current_x += draw.textlength(rang_text, font=font)
        
        # 4. Рисуем ММР (Бирюзовый для всех, жирный для 1-3 мест)
        draw.text((current_x, current_y), mmr_text, fill=color_turquoise, font=font, stroke_width=stroke, stroke_fill=color_turquoise)
        current_x += draw.textlength(mmr_text, font=font)
        
        # Координата X для первой иконки (с небольшим отступом от текста)
        current_icon_x = int(current_x + 12)
        icon_y = current_y - 6  # Центрирование иконок относительно базовой линии текста
        
        # --- БЛОК 1: ОТРИСОВКА МЕДАЛИ РАНГА ---
        rang_base = rang.split()[0] if rang else "Рекрут"
        medal_path = os.path.join(BASE_DIR, "assets", "medals", f"{rang_base}.png")
        
        if os.path.exists(medal_path):
            try:
                medal = Image.open(medal_path)
                medal_size = (32, 32)  # Оптимальный размер медалей
                if medal.size != medal_size:
                    medal = medal.resize(medal_size, Image.Resampling.LANCZOS)
                
                img.paste(medal, (current_icon_x, icon_y), medal)
                current_icon_x += 38  # Сдвигаем позицию для следующей иконки
            except Exception as e:
                if 'logger' in globals():
                    logger.error(f"Ошибка отрисовки медали {rang_base}: {e}")
                else:
                    print(f"Ошибка отрисовки медали {rang_base}: {e}")

        # --- БЛОК 2: ОТРИСОВКА ЗНАЧКА АДМИНИСТРАТОРА (ЛЯМБДЫ) ---
        if user_id in admin_ids:
            admin_icon_path = os.path.join(BASE_DIR, "assets", "medals", "Админ.png")
            if os.path.exists(admin_icon_path):
                try:
                    admin_icon = Image.open(admin_icon_path)
                    admin_size = (32, 32)  
                    if admin_icon.size != admin_size:
                        admin_icon = admin_icon.resize(admin_size, Image.Resampling.LANCZOS)
                    
                    img.paste(admin_icon, (current_icon_x, icon_y), admin_icon)
                except Exception as e:
                    if 'logger' in globals():
                        logger.error(f"Ошибка отрисовки значка админа: {e}")
                    else:
                        print(f"Ошибка отрисовки значка админа: {e}")

    # Сохранение готового изображения в буфер для отправки в Telegram
    image_buffer = io.BytesIO()
    image_buffer.name = 'top_leaderboard.png'
    img.save(image_buffer, format='PNG')
    image_buffer.seek(0)
    
    return image_buffer