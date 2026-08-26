from datetime import datetime
from typing import List, Optional
from decimal import Decimal
from sqlalchemy import String, DateTime, Text, Numeric, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class ProductModel(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    barcode: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    sku: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    category: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    brand: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    brand_id: Mapped[Optional[int]] = mapped_column(ForeignKey("brands.id", ondelete="SET NULL"), nullable=True, index=True)
    variant: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    weight: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    supplier_id: Mapped[Optional[int]] = mapped_column(ForeignKey("suppliers.id", ondelete="SET NULL"), nullable=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Extended specifications
    qr_code: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    unit: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    dimensions: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    cost_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    tax: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0.00, nullable=False)
    shelf_life: Mapped[Optional[int]] = mapped_column(nullable=True)
    expiry_tracking: Mapped[bool] = mapped_column(default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    images: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # comma separated URLs

    # AI Metadata parameters
    yolo_class_mapping: Mapped[Optional[int]] = mapped_column(nullable=True)
    clip_embeddings: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    siglip_embeddings: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array of embeddings
    ocr_reference_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ocr_keywords: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array of keywords
    confidence_threshold: Mapped[float] = mapped_column(default=0.5, nullable=False)
    aliases: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reference_image_count: Mapped[int] = mapped_column(default=0, nullable=False)
    embedding_model_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    suppliers: Mapped[List["SupplierModel"]] = relationship(
        "SupplierModel",
        secondary="product_suppliers",
        back_populates="products"
    )
    inventory_items: Mapped[List["InventoryModel"]] = relationship(
        "InventoryModel",
        back_populates="product",
        cascade="all, delete-orphan"
    )
    order_items: Mapped[List["OrderItemModel"]] = relationship(
        "OrderItemModel",
        back_populates="product",
        cascade="all, delete-orphan"
    )
    scan_detections: Mapped[List["AIScanDetectionModel"]] = relationship(
        "AIScanDetectionModel",
        back_populates="product"
    )
    stock_transactions: Mapped[List["StockTransactionModel"]] = relationship(
        "StockTransactionModel",
        back_populates="product",
        cascade="all, delete-orphan"
    )
    reference_images: Mapped[List["ReferenceImageModel"]] = relationship(
        "ReferenceImageModel",
        back_populates="product",
        cascade="all, delete-orphan"
    )
