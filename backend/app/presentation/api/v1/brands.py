import os
import shutil
import secrets
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.config import settings
from app.data.models.brand_model import BrandModel
from app.presentation.schemas.brand_schemas import (
    BrandCreate,
    BrandUpdate,
    BrandOut
)
from app.presentation.api.v1.auth import get_current_user
from app.domain.entities.user import User
from app.data.models.audit_log_model import AuditLogModel
import logging

logger = logging.getLogger("grocery_system")

router = APIRouter(prefix="/brands", tags=["brands-management"])

UPLOAD_DIR = os.path.join(settings.LOCAL_STORAGE_DIR, "logos")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def write_audit_log(db: Session, user_id: Optional[int], action: str, record_id: int, payload: dict):
    try:
        log = AuditLogModel(
            user_id=user_id,
            action=action,
            table_name="brands",
            record_id=record_id,
            payload=payload
        )
        db.add(log)
        db.commit()
    except Exception as e:
        logger.error(f"Audit log insertion failed: {str(e)}")



@router.post("", response_model=BrandOut, status_code=status.HTTP_201_CREATED)
def create_brand(
    payload: BrandCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Creates a new brand. Prevents duplicate brand names."""
    dup = db.query(BrandModel).filter(
        BrandModel.name == payload.name,
        BrandModel.deleted_at.is_(None)
    ).first()
    if dup:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Brand with this name already exists."
        )

    brand = BrandModel(
        name=payload.name,
        logo_url=payload.logo_url,
        description=payload.description,
        country_of_origin=payload.country_of_origin,
        website=payload.website,
        is_active=payload.is_active
    )
    db.add(brand)
    db.commit()
    db.refresh(brand)

    write_audit_log(
        db=db,
        user_id=current_user.id if current_user else None,
        action="CREATE",
        record_id=brand.id,
        payload={"name": brand.name, "origin": brand.country_of_origin}
    )

    return brand


@router.get("", response_model=List[BrandOut])
def list_brands(
    search: Optional[str] = None,
    country: Optional[str] = None,
    include_deleted: bool = False,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Lists all brands with filters and pagination."""
    query = db.query(BrandModel)

    if not include_deleted:
        query = query.filter(BrandModel.deleted_at.is_(None))

    if search:
        query = query.filter(
            BrandModel.name.ilike(f"%{search}%") | 
            BrandModel.description.ilike(f"%{search}%")
        )

    if country:
        query = query.filter(BrandModel.country_of_origin.ilike(country))

    query = query.order_by(BrandModel.name.asc())
    return query.offset(skip).limit(limit).all()


@router.get("/{id}", response_model=BrandOut)
def get_brand(id: int, db: Session = Depends(get_db)):
    """Retrieves a single brand's details."""
    brand = db.query(BrandModel).filter(
        BrandModel.id == id,
        BrandModel.deleted_at.is_(None)
    ).first()
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand not found or deleted."
        )
    return brand


@router.put("/{id}", response_model=BrandOut)
def update_brand(
    id: int,
    payload: BrandUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Updates an existing brand's details."""
    brand = db.query(BrandModel).filter(
        BrandModel.id == id,
        BrandModel.deleted_at.is_(None)
    ).first()
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand not found."
        )

    if payload.name is not None:
        # Check name unique if changing
        if payload.name != brand.name:
            dup = db.query(BrandModel).filter(
                BrandModel.name == payload.name,
                BrandModel.deleted_at.is_(None)
            ).first()
            if dup:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Brand name already exists."
                )
        brand.name = payload.name

    if payload.logo_url is not None:
        brand.logo_url = payload.logo_url
    if payload.description is not None:
        brand.description = payload.description
    if payload.country_of_origin is not None:
        brand.country_of_origin = payload.country_of_origin
    if payload.website is not None:
        brand.website = payload.website
    if payload.is_active is not None:
        brand.is_active = payload.is_active

    db.commit()
    db.refresh(brand)

    write_audit_log(
        db=db,
        user_id=current_user.id if current_user else None,
        action="UPDATE",
        record_id=brand.id,
        payload={"name": brand.name, "updated_fields": payload.model_dump(exclude_unset=True)}
    )

    return brand


@router.delete("/{id}")
def delete_brand(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Soft deletes a brand by populating deleted_at timestamp."""
    brand = db.query(BrandModel).filter(
        BrandModel.id == id,
        BrandModel.deleted_at.is_(None)
    ).first()
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand not found."
        )

    brand.deleted_at = datetime.now(timezone.utc)
    db.commit()

    write_audit_log(
        db=db,
        user_id=current_user.id if current_user else None,
        action="DELETE",
        record_id=brand.id,
        payload={"name": brand.name, "deleted_at": str(brand.deleted_at)}
    )

    return {"success": True, "message": "Brand soft-deleted successfully."}


@router.patch("/{id}/restore")
def restore_brand(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Restores a soft-deleted brand."""
    brand = db.query(BrandModel).filter(BrandModel.id == id).first()
    if not brand:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brand not found."
        )

    brand.deleted_at = None
    db.commit()

    write_audit_log(
        db=db,
        user_id=current_user.id if current_user else None,
        action="RESTORE",
        record_id=brand.id,
        payload={"name": brand.name}
    )

    return {"success": True, "message": "Brand restored successfully."}


@router.post("/upload-logo")
async def upload_brand_logo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Handles logo file uploading and returns the accessible static storage link."""
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in [".jpg", ".jpeg", ".png", ".svg"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported image format. Upload JPG, PNG, or SVG."
        )

    filename = f"logo_{secrets.token_hex(6)}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "success": True,
        "logo_url": f"/static/uploads/logos/{filename}"
    }
