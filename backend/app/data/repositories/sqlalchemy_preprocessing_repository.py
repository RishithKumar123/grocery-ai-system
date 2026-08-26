import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.data.models.preprocessing_model import (
    PreprocessingJobModel,
    PreprocessingLogModel,
    ImageQualityModel,
    VideoProcessingModel,
    PipelineConfigurationModel,
)


class SQLAlchemyPreprocessingRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_pipeline_configuration(self, payload: Dict[str, Any]) -> PipelineConfigurationModel:
        config = PipelineConfigurationModel(
            name=payload.get("name", "default"),
            resize_width=payload.get("resize_width", 1024),
            resize_height=payload.get("resize_height", 1024),
            compression_level=payload.get("compression_level", 85),
            quality_threshold=payload.get("quality_threshold", 60),
            max_image_size_mb=payload.get("max_image_size_mb", 8),
            frame_interval=payload.get("frame_interval", 30),
            target_video_width=payload.get("target_video_width", 1280),
            target_video_height=payload.get("target_video_height", 720),
            target_video_fps=payload.get("target_video_fps", 30),
            accepted_image_formats=payload.get("accepted_image_formats", ["jpg", "jpeg", "png", "webp", "bmp", "tiff"]),
            accepted_video_formats=payload.get("accepted_video_formats", ["mp4", "avi", "mov", "mkv", "webm"]),
            enable_background_cleanup=payload.get("enable_background_cleanup", False),
            max_video_duration_seconds=payload.get("max_video_duration_seconds", 900),
        )
        self.db.add(config)
        self.db.commit()
        self.db.refresh(config)
        return config

    def update_pipeline_configuration(self, config_id: int, payload: Dict[str, Any]) -> Optional[PipelineConfigurationModel]:
        config = self.db.query(PipelineConfigurationModel).filter(PipelineConfigurationModel.id == config_id).first()
        if not config:
            return None

        for field in [
            "name",
            "resize_width",
            "resize_height",
            "compression_level",
            "quality_threshold",
            "max_image_size_mb",
            "frame_interval",
            "target_video_width",
            "target_video_height",
            "target_video_fps",
            "enable_background_cleanup",
            "max_video_duration_seconds",
        ]:
            if field in payload:
                setattr(config, field, payload[field])

        if payload.get("accepted_image_formats") is not None:
            config.accepted_image_formats = payload["accepted_image_formats"]
        if payload.get("accepted_video_formats") is not None:
            config.accepted_video_formats = payload["accepted_video_formats"]

        self.db.commit()
        self.db.refresh(config)
        return config

    def get_pipeline_configuration(self, config_id: int) -> Optional[PipelineConfigurationModel]:
        return self.db.query(PipelineConfigurationModel).filter(PipelineConfigurationModel.id == config_id).first()

    def list_pipeline_configurations(self) -> List[PipelineConfigurationModel]:
        return self.db.query(PipelineConfigurationModel).order_by(PipelineConfigurationModel.updated_at.desc()).all()

    def get_default_configuration(self) -> Optional[PipelineConfigurationModel]:
        return self.db.query(PipelineConfigurationModel).order_by(PipelineConfigurationModel.created_at.asc()).first()

    def create_job(self, payload: Dict[str, Any]) -> PreprocessingJobModel:
        job = PreprocessingJobModel(
            dataset_id=payload["dataset_id"],
            job_name=payload.get("job_name", "Dataset Preprocess"),
            asset_type=payload.get("asset_type", "all"),
            requested_by_id=payload["requested_by_id"],
            config_id=payload.get("config_id"),
            settings=payload.get("settings") or {},
            status="pending",
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def get_job(self, job_id: int) -> Optional[PreprocessingJobModel]:
        return self.db.query(PreprocessingJobModel).filter(PreprocessingJobModel.id == job_id).first()

    def list_jobs(self, status: Optional[str] = None, dataset_id: Optional[int] = None) -> List[PreprocessingJobModel]:
        query = self.db.query(PreprocessingJobModel)
        if status is not None:
            query = query.filter(PreprocessingJobModel.status == status)
        if dataset_id is not None:
            query = query.filter(PreprocessingJobModel.dataset_id == dataset_id)
        return query.order_by(PreprocessingJobModel.created_at.desc()).all()

    def update_job_status(self, job_id: int, status: str, progress: Optional[float] = None, completed_at: Optional[datetime] = None) -> Optional[PreprocessingJobModel]:
        job = self.get_job(job_id)
        if not job:
            return None
        job.status = status
        if progress is not None:
            job.progress = progress
        if completed_at is not None:
            job.completed_at = completed_at
        self.db.commit()
        self.db.refresh(job)
        return job

    def cancel_job(self, job_id: int) -> bool:
        job = self.get_job(job_id)
        if not job or job.status not in ["pending", "running"]:
            return False
        job.is_cancelled = True
        job.status = "cancelling"
        self.db.commit()
        return True

    def restart_job(self, job_id: int) -> Optional[PreprocessingJobModel]:
        job = self.get_job(job_id)
        if not job:
            return None

        job.status = "pending"
        job.progress = 0.0
        job.processed_assets = 0
        job.failed_assets = 0
        job.warnings_count = 0
        job.errors_count = 0
        job.is_cancelled = False
        job.completed_at = None
        self.db.commit()
        self.db.refresh(job)
        return job

    def increment_job_counters(self, job_id: int, processed: int = 0, failed: int = 0, warnings: int = 0, errors: int = 0) -> None:
        job = self.get_job(job_id)
        if not job:
            return
        job.processed_assets += processed
        job.failed_assets += failed
        job.warnings_count += warnings
        job.errors_count += errors
        if job.total_assets > 0:
            job.progress = round((job.processed_assets + job.failed_assets) / job.total_assets * 100, 2)
        self.db.commit()

    def add_preprocessing_log(self, payload: Dict[str, Any]) -> PreprocessingLogModel:
        log = PreprocessingLogModel(
            job_id=payload["job_id"],
            dataset_id=payload["dataset_id"],
            asset_type=payload["asset_type"],
            asset_id=payload.get("asset_id"),
            asset_url=payload["asset_url"],
            status=payload["status"],
            message=payload.get("message"),
            quality_metrics=payload.get("quality_metrics") or {},
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log

    def add_image_quality(self, payload: Dict[str, Any]) -> ImageQualityModel:
        quality = ImageQualityModel(
            job_id=payload["job_id"],
            dataset_id=payload["dataset_id"],
            image_id=payload["image_id"],
            blur_score=payload["blur_score"],
            brightness_score=payload["brightness_score"],
            contrast_score=payload["contrast_score"],
            noise_score=payload["noise_score"],
            resolution_score=payload["resolution_score"],
            overall_score=payload["overall_score"],
            is_valid=payload.get("is_valid", True),
            remarks=payload.get("remarks"),
        )
        self.db.add(quality)
        self.db.commit()
        self.db.refresh(quality)
        return quality

    def add_video_processing(self, payload: Dict[str, Any]) -> VideoProcessingModel:
        video_entry = VideoProcessingModel(
            job_id=payload["job_id"],
            dataset_id=payload["dataset_id"],
            video_id=payload["video_id"],
            thumbnail_url=payload.get("thumbnail_url"),
            compressed_file_url=payload.get("compressed_file_url"),
            duration_seconds=payload.get("duration_seconds"),
            original_resolution=payload.get("original_resolution"),
            converted_resolution=payload.get("converted_resolution"),
            original_fps=payload.get("original_fps"),
            converted_fps=payload.get("converted_fps"),
            frame_count=payload.get("frame_count"),
            scene_count=payload.get("scene_count", 0),
            duplicate_frames_removed=payload.get("duplicate_frames_removed", 0),
            file_size=payload.get("file_size", 0),
            status=payload.get("status", "completed"),
        )
        self.db.add(video_entry)
        self.db.commit()
        self.db.refresh(video_entry)
        return video_entry

    def get_job_logs(self, job_id: int) -> List[PreprocessingLogModel]:
        return self.db.query(PreprocessingLogModel).filter(PreprocessingLogModel.job_id == job_id).order_by(PreprocessingLogModel.created_at.asc()).all()

    def get_failed_assets(self, job_id: int) -> List[PreprocessingLogModel]:
        return self.db.query(PreprocessingLogModel).filter(
            PreprocessingLogModel.job_id == job_id,
            PreprocessingLogModel.status.in_(["failed", "rejected"])
        ).order_by(PreprocessingLogModel.created_at.desc()).all()

    def get_quality_report(self, job_id: int) -> List[ImageQualityModel]:
        return self.db.query(ImageQualityModel).filter(ImageQualityModel.job_id == job_id).order_by(ImageQualityModel.overall_score.desc()).all()

    def get_video_reports(self, job_id: int) -> List[VideoProcessingModel]:
        return self.db.query(VideoProcessingModel).filter(VideoProcessingModel.job_id == job_id).order_by(VideoProcessingModel.created_at.desc()).all()

    def get_job_metrics(self, job_id: int) -> Dict[str, Any]:
        job = self.get_job(job_id)
        if not job:
            return {}
        return {
            "total_assets": job.total_assets,
            "processed_assets": job.processed_assets,
            "failed_assets": job.failed_assets,
            "warnings_count": job.warnings_count,
            "errors_count": job.errors_count,
            "progress": job.progress,
            "status": job.status,
        }
