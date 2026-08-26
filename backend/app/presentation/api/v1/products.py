import csv
import io
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from app.core.database import get_db
from app.core.exceptions import EntityNotFoundException, EntityAlreadyExistsException
from app.data.models.product_model import ProductModel
from app.data.models.inventory_model import InventoryModel
from app.data.models.supplier_model import SupplierModel
from app.data.repositories.storage_repository import StorageRepository
from app.domain.entities.user import User
from app.presentation.api.v1.auth import get_current_user
from app.presentation.schemas.product_schemas import ProductCreate, ProductUpdate, ProductOut

router = APIRouter(prefix="/products", tags=["product-management"])
storage = StorageRepository()


def map_to_product_out(p: ProductModel, db: Session) -> ProductOut:
    total_stock = db.query(func.sum(InventoryModel.quantity)).filter(
        InventoryModel.product_id == p.id
    ).scalar() or 0

    supplier_name = None
    if p.supplier_id:
        supplier = db.query(SupplierModel).filter(SupplierModel.id == p.supplier_id).first()
        supplier_name = supplier.name if supplier else None

    return ProductOut(
        id=p.id,
        name=p.name,
        barcode=p.barcode,
        sku=p.sku,
        category=p.category,
        brand=p.brand,
        variant=p.variant,
        weight=p.weight,
        price=float(p.price),
        image_url=p.image_url,
        description=p.description,
        supplier_id=p.supplier_id,
        supplier_name=supplier_name,
        total_stock=total_stock,
        created_at=p.created_at,
        updated_at=p.updated_at,
        
        # Extended specifications
        qr_code=p.qr_code,
        unit=p.unit,
        dimensions=p.dimensions,
        cost_price=float(p.cost_price),
        tax=float(p.tax),
        shelf_life=p.shelf_life,
        expiry_tracking=p.expiry_tracking,
        status=p.status,
        images=p.images,
        
        # AI Metadata
        yolo_class_mapping=p.yolo_class_mapping,
        clip_embeddings=p.clip_embeddings,
        ocr_reference_text=p.ocr_reference_text,
        confidence_threshold=p.confidence_threshold,
        aliases=p.aliases
    )


@router.get("", response_model=List[ProductOut])
def list_products(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = Query(None, description="Search by name, SKU, brand, barcode, OCR text, or aliases"),
    category: Optional[str] = Query(None, description="Filter by category"),
    brand: Optional[str] = Query(None, description="Filter by brand name"),
    supplier_id: Optional[int] = Query(None, description="Filter by supplier ID"),
    status_filter: Optional[str] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve list of products with advanced filters and fuzzy searches."""
    query = db.query(ProductModel)

    if category:
        query = query.filter(ProductModel.category == category)
    if brand:
        query = query.filter(ProductModel.brand.ilike(brand))
    if supplier_id:
        query = query.filter(ProductModel.supplier_id == supplier_id)
    if status_filter:
        query = query.filter(ProductModel.status == status_filter)

    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            or_(
                ProductModel.name.ilike(search_filter),
                ProductModel.sku.ilike(search_filter),
                ProductModel.barcode.ilike(search_filter),
                ProductModel.brand.ilike(search_filter),
                ProductModel.aliases.ilike(search_filter),
                ProductModel.ocr_reference_text.ilike(search_filter)
            )
        )

    products = query.offset(skip).limit(limit).all()
    return [map_to_product_out(p, db) for p in products]


@router.get("/{product_id}", response_model=ProductOut)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve details for a single catalog product."""
    product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if not product:
        raise EntityNotFoundException("Product", str(product_id))

    return map_to_product_out(product, db)


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Creates a new product catalog with full AI specifications."""
    exist_sku = db.query(ProductModel).filter(ProductModel.sku == payload.sku).first()
    if exist_sku:
        raise EntityAlreadyExistsException("Product SKU", payload.sku)

    exist_bar = db.query(ProductModel).filter(ProductModel.barcode == payload.barcode).first()
    if exist_bar:
        raise EntityAlreadyExistsException("Product Barcode", payload.barcode)

    product = ProductModel(
        name=payload.name,
        barcode=payload.barcode,
        sku=payload.sku,
        category=payload.category,
        brand=payload.brand,
        variant=payload.variant,
        weight=payload.weight,
        price=payload.price,
        supplier_id=payload.supplier_id,
        description=payload.description,
        
        # Extended Specifications
        qr_code=payload.qr_code,
        unit=payload.unit,
        dimensions=payload.dimensions,
        cost_price=payload.cost_price,
        tax=payload.tax,
        shelf_life=payload.shelf_life,
        expiry_tracking=payload.expiry_tracking,
        status=payload.status,
        images=payload.images,
        
        # AI Metadata
        yolo_class_mapping=payload.yolo_class_mapping,
        clip_embeddings=payload.clip_embeddings,
        ocr_reference_text=payload.ocr_reference_text,
        confidence_threshold=payload.confidence_threshold,
        aliases=payload.aliases
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    # Initial inventory stocking if requested
    if payload.store_id and payload.initial_stock and payload.initial_stock > 0:
        inventory = InventoryModel(
            store_id=payload.store_id,
            product_id=product.id,
            name=product.name,
            sku=product.sku,
            quantity=payload.initial_stock,
            status="In Stock"
        )
        db.add(inventory)
        db.commit()

    return map_to_product_out(product, db)


@router.put("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Updates catalog parameters of an existing product."""
    product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if not product:
        raise EntityNotFoundException("Product", str(product_id))

    update_data = payload.model_dump(exclude_unset=True)
    for key, val in update_data.items():
        setattr(product, key, val)

    db.commit()
    db.refresh(product)
    return map_to_product_out(product, db)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deletes a product from the system catalog."""
    product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if not product:
        raise EntityNotFoundException("Product", str(product_id))

    db.delete(product)
    db.commit()
    return


@router.post("/{product_id}/image", response_model=ProductOut)
async def upload_product_image(
    product_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Uploads an image file for a product and appends it to images array."""
    product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if not product:
        raise EntityNotFoundException("Product", str(product_id))

    file_bytes = await file.read()
    file_url = storage.upload_file(file_bytes, f"prod-{product_id}-{file.filename}", file.content_type)

    product.image_url = file_url
    
    # Store in comma-separated images array
    if product.images:
        product.images = f"{product.images},{file_url}"
    else:
        product.images = file_url

    db.commit()
    db.refresh(product)
    return map_to_product_out(product, db)


# Bulk and Import/Export Utilities
@router.post("/bulk-delete", status_code=status.HTTP_200_OK)
def bulk_delete_products(
    product_ids: List[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bulk deletes multiple products by ID list."""
    deleted_count = 0
    for pid in product_ids:
        product = db.query(ProductModel).filter(ProductModel.id == pid).first()
        if product:
            db.delete(product)
            deleted_count += 1
    db.commit()
    return {"success": True, "message": f"Successfully deleted {deleted_count} products."}


@router.get("/export/csv")
def export_products_csv(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Exports the entire product catalog as a CSV data stream."""
    products = db.query(ProductModel).all()
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "name", "sku", "barcode", "category", "brand", "variant", 
        "weight", "price", "description", "qr_code", "unit", "dimensions",
        "cost_price", "tax", "shelf_life", "expiry_tracking", "status",
        "yolo_class_mapping", "ocr_reference_text", "confidence_threshold", "aliases"
    ])

    for p in products:
        writer.writerow([
            p.name, p.sku, p.barcode, p.category, p.brand, p.variant,
            p.weight, float(p.price), p.description, p.qr_code, p.unit, p.dimensions,
            float(p.cost_price), float(p.tax), p.shelf_life, p.expiry_tracking, p.status,
            p.yolo_class_mapping, p.ocr_reference_text, p.confidence_threshold, p.aliases
        ])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=products_catalog.csv"}
    )


