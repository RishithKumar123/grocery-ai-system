"""Production-Ready Enterprise YOLOv11 Engine for Grocery Product Detection."""
from __future__ import annotations

import time
import os
import threading
import numpy as np
import cv2
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger
from app.ml.class_registry import resolve_product_for_detection

try:
    import torch
    from ultralytics import YOLO
    HAS_YOLO = True
except ImportError:
    HAS_YOLO = False
    logger.warning("PyTorch or Ultralytics package is missing or not installed.")

UNKNOWN_PRODUCT_NAME = "Unknown Product"


class YoloV11InferenceEngine:
    """Production YOLOv11 Inference Engine with Singleton Pattern, Telemetry Logging, and Custom Weights Enforcement."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, db: Optional[Session] = None):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, db: Optional[Session] = None) -> None:
        if not hasattr(self, "initialized"):
            self.db = db
            self.device = "cuda" if HAS_YOLO and torch.cuda.is_available() else "cpu"
            self.model = None
            self.load_model()
            self.initialized = True

    def load_model(self) -> None:
        """Load custom YOLOv11 grocery model weights into memory (Singleton loading)."""
        if HAS_YOLO and self.model is None:
            weights_candidates = [
                Path("backend/models/production/production_best.pt").resolve(),
                Path("models/production/production_best.pt").resolve(),
                Path("backend/models/best.pt").resolve(),
                Path("models/best.pt").resolve(),
                Path(settings.YOLO_MODEL_PATH).resolve(),
            ]

            selected_path = None
            for cand in weights_candidates:
                if cand.is_file():
                    selected_path = cand
                    break

            if not selected_path:
                raise FileNotFoundError("Custom grocery model not found.")

            try:
                gpu_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU Fallback"
                logger.info(f"Initializing Enterprise YOLOv11 Production Engine on {self.device} ({gpu_name})...")
                
                self.model = YOLO(str(selected_path))
                self.model.to(self.device)

                # Telemetry Audit
                file_size_mb = round(selected_path.stat().st_size / (1024 * 1024), 2)
                names_map = getattr(self.model, "names", {})
                num_classes = len(names_map)

                logger.info("=========================================================")
                logger.info("YOLOV11 ENGINE STARTUP TELEMETRY REPORT")
                logger.info(f"  • Model Path:     {selected_path}")
                logger.info(f"  • File Size:      {file_size_mb} MB")
                logger.info(f"  • Class Count:    {num_classes}")
                logger.info(f"  • Hardware:       {gpu_name} (device={self.device})")
                logger.info("=========================================================")

                # Catalog Alignment Check
                if self.db:
                    try:
                        from app.data.models.product_model import ProductModel
                        prods = self.db.query(ProductModel).filter(ProductModel.yolo_class_mapping.isnot(None)).all()
                        for p in prods:
                            cid = int(p.yolo_class_mapping)
                            model_cls_name = names_map.get(cid)
                            if model_cls_name and model_cls_name.lower() != p.name.lower():
                                logger.warning(f"Catalog Mapping Alert: DB Class {cid} '{p.name}' vs Model Class '{model_cls_name}'")
                    except Exception as db_err:
                        logger.debug(f"Catalog alignment check skipped: {db_err}")

            except Exception as e:
                logger.error(f"Failed to load custom YOLOv11 model: {e}", exc_info=True)
                raise

    def _decode_image(self, source: Union[str, bytes, np.ndarray]) -> np.ndarray:
        if isinstance(source, np.ndarray):
            return source
        if isinstance(source, bytes):
            arr = np.frombuffer(source, np.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if img is None:
                raise ValueError("Could not decode image bytes")
            return img
        path = Path(source)
        img = cv2.imread(str(path))
        if img is None:
            raise FileNotFoundError(f"Could not read image file: {path}")
        return img

    def predict(
        self,
        source: Union[str, bytes, np.ndarray],
        conf: Optional[float] = None,
        iou: Optional[float] = None,
        persist_track: bool = False,
    ) -> Dict[str, Any]:
        """Perform high-precision product detection with ByteTrack tracking and crop routing."""
        if not self.model:
            raise RuntimeError("YOLOv11 model is not initialized.")

        conf_thres = conf if conf is not None else float(settings.YOLO_CONFIDENCE_THRESHOLD)
        iou_thres = iou if iou is not None else float(settings.YOLO_IOU_THRESHOLD)

        img = self._decode_image(source)
        img_h, img_w, _ = img.shape
        start_time = time.perf_counter()

        try:
            if persist_track:
                results = self.model.track(
                    img,
                    persist=True,
                    tracker="bytetrack.yaml",
                    conf=conf_thres,
                    iou=iou_thres,
                    max_det=300,
                    verbose=False,
                )
            else:
                results = self.model.predict(
                    source=img,
                    conf=conf_thres,
                    iou=iou_thres,
                    max_det=300,
                    verbose=False,
                )
        except Exception as e:
            logger.error(f"YOLOv11 inference execution failed: {e}", exc_info=True)
            raise

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)
        detections: List[Dict[str, Any]] = []
        product_quantities: Dict[str, int] = {}
        ocr_reader = None

        for r in results:
            track_ids: List[int] = []
            if getattr(r.boxes, "id", None) is not None:
                track_ids = r.boxes.id.int().cpu().tolist()

            model_names = getattr(r, "names", {}) or getattr(self.model, "names", {})

            for idx, box in enumerate(r.boxes):
                xyxy = box.xyxy[0].tolist()
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                
                raw_name = model_names.get(class_id, str(class_id))
                x1, y1, x2, y2 = [int(v) for v in xyxy]
                bbox_coords = [x1, y1, x2, y2]

                product_name = UNKNOWN_PRODUCT_NAME
                sku = None
                barcode = None
                product_id = None
                is_unknown = True
                category = "Grocery"
                final_conf = confidence

                # 1. Primary YOLO Prediction
                if confidence >= conf_thres and self.db:
                    p_name, prod, is_unk = resolve_product_for_detection(
                        self.db, class_id, raw_name, confidence, conf_thres
                    )
                    if prod and not is_unk:
                        product_name = prod.name
                        product_id = prod.id
                        sku = prod.sku
                        barcode = prod.barcode
                        category = prod.category
                        is_unknown = False
                elif self.db:
                    # 2. Lower Confidence Fallback (OCR & Barcode Crop Verification)
                    x1_c, y1_c = max(0, x1), max(0, y1)
                    x2_c, y2_c = min(img_w, x2), min(img_h, y2)
                    crop = img[y1_c:y2_c, x1_c:x2_c]

                    # Barcode Check
                    try:
                        from app.ai.barcode_scanner import EnhancedBarcodeReader
                        bc_reader = EnhancedBarcodeReader()
                        bc_results = bc_reader.scan_image(crop, db=self.db)
                        if bc_results:
                            top_bc = bc_results[0]
                            if top_bc.get("matched_product"):
                                p_match = top_bc["matched_product"]
                                product_name = p_match.get("name", UNKNOWN_PRODUCT_NAME)
                                product_id = p_match.get("id")
                                sku = p_match.get("sku")
                                barcode = top_bc.get("barcode")
                                category = p_match.get("category", "Grocery")
                                is_unknown = False
                                final_conf = 1.0
                    except Exception as bce:
                        logger.debug(f"Crop barcode check skipped: {bce}")

                    # OCR Check if barcode didn't match
                    if is_unknown and crop.size > 0:
                        try:
                            from app.ai.ocr_engine import EasyOCREngine
                            if ocr_reader is None:
                                ocr_reader = EasyOCREngine()
                            ocr_lines = ocr_reader.extract_text(crop)
                            if ocr_lines:
                                joined_text = " ".join(ocr_lines).lower()
                                for item in catalog:
                                    item_name_clean = item.name.lower()
                                    words = [w for w in item_name_clean.split() if len(w) > 3]
                                    matching_words = [w for w in words if w in joined_text]
                                    if item_name_clean in joined_text or (len(words) > 0 and len(matching_words) / len(words) >= 0.6):
                                        product_name = item.name
                                        product_id = item.id
                                        sku = item.sku
                                        barcode = item.barcode
                                        category = item.category
                                        is_unknown = False
                                        final_conf = 0.88
                                        break
                        except Exception as ocre:
                            logger.debug(f"Crop OCR check skipped: {ocre}")

                # If product resolution failed, mark strictly as "Unknown Product"
                if is_unknown or not product_name:
                    product_name = UNKNOWN_PRODUCT_NAME

                # Count quantities
                if product_name != UNKNOWN_PRODUCT_NAME:
                    product_quantities[product_name] = product_quantities.get(product_name, 0) + 1
                    qty = product_quantities[product_name]
                else:
                    qty = 1

                detection = {
                    "product": product_name,
                    "product_name": product_name,
                    "confidence": round(final_conf * 100, 1),
                    "quantity": qty,
                    "bbox": bbox_coords,
                    "bounding_box": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                    "box": bbox_coords,
                    "class_id": class_id,
                    "class_name": raw_name,
                    "category": category,
                    "sku": sku,
                    "barcode": barcode,
                    "product_id": product_id,
                    "track_id": track_ids[idx] if idx < len(track_ids) else None,
                    "is_unknown": is_unknown,
                    "detection_time_ms": elapsed_ms,
                }
                detections.append(detection)

        logger.info(f"YOLOv11 Inference completed: {len(detections)} detections in {elapsed_ms}ms")
        
        return {
            "detections": detections,
            "inference_time_ms": elapsed_ms,
            "model_type": "YOLOv11 Custom Grocery Engine",
            "device": self.device,
        }

    def predict_image(self, source: Union[str, bytes, np.ndarray], conf: Optional[float] = None) -> Dict[str, Any]:
        """Predict products on a single image."""
        return self.predict(source, conf=conf, persist_track=False)

    def predict_video(self, source: Union[str, bytes, np.ndarray], conf: Optional[float] = None) -> Dict[str, Any]:
        """Predict products on a video frame."""
        return self.predict(source, conf=conf, persist_track=True)

    def predict_camera(self, frame: np.ndarray, conf: Optional[float] = None) -> Dict[str, Any]:
        """Predict products on a live camera frame."""
        return self.predict(frame, conf=conf, persist_track=True)

    def track_video(self, source: Union[str, bytes, np.ndarray], conf: Optional[float] = None) -> Dict[str, Any]:
        """Track products using ByteTrack across video frames."""
        return self.predict(source, conf=conf, persist_track=True)

    def batch_predict(self, sources: List[Union[str, bytes, np.ndarray]], conf: Optional[float] = None) -> List[Dict[str, Any]]:
        """Perform batch prediction across multiple image sources."""
        return [self.predict(src, conf=conf) for src in sources]

    def crop_objects(self, source: Union[str, bytes, np.ndarray], detections: List[Dict[str, Any]]) -> List[np.ndarray]:
        """Crop detected objects from an image source."""
        img = self._decode_image(source)
        img_h, img_w, _ = img.shape
        crops = []
        for d in detections:
            box = d.get("bbox") or d.get("box") or [
                d.get("bounding_box", {}).get("x1", 0),
                d.get("bounding_box", {}).get("y1", 0),
                d.get("bounding_box", {}).get("x2", img_w),
                d.get("bounding_box", {}).get("y2", img_h),
            ]
            x1, y1, x2, y2 = [int(v) for v in box]
            x1_c, y1_c = max(0, x1), max(0, y1)
            x2_c, y2_c = min(img_w, x2), min(img_h, y2)
            crops.append(img[y1_c:y2_c, x1_c:x2_c])
        return crops


# Backward-compatibility alias
GroceryInferenceEngine = YoloV11InferenceEngine
