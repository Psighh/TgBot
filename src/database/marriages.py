import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

#--------------------------------Свадьбы-----------------------------------------------

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