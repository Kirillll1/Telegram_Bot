import logging  # Для логування

# Імпорти для роботи з Telegram ботом
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup  # Для обробки оновлень та створення кнопок відповіді
from telegram.ext import ContextTypes  # Для типізації контексту в асинхронних функціях
from mongodb import customers_collection


async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    existing_customer = customers_collection.find_one({"telegram_id": user.id})

    if existing_customer:
        buttons = [
            [KeyboardButton("Показати категорії")],
            [KeyboardButton("Видалити акаунт")]
        ]
    else:
        buttons = [
            [KeyboardButton("Поділитися контактом")]
        ]

    reply_markup = ReplyKeyboardMarkup(buttons, resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("Оберіть опцію:", reply_markup=reply_markup)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    existing_customer = customers_collection.find_one({"telegram_id": user.id})

    if existing_customer:
        await update.message.reply_text(f'Ласкаво просимо назад, {existing_customer["name"]}! Використовуйте /menu для доступу до опцій.')
    else:
        button = KeyboardButton("Поділитися контактом", request_contact=True)
        reply_markup = ReplyKeyboardMarkup([[button]], one_time_keyboard=True, selective=True)
        await update.message.reply_text(
            f'Привіт {user.first_name}! Будь ласка, поділіться своїм номером телефону для реєстрації.', reply_markup=reply_markup
        )
