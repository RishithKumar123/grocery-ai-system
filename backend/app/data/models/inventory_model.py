from datetime import date, datetime
from typing import Optional
from sqlalchemy import String, Integer, Float, Date, DateTime, ForeignKey, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class InventoryModel(Base):
    __tablename__ = "inventory_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    sku: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False) # Current stock
    available_stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reserved_stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    damaged_stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    min_stock: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    max_stock: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    reorder_level: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    expiry_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    location_bin: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="In Stock", index=True, nullable=False)
    
    shelf_id: Mapped[Optional[int]] = mapped_column(ForeignKey("shelves.id", ondelete="SET NULL"), nullable=True, index=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    store: Mapped["StoreModel"] = relationship("StoreModel", back_populates="inventory_items")
    product: Mapped["ProductModel"] = relationship("ProductModel", back_populates="inventory_items")
    shelf: Mapped[Optional["ShelfModel"]] = relationship("ShelfModel", back_populates="inventory_items")

    @property
    def stock_valuation(self) -> float:
        if self.product:
            return float(self.quantity * self.product.price)
        return 0.0

    # Composite Index for rapid store lookup on products
    __table_args__ = (
        Index("idx_inventory_store_product", store_id, product_id),
    )

