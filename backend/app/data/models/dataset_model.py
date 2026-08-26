from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, DateTime, Boolean, ForeignKey, Text, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class DatasetModel(Base):
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    dataset_type: Mapped[str] = mapped_column(String(50), nullable=False, default="training")
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False, index=True)
    visibility: Mapped[str] = mapped_column(String(50), default="private", nullable=False)
    owner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
    current_version: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    archived_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tags: Mapped[List["DatasetTagModel"]] = relationship(
        "DatasetTagModel",
        back_populates="dataset",
        cascade="all, delete-orphan"
    )
    versions: Mapped[List["DatasetVersionModel"]] = relationship(
        "DatasetVersionModel",
        back_populates="dataset",
        cascade="all, delete-orphan"
    )
    statistics: Mapped[Optional["DatasetStatisticsModel"]] = relationship(
        "DatasetStatisticsModel",
        back_populates="dataset",
        uselist=False,
        cascade="all, delete-orphan"
    )
    images: Mapped[List["DatasetImageModel"]] = relationship(
        "DatasetImageModel",
        back_populates="dataset",
        cascade="all, delete-orphan"
    )
    videos: Mapped[List["DatasetVideoModel"]] = relationship(
        "DatasetVideoModel",
        back_populates="dataset",
        cascade="all, delete-orphan"
    )
    metadata_entries: Mapped[List["DatasetMetadataModel"]] = relationship(
        "DatasetMetadataModel",
        back_populates="dataset",
        cascade="all, delete-orphan"
    )


class DatasetTagModel(Base):
    __tablename__ = "dataset_tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    dataset: Mapped["DatasetModel"] = relationship("DatasetModel", back_populates="tags")


class DatasetVersionModel(Base):
    __tablename__ = "dataset_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    version_tag: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    archive_url: Mapped[str] = mapped_column(String(500), nullable=False)
    file_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    dataset: Mapped["DatasetModel"] = relationship("DatasetModel", back_populates="versions")


class DatasetStatisticsModel(Base):
    __tablename__ = "dataset_statistics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    total_images: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_videos: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_annotations: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_updated: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    dataset: Mapped["DatasetModel"] = relationship("DatasetModel", back_populates="statistics")


class DatasetImageModel(Base):
    __tablename__ = "dataset_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[Optional[int]] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)
    brand_id: Mapped[Optional[int]] = mapped_column(ForeignKey("brands.id", ondelete="SET NULL"), nullable=True, index=True)
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("product_categories.id", ondelete="SET NULL"), nullable=True, index=True)
    supplier_id: Mapped[Optional[int]] = mapped_column(ForeignKey("product_suppliers.supplier_id", ondelete="SET NULL"), nullable=True, index=True)
    store_id: Mapped[Optional[int]] = mapped_column(ForeignKey("stores.id", ondelete="SET NULL"), nullable=True, index=True)
    shelf_id: Mapped[Optional[int]] = mapped_column(ForeignKey("shelves.id", ondelete="SET NULL"), nullable=True, index=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    width: Mapped[int] = mapped_column(Integer, nullable=False)
    height: Mapped[int] = mapped_column(Integer, nullable=False)
    aspect_ratio: Mapped[str] = mapped_column(String(50), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    capture_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    gps_coordinates: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    camera_info: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    color_space: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    hash: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    annotation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    dataset: Mapped["DatasetModel"] = relationship("DatasetModel", back_populates="images")


class DatasetVideoModel(Base):
    __tablename__ = "dataset_videos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id: Mapped[Optional[int]] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)
    brand_id: Mapped[Optional[int]] = mapped_column(ForeignKey("brands.id", ondelete="SET NULL"), nullable=True, index=True)
    category_id: Mapped[Optional[int]] = mapped_column(ForeignKey("product_categories.id", ondelete="SET NULL"), nullable=True, index=True)
    supplier_id: Mapped[Optional[int]] = mapped_column(ForeignKey("product_suppliers.supplier_id", ondelete="SET NULL"), nullable=True, index=True)
    store_id: Mapped[Optional[int]] = mapped_column(ForeignKey("stores.id", ondelete="SET NULL"), nullable=True, index=True)
    shelf_id: Mapped[Optional[int]] = mapped_column(ForeignKey("shelves.id", ondelete="SET NULL"), nullable=True, index=True)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    resolution: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    fps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    frame_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    dataset: Mapped["DatasetModel"] = relationship("DatasetModel", back_populates="videos")


class DatasetMetadataModel(Base):
    __tablename__ = "dataset_metadata"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_type: Mapped[str] = mapped_column(String(16), nullable=False)
    asset_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    key: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    dataset: Mapped["DatasetModel"] = relationship("DatasetModel", back_populates="metadata_entries")
