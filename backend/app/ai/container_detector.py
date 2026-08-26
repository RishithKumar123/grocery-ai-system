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


class ContainerDetector:
    """
    Generic Product Container Detector for Product Verification System.
    
    This detector uses YOLOv11 to identify generic product containers/objects
    rather than specific product classifications. It detects:
    - Product (generic product shape)
    - Bottle (bottles, jars)
    - Can (cans, tins)
    - Box (boxes, cartons)
    - Pouch (pouches, sachets)
    - Packet (packets)
    - Bag (bags)
    - Carton (cartons)
    - Container (generic container)
    
    The actual product identification is done via:
    1. Barcode scanning (highest priority)
    2. OCR text matching
    3. Visual embedding similarity
    """
    
    # Generic container classes for YOLO training
    CONTAINER_CLASSES = [
        "product",    # Generic product shape
        "bottle",     # Bottles, jars
        "can",        # Cans, tins
        "jar",        # Jars
        "box",        # Boxes, cartons
        "pouch",      # Pouches, sachets
        "packet",     # Packets
        "bag",        # Bags
        "carton",     # Cartons
        "container"   # Generic container
    ]
    
    def __init__(self):
        self.model_path = settings.YOLO_MODEL_PATH
        self.model = None
        self.device = "cpu"
        
        if HAS_ULTRALYTICS:
            # Detect GPU availability
            if torch.cuda.is_available():
                self.device = "cuda"
                logger.info("ContainerDetector: GPU (CUDA) detected! Running on GPU.")
            else:
                self.device = "cpu"
                logger.info("ContainerDetector: GPU not available. Running on CPU.")
            
            # Load model - prefer generic pretrained model for container detection
            # For production, this should be trained on container classes
            try:
                if os.path.exists(self.model_path):
                    self.model = YOLO(self.model_path)
                    logger.info(f"ContainerDetector: Model loaded from custom path: {self.model_path}")
                else:
                    # Use pretrained YOLOv11 for generic object detection
                    # This will detect common objects which we can filter for containers
                    logger.info("ContainerDetector: Loading pretrained yolo11n.pt for generic detection...")
                    self.model = YOLO("yolo11n.pt")
                    logger.info("ContainerDetector: Pretrained weights loaded successfully.")
            except Exception as e:
                logger.error(f"ContainerDetector: Error loading YOLO model: {str(e)}")
        else:
            logger.info("ContainerDetector: YOLO model not loaded (missing packages).")
    
    def detect_containers(
        self, 
        image_bytes: bytes, 
        conf_threshold: float = 0.20,
        iou_threshold: float = 0.70
    ) -> List[Dict[str, Any]]:
        """
        Detect product containers in the image.
        
        Returns list of detections with:
        - box: [xmin, ymin, xmax, ymax]
        - confidence: float
        - container_type: str (product, bottle, can, etc.)
        - class_id: int
        """
        if self.model is None:
            logger.error("ContainerDetector: Model not loaded")
            return []
        
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                logger.error("ContainerDetector: Failed to decode image")
                return []
            
            # Run YOLO inference
            results = self.model(
                img, 
                device=self.device, 
                verbose=False,
                conf=conf_threshold,
                iou=iou_threshold,
                max_det=300
            )
            
            detections = []
            for r in results:
                for box in r.boxes:
                    coords = box.xyxy[0].tolist()
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    raw_label = self.model.names[cls].lower()
                    
                    # Map detected class to our container types
                    container_type = self._map_to_container_type(raw_label)
                    
                    # Only include detections that match our container types
                    if container_type:
                        detections.append({
                            "box": [int(x) for x in coords],
                            "confidence": round(conf, 2),
                            "container_type": container_type,
                            "class_id": cls,
                            "raw_label": raw_label
                        })
            
            # If YOLO returned 0 or 1 box on complex or non-COCO package layouts, extract contour proposals
            if len(detections) <= 1:
                img_h, img_w, _ = img.shape
                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                blurred = cv2.GaussianBlur(gray, (5, 5), 0)
                edged = cv2.Canny(blurred, 30, 150)
                contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                min_area = (img_h * img_w) * 0.015
                max_area = (img_h * img_w) * 0.90
                
                contour_boxes = []
                for c in contours:
                    area = cv2.contourArea(c)
                    if min_area <= area <= max_area:
                        x, y, w, h = cv2.boundingRect(c)
                        contour_boxes.append({
                            "box": [int(x), int(y), int(x + w), int(y + h)],
                            "confidence": 0.75,
                            "container_type": "product",
                            "class_id": 0,
                            "raw_label": "product"
                        })
                
                if contour_boxes:
                    detections = contour_boxes
                    logger.info(f"ContainerDetector: Fallback contour proposals generated {len(detections)} candidate boxes")

            logger.info(f"ContainerDetector: Detected {len(detections)} containers")
            return detections
            
        except Exception as e:
            logger.error(f"ContainerDetector: Error during inference: {str(e)}")
            return []
    
    def _map_to_container_type(self, label: str) -> str:
        """
        Map YOLO class labels to our container types.
        
        For pretrained YOLO, we map common objects to container types:
        - bottle, cup, wine glass -> bottle
        - person, cell phone, etc. -> None (not containers)
        - etc.
        """
        label_lower = label.lower()
        
        # Direct matches
        if label_lower in self.CONTAINER_CLASSES:
            return label_lower
        
        # Map common YOLO classes to container types
        container_mappings = {
            "bottle": "bottle",
            "cup": "bottle",
            "wine glass": "bottle",
            "wine glass": "bottle",
            "can": "can",
            "box": "box",
            "carton": "carton",
            "bag": "bag",
            "handbag": "bag",
            "suitcase": "bag",
            "backpack": "bag",
            "jar": "jar",
            "pouch": "pouch",
            "packet": "packet",
        }
        
        for yolo_class, container_type in container_mappings.items():
            if yolo_class in label_lower:
                return container_type
        
        # Default to generic product if it could be a container
        # Exclude non-container objects
        non_containers = [
            "person", "car", "truck", "bus", "motorcycle", "bicycle",
            "dog", "cat", "bird", "horse", "sheep", "cow",
            "cell phone", "laptop", "keyboard", "mouse", "remote",
            "chair", "couch", "bed", "dining table",
            "toilet", "sink", "bathtub"
        ]
        
        if any(nc in label_lower for nc in non_containers):
            return None
        
        # If unknown but not clearly a non-container, treat as generic product
        return "product"
    
    def crop_detections(
        self, 
        image_bytes: bytes, 
        detections: List[Dict[str, Any]]
    ) -> List[np.ndarray]:
        """
        Crop image regions for each detection.
        
        Returns list of cropped images as numpy arrays.
        """
        if not detections:
            return []
        
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return []
        
        cropped_images = []
        for det in detections:
            box = det["box"]
            xmin, ymin, xmax, ymax = box
            
            # Ensure coordinates are within image bounds
            h, w = img.shape[:2]
            xmin = max(0, xmin)
            ymin = max(0, ymin)
            xmax = min(w, xmax)
            ymax = min(h, ymax)
            
            if xmax > xmin and ymax > ymin:
                cropped = img[ymin:ymax, xmin:xmax]
                cropped_images.append(cropped)
            else:
                logger.warning(f"ContainerDetector: Invalid bounding box {box}")
        
        return cropped_images
