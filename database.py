from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING
import os
from dotenv import load_dotenv

load_dotenv()

MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "shetech_db")

client = AsyncIOMotorClient(MONGODB_URL)
db = client[DATABASE_NAME]

# Collections
users_collection = db["users"]
transactions_collection = db["transactions"]
subscriptions_collection = db["subscriptions"]
alerts_collection = db["alerts"]


async def init_db():
    """Create indexes for better query performance."""
    await users_collection.create_index([("email", ASCENDING)], unique=True)
    await transactions_collection.create_index([("user_id", ASCENDING), ("date", DESCENDING)])
    await transactions_collection.create_index([("merchant", ASCENDING)])
    await subscriptions_collection.create_index([("user_id", ASCENDING)])
    await alerts_collection.create_index([("user_id", ASCENDING), ("is_read", ASCENDING)])
    print("✅ Database indexes created.")
