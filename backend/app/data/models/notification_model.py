from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, ForeignKey, Boolean, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Index
from app.core.database import Base


class NotificationModel(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    store_id: Mapped[Optional[int]] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)  # Expiry, Low Stock, etc.
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    user: Mapped["UserModel"] = relationship("UserModel", back_populates="notifications")
    store: Mapped[Optional["StoreModel"]] = relationship("StoreModel")

    # Partial Index for unread notifications optimization
    __table_args__ = (
        Index(
            "idx_notifications_unread",
            user_id,
            postgresql_where=(is_read == False)
        ),
    )
