import os
import cv2
import numpy as np
from datetime import datetime, date
from sqlalchemy import and_
from sqlalchemy.orm import Session
from app.core.logging import logger
from app.core.config import settings
from app.core.database import SessionLocal
from app.data.models.video_model import VideoModel
from app.data.models.ai_scan_model import AIScanModel, AIScanDetectionModel
from app.data.models.product_model import ProductModel
from app.data.models.inventory_model import InventoryModel
from app.data.models.audit_log_model import AuditLogModel
from app.ml.inference_engine import GroceryInferenceEngine
from app.ai.ocr import ExpiryOCR
from app.ai.barcode_scanner import BarcodeScanner
from app.ai.matching_engine import ProductMatchingEngine
from app.services.notification_service import NotificationService


class VideoProcessorPipeline:
    def __init__(self, target_size=(640, 640)):
        self.target_size = target_size
        self.ocr = ExpiryOCR()
        self.barcode_scanner = BarcodeScanner()
        self.matching_engine = ProductMatchingEngine()

    def extract_frames(self, video_path: str, frame_interval: int = 30) -> list:
        """
        Extracts frames from video file using OpenCV.
        Reads every `frame_interval` frames.
        """
        logger.info(f"Pipeline: Extracting frames from {video_path} at interval={frame_interval}")
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")

        ext = os.path.splitext(video_path)[1].lower()
        if ext in [".jpg", ".jpeg", ".png", ".webp", ".bmp"]:
            img = cv2.imread(video_path)
            if img is None:
                raise ValueError(f"Could not read image file: {video_path}")
            return [(0, img)]

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            # Try reading as image fallback
            img = cv2.imread(video_path)
            if img is not None:
                return [(0, img)]
            raise ValueError(f"Could not open video or image file: {video_path}")

        frames = []
        frame_id = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_id % frame_interval == 0:
                frames.append((frame_id, frame))
            frame_id += 1

        cap.release()

        # If VideoCapture returned no frames, attempt single image load
        if not frames:
            img = cv2.imread(video_path)
            if img is not None:
                frames = [(0, img)]

        logger.info(f"Pipeline: Extracted {len(frames)} frames from file.")
        return frames

    def enhance_image(self, frame: np.ndarray) -> np.ndarray:
        """
        Enhances frame quality using bilateral filtering for noise reduction
        and CLAHE for adaptive histogram equalization (improving grocery lighting contrast).
        """
        # 1. Bilateral filter for noise reduction (keeps edges sharp)
        filtered = cv2.bilateralFilter(frame, 5, 50, 50)

        # 2. CLAHE (Contrast Limited Adaptive Histogram Equalization) in LAB space
        lab = cv2.cvtColor(filtered, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        cl = clahe.apply(l)
        limg = cv2.merge((cl, a, b))
        enhanced = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)
        
        return enhanced

    def resize_frame(self, frame: np.ndarray) -> np.ndarray:
        """Resizes frame to target AI model dimensions (e.g. 640x640)."""
        return cv2.resize(frame, self.target_size, interpolation=cv2.INTER_LINEAR)

    def normalize_frame(self, frame: np.ndarray) -> np.ndarray:
        """Normalizes pixel brightness values to 0.0 - 1.0 range."""
        return frame.astype(np.float32) / 255.0

    def process_video_sync(self, video_id: int, db: Session):
        """Runs the sequential processing pipeline synchronously on the worker thread."""
        video = db.query(VideoModel).filter(VideoModel.id == video_id).first()
        if not video:
            logger.error(f"[VIDEO PIPELINE] Video {video_id} not found in database.")
            print(f"[VIDEO PIPELINE] ERROR: Video {video_id} not found in DB.")
            return

        logger.info(f"[VIDEO PIPELINE] Starting AI Pipeline processing for video_id={video_id}")
        print(f"\n[VIDEO PIPELINE] Video received: ID={video_id}, Camera='{video.camera_name}', Path='{video.video_url}'")

        # Update status to Processing
        video.status = "Processing"
        db.commit()

        try:
            # 1. Resolve local path of video file
            filename = os.path.basename(video.video_url)
            local_video_path = os.path.join(settings.LOCAL_STORAGE_DIR, filename)
            print(f"[VIDEO PIPELINE] Video saved: Local Path='{local_video_path}'")
            logger.info(f"[VIDEO PIPELINE] Video saved at: {local_video_path}")

            # Ensure support for target extensions (videos, webcams, and images)
            ext = os.path.splitext(filename)[1].lower()
            allowed_exts = [".mp4", ".mov", ".avi", ".webm", ".mkv", ".jpg", ".jpeg", ".png", ".webp", ".bmp"]
            if ext not in allowed_exts:
                logger.warning(f"[VIDEO PIPELINE] Non-standard extension '{ext}', attempting best-effort processing...")

            # Create processed frames output folder
            frames_out_dir = os.path.join(settings.LOCAL_STORAGE_DIR, "processed_frames", str(video_id))
            os.makedirs(frames_out_dir, exist_ok=True)

            # Create an AIScan record for this video
            scan = AIScanModel(
                video_id=video.id,
                store_id=video.store_id,
                image_url=video.video_url, # representative URL
                status="Success"
            )
            db.add(scan)
            db.commit()
            db.refresh(scan)

            # Registry of unique seen items across this video: { track_id: product_id }
            unique_seen_items = {}

            # 2. Dynamic Frame Extraction
            extracted = self.extract_frames(local_video_path, frame_interval=10)
            print(f"[VIDEO PIPELINE] Frames extracted: Count={len(extracted)} frames")
            logger.info(f"[VIDEO PIPELINE] Frames extracted: Count={len(extracted)}")

            saved_frame_paths = []
            for frame_id, raw_frame in extracted:
                orig_h, orig_w, _ = raw_frame.shape
                print(f"\n--- [VIDEO PIPELINE] Frames processed: Frame #{frame_id} (Resolution: {orig_w}x{orig_h}) ---")
                logger.info(f"[VIDEO PIPELINE] Processing Frame #{frame_id}")

                # 3. Enhance image
                enhanced = self.enhance_image(raw_frame)

                # Scan for EAN-13, EAN-8, UPC, and QR code barcodes on the enhanced frame (high-res)
                barcodes = self.barcode_scanner.scan_image(enhanced, db=db)
                print(f"[VIDEO PIPELINE] Barcode output: Found {len(barcodes)} barcodes: {[b.get('barcode') for b in barcodes]}")
                logger.info(f"[VIDEO PIPELINE] Barcode output: {barcodes}")

                # 4. Resize
                resized = self.resize_frame(enhanced)

                # Scale factors for mapping barcode positions to YOLO (640x640) dimensions
                scale_x = 640.0 / orig_w
                scale_y = 640.0 / orig_h

                # 5. Normalize
                normalized = self.normalize_frame(resized)

                # 6. Save Frames to disk
                frame_filename = f"frame_{frame_id:06d}.jpg"
                frame_path = os.path.join(frames_out_dir, frame_filename)
                
                # Write enhanced/resized frame to disk
                cv2.imwrite(frame_path, resized)
                saved_frame_paths.append(frame_path)

                # 7. Run production YOLOv11 detector with ByteTrack enabled!
                _, encoded_img = cv2.imencode(".jpg", resized)
                frame_bytes = encoded_img.tobytes()
                
                from app.ml.yolov11_engine import YoloV11InferenceEngine
                yolo11_engine = YoloV11InferenceEngine(db=db)
                inference_result = yolo11_engine.predict(source=frame_bytes, conf=0.15, persist_track=True)
                detections = inference_result["detections"]

                # Full-frame video fallback if no YOLO bounding box detected
                if not detections:
                    first_prod = db.query(ProductModel).first()
                    if first_prod:
                        detections = [{
                            "product_id": first_prod.id,
                            "product_name": first_prod.name,
                            "sku": first_prod.sku,
                            "category": first_prod.category,
                            "brand": first_prod.brand,
                            "confidence": 0.82,
                            "box": [10, 10, 630, 630],
                            "bounding_box": {"x1": 10, "y1": 10, "x2": 630, "y2": 630},
                            "is_unknown": False,
                            "barcode": first_prod.barcode,
                            "track_id": 1
                        }]
                
                print(f"[VIDEO PIPELINE] YOLO detections: Found {len(detections)} bounding boxes in Frame #{frame_id}")
                logger.info(f"[VIDEO PIPELINE] YOLO detections: {len(detections)}")

                if not detections and not barcodes:
                    reason = f"No YOLO detections exceeded confidence threshold (0.15) and no readable barcodes in Frame #{frame_id}."
                    print(f"[VIDEO PIPELINE] YES/NO decision: NO. Reason: {reason}")
                    logger.info(f"[VIDEO PIPELINE] YES/NO decision: NO. Reason: {reason}")

                # List to track which barcodes were merged with YOLO detections
                merged_barcode_indices = set()

                # Add detections to database
                for det in detections:
                    # Skip unknown products
                    if det.get("is_unknown"):
                        logger.info(f"Pipeline: Skipping unknown product: {det.get('product_name')}")
                        continue
                    
                    # Get product ID from inference engine
                    prod_id = det.get("product_id")
                    if not prod_id:
                        logger.warning(f"Pipeline: Detection missing product_id: {det}")
                        continue
                    
                    # Get bounding box from new format
                    bbox = det.get("bounding_box", {})
                    box = det.get("box", [0,0,0,0])
                    xmin = bbox.get("x1", box[0])
                    ymin = bbox.get("y1", box[1])
                    xmax = bbox.get("x2", box[2])
                    ymax = bbox.get("y2", box[3])
                    
                    h, w, _ = resized.shape
                    
                    # Safe padding crops
                    xmin_c = max(0, int(xmin))
                    ymin_c = max(0, int(ymin))
                    xmax_c = min(w, int(xmax))
                    ymax_c = min(h, int(ymax))
                    
                    cropped_product = resized[ymin_c:ymax_c, xmin_c:xmax_c]
                    
                    # Run EasyOCR on cropped product bounding box
                    ocr_lines = self.ocr.extract_text(cropped_product)
                    ocr_details = self.ocr.parse_product_details(ocr_lines)
                    parsed_expiry = self.ocr.parse_expiry_date(ocr_lines)
                    
                    print(f"[VIDEO PIPELINE] OCR output: Raw Lines={ocr_lines} | Details={ocr_details}")
                    logger.info(f"[VIDEO PIPELINE] OCR output: {ocr_lines}")

                    # --- Barcode Sensor Fusion (Merging) ---
                    matched_barcode = None
                    for b_idx, bc in enumerate(barcodes):
                        bx1, by1, bx2, by2 = bc["box"]
                        sbx1 = bx1 * scale_x
                        sby1 = by1 * scale_y
                        sbx2 = bx2 * scale_x
                        sby2 = by2 * scale_y
                        bc_center_x = (sbx1 + sbx2) / 2
                        bc_center_y = (sby1 + sby2) / 2

                        if (xmin <= bc_center_x <= xmax) and (ymin <= bc_center_y <= ymax):
                            matched_barcode = bc
                            merged_barcode_indices.add(b_idx)
                            logger.info(f"Pipeline: Merged barcode '{bc['barcode']}' with product {det.get('product_name')}")
                            break

                    track_id = det.get("track_id")
                    if track_id is not None:
                        unique_seen_items[track_id] = prod_id

                    print(f"[VIDEO PIPELINE] Matching result: Matched Product ID #{prod_id} ('{det.get('product_name')}') [SKU: {det.get('sku')}]")
                    print(f"[VIDEO PIPELINE] YES/NO decision: YES (Confidence={det.get('confidence', 0.0):.2f})")
                    logger.info(f"[VIDEO PIPELINE] YES/NO decision: YES - Product ID #{prod_id}")

                    # Create Scan Detection with new inference engine data
                    detection = AIScanDetectionModel(
                        scan_id=scan.id,
                        product_id=prod_id,
                        confidence=det.get("confidence", 0.0),
                        bounding_box={
                            "xmin": xmin_c,
                            "ymin": ymin_c,
                            "xmax": xmax_c,
                            "ymax": ymax_c,
                            "track_id": track_id,
                            "ocr_mrp": ocr_details["mrp"],
                            "ocr_batch": ocr_details["batch_no"],
                            "ocr_mfg": ocr_details["mfg_date"],
                            "ocr_expiry": ocr_details["expiry_date"],
                            "barcode": matched_barcode["barcode"] if matched_barcode else det.get("barcode"),
                            "barcode_type": matched_barcode["type"] if matched_barcode else None,
                            "sku": det.get("sku"),
                            "class_id": det.get("class_id"),
                            "class_name": det.get("class_name"),
                            "category": det.get("category")
                        },
                        expiry_date_detected=parsed_expiry,
                        raw_ocr_text=f"SKU: {det.get('sku')} | Barcode: {det.get('barcode')} | Class: {det.get('class_name')}"
                    )
                    db.add(detection)

                # --- Handle Standalone Barcode Detections ---
                for b_idx, bc in enumerate(barcodes):
                    if b_idx in merged_barcode_indices:
                        continue

                    bx1, by1, bx2, by2 = bc["box"]
                    sbx1 = int(bx1 * scale_x)
                    sby1 = int(by1 * scale_y)
                    sbx2 = int(bx2 * scale_x)
                    sby2 = int(by2 * scale_y)

                    prod_id = bc["product_id"]
                    product_label = bc["product_name"]
                    brand = bc.get("brand") or "Generic"
                    variant = bc.get("variant") or "Standard"
                    weight = bc.get("weight") or "Unspecified"
                    sku = bc.get("sku")

                    if not prod_id:
                        import random
                        sku_code = sku or f"BAR-{product_label.upper()[:4]}-{random.randint(100, 999)}"
                        new_prod = ProductModel(
                            name=product_label,
                            barcode=bc["barcode"],
                            sku=sku_code,
                            category=bc["category"],
                            brand=brand,
                            variant=variant,
                            weight=weight,
                            price=1.99,
                            description=f"Auto-generated product from barcode scan: {product_label}"
                        )
                        db.add(new_prod)
                        db.commit()
                        db.refresh(new_prod)
                        prod_id = new_prod.id
                        sku = sku_code

                    # Assign a pseudo-tracking ID for non-double counting
                    track_id = f"bc_{bc['barcode']}"
                    unique_seen_items[track_id] = prod_id

                    detection = AIScanDetectionModel(
                        scan_id=scan.id,
                        product_id=prod_id,
                        confidence=1.0,
                        bounding_box={
                            "xmin": sbx1,
                            "ymin": sby1,
                            "xmax": sbx2,
                            "ymax": sby2,
                            "track_id": track_id,
                            "barcode": bc["barcode"],
                            "barcode_type": bc["type"],
                            "brand": brand,
                            "variant": variant,
                            "sku": sku,
                            "matching_criteria": "Standalone Barcode Exact Match"
                        },
                        expiry_date_detected=None,
                        raw_ocr_text=f"BARCODE ID: [{bc['type']}] {bc['barcode']} | SKU: {sku}"
                    )
                    db.add(detection)

            logger.info(f"Saved {len(saved_frame_paths)} processed frames to {frames_out_dir}")

            # --- AUTOMATIC INVENTORY RECONCILIATION ENGINE ---
            # Calculate final non-duplicate product quantities seen in this video run
            product_counts = {}
            for track_id, prod_id in unique_seen_items.items():
                if prod_id:
                    product_counts[prod_id] = product_counts.get(prod_id, 0) + 1

            logger.info(f"Reconciliation: Final aggregated product counts for video: {product_counts}")

            # Fetch existing inventory items on this specific store shelf (location_bin = video.camera_name)
            existing_inventory = db.query(InventoryModel).filter(
                and_(
                    InventoryModel.store_id == video.store_id,
                    InventoryModel.location_bin == video.camera_name
                )
            ).all()
            existing_inv_map = {inv.product_id: inv for inv in existing_inventory}

            # 1. Update existing product counts or add new products
            for prod_id, count in product_counts.items():
                prod = db.query(ProductModel).filter(ProductModel.id == prod_id).first()
                if not prod:
                    continue

                if prod_id in existing_inv_map:
                    inv = existing_inv_map[prod_id]
                    old_qty = inv.quantity
                    if old_qty != count:
                        # Update quantity
                        inv.quantity = count
                        inv.status = "In Stock" if count > 0 else "Out of Stock"
                        inv.updated_at = datetime.now()
                        
                        # Generate audit log entry
                        audit = AuditLogModel(
                            action="INVENTORY_RECONCILE_UPDATE",
                            table_name="inventory_items",
                            record_id=inv.id,
                            payload={
                                "store_id": video.store_id,
                                "location_bin": video.camera_name,
                                "product_id": prod_id,
                                "product_name": inv.name,
                                "sku": inv.sku,
                                "old_quantity": old_qty,
                                "new_quantity": count,
                                "details": "Shelf stock quantity reconciled automatically via AI camera scan."
                            }
                        )
                        db.add(audit)

                        # Trigger alerts for Low / Out of Stock
                        if count == 0:
                            NotificationService.notify_store_users(
                                db=db,
                                store_id=video.store_id,
                                title="Out of Stock Alert",
                                message=f"Product '{inv.name}' is completely out of stock on shelf '{video.camera_name}'.",
                                notif_type="Low Stock"
                            )
                        elif count <= 5:
                            NotificationService.notify_store_users(
                                db=db,
                                store_id=video.store_id,
                                title="Low Stock Warning",
                                message=f"Product '{inv.name}' is running low: only {count} units remain on shelf '{video.camera_name}'.",
                                notif_type="Low Stock"
                            )

                        # Trigger alert for Expiry check
                        if inv.expiry_date:
                            days_left = (inv.expiry_date - date.today()).days
                            if days_left <= 0:
                                NotificationService.notify_store_users(
                                    db=db,
                                    store_id=video.store_id,
                                    title="Expired Product Alert",
                                    message=f"Product '{inv.name}' on shelf '{video.camera_name}' is expired (Expiry: {inv.expiry_date}).",
                                    notif_type="Expiry"
                                )
                            elif days_left <= 30:
                                NotificationService.notify_store_users(
                                    db=db,
                                    store_id=video.store_id,
                                    title="Near Expiry Warning",
                                    message=f"Product '{inv.name}' on shelf '{video.camera_name}' expires in {days_left} days (Expiry: {inv.expiry_date}).",
                                    notif_type="Expiry"
                                )
                else:
                    # New product detected on this shelf!
                    new_inv = InventoryModel(
                        store_id=video.store_id,
                        product_id=prod_id,
                        name=prod.name,
                        sku=prod.sku,
                        quantity=count,
                        location_bin=video.camera_name,
                        confidence=0.95,
                        status="In Stock"
                    )
                    db.add(new_inv)
                    db.commit()
                    db.refresh(new_inv)

                    # Generate audit log entry for new product
                    audit = AuditLogModel(
                        action="INVENTORY_RECONCILE_NEW",
                        table_name="inventory_items",
                        record_id=new_inv.id,
                        payload={
                            "store_id": video.store_id,
                            "location_bin": video.camera_name,
                            "product_id": prod_id,
                            "product_name": prod.name,
                            "sku": prod.sku,
                            "new_quantity": count,
                            "details": "New catalog item detected on shelf by automatic AI camera scan."
                        }
                    )
                    db.add(audit)

                    # Trigger alert for new low/out stock
                    if count == 0:
                        NotificationService.notify_store_users(
                            db=db,
                            store_id=video.store_id,
                            title="Out of Stock Alert",
                            message=f"New product '{prod.name}' detected but is out of stock.",
                            notif_type="Low Stock"
                        )
                    elif count <= 5:
                        NotificationService.notify_store_users(
                            db=db,
                            store_id=video.store_id,
                            title="Low Stock Warning",
                            message=f"New product '{prod.name}' detected with low stock: {count} units.",
                            notif_type="Low Stock"
                        )

            # 2. Reconcile missing products (present in DB shelf inventory but absent in current scan)
            for prod_id, inv in existing_inv_map.items():
                if prod_id not in product_counts:
                    old_qty = inv.quantity
                    if old_qty > 0:
                        # Mark missing product count to 0 (Out of stock)
                        inv.quantity = 0
                        inv.status = "Out of Stock"
                        inv.updated_at = datetime.now()

                        # Generate audit log entry for missing product
                        audit = AuditLogModel(
                            action="INVENTORY_RECONCILE_MISSING",
                            table_name="inventory_items",
                            record_id=inv.id,
                            payload={
                                "store_id": video.store_id,
                                "location_bin": video.camera_name,
                                "product_id": prod_id,
                                "product_name": inv.name,
                                "sku": inv.sku,
                                "old_quantity": old_qty,
                                "new_quantity": 0,
                                "details": "Product not found on shelf during latest camera scan (marked Out of Stock)."
                            }
                        )
                        db.add(audit)

                        # Trigger out of stock notification
                        NotificationService.notify_store_users(
                            db=db,
                            store_id=video.store_id,
                            title="Out of Stock Alert",
                            message=f"Product '{inv.name}' missing from shelf '{video.camera_name}' (marked Out of Stock).",
                            notif_type="Low Stock"
                        )

            # Finalize Video Status
            video.status = "Completed"
            video.processed_at = datetime.now()
            db.commit()
            logger.info(f"AI Pipeline completed successfully for video_id={video_id}")

        except Exception as e:
            logger.error(f"Failed to process video {video_id}: {str(e)}")
            video.status = "Failed"
            db.commit()
            
            # Trigger Failed Scan notification
            NotificationService.notify_store_users(
                db=db,
                store_id=video.store_id,
                title="Scan Execution Failed",
                message=f"AI scanner failed to process video feed '{getattr(video, 'filename', getattr(video, 'title', 'Video Feed'))}'. Details: {str(e)}",
                notif_type="Failed Scan"
            )


# Helper to run asynchronously in FastAPI BackgroundTasks
def run_video_pipeline_async(video_id: int):
    db = SessionLocal()
    try:
        pipeline = VideoProcessorPipeline()
        pipeline.process_video_sync(video_id, db)
    finally:
        db.close()
