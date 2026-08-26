"""YOLOv11 Candidate Model Validation & Evaluation Engine."""
import sys
import yaml
from pathlib import Path

try:
    import torch
    from ultralytics import YOLO
    HAS_YOLO = True
except ImportError:
    HAS_YOLO = False

def run_validation():
    script_dir = Path(__file__).parent.resolve()
    backend_dir = script_dir.parent.resolve()
    data_yaml = script_dir / "data.yaml"

    candidate_weights = backend_dir / "models" / "candidates" / "candidate_best.pt"
    if not candidate_weights.is_file():
        candidate_weights = backend_dir / "models" / "best.pt"

    print("=========================================================")
    print("YOLOV11 MODEL EVALUATION & METRICS ENGINE")
    print(f"Target Weights : {candidate_weights}")
    print(f"Data YAML      : {data_yaml}")
    print("=========================================================")

    if not HAS_YOLO:
        print("Error: PyTorch or Ultralytics package is missing.")
        sys.exit(1)

    if not candidate_weights.is_file():
        print(f"Error: Candidate model weights not found at '{candidate_weights}'")
        sys.exit(1)

    model = YOLO(str(candidate_weights))
    metrics = model.val(data=str(data_yaml), imgsz=640, split="val")

    mp = metrics.box.mp  # Mean Precision
    mr = metrics.box.mr  # Mean Recall
    map50 = metrics.box.map50  # mAP50
    map95 = metrics.box.map    # mAP50-95

    print("\n=========================================================")
    print("AGGREGATED EVALUATION METRICS REPORT")
    print("=========================================================")
    print(f"  • Mean Precision (P)    : {mp * 100:.2f}%")
    print(f"  • Mean Recall (R)       : {mr * 100:.2f}%")
    print(f"  • mAP@50                : {map50 * 100:.2f}%")
    print(f"  • mAP@50-95             : {map95 * 100:.2f}%")
    print("=========================================================")

    names = metrics.names
    print(f"\nPER-CLASS PERFORMANCE BREAKDOWN ({len(names)} Classes):")
    print("---------------------------------------------------------")
    print(f"{'Class ID':<8} | {'Class Name':<35} | {'mAP50'}")
    print("---------------------------------------------------------")

    maps_per_class = metrics.box.maps if hasattr(metrics.box, "maps") else []
    for cls_id, cls_name in sorted(names.items(), key=lambda x: int(x[0])):
        c_map = maps_per_class[int(cls_id)] * 100 if int(cls_id) < len(maps_per_class) else 0.0
        print(f"[{cls_id:03d}]     | {cls_name:<35} | {c_map:.1f}%")

    print("=========================================================")
    if map50 >= 0.15:
        print("[OK] VALIDATION PASSED: Candidate model meets performance threshold!")
        print("💡 Next Step: Run 'python training/deploy.py' to promote to production.")
    else:
        print("⚠️ WARNING: Validation metrics are low. Collect more annotated images before deployment.")

if __name__ == "__main__":
    run_validation()
