import logging
from utils import calculate_rang

logger = logging.getLogger(__name__)

async def give_mmr(pool, user_id: int, context, chat_id: int, amount: int = 1):
    try:
        async with pool.acquire() as conn:
            current_data = await conn.fetchrow(
                "SELECT rating, rang, custom_nickname FROM users WHERE user_id = $1", user_id
            )
            if not current_data: return False

            old_rang = current_data['rang']
            new_mmr = int(current_data['rating']) + amount
            new_rang = calculate_rang(new_mmr)
            nickname = current_data['custom_nickname']

            await conn.execute("UPDATE users SET rating = $1, rang = $2 WHERE user_id = $3", new_mmr, new_rang, user_id)
            
            if old_rang != new_rang:
                user_link = f"[{nickname}](tg://user?id={user_id})"
                congrats_text = (
                    f"🎖Поздравляю, {user_link}, ты теперь: **{new_rang}**!\n"
                    f"Твой рейтинг: {new_mmr} ммр."
                )
                await context.bot.send_message(chat_id=chat_id, text=congrats_text, parse_mode="Markdown")
            return True
    except Exception as e:
        logger.error(f"Ошибка в give_mmr: {e}")
        return False

async def get_top_users(pool):
    try:
        async with pool.acquire() as conn:
            rows = await conn.fetch("SELECT user_id, custom_nickname, rang, rating FROM users ORDER BY rating DESC LIMIT 10")
            if not rows: return "📈 Список пуст. Никто еще не зарегистрировался!"
            text = "🏆 **Топ пользователей по рейтингу:**\n\n"
            for i, row in enumerate(rows, start=1):
                user_link = f"[{row['custom_nickname']}](tg://user?id={row['user_id']})"
                text += f"{i}. {user_link} [[{row['rang']}]] — {row['rating']} ммр.\n"
            return text
    except Exception as e:
        return "🚨 Произошла ошибка при получении списка лидеров."

async def register_user(pool, user, nickname: str):
    if not nickname: return False, "❌ Введи ник! напрмер: адскийДрочила228"
    if len(nickname) > 100: return False, "❌ Слишком длинный никнейм"
    try:
        async with pool.acquire() as conn:
            existing = await conn.fetchrow("SELECT user_id FROM users WHERE user_id = $1", user.id)
            if existing: return False, "✨ Ты уже зарегистрирован в боте!"
            username = f"@{user.username}" if user.username else "NoUsername"
            await conn.execute("INSERT INTO users (user_id, username, custom_nickname) VALUES ($1, $2, $3)", user.id, username, nickname)
            user_link = f"[{nickname}](tg://user?id={user.id})"
            return True, f"✅ Регистрация прошла успешно, {user_link}! \nТвои данные переданы в пентагон."
    except Exception as e:
        return False, "🚨 Произошла ошибка при попытке занести тебя в списки."

async def update_nickname(pool, user_id: int, new_nickname: str):
    if not new_nickname: return False, "❌ Введи новый ник! Пример: гв ник дрочила228"
    if len(new_nickname) > 100: return False, "❌ Слишком длинный никнейм (макс. 100 символов)."
    try:
        async with pool.acquire() as conn:
            existing = await conn.fetchrow("SELECT custom_nickname FROM users WHERE user_id = $1", user_id)
            if not existing: return False, "⚠️ Ты еще не зарегистрирован! Сначала используй команду гв рег (ник)"
            await conn.execute("UPDATE users SET custom_nickname = $1 WHERE user_id = $2", new_nickname, user_id)
            user_link = f"[{new_nickname}](tg://user?id={user_id})"
            return True, f"✅ Ник успешно изменен! Теперь ты {user_link}."
    except Exception as e:
        return False, "🚨 Произошла ошибка при смене ника."

async def get_user_info(pool, user_id: int):
    try:
        async with pool.acquire() as conn:
            user_data = await conn.fetchrow("SELECT custom_nickname, rang, rating, registered_at FROM users WHERE user_id = $1", user_id)
            if not user_data: return False, "⚠️ Ты еще не зарегистрирован! Используй: гв рег (ник)"
            reg_date_str = user_data['registered_at'].strftime("%d.%m.%Y") if user_data['registered_at'] else "Неизвестно"
            user_link = f"[{user_data['custom_nickname']}](tg://user?id={user_id})"
            info_text = (f"👤 **Твой профиль:**\n🏷 **Ник:** {user_link}\n🎖 **Ранг:** {user_data['rang']}\n🏆 **Рейтинг:** {user_data['rating']} ммр.\n📅 **Дата регистрации:** {reg_date_str}")
            return True, info_text
    except Exception as e:
        return False, "🚨 Произошла ошибка при получении данных из базы."

async def get_nickname(pool, user_id: int):
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT custom_nickname FROM users WHERE user_id = $1::BIGINT", user_id)
        return row['custom_nickname'] if row else None

async def get_marriage(pool, user_id: int):
    async with pool.acquire() as conn:
        return await conn.fetchrow(
            "SELECT * FROM marriages WHERE user_one_id = $1::BIGINT OR user_two_id = $1::BIGINT", 
            user_id
        )

async def create_marriage(pool, user_one: int, user_two: int, chat_id: int):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO marriages (user_one_id, user_two_id, chat_id) 
            VALUES (
                LEAST($1::BIGINT, $2::BIGINT), 
                GREATEST($1::BIGINT, $2::BIGINT), 
                $3::BIGINT
            )
            """,
            user_one, user_two, chat_id
        )

async def delete_marriage(pool, user_id: int):
    async with pool.acquire() as conn:
        result = await conn.execute(
            "DELETE FROM marriages WHERE user_one_id = $1::BIGINT OR user_two_id = $1::BIGINT", 
            user_id
        )
        return result == "DELETE 1"

async def get_all_marriages(pool):
    query = """
        SELECT 
            m.user_one_id, 
            m.user_two_id, 
            u1.custom_nickname as nick_one, 
            u2.custom_nickname as nick_two,
            (CURRENT_DATE - m.married_at::date) as days_together
        FROM marriages m
        JOIN users u1 ON m.user_one_id = u1.user_id
        JOIN users u2 ON m.user_two_id = u2.user_id
        ORDER BY days_together DESC
    """
    async with pool.acquire() as conn:
        return await conn.fetch(query)