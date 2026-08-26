"""Unified grocery detection inference with catalog mapping and unknown-product handling."""
from __future__ import annotations

import time
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from functools import lru_cache
import threading

import cv2
import numpy as np
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import logger, get_inference_logger, get_prediction_logger, get_unknown_product_logger, get_error_logger
from app.ml.class_registry import UNKNOWN_LABEL, resolve_product_for_detection
from app.ml.model_manager import ModelNotConfiguredError, YoloModelManager
from app.ml.paths import unknown_products_dir
from app.product_recognition.repository import SQLAlchemyProductRecognitionRepository


class GroceryInferenceEngine:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, db: Optional[Session] = None):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, db: Optional[Session] = None) -> None:
        if not hasattr(self, 'initialized'):
            self.db = db
            self.manager = YoloModelManager.get()
            self._threshold = float(settings.YOLO_CONFIDENCE_THRESHOLD)
            self._cache_enabled = True
            self._detection_cache = {}
            self._cache_ttl = 300  # 5 minutes
            self.initialized = True

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
            raise FileNotFoundError(f"Could not read image: {path}")
        return img

    def _store_unknown_crop(self, crop: np.ndarray, meta: dict) -> Optional[str]:
        try:
            out_dir = unknown_products_dir()
            ts = int(time.time() * 1000)
            out_path = out_dir / f"unknown_{ts}.jpg"
            cv2.imwrite(str(out_path), crop)
            if self.db:
                repo = SQLAlchemyProductRecognitionRepository(self.db)
                repo.create_unknown(
                    image_path=str(out_path),
                    ocr_text=meta.get("ocr_text"),
                    barcode=meta.get("barcode"),
                    yolo_class=meta.get("yolo_class"),
                    confidence=meta.get("confidence"),
                    metadata=meta,
                )
            logger.info("Stored unknown product crop at %s", out_path)
            return str(out_path)
        except Exception as e:
            logger.error("Failed to store unknown product: %s", e)
            return None

    def predict(
        self,
        source: Union[str, bytes, np.ndarray],
        conf: Optional[float] = None,
        iou: Optional[float] = None,
        persist_track: bool = False,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        inference_logger = get_inference_logger()
        prediction_logger = get_prediction_logger()
        unknown_logger = get_unknown_product_logger()
        error_logger = get_error_logger()
        
        conf_thres = conf if conf is not None else self._threshold
        iou_thres = iou if iou is not None else float(settings.YOLO_IOU_THRESHOLD)

        inference_logger.info(f"Starting inference with confidence threshold: {conf_thres}, IOU threshold: {iou_thres}")

        # Check cache for byte sources
        if use_cache and self._cache_enabled and isinstance(source, bytes):
            cache_key = hashlib.sha256(source).hexdigest()
            if cache_key in self._detection_cache:
                cached_result, cached_time = self._detection_cache[cache_key]
                if time.time() - cached_time < self._cache_ttl:
                    logger.debug(f"Cache hit for detection: {cache_key}")
                    inference_logger.debug(f"Cache hit for detection: {cache_key}")
                    return cached_result

        try:
            model = self.manager.model
        except ModelNotConfiguredError:
            error_logger.error("Model not configured for inference")
            raise

        img = self._decode_image(source)
        start = time.perf_counter()

        try:
            if persist_track:
                results = model.track(
                    img,
                    persist=True,
                    tracker="bytetrack.yaml",
                    conf=conf_thres,
                    iou=iou_thres,
                    max_det=300,
                    verbose=False,
                )
            else:
                results = model.predict(source=img, conf=conf_thres, iou=iou_thres, max_det=300, verbose=False)
        except Exception as e:
            error_logger.error(f"Model prediction failed: {str(e)}", exc_info=True)
            raise

        elapsed_ms = int((time.perf_counter() - start) * 1000)
        detections: List[Dict[str, Any]] = []

        for r in results:
            track_ids: List[int] = []
            if getattr(r.boxes, "id", None) is not None:
                track_ids = r.boxes.id.int().cpu().tolist()

            for idx, box in enumerate(r.boxes):
                xyxy = box.xyxy[0].tolist()
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                raw_name = self.manager.meta.class_names.get(class_id) if self.manager.meta else str(class_id)
                if not raw_name and hasattr(model, "names"):
                    raw_name = model.names.get(class_id, str(class_id))

                x1, y1, x2, y2 = [int(v) for v in xyxy]
                crop = img[max(0, y1) : max(0, y2), max(0, x1) : max(0, x2)]

                product_name = UNKNOWN_LABEL
                sku = None
                barcode = None
                product_id = None
                is_unknown = True
                category = "Unknown"

                if self.db:
                    product_name, prod, is_unknown = resolve_product_for_detection(
                        self.db, class_id, str(raw_name), confidence, conf_thres
                    )
                    if prod:
                        product_id = prod.id
                        sku = prod.sku
                        barcode = prod.barcode
                        category = prod.category
                elif confidence >= conf_thres:
                    product_name = str(raw_name)
                    is_unknown = False

                unknown_image_path = None
                if is_unknown and crop.size > 0:
                    unknown_image_path = self._store_unknown_crop(
                        crop,
                        {
                            "class_id": class_id,
                            "yolo_class": raw_name,
                            "confidence": confidence,
                            "bbox": [x1, y1, x2, y2],
                        },
                    )
                    unknown_logger.info(f"Unknown product detected: class_id={class_id}, class_name={raw_name}, confidence={confidence:.4f}, image_path={unknown_image_path}")

                detection = {
                    "product_name": product_name,
                    "confidence": round(confidence, 4),
                    "bounding_box": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                    "box": [x1, y1, x2, y2],
                    "class_id": class_id,
                    "class_name": str(raw_name),
                    "label": product_name,
                    "category": category,
                    "sku": sku,
                    "barcode": barcode,
                    "product_id": product_id,
                    "track_id": track_ids[idx] if idx < len(track_ids) else None,
                    "is_unknown": is_unknown,
                    "unknown_image_path": unknown_image_path,
                    "detection_time_ms": elapsed_ms,
                }
                
                # Log prediction
                prediction_logger.info(f"Detection: product_name={product_name}, confidence={confidence:.4f}, class_id={class_id}, is_unknown={is_unknown}")
                
                detections.append(detection)

        logger.info("Inference completed: %s detections in %sms", len(detections), elapsed_ms)
        inference_logger.info(f"Inference completed: {len(detections)} detections in {elapsed_ms}ms")
        
        result = {
            "detections": detections,
            "inference_time_ms": elapsed_ms,
            "model_path": self.manager.meta.path if self.manager.meta else None,
            "model_meta": self.manager.meta.__dict__ if self.manager.meta else {},
        }
        
        # Cache result for byte sources
        if use_cache and self._cache_enabled and isinstance(source, bytes):
            cache_key = hashlib.sha256(source).hexdigest()
            self._detection_cache[cache_key] = (result, time.time())
            inference_logger.debug(f"Result cached with key: {cache_key}")
            
            # Clean old cache entries
            current_time = time.time()
            self._detection_cache = {
                k: v for k, v in self._detection_cache.items()
                if current_time - v[1] < self._cache_ttl
            }
        
        return result
    
    def predict_batch(
        self,
        sources: List[Union[str, bytes, np.ndarray]],
        conf: Optional[float] = None,
        iou: Optional[float] = None,
        batch_size: int = 8,
    ) -> List[Dict[str, Any]]:
        """Batch inference for multiple images."""
        conf_thres = conf if conf is not None else self._threshold
        iou_thres = iou if iou is not None else float(settings.YOLO_IOU_THRESHOLD)

        try:
            model = self.manager.model
        except ModelNotConfiguredError:
            raise

        results = []
        for i in range(0, len(sources), batch_size):
            batch = sources[i:i + batch_size]
            batch_results = []
            
            for source in batch:
                try:
                    result = self.predict(source, conf=conf_thres, iou=iou_thres, use_cache=False)
                    batch_results.append(result)
                except Exception as e:
                    logger.error(f"Failed to process image in batch: {e}")
                    batch_results.append({
                        "detections": [],
                        "inference_time_ms": 0,
                        "error": str(e),
                    })
            
            results.extend(batch_results)
        
        logger.info(f"Batch inference completed: {len(results)} images processed")
        return results
    
    def clear_cache(self) -> None:
        """Clear the detection cache."""
        self._detection_cache.clear()
        logger.info("Detection cache cleared")
    
    def set_cache_enabled(self, enabled: bool) -> None:
        """Enable or disable caching."""
        self._cache_enabled = enabled
        logger.info(f"Detection cache {'enabled' if enabled else 'disabled'}")
