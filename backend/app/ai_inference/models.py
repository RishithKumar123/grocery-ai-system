from datetime import datetime
from typing import Optional
from sqlalchemy import Integer, String, DateTime, Boolean, Float, Text, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class InferenceJobModel(Base):
    __tablename__ = "inference_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)  # image/video/live
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True)
    created_by_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    results = relationship("InferenceResultModel", back_populates="job", cascade="all, delete-orphan")


class InferenceResultModel(Base):
    __tablename__ = "inference_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("inference_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    source: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)  # file path or stream id
    model_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    model_version: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    result_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    job = relationship("InferenceJobModel", back_populates="results")
    detections = relationship("DetectionModel", back_populates="result", cascade="all, delete-orphan")


class DetectionModel(Base):
    __tablename__ = "detections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    result_id: Mapped[int] = mapped_column(ForeignKey("inference_results.id", ondelete="CASCADE"), nullable=False, index=True)
    class_id: Mapped[int] = mapped_column(Integer, nullable=False)
    class_name: Mapped[str] = mapped_column(String(255), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    bbox: Mapped[dict] = mapped_column(JSON, nullable=False)  # {x1,y1,x2,y2}
    detection_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    result = relationship("InferenceResultModel", back_populates="detections")


class ProcessedImageModel(Base):
    __tablename__ = "processed_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    result_id: Mapped[int] = mapped_column(ForeignKey("inference_results.id", ondelete="CASCADE"), nullable=False, index=True)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    thumbnail_path: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    size_bytes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ProcessedVideoModel(Base):
    __tablename__ = "processed_videos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    result_id: Mapped[int] = mapped_column(ForeignKey("inference_results.id", ondelete="CASCADE"), nullable=False, index=True)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    frame_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class RuntimeStatisticModel(Base):
    __tablename__ = "runtime_statistics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    model_version: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    gpu_util: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    cpu_util: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    mem_usage_mb: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    inference_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
