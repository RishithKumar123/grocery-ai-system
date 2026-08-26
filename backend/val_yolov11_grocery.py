"""YOLOv11 Model Validation Script."""
import sys
from pathlib import Path

try:
    import torch
    from ultralytics import YOLO
    HAS_YOLO = True
except ImportError:
    HAS_YOLO = False

def val_yolov11_grocery_model():
    if not HAS_YOLO:
        print("Error: PyTorch or Ultralytics package is not installed.")
        return False

    weights_path = Path("models/best.pt")
    if not weights_path.is_file():
        weights_path = Path("yolo11m.pt")

    data_yaml = Path("dataset/data.yaml")
    if not data_yaml.is_file():
        print(f"Error: Dataset yaml file not found at '{data_yaml}'. Run train_yolov11_grocery.py first.")
        return False

    device = "0" if torch.cuda.is_available() else "cpu"
    print(f"=========================================================")
    print(f"VAL YOLOV11 GROCERY MODEL METRICS")
    print(f"  • Weights: {weights_path}")
    print(f"  • Data YAML: {data_yaml}")
    print(f"  • Device: {device}")
    print(f"=========================================================")

    model = YOLO(str(weights_path))
    metrics = model.val(data=str(data_yaml), imgsz=640, device=device)

    print(f"✓ Validation Complete:")
    print(f"  • mAP50:    {metrics.box.map50:.4f}")
    print(f"  • mAP50-95: {metrics.box.map:.4f}")
    print(f"  • Precision: {metrics.box.mp:.4f}")
    print(f"  • Recall:    {metrics.box.mr:.4f}")
    print("=========================================================")
    return True

if __name__ == "__main__":
    success = val_yolov11_grocery_model()
    sys.exit(0 if success else 1)
