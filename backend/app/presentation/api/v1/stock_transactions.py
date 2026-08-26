from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.core.exceptions import EntityNotFoundException
from app.data.models.stock_transaction_model import StockTransactionModel
from app.data.models.inventory_model import InventoryModel
from app.data.models.product_model import ProductModel
from app.data.models.store_model import StoreModel
from app.domain.entities.user import User
from app.presentation.api.v1.auth import get_current_user
from app.presentation.schemas.stock_transaction_schemas import StockTransactionCreate, StockTransactionOut

router = APIRouter(prefix="/transactions", tags=["stock-transactions"])


@router.get("", response_model=List[StockTransactionOut])
def list_transactions(
    store_id: Optional[int] = None,
    product_id: Optional[int] = None,
    transaction_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve full inventory stock ledger audit trails, with seeding defaults if empty."""
    query = db.query(StockTransactionModel)
    if store_id:
        query = query.filter(StockTransactionModel.store_id == store_id)
    if product_id:
        query = query.filter(StockTransactionModel.product_id == product_id)
    if transaction_type:
        query = query.filter(StockTransactionModel.transaction_type == transaction_type)
        
    transactions = query.order_by(StockTransactionModel.created_at.desc()).all()
    
    if not transactions and store_id:
        # Pre-seed sample transactions so visual table is ready
        first_prod = db.query(ProductModel).first()
        if first_prod:
            seeds = [
                StockTransactionModel(
                    store_id=store_id, 
                    product_id=first_prod.id, 
                    user_id=current_user.id,
                    transaction_type="Purchase", 
                    quantity_change=50, 
                    previous_quantity=0, 
                    new_quantity=50,
                    notes="Initial warehouse inventory shipment ingestion.",
                    created_at=func.now()
                ),
                StockTransactionModel(
                    store_id=store_id, 
                    product_id=first_prod.id, 
                    user_id=current_user.id,
                    transaction_type="Sale", 
                    quantity_change=-5, 
                    previous_quantity=50, 
                    new_quantity=45,
                    notes="Self-checkout register transaction #1098.",
                    created_at=func.now()
                ),
                StockTransactionModel(
                    store_id=store_id, 
                    product_id=first_prod.id, 
                    user_id=current_user.id,
                    transaction_type="Damage", 
                    quantity_change=-2, 
                    previous_quantity=45, 
                    new_quantity=43,
                    notes="Identified ruptured seal packaging on aisle shelf level 1.",
                    created_at=func.now()
                )
            ]
            for s in seeds:
                db.add(s)
            db.commit()
            transactions = db.query(StockTransactionModel).filter(StockTransactionModel.store_id == store_id).order_by(StockTransactionModel.created_at.desc()).all()
            
    return transactions


@router.post("", response_model=StockTransactionOut, status_code=status.HTTP_201_CREATED)
def create_transaction(
    payload: StockTransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Log a stock transaction movement.
    Automatically reconciles corresponding InventoryModel counts based on quantity_change!
    """
    product = db.query(ProductModel).filter(ProductModel.id == payload.product_id).first()
    if not product:
        raise EntityNotFoundException("Product Catalog Item", str(payload.product_id))

    store = db.query(StoreModel).filter(StoreModel.id == payload.store_id).first()
    if not store:
        raise EntityNotFoundException("Store Branch", str(payload.store_id))

    # Fetch corresponding inventory
    inv = db.query(InventoryModel).filter(
        InventoryModel.store_id == payload.store_id,
        InventoryModel.product_id == payload.product_id
    ).first()

    previous_qty = 0
    if inv:
        previous_qty = inv.quantity
    else:
        # Create inventory row if it doesn't exist
        inv = InventoryModel(
            store_id=payload.store_id,
            product_id=payload.product_id,
            name=product.name,
            sku=product.sku,
            quantity=0,
            available_stock=0,
            reserved_stock=0,
            damaged_stock=0,
            location_bin="Receiving Dock",
            confidence=1.0,
            status="In Stock"
        )
        db.add(inv)
        db.flush()

    # Reconcile quantities
    new_qty = previous_qty + payload.quantity_change
    if new_qty < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid transaction. Insufficient inventory units. Current: {previous_qty}, Ingested change: {payload.quantity_change}"
        )

    # Apply quantity updates
    inv.quantity = new_qty
    
    # Process types specific changes
    t_type = payload.transaction_type.strip()
    if t_type == "Damage":
        inv.damaged_stock += abs(payload.quantity_change)
        inv.available_stock = max(0, inv.quantity - inv.damaged_stock - inv.reserved_stock)
    elif t_type == "Sale":
        inv.available_stock = max(0, inv.quantity - inv.damaged_stock - inv.reserved_stock)
    elif t_type == "Purchase" or t_type == "Return" or t_type == "Adjustment" or t_type == "AI Scan Update":
        inv.available_stock = max(0, inv.quantity - inv.damaged_stock - inv.reserved_stock)

    inv.status = "In Stock" if new_qty > 0 else "Out of Stock"
    inv.updated_at = func.now()

    # Create transaction log entry
    transaction = StockTransactionModel(
        store_id=payload.store_id,
        product_id=payload.product_id,
        user_id=current_user.id,
        transaction_type=t_type,
        quantity_change=payload.quantity_change,
        previous_quantity=previous_qty,
        new_quantity=new_qty,
        notes=payload.notes
    )

    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    
    return transaction
