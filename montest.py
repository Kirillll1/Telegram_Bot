from pymongo import MongoClient
from config import MONGO_URI  # Make sure this contains your MongoDB connection string

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client['my_store_db']

# Access or create the subcategories collection
subcategory_collection = db['subcategory']

# Example subcategories to insert
subcategory = [
    {
        "subcategory_id": 1,
        "category_id": 1,  # Reference to the category ID (e.g., 1 = Clothing)
        "name": "Shoes",
        "description": "A variety of shoes including sports, formal, and casual.",
        "image_url": "https://st2.depositphotos.com/1854227/7301/i/450/depositphotos_73016671-stock-photo-running-shoes-and-mp3-player.jpg"
    },
    {
        "subcategory_id": 2,
        "category_id": 1,  # Reference to the category ID (e.g., 1 = Clothing)
        "name": "Pants",
        "description": "Pants in various styles and sizes.",
        "image_url": "https://www.menswearr.com/cdn/shop/articles/types-of-trousers-for-men_1100x.webp?v=1725252145"
    },
    {
        "subcategory_id": 3,
        "category_id": 1,  # Reference to a different category ID (e.g., 2 = Accessories)
        "name": "Hats",
        "description": "Hats and caps of various styles.",
        "image_url": "https://fcdrycleaners.com/wp-content/uploads/2023/09/Do-Dry-Cleaners-Clean-Hats-A-Complete-Guide-To-Hat-Cleaning.jpg"
    },
    {
        "subcategory_id": 4,
        "category_id": 1,  # Reference to a different category ID (e.g., 2 = Accessories)
        "name": "Shirts",
        "description": "Hats and caps of various styles.",
        "image_url": "https://media.gq.com/photos/65b2b0d448455df33f4cf305/4:3/w_1500,h_1125,c_limit/western-shirt-art.jpg"
    },
        {
        "subcategory_id": 5,
        "category_id": 1,  # Reference to a different category ID (e.g., 2 = Accessories)
        "name": "Shorts",
        "description": "Hats and caps of various styles.",
        "image_url": "https://images.squarespace-cdn.com/content/v1/630f9449e9d3ae151b3599d3/1662514201600-ULK9J672WEYJJRJWD5SW/shorts-fit-guide-men-Featured-Image.jpg"
    },
        {
        "subcategory_id": 6,
        "category_id": 2,  # Reference to the category ID (e.g., 1 = Clothing)
        "name": "Shoes",
        "description": "A variety of shoes including sports, formal, and casual.",
        "image_url": "https://example.com/images/shoes.jpg"
    },
    {
        "subcategory_id": 7,
        "category_id": 2,  # Reference to the category ID (e.g., 1 = Clothing)
        "name": "Pants",
        "description": "Pants in various styles and sizes.",
        "image_url": "https://example.com/images/pants.jpg"
    },
    {
        "subcategory_id": 8,
        "category_id": 2,  # Reference to a different category ID (e.g., 2 = Accessories)
        "name": "Hats",
        "description": "Hats and caps of various styles.",
        "image_url": "https://example.com/images/hats.jpg"
    },
    {
        "subcategory_id": 9,
        "category_id": 2,  # Reference to a different category ID (e.g., 2 = Accessories)
        "name": "Shirts",
        "description": "Hats and caps of various styles.",
        "image_url": "https://example.com/images/hats.jpg"
    },
    {
        "subcategory_id": 10,
        "category_id": 2,  # Reference to a different category ID (e.g., 2 = Accessories)
        "name": "Shorts",
        "description": "Hats and caps of various styles.",
        "image_url": "https://example.com/images/hats.jpg"
    },
        {
        "subcategory_id": 11,
        "category_id": 3,  # Reference to the category ID (e.g., 1 = Clothing)
        "name": "Shoes",
        "description": "A variety of shoes including sports, formal, and casual.",
        "image_url": "https://example.com/images/shoes.jpg"
    },
    {
        "subcategory_id": 12,
        "category_id": 3,  # Reference to the category ID (e.g., 1 = Clothing)
        "name": "Pants",
        "description": "Pants in various styles and sizes.",
        "image_url": "https://example.com/images/pants.jpg"
    },
    {
        "subcategory_id": 13,
        "category_id": 3,  # Reference to a different category ID (e.g., 2 = Accessories)
        "name": "Hats",
        "description": "Hats and caps of various styles.",
        "image_url": "https://example.com/images/hats.jpg"
    },
    {
        "subcategory_id": 14,
        "category_id": 3,  # Reference to a different category ID (e.g., 2 = Accessories)
        "name": "Shirts",
        "description": "Hats and caps of various styles.",
        "image_url": "https://example.com/images/hats.jpg"
    },
    {
        "subcategory_id": 15,
        "category_id": 3,  # Reference to a different category ID (e.g., 2 = Accessories)
        "name": "Shorts",
        "description": "Hats and caps of various styles.",
        "image_url": "https://example.com/images/hats.jpg"
    }
    # Add more subcategories as needed
]

# Insert the subcategories into the MongoDB collection
result = subcategory_collection.insert_many(subcategory)
print("Inserted subcategories with IDs:", result.inserted_ids)
