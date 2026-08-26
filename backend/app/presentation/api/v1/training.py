"""Training management API endpoints."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.logging import logger
from app.ml.training_service import YoloTrainingService, TrainingJobStore
from app.ml.dataset_validator import validate_dataset
from app.ml.class_registry import build_data_yaml_from_catalog
from app.ml.paths import data_yaml_path
from app.presentation.api.v1.auth import get_current_user
from app.domain.entities.user import User

router = APIRouter(prefix="/training", tags=["training-management"])


@router.post("/start")
def start_training(
    epochs: Optional[int] = Query(200, ge=1, le=500),
    imgsz: Optional[int] = Query(640, ge=320, le=1280),
    batch: Optional[int] = Query(None, ge=1, le=64),
    model: Optional[str] = Query("yolo11m.pt"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start a new YOLOv11 training job."""
    config_overrides = {
        "epochs": epochs,
        "imgsz": imgsz,
        "model": model,
    }
    if batch:
        config_overrides["batch"] = batch
    
    service = YoloTrainingService()
    try:
        # Ensure data.yaml is generated from the product catalog before training.
        build_data_yaml_from_catalog(db)
        job = service.start_training(config_overrides)
        return {
            "job_id": job.job_id,
            "status": job.status,
            "config": job.config,
            "message": "Training job started successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to start training: {e}")
        raise HTTPException(status_code=500, detail="Failed to start training job")


@router.post("/resume/{run_dir}")
def resume_training(
    run_dir: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Resume training from a previous run."""
    service = YoloTrainingService()
    try:
        job = service.resume_training(run_dir)
        return {
            "job_id": job.job_id,
            "status": job.status,
            "config": job.config,
            "message": "Training job resumed successfully"
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to resume training: {e}")
        raise HTTPException(status_code=500, detail="Failed to resume training job")


@router.get("/jobs/{job_id}")
def get_job_status(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get status of a training job."""
    job = TrainingJobStore.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Training job not found")
    
    return {
        "job_id": job.job_id,
        "status": job.status,
        "config": job.config,
        "run_dir": job.run_dir,
        "best_weights": job.best_weights,
        "last_weights": job.last_weights,
        "metrics": job.metrics,
        "error": job.error,
        "started_at": job.started_at,
        "finished_at": job.finished_at
    }


@router.get("/jobs")
def list_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all training jobs."""
    jobs = TrainingJobStore.list_jobs()
    return [
        {
            "job_id": job.job_id,
            "status": job.status,
            "config": job.config,
            "run_dir": job.run_dir,
            "started_at": job.started_at,
            "finished_at": job.finished_at
        }
        for job in jobs
    ]


@router.get("/validate")
def validate_dataset_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Validate the current dataset."""
    report = validate_dataset()
    return report.to_dict()


@router.get("/data-yaml")
def get_data_yaml(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get the current data.yaml configuration."""
    yaml_path = data_yaml_path()
    if not yaml_path.is_file():
        raise HTTPException(status_code=404, detail="data.yaml not found. Generate it first.")
    
    import yaml
    with yaml_path.open("r", encoding="utf-8") as f:
        content = yaml.safe_load(f)
    
    return content
