from fastapi import APIRouter, HTTPException
from models.admin_models import EmailVerify,OTPVerify, Admin
from passlib.context import CryptContext
from datetime import datetime, timedelta
from email.message import EmailMessage
from dotenv import load_dotenv
from database import db  
import smtplib
import os
import random


load_dotenv()
router = APIRouter()
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def send_email(to_email: str, subject: str, body: str):
    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = subject
    msg["From"] = os.getenv("EMAIL")
    msg["To"] = to_email
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(os.getenv("EMAIL"), os.getenv("EMAIL_VERIFICATION_PASSWORD"))
        server.send_message(msg)

@router.post("/send-signup-otp")
async def send_otp(data: EmailVerify):
    try:
        email = data.email
        existing_user = await db.admins.find_one({"email": email})
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail={"email": "Email already registered"}
            )
        otp = str(random.randint(100000, 999999))
        expires_at = datetime.utcnow() + timedelta(minutes=5)
        await db.otps.update_one(
            {"email": email},
            {"$set": {"otp": otp, "expires_at": expires_at, "verified": False}},
            upsert=True
        )
        send_email(email, "Your KisanAi OTP", f"Your OTP is: {otp}")
        return {"message": "OTP sent successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"general": f"Failed to send OTP: {str(e)}"}
        )

@router.post("/verify-otp")
async def verify_otp(data: OTPVerify):
    record = await db.otps.find_one({"email": data.email})
    if not record:
        raise HTTPException(status_code=404, detail="OTP not found")
    if record["otp"] != data.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP")
    if datetime.utcnow() > record["expires_at"]:
        raise HTTPException(status_code=400, detail="OTP expired")
    await db.otps.update_one(
        {"email": data.email},
        {"$set": {"verified": True}}
    )
    return {"message": "OTP verified successfully"}


@router.post("/signup")
async def signup(data: Admin):
    existing_user = await db.admins.find_one({"email": data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    otp_record = await db.otps.find_one({"email": data.email})
    if not otp_record or not otp_record.get("verified", False):
        raise HTTPException(status_code=400, detail="Email not verified")
    hashed_password = pwd_context.hash(data.password[:72])
    new_admin = {
        "name": data.name,
        "email": data.email,
        "password": hashed_password,
        "profile_picture": str(data.profile_picture) if data.profile_picture else None,
        "isEmailVerified": True
    }
    await db.admins.insert_one(new_admin)
    await db.otps.delete_one({"email": data.email})
    return {"message": "Account created successfully"}

@router.get("/login/{email}")
async def login(email: str):
    print("Received email:", email)
    user = await db.admins.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user["_id"] = str(user["_id"])
    return {
        "message": "Login success",
        "user": user
    }