@router.post("/import/csv", status_code=status.HTTP_200_OK)
async def import_products_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bulk imports/updates catalog products from a CSV file upload."""
    content = await file.read()
    decoded = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(decoded))

    inserted_count = 0
    updated_count = 0

    for row in reader:
        # Check required fields
        if not row.get("name") or not row.get("sku") or not row.get("barcode"):
            continue

        sku = row["sku"].strip()
        barcode = row["barcode"].strip()

        # Check duplicate or existing SKU
        product = db.query(ProductModel).filter(
            or_(ProductModel.sku == sku, ProductModel.barcode == barcode)
        ).first()

        if product:
            # Update existing
            product.name = row.get("name", product.name)
            product.category = row.get("category", product.category)
            product.brand = row.get("brand", product.brand)
            product.variant = row.get("variant", product.variant)
            product.weight = row.get("weight", product.weight)
            product.price = float(row.get("price", product.price))
            product.description = row.get("description", product.description)
            product.qr_code = row.get("qr_code", product.qr_code)
            product.unit = row.get("unit", product.unit)
            product.dimensions = row.get("dimensions", product.dimensions)
            product.cost_price = float(row.get("cost_price", product.cost_price or 0))
            product.tax = float(row.get("tax", product.tax or 0))
            product.shelf_life = int(row["shelf_life"]) if row.get("shelf_life") else product.shelf_life
            product.expiry_tracking = row.get("expiry_tracking", "false").lower() == "true"
            product.status = row.get("status", product.status)
            product.yolo_class_mapping = int(row["yolo_class_mapping"]) if row.get("yolo_class_mapping") else product.yolo_class_mapping
            product.ocr_reference_text = row.get("ocr_reference_text", product.ocr_reference_text)
            product.confidence_threshold = float(row.get("confidence_threshold", product.confidence_threshold or 0.5))
            product.aliases = row.get("aliases", product.aliases)
            updated_count += 1
        else:
            # Create new
            product = ProductModel(
                name=row["name"],
                sku=sku,
                barcode=barcode,
                category=row.get("category", "Uncategorized"),
                brand=row.get("brand"),
                variant=row.get("variant"),
                weight=row.get("weight"),
                price=float(row.get("price", 0.00)),
                description=row.get("description"),
                qr_code=row.get("qr_code"),
                unit=row.get("unit"),
                dimensions=row.get("dimensions"),
                cost_price=float(row.get("cost_price", 0.00)),
                tax=float(row.get("tax", 0.00)),
                shelf_life=int(row["shelf_life"]) if row.get("shelf_life") else None,
                expiry_tracking=row.get("expiry_tracking", "false").lower() == "true",
                status=row.get("status", "active"),
                yolo_class_mapping=int(row["yolo_class_mapping"]) if row.get("yolo_class_mapping") else None,
                ocr_reference_text=row.get("ocr_reference_text"),
                confidence_threshold=float(row.get("confidence_threshold", 0.5)),
                aliases=row.get("aliases")
            )
            db.add(product)
            inserted_count += 1

    db.commit()
    return {
        "success": True,
        "inserted": inserted_count,
        "updated": updated_count,
        "message": f"Successfully processed CSV. Inserted: {inserted_count}, Updated: {updated_count}."
    }
