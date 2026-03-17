import aiohttp
import asyncpg
from telegram import Update
from telegram.ext import Application, ContextTypes
from config import DB_CONFIG
from handlers import custom_command_handler

network_error_active = False

async def post_init(application: Application):
    application.bot_data['http_session'] = aiohttp.ClientSession()
    print("HTTP соединение создано")
    application.bot_data['db_pool'] = await asyncpg.create_pool(DB_CONFIG)
    print("БД синхронизирована")
    print("Бот запущен...")

async def post_shutdown(application: Application):
    if application.bot_data.get('http_session'): 
        await application.bot_data['http_session'].close()
    if application.bot_data.get('db_pool'): 
        await application.bot_data['db_pool'].close()
    print("Соединения закрыты. Бот остановлен.")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    global network_error_active
    if "httpx" in str(context.error):
        if not network_error_active:
            print("Сетевая ошибка: Потеряно соединение. Ожидаю восстановления...")
            network_error_active = True
    else:
        print(f"Произошла ошибка: {context.error}")

async def check_network_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global network_error_active
    if network_error_active:
        print("Соединение восстановлено! Бот снова в строю.")
        network_error_active = False
    
    await custom_command_handler(update, context)