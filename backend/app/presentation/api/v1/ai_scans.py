from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.data.models.ai_scan_model import AIScanModel, AIScanDetectionModel
from app.data.models.product_model import ProductModel
from app.domain.entities.user import User
from app.presentation.api.v1.auth import get_current_user
from app.presentation.schemas.scan_schemas import ScanOut, DetectionOut

router = APIRouter(prefix="/scans", tags=["ai-scans"])


@router.get("", response_model=List[ScanOut])
def list_scans(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all AI Shelf Scans and item detections details."""
    scans = db.query(AIScanModel).order_by(AIScanModel.created_at.desc()).all()
    results = []

    for s in scans:
        detections_out = []
        for det in s.detections:
            product_name = None
            if det.product_id:
                prod = db.query(ProductModel).filter(ProductModel.id == det.product_id).first()
                product_name = prod.name if prod else None

            detections_out.append(
                DetectionOut(
                    id=det.id,
                    scan_id=det.scan_id,
                    product_id=det.product_id,
                    product_name=product_name or det.raw_ocr_text or "Unknown Product",
                    confidence=det.confidence,
                    bounding_box=det.bounding_box,
                    raw_ocr_text=det.raw_ocr_text,
                    created_at=det.created_at
                )
            )

        results.append(
            ScanOut(
                id=s.id,
                video_id=s.video_id,
                store_id=s.store_id,
                image_url=s.image_url,
                status=s.status,
                created_at=s.created_at,
                detections=detections_out,
                scan_start_time=s.scan_start_time,
                scan_end_time=s.scan_end_time,
                scan_duration=s.scan_duration,
                frames_processed=s.frames_processed,
                fps=s.fps,
                progress_percentage=s.progress_percentage,
                progress_stage=s.progress_stage
            )
        )

    return results


@router.get("/performance/metrics")
def get_scans_performance_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve aggregate performance timings for dashboard stats."""
    from datetime import date, datetime
    scans = db.query(AIScanModel).filter(AIScanModel.status == "Completed").all()
    
    if not scans:
        return {
            "today_avg_scan_time": 0.0,
            "fastest_scan": 0.0,
            "slowest_scan": 0.0,
            "last_scan_time": None,
            "avg_products_per_scan": 0.0
        }

    durations = [s.scan_duration for s in scans if s.scan_duration is not None and s.scan_duration > 0]
    today_start = datetime.combine(date.today(), datetime.min.time())
    today_scans = [s for s in scans if s.created_at >= today_start and s.scan_duration is not None]
    
    today_avg = sum(s.scan_duration for s in today_scans) / len(today_scans) if today_scans else 0.0
    fastest = min(durations) if durations else 0.0
    slowest = max(durations) if durations else 0.0
    last_scan = max(s.created_at for s in scans) if scans else None
    
    total_detections = sum(len(s.detections) for s in scans)
    avg_products = total_detections / len(scans) if scans else 0.0

    return {
        "today_avg_scan_time": round(today_avg, 2),
        "fastest_scan": round(fastest, 2),
        "slowest_scan": round(slowest, 2),
        "last_scan_time": last_scan.isoformat() if last_scan else None,
        "avg_products_per_scan": round(avg_products, 2)
    }


@router.get("/{scan_id}", response_model=ScanOut)
def get_scan_by_id(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve details for a single AI Scan by ID."""
    s = db.query(AIScanModel).filter(AIScanModel.id == scan_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Scan not found.")

    detections_out = []
    for det in s.detections:
        product_name = None
        if det.product_id:
            prod = db.query(ProductModel).filter(ProductModel.id == det.product_id).first()
            product_name = prod.name if prod else None

        detections_out.append(
            DetectionOut(
                id=det.id,
                scan_id=det.scan_id,
                product_id=det.product_id,
                product_name=product_name or det.raw_ocr_text or "Unknown Product",
                confidence=det.confidence,
                bounding_box=det.bounding_box,
                raw_ocr_text=det.raw_ocr_text,
                created_at=det.created_at
            )
        )

    return ScanOut(
        id=s.id,
        video_id=s.video_id,
        store_id=s.store_id,
        image_url=s.image_url,
        status=s.status,
        created_at=s.created_at,
        detections=detections_out,
        scan_start_time=s.scan_start_time,
        scan_end_time=s.scan_end_time,
        scan_duration=s.scan_duration,
        frames_processed=s.frames_processed,
        fps=s.fps,
        progress_percentage=s.progress_percentage,
        progress_stage=s.progress_stage
    )
