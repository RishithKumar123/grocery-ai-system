from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class StoreCreate(BaseModel):
    name: str = Field(..., min_length=1)
    location: Optional[str] = None
    address: Optional[str] = None
    contact: Optional[str] = None
    timezone: str = "UTC"
    is_active: bool = True
    settings: Optional[str] = None


class StoreUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    address: Optional[str] = None
    contact: Optional[str] = None
    timezone: Optional[str] = None
    is_active: Optional[bool] = None
    settings: Optional[str] = None


class StoreOut(BaseModel):
    id: int
    name: str
    location: Optional[str] = None
    address: Optional[str] = None
    contact: Optional[str] = None
    timezone: str
    is_active: bool
    settings: Optional[str] = None
    total_stock: int = 0
    employee_count: int = 0
    vendor_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StoreUserOut(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    is_verified: bool

    model_config = ConfigDict(from_attributes=True)


class UserAssignment(BaseModel):
    user_id: int
