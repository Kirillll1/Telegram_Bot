from telegram import Update
from telegram.ext import ContextTypes
from handlers.categories_handler import show_categories
from handlers.user_handlers import delete_account


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    if text == "Show Categories":
        await show_categories(update, context)
    elif text == "Delete Account":
        await delete_account(update, context)
    else:
        await update.message.reply_text("Unknown command. Please choose an option from the menu.")
