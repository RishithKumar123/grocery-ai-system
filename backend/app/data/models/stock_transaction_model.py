from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class StockTransactionModel(Base):
    __tablename__ = "stock_transactions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True) 
    # "Purchase", "Sale", "Return", "Adjustment", "Damage", "Transfer", "Expiry", "AI Scan Update"
    
    quantity_change: Mapped[int] = mapped_column(Integer, nullable=False)
    previous_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    new_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    store: Mapped["StoreModel"] = relationship("StoreModel", back_populates="stock_transactions")
    product: Mapped["ProductModel"] = relationship("ProductModel", back_populates="stock_transactions")
    user: Mapped[Optional["UserModel"]] = relationship("UserModel")
