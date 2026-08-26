import os
import cv2
import numpy as np
from typing import List, Dict, Any
from app.core.config import settings
from app.core.logging import logger

try:
    import torch
    from ultralytics import YOLO
    HAS_ULTRALYTICS = True
except ImportError:
    HAS_ULTRALYTICS = False
    logger.warning("ultralytics or torch package is missing or not installed.")


class ObjectDetector:
    """
    DEPRECATED: Use GroceryInferenceEngine from app.ml.inference_engine instead.
    
    This class is maintained for backward compatibility only.
    The new GroceryInferenceEngine:
    - Blocks generic pretrained weights (yolo11n.pt, etc.)
    - Loads custom-trained grocery models only
    - Integrates with product catalog for proper class mapping
    - Handles unknown products with confidence thresholds
    """
    def __init__(self):
        logger.warning("ObjectDetector is deprecated. Use GroceryInferenceEngine from app.ml.inference_engine instead.")
        self.model_path = settings.YOLO_MODEL_PATH
        self.model = None
        self.device = "cpu"

        if HAS_ULTRALYTICS:
            # Detect GPU availability
            if torch.cuda.is_available():
                self.device = "cuda"
                logger.info("YOLOv11: GPU (CUDA) detected! Running on GPU.")
            else:
                self.device = "cpu"
                logger.info("YOLOv11: GPU not available. Running on CPU.")

            # Load custom weights only - NO fallback to generic pretrained models
            try:
                if os.path.exists(self.model_path):
                    self.model = YOLO(self.model_path)
                    logger.info(f"YOLOv11 model loaded from custom path: {self.model_path}")
                else:
                    # Try to find latest trained model
                    from app.ml.model_manager import YoloModelManager
                    manager = YoloModelManager.get()
                    try:
                        model_info = manager.load()
                        self.model = manager.model
                        logger.info(f"Loaded latest trained model: {model_info.path}")
                    except Exception as e:
                        logger.error(f"No custom trained model found. Please train a model first. Error: {str(e)}")
                        logger.error("Generic pretrained weights (yolo11n.pt) are blocked in production.")
            except Exception as e:
                logger.error(f"Error loading YOLOv11 model: {str(e)}")
                raise RuntimeError("YOLOv11 model not loaded. Train or configure custom weights first.")
        if not HAS_ULTRALYTICS:
            raise RuntimeError("ultralytics and torch are required for YOLO inference.")

    def detect(self, image_bytes: bytes, persist: bool = False) -> List[Dict[str, Any]]:
        """
        Detects grocery items using custom YOLOv11 weights.
        """
        if self.model is None:
            raise RuntimeError("YOLOv11 model not loaded. Train or configure custom weights first.")

        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if persist:
                results = self.model.track(
                    img,
                    persist=True,
                    tracker="bytetrack.yaml",
                    device=self.device,
                    verbose=False,
                )
            else:
                results = self.model(img, device=self.device, verbose=False)

            detections = []
            for r in results:
                track_ids = []
                if getattr(r.boxes, "id", None) is not None:
                    track_ids = r.boxes.id.int().cpu().tolist()

                for idx, box in enumerate(r.boxes):
                    coords = box.xyxy[0].tolist()
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    raw_label = self.model.names[cls].lower()
                    
                    track_id = track_ids[idx] if idx < len(track_ids) else None
                    category, display_label = self._map_to_grocery_categories(raw_label)
                    
                    detections.append({
                        "box": [int(x) for x in coords],
                        "confidence": round(conf, 2),
                        "label": display_label,
                        "category": category,
                        "track_id": track_id,
                    })
            return detections
        except Exception as e:
            logger.error(f"Error during YOLOv11/ByteTrack inference: {str(e)}")
            raise RuntimeError("YOLOv11 inference failed.")
    def _map_to_grocery_categories(self, label: str) -> tuple:
        """Maps standard COCO labels to target grocery shelf categories."""
        fruits = ["banana", "apple", "orange", "strawberry", "lemon"]
        vegetables = ["broccoli", "carrot", "cucumber", "tomato", "salad"]
        drinks = ["bottle", "cup", "wine glass", "glass", "can"]
        packaged_foods = ["sandwich", "pizza", "donut", "cake", "hot dog", "box", "can"]
        dairy = ["milk", "cheese", "butter", "yogurt"]

        if label in fruits:
            return "Fruits", label.capitalize()
        elif label in vegetables:
            return "Vegetables", label.capitalize()
        elif label in drinks:
            return "Drinks", f"Drink ({label.capitalize()})"
        elif label in packaged_foods:
            return "Packaged Foods", label.capitalize()
        elif label in dairy:
            return "Dairy", label.capitalize()
        else:
            return "Grocery Products", label.capitalize()

