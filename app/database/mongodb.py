from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

client = AsyncIOMotorClient(str(settings.mongodb_uri))

db = client['dashboard']


sessions_collection = db['sessions']
conversations_collection = db['conversations']
