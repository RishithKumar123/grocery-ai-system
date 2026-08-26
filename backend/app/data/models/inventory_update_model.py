from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, DateTime, ForeignKey, Float, Integer, Text, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class InventoryUpdateModel(Base):
    __tablename__ = "inventory_updates"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    previous_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    new_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    variance: Mapped[int] = mapped_column(Integer, default=0, nullable=False) # new_quantity - previous_quantity
    status: Mapped[str] = mapped_column(String(50), default="Pending", nullable=False) # Pending, Approved, Rejected, Applied, Rolled Back
    confidence: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    product: Mapped["ProductModel"] = relationship("ProductModel")
    store: Mapped["StoreModel"] = relationship("StoreModel")
    adjustments: Mapped[List["InventoryAdjustmentModel"]] = relationship("InventoryAdjustmentModel", back_populates="inventory_update", cascade="all, delete-orphan")
    approval_requests: Mapped[List["ApprovalRequestModel"]] = relationship("ApprovalRequestModel", back_populates="inventory_update", cascade="all, delete-orphan")


class InventoryAdjustmentModel(Base):
    __tablename__ = "inventory_adjustments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    inventory_update_id: Mapped[Optional[int]] = mapped_column(ForeignKey("inventory_updates.id", ondelete="SET NULL"), nullable=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    adjustment_type: Mapped[str] = mapped_column(String(100), nullable=False) # Stock Increase, Stock Decrease, Rollback, Manual Override
    quantity_adjusted: Mapped[int] = mapped_column(Integer, nullable=False)
    adjusted_by_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    inventory_update: Mapped[Optional["InventoryUpdateModel"]] = relationship("InventoryUpdateModel", back_populates="adjustments")
    product: Mapped["ProductModel"] = relationship("ProductModel")
    store: Mapped["StoreModel"] = relationship("StoreModel")


class InventoryReconciliationModel(Base):
    __tablename__ = "inventory_reconciliation"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    scanned_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    total_items_db: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_items_ai: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    variance_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    accuracy_rate: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)

    # Relationships
    store: Mapped["StoreModel"] = relationship("StoreModel")


class InventorySnapshotModel(Base):
    __tablename__ = "inventory_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot_batch_tag: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    product: Mapped["ProductModel"] = relationship("ProductModel")
    store: Mapped["StoreModel"] = relationship("StoreModel")


class UpdateRuleModel(Base):
    __tablename__ = "update_rules"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    rule_key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    rule_name: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class UpdateQueueModel(Base):
    __tablename__ = "update_queue"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    inventory_update_id: Mapped[int] = mapped_column(ForeignKey("inventory_updates.id", ondelete="CASCADE"), nullable=False, index=True)
    process_status: Mapped[str] = mapped_column(String(50), default="Queued", nullable=False) # Queued, Processing, Success, Failed
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class ApprovalRequestModel(Base):
    __tablename__ = "approval_requests"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    inventory_update_id: Mapped[int] = mapped_column(ForeignKey("inventory_updates.id", ondelete="CASCADE"), nullable=False, index=True)
    requested_by: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="Pending", nullable=False) # Pending, Approved, Rejected
    approver_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    inventory_update: Mapped["InventoryUpdateModel"] = relationship("InventoryUpdateModel", back_populates="approval_requests")


class RollbackHistoryModel(Base):
    __tablename__ = "rollback_history"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    rollback_batch_tag: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    rolled_back_by_user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    reverted_records_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    store: Mapped["StoreModel"] = relationship("StoreModel")
