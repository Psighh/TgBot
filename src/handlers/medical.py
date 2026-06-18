from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import database as db
from config import ALLOWED_MEDICS

#-------------------------------------------------Медицина----------------------------------------------------------------------

async def handle_medic_private_message(update: Update, context: ContextTypes.DEFAULT_TYPE, pool, text: str) -> bool:
    """
    Обрабатывает сообщения от вити в личных сообщениях.
    Возвращает True, если сообщение было обработано и выполнение нужно прервать.
    """
    waiting_info = context.user_data.get('waiting_for_answer_to')
    
    # Если бот ожидает от медика текст ответа на вопрос
    if waiting_info:
        if text.strip().lower() == "отмена":
            context.user_data.pop('waiting_for_answer_to', None)
            await update.message.reply_text("❌ Отменено.")
            await show_medical_question_interface(update, context, pool, current_index=waiting_info['current_index'])
            return True
            
        await handle_medic_answer_text(update, context, pool, waiting_info)
        return True

    # Если медик нажимает кнопки интерфейса управления
    if text.strip().lower() in ["/start", "вопросы"]:
        reply_markup = ReplyKeyboardMarkup([["Вопросы"]], resize_keyboard=True)
        if text.strip().lower() == "вопросы":
            await show_medical_question_interface(update, context, pool)
        else:
            await update.message.reply_text("Нажми на кнопку «Вопросы», чтобы просмотреть очередь.", reply_markup=reply_markup)
        return True

    # Если ни одно условие не подошло (например, медик просто пишет обычный текст)
    return False

async def handle_medical_question_command(update: Update, context: ContextTypes.DEFAULT_TYPE, pool, command: str):
    user = update.effective_user
    chat_id = update.effective_chat.id
    question = command[8:].strip()
    
    if not question:
        await update.message.reply_text("Введи вопрос!", parse_mode="Markdown")
        return
        
    u_nick = await db.get_nickname(pool, user.id)
    if not u_nick:
        await update.message.reply_text("⚠️ Ты еще не зарегистрирован! Используй команду: `гв рег (ник)`", parse_mode="Markdown")
        return

    if await db.is_medical_banned(pool, user.id):
        await update.message.reply_text("⛔ Вы находитесь в бане")
        return
        
    await db.add_medical_question(pool, user.id, chat_id, question)
    await update.message.reply_text("Твой вопрос записан и передан Виктору!")

