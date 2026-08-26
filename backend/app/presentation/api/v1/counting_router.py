from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.domain.entities.user import User
from app.presentation.api.v1.auth import get_current_user
from app.data.models.counting_model import (
    CountingJobModel,
    CountingResultModel,
    TrackedObjectModel,
    CountStatisticsModel,
    CountValidationModel,
    CountHistoryModel
)
from app.data.models.product_model import ProductModel
from app.services.counting_service import CountingEngineService
from app.presentation.schemas.counting_schemas import (
    CountingImagePayload,
    CountingJobPayload,
    CountingJobOut,
    CountHistoryOut,
    CountHistoryVerifyPayload
)

router = APIRouter(prefix="/counting", tags=["enterprise-inventory-counting"])
service = CountingEngineService()


@router.post("/image", status_code=status.HTTP_201_CREATED)
def count_products_on_image(
    payload: CountingImagePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Filter, deduplicate, and count recognized products from a static image frame."""
    detections_list = []
    for d in payload.detections:
        detections_list.append({
            "yolo_label": d.yolo_label,
            "ocr_text": d.ocr_text,
            "barcode": d.barcode,
            "confidence": d.confidence,
            "bounding_box": {
                "xmin": d.bounding_box.xmin,
                "ymin": d.bounding_box.ymin,
                "xmax": d.bounding_box.xmax,
                "ymax": d.bounding_box.ymax
            }
        })

    result = service.count_static_images(
        db=db,
        store_id=payload.store_id,
        shelf_id=payload.shelf_id,
        detections=detections_list
    )
    return result


@router.post("/jobs", response_model=CountingJobOut, status_code=status.HTTP_201_CREATED)
def start_counting_job(
    payload: CountingJobPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Start tracking inventory counts on camera streams, mobile devices, or video feeds."""
    job = service.simulate_video_tracking_job(
        db=db,
        store_id=payload.store_id,
        video_id=payload.video_id,
        user_id=current_user.id,
        config=payload.config
    )
    return job


@router.post("/jobs/{job_id}/stop", response_model=CountingJobOut)
def stop_counting_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Terminate an active inventory counting stream tracker."""
    job = db.query(CountingJobModel).filter(CountingJobModel.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Counting job not found.")
    
    job.status = "Stopped"
    db.commit()
    db.refresh(job)
    return job


@router.get("/jobs", response_model=List[CountingJobOut])
def list_counting_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve tracking logs and analytics list for all inventory counting streams."""
    jobs = db.query(CountingJobModel).order_by(CountingJobModel.created_at.desc()).all()
    return jobs


@router.get("/jobs/{job_id}", response_model=CountingJobOut)
def get_counting_job_details(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fetch analytics dashboard parameters, tracked paths, heatmaps and validations for a job."""
    job = db.query(CountingJobModel).filter(CountingJobModel.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Counting job not found.")
    return job


@router.get("/history", response_model=List[CountHistoryOut])
def get_count_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve audit history ledger logs of completed tracking counts."""
    history = db.query(CountHistoryModel).order_by(CountHistoryModel.verified_at.desc()).all()
    
    output = []
    for h in history:
        p_name = h.product.name if h.product else "Unknown Product"
        s_aisle = h.shelf.aisle if h.shelf else "Unknown Aisle"
        s_level = h.shelf.shelf_level if h.shelf else "Unknown Level"
        
        output.append(CountHistoryOut(
            id=h.id,
            product_id=h.product_id,
            product_name=p_name,
            shelf_id=h.shelf_id,
            shelf_aisle=s_aisle,
            shelf_level=s_level,
            count=h.count,
            verified_at=h.verified_at,
            job_id=h.job_id
        ))
    return output


@router.post("/jobs/{job_id}/verify")
def verify_and_approve_counts(
    job_id: int,
    payload: Optional[CountHistoryVerifyPayload] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Approve tracking calculations logs and append verification flags before syncing catalog."""
    job = db.query(CountingJobModel).filter(CountingJobModel.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Counting job not found.")

    # Save to history for all counts in this job
    for result in job.results:
        if result.product_id:
            # Check if history entry already exists to avoid duplicates
            existing = db.query(CountHistoryModel).filter(
                CountHistoryModel.job_id == job.id,
                CountHistoryModel.product_id == result.product_id
            ).first()

            if not existing:
                history = CountHistoryModel(
                    product_id=result.product_id,
                    count=result.verified_count,
                    job_id=job.id
                )
                db.add(history)

    job.status = "Completed"
    db.commit()
    return {"message": "Detections count ledger approved and verified."}
