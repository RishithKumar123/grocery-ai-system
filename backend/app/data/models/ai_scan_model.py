from datetime import date, datetime
from typing import List, Optional
from sqlalchemy import String, DateTime, ForeignKey, Float, Date, Text, func, JSON, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Index
from app.core.database import Base


class AIScanModel(Base):
    __tablename__ = "ai_scans"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    video_id: Mapped[Optional[int]] = mapped_column(ForeignKey("videos.id", ondelete="SET NULL"), nullable=True, index=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    scanned_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="Success", index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # Performance Tracking fields
    scan_start_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    scan_end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    scan_duration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    frames_processed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    fps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    progress_percentage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    progress_stage: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Relationships
    video: Mapped[Optional["VideoModel"]] = relationship("VideoModel", back_populates="scans")
    store: Mapped["StoreModel"] = relationship("StoreModel", back_populates="scans")
    scanned_by: Mapped[Optional["UserModel"]] = relationship("UserModel")
    detections: Mapped[List["AIScanDetectionModel"]] = relationship(
        "AIScanDetectionModel",
        back_populates="scan",
        cascade="all, delete-orphan"
    )


class AIScanDetectionModel(Base):
    __tablename__ = "ai_scan_detections"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    scan_id: Mapped[int] = mapped_column(ForeignKey("ai_scans.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[Optional[int]] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)
    shelf_id: Mapped[Optional[int]] = mapped_column(ForeignKey("shelves.id", ondelete="SET NULL"), nullable=True, index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    bounding_box: Mapped[dict] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=False)  # {"xmin", "ymin", "xmax", "ymax"}
    expiry_date_detected: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    raw_ocr_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    scan: Mapped["AIScanModel"] = relationship("AIScanModel", back_populates="detections")
    product: Mapped[Optional["ProductModel"]] = relationship("ProductModel", back_populates="scan_detections")
    shelf: Mapped[Optional["ShelfModel"]] = relationship("ShelfModel")

    # Scale GIN indexing on JSONB bounding box values
    __table_args__ = (
        Index("idx_detections_bounding_box", bounding_box, postgresql_using="gin"),
    )
