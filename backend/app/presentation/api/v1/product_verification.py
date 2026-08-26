from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, File, UploadFile, status, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
import json
import numpy as np
import cv2

from app.core.database import get_db
from app.core.logging import logger
from app.data.models.product_model import ProductModel
from app.data.models.reference_image_model import ReferenceImageModel
from app.domain.entities.user import User
from app.presentation.api.v1.auth import get_current_user
from app.ai.embedding_engine import EmbeddingEngine
from app.ai.ocr_matching_engine import OCRMatchingEngine
from app.data.repositories.storage_repository import StorageRepository

router = APIRouter(prefix="/product-verification", tags=["product-verification"])


# Schemas
class ReferenceImageUpload(BaseModel):
    product_id: int
    is_primary: bool = False


class OCRKeywordsUpdate(BaseModel):
    product_id: int
    keywords: List[str]


class AliasesUpdate(BaseModel):
    product_id: int
    aliases: List[str]


class ProductRegistrationResponse(BaseModel):
    product_id: int
    reference_image_count: int
    embeddings_generated: int
    status: str


@router.post("/register-reference-image", response_model=ProductRegistrationResponse)
async def register_reference_image(
    product_id: int,
    file: UploadFile = File(...),
    is_primary: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a reference image for a product and auto-generate embeddings.
    
    This enables the product to be verified using visual similarity matching.
    """
    # Verify product exists
    product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Read image
    file_bytes = await file.read()
    
    # Store image
    storage = StorageRepository()
    image_url = storage.upload_file(file_bytes, file.filename, file.content_type)
    
    # Decode for embedding generation
    nparr = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        raise HTTPException(status_code=400, detail="Invalid image file")
    
    # Generate embedding
    embedding_engine = EmbeddingEngine()
    embedding = embedding_engine.generate_embedding(img)
    
    # Store reference image record
    reference_image = ReferenceImageModel(
        product_id=product_id,
        image_url=image_url,
        width=img.shape[1],
        height=img.shape[0],
        file_size=len(file_bytes),
        embedding=embedding_engine.embedding_to_json(embedding) if embedding else None,
        embedding_model=embedding_engine.model_name if embedding else None,
        is_primary=is_primary,
        embedding_generated=embedding is not None,
        quality_score=0.8  # Could be calculated with image quality assessment
    )
    
    db.add(reference_image)
    
    # Update product reference count
    if product.reference_image_count is None:
        product.reference_image_count = 0
    product.reference_image_count += 1
    
    # If primary, update product image URL
    if is_primary:
        product.image_url = image_url
    
    # Update embedding model version
    if embedding:
        product.embedding_model_version = embedding_engine.model_name
    
    db.commit()
    db.refresh(reference_image)
    
    logger.info(f"Registered reference image for product {product_id}: {image_url}")
    
    return ProductRegistrationResponse(
        product_id=product_id,
        reference_image_count=product.reference_image_count,
        embeddings_generated=1 if embedding else 0,
        status="success"
    )


@router.post("/update-ocr-keywords")
async def update_ocr_keywords(
    data: OCRKeywordsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update OCR keywords for a product to improve text matching.
    
    Keywords should include brand names, product variants, and common
    text that appears on the product packaging.
    """
    product = db.query(ProductModel).filter(ProductModel.id == data.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product.ocr_keywords = json.dumps(data.keywords)
    db.commit()
    
    logger.info(f"Updated OCR keywords for product {data.product_id}: {data.keywords}")
    
    return {"status": "success", "keywords_count": len(data.keywords)}


@router.post("/update-aliases")
async def update_aliases(
    data: AliasesUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update product aliases for fuzzy matching.
    
    Aliases are alternative names the product might be recognized by.
    """
    product = db.query(ProductModel).filter(ProductModel.id == data.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product.aliases = json.dumps(data.aliases)
    db.commit()
    
    logger.info(f"Updated aliases for product {data.product_id}: {data.aliases}")
    
    return {"status": "success", "aliases_count": len(data.aliases)}


@router.get("/reference-images/{product_id}")
async def get_reference_images(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all reference images for a product.
    """
    product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    reference_images = db.query(ReferenceImageModel).filter(
        ReferenceImageModel.product_id == product_id
    ).all()
    
    return {
        "product_id": product_id,
        "reference_images": [
            {
                "id": img.id,
                "image_url": img.image_url,
                "is_primary": img.is_primary,
                "embedding_generated": img.embedding_generated,
                "quality_score": img.quality_score,
                "created_at": img.created_at
            }
            for img in reference_images
        ]
    }


@router.delete("/reference-images/{image_id}")
async def delete_reference_image(
    image_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a reference image.
    """
    reference_image = db.query(ReferenceImageModel).filter(
        ReferenceImageModel.id == image_id
    ).first()
    
    if not reference_image:
        raise HTTPException(status_code=404, detail="Reference image not found")
    
    product_id = reference_image.product_id
    
    # Update product reference count
    product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if product and product.reference_image_count > 0:
        product.reference_image_count -= 1
    
    db.delete(reference_image)
    db.commit()
    
    logger.info(f"Deleted reference image {image_id} for product {product_id}")
    
    return {"status": "success"}


@router.post("/batch-register-reference-images")
async def batch_register_reference_images(
    product_id: int,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Upload multiple reference images for a product at once.
    First image is marked as primary.
    """
    product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    embedding_engine = EmbeddingEngine()
    storage = StorageRepository()
    
    success_count = 0
    embedding_count = 0
    
    for idx, file in enumerate(files):
        try:
            file_bytes = await file.read()
            image_url = storage.upload_file(file_bytes, file.filename, file.content_type)
            
            nparr = np.frombuffer(file_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                continue
            
            embedding = embedding_engine.generate_embedding(img)
            
            reference_image = ReferenceImageModel(
                product_id=product_id,
                image_url=image_url,
                width=img.shape[1],
                height=img.shape[0],
                file_size=len(file_bytes),
                embedding=embedding_engine.embedding_to_json(embedding) if embedding else None,
                embedding_model=embedding_engine.model_name if embedding else None,
                is_primary=(idx == 0),  # First image is primary
                embedding_generated=embedding is not None,
                quality_score=0.8
            )
            
            db.add(reference_image)
            success_count += 1
            if embedding:
                embedding_count += 1
                
        except Exception as e:
            logger.error(f"Error processing image {file.filename}: {str(e)}")
            continue
    
    # Update product
    if product.reference_image_count is None:
        product.reference_image_count = 0
    product.reference_image_count += success_count
    
    if success_count > 0:
        product.embedding_model_version = embedding_engine.model_name
    
    db.commit()
    
    logger.info(f"Batch registered {success_count} reference images for product {product_id}")
    
    return ProductRegistrationResponse(
        product_id=product_id,
        reference_image_count=product.reference_image_count,
        embeddings_generated=embedding_count,
        status="success"
    )


@router.get("/search-products")
async def search_products(
    keywords: str = Query(...),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search products by keywords (for product selection in verification).
    """
    ocr_engine = OCRMatchingEngine()
    products = ocr_engine.search_products_by_keywords(keywords, db, limit)
    
    return {
        "keywords": keywords,
        "results": [
            {
                "id": p.id,
                "name": p.name,
                "brand": p.brand,
                "sku": p.sku,
                "barcode": p.barcode,
                "image_url": p.image_url,
                "reference_image_count": p.reference_image_count
            }
            for p in products
        ]
    }
