from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domain.entities.user import User
from app.presentation.api.v1.auth import get_current_user
from app.data.models.inventory_model import InventoryModel
from app.data.models.product_model import ProductModel
from app.data.models.inventory_update_model import (
    InventoryUpdateModel,
    InventoryAdjustmentModel,
    InventoryReconciliationModel,
    InventorySnapshotModel,
    UpdateRuleModel,
    ApprovalRequestModel
)
from app.services.inventory_update_service import InventoryUpdateService
from app.presentation.schemas.inventory_update_schemas import (
    ApplyUpdatePayload,
    BatchUpdatePayload,
    UpdateRuleOut,
    UpdateRuleUpdate,
    InventoryUpdateOut,
    InventoryDifferenceOut,
    ApprovalRequestOut,
    RollbackPayload
)

router = APIRouter(prefix="/inventory-update", tags=["automatic-inventory-updates"])
service = InventoryUpdateService()


@router.post("/apply", response_model=InventoryUpdateOut, status_code=status.HTTP_201_CREATED)
def apply_single_inventory_update(
    payload: ApplyUpdatePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Synchronizes verified AI scan counts to revision database, routing variance to queue."""
    try:
        upd = service.apply_update(
            db=db,
            store_id=payload.store_id,
            product_id=payload.product_id,
            new_quantity=payload.new_quantity,
            confidence=payload.confidence,
            notes=payload.notes,
            user_id=current_user.id,
            requested_by=current_user.full_name
        )
        # Fetch names for Pydantic mapping
        p_name = upd.product.name if upd.product else "Unknown Product"
        p_sku = upd.product.sku if upd.product else "N/A"
        
        return InventoryUpdateOut(
            id=upd.id,
            store_id=upd.store_id,
            product_id=upd.product_id,
            product_name=p_name,
            sku=p_sku,
            previous_quantity=upd.previous_quantity,
            new_quantity=upd.new_quantity,
            variance=upd.variance,
            status=upd.status,
            confidence=upd.confidence,
            notes=upd.notes,
            created_at=upd.created_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/batch", response_model=List[InventoryUpdateOut], status_code=status.HTTP_201_CREATED)
def apply_batch_updates(
    payload: BatchUpdatePayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Processes a batch list of product update requests inside a single queue block."""
    results = []
    for item in payload.updates:
        try:
            upd = service.apply_update(
                db=db,
                store_id=item.store_id,
                product_id=item.product_id,
                new_quantity=item.new_quantity,
                confidence=item.confidence,
                notes=item.notes,
                user_id=current_user.id,
                requested_by=current_user.full_name
            )
            p_name = upd.product.name if upd.product else "Unknown Product"
            p_sku = upd.product.sku if upd.product else "N/A"
            results.append(InventoryUpdateOut(
                id=upd.id,
                store_id=upd.store_id,
                product_id=upd.product_id,
                product_name=p_name,
                sku=p_sku,
                previous_quantity=upd.previous_quantity,
                new_quantity=upd.new_quantity,
                variance=upd.variance,
                status=upd.status,
                confidence=upd.confidence,
                notes=upd.notes,
                created_at=upd.created_at
            ))
        except ValueError as e:
            # Continue batch but log error
            continue
    return results


@router.get("/preview", response_model=List[InventoryDifferenceOut])
def preview_inventory_differences(
    store_id: int = 1,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generates preview differences between DB quantities vs recent scanner counting lists."""
    service.seed_default_rules_if_empty(db)
    
    # Query current stock levels
    items = db.query(InventoryModel).filter(InventoryModel.store_id == store_id).all()
    output = []
    
    for item in items:
        # Check if there is an update pending or applied
        latest_upd = db.query(InventoryUpdateModel).filter(
            InventoryUpdateModel.store_id == store_id,
            InventoryUpdateModel.product_id == item.product_id
        ).order_by(InventoryUpdateModel.created_at.desc()).first()

        physical = latest_upd.new_quantity if latest_upd else item.quantity
        diff = physical - item.quantity
        
        var_pct = 0.0
        if item.quantity > 0:
            var_pct = (abs(diff) / item.quantity) * 100

        recom = "Align database quantity to scan value" if diff != 0 else "Quantities match"
        if abs(diff) > 10:
            recom = "Manual auditor validation required (high variance)"

        p_name = item.product.name if item.product else item.name
        p_sku = item.product.sku if item.product else item.sku

        output.append(InventoryDifferenceOut(
            product_id=item.product_id,
            product_name=p_name,
            sku=p_sku,
            database_stock=item.quantity,
            physical_scan=physical,
            difference=diff,
            variance_percentage=round(var_pct, 2),
            recommendation=recom
        ))
    return output


@router.get("/rules", response_model=List[UpdateRuleOut])
def get_validation_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve validation rules thresholds parameters."""
    service.seed_default_rules_if_empty(db)
    rules = db.query(UpdateRuleModel).all()
    return rules


@router.put("/rules/{key}", response_model=UpdateRuleOut)
def update_validation_rule_config(
    key: str,
    payload: UpdateRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Allows administrators to configure thresholds limits parameters."""
    rule = db.query(UpdateRuleModel).filter(UpdateRuleModel.rule_key == key).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Update rule parameter not found.")
    
    rule.value = payload.value
    rule.is_active = payload.is_active
    db.commit()
    db.refresh(rule)
    return rule


@router.get("/approval-queue", response_model=List[ApprovalRequestOut])
def list_pending_approvals(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve details on pending approval queue requests."""
    reqs = db.query(ApprovalRequestModel).order_by(ApprovalRequestModel.id.desc()).all()
    output = []
    
    for r in reqs:
        upd = r.inventory_update
        p_name = upd.product.name if upd.product else "Unknown Product"
        p_sku = upd.product.sku if upd.product else "N/A"
        
        details = InventoryUpdateOut(
            id=upd.id,
            store_id=upd.store_id,
            product_id=upd.product_id,
            product_name=p_name,
            sku=p_sku,
            previous_quantity=upd.previous_quantity,
            new_quantity=upd.new_quantity,
            variance=upd.variance,
            status=upd.status,
            confidence=upd.confidence,
            notes=upd.notes,
            created_at=upd.created_at
        )

        output.append(ApprovalRequestOut(
            id=r.id,
            inventory_update_id=r.inventory_update_id,
            requested_by=r.requested_by,
            status=r.status,
            approver_notes=r.approver_notes,
            reviewed_at=r.reviewed_at,
            update_details=details
        ))
    return output


@router.post("/approve/{update_id}")
def approve_pending_revision(
    update_id: int,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Approves a pending stock revision request, applying changes to inventory."""
    try:
        service.approve_update_request(db, update_id, current_user.id, notes)
        return {"status": "Success", "message": f"Update ID {update_id} approved and applied successfully."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/reject/{update_id}")
def reject_pending_revision(
    update_id: int,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Rejects a pending stock revision request."""
    try:
        service.reject_update_request(db, update_id, notes)
        return {"status": "Success", "message": f"Update ID {update_id} rejected."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/rollback")
def rollback_batch_updates(
    payload: RollbackPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Initiate batch rollback restoring previous stocks snapshots tags."""
    try:
        count = service.rollback_batch(db, payload.rollback_batch_tag, payload.store_id, current_user.id)
        return {"status": "Success", "message": f"Rollback completed successfully. Reverted {count} items records."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history", response_model=List[InventoryUpdateOut])
def get_inventory_update_history(
    store_id: int = 1,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve full timeline logs details tracking adjustments."""
    logs = db.query(InventoryUpdateModel).filter(InventoryUpdateModel.store_id == store_id).order_by(InventoryUpdateModel.created_at.desc()).all()
    output = []
    
    for l in logs:
        p_name = l.product.name if l.product else "Unknown Product"
        p_sku = l.product.sku if l.product else "N/A"
        
        output.append(InventoryUpdateOut(
            id=l.id,
            store_id=l.store_id,
            product_id=l.product_id,
            product_name=p_name,
            sku=p_sku,
            previous_quantity=l.previous_quantity,
            new_quantity=l.new_quantity,
            variance=l.variance,
            status=l.status,
            confidence=l.confidence,
            notes=l.notes,
            created_at=l.created_at
        ))
    return output


@router.get("/snapshots")
def list_available_snapshots(
    store_id: int = 1,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve list of batch snapshot tags available for rollback selection."""
    tags = db.query(
        InventorySnapshotModel.snapshot_batch_tag,
        func.count(InventorySnapshotModel.id).label("records_count"),
        func.min(InventorySnapshotModel.created_at).label("created_at")
    ).filter(InventorySnapshotModel.store_id == store_id).group_by(InventorySnapshotModel.snapshot_batch_tag).all()
    
    return [
        {
            "tag": t.snapshot_batch_tag,
            "records_count": t.records_count,
            "created_at": t.created_at
        }
        for t in tags
    ]
