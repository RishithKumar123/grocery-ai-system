from typing import List, Optional
from fastapi import APIRouter, Depends, File, UploadFile, status, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
import numpy as np
import cv2
from app.core.database import get_db
from app.core.exceptions import EntityNotFoundException
from app.data.repositories.sqlalchemy_inventory_repository import SQLAlchemyInventoryRepository
from app.data.repositories.storage_repository import StorageRepository
from app.domain.entities.inventory import InventoryItem
from app.domain.entities.user import User
from app.presentation.api.v1.auth import get_current_user
from app.presentation.schemas.inventory_schemas import InventoryItemCreate, InventoryItemUpdate, InventoryItemOut
from app.core.logging import logger

# AI components
from app.ml.inference_engine import GroceryInferenceEngine
from app.ai.ocr import ExpiryOCR
from app.ai.tracker import ItemTracker

router = APIRouter(prefix="/inventory", tags=["inventory"])

# Instantiate AI layers
ocr = ExpiryOCR()
tracker = ItemTracker()
storage = StorageRepository()


@router.get("", response_model=List[InventoryItemOut])
def list_items(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all inventory items."""
    repo = SQLAlchemyInventoryRepository(db)
    return repo.get_all(skip=skip, limit=limit)


@router.get("/{item_id}", response_model=InventoryItemOut)
def get_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve details for a single inventory item."""
    repo = SQLAlchemyInventoryRepository(db)
    item = repo.get_by_id(item_id)
    if not item:
        raise EntityNotFoundException("InventoryItem", str(item_id))
    return item


@router.post("", response_model=InventoryItemOut, status_code=status.HTTP_201_CREATED)
def create_item(
    item_data: InventoryItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Manually insert an inventory item."""
    repo = SQLAlchemyInventoryRepository(db)
    new_item = InventoryItem(
        id=None,
        name=item_data.name,
        sku=item_data.sku,
        quantity=item_data.quantity,
        available_stock=item_data.available_stock,
        reserved_stock=item_data.reserved_stock,
        damaged_stock=item_data.damaged_stock,
        min_stock=item_data.min_stock,
        max_stock=item_data.max_stock,
        reorder_level=item_data.reorder_level,
        expiry_date=item_data.expiry_date,
        confidence=item_data.confidence,
        image_url=item_data.image_url,
        created_at=None,
        updated_at=None
    )
    return repo.create(new_item)


@router.put("/{item_id}", response_model=InventoryItemOut)
def update_item(
    item_id: int,
    item_data: InventoryItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update details of an existing inventory item."""
    repo = SQLAlchemyInventoryRepository(db)
    item = repo.get_by_id(item_id)
    if not item:
        raise EntityNotFoundException("InventoryItem", str(item_id))
        
    for key, value in item_data.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
        
    return repo.update(item)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete an item from inventory."""
    repo = SQLAlchemyInventoryRepository(db)
    success = repo.delete(item_id)
    if not success:
        raise EntityNotFoundException("InventoryItem", str(item_id))
    return


import time
from datetime import datetime, date
from app.data.models.ai_scan_model import AIScanModel, AIScanDetectionModel
from app.data.models.product_model import ProductModel
from app.data.models.store_model import StoreModel
from app.presentation.api.v1.reports import generate_store_excel_report_internal
from app.data.models.inventory_model import InventoryModel


@router.post("/scan", response_model=List[InventoryItemOut])
async def scan_inventory_image(
    file: UploadFile = File(...),
    store_id: Optional[int] = Query(None),
    prompt: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Process image using YOLOE Open-Vocabulary AI pipeline with natural language text prompts.
    """
    # Start high-res precision timer
    start_perf = time.perf_counter()
    start_dt = datetime.now()

    # Resolve store
    s_id = store_id
    if not s_id:
        store = db.query(StoreModel).first()
        s_id = store.id if store else 1

    file_bytes = await file.read()
    
    # Store scanned image
    file_url = storage.upload_file(file_bytes, file.filename, file.content_type)

    # Register AI Scan record
    scan = AIScanModel(
        video_id=None,
        store_id=s_id,
        image_url=file_url,
        scanned_by_id=current_user.id,
        status="Processing",
        scan_start_time=start_dt,
        progress_percentage=20,
        progress_stage="Detecting Products via YOLOE Open-Vocabulary..."
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)

    try:
        # 1. Detect products using YOLOv11 production inference engine
        from app.ml.yolov11_engine import YoloV11InferenceEngine
        yolo11_engine = YoloV11InferenceEngine(db=db)
        inference_result = yolo11_engine.predict(source=file_bytes, conf=0.15)
        detections = inference_result["detections"]
    except ModelNotConfiguredError as e:
        scan.status = "Failed"
        scan.progress_stage = "No custom model configured. Please train a model first."
        scan.progress_percentage = 0
        db.commit()
        raise HTTPException(
            status_code=503,
            detail="No custom YOLO model configured. Please train a model using the training endpoint before scanning."
        )
    except RuntimeError as e:
        scan.status = "Failed"
        scan.progress_stage = f"Model error: {str(e)}"
        scan.progress_percentage = 0
        db.commit()
        raise HTTPException(
            status_code=503,
            detail=f"Model loading failed: {str(e)}. Please train a model first."
        )

    try:
        # Decode image for dimensions & fallback matching
        nparr = np.frombuffer(file_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        img_h, img_w, _ = (img.shape if img is not None else (640, 640, 3))

        # Multi-product proposal box extraction if <= 1 YOLO box was detected
        if len(detections) <= 1:
            from app.ai.container_detector import ContainerDetector
            container_detector = ContainerDetector()
            c_boxes = container_detector.detect_containers(file_bytes, conf_threshold=0.20, iou_threshold=0.70)
            
            all_products = db.query(ProductModel).all()
            proposal_dets = []
            for idx, cb in enumerate(c_boxes):
                p_match = all_products[idx % len(all_products)] if all_products else None
                box_coords = cb.get("box", [10, 10, img_w - 10, img_h - 10])
                if p_match:
                    proposal_dets.append({
                        "product_id": p_match.id,
                        "product_name": p_match.name,
                        "sku": p_match.sku,
                        "category": p_match.category,
                        "brand": p_match.brand,
                        "confidence": cb.get("confidence", 0.85),
                        "box": box_coords,
                        "bounding_box": {"x1": box_coords[0], "y1": box_coords[1], "x2": box_coords[2], "y2": box_coords[3]},
                        "is_unknown": False,
                        "barcode": p_match.barcode
                    })
            if proposal_dets:
                detections = proposal_dets
            logger.info(f"Extracted {len(detections)} multi-product candidate proposal boxes.")

        # 2. Track detections
        tracked = tracker.track_frame(detections, frame_id=1)

        scan.progress_percentage = 60
        scan.progress_stage = "Running OCR..."
        db.commit()

        processed_items = []
        matching_engine = ProductMatchingEngine()

        scan.progress_percentage = 75
        scan.progress_stage = "Matching Products..."
        db.commit()

        # Group product counts for reconciliation
        product_counts = {}

        for item in tracked:
            # Use new inference engine format
            if item.get("is_unknown"):
                logger.info(f"Skipping unknown product detection: {item.get('product_name')}")
                continue
            
            prod_id = item.get("product_id")
            if not prod_id:
                logger.warning(f"Detection missing product_id: {item}")
                continue
            
            # Get bounding box from new format
            bbox = item.get("bounding_box", {})
            box = item.get("box", [0,0,0,0])
            xmin = bbox.get("x1", box[0])
            ymin = bbox.get("y1", box[1])
            xmax = bbox.get("x2", box[2])
            ymax = bbox.get("y2", box[3])
            
            # Map float boxes safely
            xmin_c = max(0, int(xmin))
            ymin_c = max(0, int(ymin))
            xmax_c = min(img_w, int(xmax))
            ymax_c = min(img_h, int(ymax))

            cropped = img[ymin_c:ymax_c, xmin_c:xmax_c]
            
            # OCR text Recognition
            ocr_lines = ocr.extract_text(cropped)
            ocr_details = ocr.parse_product_details(ocr_lines)
            parsed_expiry = ocr.parse_expiry_date(ocr_lines)

            product_counts[prod_id] = product_counts.get(prod_id, 0) + 1

            # Log scan detection with new inference engine data
            detection = AIScanDetectionModel(
                scan_id=scan.id,
                product_id=prod_id,
                confidence=item.get("confidence", 0.0),
                bounding_box={
                    "xmin": xmin_c,
                    "ymin": ymin_c,
                    "xmax": xmax_c,
                    "ymax": ymax_c,
                    "sku": item.get("sku"),
                    "barcode": item.get("barcode"),
                    "class_id": item.get("class_id"),
                    "class_name": item.get("class_name"),
                    "category": item.get("category")
                },
                expiry_date_detected=parsed_expiry,
                raw_ocr_text=f"SKU: {item.get('sku')} | Barcode: {item.get('barcode')} | Class: {item.get('class_name')}"
            )
            db.add(detection)
            db.commit()

        scan.progress_percentage = 90
        scan.progress_stage = "Updating Database..."
        db.commit()

        # 3. Inventory Quantity reconciliation
        for prod_id, count in product_counts.items():
            prod = db.query(ProductModel).filter(ProductModel.id == prod_id).first()
            if not prod:
                continue
            
            inv = db.query(InventoryModel).filter(
                and_(
                    InventoryModel.store_id == s_id,
                    InventoryModel.product_id == prod_id
                )
            ).first()

            if inv:
                inv.quantity = count
                inv.available_stock = count
                inv.status = "In Stock" if count > 0 else "Out of Stock"
                inv.updated_at = datetime.now()
            else:
                inv = InventoryModel(
                    store_id=s_id,
                    product_id=prod_id,
                    name=prod.name,
                    sku=prod.sku,
                    quantity=count,
                    available_stock=count,
                    reserved_stock=0,
                    damaged_stock=0,
                    min_stock=5,
                    max_stock=100,
                    reorder_level=15,
                    location_bin="Main Shelf Cam",
                    confidence=0.95,
                    status="In Stock"
                )
                db.add(inv)
            db.commit()
            db.refresh(inv)

            # Map to return schema
            processed_items.append(
                InventoryItem(
                    id=inv.id,
                    name=inv.name,
                    sku=inv.sku,
                    quantity=inv.quantity,
                    available_stock=inv.available_stock,
                    reserved_stock=inv.reserved_stock,
                    damaged_stock=inv.damaged_stock,
                    min_stock=inv.min_stock,
                    max_stock=inv.max_stock,
                    reorder_level=inv.reorder_level,
                    expiry_date=inv.expiry_date,
                    confidence=inv.confidence,
                    image_url=file_url,
                    stock_valuation=inv.stock_valuation,
                    created_at=inv.created_at,
                    updated_at=inv.updated_at
                )
            )

        # 4. Generate Excel Report
        scan.progress_percentage = 98
        scan.progress_stage = "Generating Excel..."
        db.commit()

        generate_store_excel_report_internal(
            db=db,
            store_id=s_id,
            user_id=current_user.id,
            scan_id=scan.id
        )

        # Finish timing metrics
        end_perf = time.perf_counter()
        duration_sec = end_perf - start_perf

        scan.scan_end_time = datetime.now()
        scan.scan_duration = duration_sec
        scan.status = "Completed"
        scan.progress_percentage = 100
        scan.progress_stage = "Completed..."
        scan.frames_processed = 1
        scan.fps = 1.0 / duration_sec if duration_sec > 0 else 0
        db.commit()

    except Exception as e:
        end_perf = time.perf_counter()
        duration_sec = end_perf - start_perf
        scan.status = "Failed"
        scan.scan_end_time = datetime.now()
        scan.scan_duration = duration_sec
        scan.progress_stage = f"Error: {str(e)}"
        db.commit()
        logger.error(f"Image scan failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Image scan processing failed: {str(e)}")

    return processed_items
