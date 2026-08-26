"""Export trained grocery YOLO weights to deployment formats."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from app.core.logging import logger


class YoloExportService:
    def export_all(self, weights_path: str, imgsz: int = 640) -> Dict[str, str]:
        from ultralytics import YOLO

        path = Path(weights_path)
        if not path.is_file():
            raise FileNotFoundError(weights_path)

        model = YOLO(str(path))
        out_dir = path.parent
        exported: Dict[str, str] = {"best_pt": str(path)}

        try:
            ts_path = model.export(format="torchscript", imgsz=imgsz)
            exported["torchscript"] = str(ts_path)
        except Exception as e:
            logger.error("TorchScript export failed: %s", e)

        try:
            onnx_path = model.export(format="onnx", imgsz=imgsz, simplify=True)
            exported["onnx"] = str(onnx_path)
        except Exception as e:
            logger.error("ONNX export failed: %s", e)

        logger.info("Exported artifacts from %s: %s", path, list(exported.keys()))
        return exported

    def list_artifacts(self, weights_path: str) -> List[str]:
        parent = Path(weights_path).parent
        return [str(p) for p in parent.glob("*") if p.is_file()]