async def show_medical_question_interface(update: Update, context: ContextTypes.DEFAULT_TYPE, pool, current_index: int = 0, edit_message_id: int = None):
    questions = await db.get_all_medical_questions(pool)
    chat_id = update.effective_chat.id
    
    if not questions:
        text = "🎉 **Вопросов пока нет или кончились!**"
        if edit_message_id:
            await context.bot.edit_message_text(chat_id=chat_id, message_id=edit_message_id, text=text, parse_mode="Markdown")
        else:
            await context.bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
        return

    # Зацикливаем индекс, если дошли до конца списка
    if current_index >= len(questions) or current_index < 0:
        current_index = 0
        
    q = questions[current_index]
    asker_nick = await db.get_nickname(pool, q['user_id']) or "Аноним"
    
    text = (
        f"🩺 **Вопрос №{current_index + 1} из {len(questions)}**\n"
        f"👤 **От кого:** [{asker_nick}](tg://user?id={q['user_id']})\n"
        f"❓ **Вопрос:** {q['question_text']}"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("Ответить", callback_data=f"med_ans_{q['id']}_{current_index}"),
            InlineKeyboardButton("Следующий вопрос", callback_data=f"med_next_{current_index + 1}")
        ],
        [
            InlineKeyboardButton("Удалить вопрос", callback_data=f"med_del_{q['id']}_{current_index}"),
            InlineKeyboardButton("Бан", callback_data=f"med_ban_{q['id']}_{current_index}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if edit_message_id:
        try:
            await context.bot.edit_message_text(chat_id=chat_id, message_id=edit_message_id, text=text, reply_markup=reply_markup, parse_mode="Markdown")
        except Exception:
            pass 
    else:
        await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode="Markdown")

async def medical_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id not in ALLOWED_MEDICS:
        return

    pool = context.bot_data.get('db_pool')
    data = query.data
    
    if data.startswith("med_next_"):
        next_index = int(data.split("_")[2])
        await show_medical_question_interface(update, context, pool, current_index=next_index, edit_message_id=query.message.message_id)
        
    elif data.startswith("med_ans_"):
        _, _, q_id, current_index = data.split("_")
        q_id, current_index = int(q_id), int(current_index)
        
        q = await db.get_medical_question_by_id(pool, q_id)
        if not q:
            await query.message.edit_text("⚠️ На этот вопрос уже ответили или он был удален.")
            return
            
        context.user_data['waiting_for_answer_to'] = {
            "q_id": q_id,
            "current_index": current_index,
            "message_id": query.message.message_id
        }
        
        asker_nick = await db.get_nickname(pool, q['user_id']) or "Аноним"

        keyboard = [[InlineKeyboardButton("Отмена", callback_data=f"med_cancel_{current_index}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.message.edit_text(
            f"✏️ **Пишем ответ для {asker_nick}:**\n"
            f"» *{q['question_text']}*\n\n"
            f"Введите текст ответа следующим сообщением",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    elif data.startswith("med_cancel_"):
        current_index = int(data.split("_")[2])
        
        context.user_data.pop('waiting_for_answer_to', None)
        
        await show_medical_question_interface(update, context, pool, current_index=current_index, edit_message_id=query.message.message_id)
    elif data.startswith("med_del_"):
        _, _, q_id, current_index = data.split("_")
        q_id, current_index = int(q_id), int(current_index)
        
        q = await db.get_medical_question_by_id(pool, q_id)
        if q:
            user_id = q['user_id']
            await db.delete_medical_question(pool, q_id)
            try:
                await context.bot.send_message(chat_id=user_id, text="Ваш вопрос удалён и не получил ответа")
            except Exception as e:
                print(f"Не удалось отправить уведомление об удалении пользователю {user_id}: {e}")
                
        await show_medical_question_interface(update, context, pool, current_index=current_index, edit_message_id=query.message.message_id)

    elif data.startswith("med_ban_"):
        _, _, q_id, current_index = data.split("_")
        q_id, current_index = int(q_id), int(current_index)
        
        q = await db.get_medical_question_by_id(pool, q_id)
        if q:
            user_id = q['user_id']
            await db.ban_user_medical(pool, user_id)
            await db.delete_medical_question(pool, q_id)
            try:
                await context.bot.send_message(chat_id=user_id, text="Ваш вопрос удалён, и вы получили блокировку в медицинском модуле на 1 день.")
            except Exception as e:
                print(f"Не удалось отправить уведомление о бане пользователю {user_id}: {e}")
                
        await show_medical_question_interface(update, context, pool, current_index=current_index, edit_message_id=query.message.message_id)

async def handle_medic_answer_text(update: Update, context: ContextTypes.DEFAULT_TYPE, pool, waiting_info: dict):
    q_id = waiting_info['q_id']
    current_index = waiting_info['current_index']
    answer_text = update.message.text

    q = await db.get_medical_question_by_id(pool, q_id)
    if not q:
        await update.message.reply_text("❌ Ошибка: вопрос не найден в базе данных.")
        context.user_data.pop('waiting_for_answer_to', None)
        return

    user_id = q['user_id']
    chat_id = q['chat_id']  

    try:
        notification = (
            f"🩺 **Поступил ответ от Виктора!**\n\n"
            f"❓ **Твой вопрос:** {q['question_text']}\n"
            f"💡 **Ответ:** {answer_text}"
        )
        await context.bot.send_message(chat_id=user_id, text=notification, parse_mode="Markdown")
        user_sent = True
    except Exception as e:
        user_sent = False
        print(f"Не удалось отправить ответ в ЛС пользователю {user_id}: {e}")

    if chat_id and chat_id != user_id:
        try:
            asker_nick = await db.get_nickname(pool, user_id) or "Пользователь"
            asker_link = f"[{asker_nick}](tg://user?id={user_id})"
            
            group_notification = (
                f"🩺 **Виктор ответил на медицинский вопрос пользователя {asker_link}!**\n\n"
                f"❓ **Вопрос:** {q['question_text']}\n"
                f"💡 **Ответ:** {answer_text}"
            )
            await context.bot.send_message(chat_id=chat_id, text=group_notification, parse_mode="Markdown")
        except Exception as e:
            print(f"Не удалось отправить ответ в беседу {chat_id}: {e}")

    await db.delete_medical_question(pool, q_id)
    context.user_data.pop('waiting_for_answer_to', None)

    if user_sent:
        await update.message.reply_text("Ответ отправлен, вопрос удалён")
    else:
        await update.message.reply_text("⚠️ Не удалось доставить ответ в ЛС (Видимо, у пользователя нет ЛС с ботом.)")

    # Показываем интерфейс со следующим вопросом
    await show_medical_question_interface(update, context, pool, current_index=current_index)