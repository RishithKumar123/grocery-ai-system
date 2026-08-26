"""YOLOv11 training orchestration for custom grocery detection."""
from __future__ import annotations

import csv
import json
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.logging import logger, get_training_logger, get_error_logger
from app.ml.dataset_validator import validate_dataset
from app.ml.model_manager import YoloModelManager
from app.ml.paths import data_yaml_path, runs_root


@dataclass
class TrainingJob:
    job_id: str
    status: str = "queued"
    config: Dict[str, Any] = field(default_factory=dict)
    run_dir: Optional[str] = None
    best_weights: Optional[str] = None
    last_weights: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    started_at: Optional[float] = None
    finished_at: Optional[float] = None


class TrainingJobStore:
    _jobs: Dict[str, TrainingJob] = {}
    _lock = threading.Lock()

    @classmethod
    def create(cls, config: Dict[str, Any]) -> TrainingJob:
        job = TrainingJob(job_id=str(uuid.uuid4()), config=config)
        with cls._lock:
            cls._jobs[job.job_id] = job
        return job

    @classmethod
    def get(cls, job_id: str) -> Optional[TrainingJob]:
        return cls._jobs.get(job_id)

    @classmethod
    def list_jobs(cls) -> List[TrainingJob]:
        return list(cls._jobs.values())


def _detect_batch_size(fallback: int = 8) -> int:
    try:
        import torch

        if not torch.cuda.is_available():
            return max(2, fallback // 2)
        props = torch.cuda.get_device_properties(0)
        vram_gb = props.total_memory / (1024**3)
        if vram_gb >= 24:
            return 32
        if vram_gb >= 16:
            return 16
        if vram_gb >= 12:
            return 12
        if vram_gb >= 8:
            return 8
        return 4
    except Exception:
        return fallback


def _default_train_config(overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    cfg = {
        "model": settings.YOLO_BASE_MODEL,
        "data": str(data_yaml_path()),
        "epochs": 200,
        "imgsz": 640,
        "batch": _detect_batch_size(),
        "optimizer": "AdamW",
        "amp": True,
        "patience": 30,
        "cos_lr": True,
        "resume": False,
        "project": str(runs_root() / "detect"),
        "name": f"grocery_train_{int(time.time())}",
        "hsv_h": 0.015,
        "hsv_s": 0.7,
        "hsv_v": 0.4,
        "degrees": 10.0,
        "translate": 0.1,
        "scale": 0.5,
        "shear": 2.0,
        "perspective": 0.0005,
        "flipud": 0.0,
        "fliplr": 0.5,
        "mosaic": 1.0,
        "mixup": 0.1,
        "copy_paste": 0.0,
        "erasing": 0.2,
    }
    if overrides:
        cfg.update(overrides)
    return cfg


class YoloTrainingService:
    def start_training(self, config_overrides: Optional[Dict[str, Any]] = None) -> TrainingJob:
        report = validate_dataset()
        if not report.ok:
            raise ValueError(f"Dataset validation failed with {len(report.issues)} issues")

        yaml_path = data_yaml_path()
        if not yaml_path.is_file():
            raise FileNotFoundError(f"Missing data.yaml at {yaml_path}")

        job = TrainingJobStore.create(_default_train_config(config_overrides))
        thread = threading.Thread(target=self._run_training, args=(job,), daemon=True)
        thread.start()
        return job

    def resume_training(self, run_dir: str, config_overrides: Optional[Dict[str, Any]] = None) -> TrainingJob:
        last = Path(run_dir) / "weights" / "last.pt"
        if not last.is_file():
            raise FileNotFoundError(f"Cannot resume; missing {last}")
        cfg = _default_train_config(config_overrides)
        cfg["resume"] = str(last)
        job = TrainingJobStore.create(cfg)
        thread = threading.Thread(target=self._run_training, args=(job,), daemon=True)
        thread.start()
        return job

    def _run_training(self, job: TrainingJob) -> None:
        job.status = "running"
        job.started_at = time.time()
        training_logger = get_training_logger()
        error_logger = get_error_logger()
        
        training_logger.info(f"Training job {job.job_id} started with config: {job.config}")
        
        try:
            from ultralytics import YOLO

            cfg = job.config
            model = YOLO(cfg["model"])
            train_kwargs = {k: v for k, v in cfg.items() if k != "model"}
            
            training_logger.info(f"Starting YOLO training with model: {cfg['model']}")
            training_logger.info(f"Training parameters: epochs={cfg.get('epochs')}, imgsz={cfg.get('imgsz')}, batch={cfg.get('batch')}")
            
            results = model.train(**train_kwargs)
            run_dir = Path(results.save_dir) if hasattr(results, "save_dir") else Path(cfg["project"]) / cfg["name"]

            job.run_dir = str(run_dir)
            best = run_dir / "weights" / "best.pt"
            last = run_dir / "weights" / "last.pt"
            job.best_weights = str(best) if best.is_file() else None
            job.last_weights = str(last) if last.is_file() else None

            training_logger.info(f"Training completed. Best weights: {job.best_weights}")
            
            self._export_metrics_csv(run_dir)
            if job.best_weights:
                YoloModelManager.get().copy_best_to_production(Path(job.best_weights))
                training_logger.info(f"Model copied to production: {job.best_weights}")

            job.metrics = self._collect_run_metrics(run_dir)
            job.status = "completed"
            
            training_logger.info(f"Training job {job.job_id} completed successfully")
            training_logger.info(f"Final metrics: {job.metrics}")
            logger.info("Training job %s completed: %s", job.job_id, job.best_weights)
        except Exception as e:
            job.status = "failed"
            job.error = str(e)
            error_logger.error(f"Training job {job.job_id} failed: {str(e)}", exc_info=True)
            logger.exception("Training job %s failed", job.job_id)
        finally:
            job.finished_at = time.time()
            training_logger.info(f"Training job {job.job_id} finished at {job.finished_at}")

    def _export_metrics_csv(self, run_dir: Path) -> None:
        results_csv = run_dir / "results.csv"
        if not results_csv.is_file():
            return
        metrics_csv = run_dir / "metrics.csv"
        shutil_copy = results_csv.read_text(encoding="utf-8")
        metrics_csv.write_text(shutil_copy, encoding="utf-8")

    def _collect_run_metrics(self, run_dir: Path) -> Dict[str, Any]:
        out: Dict[str, Any] = {"run_dir": str(run_dir)}
        results_csv = run_dir / "results.csv"
        if results_csv.is_file():
            with results_csv.open("r", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            if rows:
                last = rows[-1]
                out["last_epoch"] = last
                for key in ("metrics/mAP50(B)", "metrics/mAP50-95(B)", "metrics/precision(B)", "metrics/recall(B)"):
                    if key in last:
                        out[key] = last[key]
        for art in ("confusion_matrix.png", "results.png"):
            p = run_dir / art
            if p.is_file():
                out[art] = str(p)
        return out
