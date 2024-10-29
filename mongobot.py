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
# New handler to display subcategories
async def show_subcategories(update: Update, context: ContextTypes.DEFAULT_TYPE, category_id: int, page: int = 0) -> None:
    print(f"Querying subcategories for category_id: {category_id}, page: {page}")  # Debug output

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

    # Calculate pagination
    start_index = page * ITEMS_PER_PAGE
    end_index = start_index + ITEMS_PER_PAGE
    paginated_subcategories = subcategories[start_index:end_index]

    if paginated_subcategories:
        combined_description = f"Category: *{category_name}*\n\n"  # Include the category name
        inline_buttons = []  # List to hold inline buttons for subcategories

        for subcategory in paginated_subcategories:
            name = subcategory.get("name", "No Name")
            # Create an inline button for each subcategory
            inline_buttons.append(
                [InlineKeyboardButton(name, callback_data=f"subcategory_{subcategory.get('subcategory_id')}")]
            )

        # Pagination buttons
        pagination_buttons = []
        if page > 0:  # Previous button
            pagination_buttons.append(
                InlineKeyboardButton("⬅️ Previous", callback_data=f"subcategory_page_{category_id}_{page - 1}")
            )
        if end_index < len(subcategories):  # Next button
            pagination_buttons.append(
                InlineKeyboardButton("➡️ Next", callback_data=f"subcategory_page_{category_id}_{page + 1}")
            )

        # Add pagination buttons to inline buttons if they exist
        if pagination_buttons:
            inline_buttons.append(pagination_buttons)

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

async def paginate_subcategories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    # Extract category ID and page number from callback data
    try:
        _, category_id, page = query.data.split("_")
        category_id = int(category_id)
        page = int(page)
    except (ValueError, IndexError):
        await query.message.reply_text("Invalid pagination selection.")
        return

    # Call show_subcategories with the new page number
    await show_subcategories(update, context, category_id, page)


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
    application.add_handler(CallbackQueryHandler(paginate_subcategories, pattern=r"^subcategory_page_\d+_\d+$"))

    # Run the bot
    await application.run_polling()

if __name__ == '__main__':
    asyncio.run(main())