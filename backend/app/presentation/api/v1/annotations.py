from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.logging import logger
from app.data.repositories.sqlalchemy_annotation_repository import SQLAlchemyAnnotationRepository
from app.domain.entities.user import User
from app.presentation.api.v1.auth import get_current_user
from app.presentation.schemas.annotation_schemas import (
    AnnotationCreate,
    AnnotationUpdate,
    AnnotationOut,
    AnnotationReviewCreate,
    AnnotationReviewOut,
    AnnotationCommentCreate,
    AnnotationCommentOut,
    AnnotationTaskCreate,
    AnnotationTaskOut,
    AnnotationSearchFilters,
    AnnotationStatisticsOut,
    AnnotationExportRequest,
    AnnotationExportOut,
)

router = APIRouter(prefix="/annotations", tags=["annotations"])


@router.post("", response_model=AnnotationOut, status_code=status.HTTP_201_CREATED)
def create_annotation(
    payload: AnnotationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = SQLAlchemyAnnotationRepository(db)
    annotation = repo.create_annotation(payload.model_dump(), current_user.id)
    return annotation


@router.get("/{annotation_id}", response_model=AnnotationOut)
def get_annotation(
    annotation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = SQLAlchemyAnnotationRepository(db)
    annotation = repo.get_annotation(annotation_id)
    if not annotation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Annotation not found.")
    return annotation


@router.put("/{annotation_id}", response_model=AnnotationOut)
def update_annotation(
    annotation_id: int,
    payload: AnnotationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = SQLAlchemyAnnotationRepository(db)
    annotation = repo.update_annotation(annotation_id, payload.model_dump(exclude_none=True), current_user.id)
    if not annotation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Annotation not found.")
    return annotation


@router.delete("/{annotation_id}")
def delete_annotation(
    annotation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = SQLAlchemyAnnotationRepository(db)
    if not repo.delete_annotation(annotation_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Annotation not found.")
    return {"success": True, "message": "Annotation deleted."}


@router.post("/{annotation_id}/review", response_model=AnnotationReviewOut)
def review_annotation(
    annotation_id: int,
    payload: AnnotationReviewCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = SQLAlchemyAnnotationRepository(db)
    review = repo.create_annotation_review(annotation_id, payload.model_dump(), current_user.id)
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Annotation not found.")
    return review


@router.get("", response_model=List[AnnotationOut])
def search_annotations(
    dataset_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    reviewer_id: Optional[int] = Query(None),
    assigned_to_id: Optional[int] = Query(None),
    query: Optional[str] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = SQLAlchemyAnnotationRepository(db)
    filters = {
        "dataset_id": dataset_id,
        "status": status,
        "reviewer_id": reviewer_id,
        "assigned_to_id": assigned_to_id,
        "query": query,
    }
    return repo.search_annotations(filters, offset, limit)


@router.get("/statistics", response_model=AnnotationStatisticsOut)
def annotation_statistics(
    dataset_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = SQLAlchemyAnnotationRepository(db)
    return repo.get_annotation_statistics(dataset_id)


@router.post("/export", response_model=AnnotationExportOut)
def export_annotations(
    payload: AnnotationExportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    repo = SQLAlchemyAnnotationRepository(db)
    export_path = repo.export_annotations(payload.dataset_id, payload.export_format, payload.version_tag)
    return {"export_url": export_path, "export_format": payload.export_format, "created_at": datetime.utcnow()}
