import logging
import telegram
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InputMediaPhoto
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from pymongo import MongoClient
from datetime import datetime
import asyncio, nest_asyncio
from config import *  # Make sure your TELEGRAM_TOKEN is defined in config.py

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# MongoDB configuration
MONGO_URI = "mongodb+srv://chobotarkyrylo:ltx8ZOKkpsmwOjAW@cluster0.ofuyj.mongodb.net/my_store_db?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['my_store_db']
customers_collection = db['customers']
categories_collection = db['categories']

# Define the start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    existing_customer = customers_collection.find_one({"telegram_id": user.id})

    if existing_customer:
        await update.message.reply_text(f'Welcome back, {existing_customer["name"]}! Use /menu to access options.')
    else:
        button = KeyboardButton("Share Contact", request_contact=True)
        reply_markup = ReplyKeyboardMarkup([[button]], one_time_keyboard=True, selective=True)
        await update.message.reply_text(
            f'Hello {user.first_name}! Please share your phone number to register.', reply_markup=reply_markup
        )

# Menu command handler to show options if user is registereda
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    existing_customer = customers_collection.find_one({"telegram_id": user.id})

    # Only unregistered users see the "Share Contact" button
    if existing_customer:
        buttons = [
            [KeyboardButton("Show Categories")],
            [KeyboardButton("Delete Account")]
        ]
    else:
        buttons = [
            [KeyboardButton("Share Contact")]
        ]

    reply_markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("Choose an option:", reply_markup=reply_markup)

# Show categories handler
async def show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    categories = list(categories_collection.find().sort([("category_id", 1)]).limit(4))

    if categories:
        media = []
        combined_caption = ""
        for category in categories:
            name = category.get("name", "No Name")
            description = category.get("description", "No Description")
            combined_caption += f"{name}\n{description}\n\n"

        combined_caption = combined_caption.strip()

        for index, category in enumerate(categories):
            image_url = category.get("image_url", "")
            if image_url:
                caption = combined_caption if index == 0 else None
                media.append(
                    InputMediaPhoto(
                        media=image_url,
                        caption=caption,
                        parse_mode="Markdown" if index == 0 else None
                    )
                )

        if media:
            try:
                await update.message.reply_media_group(media=media)
                logging.info("Sent images for categories with combined captions.")
            except telegram.error.BadRequest as e:
                logging.error(f"Error sending images for categories: {e}")
        else:
            await update.message.reply_text("No valid images to send.")
    else:
        await update.message.reply_text("No categories found.")

# Delete account handler
async def delete_account(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    result = customers_collection.delete_one({"telegram_id": user.id})
    
    if result.deleted_count > 0:
        await update.message.reply_text("Your account has been deleted.", reply_markup=ReplyKeyboardMarkup([[]], resize_keyboard=True))
        button = KeyboardButton("Share Contact", request_contact=True)
        reply_markup = ReplyKeyboardMarkup([[button]], one_time_keyboard=True, selective=True)
        await update.message.reply_text("To register again, please share your contact:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("No account found to delete.")

# Handler to share contact
async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    contact = update.message.contact

    existing_customer = customers_collection.find_one({"telegram_id": user.id})
    if not existing_customer:
        customer_data = {
            "telegram_id": user.id,
            "name": user.first_name,
            "phone": contact.phone_number,
            "registered_date": datetime.utcnow()
        }
        customers_collection.insert_one(customer_data)
        
        buttons = [
            [KeyboardButton("Show Categories")],
            [KeyboardButton("Delete Account")]
        ]
        reply_markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=True)
        await update.message.reply_text("Registration successful! Choose an option:", reply_markup=reply_markup)
    else:
        await update.message.reply_text("You are already registered.")

# New handler to manage reply keyboard button actions
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    if text == "Show Categories":
        await show_categories(update, context)
    elif text == "Delete Account":
        await delete_account(update, context)
    else:
        await update.message.reply_text("Unknown command. Please choose an option from the menu.")

async def main() -> None:
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Register command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CommandHandler("show_categories", show_categories))
    application.add_handler(CommandHandler("delete_account", delete_account))
    # Register specific text handlers for reply keyboard actions
    application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Run the bot
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
