from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters
import asyncio, nest_asyncio
from config import *  # Make sure your TELEGRAM_TOKEN is defined in config.py
from handlers.user_handlers import handle_contact, delete_account # Import the separated handlers
from handlers.navigation_handlers import menu, start
from handlers.categories_handler import show_categories,  paginate_categories, category_selected
from handlers.text_handler import handle_text
# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()


#  handler to manage reply keyboard button actions

async def main() -> None:
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Register command and callback handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CommandHandler("show_categories", show_categories))
    application.add_handler(CommandHandler("delete_account", delete_account))
    application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Register callback handler for pagination
    application.add_handler(CallbackQueryHandler(paginate_categories, pattern=r"^page_\d+$"))
    application.add_handler(CallbackQueryHandler(category_selected, pattern=r"^category_\d+$"))
    

    # Run the bot
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())