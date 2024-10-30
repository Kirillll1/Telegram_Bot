import logging
from pymongo import MongoClient
from config import MONGO_URI
# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

client = MongoClient(MONGO_URI)
db = client['my_store_db']
customers_collection = db['customers']
categories_collection = db['categories']