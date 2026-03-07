from pydantic import BaseModel, EmailStr, HttpUrl
from typing import Optional

class EmailVerify(BaseModel):
    email: EmailStr

class OTPVerify(BaseModel):
    email: EmailStr
    otp: str

class Admin(BaseModel):
    name: str
    email: EmailStr
    password: str
    profile_picture: Optional[HttpUrl] = None