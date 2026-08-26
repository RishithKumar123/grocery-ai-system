from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, DateTime, Column, ForeignKey, Table, Integer, func, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

# Association table for User-Store many-to-many relationship
user_store_assignments = Table(
    "user_store_assignments",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("store_id", Integer, ForeignKey("stores.id", ondelete="CASCADE"), primary_key=True),
    Column("assigned_at", DateTime, default=func.now())
)


class StoreModel(Base):
    __tablename__ = "stores"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contact: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    settings: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # JSON settings
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    users: Mapped[List["UserModel"]] = relationship(
        "UserModel",
        secondary=user_store_assignments,
        back_populates="stores"
    )
    inventory_items: Mapped[List["InventoryModel"]] = relationship(
        "InventoryModel",
        back_populates="store",
        cascade="all, delete-orphan"
    )
    videos: Mapped[List["VideoModel"]] = relationship(
        "VideoModel",
        back_populates="store",
        cascade="all, delete-orphan"
    )
    orders: Mapped[List["OrderModel"]] = relationship(
        "OrderModel",
        back_populates="store",
        cascade="all, delete-orphan"
    )
    scans: Mapped[List["AIScanModel"]] = relationship(
        "AIScanModel",
        back_populates="store",
        cascade="all, delete-orphan"
    )
    shelves: Mapped[List["ShelfModel"]] = relationship(
        "ShelfModel",
        back_populates="store",
        cascade="all, delete-orphan"
    )
    stock_transactions: Mapped[List["StockTransactionModel"]] = relationship(
        "StockTransactionModel",
        back_populates="store",
        cascade="all, delete-orphan"
    )
