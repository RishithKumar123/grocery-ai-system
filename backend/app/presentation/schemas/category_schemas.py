from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    parent_id: Optional[int] = None
    image_url: Optional[str] = Field(default=None, max_length=500)
    icon_name: Optional[str] = Field(default=None, max_length=100)
    is_active: bool = True
    order_index: int = 0


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    parent_id: Optional[int] = None
    image_url: Optional[str] = Field(default=None, max_length=500)
    icon_name: Optional[str] = Field(default=None, max_length=100)
    is_active: Optional[bool] = None
    order_index: Optional[int] = None


class CategoryOut(CategoryBase):
    id: int
    deleted_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CategoryTreeOut(CategoryOut):
    children: List["CategoryTreeOut"] = []

    model_config = ConfigDict(from_attributes=True)
