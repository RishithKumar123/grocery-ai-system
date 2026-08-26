from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, File, UploadFile, status, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
import json
import numpy as np
import cv2
import time

from app.core.database import get_db
from app.core.logging import logger
from app.data.models.product_model import ProductModel
from app.data.models.reference_image_model import ReferenceImageModel
from app.domain.entities.user import User
from app.presentation.api.v1.auth import get_current_user
from app.ai.container_detector import ContainerDetector
from app.ai.enhanced_barcode import EnhancedBarcodeReader
from app.ai.paddle_ocr import PaddleOCREngine
from app.ai.embedding_engine import EmbeddingEngine
from app.ai.ocr_matching_engine import OCRMatchingEngine
from app.services.decision_service import DecisionEngineService
from app.data.repositories.storage_repository import StorageRepository

router = APIRouter(prefix="/verification", tags=["verification"])


# Schemas
class VerificationRequest(BaseModel):
    product_id: int
    confidence_threshold: float = 0.5


class VerificationResponse(BaseModel):
    present: bool
    confidence: float
    quantity: int
    bounding_boxes: List[Dict[str, Any]]
    boundingBoxes: List[Dict[str, Any]]
    barcode_matched: bool
    barcodeMatched: bool
    ocr_matched: bool
    ocrMatched: bool
    embedding_similarity: float
    embeddingSimilarity: float
    detection_time_ms: float
    explanation: str
    product_id: int
    product_name: str


