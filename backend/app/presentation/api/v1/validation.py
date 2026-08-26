from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.role_checker import RoleChecker
from app.presentation.api.v1.auth import get_current_user
from app.domain.entities.user import User
from app.data.repositories.sqlalchemy_validation_repository import SQLAlchemyValidationRepository
from app.presentation.schemas.validation_schemas import (
    ValidationJobCreate,
    ValidationJobOut,
    ValidationErrorOut,
    DatasetQualityReportOut,
    DatasetApprovalCreate,
    DatasetApprovalOut,
    ValidationAnalyticsOut,
)
from app.services.validation_service import run_validation_job_async
from app.data.repositories.sqlalchemy_dataset_repository import SQLAlchemyDatasetRepository

router = APIRouter(prefix="/validation", tags=["validation"])


@router.post("/start", response_model=ValidationJobOut, status_code=status.HTTP_201_CREATED)
def start_validation_job(
    payload: ValidationJobCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker(allowed_roles=["Admin", "Vendor"]))
):
    dataset_repo = SQLAlchemyDatasetRepository(db)
    dataset = dataset_repo.get_dataset(payload.dataset_id)
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found.")

    repo = SQLAlchemyValidationRepository(db)
    job = repo.create_validation_job(payload.model_dump(), current_user.id)
    background_tasks.add_task(run_validation_job_async, job.id)
    return job


@router.post("/{job_id}/cancel")
def cancel_validation_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker(allowed_roles=["Admin", "Vendor"]))
):
    repo = SQLAlchemyValidationRepository(db)
    success = repo.cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found or cannot be cancelled.")
    return {"success": True, "message": "Validation job cancellation requested."}


@router.post("/{job_id}/rerun", response_model=ValidationJobOut)
def rerun_validation_job(
    job_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker(allowed_roles=["Admin", "Vendor"]))
):
    repo = SQLAlchemyValidationRepository(db)
    existing_job = repo.get_job(job_id)
    if not existing_job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    new_job = repo.create_validation_job({
        "dataset_id": existing_job.dataset_id,
        "validation_type": existing_job.validation_type,
        "version_tag": existing_job.version_tag,
        "status": "pending_validation",
    }, current_user.id)

    background_tasks.add_task(run_validation_job_async, new_job.id)
    return new_job


@router.get("/jobs", response_model=List[ValidationJobOut])
def list_validation_jobs(
    status: Optional[str] = Query(None),
    dataset_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker(allowed_roles=["Admin", "Vendor"]))
):
    repo = SQLAlchemyValidationRepository(db)
    return repo.list_jobs(dataset_id=dataset_id, status=status)


@router.get("/jobs/{job_id}", response_model=ValidationJobOut)
def get_validation_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker(allowed_roles=["Admin", "Vendor"]))
):
    repo = SQLAlchemyValidationRepository(db)
    job = repo.get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")
    return job


@router.get("/jobs/{job_id}/report", response_model=DatasetQualityReportOut)
def get_validation_report(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker(allowed_roles=["Admin", "Vendor"]))
):
    repo = SQLAlchemyValidationRepository(db)
    job = repo.get_job(job_id)
    if not job or not job.report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Validation report not found.")
    return job.report


@router.get("/jobs/{job_id}/errors", response_model=List[ValidationErrorOut])
def list_validation_errors(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker(allowed_roles=["Admin", "Vendor"]))
):
    repo = SQLAlchemyValidationRepository(db)
    return repo.list_errors(job_id=job_id)


@router.post("/jobs/{job_id}/approve", response_model=DatasetApprovalOut)
def approve_validation_job(
    job_id: int,
    payload: DatasetApprovalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker(allowed_roles=["Admin"]))
):
    repo = SQLAlchemyValidationRepository(db)
    job = repo.get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    if job.status not in ["pending_review", "validation_failed", "draft"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job cannot be approved in its current state.")

    job.status = "approved"
    job.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(job)

    approval = repo.add_dataset_approval({
        "job_id": job.id,
        "dataset_id": job.dataset_id,
        "approved_by_id": current_user.id,
        "status": "approved",
        "comment": payload.comment,
    })
    repo.add_review_history({
        "job_id": job.id,
        "dataset_id": job.dataset_id,
        "reviewer_id": current_user.id,
        "action": "approved",
        "comment": payload.comment,
    })
    return approval


@router.post("/jobs/{job_id}/reject", response_model=DatasetApprovalOut)
def reject_validation_job(
    job_id: int,
    payload: DatasetApprovalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker(allowed_roles=["Admin"]))
):
    repo = SQLAlchemyValidationRepository(db)
    job = repo.get_job(job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found.")

    job.status = "rejected"
    job.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(job)

    approval = repo.add_dataset_approval({
        "job_id": job.id,
        "dataset_id": job.dataset_id,
        "approved_by_id": current_user.id,
        "status": "rejected",
        "comment": payload.comment,
    })
    repo.add_review_history({
        "job_id": job.id,
        "dataset_id": job.dataset_id,
        "reviewer_id": current_user.id,
        "action": "rejected",
        "comment": payload.comment,
    })
    return approval


@router.get("/analytics", response_model=ValidationAnalyticsOut)
def validation_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(RoleChecker(allowed_roles=["Admin", "Vendor"]))
):
    repo = SQLAlchemyValidationRepository(db)
    return repo.get_analytics_summary()
