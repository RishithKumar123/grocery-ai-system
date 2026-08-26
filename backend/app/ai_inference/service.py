import hashlib
import threading
import time
from typing import Optional, Dict, Any, List
from pathlib import Path
from app.ai_inference import repository
from app.presentation.api.v1.auth import get_current_user
from app.data.repositories.sqlalchemy_model_registry_repository import SQLAlchemyModelRegistryRepository
from app.core.database import get_db


class ModelLoadError(Exception):
    pass


class AIInferenceService:
    """Service responsible for loading approved models and running inference.

    This is a simplified but production-oriented scaffold. Concrete model-specific
    code (YOLOv11 loader) is isolated so it can be replaced with framework APIs.
    """

    def __init__(self, db_session):
        self.db = db_session
        self.repo = repository.SQLAlchemyInferenceRepository(self.db)
        self.registry = SQLAlchemyModelRegistryRepository(self.db)
        self._model = None
        self._model_meta: Optional[Dict[str, Any]] = None
        self._lock = threading.RLock()

    def _checksum(self, path: Path) -> str:
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    def load_latest_production(self):
        # Query model registry for approved production model
        model_rec = self.registry.get_latest_production_model()
        if not model_rec:
            raise ModelLoadError("No approved production model available")

        model_path = Path(model_rec.storage_path)
        expected_checksum = getattr(model_rec, "checksum", None)
        if expected_checksum:
            actual = self._checksum(model_path)
            if actual != expected_checksum:
                raise ModelLoadError("Model checksum mismatch")

        # Model loader - try ultralytics YOLO, fallback to torch
        try:
            from ultralytics import YOLO
            model = YOLO(str(model_path))
        except Exception as e:
            # Keep a clear error message; in production we would support multiple backends
            raise ModelLoadError(f"Failed to load model: {e}")

        with self._lock:
            self._model = model
            self._model_meta = {"id": model_rec.id, "version": model_rec.version}

        return self._model_meta

    def hot_swap_model(self, model_id: int):
        # Load given model by id from registry and replace current model
        model_rec = self.registry.get_model_by_id(model_id)
        if not model_rec:
            raise ModelLoadError("Model id not found in registry")
        path = Path(model_rec.storage_path)
        if getattr(model_rec, "checksum", None) and self._checksum(path) != model_rec.checksum:
            raise ModelLoadError("Checksum mismatch for requested model")
        try:
            from ultralytics import YOLO
            model = YOLO(str(path))
        except Exception as e:
            raise ModelLoadError(f"Failed to load model: {e}")

        with self._lock:
            self._model = model
            self._model_meta = {"id": model_rec.id, "version": model_rec.version}

    def predict_image(self, image_path: str, conf_thres: float = 0.25, iou_thres: float = 0.45) -> List[Dict[str, Any]]:
        if not self._model:
            self.load_latest_production()

        start = time.time()
        # ultralytics YOLO returns results with boxes and probs
        results = self._model.predict(source=image_path, conf=conf_thres, iou=iou_thres)
        # Flatten detections
        detections = []
        for r in results:
            boxes = getattr(r, 'boxes', None)
            if boxes is None:
                continue
            for b in boxes:
                xyxy = b.xyxy.tolist()[0] if hasattr(b.xyxy, 'tolist') else list(b.xyxy)
                conf = float(b.conf) if hasattr(b, 'conf') else float(b.confidence)
                cls = int(b.cls) if hasattr(b, 'cls') else int(b.class_id)
                name = self._model.names[cls] if hasattr(self._model, 'names') else str(cls)
                detections.append({
                    "bbox": {"x1": float(xyxy[0]), "y1": float(xyxy[1]), "x2": float(xyxy[2]), "y2": float(xyxy[3])},
                    "confidence": conf,
                    "class_id": cls,
                    "class_name": name,
                })
        end = time.time()
        return {"detections": detections, "inference_time_ms": int((end - start) * 1000), "model_meta": self._model_meta}