@router.post("/verify-product", response_model=VerificationResponse)
async def verify_product(
    product_id: int,
    file: UploadFile = File(...),
    confidence_threshold: float = 0.5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Verify if a specific product is present in the uploaded image.
    
    Process:
    1. Detect product containers using YOLO
    2. Read barcodes from detected regions
    3. Extract OCR text from detected regions
    4. Generate visual embeddings
    5. Match against reference images
    6. Apply decision engine with weighted rules
    7. Return YES/NO with confidence
    """
    start_time = time.perf_counter()
    
    # Get target product
    product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Load reference embeddings for the product
    reference_images = db.query(ReferenceImageModel).filter(
        ReferenceImageModel.product_id == product_id,
        ReferenceImageModel.embedding_generated == True
    ).all()
    
    if not reference_images:
        logger.warning(f"No reference embeddings found for product {product_id}")
    
    # Read image
    file_bytes = await file.read()
    nparr = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if img is None:
        raise HTTPException(status_code=400, detail="Invalid image file")
    
    img_h, img_w, _ = img.shape

    # Initialize engines
    from app.ml.yolov11_engine import YoloV11InferenceEngine
    yolo11_engine = YoloV11InferenceEngine(db=db)
    container_detector = ContainerDetector()
    barcode_reader = EnhancedBarcodeReader()
    ocr_engine = PaddleOCREngine()
    embedding_engine = EmbeddingEngine()
    decision_engine = DecisionEngineService()
    
    # Step 1: Detect candidate product boxes via YOLOv11 Engine
    yolo11_res = yolo11_engine.predict(source=file_bytes, conf=0.15)
    
    detections = []
    for d in yolo11_res.get("detections", []):
        detections.append({
            "box": d["box"],
            "confidence": d["confidence"],
            "container_type": d.get("class_name", "product")
        })

    if not detections:
        detections = container_detector.detect_containers(file_bytes)
    
    # Full-frame fallback if no box was detected
    if not detections:
        logger.info("No YOLOE bounding box detected; applying full-frame fallback crop.")
        detections = [{
            "box": [10, 10, img_w - 10, img_h - 10],
            "confidence": 0.85,
            "container_type": "product"
        }]
    
    # Step 2: Process each detection
    matched_detections = []
    best_barcode = None
    best_ocr_text = None
    best_embedding_similarity = 0.0
    
    for detection in detections:
        box = detection["box"]
        xmin, ymin, xmax, ymax = box
        
        # Crop detection
        cropped = img[ymin:ymax, xmin:xmax]
        
        if cropped.size == 0:
            continue
        
        # Read barcode
        barcode_results = barcode_reader.read_barcodes(cropped, db)
        barcode_matched = False
        current_barcode = None
        
        for barcode_result in barcode_results:
            if barcode_result.get("product_id") == product_id:
                barcode_matched = True
                current_barcode = barcode_result.get("barcode")
                if not best_barcode:
                    best_barcode = current_barcode
                break
        
        # Extract OCR
        ocr_results = ocr_engine.extract_text(cropped)
        ocr_details = ocr_engine.parse_product_details(ocr_results)
        ocr_text = ocr_details.get("product_name")
        
        if ocr_text:
            if not best_ocr_text:
                best_ocr_text = ocr_text
        
        # Generate embedding and compare with reference
        embedding_similarity = 0.0
        if reference_images:
            query_embedding = embedding_engine.generate_embedding(cropped)
            if query_embedding is not None:
                for ref_img in reference_images:
                    ref_embedding = embedding_engine.embedding_from_json(ref_img.embedding)
                    if ref_embedding is not None:
                        similarity = embedding_engine.calculate_similarity(
                            query_embedding,
                            ref_embedding
                        )
                        if similarity > embedding_similarity:
                            embedding_similarity = similarity
        
        if embedding_similarity > best_embedding_similarity:
            best_embedding_similarity = embedding_similarity
        
        # Decision for this detection
        decision_result = decision_engine.resolve_decision(
            db=db,
            yolo_label=detection["container_type"],
            ocr_text=ocr_text,
            barcode=current_barcode,
            embedding_similarity=embedding_similarity,
            target_product_id=product_id
        )
        
        if decision_result["present"]:
            matched_detections.append({
                "box": box,
                "confidence": decision_result["confidence"],
                "barcode_matched": barcode_matched,
                "ocr_matched": decision_result["ocr_matched"],
                "embedding_similarity": embedding_similarity
            })
    
    # Step 3: Final decision
    quantity = len(matched_detections)
    present = quantity > 0
    
    # Calculate overall confidence
    overall_confidence = 0.0
    if matched_detections:
        overall_confidence = max(d["confidence"] for d in matched_detections)
    
    # Build explanation
    explanation_parts = []
    if best_barcode:
        explanation_parts.append("Barcode matched")
    if best_ocr_text:
        explanation_parts.append("OCR text matched")
    if best_embedding_similarity > 0.75:
        explanation_parts.append(f"Visual similarity: {best_embedding_similarity:.2f}")
    
    explanation = ", ".join(explanation_parts) if explanation_parts else "Low confidence match"
    
    detection_time = (time.perf_counter() - start_time) * 1000
    
    logger.info(f"Verification result for product {product_id}: Present={present}, Confidence={overall_confidence:.2f}, Quantity={quantity}")
    
    boxes = [d["box"] for d in matched_detections]
    b_match = best_barcode is not None
    o_match = best_ocr_text is not None
    e_sim = round(best_embedding_similarity, 4)

    return VerificationResponse(
        present=present,
        confidence=round(overall_confidence, 4),
        quantity=quantity,
        bounding_boxes=boxes,
        boundingBoxes=boxes,
        barcode_matched=b_match,
        barcodeMatched=b_match,
        ocr_matched=o_match,
        ocrMatched=o_match,
        embedding_similarity=e_sim,
        embeddingSimilarity=e_sim,
        detection_time_ms=round(detection_time, 2),
        explanation=explanation,
        product_id=product_id,
        product_name=product.name
    )


@router.post("/verify-by-barcode")
async def verify_by_barcode(
    barcode: str = Query(...),
    file: UploadFile = File(...),
    confidence_threshold: float = 0.5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Verify product by barcode (alternative to product_id).
    """
    # Find product by barcode
    product = db.query(ProductModel).filter(ProductModel.barcode == barcode).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product with this barcode not found")
    
    # Use the main verification endpoint
    return await verify_product(
        product_id=product.id,
        file=file,
        confidence_threshold=confidence_threshold,
        db=db,
        current_user=current_user
    )


@router.get("/products/search")
async def search_products_for_verification(
    query: str = Query(...),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search products for verification (by name, brand, SKU, barcode).
    """
    query_lower = query.lower()
    
    products = db.query(ProductModel).filter(
        (
            ProductModel.name.ilike(f"%{query_lower}%") |
            ProductModel.brand.ilike(f"%{query_lower}%") |
            ProductModel.sku.ilike(f"%{query_lower}%") |
            ProductModel.barcode.ilike(f"%{query_lower}%")
        )
    ).limit(limit).all()
    
    return {
        "query": query,
        "results": [
            {
                "id": p.id,
                "name": p.name,
                "brand": p.brand,
                "sku": p.sku,
                "barcode": p.barcode,
                "image_url": p.image_url,
                "reference_image_count": p.reference_image_count,
                "has_embeddings": p.reference_image_count > 0
            }
            for p in products
        ]
    }


@router.get("/products/{product_id}/verification-status")
async def get_product_verification_status(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check if a product is ready for verification (has reference images and embeddings).
    """
    product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    reference_images = db.query(ReferenceImageModel).filter(
        ReferenceImageModel.product_id == product_id
    ).all()
    
    embedding_count = sum(1 for img in reference_images if img.embedding_generated)
    
    return {
        "product_id": product_id,
        "product_name": product.name,
        "reference_image_count": len(reference_images),
        "embedding_count": embedding_count,
        "ready_for_verification": embedding_count > 0,
        "embedding_model_version": product.embedding_model_version,
        "recommendations": [
            "Upload at least 3 reference images" if len(reference_images) < 3 else None,
            "Ensure embeddings are generated" if embedding_count == 0 else None
        ]
    }


class InventorySyncRequest(BaseModel):
    product_id: int
    quantity: int
    store_id: int = 1


@router.post("/inventory/update")
async def update_verified_inventory(
    req: InventorySyncRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Automatically update inventory stock count and write audit logs upon successful verification.
    """
    from app.data.models.inventory_model import InventoryModel
    from app.data.models.audit_log_model import AuditLogModel
    from datetime import datetime

    product = db.query(ProductModel).filter(ProductModel.id == req.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    inv = db.query(InventoryModel).filter(
        InventoryModel.product_id == req.product_id,
        InventoryModel.store_id == req.store_id
    ).first()

    if inv:
        inv.quantity_on_hand = req.quantity
        inv.last_updated = datetime.utcnow()
    else:
        inv = InventoryModel(
            store_id=req.store_id,
            product_id=req.product_id,
            quantity_on_hand=req.quantity,
            reorder_point=10,
            target_stock_level=50,
            last_updated=datetime.utcnow()
        )
        db.add(inv)

    # Insert audit record
    audit = AuditLogModel(
        user_id=current_user.id,
        action="VERIFICATION_INVENTORY_SYNC",
        resource_type="Inventory",
        resource_id=str(req.product_id),
        details=f"Verified target presence of Product ID #{req.product_id} ('{product.name}') with quantity={req.quantity}."
    )
    db.add(audit)
    db.commit()
    db.refresh(inv)

    return {
        "success": True,
        "message": f"Successfully updated stock for {product.name} to {req.quantity} units.",
        "product_id": req.product_id,
        "product_name": product.name,
        "quantity_on_hand": inv.quantity_on_hand
    }
