from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class User:
    id: Optional[int]
    email: str
    hashed_password: str
    full_name: str
    is_active: bool
    role: str
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    verification_token: Optional[str] = None
    reset_token: Optional[str] = None
    reset_token_expires: Optional[datetime] = None
    
    # Profile parameters
    phone_number: Optional[str] = None
    profile_photo: Optional[str] = None
    language: str = "en"
    timezone: str = "UTC"
    notification_preferences: str = "email,sms,push"
    status: str = "active"
