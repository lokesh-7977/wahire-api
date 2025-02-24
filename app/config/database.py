from beanie import init_beanie
import motor.motor_asyncio
from app.models.user_model import User
from app.config.settings import Settings

settings = Settings()

async def init_db():
    client = motor.motor_asyncio.AsyncIOMotorClient(settings.database_uri)
    database_name = settings.database_uri.rsplit("/", 1)[-1].split("?")[0]
    database = client[database_name]

    await init_beanie(database, document_models=[User])
