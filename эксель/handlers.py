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
    user = update.effective_user

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

async def handle_sticker_reactions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.sticker.file_id == "CAACAgIAAxkBAAIB0GmprRn4W6u5b92a222Lm5mOPYPLAAKrmQAC9UXoS6VAy4587toFOgQ":
        try:
            await context.bot.set_message_reaction(chat_id=update.effective_chat.id, message_id=update.message.message_id, reaction=[ReactionTypeEmoji("❤️")])
        except: pass

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