import uuid
import random
import time
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from beanie import PydanticObjectId
from app.models.user_model import User
from twilio.rest import Client
from app.config.settings import Settings
from passlib.hash import bcrypt

router = APIRouter()
settings = Settings()

twilio_client = Client(settings.twilio_account_sid, settings.twilio_auth_token)

# Temporary in-memory OTP store (for production, use a database)
otp_store = {}

### ====================== 📌 REQUEST SCHEMAS ====================== ###
class RegisterSchema(BaseModel):
    name: str
    phone: str

class OTPVerifySchema(BaseModel):
    phone: str
    otp: str

class UpdateUserSchema(BaseModel):
    name: str

### ====================== 📌 UTILITY FUNCTIONS ====================== ###

def generate_otp(phone: str) -> str:
    """Generates and stores an OTP securely."""
    otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
    hashed_otp = bcrypt.hash(otp)
    otp_store[phone] = {"otp": hashed_otp, "expires_at": time.time() + 300}
    return otp

async def send_whatsapp_message(to: str, body: str):
    """Sends a WhatsApp message via Twilio."""
    try:
        message = twilio_client.messages.create(
            from_=f"whatsapp:{settings.twilio_whatsapp_number}",
            to=f"whatsapp:+91{to}",
            body=body
        )
        return message.sid
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")
    

    

### ====================== 📌 USER REGISTRATION ====================== ###
@router.post("/register")
async def register_user(user_data: RegisterSchema):
    """Registers a new user and sends OTP via WhatsApp."""
    existing_user = await User.find_one(User.phone == user_data.phone)
    if existing_user:
        if not existing_user.isUserDeleted:
            raise HTTPException(status_code=400, detail="User already exists")
        else:
            existing_user.isUserDeleted = False
            existing_user.name = user_data.name
            await existing_user.save()
    else:
        user = User(
            id=str(uuid.uuid4()), 
            name=user_data.name,
            phone=user_data.phone,
            role="user",
            isPhoneVerified=False,
            isUserDeleted=False
        )
        await user.insert()

    otp = generate_otp(user_data.phone)

    await send_whatsapp_message(
        user_data.phone,
        f"""
🔐 *WaHire OTP Verification*

Dear *{user_data.name}*,

Your OTP for verification is: *{otp}*
Valid for *5 minutes*. Do not share it.

Thank you for choosing *WaHire*! 🚀
"""
    )

    return {"message": "User registered successfully. OTP sent."}



### ====================== 📌 VERIFY OTP ====================== ###
@router.post("/verify-otp")
async def verify_otp(otp_data: OTPVerifySchema):
    """Verifies OTP and updates user verification status."""
    otp_entry = otp_store.get(otp_data.phone)
    
    if not otp_entry or time.time() > otp_entry["expires_at"]:
        del otp_store[otp_data.phone]
        raise HTTPException(status_code=400, detail="OTP expired or invalid")

    if not bcrypt.verify(otp_data.otp, otp_entry["otp"]):
        raise HTTPException(status_code=400, detail="Incorrect OTP")

    user = await User.find_one(User.phone == otp_data.phone)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.isPhoneVerified = True
    await user.save()

    del otp_store[otp_data.phone]  

    await send_whatsapp_message(
        otp_data.phone,
        f""" 🎉 Welcome to WaHire – Your Professional Job Network! 🎉

✅ Your account has been successfully verified!

🚀 What’s Next? 
🔍 Receive personalized job alerts tailored to your skills 
💼 Explore exclusive job opportunities with top employers 
🤝 Connect with leading companies and grow your career

✨ We’re here to support you every step of the way!

📢 Stay tuned for exciting job updates! 

💡 Tip: Keep your profile updated to receive the best job matches!

Best Regards, 
The WaHire Team 🚀
"""
    )

    return {"message": "OTP verified successfully"}



### ====================== 📌 FETCH ALL USERS ====================== ###
@router.get("/get-all-users")
async def get_all_users():
    """Fetches all users."""
    users = await User.find_all().to_list()
    return users



### ====================== 📌 FETCH USER BY ID ====================== ###
@router.get("/{user_id}")
async def get_user_by_id(user_id: str):
    """Fetches a user by their ID (UUID)."""
    user = await User.get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user



### ====================== 📌 UPDATE USER ====================== ###
@router.patch("/{phone}")
async def update_user(phone: str, user_data: UpdateUserSchema):
    """Updates user details."""
    user = await User.find_one(User.phone == phone)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.name = user_data.name
    await user.save()

    return {"message": "User updated successfully"}



### ====================== 📌 SOFT DELETE USER ====================== ###
@router.delete("/{phone}")
async def delete_user(phone: str):
    """Soft deletes a user by setting isUserDeleted = True."""
    user = await User.find_one(User.phone == phone)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.isUserDeleted = True
    await user.save()

    return {"message": "User deleted successfully"}
