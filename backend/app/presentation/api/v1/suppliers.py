from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.data.models.supplier_model import SupplierModel, ProductSupplierLink
from app.data.models.product_model import ProductModel
from app.data.models.audit_log_model import AuditLogModel
from app.domain.entities.user import User
from app.presentation.api.v1.auth import get_current_user
from app.presentation.schemas.product_schemas import SupplierOut, SupplierCreate, SupplierUpdate, ProductOut
import logging

logger = logging.getLogger("grocery_system")

router = APIRouter(prefix="/suppliers", tags=["supplier-management"])


def write_audit_log(db: Session, user_id: Optional[int], action: str, record_id: int, payload: dict):
    try:
        log = AuditLogModel(
            user_id=user_id,
            action=action,
            table_name="suppliers",
            record_id=record_id,
            payload=payload
        )
        db.add(log)
        db.commit()
    except Exception as e:
        logger.error(f"Audit log insertion failed: {str(e)}")



@router.get("", response_model=List[SupplierOut])
def list_suppliers(
    search: Optional[str] = None,
    region: Optional[str] = None,
    is_active: Optional[bool] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all suppliers with searching, region queries, and active status filters."""
    query = db.query(SupplierModel)

    if search:
        query = query.filter(
            SupplierModel.name.ilike(f"%{search}%") | 
            SupplierModel.company_name.ilike(f"%{search}%") |
            SupplierModel.contact_person.ilike(f"%{search}%")
        )

    if region:
        query = query.filter(SupplierModel.region.ilike(region))

    if is_active is not None:
        query = query.filter(SupplierModel.is_active == is_active)

    suppliers = query.offset(skip).limit(limit).all()

    # Pre-seed a few suppliers if empty for ease of testing
    if not suppliers and not search and not region and is_active is None:
        seeds = [
            SupplierModel(
                name="Apex Foods Corp", 
                company_name="Apex Foodstuffs Global Ltd",
                contact_person="John Doe",
                contact_email="sales@apexfoods.com", 
                phone="+1-555-0192", 
                address="100 Distribution Way",
                gst_vat="GST123456",
                region="US",
                payment_terms="Net 30",
                is_active=True
            ),
            SupplierModel(
                name="Global Agro Ltd", 
                company_name="Global Agriculture Cooperative",
                contact_person="Alice Smith",
                contact_email="orders@globalagro.org", 
                phone="+1-555-0143", 
                address="42 Farm Road",
                gst_vat="VAT7890",
                region="EU",
                payment_terms="COD",
                is_active=True
            ),
            SupplierModel(
                name="Metro Grocers Inc", 
                company_name="Metro Logistics Partners",
                contact_person="Bob Johnson",
                contact_email="contact@metrogrocers.net", 
                phone="+1-555-0187", 
                address="500 Logistics Ave",
                gst_vat="GST9999",
                region="IN",
                payment_terms="Net 60",
                is_active=True
            )
        ]
        for s in seeds:
            db.add(s)
        db.commit()
        suppliers = query.offset(skip).limit(limit).all()

    return suppliers


@router.post("", response_model=SupplierOut, status_code=status.HTTP_201_CREATED)
def create_supplier(
    payload: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Creates a new supplier."""
    supplier = SupplierModel(
        name=payload.name,
        company_name=payload.company_name,
        contact_person=payload.contact_person,
        contact_email=payload.contact_email,
        phone=payload.phone,
        address=payload.address,
        gst_vat=payload.gst_vat,
        region=payload.region,
        payment_terms=payload.payment_terms,
        is_active=payload.is_active
    )
    db.add(supplier)
    db.commit()
    db.refresh(supplier)

    write_audit_log(
        db=db,
        user_id=current_user.id if current_user else None,
        action="CREATE",
        record_id=supplier.id,
        payload={"name": supplier.name, "company_name": supplier.company_name}
    )

    return supplier


@router.get("/{id}", response_model=SupplierOut)
def get_supplier(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves a single supplier by ID."""
    supplier = db.query(SupplierModel).filter(SupplierModel.id == id).first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with ID {id} not found."
        )
    return supplier


@router.put("/{id}", response_model=SupplierOut)
def update_supplier(
    id: int,
    payload: SupplierUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Updates an existing supplier's details."""
    supplier = db.query(SupplierModel).filter(SupplierModel.id == id).first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with ID {id} not found."
        )

    if payload.name is not None:
        supplier.name = payload.name
    if payload.company_name is not None:
        supplier.company_name = payload.company_name
    if payload.contact_person is not None:
        supplier.contact_person = payload.contact_person
    if payload.contact_email is not None:
        supplier.contact_email = payload.contact_email
    if payload.phone is not None:
        supplier.phone = payload.phone
    if payload.address is not None:
        supplier.address = payload.address
    if payload.gst_vat is not None:
        supplier.gst_vat = payload.gst_vat
    if payload.region is not None:
        supplier.region = payload.region
    if payload.payment_terms is not None:
        supplier.payment_terms = payload.payment_terms
    if payload.is_active is not None:
        supplier.is_active = payload.is_active

    db.commit()
    db.refresh(supplier)

    write_audit_log(
        db=db,
        user_id=current_user.id if current_user else None,
        action="UPDATE",
        record_id=supplier.id,
        payload={"name": supplier.name, "updated_fields": payload.model_dump(exclude_unset=True)}
    )

    return supplier


@router.delete("/{id}")
def delete_supplier(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deletes a supplier record."""
    supplier = db.query(SupplierModel).filter(SupplierModel.id == id).first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with ID {id} not found."
        )
    db.delete(supplier)
    db.commit()

    write_audit_log(
        db=db,
        user_id=current_user.id if current_user else None,
        action="DELETE",
        record_id=supplier.id,
        payload={"name": supplier.name}
    )

    return {"success": True, "message": "Supplier deleted successfully."}


# Supplier-Product Many-to-Many Mappings API
@router.post("/{id}/products/{product_id}", status_code=status.HTTP_200_OK)
def link_supplier_to_product(
    id: int,
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Links a supplier to a product to support multiple suppliers per product."""
    supplier = db.query(SupplierModel).filter(SupplierModel.id == id).first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with ID {id} not found."
        )

    product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found."
        )

    exists = db.query(ProductSupplierLink).filter_by(
        product_id=product_id,
        supplier_id=id
    ).first()

    if not exists:
        link = ProductSupplierLink(product_id=product_id, supplier_id=id)
        db.add(link)
        db.commit()

        write_audit_log(
            db=db,
            user_id=current_user.id if current_user else None,
            action="LINK_PRODUCT",
            record_id=id,
            payload={"product_id": product_id}
        )

    return {"success": True, "message": f"Supplier linked to product successfully."}


@router.delete("/{id}/products/{product_id}", status_code=status.HTTP_200_OK)
def unlink_supplier_from_product(
    id: int,
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Unlinks a supplier from a product."""
    link = db.query(ProductSupplierLink).filter_by(
        product_id=product_id,
        supplier_id=id
    ).first()

    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Association between supplier and product not found."
        )

    db.delete(link)
    db.commit()

    write_audit_log(
        db=db,
        user_id=current_user.id if current_user else None,
        action="UNLINK_PRODUCT",
        record_id=id,
        payload={"product_id": product_id}
    )

    return {"success": True, "message": "Supplier unlinked from product successfully."}


@router.get("/{id}/products", response_model=List[ProductOut])
def get_supplier_products(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieves list of products linked to a specific supplier."""
    supplier = db.query(SupplierModel).filter(SupplierModel.id == id).first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with ID {id} not found."
        )
    return supplier.products
