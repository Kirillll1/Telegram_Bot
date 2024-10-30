from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from mongodb import categories_collection, db

ITEMS_PER_PAGE = 5

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