import uuid
import random
import time
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from beanie import PydanticObjectId
from app.models.user_model import User
from twilio.rest import Client
from app.config.settings import Settings
from passlib.hash import bcrypt

router = APIRouter()
settings = Settings()

twilio_client = Client(settings.twilio_account_sid, settings.twilio_auth_token)

# Temporary in-memory OTP store (for production, use a database or cache like Redis)
otp_store = {}

### ====================== 📌 REQUEST SCHEMAS ====================== ###
class RegisterSchema(BaseModel):
    name: str
    phone: str

class OTPVerifySchema(BaseModel):
    phone: str
    otp: str

class OTPResendSchema(BaseModel):
    phone: str

class UpdateUserSchema(BaseModel):
    name: str

### ====================== 📌 UTILITY FUNCTIONS ====================== ###

def generate_otp(phone: str) -> str:
    """Generates and stores an OTP securely."""
    otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
    hashed_otp = bcrypt.hash(otp)
    otp_store[phone] = {"otp": hashed_otp, "expires_at": time.time() + 300}  # 5 min expiry
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

def mask_phone(phone: str) -> str:
    """Masks all but the last 4 digits of a phone number."""
    return f"{'*' * (len(phone) - 4)}{phone[-4:]}"

### ====================== 📌 USER REGISTRATION ====================== ###
@router.post("/register")
async def register_user(user_data: RegisterSchema):
    """Registers a new user and sends OTP via WhatsApp."""
    
    existing_user = await User.find_one(User.phone == mask_phone(user_data.phone))
    
    if existing_user and not existing_user.isUserDeleted:
        raise HTTPException(status_code=400, detail="User with this phone number already exists.")

    if existing_user and existing_user.isUserDeleted:
        existing_user.isUserDeleted = False
        existing_user.name = user_data.name
        await existing_user.save()

    else:
        user = User(
            id=str(uuid.uuid4()), 
            name=user_data.name,
            phone=mask_phone(user_data.phone), 
            role="user",
            isPhoneVerified=False,
            isUserDeleted=False
        )
        await user.insert()

    otp = generate_otp(user_data.phone)  
    await send_whatsapp_message(user_data.phone, 
  f"""
🔐 *WaHire OTP Verification*

Dear *{user_data.name}*,

Your OTP for verification is: *{otp}*
Valid for *5 minutes*. Do not share it.

Thank you for choosing *WaHire*! 🚀
""")

    return {"message": f"User registered successfully. OTP sent to {mask_phone(user_data.phone)}."}


### ====================== 📌 VERIFY OTP ====================== ###
@router.post("/verify-otp")
async def verify_otp(otp_data: OTPVerifySchema):
    """Verifies OTP and updates user verification status."""
    
    otp_entry = otp_store.get(otp_data.phone)
    if not otp_entry or time.time() > otp_entry["expires_at"]:
        otp_store.pop(otp_data.phone, None)  
        raise HTTPException(status_code=400, detail="OTP expired or invalid")

    if not bcrypt.verify(otp_data.otp, otp_entry["otp"]):
        raise HTTPException(status_code=400, detail="Incorrect OTP")

    masked_phone = mask_phone(otp_data.phone)

    user = await User.find_one(User.phone == masked_phone)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.isPhoneVerified = True
    await user.save()

    otp_store.pop(otp_data.phone, None)
    await send_whatsapp_message(
        otp_data.phone,
        f"""
🎉 *Welcome to WaHire – Your Trusted Career Partner!* 🎉  

Dear *{user.name}*,  

✅ *Your account has been successfully verified!*  
You now have full access to exclusive job opportunities, career insights, and personalized recommendations.  

🚀 *What’s Next?*  
🔍 *Explore Curated Job Openings:* Find roles that align with your skills and aspirations.  
💼 *Connect with Top Employers:* Gain direct access to leading organizations.  
📈 *Enhance Your Professional Profile:* Stay ahead by keeping your profile updated.  

💡 *Pro Tip:* A well-optimized profile increases your chances of landing the perfect job!  

📩 *Need Assistance?* Our support team is here to help: [support@wahire.com](mailto:support@wahire.com).  

We’re excited to be part of your career journey!  

Best Regards,  
🚀 *The WaHire Team*  
"""
    )

    return {"message": f"OTP verified successfully for {masked_phone}."}


### ====================== 📌 RESEND OTP ====================== ###
@router.post("/resend-otp")
async def resend_otp(otp_data: OTPResendSchema):
    """Resends OTP to the user for verification."""
    
    masked_phone = mask_phone(otp_data.phone)

    user = await User.find_one(User.phone == masked_phone)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.isPhoneVerified:
        raise HTTPException(status_code=400, detail="User is already verified")

    masked_phone = mask_phone(otp_data.phone)

    otp = generate_otp(otp_data.phone)
    
    otp_store[otp_data.phone] = {
        "otp": bcrypt.hash(otp),
        "expires_at": time.time() + 300  
    }

    await send_whatsapp_message(
        otp_data.phone,
        f"""
🔐 *WaHire OTP Resend Request*  

Dear *{user.name}*,  

Your new OTP for verification is: *{otp}*  
This OTP is valid for *5 minutes*. Do not share it with anyone.  

🚀 Secure your WaHire account and unlock exclusive job opportunities!  

Best Regards,  
🚀 *The WaHire Team*  
"""
    )

    return {"message": f"New OTP sent successfully to {masked_phone}."}


### ====================== 📌 FETCH ALL USERS ====================== ###
@router.get("/get-all-users")
async def get_all_users():
    """Fetches all users."""
    users = await User.find(User.isPhoneVerified == True).to_list()
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
    masked_phone = mask_phone(phone)

    user = await User.find_one(User.phone == masked_phone)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.name = user_data.name
    await user.save()

    return {"message": "User updated successfully"}



### ====================== 📌 SOFT DELETE USER ====================== ###
@router.delete("/{phone}")
async def delete_user(phone: str):
    """Soft deletes a user by setting isUserDeleted = True."""
@router.delete("/{phone}")
async def delete_user(phone: str):
    """Soft deletes a user by setting isUserDeleted = True."""
    masked_phone = mask_phone(phone)

    user = await User.find_one(User.phone == masked_phone)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.isUserDeleted = True
    await user.save()

    return {"message": "User deleted successfully"}
