from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.domain.entities.user import User
from app.presentation.api.v1.auth import get_current_user
from app.data.models.shelf_mapping_model import (
    StoreMapModel,
    AisleMapModel,
    RackLocationModel,
    ShelfMapModel,
    PlanogramModel,
    ProductLocationModel,
    LocationHistoryModel,
    MisplacedProductModel,
    EmptyShelfModel,
    OccupancyStatisticsModel
)
from app.data.models.product_model import ProductModel
from app.services.location_service import LocationIntelligenceService
from app.presentation.schemas.location_schemas import (
    MapShelfPayload,
    LocateProductPayload,
    ProductLocationOut,
    StoreMapOut,
    ShelfMapOut,
    PlanogramOut,
    MisplacedProductOut,
    EmptyShelfOut,
    OccupancyStatsOut
)

router = APIRouter(prefix="/location", tags=["shelf-mapping-location-intelligence"])
service = LocationIntelligenceService()


@router.post("/map-shelf", response_model=ShelfMapOut, status_code=status.HTTP_201_CREATED)
def map_new_shelf(
    payload: MapShelfPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Registers a shelf level inside a rack."""
    rack = db.query(RackLocationModel).filter(RackLocationModel.id == payload.rack_location_id).first()
    if not rack:
        raise HTTPException(status_code=404, detail="Rack location not found.")
    
    shelf = ShelfMapModel(
        rack_location_id=payload.rack_location_id,
        shelf_level=payload.shelf_level,
        height_meters=payload.height_meters,
        width_meters=payload.width_meters,
        max_capacity=payload.max_capacity
    )
    db.add(shelf)
    db.commit()
    db.refresh(shelf)
    return shelf


@router.post("/locate-product", response_model=ProductLocationOut, status_code=status.HTTP_201_CREATED)
def locate_and_map_product(
    payload: LocateProductPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Determines exact coordinate positions of a recognized product, checking deviations."""
    try:
        placement = service.assign_product_location(
            db=db,
            shelf_map_id=payload.shelf_map_id,
            product_id=payload.product_id,
            x_relative=payload.x_relative,
            y_relative=payload.y_relative,
            facing_count=payload.facing_count,
            slot_number=payload.slot_number
        )
        return placement
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/store-map", response_model=StoreMapOut)
def get_store_map(
    store_id: int = 1,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generates digital store floor map coordinate models for interactive graphics overlays."""
    # Seeding layout on-the-fly to prevent empty states
    store_map = service.get_or_create_store_map(db, store_id)
    return store_map


@router.get("/planogram", response_model=List[PlanogramOut])
def list_planogram_templates(
    shelf_map_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve compliance facecounts templates matching planograms rules."""
    query = db.query(PlanogramModel)
    if shelf_map_id:
        query = query.filter(PlanogramModel.shelf_map_id == shelf_map_id)
    plans = query.all()
    
    output = []
    for p in plans:
        p_name = p.product.name if p.product else "Unknown Product"
        output.append(PlanogramOut(
            id=p.id,
            shelf_map_id=p.shelf_map_id,
            product_id=p.product_id,
            product_name=p_name,
            expected_position=p.expected_position,
            expected_facing_count=p.expected_facing_count
        ))
    return output


@router.get("/misplaced", response_model=List[MisplacedProductOut])
def get_misplaced_products(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve coordinates logs detailing misplaced products and severity alerts."""
    logs = db.query(MisplacedProductModel).order_by(MisplacedProductModel.created_at.desc()).all()
    
    output = []
    for l in logs:
        p_name = l.product.name if l.product else "Unknown Product"
        p_sku = l.product.sku if l.product else "N/A"
        det_name = f"Rack {l.detected_shelf.rack_location.rack_number} / {l.detected_shelf.shelf_level}" if l.detected_shelf else "Unknown Shelf"
        exp_name = f"Rack {l.expected_shelf.rack_location.rack_number} / {l.expected_shelf.shelf_level}" if l.expected_shelf else "Aisle Floor"
        
        output.append(MisplacedProductOut(
            id=l.id,
            product_id=l.product_id,
            product_name=p_name,
            sku=p_sku,
            detected_shelf_map_id=l.detected_shelf_map_id,
            detected_shelf_name=det_name,
            expected_shelf_map_id=l.expected_shelf_map_id,
            expected_shelf_name=exp_name,
            detected_position=l.detected_position,
            expected_position=l.expected_position,
            severity=l.severity,
            created_at=l.created_at
        ))
    return output


@router.get("/empty-space", response_model=List[EmptyShelfOut])
def get_empty_shelf_spots(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve details on vacant gaps and space allocations."""
    spots = db.query(EmptyShelfModel).all()
    return spots


@router.get("/occupancy", response_model=List[OccupancyStatsOut])
def get_occupancy_telemetry(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve high-precision shelf/rack utilization ratios."""
    stats = db.query(OccupancyStatisticsModel).all()
    output = []
    for s in stats:
        shelf_name = f"{s.shelf_map.rack_location.aisle_map.aisle_name} / Rack {s.shelf_map.rack_location.rack_number} - {s.shelf_map.shelf_level}"
        output.append(OccupancyStatsOut(
            id=s.id,
            shelf_map_id=s.shelf_map_id,
            shelf_name=shelf_name,
            occupancy_percentage=s.occupancy_percentage,
            unassigned_space_percentage=s.unassigned_space_percentage,
            created_at=s.created_at
        ))
    return output


@router.get("/history")
def get_location_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve history ledger auditing item movements and relocations."""
    logs = db.query(LocationHistoryModel).order_by(LocationHistoryModel.moved_at.desc()).all()
    output = []
    for l in logs:
        p_name = l.product.name if l.product else "Unknown Product"
        p_sku = l.product.sku if l.product else "N/A"
        new_name = f"Rack {l.new_shelf_map.rack_location.rack_number} / {l.new_shelf_map.shelf_level}" if l.new_shelf_map else "Unknown Shelf"
        
        output.append({
            "id": l.id,
            "product_name": p_name,
            "sku": p_sku,
            "previous_shelf_name": "Initial Scan" if not l.previous_shelf_map_id else f"Shelf ID: {l.previous_shelf_map_id}",
            "new_shelf_name": new_name,
            "moved_at": l.moved_at
        })
    return output
