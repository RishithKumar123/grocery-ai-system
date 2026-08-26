import logging
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.data.models.product_model import ProductModel
from app.data.models.inventory_model import InventoryModel
from app.data.models.stock_transaction_model import StockTransactionModel
from app.data.models.inventory_update_model import (
    InventoryUpdateModel,
    InventoryAdjustmentModel,
    InventoryReconciliationModel,
    InventorySnapshotModel,
    UpdateRuleModel,
    UpdateQueueModel,
    ApprovalRequestModel,
    RollbackHistoryModel
)

logger = logging.getLogger("grocery_system")


class InventoryUpdateService:
    """Enterprise Automatic Inventory Update Engine pipeline layer."""

    def seed_default_rules_if_empty(self, db: Session):
        """Pre-populates default update rules thresholds."""
        default_rules = [
            {"key": "min_confidence_threshold", "name": "Minimum Confidence Threshold", "value": "0.60", "desc": "Rejects updates with prediction confidence lower than this."},
            {"key": "require_approval_variance_threshold", "name": "Approval Variance Threshold", "value": "10", "desc": "Requires manual auditor approval if absolute variance exceeds this quantity."},
            {"key": "prevent_negative_inventory", "name": "Prevent Negative Inventory", "value": "true", "desc": "Blocks updates that drop stock below 0."},
            {"key": "variance_percent_approval_threshold", "name": "Variance Percentage Approval", "value": "50.0", "desc": "Requires approval if stock variance percent exceeds this threshold."}
        ]

        for r in default_rules:
            existing = db.query(UpdateRuleModel).filter(UpdateRuleModel.rule_key == r["key"]).first()
            if not existing:
                rule = UpdateRuleModel(
                    rule_key=r["key"],
                    rule_name=r["name"],
                    value=r["value"],
                    description=r["desc"],
                    is_active=True
                )
                db.add(rule)
        db.commit()

    def get_rule_value(self, db: Session, key: str, default: str) -> str:
        """Fetches rule value from DB."""
        rule = db.query(UpdateRuleModel).filter(UpdateRuleModel.rule_key == key, UpdateRuleModel.is_active == True).first()
        return rule.value if rule else default

    def apply_update(
        self,
        db: Session,
        store_id: int,
        product_id: int,
        new_quantity: int,
        confidence: float,
        notes: Optional[str] = None,
        user_id: Optional[int] = None,
        requested_by: str = "AI Sync Engine"
    ) -> InventoryUpdateModel:
        """Compares stock levels, validates rules constraints, and updates database."""
        logger.info(f"InventorySync: Applying update for product={product_id} at store={store_id}")
        self.seed_default_rules_if_empty(db)

        # 1. Rules Check: Minimum Confidence Threshold
        min_conf = float(self.get_rule_value(db, "min_confidence_threshold", "0.60"))
        if confidence < min_conf:
            raise ValueError(f"Update rejected: Confidence {confidence} is below minimum threshold of {min_conf}.")

        # 2. Check if product exists
        prod = db.query(ProductModel).filter(ProductModel.id == product_id).first()
        if not prod:
            raise ValueError("Catalog product not found.")

        # 3. Prevent Negative Inventory
        prevent_neg = self.get_rule_value(db, "prevent_negative_inventory", "true") == "true"
        if prevent_neg and new_quantity < 0:
            raise ValueError("Update rejected: Negative inventory levels are prevented by business rules.")

        # 4. Fetch or seed current inventory item
        inv = db.query(InventoryModel).filter(
            InventoryModel.store_id == store_id,
            InventoryModel.product_id == product_id
        ).first()

        prev_qty = 0
        if inv:
            prev_qty = inv.quantity
        else:
            # Seed inventory item if not exists
            inv = InventoryModel(
                store_id=store_id,
                product_id=product_id,
                name=prod.name,
                sku=prod.sku,
                quantity=0,
                available_stock=0
            )
            db.add(inv)
            db.commit()
            db.refresh(inv)

        variance = new_quantity - prev_qty
        
        # Write Update Record in Pending state
        upd = InventoryUpdateModel(
            store_id=store_id,
            product_id=product_id,
            previous_quantity=prev_qty,
            new_quantity=new_quantity,
            variance=variance,
            status="Pending",
            confidence=confidence,
            notes=notes
        )
        db.add(upd)
        db.commit()
        db.refresh(upd)

        # 5. Check Variance Approval rules
        var_limit = int(self.get_rule_value(db, "require_approval_variance_threshold", "10"))
        variance_percent = 0.0
        if prev_qty > 0:
            variance_percent = (abs(variance) / prev_qty) * 100

        var_pct_limit = float(self.get_rule_value(db, "variance_percent_approval_threshold", "50.0"))

        needs_approval = (abs(variance) > var_limit) or (variance_percent > var_pct_limit)

        if needs_approval:
            # Route to Approval Queue
            app_req = ApprovalRequestModel(
                inventory_update_id=upd.id,
                requested_by=requested_by,
                status="Pending"
            )
            db.add(app_req)
            db.commit()
            logger.warning(f"InventorySync: High variance update id={upd.id} routed to approvals queue.")
            return upd
        else:
            # Automatically apply the update
            self.execute_stock_revision(db, upd, inv, user_id)
            return upd

    def execute_stock_revision(self, db: Session, upd: InventoryUpdateModel, inv: InventoryModel, user_id: Optional[int]):
        """Modifies physical inventory levels, logging snapshots and audit adjustments."""
        # 1. Take Snapshot
        batch_tag = f"SNAP-{uuid.uuid4().hex[:8].upper()}"
        snap = InventorySnapshotModel(
            store_id=inv.store_id,
            product_id=inv.product_id,
            quantity=inv.quantity,
            snapshot_batch_tag=batch_tag
        )
        db.add(snap)

        # 2. Update stock
        inv.quantity = upd.new_quantity
        inv.available_stock = upd.new_quantity
        inv.confidence = upd.confidence
        
        # 3. Log Adjustment
        adj_type = "Stock Increase" if upd.variance >= 0 else "Stock Decrease"
        adj = InventoryAdjustmentModel(
            inventory_update_id=upd.id,
            product_id=inv.product_id,
            store_id=inv.store_id,
            adjustment_type=adj_type,
            quantity_adjusted=upd.variance,
            adjusted_by_user_id=user_id
        )
        db.add(adj)

        # 4. Log Transaction in Stock Movements Ledger
        tx = StockTransactionModel(
            store_id=inv.store_id,
            product_id=inv.product_id,
            user_id=user_id,
            transaction_type="AI Scan Update",
            quantity_change=upd.variance,
            previous_quantity=upd.previous_quantity,
            new_quantity=upd.new_quantity,
            notes=f"Auto sync update id #{upd.id}. Snapshot tag: {batch_tag}"
        )
        db.add(tx)

        # Save status
        upd.status = "Applied"
        db.commit()

        # Update Reconciliation metrics
        self.recalculate_reconciliation(db, inv.store_id)
        logger.info(f"InventorySync: Applied stock revision product={inv.product_id} quantity={upd.new_quantity}")

    def approve_update_request(self, db: Session, update_id: int, user_id: Optional[int], notes: Optional[str] = None):
        """Approves a pending variance update in the queue."""
        upd = db.query(InventoryUpdateModel).filter(InventoryUpdateModel.id == update_id).first()
        req = db.query(ApprovalRequestModel).filter(ApprovalRequestModel.inventory_update_id == update_id).first()
        if not upd or not req:
            raise ValueError("Update request not found.")

        if req.status != "Pending":
            raise ValueError(f"Request already processed with status: {req.status}")

        inv = db.query(InventoryModel).filter(
            InventoryModel.store_id == upd.store_id,
            InventoryModel.product_id == upd.product_id
        ).first()

        if not inv:
            raise ValueError("Inventory record not seeded.")

        # Apply revision
        self.execute_stock_revision(db, upd, inv, user_id)

        # Update status
        req.status = "Approved"
        req.approver_notes = notes
        req.reviewed_at = datetime.utcnow()
        db.commit()

    def reject_update_request(self, db: Session, update_id: int, notes: Optional[str] = None):
        """Rejects a pending variance update in the queue."""
        upd = db.query(InventoryUpdateModel).filter(InventoryUpdateModel.id == update_id).first()
        req = db.query(ApprovalRequestModel).filter(ApprovalRequestModel.inventory_update_id == update_id).first()
        if not upd or not req:
            raise ValueError("Update request not found.")

        req.status = "Rejected"
        req.approver_notes = notes
        req.reviewed_at = datetime.utcnow()
        upd.status = "Rejected"
        db.commit()

    def rollback_batch(self, db: Session, rollback_batch_tag: str, store_id: int, user_id: Optional[int]) -> int:
        """Restores previous inventory snapshots, reversing revision transactions."""
        logger.info(f"InventorySync: Executing rollback for batch={rollback_batch_tag}")
        snaps = db.query(InventorySnapshotModel).filter(
            InventorySnapshotModel.snapshot_batch_tag == rollback_batch_tag,
            InventorySnapshotModel.store_id == store_id
        ).all()

        if not snaps:
            raise ValueError("No snapshots found matching this batch tag.")

        reverted_count = 0
        for s in snaps:
            inv = db.query(InventoryModel).filter(
                InventoryModel.store_id == store_id,
                InventoryModel.product_id == s.product_id
            ).first()

            if inv:
                prev_qty = inv.quantity
                inv.quantity = s.quantity
                inv.available_stock = s.quantity

                # Record Rollback adjustment
                adj = InventoryAdjustmentModel(
                    product_id=s.product_id,
                    store_id=store_id,
                    adjustment_type="Rollback",
                    quantity_adjusted=s.quantity - prev_qty,
                    adjusted_by_user_id=user_id
                )
                db.add(adj)

                # Record stock transaction rollback
                tx = StockTransactionModel(
                    store_id=store_id,
                    product_id=s.product_id,
                    user_id=user_id,
                    transaction_type="Adjustment",
                    quantity_change=s.quantity - prev_qty,
                    previous_quantity=prev_qty,
                    new_quantity=s.quantity,
                    notes=f"Rollback operation for snapshot batch: {rollback_batch_tag}"
                )
                db.add(tx)
                reverted_count += 1

        # Mark update updates status as Rolled Back
        updates = db.query(InventoryUpdateModel).filter(
            InventoryUpdateModel.store_id == store_id,
            InventoryUpdateModel.status == "Applied"
        ).all()
        for u in updates:
            u.status = "Rolled Back"

        # Log rollback history
        history = RollbackHistoryModel(
            rollback_batch_tag=rollback_batch_tag,
            rolled_back_by_user_id=user_id,
            store_id=store_id,
            reverted_records_count=reverted_count
        )
        db.add(history)
        
        db.commit()
        
        self.recalculate_reconciliation(db, store_id)
        return reverted_count

    def recalculate_reconciliation(self, db: Session, store_id: int):
        """Generates reconciliation reports matching current stocks vs updates history."""
        total_items_db = db.query(func.sum(InventoryModel.quantity)).filter(InventoryModel.store_id == store_id).scalar() or 0
        
        # Calculate recent AI update quantities sum
        total_items_ai = db.query(func.sum(InventoryUpdateModel.new_quantity)).filter(
            InventoryUpdateModel.store_id == store_id,
            InventoryUpdateModel.status == "Applied"
        ).scalar() or 0

        variance = total_items_ai - total_items_db
        accuracy_rate = 100.0
        if total_items_db > 0:
            accuracy_rate = max(100.0 - (abs(variance) / total_items_db * 100), 0.0)

        # Clear old logs
        db.query(InventoryReconciliationModel).filter(InventoryReconciliationModel.store_id == store_id).delete()

        recon = InventoryReconciliationModel(
            store_id=store_id,
            total_items_db=int(total_items_db),
            total_items_ai=int(total_items_ai),
            variance_count=int(variance),
            accuracy_rate=round(accuracy_rate, 2)
        )
        db.add(recon)
        db.commit()
