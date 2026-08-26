from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, Integer, DateTime, Boolean, ForeignKey, Text, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class PreprocessingJobModel(Base):
    __tablename__ = "preprocessing_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    job_name: Mapped[str] = mapped_column(String(255), nullable=False)
    asset_type: Mapped[str] = mapped_column(String(50), nullable=False, default="all")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending", index=True)
    requested_by_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
    config_id: Mapped[Optional[int]] = mapped_column(ForeignKey("pipeline_configuration.id", ondelete="SET NULL"), nullable=True, index=True)
    settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    total_assets: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processed_assets: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_assets: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    warnings_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    errors_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    progress: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    is_cancelled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    logs: Mapped[List["PreprocessingLogModel"]]
    image_quality: Mapped[List["ImageQualityModel"]]
    video_processing: Mapped[List["VideoProcessingModel"]]
    configuration: Mapped[Optional["PipelineConfigurationModel"]]

    logs = relationship(
        "PreprocessingLogModel",
        back_populates="job",
        cascade="all, delete-orphan"
    )
    image_quality = relationship(
        "ImageQualityModel",
        back_populates="job",
        cascade="all, delete-orphan"
    )
    video_processing = relationship(
        "VideoProcessingModel",
        back_populates="job",
        cascade="all, delete-orphan"
    )
    configuration = relationship("PipelineConfigurationModel", back_populates="jobs")


class PreprocessingLogModel(Base):
    __tablename__ = "preprocessing_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("preprocessing_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_type: Mapped[str] = mapped_column(String(16), nullable=False)
    asset_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    asset_url: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    quality_metrics: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    job: Mapped["PreprocessingJobModel"] = relationship("PreprocessingJobModel", back_populates="logs")


class ImageQualityModel(Base):
    __tablename__ = "image_quality"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("preprocessing_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    image_id: Mapped[int] = mapped_column(ForeignKey("dataset_images.id", ondelete="CASCADE"), nullable=False, index=True)
    blur_score: Mapped[float] = mapped_column(Float, nullable=False)
    brightness_score: Mapped[float] = mapped_column(Float, nullable=False)
    contrast_score: Mapped[float] = mapped_column(Float, nullable=False)
    noise_score: Mapped[float] = mapped_column(Float, nullable=False)
    resolution_score: Mapped[float] = mapped_column(Float, nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    is_valid: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    job: Mapped["PreprocessingJobModel"] = relationship("PreprocessingJobModel", back_populates="image_quality")


class VideoProcessingModel(Base):
    __tablename__ = "video_processing"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("preprocessing_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_id: Mapped[int] = mapped_column(ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("dataset_videos.id", ondelete="CASCADE"), nullable=False, index=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    compressed_file_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    original_resolution: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    converted_resolution: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    original_fps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    converted_fps: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    frame_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    scene_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duplicate_frames_removed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="completed")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    job: Mapped["PreprocessingJobModel"] = relationship("PreprocessingJobModel", back_populates="video_processing")


class PipelineConfigurationModel(Base):
    __tablename__ = "pipeline_configuration"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    resize_width: Mapped[int] = mapped_column(Integer, default=1024, nullable=False)
    resize_height: Mapped[int] = mapped_column(Integer, default=1024, nullable=False)
    compression_level: Mapped[int] = mapped_column(Integer, default=85, nullable=False)
    quality_threshold: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    max_image_size_mb: Mapped[int] = mapped_column(Integer, default=8, nullable=False)
    frame_interval: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    target_video_width: Mapped[int] = mapped_column(Integer, default=1280, nullable=False)
    target_video_height: Mapped[int] = mapped_column(Integer, default=720, nullable=False)
    target_video_fps: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    accepted_image_formats: Mapped[List[str]] = mapped_column(JSON, default=["jpg", "jpeg", "png", "webp", "bmp", "tiff"], nullable=False)
    accepted_video_formats: Mapped[List[str]] = mapped_column(JSON, default=["mp4", "avi", "mov", "mkv", "webm"], nullable=False)
    enable_background_cleanup: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    max_video_duration_seconds: Mapped[int] = mapped_column(Integer, default=900, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    jobs: Mapped[List["PreprocessingJobModel"]] = relationship("PreprocessingJobModel", back_populates="configuration")
