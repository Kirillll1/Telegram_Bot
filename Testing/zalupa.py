from pymongo import MongoClient
from config import MONGO_URI  # Make sure this contains your MongoDB connection string

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client['my_store_db']

# Access or create the subcategories collection
subcategory_collection = db['subcategory']

# Define the category ID you want to search for
category_id = 1

# Query the subcategory collection for documents with the specified category_id
results = subcategory_collection.find({"category_id": category_id})

# Optionally, print the results
for result in results:
    print(result)