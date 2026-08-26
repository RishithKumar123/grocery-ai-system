from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.exceptions import EntityNotFoundException
from app.data.models.layout_model import ShelfModel
from app.data.models.store_model import StoreModel
from app.domain.entities.user import User
from app.presentation.api.v1.auth import get_current_user
from app.presentation.schemas.layout_schemas import ShelfCreate, ShelfUpdate, ShelfOut

router = APIRouter(prefix="/layout", tags=["physical-store-layout"])


@router.get("", response_model=List[ShelfOut])
def list_shelves(
    store_id: Optional[int] = None,
    aisle_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve physical shelves grid map, pre-seeding defaults for the store network if empty."""
    query = db.query(ShelfModel)
    if store_id:
        query = query.filter(ShelfModel.store_id == store_id)
    if aisle_filter:
        query = query.filter(ShelfModel.aisle.like(f"%{aisle_filter}%"))
        
    shelves = query.all()
    
    if not shelves and store_id:
        # Pre-seed physical layout structure for the store
        store_exists = db.query(StoreModel).filter(StoreModel.id == store_id).first()
        if store_exists:
            seeds = [
                ShelfModel(store_id=store_id, aisle="Aisle A", shelf_level="Level 1", section="Sec 1", bin_rack="Rack 1", capacity=50, status="active"),
                ShelfModel(store_id=store_id, aisle="Aisle A", shelf_level="Level 2", section="Sec 1", bin_rack="Rack 1", capacity=50, status="active"),
                ShelfModel(store_id=store_id, aisle="Aisle B", shelf_level="Level 1", section="Sec 2", bin_rack="Rack 2", capacity=75, status="active"),
                ShelfModel(store_id=store_id, aisle="Aisle C (Cold)", shelf_level="Level 1", section="Sec 3", bin_rack="Cooler 1", capacity=30, status="active")
            ]
            for s in seeds:
                db.add(s)
            db.commit()
            shelves = db.query(ShelfModel).filter(ShelfModel.store_id == store_id).all()
            
    return shelves


@router.get("/{shelf_id}", response_model=ShelfOut)
def get_shelf(
    shelf_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve detailed physical layout data for a specific shelf."""
    shelf = db.query(ShelfModel).filter(ShelfModel.id == shelf_id).first()
    if not shelf:
        raise EntityNotFoundException("Store Shelf", str(shelf_id))
    return shelf


@router.post("", response_model=ShelfOut, status_code=status.HTTP_201_CREATED)
def create_shelf(
    payload: ShelfCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Register a new physical shelf coordinates mapping."""
    store_exists = db.query(StoreModel).filter(StoreModel.id == payload.store_id).first()
    if not store_exists:
        raise EntityNotFoundException("Store Branch", str(payload.store_id))

    shelf = ShelfModel(
        store_id=payload.store_id,
        aisle=payload.aisle,
        shelf_level=payload.shelf_level,
        section=payload.section,
        bin_rack=payload.bin_rack,
        capacity=payload.capacity,
        status=payload.status
    )
    db.add(shelf)
    db.commit()
    db.refresh(shelf)
    return shelf


@router.put("/{shelf_id}", response_model=ShelfOut)
def update_shelf(
    shelf_id: int,
    payload: ShelfUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update layout configurations for a physical shelf."""
    shelf = db.query(ShelfModel).filter(ShelfModel.id == shelf_id).first()
    if not shelf:
        raise EntityNotFoundException("Store Shelf", str(shelf_id))

    update_data = payload.model_dump(exclude_unset=True)
    for key, val in update_data.items():
        setattr(shelf, key, val)

    db.commit()
    db.refresh(shelf)
    return shelf


@router.delete("/{shelf_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_shelf(
    shelf_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deletes a physical shelf definition mapping."""
    shelf = db.query(ShelfModel).filter(ShelfModel.id == shelf_id).first()
    if not shelf:
        raise EntityNotFoundException("Store Shelf", str(shelf_id))

    db.delete(shelf)
    db.commit()
    return
