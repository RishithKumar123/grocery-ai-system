from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, ForeignKey, Integer, func, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Index
from app.core.database import Base


class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    table_name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    record_id: Mapped[Optional[int]] = mapped_column(Integer, index=True, nullable=True)
    payload: Mapped[dict] = mapped_column(JSON().with_variant(JSONB, "postgresql"), default=dict, nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    user: Mapped[Optional["UserModel"]] = relationship("UserModel", back_populates="audit_logs")

    # Index on JSONB payload for GIN query parsing
    __table_args__ = (
        Index("idx_audit_logs_payload", payload, postgresql_using="gin"),
    )
