import logging
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from datetime import datetime
from pymongo import MongoClient
from bson.objectid import ObjectId

# MongoDB configuration
MONGO_URI = "mongodb+srv://chobotarkyrylo:ltx8ZOKkpsmwOjAW@cluster0.ofuyj.mongodb.net/my_store_db?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['my_store_db']
customers_collection = db['customers']

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

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