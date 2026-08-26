from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class QualityMetrics(BaseModel):
    blur_score: float
    brightness_score: float
    contrast_score: float
    noise_score: float
    resolution_score: float
    overall_score: float
    remarks: Optional[str] = None


class PipelineConfigurationBase(BaseModel):
    name: str = Field(..., min_length=1)
    resize_width: int = 1024
    resize_height: int = 1024
    compression_level: int = 85
    quality_threshold: int = 60
    max_image_size_mb: int = 8
    frame_interval: int = 30
    target_video_width: int = 1280
    target_video_height: int = 720
    target_video_fps: int = 30
    accepted_image_formats: List[str] = ["jpg", "jpeg", "png", "webp", "bmp", "tiff"]
    accepted_video_formats: List[str] = ["mp4", "avi", "mov", "mkv", "webm"]
    enable_background_cleanup: bool = False
    max_video_duration_seconds: int = 900


class PipelineConfigurationCreate(PipelineConfigurationBase):
    pass


class PipelineConfigurationUpdate(BaseModel):
    name: Optional[str] = None
    resize_width: Optional[int] = None
    resize_height: Optional[int] = None
    compression_level: Optional[int] = None
    quality_threshold: Optional[int] = None
    max_image_size_mb: Optional[int] = None
    frame_interval: Optional[int] = None
    target_video_width: Optional[int] = None
    target_video_height: Optional[int] = None
    target_video_fps: Optional[int] = None
    accepted_image_formats: Optional[List[str]] = None
    accepted_video_formats: Optional[List[str]] = None
    enable_background_cleanup: Optional[bool] = None
    max_video_duration_seconds: Optional[int] = None


class PipelineConfigurationOut(PipelineConfigurationBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PreprocessingJobStartPayload(BaseModel):
    dataset_id: int
    job_name: Optional[str] = "Dataset Preprocessing"
    asset_type: Optional[str] = "all"
    config_id: Optional[int] = None
    settings: Optional[Dict[str, Any]] = None


class PreprocessingJobOut(BaseModel):
    id: int
    dataset_id: int
    job_name: str
    asset_type: str
    status: str
    requested_by_id: int
    config_id: Optional[int]
    settings: Optional[Dict[str, Any]]
    total_assets: int
    processed_assets: int
    failed_assets: int
    warnings_count: int
    errors_count: int
    progress: float
    is_cancelled: bool
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class PreprocessingLogOut(BaseModel):
    id: int
    job_id: int
    dataset_id: int
    asset_type: str
    asset_id: Optional[int]
    asset_url: str
    status: str
    message: Optional[str]
    quality_metrics: Optional[Dict[str, Any]]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ImageQualityOut(BaseModel):
    id: int
    job_id: int
    dataset_id: int
    image_id: int
    blur_score: float
    brightness_score: float
    contrast_score: float
    noise_score: float
    resolution_score: float
    overall_score: float
    is_valid: bool
    remarks: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VideoProcessingOut(BaseModel):
    id: int
    job_id: int
    dataset_id: int
    video_id: int
    thumbnail_url: Optional[str]
    compressed_file_url: Optional[str]
    duration_seconds: Optional[float]
    original_resolution: Optional[str]
    converted_resolution: Optional[str]
    original_fps: Optional[float]
    converted_fps: Optional[float]
    frame_count: Optional[int]
    scene_count: int
    duplicate_frames_removed: int
    file_size: int
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
