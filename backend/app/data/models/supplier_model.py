from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, DateTime, Text, Boolean, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


# Many-to-many link table between Products and Suppliers
class ProductSupplierLink(Base):
    __tablename__ = "product_suppliers"

    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id", ondelete="CASCADE"), primary_key=True)
    supplier_id: Mapped[int] = mapped_column(Integer, ForeignKey("suppliers.id", ondelete="CASCADE"), primary_key=True)


class SupplierModel(Base):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    company_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact_person: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    gst_vat: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    region: Mapped[Optional[str]] = mapped_column(String(100), nullable=True) # GST/VAT region e.g. IN, EU
    payment_terms: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # e.g. Net 30, COD
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # Many-to-many relationship with ProductModel
    products: Mapped[List["ProductModel"]] = relationship(
        "ProductModel",
        secondary="product_suppliers",
        back_populates="suppliers"
    )

    orders: Mapped[List["OrderModel"]] = relationship(
        "OrderModel",
        back_populates="supplier"
    )
