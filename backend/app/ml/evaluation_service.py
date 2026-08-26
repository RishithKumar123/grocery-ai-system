"""Post-training evaluation metrics for grocery YOLO models."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.logging import logger
from app.ml.paths import data_yaml_path


class YoloEvaluationService:
    def evaluate(self, weights_path: str, imgsz: int = 640) -> Dict[str, Any]:
        from ultralytics import YOLO

        model = YOLO(weights_path)
        data = str(data_yaml_path())
        metrics = model.val(data=data, imgsz=imgsz, plots=True)

        summary: Dict[str, Any] = {
            "weights": weights_path,
            "data": data,
        }

        if hasattr(metrics, "results_dict"):
            summary.update(metrics.results_dict)
        if hasattr(metrics, "box"):
            box = metrics.box
            summary["mAP50"] = float(getattr(box, "map50", 0.0))
            summary["mAP50_95"] = float(getattr(box, "map", 0.0))
            summary["precision"] = float(getattr(box, "mp", 0.0))
            summary["recall"] = float(getattr(box, "mr", 0.0))
            p, r = summary["precision"], summary["recall"]
            summary["f1"] = (2 * p * r / (p + r)) if (p + r) > 0 else 0.0

        run_dir = Path(weights_path).parent.parent
        cm = run_dir / "confusion_matrix.png"
        if cm.is_file():
            summary["confusion_matrix"] = str(cm)

        per_class = self._per_class_accuracy(model, data, imgsz)
        summary["per_class"] = per_class
        summary["worst_classes"] = sorted(per_class, key=lambda x: x.get("ap50", 0.0))[:10]

        out_json = run_dir / "evaluation_summary.json"
        out_json.write_text(json.dumps(summary, indent=2), encoding="utf-8")
        logger.info("Evaluation saved to %s", out_json)
        return summary

    def _per_class_accuracy(self, model, data: str, imgsz: int) -> List[Dict[str, Any]]:
        try:
            val = model.val(data=data, imgsz=imgsz, verbose=False)
            names = getattr(model, "names", {}) or {}
            per_class: List[Dict[str, Any]] = []
            if hasattr(val, "box") and hasattr(val.box, "ap50"):
                ap50 = val.box.ap50
                if ap50 is not None:
                    for i, score in enumerate(ap50):
                        per_class.append(
                            {
                                "class_id": i,
                                "class_name": names.get(i, str(i)),
                                "ap50": float(score),
                            }
                        )
            return per_class
        except Exception as e:
            logger.warning("Per-class metrics unavailable: %s", e)
            return []
