from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, ForeignKey, Float, Integer, Text, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class AvailabilityRequestModel(Base):
    __tablename__ = "availability_requests"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    search_query: Mapped[str] = mapped_column(String(255), nullable=False)
    search_method: Mapped[str] = mapped_column(String(50), nullable=False)  # Name, Barcode, SKU, Product ID, Image
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    store: Mapped["StoreModel"] = relationship("StoreModel")
    user: Mapped[Optional["UserModel"]] = relationship("UserModel")
    results: Mapped[Optional["AvailabilityResultModel"]] = relationship("AvailabilityResultModel", back_populates="request", uselist=False, cascade="all, delete-orphan")


class AvailabilityResultModel(Base):
    __tablename__ = "availability_results"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    availability_request_id: Mapped[int] = mapped_column(ForeignKey("availability_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(10), nullable=False)  # YES or NO
    product_id: Mapped[Optional[int]] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    nearest_store_id: Mapped[Optional[int]] = mapped_column(ForeignKey("stores.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    request: Mapped["AvailabilityRequestModel"] = relationship("AvailabilityRequestModel", back_populates="results")
    product: Mapped[Optional["ProductModel"]] = relationship("ProductModel")
    nearest_store: Mapped[Optional["StoreModel"]] = relationship("StoreModel", foreign_keys=[nearest_store_id])


class AvailabilityHistoryModel(Base):
    __tablename__ = "availability_history"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    product_id: Mapped[Optional[int]] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"), nullable=True, index=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    search_query: Mapped[str] = mapped_column(String(255), nullable=False)
    search_method: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False)  # YES or NO
    reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    product: Mapped[Optional["ProductModel"]] = relationship("ProductModel")
    store: Mapped["StoreModel"] = relationship("StoreModel")


class AvailabilityCacheModel(Base):
    __tablename__ = "availability_cache"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    cache_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    cached_response: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class AvailabilityStatisticsModel(Base):
    __tablename__ = "availability_statistics"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    total_searches: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    available_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unavailable_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    average_search_time_ms: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    # Relationships
    store: Mapped["StoreModel"] = relationship("StoreModel")
