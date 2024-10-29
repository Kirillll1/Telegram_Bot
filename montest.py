import logging
import telegram
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from pymongo import MongoClient
from datetime import datetime
import asyncio, nest_asyncio
from bson.objectid import ObjectId  # Import ObjectId to handle MongoDB object IDs
from config import *  # Make sure your TELEGRAM_TOKEN is defined in config.py
from handlers import handle_contact, delete_account, menu, start # Import the separated handlers

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()
ITEMS_PER_PAGE = 5

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# MongoDB configuration
MONGO_URI = "mongodb+srv://chobotarkyrylo:ltx8ZOKkpsmwOjAW@cluster0.ofuyj.mongodb.net/my_store_db?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['my_store_db']
customers_collection = db['customers']
categories_collection = db['categories']

# Define the start command handler


# Menu command handler to show options if user is registered


# Show categories handler with inline buttons
# Show categories handler with pagination support
async def show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE, page=0) -> None:
    categories = list(categories_collection.find().sort([("category_id", 1)]))
    
    # Calculate the start and end indices of categories for the current page
    start = page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    page_categories = categories[start:end]

    if page_categories:
        # Prepare the description and buttons
        combined_description = ""
        inline_buttons = []

        for category in page_categories:
            name = category.get("name", "No Name")
            description = category.get("description", "No Description")
            combined_description += f"*{name}*\n{description}\n\n"
            
            # Create an inline button for each category
            inline_buttons.append(
                [InlineKeyboardButton(name, callback_data=f"category_{category.get('category_id')}")]
            )

        combined_description = combined_description.strip()

        # Pagination buttons
        pagination_buttons = []
        if page > 0:
            pagination_buttons.append(
                InlineKeyboardButton("⬅️ Previous", callback_data=f"page_{page - 1}")
            )
        if end < len(categories):
            pagination_buttons.append(
                InlineKeyboardButton("➡️ Next", callback_data=f"page_{page + 1}")
            )

        # Add pagination buttons in a row below category buttons
        inline_buttons.append(pagination_buttons)
        
        reply_markup = InlineKeyboardMarkup(inline_buttons)

        # Send or edit message with categories and pagination buttons
        if update.callback_query:
            # If this was triggered by a callback, edit the message
            await update.callback_query.edit_message_caption(
                caption=combined_description,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
        else:
            # First-time display
            main_image_url = page_categories[0].get("image_url", "")
            if main_image_url:
                await update.message.reply_photo(
                    photo=main_image_url,
                    caption=combined_description,
                    parse_mode="Markdown",
                    reply_markup=reply_markup
                )
            else:
                await update.message.reply_text(
                    combined_description,
                    parse_mode="Markdown",
                    reply_markup=reply_markup
                )
    else:
        await update.message.reply_text("No categories found.")

async def paginate_categories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    # Extract the page number from the callback data
    page = int(query.data.split("_")[1])

    # Call show_categories with the new page number
    await show_categories(update, context, page=page)

# Callback handler for category buttons
async def category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    # Print the query data to see its contents
    print(f"Query data: {query.data}")  # Debug output

    # Extract category ID from callback data and convert to int
    try:
        category_id = int(query.data.split("_")[1])  # Ensure this matches your data format
    except (IndexError, ValueError):
        await query.message.reply_text("Invalid category selection.")
        return
    
    # Call the new subcategory handler
    await show_subcategories(update, context, category_id)


# New handler to display subcategories
async def show_subcategories(update: Update, context: ContextTypes.DEFAULT_TYPE, category_id: int) -> None:
    print(f"Querying subcategories for category_id: {category_id}")  # Debug output

    # Fetch the category to get its name and image
    category = categories_collection.find_one({"category_id": category_id})
    if category:
        category_name = category.get("name", "Unknown Category")
        category_image_url = category.get("image_url", None)  # Fetch the image URL
    else:
        category_name = "Unknown Category"
        category_image_url = None

    # Fetch subcategories for the given category_id
    subcategories = list(db.subcategory.find({"category_id": category_id}))

    if subcategories:
        combined_description = f"Category: *{category_name}*\n\n"  # Include the category name
        inline_buttons = []  # List to hold inline buttons for subcategories

        for subcategory in subcategories:
            name = subcategory.get("name", "No Name")
            # Create an inline button for each subcategory
            inline_buttons.append(
                [InlineKeyboardButton(name, callback_data=f"subcategory_{subcategory.get('subcategory_id')}")]
            )

        # Prepare reply markup for inline buttons
        reply_markup = InlineKeyboardMarkup(inline_buttons)

        # Send category image if available
        if category_image_url:
            await update.callback_query.message.reply_photo(
                photo=category_image_url,
                caption=combined_description.strip(),
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
        else:
            await update.callback_query.message.reply_text(
                combined_description.strip(),
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
    else:
        await update.callback_query.message.reply_text(f"No subcategories found for the category '{category_name}'.")




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