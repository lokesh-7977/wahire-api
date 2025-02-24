import uuid
from beanie import Document
from pydantic import EmailStr, Field
from typing import Optional
from uuid import UUID

class User(Document):
    id: UUID = Field(default_factory=uuid.uuid4, alias="_id")  # UUID as primary key
    name: str = Field(..., title="Full Name", min_length=2)
    phone: str = Field(..., title="Phone Number", min_length=10, max_length=15)
    email: Optional[EmailStr] = Field(None, title="Email Address")
    password: Optional[str] = Field(None, title="Password (Hashed)")
    role: str = Field(..., title="User Role")
    isPhoneVerified: bool = Field(False, title="Phone Verification Status")
    isUserDeleted: bool = Field(False, title="User Deletion Status")
    job_category: Optional[str] = Field(None, title="Preferred Job Category")
    job_type: Optional[str] = Field(None, title="Preferred Job Type")

    class Settings:
        collection = "users"  

    class Config:
        json_encoders = {UUID: str}  
