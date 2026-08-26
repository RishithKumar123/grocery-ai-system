import os
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.logging import logger
from app.data.repositories.sqlalchemy_preprocessing_repository import SQLAlchemyPreprocessingRepository
from app.data.repositories.sqlalchemy_dataset_repository import SQLAlchemyDatasetRepository
from app.presentation.schemas.preprocessing_schemas import (
    PipelineConfigurationCreate,
    PipelineConfigurationUpdate,
    PipelineConfigurationOut,
    PreprocessingJobStartPayload,
    PreprocessingJobOut,
    PreprocessingLogOut,
    ImageQualityOut,
    VideoProcessingOut,
)
from app.presentation.api.v1.auth import get_current_user
from app.domain.entities.user import User
from app.services.preprocessing_service import run_preprocessing_job_async

router = APIRouter(prefix="/preprocessing", tags=["preprocessing"])


@router.post("/config", response_model=PipelineConfigurationOut, status_code=status.HTTP_201_CREATED)
def create_pipeline_configuration(
    payload: PipelineConfigurationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = SQLAlchemyPreprocessingRepository(db)
    config = repo.create_pipeline_configuration(payload.model_dump())
    return config


@router.get("/config", response_model=List[PipelineConfigurationOut])
def list_pipeline_configurations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = SQLAlchemyPreprocessingRepository(db)
    return repo.list_pipeline_configurations()


@router.put("/config/{config_id}", response_model=PipelineConfigurationOut)
def update_pipeline_configuration(
    config_id: int,
    payload: PipelineConfigurationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = SQLAlchemyPreprocessingRepository(db)
    config = repo.update_pipeline_configuration(config_id, payload.model_dump(exclude_none=True))
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline configuration not found.")
    return config


@router.post("/start", response_model=PreprocessingJobOut, status_code=status.HTTP_201_CREATED)
def start_preprocessing(
    payload: PreprocessingJobStartPayload,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    dataset_repo = SQLAlchemyDatasetRepository(db)
    dataset = dataset_repo.get_dataset(payload.dataset_id)
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found.")

    repo = SQLAlchemyPreprocessingRepository(db)
    job = repo.create_job({
        "dataset_id": payload.dataset_id,
        "job_name": payload.job_name,
        "asset_type": payload.asset_type or "all",
        "requested_by_id": current_user.id,
        "config_id": payload.config_id,
        "settings": payload.settings or {},
    })

    background_tasks.add_task(run_preprocessing_job_async, job.id)
    return job


@router.post("/{job_id}/cancel")
def cancel_preprocessing_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = SQLAlchemyPreprocessingRepository(db)
    success = repo.cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found or cannot be cancelled.")
    return {"success": True, "message": "Cancellation requested."}


@router.post("/{job_id}/restart", response_model=PreprocessingJobOut)
def restart_preprocessing_job(
    job_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = SQLAlchemyPreprocessingRepository(db)
    job = repo.restart_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
    background_tasks.add_task(run_preprocessing_job_async, job.id)
    return job


@router.get("/jobs", response_model=List[PreprocessingJobOut])
def list_preprocessing_jobs(
    status: Optional[str] = Query(None),
    dataset_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = SQLAlchemyPreprocessingRepository(db)
    return repo.list_jobs(status=status, dataset_id=dataset_id)


@router.get("/jobs/{job_id}", response_model=PreprocessingJobOut)
def get_preprocessing_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = SQLAlchemyPreprocessingRepository(db)
    job = repo.get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
    return job


@router.get("/jobs/{job_id}/logs", response_model=List[PreprocessingLogOut])
def get_preprocessing_logs(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = SQLAlchemyPreprocessingRepository(db)
    return repo.get_job_logs(job_id)


@router.get("/jobs/{job_id}/failed", response_model=List[PreprocessingLogOut])
def get_failed_preprocessing_assets(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = SQLAlchemyPreprocessingRepository(db)
    return repo.get_failed_assets(job_id)


@router.get("/jobs/{job_id}/quality", response_model=List[ImageQualityOut])
def get_preprocessing_quality_report(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = SQLAlchemyPreprocessingRepository(db)
    return repo.get_quality_report(job_id)


@router.get("/jobs/{job_id}/videos", response_model=List[VideoProcessingOut])
def get_preprocessing_video_report(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = SQLAlchemyPreprocessingRepository(db)
    return repo.get_video_reports(job_id)


@router.get("/dashboard/metrics")
def preprocessing_dashboard_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    repo = SQLAlchemyPreprocessingRepository(db)
    jobs = repo.list_jobs()
    total = len(jobs)
    completed = sum(1 for job in jobs if job.status == "completed")
    running = sum(1 for job in jobs if job.status == "running")
    failed = sum(1 for job in jobs if job.status == "failed")
    pending = sum(1 for job in jobs if job.status == "pending")
    return {
        "total_jobs": total,
        "completed_jobs": completed,
        "running_jobs": running,
        "failed_jobs": failed,
        "pending_jobs": pending,
    }
