from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.core.database import get_db
from app.core.exceptions import EntityNotFoundException, EntityAlreadyExistsException
from app.data.models.store_model import StoreModel, user_store_assignments
from app.data.models.user_model import UserModel
from app.data.models.inventory_model import InventoryModel
from app.data.models.video_model import VideoModel
from app.data.models.order_model import OrderModel
from app.data.models.ai_scan_model import AIScanModel
from app.data.models.audit_log_model import AuditLogModel
from app.domain.entities.user import User
from app.presentation.api.v1.auth import get_current_user
from app.presentation.schemas.store_schemas import (
    StoreCreate, 
    StoreUpdate, 
    StoreOut, 
    StoreUserOut, 
    UserAssignment
)

router = APIRouter(prefix="/stores", tags=["store-management"])


@router.get("", response_model=List[StoreOut])
def list_stores(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all store branches with aggregated metrics, pre-seeding defaults if empty."""
    stores = db.query(StoreModel).all()
    if not stores:
        seeds = [
            StoreModel(
                name="Aetheria Main Outlet", 
                location="Metropolis Center", 
                address="100 Main St, Metropolis", 
                contact="+1-555-0199", 
                timezone="UTC", 
                is_active=True, 
                settings="{}"
            ),
            StoreModel(
                name="Northside Branch", 
                location="Upper District", 
                address="500 North Ave, Metropolis", 
                contact="+1-555-0288", 
                timezone="EST", 
                is_active=True, 
                settings="{}"
            )
        ]
        for s in seeds:
            db.add(s)
        db.commit()
        stores = db.query(StoreModel).all()

    results = []

    for s in stores:
        # Calculate total inventory units
        total_stock = db.query(func.sum(InventoryModel.quantity)).filter(
            InventoryModel.store_id == s.id
        ).scalar() or 0

        # Count Shopkeepers
        employee_count = db.query(func.count(UserModel.id)).join(
            user_store_assignments, UserModel.id == user_store_assignments.c.user_id
        ).filter(
            and_(
                user_store_assignments.c.store_id == s.id,
                UserModel.role == "Shopkeeper"
            )
        ).scalar() or 0

        # Count Vendors
        vendor_count = db.query(func.count(UserModel.id)).join(
            user_store_assignments, UserModel.id == user_store_assignments.c.user_id
        ).filter(
            and_(
                user_store_assignments.c.store_id == s.id,
                UserModel.role == "Vendor"
            )
        ).scalar() or 0

        results.append(
            StoreOut(
                id=s.id,
                name=s.name,
                location=s.location,
                address=s.address,
                contact=s.contact,
                timezone=s.timezone,
                is_active=s.is_active,
                settings=s.settings,
                total_stock=total_stock,
                employee_count=employee_count,
                vendor_count=vendor_count,
                created_at=s.created_at,
                updated_at=s.updated_at
            )
        )
    return results


@router.get("/users/available", response_model=List[StoreUserOut])
def get_available_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve list of employees/vendors that can be linked to branches."""
    users = db.query(UserModel).filter(
        UserModel.role.in_(["Shopkeeper", "Vendor"])
    ).all()
    return users


@router.get("/{store_id}")
def get_store_details(
    store_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve detailed dashboard and lists for a specific branch."""
    store = db.query(StoreModel).filter(StoreModel.id == store_id).first()
    if not store:
        raise EntityNotFoundException("Store Branch", str(store_id))

    # Fetch assigned employees (Shopkeepers)
    employees = db.query(UserModel).join(
        user_store_assignments, UserModel.id == user_store_assignments.c.user_id
    ).filter(
        and_(
            user_store_assignments.c.store_id == store_id,
            UserModel.role == "Shopkeeper"
        )
    ).all()

    # Fetch assigned vendors (Vendors)
    vendors = db.query(UserModel).join(
        user_store_assignments, UserModel.id == user_store_assignments.c.user_id
    ).filter(
        and_(
            user_store_assignments.c.store_id == store_id,
            UserModel.role == "Vendor"
        )
    ).all()

    # Metrics
    total_stock_skus = db.query(func.count(InventoryModel.id)).filter(
        InventoryModel.store_id == store_id
    ).scalar() or 0

    total_stock_units = db.query(func.sum(InventoryModel.quantity)).filter(
        InventoryModel.store_id == store_id
    ).scalar() or 0

    total_videos = db.query(func.count(VideoModel.id)).filter(
        VideoModel.store_id == store_id
    ).scalar() or 0

    total_orders = db.query(func.count(OrderModel.id)).filter(
        OrderModel.store_id == store_id
    ).scalar() or 0

    total_scans = db.query(func.count(AIScanModel.id)).filter(
        AIScanModel.store_id == store_id
    ).scalar() or 0

    # Fetch detailed inventory items for this branch
    inventory_items = db.query(InventoryModel).filter(
        InventoryModel.store_id == store_id
    ).all()

    # Fetch scan history list
    scans_history = db.query(AIScanModel).filter(
        AIScanModel.store_id == store_id
    ).order_by(AIScanModel.created_at.desc()).all()

    # Fetch audit logs for this store branch
    audit_logs = db.query(AuditLogModel).filter(
        AuditLogModel.action.like("INVENTORY_RECONCILE%")
    ).order_by(AuditLogModel.created_at.desc()).limit(100).all()
    
    branch_audit_logs = []
    for log in audit_logs:
        if log.payload.get("store_id") == store_id:
            branch_audit_logs.append({
                "id": log.id,
                "action": log.action,
                "created_at": log.created_at.isoformat(),
                "payload": log.payload
            })

    return {
        "id": store.id,
        "name": store.name,
        "location": store.location,
        "created_at": store.created_at,
        "employees": [StoreUserOut.model_validate(e) for e in employees],
        "vendors": [StoreUserOut.model_validate(v) for v in vendors],
        "inventory": [
            {
                "id": item.id,
                "product_id": item.product_id,
                "name": item.name,
                "sku": item.sku,
                "quantity": item.quantity,
                "expiry_date": str(item.expiry_date) if item.expiry_date else None,
                "location_bin": item.location_bin or "Main Aisle",
                "confidence": item.confidence,
                "status": item.status,
                "updated_at": item.updated_at.isoformat()
            }
            for item in inventory_items
        ],
        "scans_history": [
            {
                "id": s.id,
                "video_id": s.video_id,
                "image_url": s.image_url,
                "status": s.status,
                "created_at": s.created_at.isoformat(),
                "detections_count": len(s.detections)
            }
            for s in scans_history
        ],
        "audit_logs": branch_audit_logs,
        "analytics": {
            "total_stock_skus": total_stock_skus,
            "total_stock_units": total_stock_units,
            "total_videos": total_videos,
            "total_orders": total_orders,
            "total_scans": total_scans
        }
    }


@router.post("", response_model=StoreOut, status_code=status.HTTP_201_CREATED)
def create_store(
    payload: StoreCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new store branch/location."""
    store = StoreModel(
        name=payload.name,
        location=payload.location,
        address=payload.address,
        contact=payload.contact,
        timezone=payload.timezone,
        is_active=payload.is_active,
        settings=payload.settings
    )
    db.add(store)
    db.commit()
    db.refresh(store)
    return StoreOut(
        id=store.id,
        name=store.name,
        location=store.location,
        address=store.address,
        contact=store.contact,
        timezone=store.timezone,
        is_active=store.is_active,
        settings=store.settings,
        created_at=store.created_at,
        updated_at=store.updated_at
    )


@router.put("/{store_id}", response_model=StoreOut)
def update_store(
    store_id: int,
    payload: StoreUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Updates parameter details for a branch."""
    store = db.query(StoreModel).filter(StoreModel.id == store_id).first()
    if not store:
        raise EntityNotFoundException("Store Branch", str(store_id))

    update_data = payload.model_dump(exclude_unset=True)
    for key, val in update_data.items():
        setattr(store, key, val)

    db.commit()
    db.refresh(store)

    return StoreOut(
        id=store.id,
        name=store.name,
        location=store.location,
        address=store.address,
        contact=store.contact,
        timezone=store.timezone,
        is_active=store.is_active,
        settings=store.settings,
        created_at=store.created_at,
        updated_at=store.updated_at
    )


@router.delete("/{store_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_store(
    store_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deletes a branch from the system."""
    store = db.query(StoreModel).filter(StoreModel.id == store_id).first()
    if not store:
        raise EntityNotFoundException("Store Branch", str(store_id))

    db.delete(store)
    db.commit()
    return


@router.post("/{store_id}/assign")
def assign_user(
    store_id: int,
    payload: UserAssignment,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Links an employee or vendor to a branch."""
    store = db.query(StoreModel).filter(StoreModel.id == store_id).first()
    if not store:
        raise EntityNotFoundException("Store Branch", str(store_id))

    user = db.query(UserModel).filter(UserModel.id == payload.user_id).first()
    if not user:
        raise EntityNotFoundException("User", str(payload.user_id))

    # Check if assignment already exists
    exist = db.execute(
        user_store_assignments.select().where(
            and_(
                user_store_assignments.c.user_id == payload.user_id,
                user_store_assignments.c.store_id == store_id
            )
        )
    ).first()

    if not exist:
        db.execute(
            user_store_assignments.insert().values(
                user_id=payload.user_id,
                store_id=store_id
            )
        )
        db.commit()

    return {"message": f"User {user.full_name} assigned to branch {store.name} successfully."}


@router.post("/{store_id}/unassign")
def unassign_user(
    store_id: int,
    payload: UserAssignment,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Removes an employee/vendor link from a branch."""
    store = db.query(StoreModel).filter(StoreModel.id == store_id).first()
    if not store:
        raise EntityNotFoundException("Store Branch", str(store_id))

    db.execute(
        user_store_assignments.delete().where(
            and_(
                user_store_assignments.c.user_id == payload.user_id,
                user_store_assignments.c.store_id == store_id
            )
        )
    ).commit()

    return {"message": "User unassigned from branch successfully."}
