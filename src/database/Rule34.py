# -*- coding: utf-8 -*-
import logging
from datetime import datetime, date, timedelta

# Инициализируем логгер для модуля Rule34
logger = logging.getLogger(__name__)

#--------------------------------рул34-----------------------------------------------

async def get_r34_count(pool):
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT value_int, last_update FROM bot_settings WHERE key = 'r34_requests_count'")
        
        if row['last_update'].date() != date.today():
            await conn.execute(
                "UPDATE bot_settings SET value_int = 0, last_update = CURRENT_DATE WHERE key = 'r34_requests_count'"
            )
            return 0
        return row['value_int']

async def increment_r34_count(pool):
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE bot_settings SET value_int = value_int + 1 WHERE key = 'r34_requests_count'"
        )

async def check_r34_cooldown(pool, user_id: int):
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT last_r34_at FROM users WHERE user_id = $1::BIGINT", 
            user_id
        )
        if not row or not row['last_r34_at']:
            return True, 0 

        last_time = row['last_r34_at']
        now = datetime.now()
        diff = now - last_time

        if diff < timedelta(minutes=180):
            remaining = 180 - int(diff.total_seconds() / 60)
            return False, remaining
        
        return True, 0

async def update_r34_last_time(pool, user_id: int):
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET last_r34_at = NOW() WHERE user_id = $1::BIGINT", 
            user_id
        )