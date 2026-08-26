from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


@dataclass
class InventoryItem:
    id: Optional[int]
    name: str
    sku: str
    quantity: int
    available_stock: int
    reserved_stock: int
    damaged_stock: int
    min_stock: int
    max_stock: int
    reorder_level: int
    expiry_date: Optional[date]
    confidence: Optional[float]
    image_url: Optional[str]
    created_at: datetime
    updated_at: datetime
    stock_valuation: float = 0.0
