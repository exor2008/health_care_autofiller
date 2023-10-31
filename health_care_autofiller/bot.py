import logging
import os
from datetime import datetime
from enum import IntEnum

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from telegram_bot_calendar import LSTEP, DetailedTelegramCalendar

from health_care_autofiller.render import Parser, get_clients

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


class State(IntEnum):
    CHOOSE_CLIENTS = 1
    CHOOSE_DATE = 2


async def ask_client(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    users = list(map(int, os.getenv("USERS").split(",")))
    if not update.effective_user.id in users:
        await update.message.reply_text(
            text=f"You are unregistered user {update.effective_user.id}",
        )
        return ConversationHandler.END

    buttons = [
        [
            InlineKeyboardButton(
                text=client, callback_data=str(State.CHOOSE_CLIENTS) + "_" + client
            )
            for client in get_clients()
        ]
    ]

    keyboard = InlineKeyboardMarkup(buttons)

    await update.message.reply_text(text="Choose client", reply_markup=keyboard)

    return int(State.CHOOSE_CLIENTS)


async def generate_record(
    update: Update, context: ContextTypes.DEFAULT_TYPE, client: str, date: datetime
) -> int:
    with Parser(os.getenv("TEMPLATE"), client, date) as p:
        p.fill()
        p.save()
        await context.bot.send_document(
            update.callback_query.message.chat_id, p.filename
        )


async def init_calendar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    _, client = update.callback_query.data.split("_")
    context.user_data["CLIENT"] = client

    calendar, step = DetailedTelegramCalendar().build()

    await context.bot.send_message(
        update.callback_query.message.chat_id,
        f"Select {LSTEP[step]}",
        reply_markup=calendar,
    )
    return int(State.CHOOSE_DATE)


async def ask_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    date, key, step = DetailedTelegramCalendar().process(update.callback_query.data)
    msg = update.callback_query.message

    if date:
        client = context.user_data["CLIENT"]

        await generate_record(update, context, client, date)

        return ConversationHandler.END

    else:
        await context.bot.edit_message_text(
            f"Select {LSTEP[step]}",
            msg.chat.id,
            msg.message_id,
            reply_markup=key,
        )

        return int(State.CHOOSE_DATE)


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Unknown command.")

    return ConversationHandler.END


def start_app():
    application = ApplicationBuilder().token(os.getenv("TOKEN")).build()

    record_handler = ConversationHandler(
        entry_points=[CommandHandler("record", ask_client)],
        states={
            int(State.CHOOSE_CLIENTS): [
                CallbackQueryHandler(
                    init_calendar, pattern="^" + str(State.CHOOSE_CLIENTS) + "_\w+"
                ),
            ],
            int(State.CHOOSE_DATE): [
                CallbackQueryHandler(ask_date, pattern="^cbcal_0\w+"),
            ],
        },
        fallbacks=[
            CommandHandler("unknown", unknown),
        ],
    )

    application.add_handler(record_handler)

    logger.info("Starting bot...")
    application.run_polling()
