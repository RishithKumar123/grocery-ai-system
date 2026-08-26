from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class StockTransactionCreate(BaseModel):
    store_id: int
    product_id: int
    transaction_type: str  # "Purchase", "Sale", "Return", "Adjustment", "Damage", "Transfer", "Expiry", "AI Scan Update"
    quantity_change: int
    notes: Optional[str] = None


class StockTransactionOut(BaseModel):
    id: int
    store_id: int
    product_id: int
    user_id: Optional[int] = None
    transaction_type: str
    quantity_change: int
    previous_quantity: int
    new_quantity: int
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
