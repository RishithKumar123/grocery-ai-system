from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class InventoryItemCreate(BaseModel):
    name: str = Field(..., min_length=1)
    sku: str = Field(..., min_length=1)
    quantity: int = Field(default=0, ge=0)
    available_stock: int = Field(default=0, ge=0)
    reserved_stock: int = Field(default=0, ge=0)
    damaged_stock: int = Field(default=0, ge=0)
    min_stock: int = Field(default=5, ge=0)
    max_stock: int = Field(default=100, ge=0)
    reorder_level: int = Field(default=15, ge=0)
    expiry_date: Optional[date] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    image_url: Optional[str] = None


class InventoryItemUpdate(BaseModel):
    name: Optional[str] = None
    sku: Optional[str] = None
    quantity: Optional[int] = Field(None, ge=0)
    available_stock: Optional[int] = Field(None, ge=0)
    reserved_stock: Optional[int] = Field(None, ge=0)
    damaged_stock: Optional[int] = Field(None, ge=0)
    min_stock: Optional[int] = Field(None, ge=0)
    max_stock: Optional[int] = Field(None, ge=0)
    reorder_level: Optional[int] = Field(None, ge=0)
    expiry_date: Optional[date] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    image_url: Optional[str] = None


class InventoryItemOut(BaseModel):
    id: int
    name: str
    sku: str
    quantity: int
    available_stock: int
    reserved_stock: int
    damaged_stock: int
    min_stock: int
    max_stock: int
    reorder_level: int
    expiry_date: Optional[date] = None
    confidence: Optional[float] = None
    image_url: Optional[str] = None
    stock_valuation: float = 0.0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
