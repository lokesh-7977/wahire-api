from beanie import init_beanie 
import motor.motor_asyncio 
from pymongo.uri_parser import parse_uri  
from app.models.user_model import User
from app.config.settings import Settings

settings = Settings()

async def init_db():
    """Initialize MongoDB connection with Beanie."""
    client = motor.motor_asyncio.AsyncIOMotorClient(settings.database_uri)

    parsed_uri = parse_uri(settings.database_uri)
    database_name = parsed_uri["database"]

    database = client[database_name]
    
    await init_beanie(database, document_models=[User])
