from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, DateTime, ForeignKey, Float, Integer, JSON, func, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class CountingJobModel(Base):
    __tablename__ = "counting_jobs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    video_id: Mapped[Optional[int]] = mapped_column(ForeignKey("videos.id", ondelete="SET NULL"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(50), default="Running", index=True, nullable=False) # Running, Completed, Stopped, Failed
    started_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    total_counted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    average_confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    store: Mapped["StoreModel"] = relationship("StoreModel")
    video: Mapped[Optional["VideoModel"]] = relationship("VideoModel")
    results: Mapped[List["CountingResultModel"]] = relationship("CountingResultModel", back_populates="job", cascade="all, delete-orphan")
    tracks: Mapped[List["TrackedObjectModel"]] = relationship("TrackedObjectModel", back_populates="job", cascade="all, delete-orphan")
    statistics: Mapped[Optional["CountStatisticsModel"]] = relationship("CountStatisticsModel", back_populates="job", cascade="all, delete-orphan")
    validations: Mapped[List["CountValidationModel"]] = relationship("CountValidationModel", back_populates="job", cascade="all, delete-orphan")
    history_entries: Mapped[List["CountHistoryModel"]] = relationship("CountHistoryModel", back_populates="job", cascade="all, delete-orphan")


class CountingResultModel(Base):
    __tablename__ = "counting_results"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("counting_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[Optional[int]] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)
    raw_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    verified_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duplicate_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rejected_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    job: Mapped["CountingJobModel"] = relationship("CountingJobModel", back_populates="results")
    product: Mapped[Optional["ProductModel"]] = relationship("ProductModel")

    @property
    def product_name(self) -> str:
        return self.product.name if self.product else "Unknown Product"


class TrackedObjectModel(Base):
    __tablename__ = "tracked_objects"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("counting_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    track_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    product_id: Mapped[Optional[int]] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    bounding_box: Mapped[dict] = mapped_column(JSON().with_variant(JSONB, "postgresql"), nullable=False)  # {"xmin", "ymin", "xmax", "ymax"}
    start_frame: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    end_frame: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="Active", index=True, nullable=False) # Active, Lost, Terminated
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    job: Mapped["CountingJobModel"] = relationship("CountingJobModel", back_populates="tracks")
    product: Mapped[Optional["ProductModel"]] = relationship("ProductModel")

    @property
    def product_name(self) -> str:
        return self.product.name if self.product else "Unknown Product"


class CountStatisticsModel(Base):
    __tablename__ = "count_statistics"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("counting_jobs.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    total_products_counted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    average_counting_accuracy: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    duplicate_detection_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    tracking_accuracy: Mapped[float] = mapped_column(Float, default=100.0, nullable=False)
    processing_speed: Mapped[float] = mapped_column(Float, default=30.0, nullable=False) # FPS
    products_per_minute: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    job: Mapped["CountingJobModel"] = relationship("CountingJobModel", back_populates="statistics")


class CountValidationModel(Base):
    __tablename__ = "count_validation"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("counting_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    validation_rule_key: Mapped[str] = mapped_column(String(100), nullable=False) # e.g. "min_confidence"
    value: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="Passed", nullable=False) # Passed, Failed
    validation_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    job: Mapped["CountingJobModel"] = relationship("CountingJobModel", back_populates="validations")


class CountHistoryModel(Base):
    __tablename__ = "count_history"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    product_id: Mapped[Optional[int]] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)
    shelf_id: Mapped[Optional[int]] = mapped_column(ForeignKey("shelves.id", ondelete="SET NULL"), nullable=True, index=True)
    count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    verified_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    job_id: Mapped[int] = mapped_column(ForeignKey("counting_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    job: Mapped["CountingJobModel"] = relationship("CountingJobModel", back_populates="history_entries")
    product: Mapped[Optional["ProductModel"]] = relationship("ProductModel")
    shelf: Mapped[Optional["ShelfModel"]] = relationship("ShelfModel")
