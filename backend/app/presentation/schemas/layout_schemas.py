from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ShelfCreate(BaseModel):
    store_id: int
    aisle: str = Field(..., min_length=1)
    shelf_level: str = Field(..., min_length=1)
    section: str = Field(..., min_length=1)
    bin_rack: str = Field(..., min_length=1)
    capacity: int = Field(50, ge=1)
    status: str = "active"


class ShelfUpdate(BaseModel):
    aisle: Optional[str] = None
    shelf_level: Optional[str] = None
    section: Optional[str] = None
    bin_rack: Optional[str] = None
    capacity: Optional[int] = None
    status: Optional[str] = None


class ShelfOut(BaseModel):
    id: int
    store_id: int
    aisle: str
    shelf_level: str
    section: str
    bin_rack: str
    capacity: int
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
