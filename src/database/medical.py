# -*- coding: utf-8 -*-
import logging
from typing import Optional, List, Dict, Any

# Инициализируем логгер для медицинского модуля
logger = logging.getLogger(__name__)

#--------------------------------Медицина-----------------------------------------------

async def add_medical_question(pool, user_id: int, chat_id: int, question: str):
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO medical_questions (user_id, chat_id, question_text) VALUES ($1, $2, $3)",
            user_id, chat_id, question
        )

async def get_all_medical_questions(pool):
    async with pool.acquire() as conn:
        return await conn.fetch("SELECT id, user_id, chat_id, question_text FROM medical_questions ORDER BY id ASC")

async def get_medical_question_by_id(pool, q_id: int):
    async with pool.acquire() as conn:
        return await conn.fetchrow("SELECT id, user_id, chat_id, question_text FROM medical_questions WHERE id = $1", q_id)

async def delete_medical_question(pool, q_id: int):
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM medical_questions WHERE id = $1", q_id)

async def ban_user_medical(pool, user_id: int):
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO medical_bans (user_id, banned_until)
            VALUES ($1, NOW() + INTERVAL '1 day')
            ON CONFLICT (user_id) DO UPDATE 
            SET banned_until = EXCLUDED.banned_until;
            """,
            user_id
        )

async def is_medical_banned(pool, user_id: int) -> bool:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT banned_until FROM medical_bans WHERE user_id = $1 AND banned_until > NOW()",
            user_id
        )
        return row is not None