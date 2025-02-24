from beanie import Document
from typing import ClassVar, Optional
from pydantic import BaseModel, EmailStr 

class User(Document):
    full_name: str
    email: EmailStr
    phone: str
    password: str
    is_active: bool = True
    job_category: str
    job_type: str
    role: ClassVar[str] = 'user'     

    class Settings:
        collection = "users"
