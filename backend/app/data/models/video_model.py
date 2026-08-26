from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class VideoModel(Base):
    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    camera_name: Mapped[str] = mapped_column(String(255), nullable=False)
    video_url: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="Pending", index=True, nullable=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    store: Mapped["StoreModel"] = relationship("StoreModel", back_populates="videos")
    scans: Mapped[List["AIScanModel"]] = relationship(
        "AIScanModel",
        back_populates="video",
        cascade="all, delete-orphan"
    )
