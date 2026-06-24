from telegram import Update, ReactionTypeEmoji
from telegram.ext import ContextTypes
from utils import is_message_old
import database as db
import services
from config import ALLOWED_MEDICS

# Импорты из соседних файлов 
from .admin import handle_admin_reply_to_suggestion, handle_suggestion_command
from .medical import handle_medic_private_message, handle_medical_question_command
from .marriages import (
    handle_marriage_command,
    handle_divorce_command,
    handle_accept_marriage,
    handle_decline_marriage,
    handle_all_marriages,
)

async def custom_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    user = update.effective_user
    chat = update.effective_chat
    text = update.message.text or "[Стикер/Медиа]"
    pool = context.bot_data.get('db_pool')

    print(f"Сообщение от: {user.first_name} (ID: {user.id}) | Чат: {chat.title or 'Личка'} (ID: {chat.id}) | Текст: {text}")
    
    if update.message.sticker:
        await handle_sticker_reactions(update, context)
        return
        
    if not update.message.text or is_message_old(update):
        return

    # --- Админский инетрфейс --------------------------
    if chat.type == "private" and update.message.reply_to_message:
        if await handle_admin_reply_to_suggestion(update, context):
            return
    # ---------------------------------------------

    if chat.type == "private" and user.id in ALLOWED_MEDICS:
        if await handle_medic_private_message(update, context, pool, text):
            return

    # Начисление MMR за обычные сообщения
    if pool:
        await db.give_mmr(pool, update.effective_user.id, context, update.effective_chat.id, 1)

    message = update.message.text
    if message.lower().startswith("гв "):
        await process_gv_commands(update, context, message[3:].strip().lower())

async def process_gv_commands(update: Update, context: ContextTypes.DEFAULT_TYPE, command: str):
    chat_id = update.effective_chat.id
    pool = context.bot_data.get('db_pool')
    user = update.effective_user

    if command == "хуй":
        await context.bot.send_message(chat_id=chat_id, text="хуй")
        await context.bot.send_sticker(chat_id=chat_id, sticker="CAACAgIAAxkBAAECgzRppxgMyw2pRRTuQE2ewtzhA2EDwwACFmkAAo7ZyEjGsk1U4P9r4zoE")
    #elif command == "кастом":
        # -5160768325 -1002380022509
     #  await context.bot.send_message(chat_id=-1002380022509, text="текст")
    elif command.startswith("медицина"):
        await handle_medical_question_command(update, context, pool, command)
    elif command.startswith("рул"):
        await services.get_rule34_post(update, command[3:].strip().replace(" ", "_"), context)
    elif command.startswith("погода"):
        await services.get_weather(update, command[6:].strip(), context)
    elif command.startswith("рег"):
        success, res = await db.register_user(pool, update.effective_user, command[3:].strip())
        await update.message.reply_text(res, parse_mode="Markdown" if success or "Пример" in res else None)
    elif command.startswith("ник"):
        success, res = await db.update_nickname(pool, update.effective_user.id, command[3:].strip())
        await update.message.reply_text(res, parse_mode="Markdown" if success else None)
    elif command in ['инфа','инфо']:
        success, res = await db.get_user_info(pool, update.effective_user.id)
        await update.message.reply_text(res, parse_mode="Markdown")
    elif command == "топ":
        await handle_top_command(update, context)
    #elif command in ['секс', 'выебать', 'порно']:
    #   await services.handle_intim_command(update, pool)
    elif command == "брак":
        await handle_marriage_command(update, context, pool)    
    elif command == "принять":
        await handle_accept_marriage(update, context, pool)  
    elif command == "отклонить":
        await handle_decline_marriage(update, context)
    elif command == "развод":
        await handle_divorce_command(update, context, pool)
    elif command == "браки": 
        await handle_all_marriages(update, context, pool)
    elif command.startswith("предложение"):  # Говнецо для теста
        await handle_suggestion_command(update, context, pool)
    elif command in ["команда", "команды"]:
        await handle_help_command(update, context)


#-------------------------------------------------Стикеры----------------------------------------------------------------------

async def handle_sticker_reactions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.sticker.file_id == "CAACAgIAAxkBAAIB0GmprRn4W6u5b92a222Lm5mOPYPLAAKrmQAC9UXoS6VAy4587toFOgQ":
        try:
            await context.bot.set_message_reaction(chat_id=update.effective_chat.id, message_id=update.message.message_id, reaction=[ReactionTypeEmoji("❤️")])
        except: pass

#==============================================================СПИСОК КОМАНД==============================================================================
async def handle_help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    help_text = (
        "📖 **Список всех доступных команд бота:**\n\n"
        
        "👤 **Профиль и Рейтинг:**\n"
        "• `гв рег (ник)` — Зарегистрироваться в системе\n"
        "• `гв ник (новый ник)` — Изменить свой текущий никнейм\n"
        "• `гв инфа` / `гв инфо` — Посмотреть карточку своего профиля\n"
        "• `гв топ` — Посмотреть топ-10 пользователей по MMR\n"
        "_(Рейтинг начисляется автоматически за активность в чате)_\n\n"
        
        "💍 **Система Браков:**\n"
        "• `гв брак` — Сделать предложение (использовать ответом на сообщение партнера)\n"
        "• `гв принять` — Принять поступившее предложение руки и сердца\n"
        "• `гв отклонить` — Отклонить предложение\n"
        "• `гв развод` — Расторгнуть текущий брак\n"
        "• `гв браки` — Посмотреть список всех женатых пар в чате\n\n"
        
        "🔬 **Модули и Интерактивы:**\n"
        "• `гв медицина (вопрос)` — Отправить вопрос врачу Виктору\n"
        "• `гв погода (город)` — Узнать актуальную погоду в указанном городе\n"
        "• `гв рул (теги)` — Поиск медиа на Rule34 (Ограничение 180м)\n"
        "• `гв предложение (текст)` — Отправить идею по улучшению бота\n\n"
        
    )
    
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def handle_top_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pool = context.bot_data.get('db_pool')
    rows = await db.get_top_users(pool)
    
    if rows is None:
        await update.message.reply_text("🚨 Произошла ошибка при получении списка лидеров.")
        return
        
    if not rows:
        await update.message.reply_text("📈 Список пуст. Никто еще не зарегистрировался!")
        return

    # Отправляем сообщение-заглушку, пока Pillow собирает картинку
    status_message = await update.message.reply_text("🔄 Собираю топ...")

    try:
        # Генерируем картинку через наш сервис
        image_stream = await services.create_top_image(rows)
        
        # Отправляем её пользователю
        await update.message.reply_photo(
            photo=image_stream,
            caption="🏆 **Актуальный топ пользователей по рейтингу:**",
            parse_mode="Markdown"
        )
        
        # Удаляем заглушку
        await status_message.delete()
        
    except Exception as e:
        print(f"Ошибка при отправке топ-картинки: {e}")
        await status_message.edit_text("🚨 Не удалось сгенерировать изображение топа.")
