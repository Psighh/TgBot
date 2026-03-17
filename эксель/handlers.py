from telegram import Update, ReactionTypeEmoji
from telegram.ext import ContextTypes
from utils import is_message_old
import database as db
import services

async def custom_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        user = update.effective_user
        chat = update.effective_chat
        text = update.message.text or "[Стикер/Медиа]"
        print(f"Сообщение от: {user.first_name} (ID: {user.id}) | Чат: {chat.title or 'Личка'} (ID: {chat.id}) | Текст: {text}")
    if update.message.sticker:
        await handle_sticker_reactions(update, context)
        return
    if not update.message.text or is_message_old(update):
        return
    pool = context.bot_data.get('db_pool')
    if pool:
        await db.give_mmr(pool, update.effective_user.id, context, update.effective_chat.id, 1)
    message = update.message.text
    if message.lower().startswith("гв "):
        await process_gv_commands(update, context, message[3:].strip().lower())

async def process_gv_commands(update: Update, context: ContextTypes.DEFAULT_TYPE, command: str):
    chat_id = update.effective_chat.id
    pool = context.bot_data.get('db_pool')

    if command == "хуй":
        await context.bot.send_message(chat_id=chat_id, text="хуй")
        await context.bot.send_sticker(chat_id=chat_id, sticker="CAACAgIAAxkBAAECgzRppxgMyw2pRRTuQE2ewtzhA2EDwwACFmkAAo7ZyEjGsk1U4P9r4zoE")
    #elif command == "кастом":
    #   await context.bot.send_sticker(chat_id=-1002380022509, sticker="CAACAgIAAxkBAAECqyVpsyLE9BVggzEPYwRTVaBfsceDGQACwGcAAuu_kEgISLE2EPhp8ToE")
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
        res = await db.get_top_users(pool)
        await update.message.reply_text(res, parse_mode="Markdown", disable_web_page_preview=True)

async def handle_sticker_reactions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.sticker.file_id == "CAACAgIAAxkBAAIB0GmprRn4W6u5b92a222Lm5mOPYPLAAKrmQAC9UXoS6VAy4587toFOgQ":
        try:
            await context.bot.set_message_reaction(chat_id=update.effective_chat.id, message_id=update.message.message_id, reaction=[ReactionTypeEmoji("❤️")])
        except: pass