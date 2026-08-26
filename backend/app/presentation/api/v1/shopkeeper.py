import os
from datetime import datetime, date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.core.database import get_db
from app.core.logging import logger
from app.data.models.store_model import StoreModel, user_store_assignments
from app.data.models.inventory_model import InventoryModel
from app.data.models.video_model import VideoModel
from app.data.models.ai_scan_model import AIScanModel
from app.data.models.report_model import ReportModel
from app.data.models.notification_model import NotificationModel
from app.domain.entities.user import User
from app.presentation.api.v1.auth import get_current_user

router = APIRouter(prefix="/shopkeeper", tags=["shopkeeper-portal"])


@router.get("/dashboard")
def get_shopkeeper_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve all relevant operational data for the logged-in Shopkeeper:
    - Assigned Store Branch details
    - Today's Scan summaries
    - Inventory Stock list
    - Real-time Expiry, Low Stock, and Out-of-Stock alerts
    - Scan History and Excel Reports list
    - Notifications feed
    """
    if current_user.role not in ["Shopkeeper", "Admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: Logged in profile lacks Shopkeeper parameters."
        )

    # 1. Resolve assigned store
    # Query user_store_assignments
    store_assoc = db.query(user_store_assignments).filter(
        user_store_assignments.c.user_id == current_user.id
    ).first()

    store_id = None
    if store_assoc:
        store_id = store_assoc.store_id
    else:
        # Fallback: link to first store in database to ensure it works
        store = db.query(StoreModel).first()
        if not store:
            store = StoreModel(name="Aetheria Main Outlet", location="Metropolis Center")
            db.add(store)
            db.commit()
            db.refresh(store)
            
        # Link user to this store
        db.execute(
            user_store_assignments.insert().values(
                user_id=current_user.id,
                store_id=store.id
            )
        )
        db.commit()
        store_id = store.id
        logger.info(f"Shopkeeper: Linked user {current_user.id} to store {store.id} automatically.")

    store = db.query(StoreModel).filter(StoreModel.id == store_id).first()

    # 2. Fetch Today's Scans
    today_start = datetime.combine(date.today(), datetime.min.time())
    today_scans = db.query(AIScanModel).filter(
        and_(
            AIScanModel.store_id == store_id,
            AIScanModel.created_at >= today_start
        )
    ).all()

    # 3. Current Inventory list
    inventory_items = db.query(InventoryModel).filter(
        InventoryModel.store_id == store_id
    ).all()

    # 4. Generate Alerts on the fly
    alerts = []
    # Check low stock / out of stock
    for item in inventory_items:
        if item.quantity == 0:
            alerts.append({
                "type": "Out of Stock",
                "severity": "High",
                "message": f"Product '{item.name}' ({item.sku}) is completely sold out on shelf '{item.location_bin or 'Main Aisle'}'."
            })
        elif item.quantity <= 5:
            alerts.append({
                "type": "Low Stock",
                "severity": "Medium",
                "message": f"Product '{item.name}' ({item.sku}) is running low ({item.quantity} units remaining) on shelf '{item.location_bin or 'Main Aisle'}'."
            })
        
        # Check expiry
        if item.expiry_date:
            days_left = (item.expiry_date - date.today()).days
            if days_left <= 0:
                alerts.append({
                    "type": "Expired",
                    "severity": "High",
                    "message": f"Product '{item.name}' ({item.sku}) expired on {item.expiry_date}."
                })
            elif days_left <= 30:
                alerts.append({
                    "type": "Near Expiry",
                    "severity": "Medium",
                    "message": f"Product '{item.name}' ({item.sku}) expires soon in {days_left} days ({item.expiry_date})."
                })

    # 5. Scan History list
    scans_history = db.query(AIScanModel).filter(
        AIScanModel.store_id == store_id
    ).order_by(AIScanModel.created_at.desc()).limit(15).all()

    # 6. Reports list
    reports = db.query(ReportModel).filter(
        ReportModel.store_id == store_id
    ).order_by(ReportModel.created_at.desc()).limit(10).all()

    # 7. Notifications list
    notifications = db.query(NotificationModel).filter(
        and_(
            NotificationModel.user_id == current_user.id,
            NotificationModel.is_read == False
        )
    ).order_by(NotificationModel.created_at.desc()).all()

    # Auto-seed mock notification if none exist
    if not notifications:
        mock_notif = NotificationModel(
            user_id=current_user.id,
            store_id=store_id,
            title="System Active",
            message="Welcome to Aetheria Shopkeeper Console. Upload shelf footage in the video station to sync stock levels.",
            type="Info",
            is_read=False
        )
        db.add(mock_notif)
        db.commit()
        notifications = [mock_notif]

    return {
        "store": {
            "id": store.id,
            "name": store.name,
            "location": store.location
        },
        "today_scans": {
            "count": len(today_scans),
            "success_count": sum(1 for s in today_scans if s.status == "Success" or s.status == "Completed"),
            "failed_count": sum(1 for s in today_scans if s.status == "Failed")
        },
        "inventory": [
            {
                "id": item.id,
                "name": item.name,
                "sku": item.sku,
                "quantity": item.quantity,
                "location_bin": item.location_bin or "Main Aisle",
                "status": item.status,
                "expiry_date": str(item.expiry_date) if item.expiry_date else None,
                "updated_at": item.updated_at.isoformat()
            }
            for item in inventory_items
        ],
        "alerts": alerts,
        "scans_history": [
            {
                "id": s.id,
                "status": s.status,
                "created_at": s.created_at.isoformat(),
                "detections_count": len(s.detections)
            }
            for s in scans_history
        ],
        "reports": [
            {
                "id": r.id,
                "type": r.type,
                "file_url": r.file_url,
                "created_at": r.created_at.isoformat()
            }
            for r in reports
        ],
        "notifications": [
            {
                "id": n.id,
                "title": n.title,
                "message": n.message,
                "type": n.type,
                "created_at": n.created_at.isoformat()
            }
            for n in notifications
        ]
    }


@router.post("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark a notification as read."""
    notif = db.query(NotificationModel).filter(
        and_(
            NotificationModel.id == notification_id,
            NotificationModel.user_id == current_user.id
        )
    ).first()
    
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found.")
        
    notif.is_read = True
    db.commit()
    return {"status": "success"}


