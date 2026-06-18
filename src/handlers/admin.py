import re
from telegram import Update
from telegram.ext import ContextTypes
import database as db
from config import OWNER_USER_ID

#==============================================================Админский интерфейс==============================================================================
async def handle_suggestion_command(update: Update, context: ContextTypes.DEFAULT_TYPE, pool):
    from config import OWNER_USER_ID
    user = update.effective_user
    chat = update.effective_chat
    
    full_text = update.message.text
    idx = full_text.lower().find("предложение")
    suggestion = full_text[idx + len("предложение"):].strip()
    
    if not suggestion:
        await update.message.reply_text("❌ Введи текст предложения! Пример: `гв предложение добавить новые аниме-ранги`", parse_mode="Markdown")
        return
        
    u_nick = await db.get_nickname(pool, user.id)
    if not u_nick:
        await update.message.reply_text("⚠️ Ты еще не зарегистрирован! Используй команду: `гв рег (ник)`", parse_mode="Markdown")
        return

    user_link = f"[{u_nick}](tg://user?id={user.id})"
    
    # Формируем сообщение. В конце добавляем скрытый/технический маркер REF
    text_to_owner = (
        f"💡 **Вам новое предложение по улучшению от {user_link}!**\n\n"
        f"{suggestion}\n\n"
        f"🔑 `REF:{chat.id}:{update.message.message_id}`"
    )
    
    try:
        await context.bot.send_message(chat_id=OWNER_USER_ID, text=text_to_owner, parse_mode="Markdown")
        await update.message.reply_text("✅ Твое предложение успешно отправлено разработчику!")
    except Exception as e:
        print(f"Ошибка при отправке предложения владельцу: {e}")
        await update.message.reply_text("⚠️ Не удалось доставить предложение.")

async def handle_admin_reply_to_suggestion(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    from config import OWNER_USER_ID
    
    # Проверяем, что пишет именно создатель бота и это ответ на сообщение
    if update.effective_user.id != OWNER_USER_ID or not update.message.reply_to_message:
        return False
        
    reply = update.message.reply_to_message

    if not reply.text or reply.from_user.id != context.bot.id:
        return False
        
    # Ищем наш маркер REF:chat_id:message_id с помощью регулярного выражения
    match = re.search(r"REF:(-?\d+):(\d+)", reply.text)
    if not match:
        return False 
        
    chat_id = int(match.group(1))
    msg_id = int(match.group(2))
    admin_answer = update.message.text
    
    try:
        text_to_chat = f"📢 **Ответ разработчика:**\n\n{admin_answer}"
        
        await context.bot.send_message(
            chat_id=chat_id,
            text=text_to_chat,
            reply_to_message_id=msg_id,
            parse_mode="Markdown"
        )
        await update.message.reply_text("✅ Ответ успешно отправлен в беседу!")
        return True
    except Exception as e:
        await update.message.reply_text(f"❌ Не удалось доставить ответ в чат. Ошибка: {e}")
        return True
#==============================================================ТЕСТОВАЯ ХЕРНЯ==============================================================================