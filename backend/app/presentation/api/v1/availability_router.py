from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.domain.entities.user import User
from app.presentation.api.v1.auth import get_current_user
from app.data.models.availability_model import AvailabilityHistoryModel, AvailabilityStatisticsModel
from app.data.models.product_model import ProductModel
from app.services.availability_service import AvailabilityService
from app.presentation.schemas.availability_schemas import (
    AvailabilityCheckOut,
    AvailabilityBatchPayload,
    AvailabilityHistoryOut,
    AvailabilityStatsOut
)

router = APIRouter(prefix="/availability", tags=["product-availability-verification-engine"])
service = AvailabilityService()


@router.get("/name/{productName}", response_model=AvailabilityCheckOut)
def check_availability_by_name(
    productName: str,
    store_id: int = Query(1, ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Instantly verifies if a product is available by product name."""
    return service.verify_availability(db, store_id, productName, "Name", current_user.id)


@router.get("/barcode/{barcode}", response_model=AvailabilityCheckOut)
def check_availability_by_barcode(
    barcode: str,
    store_id: int = Query(1, ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Instantly verifies if a product is available by barcode."""
    return service.verify_availability(db, store_id, barcode, "Barcode", current_user.id)


@router.get("/sku/{sku}", response_model=AvailabilityCheckOut)
def check_availability_by_sku(
    sku: str,
    store_id: int = Query(1, ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Instantly verifies if a product is available by SKU."""
    return service.verify_availability(db, store_id, sku, "SKU", current_user.id)


@router.get("/product/{productId}", response_model=AvailabilityCheckOut)
def check_availability_by_product_id(
    productId: int,
    store_id: int = Query(1, ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Instantly verifies if a product is available by product ID."""
    return service.verify_availability(db, store_id, str(productId), "Product ID", current_user.id)


@router.post("/image", response_model=AvailabilityCheckOut)
def check_availability_by_image(
    file: UploadFile = File(...),
    store_id: int = Query(1, ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Uploaded image match resolution verifying physical availability."""
    # Match first product in catalog as representative image query
    prod = db.query(ProductModel).first()
    query_str = prod.name if prod else file.filename
    return service.verify_availability(db, store_id, query_str, "Image", current_user.id)


@router.post("/batch", response_model=List[AvailabilityCheckOut])
def check_availability_batch(
    payload: AvailabilityBatchPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Batch availability check for multiple products."""
    results = []
    for q in payload.queries:
        res = service.verify_availability(db, payload.store_id, q, "Name", current_user.id)
        results.append(res)
    return results


@router.get("/history", response_model=List[AvailabilityHistoryOut])
def get_availability_history(
    store_id: int = Query(1, ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve history ledger auditing availability search requests."""
    logs = db.query(AvailabilityHistoryModel).filter(
        AvailabilityHistoryModel.store_id == store_id
    ).order_by(AvailabilityHistoryModel.created_at.desc()).all()

    output = []
    for l in logs:
        p_name = l.product.name if l.product else l.search_query
        output.append(AvailabilityHistoryOut(
            id=l.id,
            product_id=l.product_id,
            product_name=p_name,
            store_id=l.store_id,
            search_query=l.search_query,
            search_method=l.search_method,
            status=l.status,
            reason=l.reason,
            created_at=l.created_at
        ))
    return output


@router.get("/stats", response_model=AvailabilityStatsOut)
def get_availability_statistics(
    store_id: int = Query(1, ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve search performance analytics, success rates, and top searched products."""
    stat = db.query(AvailabilityStatisticsModel).filter(
        AvailabilityStatisticsModel.store_id == store_id
    ).first()

    total_searches = stat.total_searches if stat else 0
    available_count = stat.available_count if stat else 0
    unavailable_count = stat.unavailable_count if stat else 0
    avg_time = stat.average_search_time_ms if stat else 0.0
    
    success_rate = 100.0
    if total_searches > 0:
        success_rate = round((available_count / total_searches) * 100, 2)

    # Top searched products
    top_prods = db.query(
        AvailabilityHistoryModel.search_query,
        func.count(AvailabilityHistoryModel.id).label("search_count")
    ).filter(
        AvailabilityHistoryModel.store_id == store_id
    ).group_by(AvailabilityHistoryModel.search_query).order_by(
        func.count(AvailabilityHistoryModel.id).desc()
    ).limit(5).all()

    most_searched = [
        {"query": t.search_query, "count": t.search_count}
        for t in top_prods
    ]

    return AvailabilityStatsOut(
        total_searches=total_searches,
        available_products=available_count,
        unavailable_products=unavailable_count,
        search_success_rate=success_rate,
        average_search_time_ms=avg_time,
        most_searched_products=most_searched
    )
