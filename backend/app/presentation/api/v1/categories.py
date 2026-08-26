from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.data.models.category_model import CategoryModel
from app.presentation.schemas.category_schemas import (
    CategoryCreate,
    CategoryUpdate,
    CategoryOut,
    CategoryTreeOut
)
from app.presentation.api.v1.auth import get_current_user
from app.domain.entities.user import User

router = APIRouter(prefix="/categories", tags=["categories-management"])


@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Creates a new category. Prevents duplicate subcategory names under the same parent."""
    # Check parent exists if provided
    if payload.parent_id is not None:
        parent = db.query(CategoryModel).filter(
            CategoryModel.id == payload.parent_id,
            CategoryModel.deleted_at.is_(None)
        ).first()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent category with id {payload.parent_id} not found."
            )

    # Check duplicate under same parent
    dup = db.query(CategoryModel).filter(
        CategoryModel.name == payload.name,
        CategoryModel.parent_id == payload.parent_id,
        CategoryModel.deleted_at.is_(None)
    ).first()
    if dup:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category with this name already exists under the target parent."
        )

    category = CategoryModel(
        name=payload.name,
        description=payload.description,
        parent_id=payload.parent_id,
        image_url=payload.image_url,
        icon_name=payload.icon_name,
        is_active=payload.is_active,
        order_index=payload.order_index
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.get("", response_model=List[CategoryOut])
def list_categories(
    search: Optional[str] = None,
    parent_id: Optional[int] = Query(default=None),
    only_roots: bool = False,
    include_deleted: bool = False,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Lists categories with filtering, pagination, and parent nesting checks."""
    query = db.query(CategoryModel)

    if not include_deleted:
        query = query.filter(CategoryModel.deleted_at.is_(None))

    if search:
        query = query.filter(CategoryModel.name.ilike(f"%{search}%") | CategoryModel.description.ilike(f"%{search}%"))

    if only_roots:
        query = query.filter(CategoryModel.parent_id.is_(None))
    elif parent_id is not None:
        query = query.filter(CategoryModel.parent_id == parent_id)

    query = query.order_by(CategoryModel.order_index.asc(), CategoryModel.name.asc())
    return query.offset(skip).limit(limit).all()


@router.get("/{id}", response_model=CategoryOut)
def get_category(id: int, db: Session = Depends(get_db)):
    """Retrieves a single active category detail."""
    category = db.query(CategoryModel).filter(
        CategoryModel.id == id,
        CategoryModel.deleted_at.is_(None)
    ).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found or deleted."
        )
    return category


@router.put("/{id}", response_model=CategoryOut)
def update_category(
    id: int,
    payload: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Modifies an existing category."""
    category = db.query(CategoryModel).filter(
        CategoryModel.id == id,
        CategoryModel.deleted_at.is_(None)
    ).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found."
        )

    # Avoid self-referencing hierarchy loop
    if payload.parent_id == id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A category cannot be its own parent."
        )

    if payload.name is not None:
        category.name = payload.name
    if payload.description is not None:
        category.description = payload.description
    if payload.parent_id is not None:
        category.parent_id = payload.parent_id
    if payload.image_url is not None:
        category.image_url = payload.image_url
    if payload.icon_name is not None:
        category.icon_name = payload.icon_name
    if payload.is_active is not None:
        category.is_active = payload.is_active
    if payload.order_index is not None:
        category.order_index = payload.order_index

    db.commit()
    db.refresh(category)
    return category


@router.delete("/{id}")
def delete_category(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Soft deletes a category and sets deleted_at timestamp."""
    category = db.query(CategoryModel).filter(
        CategoryModel.id == id,
        CategoryModel.deleted_at.is_(None)
    ).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found."
        )

    category.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return {"success": True, "message": "Category soft-deleted successfully."}


@router.patch("/{id}/restore")
def restore_category(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Restores a soft-deleted category."""
    category = db.query(CategoryModel).filter(CategoryModel.id == id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found."
        )

    category.deleted_at = None
    db.commit()
    return {"success": True, "message": "Category restored successfully."}
