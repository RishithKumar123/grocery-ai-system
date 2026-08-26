from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class BrandBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    logo_url: Optional[str] = Field(default=None, max_length=500)
    description: Optional[str] = Field(default=None, max_length=1000)
    country_of_origin: Optional[str] = Field(default=None, max_length=100)
    website: Optional[str] = Field(default=None, max_length=255)
    is_active: bool = True


class BrandCreate(BrandBase):
    pass


class BrandUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    logo_url: Optional[str] = Field(default=None, max_length=500)
    description: Optional[str] = Field(default=None, max_length=1000)
    country_of_origin: Optional[str] = Field(default=None, max_length=100)
    website: Optional[str] = Field(default=None, max_length=255)
    is_active: Optional[bool] = None


class BrandOut(BrandBase):
    id: int
    deleted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
