from telegram import Update, ReactionTypeEmoji, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from utils import is_message_old
import database as db
import services
from config import ALLOWED_MEDICS

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
        res = await db.get_top_users(pool)
        await update.message.reply_text(res, parse_mode="Markdown", disable_web_page_preview=True)
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

#-------------------------------------------------Стикеры----------------------------------------------------------------------

async def handle_sticker_reactions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.sticker.file_id == "CAACAgIAAxkBAAIB0GmprRn4W6u5b92a222Lm5mOPYPLAAKrmQAC9UXoS6VAy4587toFOgQ":
        try:
            await context.bot.set_message_reaction(chat_id=update.effective_chat.id, message_id=update.message.message_id, reaction=[ReactionTypeEmoji("❤️")])
        except: pass

#-------------------------------------------------Свадьбы----------------------------------------------------------------------

async def handle_marriage_command(update: Update, context: ContextTypes.DEFAULT_TYPE, pool):
    user = update.effective_user
    chat_id = update.effective_chat.id

    if not update.message.reply_to_message:
        await update.message.reply_text("Нужно ответить на чье-то сообщение.")
        return

    target_user = update.message.reply_to_message.from_user
    if user.id == target_user.id:
        await update.message.reply_text("🤔 Жениться на самом себе нельзя.")
        return

    u1_nick = await db.get_nickname(pool, user.id)
    u2_nick = await db.get_nickname(pool, target_user.id)

    if not u1_nick:
        await update.message.reply_text("Ты еще не зарегистрирован!")
        return
    if not u2_nick:
        await update.message.reply_text(f"{target_user.first_name} еще не зарегистрирован в боте.")
        return

    if await db.get_marriage(pool, user.id):
        await update.message.reply_text("Ты уже в браке! Сначала разведись.")
        return
    if await db.get_marriage(pool, target_user.id):
        await update.message.reply_text(f"{u2_nick} уже в браке")
        return

    if 'marriage_proposals' not in context.chat_data:
        context.chat_data['marriage_proposals'] = {}
    
    context.chat_data['marriage_proposals'][target_user.id] = user.id

    u1_link = f"[{u1_nick}](tg://user?id={user.id})"
    u2_link = f"[{u2_nick}](tg://user?id={target_user.id})"

    await update.message.reply_text(
        f"💍 {u2_link}, хочешь ли ты вступить в брак с {u1_link}?\n"
        f"Напиши **Гв принять**, либо **Гв отклонить**.",
        parse_mode="Markdown"
    )

async def handle_divorce_command(update: Update, context: ContextTypes.DEFAULT_TYPE, pool):
    user = update.effective_user
    u_nick = await db.get_nickname(pool, user.id)

    if not u_nick:
        await update.message.reply_text("Ты еще не зарегистрирован!")
        return

    marriage = await db.get_marriage(pool, user.id)
    if not marriage:
        await update.message.reply_text("🤔 Ты и так не состоишь в браке.")
        return

    partner_id = marriage['user_two_id'] if marriage['user_one_id'] == user.id else marriage['user_one_id']
    partner_nick = await db.get_nickname(pool, partner_id)
    partner_name = partner_nick if partner_nick else "своей половинкой"

    success = await db.delete_marriage(pool, user.id)

    u_link = f"[{u_nick}](tg://user?id={user.id})"
    p_link = f"[{partner_name}](tg://user?id={partner_id})"

    if success:
        await update.message.reply_text(
            f"💔 Эх.... {u_link} и {p_link} теперь официально в разводе.",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("Произошла ошибка, видимо судьба против.")

async def handle_accept_marriage(update: Update, context: ContextTypes.DEFAULT_TYPE, pool):
    user = update.effective_user
    chat_id = update.effective_chat.id
    proposals = context.chat_data.get('marriage_proposals', {})

    if user.id not in proposals:
        await update.message.reply_text("Вам не было отправлено заявки на брак.")
        return

    proposer_id = proposals.pop(user.id)
    u1_nick = await db.get_nickname(pool, proposer_id)
    u2_nick = await db.get_nickname(pool, user.id)
    await db.create_marriage(pool, proposer_id, user.id, chat_id)
    
    u1_link = f"[{u1_nick}](tg://user?id={proposer_id})"
    u2_link = f"[{u2_nick}](tg://user?id={user.id})"

    await update.message.reply_text(
        f"🥳 Поздравляем! {u1_link} и {u2_link} теперь официально в браке! 🎉",
        parse_mode="Markdown"
    )

async def handle_decline_marriage(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    proposals = context.chat_data.get('marriage_proposals', {})

    if user.id not in proposals:
        await update.message.reply_text("Вам не было отправлено заявки на брак.")
        return

    proposals.pop(user.id)
    await update.message.reply_text("💔 Заявка отклонена.")

async def handle_all_marriages(update: Update, context: ContextTypes.DEFAULT_TYPE, pool):
    marriages = await db.get_all_marriages(pool)
    
    if not marriages:
        await update.message.reply_text("Пока браков нет.")
        return

    text = "💍 **Список всех зарегистрированных браков:**\n\n"
    
    for i, row in enumerate(marriages, start=1):
        u1_link = f"[{row['nick_one']}](tg://user?id={row['user_one_id']})"
        u2_link = f"[{row['nick_two']}](tg://user?id={row['user_two_id']})"
        
        days = row['days_together']
        if days % 10 == 1 and days % 100 != 11:
            day_str = "день"
        elif 2 <= days % 10 <= 4 and (days % 100 < 10 or days % 100 >= 20):
            day_str = "дня"
        else:
            day_str = "дней"
            
        text += f"{i}. {u1_link} и {u2_link} — {days} {day_str}\n"

    await update.message.reply_text(text, parse_mode="Markdown", disable_web_page_preview=True)