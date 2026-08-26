import pytest
from sqlalchemy.orm import Session
from app.data.models.product_model import ProductModel
from app.data.models.inventory_model import InventoryModel
from app.data.models.inventory_update_model import (
    InventoryUpdateModel,
    InventoryAdjustmentModel,
    InventorySnapshotModel,
    UpdateRuleModel,
    ApprovalRequestModel
)
from app.services.inventory_update_service import InventoryUpdateService


def test_automatic_inventory_sync_and_approval_routing(db_session: Session):
    service = InventoryUpdateService()

    # Seed catalog item
    prod = ProductModel(name="Aetheria Juice 1L", barcode="4444444444444", sku="JUICE-1L", category="Beverages", price=120.0)
    db_session.add(prod)
    db_session.commit()

    # Seed current inventory stock
    inv = InventoryModel(store_id=1, product_id=prod.id, name=prod.name, sku=prod.sku, quantity=20, available_stock=20)
    db_session.add(inv)
    db_session.commit()

    # 1. Reject low confidence update
    with pytest.raises(ValueError, match="is below minimum threshold"):
        service.apply_update(
            db=db_session,
            store_id=1,
            product_id=prod.id,
            new_quantity=22,
            confidence=0.45 # Threshold is 0.60
        )

    # 2. Apply low-variance update immediately (variance = +3 <= threshold 10)
    upd1 = service.apply_update(
        db=db_session,
        store_id=1,
        product_id=prod.id,
        new_quantity=23,
        confidence=0.85
    )

    assert upd1.status == "Applied"
    assert upd1.variance == 3
    
    # Reload inventory stock
    db_session.refresh(inv)
    assert inv.quantity == 23

    # 3. Route high-variance update to queue (variance = +15 > threshold 10)
    upd2 = service.apply_update(
        db=db_session,
        store_id=1,
        product_id=prod.id,
        new_quantity=38,
        confidence=0.90
    )

    assert upd2.status == "Pending"
    # Stock should remain unchanged
    db_session.refresh(inv)
    assert inv.quantity == 23

    # Verify approval request created
    req = db_session.query(ApprovalRequestModel).filter(ApprovalRequestModel.inventory_update_id == upd2.id).first()
    assert req is not None
    assert req.status == "Pending"


def test_inventory_snapshots_rollback_process(db_session: Session):
    service = InventoryUpdateService()

    # Seed catalog item
    prod = ProductModel(name="Aetheria Crisps 150g", barcode="5555555555555", sku="CRISPS-150G", category="Snacks", price=60.0)
    db_session.add(prod)
    db_session.commit()

    inv = InventoryModel(store_id=1, product_id=prod.id, name=prod.name, sku=prod.sku, quantity=50, available_stock=50)
    db_session.add(inv)
    db_session.commit()

    # Apply auto-update
    upd = service.apply_update(
        db=db_session,
        store_id=1,
        product_id=prod.id,
        new_quantity=55,
        confidence=0.95
    )
    
    db_session.refresh(inv)
    assert inv.quantity == 55

    # Fetch snapshot tag created
    snap = db_session.query(InventorySnapshotModel).filter(InventorySnapshotModel.product_id == prod.id).first()
    assert snap is not None
    assert snap.quantity == 50 # Stores previous stock state
    tag = snap.snapshot_batch_tag

    # Execute rollback
    reverted = service.rollback_batch(db=db_session, rollback_batch_tag=tag, store_id=1, user_id=None)
    assert reverted == 1

    db_session.refresh(inv)
    assert inv.quantity == 50 # Reverted back successfully
