from telegram import Update, LabeledPrice
from telegram.ext import ContextTypes
from mongodb import cart_collection
from config import Payment_Provider_Token
from mongodb import cart_collection, products_collection
import time
import logging

async def send_invoice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_id = update.effective_user.id
    user_cart = cart_collection.find_one({"telegram_id": telegram_id, "status": "active"})

    if not user_cart or not user_cart.get("products"):
        await update.callback_query.message.reply_text("Ваш кошик порожній.")
        return

    # Calculate total amount in kopecks (smallest currency unit)
    total_amount = sum(item["total_price"] * 100 for item in user_cart["products"])  # Total amount in kopecks

    # Ensure total amount consistency
    if total_amount != user_cart['total_price'] * 100:
        logging.error(f"Total amount mismatch: calculated {total_amount}, but user cart total {user_cart['total_price'] * 100}")

    # Create LabeledPrice objects for each product in the cart
    prices = [
        LabeledPrice(label=item["product_name"], amount=item["total_price"] * 100)  # Convert to kopecks
        for item in user_cart["products"]
    ]

    try:
        # Ensure you use the correct provider token (this should be your valid TEST provider token)
        

        # Send the invoice to the user
        await update.callback_query.message.reply_invoice(
            provider_token= Payment_Provider_Token,
            title="Ваш рахунок",
            description="Оплата за товар(и)",
            payload=f"invoice_{telegram_id}_{int(time.time())}",
            currency="UAH",  # Ensure currency is correct (UAH in this case)
            prices=prices,  # List of LabeledPrice
            need_shipping_address=True,  # Request for shipping address
            need_email=True,  # Request for email
        )

        logging.info(f"Invoice for {total_amount / 100} UAH sent to user {telegram_id}.")
    except Exception as e:
        logging.error(f"Error sending invoice: {e}")
        await update.callback_query.message.reply_text("Помилка при з'єднанні з сервером оплати.")


async def pre_checkout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.pre_checkout_query
    # Answer the pre-checkout query to proceed with the payment
    await query.answer(ok=True)  # Set to `ok=False` if you want to decline the payment
    logging.info("Pre-checkout query successfully answered.")

# Payment successful handler
async def successful_payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    telegram_id = update.effective_user.id

    # Retrieve the user's cart to get the list of products and quantities
    user_cart = cart_collection.find_one({"telegram_id": telegram_id, "status": "active"})
    
    if user_cart and user_cart.get("products"):
        # Update stock quantity for each product in the cart
        for item in user_cart["products"]:
            product_id = item["product_id"]  # Adjust this key to match your schema
            quantity_purchased = item["quantity"]

            # Reduce the product quantity in the products collection
            products_collection.update_one(
                {"_id": product_id},
                {"$inc": {"quantity": -quantity_purchased}}
            )

        # Clear the user's cart after payment by setting "status" to "paid"
        cart_collection.update_one(
            {"telegram_id": telegram_id, "status": "active"},
            {"$set": {"status": "paid"}}
        )
        
        # Notify the user that the payment was successful and cart is cleared
        await update.message.reply_text("Дякую! Ваш платіж пройшов успішно.")
        logging.info(f"Payment successful for user {telegram_id}. Cart cleared and product quantities updated.")
    else:
        logging.info(f"No active cart found for user {telegram_id} after payment.")