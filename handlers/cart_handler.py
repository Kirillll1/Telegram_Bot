import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from mongodb import db, cart_collection
from datetime import datetime

logging.basicConfig(level=logging.INFO)


async def add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    logging.info("Кнопку 'Додати в кошик' натиснуто.")  # Лог натискання кнопки

    # Парсинг product_id з callback data
    try:
        _, product_id = query.data.split("_")
        product_id = int(product_id)  # Переконайтеся, що product_id є цілим числом
        logging.info(f"Розпізнано product_id: {product_id}")  # Лог розпізнаного product_id
    except (IndexError, ValueError) as e:
        logging.error(f"Помилка розбору callback даних: {str(e)}")  # Лог помилки при розборі
        await query.message.reply_text("Помилка додавання продукту в кошик.")
        return

    # Отримання інформації про продукт з MongoDB
    product = db.products.find_one({"product_id": product_id})
    if not product:
        logging.error(f"Продукт з ID {product_id} не знайдено в базі даних.")  # Лог, якщо продукт не знайдено
        await query.message.reply_text("Продукт не знайдено.")
        return

    logging.info(f"Знайдено продукт: {product['product_name']}")  # Лог, якщо продукт знайдено

    # Використання telegram_id для ідентифікації кошика користувача
    telegram_id = update.effective_user.id

    # Інформація про товар для кошика
    cart_item = {
        "product_id": product["product_id"],
        "product_name": product["product_name"],
        "price": product["price"],
        "quantity": 1,  # Кількість за замовчуванням
        "total_price": product["price"]
    }

    # Перевірка наявності активного кошика для користувача
    user_cart = cart_collection.find_one({"telegram_id": telegram_id, "status": "active"})
    logging.info(f"Кошик користувача знайдено: {user_cart is not None}")  # Лог наявності кошика

    if user_cart:
        # Оновлення кошика, якщо продукт вже існує, або додавання нового товару
        existing_product = next((item for item in user_cart["products"] if item["product_id"] == product_id), None)
        
        if existing_product:
            logging.info(f"Продукт {product_id} вже в кошику. Оновлюємо кількість.")  # Лог, якщо продукт вже в кошику
            
            # Оновлення кількості та загальної вартості
            db.cart.update_one(
                {"telegram_id": telegram_id, "status": "active", "products.product_id": product_id},
                {
                    "$inc": {
                        "products.$.quantity": 1,  # Збільшення кількості на 1
                        "products.$.total_price": product["price"],  # Збільшення загальної ціни товару
                        "total_price": product["price"]  # Збільшення загальної суми кошика
                    }
                }
            )
        else:
            logging.info(f"Продукт {product_id} не в кошику. Додаємо новий товар.")  # Лог додавання нового товару
            # Додавання нового продукту в кошик
            db.cart.update_one(
                {"telegram_id": telegram_id, "status": "active"},
                {
                    "$push": {"products": cart_item},  # Додавання нового товару до масиву кошика
                    "$inc": {"total_price": product["price"]}  # Збільшення загальної суми кошика
                }
            )
    else:
        logging.info("Активний кошик не знайдено. Створюємо новий кошик.")  # Лог створення нового кошика
        # Створення нового кошика, якщо активного не існує
        new_cart = {
            "telegram_id": telegram_id,
            "products": [cart_item],
            "total_price": product["price"],
            "status": "active",
            "created_at": datetime.utcnow()
        }
        db.cart.insert_one(new_cart)

    # Інлайн-клавіатура з кнопками для видалення товару
    keyboard = [
        [
            InlineKeyboardButton("❌ Видалити товар", callback_data=f"delete_item_{product_id}"),
            InlineKeyboardButton("🛒 Переглянути кошик", callback_data="view_cart")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    logging.info(f"{product['product_name']} додано в кошик.")  # Лог успішного додавання в кошик
    await query.message.reply_text(f"{product['product_name']} додано у ваш кошик.", reply_markup=reply_markup)


async def delete_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    try:
        # Скореговано для правильного розбору callback даних
        callback_data = query.data
        logging.info(f"Отримані callback дані для delete_item: {callback_data}")

        # Перевірка формату та розбір callback даних
        if not callback_data.startswith("delete_item_"):
            logging.error("Неправильний формат callback даних.")
            await query.message.reply_text("Неприпустима операція.")
            return

        # Розбір та отримання ID продукту
        product_id = int(callback_data.split("_")[-1])
        logging.info(f"Розпізнано product_id для видалення: {product_id}")

    except (ValueError, IndexError) as e:
        logging.error(f"Помилка розбору callback даних для delete_item: {str(e)}")
        await query.message.reply_text("Помилка видалення продукту з кошика.")
        return

    telegram_id = update.effective_user.id

    # Отримання інформації про продукт з кошика для коригування загальної ціни
    user_cart = cart_collection.find_one({"telegram_id": telegram_id, "status": "active"})
    product = next((item for item in user_cart["products"] if item["product_id"] == product_id), None)
    if not product:
        logging.info(f"Продукт {product_id} не знайдено в кошику.")
        await query.message.reply_text("Продукт не знайдено у вашому кошику.")
        return

    # Видалення продукту з кошика користувача
    result = cart_collection.update_one(
        {"telegram_id": telegram_id, "status": "active"},
        {
            "$pull": {"products": {"product_id": product_id}},
            "$inc": {"total_price": -product["total_price"]}
        }
    )

    if result.modified_count > 0:
        logging.info(f"Продукт {product_id} видалено з кошика.")
        await query.message.reply_text(f"{product['product_name']} видалено з вашого кошика.")
    else:
        await query.message.reply_text("Сталася помилка. Будь ласка, спробуйте ще раз.")


async def clear_cart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_id = update.effective_user.id
    cart_collection.update_one(
        {"telegram_id": telegram_id, "status": "active"},
        {"$set": {"products": [], "total_price": 0}}
    )
    logging.info("Кошик очищено для користувача: %s", telegram_id)
    await update.callback_query.message.reply_text("Ваш кошик очищено.")


async def view_cart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_id = update.effective_user.id
    user_cart = cart_collection.find_one({"telegram_id": telegram_id, "status": "active"})

    if user_cart and user_cart.get("products"):
        cart_summary = "🛒 **Ваш кошик**:\n"
        for item in user_cart["products"]:
            cart_summary += (
                f"{item['quantity']} од. {item['product_name']} x {item['price']}грн. "
                f"= {item['total_price']} грн.\n"
            )
        cart_summary += f"\n**Загальна сума: **{user_cart['total_price']} грн."

        # Додавання кнопки "Очистити кошик"
        keyboard = [
            [
                InlineKeyboardButton("🗑️ Очистити кошик", callback_data="clear_cart")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        logging.info("Кошик переглянуто для користувача: %s", telegram_id)
        await update.callback_query.message.reply_text(cart_summary, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        logging.info("Переглянуто порожній кошик для користувача: %s", telegram_id)
        await update.callback_query.message.reply_text("Ваш кошик порожній.")
