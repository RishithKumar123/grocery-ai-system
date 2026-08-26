from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    full_name: str = Field(..., min_length=1)
    role: str = Field(default="Shopkeeper", pattern="^(Admin|Vendor|Shopkeeper)$")


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class VerifyEmailRequest(BaseModel):
    token: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6)


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    is_active: bool
    role: str
    is_verified: bool
    
    # Profile Extensions
    phone_number: Optional[str] = None
    profile_photo: Optional[str] = None
    language: str
    timezone: str
    notification_preferences: str
    status: str
    
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    profile_photo: Optional[str] = None
    language: Optional[str] = None
    timezone: Optional[str] = None
    notification_preferences: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6)


class ResendVerificationRequest(BaseModel):
    email: EmailStr


