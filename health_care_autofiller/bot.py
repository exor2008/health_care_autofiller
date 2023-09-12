import logging
import os
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

from health_care_autofiller.render import Parser, get_clients

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


class State(IntEnum):
    CHOOSE_CLIENTS = 1


async def record(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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


async def generate_record(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    _, client = update.callback_query.data.split("_")

    with Parser(os.getenv("TEMPLATE"), client) as p:
        p.fill()
        p.save()
        await context.bot.send_document(
            update.callback_query.message.chat_id, p.filename
        )

    return ConversationHandler.END


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Unknown command.")

    return ConversationHandler.END


def start_app():
    application = ApplicationBuilder().token(os.getenv("TOKEN")).build()

    record_handler = ConversationHandler(
        entry_points=[CommandHandler("record", record)],
        states={
            int(State.CHOOSE_CLIENTS): [
                CallbackQueryHandler(
                    generate_record, pattern="^" + str(State.CHOOSE_CLIENTS) + "_\w+"
                ),
            ],
        },
        fallbacks=[
            CommandHandler("unknown", unknown),
        ],
    )

    application.add_handler(record_handler)

    logger.info("Starting bot...")
    application.run_polling()
