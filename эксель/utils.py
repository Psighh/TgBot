from datetime import datetime, timedelta
from telegram import Update

def calculate_rang(mmr: int) -> str:
    if mmr < 50: return "Рекрут I"
    elif mmr < 100: return "Рекрут II"
    elif mmr < 150: return "Рекрут III"
    elif mmr < 200: return "Рекрут IV"
    elif mmr < 250: return "Рекрут V"

    elif mmr < 300: return "Страж I"
    elif mmr < 400: return "Страж II"
    elif mmr < 500: return "Страж III"
    elif mmr < 600: return "Страж IV"
    elif mmr < 700: return "Страж V"

    elif mmr < 850: return "Рыцарь I"
    elif mmr < 1000: return "Рыцарь II"
    elif mmr < 1150: return "Рыцарь III"
    elif mmr < 1300: return "Рыцарь IV"
    elif mmr < 1450: return "Рыцарь V"

    elif mmr < 1650: return "Герой I"
    elif mmr < 1850: return "Герой II"
    elif mmr < 2050: return "Герой III"
    elif mmr < 2250: return "Герой IV"
    elif mmr < 2450: return "Герой V"

    elif mmr < 2700: return "Легенда I"
    elif mmr < 2950: return "Легенда II"
    elif mmr < 3200: return "Легенда III"
    elif mmr < 3450: return "Легенда IV"
    elif mmr < 3700: return "Легенда V"

    elif mmr < 4000: return "Властелин I"
    elif mmr < 4300: return "Властелин II"
    elif mmr < 4600: return "Властелин III"
    elif mmr < 4900: return "Властелин IV"
    elif mmr < 5200: return "Властелин V"

    elif mmr < 5600: return "Божество I"
    elif mmr < 6000: return "Божество II"
    elif mmr < 6400: return "Божество III"
    elif mmr < 6800: return "Божество IV"
    elif mmr < 7200: return "Божество V"

    else: return "Титан"

def is_message_old(update: Update, seconds=10) -> bool:
    message_date = update.message.date
    if datetime.now(message_date.tzinfo) - message_date > timedelta(seconds=seconds):
        return True
    return False