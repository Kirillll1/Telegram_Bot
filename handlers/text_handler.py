from telegram import Update
from telegram.ext import ContextTypes
from handlers.categories_handler import show_categories
from handlers.user_handlers import delete_account
from handlers.cart_handler import view_cart, clear_cart


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    if text == "Показати категорії":
        await show_categories(update, context)
    elif text == "Видалити акаунт":
        await delete_account(update, context)
    else:
        await update.message.reply_text("Невідома команда. Будь ласка, виберіть опцію з меню.")


async def handle_inline_cart_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    action = query.data
    
    if action == "view_cart":
        await view_cart(update, context)
    elif action == "clear_cart":
        await clear_cart(update, context)
    await query.answer()
