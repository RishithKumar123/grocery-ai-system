"""YOLOv11 Model Exporter Script."""
import sys
from pathlib import Path

try:
    import torch
    from ultralytics import YOLO
    HAS_YOLO = True
except ImportError:
    HAS_YOLO = False

def run_export(format_type: str = "onnx"):
    if not HAS_YOLO:
        print("Error: PyTorch or Ultralytics package is not installed.")
        return False

    script_dir = Path(__file__).parent.resolve()
    best_weights = script_dir.parent / "models" / "best.pt"
    if not best_weights.is_file():
        best_weights = script_dir / "runs" / "patanjali_yolo11" / "weights" / "best.pt"
    if not best_weights.is_file():
        best_weights = Path("yolo11m.pt")

    print("=========================================================")
    print("YOLOV11 MODEL EXPORT")
    print(f"  • Model Weights: {best_weights}")
    print(f"  • Export Format: {format_type}")
    print("=========================================================")

    model = YOLO(str(best_weights))
    exported_path = model.export(format=format_type)
    print(f"✓ Model exported successfully to: {exported_path}")
    print("=========================================================")
    return True

if __name__ == "__main__":
    fmt = sys.argv[1] if len(sys.argv) > 1 else "onnx"
    run_export(fmt)
