from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters
import asyncio, nest_asyncio
from config import *  # Make sure your TELEGRAM_TOKEN is defined in config.py
from handlers.user_handlers import handle_contact, delete_account # Import the separated handlers
from handlers.navigation_handlers import menu, start
from handlers.categories_handler import show_categories,  paginate_categories, category_selected, subcategory_selected
from handlers.cart_handler import add_to_cart, view_cart, clear_cart, delete_item
from handlers.payment_handler import send_invoice, pre_checkout_handler, successful_payment_handler
from handlers.text_handler import handle_text, handle_inline_cart_action
from telegram.ext import PreCheckoutQueryHandler
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
    application.add_handler(CallbackQueryHandler(subcategory_selected, pattern=r"^subcategory_\d+_\d+$"))

    application.add_handler(CallbackQueryHandler(add_to_cart, pattern=r"^addtocart_\d+$"))
    application.add_handler(CallbackQueryHandler(delete_item, pattern="^delete_item_"))
    application.add_handler(CommandHandler("clearcart", clear_cart))
    application.add_handler(CommandHandler("viewcart", view_cart))
    application.add_handler(CallbackQueryHandler(send_invoice, pattern="^proceed_to_payment$"))
    application.add_handler(CallbackQueryHandler(handle_inline_cart_action))  # Add your other handlers here
    application.add_handler(PreCheckoutQueryHandler(pre_checkout_handler))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_handler))




    # Run the bot
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())