from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest 
from mongodb import categories_collection, db, cart_collection
from datetime import datetime
import logging
logging.basicConfig(level=logging.INFO)
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



async def paginate_categories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    # Extract the page number from the callback data
    page = int(query.data.split("_")[1])

    # Call show_categories with the new page number
    await show_categories(update, context, page=page)
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
            subcategory_id = subcategory.get('subcategory_id')

            # Create an inline button for each subcategory
            inline_buttons.append(
                [InlineKeyboardButton(name, callback_data=f"subcategory_{subcategory_id}_{category_id}")]
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





async def subcategory_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    query = update.callback_query
    await query.answer()
    
    # Parse subcategory and category ID from the callback data
    try:
        _, subcategory_id, category_id = query.data.split("_")
        subcategory_id = int(subcategory_id)
        category_id = int(category_id)
    except (IndexError, ValueError):
        await query.message.reply_text("Invalid subcategory selection.")
        return
    
    # Fetch products based on the selected category and subcategory
    products = list(db.products.find({"category_id": category_id, "subcategory_id": subcategory_id}).limit(5))

    if products:
        for product in products:
            product_id = product.get("product_id")
            product_name = product.get("product_name", "No Name")
            description = product.get("description", "No Description")
            price = product.get("price", "Price not available")
            image_url = product.get("image_url", "")

            # Prepare the message for the product
            product_message = f"*{product_name}*\n\n*Description:* {description}\n\n*Price:* {price}\n"

            # Inline button to add product to cart
            add_to_cart_button = InlineKeyboardMarkup([[
                InlineKeyboardButton("Add to Cart", callback_data=f"addtocart_{product_id}")
            ]])

            if image_url:
                try:
                    # Send the product image along with the description and "Add to Cart" button
                    await query.message.reply_photo(
                        photo=image_url,
                        caption=product_message,
                        parse_mode="Markdown",
                        reply_markup=add_to_cart_button
                    )
                except BadRequest:
                    await query.message.reply_text(
                        product_message,
                        parse_mode="Markdown",
                        reply_markup=add_to_cart_button
                    )
            else:
                await query.message.reply_text(
                    product_message,
                    parse_mode="Markdown",
                    reply_markup=add_to_cart_button
                )
    else:
        await query.message.reply_text("No products found for the selected subcategory.")
# Handler function for adding products to the cart
async def add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    logging.info("Add to Cart button clicked.")  # Log that the button was clicked

    # Parse product ID from the callback data
    try:
        _, product_id = query.data.split("_")
        product_id = int(product_id)  # Ensure product_id is treated as an integer
        logging.info(f"Parsed product_id: {product_id}")  # Log the parsed product_id
    except (IndexError, ValueError) as e:
        logging.error(f"Error parsing callback data: {str(e)}")  # Log any error during parsing
        await query.message.reply_text("Error adding product to cart.")
        return

    # Retrieve product details from MongoDB
    product = db.products.find_one({"product_id": product_id})
    if not product:
        logging.error(f"Product with ID {product_id} not found in the database.")  # Log if product not found
        await query.message.reply_text("Product not found.")
        return

    logging.info(f"Product found: {product['product_name']}")  # Log if product is found

    # Use the telegram_id as the identifier for each user's cart
    telegram_id = update.effective_user.id

    # Cart item details
    cart_item = {
        "product_id": product["product_id"],
        "product_name": product["product_name"],
        "price": product["price"],
        "quantity": 1,  # Default quantity
        "total_price": product["price"]
    }

    # Check if an active cart exists for the user
    user_cart = cart_collection.find_one({"telegram_id": telegram_id, "status": "active"})
    logging.info(f"User cart found: {user_cart is not None}")  # Log if user cart exists or not

    if user_cart:
        # Update cart if product already exists, otherwise add new item
        existing_product = next((item for item in user_cart["products"] if item["product_id"] == product_id), None)
        
        if existing_product:
            logging.info(f"Product {product_id} already in the cart. Updating quantity.")  # Log if product is already in cart
            
            # Update quantity and total price for the existing product
            db.cart.update_one(
                {"telegram_id": telegram_id, "status": "active", "products.product_id": product_id},
                {
                    "$inc": {
                        "products.$.quantity": 1,  # Increment quantity by 1
                        "products.$.total_price": product["price"],  # Increment total price for the specific product
                        "total_price": product["price"]  # Increment overall cart total price
                    }
                }
            )
        else:
            logging.info(f"Product {product_id} not in the cart. Adding new item.")  # Log if adding new item
            # Add new product to the cart
            db.cart.update_one(
                {"telegram_id": telegram_id, "status": "active"},
                {
                    "$push": {"products": cart_item},  # Add new product to the cart array
                    "$inc": {"total_price": product["price"]}  # Increment overall cart total price
                }
            )
    else:
        logging.info("No active cart found. Creating new cart.")  # Log if no active cart
        # Create a new cart if no active cart exists
        new_cart = {
            "telegram_id": telegram_id,
            "products": [cart_item],
            "total_price": product["price"],
            "status": "active",
            "created_at": datetime.utcnow()
        }
        db.cart.insert_one(new_cart)

    logging.info(f"{product['product_name']} added to the cart.")  # Log successful addition to cart
    await query.message.reply_text(f"{product['product_name']} added to your cart.")
