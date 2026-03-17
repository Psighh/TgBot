from datetime import datetime, timedelta
from telegram import Update

def calculate_rang(mmr: int) -> str:
    if mmr < 50: return "Рекрут I"
    elif mmr < 100: return "Рекрут II"
    elif mmr < 150: return "Рекрут III"
    elif mmr < 200: return "Рекрут IV"
    elif mmr < 250: return "Рекрут V"

    elif mmr < 300: return "Страж I"
    elif mmr < 375: return "Страж II"
    elif mmr < 450: return "Страж III"
    elif mmr < 525: return "Страж IV"
    elif mmr < 600: return "Страж V"

    elif mmr < 700: return "Рыцарь I"
    elif mmr < 800: return "Рыцарь II"
    elif mmr < 900: return "Рыцарь III"
    elif mmr < 1000: return "Рыцарь IV"
    elif mmr < 1100: return "Рыцарь V"

    elif mmr < 1200: return "Герой I"
    elif mmr < 1300: return "Герой II"
    elif mmr < 1400: return "Герой III"
    elif mmr < 1500: return "Герой IV"
    elif mmr < 1600: return "Герой V"

    elif mmr < 1700: return "Легенда I"
    elif mmr < 1800: return "Легенда II"
    elif mmr < 1900: return "Легенда III"
    elif mmr < 2000: return "Легенда IV"
    elif mmr < 2100: return "Легенда V"

    elif mmr < 2200: return "Властелин I"
    elif mmr < 2300: return "Властелин II"
    elif mmr < 2400: return "Властелин III"
    elif mmr < 2500: return "Властелин IV"
    elif mmr < 2600: return "Властелин V"

    elif mmr < 2800: return "Божество I"
    elif mmr < 3000: return "Божество II"
    elif mmr < 3200: return "Божество III"
    elif mmr < 3400: return "Божество IV"
    elif mmr < 3600: return "Божество V"

    else: return "Титан"

def is_message_old(update: Update, seconds=10) -> bool:
    message_date = update.message.date
    if datetime.now(message_date.tzinfo) - message_date > timedelta(seconds=seconds):
        return True
    return False