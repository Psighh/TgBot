import os
from dotenv import load_dotenv

# Загружаем переменные из файла .env, если он существует (для локального запуска на ПК)
load_dotenv()

# Токен Telegram-бота
TOKEN = os.getenv("BOT_TOKEN")

# Конфигурация базы данных PostgreSQL
DB_CONFIG = os.getenv("DB_CONFIG", "postgresql://postgres:123123@localhost:5432/postgres")

# Настройки Rule34
R34_USER_ID = os.getenv("R34_USER_ID", "6008643")
R34_API_KEY = os.getenv("R34_API_KEY")
MAX_DAILY_LIMIT = int(os.getenv("MAX_DAILY_LIMIT", "25"))

# API погоды
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

# Настройки для медицинского модуля
MEDIC_USER_ID = int(os.getenv("MEDIC_USER_ID", "1419988089"))
OWNER_USER_ID = int(os.getenv("OWNER_USER_ID", "5533189172"))

# Список разрешенных медиков (передаем через запятую в env, например: "123,456")
allowed_medics_raw = os.getenv("ALLOWED_MEDICS")
if allowed_medics_raw:
    ALLOWED_MEDICS = [int(x.strip()) for x in allowed_medics_raw.split(",") if x.strip().isdigit()]
else:
    ALLOWED_MEDICS = [MEDIC_USER_ID]