from app.data.models.order_model import OrderModel
from app.data.models.supplier_model import SupplierModel
from app.data.models.user_model import UserModel
from app.services.notification_service import NotificationService
from pydantic import BaseModel
from decimal import Decimal

class OrderRequest(BaseModel):
    store_id: int
    supplier_id: int
    amount: float

@router.post("/orders")
def place_replenishment_order(
    payload: OrderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Place a replenishment order request to a supplier, sending automated
    Push, Email, and SMS notifications to the supplier (Vendor).
    """
    if current_user.role not in ["Shopkeeper", "Admin"]:
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    # Check if supplier exists
    supplier = db.query(SupplierModel).filter(SupplierModel.id == payload.supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found.")

    order = OrderModel(
        store_id=payload.store_id,
        supplier_id=payload.supplier_id,
        created_by_id=current_user.id,
        status="Pending",
        total_amount=Decimal(str(payload.amount))
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    # Resolve Vendor user to notify
    vendor_user = db.query(UserModel).filter(UserModel.email == supplier.contact_email).first()
    
    # Notify Vendor (Supplier Updates)
    if vendor_user:
        NotificationService.dispatch(
            db=db,
            user_id=vendor_user.id,
            title="New Supply Order Requested",
            message=f"Supply order #ORD-{order.id} has been submitted by shopkeeper. Amount: ${payload.amount:.2f}.",
            notif_type="Supplier Updates",
            store_id=payload.store_id
        )

    # Notify assigned shopkeepers
    NotificationService.notify_store_users(
        db=db,
        store_id=payload.store_id,
        title="Replenishment Request Dispatched",
        message=f"Order #ORD-{order.id} has been sent to {supplier.name} for replenishment.",
        notif_type="Supplier Updates"
    )

    return {"status": "success", "order_id": order.id}
