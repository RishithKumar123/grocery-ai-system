from datetime import datetime
from typing import Optional
from sqlalchemy import Integer, String, DateTime, Float, JSON, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class BarcodeTypeModel(Base):
    __tablename__ = "barcode_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)


class BarcodeScanModel(Base):
    __tablename__ = "barcode_scans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)  # file path or stream id
    scanned_by_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    processed: Mapped[bool] = mapped_column(Boolean, default=False)

    results = relationship("BarcodeResultModel", back_populates="scan", cascade="all, delete-orphan")


class BarcodeResultModel(Base):
    __tablename__ = "barcode_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    scan_id: Mapped[int] = mapped_column(ForeignKey("barcode_scans.id", ondelete="CASCADE"), nullable=False, index=True)
    value: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    barcode_type_id: Mapped[Optional[int]] = mapped_column(ForeignKey("barcode_types.id"), nullable=True, index=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bbox: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    rotation: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    validated: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    scan = relationship("BarcodeScanModel", back_populates="results")
    barcode_type = relationship("BarcodeTypeModel")


class UnknownBarcodeModel(Base):
    __tablename__ = "unknown_barcodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    value: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    source_scan_id: Mapped[Optional[int]] = mapped_column(ForeignKey("barcode_scans.id", ondelete="SET NULL"), nullable=True)
    metadata_blob: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)
    queued_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    reviewed: Mapped[bool] = mapped_column(Boolean, default=False)
    approved: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)


class BarcodeQualityModel(Base):
    __tablename__ = "barcode_quality"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    result_id: Mapped[int] = mapped_column(ForeignKey("barcode_results.id", ondelete="CASCADE"), nullable=False, index=True)
    readability_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    quality_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
