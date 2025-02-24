from fastapi import APIRouter, HTTPException
from app.models.user_model import User

router = APIRouter()

@router.post("/register")
async def register_user(user: User):
    await user.insert()
    return {"message": "User registered successfully"}
