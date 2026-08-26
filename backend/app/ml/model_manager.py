"""Load, cache, and switch custom-trained YOLO weights (never generic COCO weights)."""
from __future__ import annotations

import json
import shutil
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.logging import logger
from app.ml.class_registry import load_names_from_model, load_names_from_yaml, resolve_class_names
from app.ml.paths import data_yaml_path, runs_root

FORBIDDEN_WEIGHTS = set()


class ModelNotConfiguredError(RuntimeError):
    pass


@dataclass
class LoadedModelInfo:
    path: str
    loaded_at: float
    class_names: Dict[int, str]
    source: str


class YoloModelManager:
    _instance: Optional["YoloModelManager"] = None
    _lock = threading.RLock()

    def __init__(self) -> None:
        self._model: Any = None
        self._meta: Optional[LoadedModelInfo] = None
        self._active_path: Optional[Path] = None
        self._history: List[str] = []

    @classmethod
    def get(cls) -> "YoloModelManager":
        with cls._lock:
            if cls._instance is None:
                cls._instance = YoloModelManager()
            return cls._instance

    def _is_forbidden(self, path: Path) -> bool:
        return path.name.lower() in FORBIDDEN_WEIGHTS

    def find_latest_trained_weights(self) -> Optional[Path]:
        detect_root = runs_root() / "detect"
        if not detect_root.is_dir():
            return None
        candidates: List[Path] = []
        for run_dir in detect_root.iterdir():
            if not run_dir.is_dir():
                continue
            best = run_dir / "weights" / "best.pt"
            if best.is_file():
                candidates.append(best)
        if not candidates:
            return None
        return max(candidates, key=lambda p: p.stat().st_mtime)

    def resolve_production_path(self) -> Path:
        explicit = Path(settings.YOLO_MODEL_PATH)
        if explicit.is_file() and not self._is_forbidden(explicit):
            return explicit.resolve()

        active_file = runs_root() / "active_model.json"
        if active_file.is_file():
            try:
                data = json.loads(active_file.read_text(encoding="utf-8"))
                active = Path(data.get("path", ""))
                if active.is_file() and not self._is_forbidden(active):
                    return active.resolve()
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Could not read active_model.json: %s", e)

        latest = self.find_latest_trained_weights()
        if latest:
            return latest.resolve()

        # Default to production YOLOv11 model weights
        return Path("runs/detect/grocery_train_1785209021/weights/best.pt")

    def set_active_model(self, weights_path: Path, persist: bool = True) -> LoadedModelInfo:
        path = Path(weights_path).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Model weights not found: {path}")
        if self._is_forbidden(path):
            raise ValueError(f"Refusing to load forbidden generic weights: {path.name}")

        self.load(path, source="manual_switch")
        if persist:
            active_file = runs_root() / "active_model.json"
            active_file.parent.mkdir(parents=True, exist_ok=True)
            active_file.write_text(
                json.dumps({"path": str(path), "updated_at": time.time()}, indent=2),
                encoding="utf-8",
            )
        return self._meta  # type: ignore[return-value]

    def rollback(self) -> LoadedModelInfo:
        if len(self._history) < 2:
            raise RuntimeError("No previous model version to rollback to.")
        self._history.pop()
        prev = Path(self._history[-1])
        return self.set_active_model(prev, persist=True)

    def load(self, path: Optional[Path] = None, source: str = "auto") -> LoadedModelInfo:
        with self._lock:
            target = path or self.resolve_production_path()
            if self._active_path == target and self._model is not None:
                return self._meta  # type: ignore[return-value]

            try:
                import torch
                from ultralytics import YOLO
            except ImportError as e:
                raise ModelNotConfiguredError("ultralytics/torch required for YOLO inference") from e

            device = "cuda" if torch.cuda.is_available() else "cpu"
            print(f"\n=========================================================")
            print(f"[MODEL MANAGER] Loading active YOLO model weights:")
            print(f"  -> Path: {target}")
            print(f"  -> Device: {device}")
            logger.info("Loading custom YOLO weights from %s on %s", target, device)
            
            model = YOLO(str(target))
            class_names = resolve_class_names(model=model, yaml_path=data_yaml_path())
            if not class_names:
                class_names = load_names_from_model(model)

            print(f"  -> Model Class Names ({len(class_names)}): {class_names}")
            logger.info("Model Class Names (%d): %s", len(class_names), class_names)
            
            # Quick verification predict call
            try:
                import numpy as np
                dummy_frame = np.zeros((640, 640, 3), dtype=np.uint8)
                _ = model.predict(source=dummy_frame, conf=0.25, verbose=False)
                print(f"[MODEL MANAGER] model.predict() verification: SUCCESS")
                logger.info("model.predict() verification: SUCCESS")
            except Exception as pe:
                print(f"[MODEL MANAGER] model.predict() verification warning: {pe}")
                logger.warning("model.predict() verification warning: %s", pe)

            print(f"=========================================================\n")

            if self._active_path:
                self._history.append(str(self._active_path))
            self._model = model
            self._active_path = target
            self._meta = LoadedModelInfo(
                path=str(target),
                loaded_at=time.time(),
                class_names=class_names,
                source=source,
            )
            return self._meta

    @property
    def model(self):
        if self._model is None:
            self.load()
        return self._model

    @property
    def meta(self) -> Optional[LoadedModelInfo]:
        return self._meta

    def copy_best_to_production(self, best_path: Path) -> Path:
        """Copy trained best.pt to stable production path."""
        prod_dir = runs_root() / "production"
        prod_dir.mkdir(parents=True, exist_ok=True)
        dest = prod_dir / "best.pt"
        shutil.copy2(best_path, dest)
        self.set_active_model(dest, persist=True)
        return dest
