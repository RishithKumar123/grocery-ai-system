from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1)
    barcode: str = Field(..., min_length=1)
    sku: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)
    brand: Optional[str] = None
    variant: Optional[str] = None
    weight: Optional[str] = None
    price: float = Field(default=0.00, ge=0.0)
    description: Optional[str] = None
    supplier_id: Optional[int] = None
    initial_stock: Optional[int] = Field(default=0, ge=0)
    store_id: Optional[int] = None
    
    # Extended specifications
    qr_code: Optional[str] = None
    unit: Optional[str] = None
    dimensions: Optional[str] = None
    cost_price: float = Field(default=0.00, ge=0.0)
    tax: float = Field(default=0.00, ge=0.0)
    shelf_life: Optional[int] = None
    expiry_tracking: bool = False
    status: str = "active"
    images: Optional[str] = None

    # AI Metadata parameters
    yolo_class_mapping: Optional[int] = None
    clip_embeddings: Optional[str] = None
    ocr_reference_text: Optional[str] = None
    confidence_threshold: float = 0.5
    aliases: Optional[str] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    barcode: Optional[str] = None
    sku: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    variant: Optional[str] = None
    weight: Optional[str] = None
    price: Optional[float] = None
    description: Optional[str] = None
    supplier_id: Optional[int] = None

    # Extended specifications
    qr_code: Optional[str] = None
    unit: Optional[str] = None
    dimensions: Optional[str] = None
    cost_price: Optional[float] = None
    tax: Optional[float] = None
    shelf_life: Optional[int] = None
    expiry_tracking: Optional[bool] = None
    status: Optional[str] = None
    images: Optional[str] = None

    # AI Metadata parameters
    yolo_class_mapping: Optional[int] = None
    clip_embeddings: Optional[str] = None
    ocr_reference_text: Optional[str] = None
    confidence_threshold: Optional[float] = None
    aliases: Optional[str] = None


class ProductOut(BaseModel):
    id: int
    name: str
    barcode: str
    sku: str
    category: str
    brand: Optional[str] = None
    variant: Optional[str] = None
    weight: Optional[str] = None
    price: float
    image_url: Optional[str] = None
    description: Optional[str] = None
    supplier_id: Optional[int] = None
    supplier_name: Optional[str] = None
    total_stock: int = 0
    created_at: datetime
    updated_at: datetime

    # Extended specifications
    qr_code: Optional[str] = None
    unit: Optional[str] = None
    dimensions: Optional[str] = None
    cost_price: float
    tax: float
    shelf_life: Optional[int] = None
    expiry_tracking: bool
    status: str
    images: Optional[str] = None

    # AI Metadata parameters
    yolo_class_mapping: Optional[int] = None
    clip_embeddings: Optional[str] = None
    ocr_reference_text: Optional[str] = None
    confidence_threshold: float
    aliases: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SupplierOut(BaseModel):
    id: int
    name: str
    company_name: Optional[str] = None
    contact_person: Optional[str] = None
    contact_email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    gst_vat: Optional[str] = None
    region: Optional[str] = None
    payment_terms: Optional[str] = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SupplierCreate(BaseModel):
    name: str = Field(..., min_length=1)
    company_name: Optional[str] = None
    contact_person: Optional[str] = None
    contact_email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    gst_vat: Optional[str] = None
    region: Optional[str] = None
    payment_terms: Optional[str] = None
    is_active: bool = True


class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    company_name: Optional[str] = None
    contact_person: Optional[str] = None
    contact_email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    gst_vat: Optional[str] = None
    region: Optional[str] = None
    payment_terms: Optional[str] = None
    is_active: Optional[bool] = None
