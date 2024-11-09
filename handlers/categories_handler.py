from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import BadRequest 
from mongodb import categories_collection, db
from datetime import datetime
import logging
logging.basicConfig(level=logging.INFO)
ITEMS_PER_PAGE = 5

async def show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE, page=0) -> None:
    categories = list(categories_collection.find().sort([("category_id", 1)]))
    
    # Розрахунок початкових і кінцевих індексів категорій для поточної сторінки
    start = page * ITEMS_PER_PAGE
    end = start + ITEMS_PER_PAGE
    page_categories = categories[start:end]

    if page_categories:
        # Підготовка опису та кнопок
        combined_description = ""
        inline_buttons = []

        for category in page_categories:
            name = category.get("name", "Без назви")
            description = category.get("description", "Без опису")
            combined_description += f"*{name}*\n{description}\n\n"
            
            # Створення кнопки для кожної категорії
            inline_buttons.append(
                [InlineKeyboardButton(name, callback_data=f"category_{category.get('category_id')}")]
            )

        combined_description = combined_description.strip()

        # Кнопки для перегортання сторінок
        pagination_buttons = []
        if page > 0:
            pagination_buttons.append(
                InlineKeyboardButton("⬅️ Попередня", callback_data=f"page_{page - 1}")
            )
        if end < len(categories):
            pagination_buttons.append(
                InlineKeyboardButton("➡️ Наступна", callback_data=f"page_{page + 1}")
            )

        # Додаємо кнопки для перегортання сторінок під кнопками категорій
        inline_buttons.append(pagination_buttons)
        
        reply_markup = InlineKeyboardMarkup(inline_buttons)

        # Надсилаємо або редагуємо повідомлення з категоріями та кнопками для перегортання сторінок
        if update.callback_query:
            # Якщо запущено через callback, редагуємо повідомлення
            await update.callback_query.edit_message_caption(
                caption=combined_description,
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
        else:
            # Відображення в перший раз
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
        await update.message.reply_text("Категорії не знайдено.")

# Обробник для вибору категорії
async def category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    # Виводимо дані запиту для діагностики
    print(f"Дані запиту: {query.data}")

    # Витягуємо ID категорії з даних запиту та перетворюємо на int
    try:
        category_id = int(query.data.split("_")[1])  # Переконайтеся, що формат даних відповідає
    except (IndexError, ValueError):
        await query.message.reply_text("Неправильний вибір категорії.")
        return
    
    # Викликаємо новий обробник для підкатегорій
    await show_subcategories(update, context, category_id)


async def paginate_categories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    # Витягуємо номер сторінки з даних запиту
    page = int(query.data.split("_")[1])

    # Викликаємо show_categories з новим номером сторінки
    await show_categories(update, context, page=page)

# Новий обробник для відображення підкатегорій

async def show_subcategories(update: Update, context: ContextTypes.DEFAULT_TYPE, category_id: int) -> None:
    print(f"Запит підкатегорій для category_id: {category_id}")

    # Отримуємо категорію, щоб отримати її назву та зображення
    category = categories_collection.find_one({"category_id": category_id})
    if category:
        category_name = category.get("name", "Невідома категорія")
        category_image_url = category.get("image_url", None)  # Отримуємо URL зображення
    else:
        category_name = "Невідома категорія"
        category_image_url = None

    # Отримуємо підкатегорії для даного category_id
    subcategories = list(db.subcategory.find({"category_id": category_id}))

    if subcategories:
        combined_description = f"Категорія: *{category_name}*\n\n"  # Включаємо назву категорії
        inline_buttons = []  # Список для зберігання кнопок підкатегорій

        for subcategory in subcategories:
            name = subcategory.get("name", "Без назви")
            subcategory_id = subcategory.get('subcategory_id')

            # Створення кнопки для кожної підкатегорії
            inline_buttons.append(
                [InlineKeyboardButton(name, callback_data=f"subcategory_{subcategory_id}_{category_id}")]
            )

        # Підготовка reply_markup для кнопок
        reply_markup = InlineKeyboardMarkup(inline_buttons)

        # Надсилаємо зображення категорії, якщо є
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
        await update.callback_query.message.reply_text(f"Підкатегорії для категорії '{category_name}' не знайдено.")


async def subcategory_selected(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    
    query = update.callback_query
    await query.answer()
    
    # Витягуємо ID підкатегорії та категорії з даних запиту
    try:
        _, subcategory_id, category_id = query.data.split("_")
        subcategory_id = int(subcategory_id)
        category_id = int(category_id)
    except (IndexError, ValueError):
        await query.message.reply_text("Неправильний вибір підкатегорії.")
        return
    
    # Отримуємо продукти на основі вибраної категорії та підкатегорії
    products = list(db.products.find({"category_id": category_id, "subcategory_id": subcategory_id}).limit(5))

    if products:
        for product in products:
            product_id = product.get("product_id")
            product_name = product.get("product_name", "Без назви")
            description = product.get("description", "Без опису")
            price = product.get("price", "Ціна не доступна")
            image_url = product.get("image_url", "")

            # Підготовка повідомлення для продукту
            product_message = f"*{product_name}*\n\n*Опис:* {description}\n\n*Ціна:* {price} грн.\n"

            # Кнопка для додавання продукту в кошик
            add_to_cart_button = InlineKeyboardMarkup([[
                InlineKeyboardButton("Додати до кошика", callback_data=f"addtocart_{product_id}")
            ]])

            if image_url:
                try:
                    # Надсилаємо зображення продукту разом з описом та кнопкою "Додати до кошика"
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
        await query.message.reply_text("Продукти для вибраної підкатегорії не знайдені.")
