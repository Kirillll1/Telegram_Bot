import logging
import telegram
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from pymongo import MongoClient
from datetime import datetime
import asyncio, nest_asyncio
from bson.objectid import ObjectId  # Import ObjectId to handle MongoDB object IDs
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

# Menu command handler to show options if user is registered
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    existing_customer = customers_collection.find_one({"telegram_id": user.id})

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

# Show categories handler with inline buttons
async def show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Retrieve categories from the database and limit to 4 for display
    categories = list(categories_collection.find().sort([("category_id", 1)]).limit(4))

    if categories:
        # Select the first category to use its image and set up a description for all categories
        main_image_url = categories[0].get("image_url", "")
        combined_description = ""
        inline_buttons = []

        for category in categories:
            name = category.get("name", "No Name")
            description = category.get("description", "No Description")
            combined_description += f"*{name}*\n{description}\n\n"
            
            # Create an inline button for each category
            inline_buttons.append(
                [InlineKeyboardButton(name, callback_data=f"category_{category.get('_id')}")]
            )

        combined_description = combined_description.strip()  # Remove any trailing newline
        reply_markup = InlineKeyboardMarkup(inline_buttons)

        # Send a single message with an image, description, and inline buttons
        if main_image_url:
            await update.message.reply_photo(
                photo=main_image_url,
                caption=combined_description,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
        else:
            # Fallback in case no image is found
            await update.message.reply_text(
                combined_description,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
    else:
        await update.message.reply_text("No categories found.")

# Callback handler for category buttons
async def category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    # Extract category ID from callback data
    category_id = query.data.split("_")[1]
    category = categories_collection.find_one({"_id": ObjectId(category_id)})

    if category:
        # Send category details
        name = category.get("name", "No Name")
        description = category.get("description", "No Description")
        image_url = category.get("image_url", None)

        message_text = f"*{name}*\n{description}"
        
        if image_url:
            await query.message.reply_photo(photo=image_url, caption=message_text, parse_mode="Markdown")
        else:
            await query.message.reply_text(text=message_text, parse_mode="Markdown")
    else:
        await query.message.reply_text("Category not found.")

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
    
    # Register specific text handlers for reply keyboard actions
    application.add_handler(MessageHandler(filters.CONTACT, handle_contact))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    # Register callback query handler for inline buttons
    application.add_handler(CallbackQueryHandler(category_selected))

    # Run the bot
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())
