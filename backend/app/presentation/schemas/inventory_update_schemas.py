from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class ApplyUpdatePayload(BaseModel):
    product_id: int
    store_id: int
    new_quantity: int = Field(..., ge=0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    notes: Optional[str] = None


class BatchUpdatePayload(BaseModel):
    updates: List[ApplyUpdatePayload]


class UpdateRuleOut(BaseModel):
    id: int
    rule_key: str
    rule_name: str
    value: str
    description: Optional[str]
    is_active: bool

    model_config = {"from_attributes": True}


class UpdateRuleUpdate(BaseModel):
    value: str
    is_active: bool


class InventoryUpdateOut(BaseModel):
    id: int
    store_id: int
    product_id: int
    product_name: str
    sku: str
    previous_quantity: int
    new_quantity: int
    variance: int
    status: str
    confidence: float
    notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class InventoryDifferenceOut(BaseModel):
    product_id: int
    product_name: str
    sku: str
    database_stock: int
    physical_scan: int
    difference: int
    variance_percentage: float
    recommendation: str


class ApprovalRequestOut(BaseModel):
    id: int
    inventory_update_id: int
    requested_by: str
    status: str
    approver_notes: Optional[str]
    reviewed_at: Optional[datetime]
    update_details: InventoryUpdateOut

    model_config = {"from_attributes": True}


class RollbackPayload(BaseModel):
    rollback_batch_tag: str
    store_id: int
