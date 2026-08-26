import os
from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.logging import logger
from app.presentation.schemas.model_registry_schemas import (
    ModelCreate,
    ModelUpdate,
    ModelOut,
    VersionCreate,
    VersionOut,
    ArtifactUploadRequest,
    ArtifactOut,
    MetricCreate,
    MetricOut,
    ReviewRequest,
    ReviewOut,
    DeploymentRequest,
    DeploymentOut,
    DeploymentHistoryOut,
    ModelRegistrySummaryOut,
)
from app.presentation.api.v1.auth import get_current_user
from app.domain.entities.user import User
from app.services.model_registry_service import ModelRegistryService
from app.data.repositories.sqlalchemy_model_registry_repository import SQLAlchemyModelRegistryRepository

router = APIRouter(prefix="/model-registry", tags=["model-registry"])


@router.post("", response_model=ModelOut, status_code=status.HTTP_201_CREATED)
def register_model(
    payload: ModelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ModelRegistryService(db)
    return service.register_model(payload.model_dump(), current_user.id)


@router.get("", response_model=List[ModelOut])
def list_models(
    name: Optional[str] = Query(None),
    model_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    owner_id: Optional[int] = Query(None),
    offset: int = Query(0),
    limit: int = Query(50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ModelRegistryService(db)
    return service.list_models({
        "name": name,
        "model_type": model_type,
        "status": status,
        "owner_id": owner_id,
    }, offset, limit)


@router.get("/{model_id}", response_model=ModelOut)
def get_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ModelRegistryService(db)
    model = service.get_model(model_id)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found.")
    return model


@router.put("/{model_id}", response_model=ModelOut)
def update_model(
    model_id: int,
    payload: ModelUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ModelRegistryService(db)
    model = service.get_model(model_id)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found.")
    updated = service.repo.update_model(model_id, payload.model_dump(exclude_none=True))
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found.")
    return updated


@router.post("/{model_id}/archive")
def archive_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = SQLAlchemyModelRegistryRepository(db)
    model = repo.get_model(model_id)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found.")
    model.is_archived = True
    db.commit()
    return {"success": True, "message": "Model archived."}


@router.post("/{model_id}/restore")
def restore_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ModelRegistryService(db)
    model = service.restore_model(model_id)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found.")
    return model


@router.delete("/{model_id}")
def delete_model(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ModelRegistryService(db)
    success = service.soft_delete_model(model_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found or already deleted.")
    return {"success": True, "message": "Model soft deleted."}


@router.post("/{model_id}/versions", response_model=VersionOut, status_code=status.HTTP_201_CREATED)
def create_version(
    model_id: int,
    payload: VersionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ModelRegistryService(db)
    model = service.get_model(model_id)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found.")
    return service.create_version(model_id, payload.model_dump(), current_user.id)


@router.get("/{model_id}/versions", response_model=List[VersionOut])
def list_versions(
    model_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ModelRegistryService(db)
    return service.list_versions(model_id)


@router.post("/versions/{version_id}/artifacts", response_model=ArtifactOut)
def upload_artifact(
    version_id: int,
    artifact_type: str = Query(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ModelRegistryService(db)
    version = service.get_version(version_id)
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found.")
    file_bytes = file.file.read()
    filename = f"models/{version_id}/{file.filename}"
    artifact = service.upload_model_artifact(version_id, file_bytes, filename, artifact_type, {}, is_primary=True)
    return artifact


@router.post("/versions/{version_id}/metrics", response_model=MetricOut, status_code=status.HTTP_201_CREATED)
def add_metric(
    payload: MetricCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ModelRegistryService(db)
    return service.add_metric(payload.model_dump())


@router.post("/versions/{version_id}/approve", response_model=ReviewOut)
def approve_version(
    version_id: int,
    payload: ReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ModelRegistryService(db)
    review = service.approve_version(version_id, current_user.id, payload.comment)
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found.")
    return review


@router.post("/versions/{version_id}/reject", response_model=ReviewOut)
def reject_version(
    version_id: int,
    payload: ReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ModelRegistryService(db)
    review = service.reject_version(version_id, current_user.id, payload.comment)
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found.")
    return review


@router.post("/{model_id}/deploy", response_model=DeploymentOut)
def deploy_model(
    model_id: int,
    payload: DeploymentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ModelRegistryService(db)
    model = service.get_model(model_id)
    if not model:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Model not found.")
    version = service.get_version(payload.version_id)
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found.")
    if version.status != "approved":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only approved versions can be deployed.")
    return service.deploy_version(model_id, payload.model_dump(), current_user.id)


@router.post("/deployments/{deployment_id}/rollback", response_model=DeploymentOut)
def rollback_deployment(
    deployment_id: int,
    payload: DeploymentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ModelRegistryService(db)
    deployment = service.rollback_deployment(deployment_id, current_user.id, payload.version_id, payload.notes)
    if not deployment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Deployment not found.")
    return deployment


@router.get("/deployments/history", response_model=List[DeploymentHistoryOut])
def deployment_history(
    model_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = SQLAlchemyModelRegistryRepository(db)
    return repo.get_deployment_history(model_id)


@router.get("/summary", response_model=ModelRegistrySummaryOut)
def model_registry_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ModelRegistryService(db)
    return service.get_dashboard_summary()
