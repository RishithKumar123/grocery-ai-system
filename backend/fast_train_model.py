import os
import sys
import time
import json
import shutil
from pathlib import Path
from ultralytics import YOLO

backend_dir = Path(__file__).parent.resolve()
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.ml.dataset_validator import validate_dataset
from app.ml.model_manager import YoloModelManager
from app.ml.paths import data_yaml_path, runs_root

def run_fast_train():
    print("\n=========================================================")
    print("STEP 1 & 2: DATASET VALIDATION & HEALTH CHECK")
    print("=========================================================")
    
    report = validate_dataset()
    print(f"Dataset Validation OK: {report.ok}")
    print(f"Dataset Stats: {report.stats}")

    print("\n=========================================================")
    print("STEP 3 & 4: YOLOv11 TRAIN & DATA AUGMENTATION")
    print("=========================================================")
    
    yaml_path = data_yaml_path()
    train_run_name = f"grocery_train_{int(time.time())}"
    detect_project_dir = runs_root() / "detect"
    
    model = YOLO("yolo11n.pt")
    
    train_kwargs = {
        "data": str(yaml_path),
        "epochs": 3,
        "imgsz": 640,
        "batch": 8,
        "optimizer": "AdamW",
        "amp": True,
        "patience": 30,
        "cos_lr": True,
        "project": str(detect_project_dir),
        "name": train_run_name,
        "hsv_h": 0.015,
        "hsv_s": 0.7,
        "hsv_v": 0.4,
        "degrees": 10.0,
        "translate": 0.1,
        "scale": 0.5,
        "shear": 2.0,
        "perspective": 0.0005,
        "fliplr": 0.5,
        "mosaic": 1.0,
        "mixup": 0.1,
        "verbose": True
    }
    
    results = model.train(**train_kwargs)
    
    run_dir = Path(results.save_dir) if hasattr(results, "save_dir") else detect_project_dir / train_run_name
    best_pt = run_dir / "weights" / "best.pt"
    last_pt = run_dir / "weights" / "last.pt"
    
    standard_train_dir = detect_project_dir / "train" / "weights"
    standard_train_dir.mkdir(parents=True, exist_ok=True)
    if best_pt.is_file():
        shutil.copy(best_pt, standard_train_dir / "best.pt")
    if last_pt.is_file():
        shutil.copy(last_pt, standard_train_dir / "last.pt")

    print("\n=========================================================")
    print("STEP 5: MODEL EVALUATION & METRICS GENERATION")
    print("=========================================================")
    
    results_csv = run_dir / "results.csv"
    metrics_csv = run_dir / "metrics.csv"
    if results_csv.is_file():
        shutil.copy(results_csv, metrics_csv)
        
    val_model = YOLO(str(best_pt if best_pt.is_file() else last_pt))
    metrics = val_model.val(data=str(yaml_path), imgsz=640)
    
    precision = metrics.box.mp
    recall = metrics.box.mr
    map50 = metrics.box.map50
    map50_95 = metrics.box.map
    
    print(f"Metrics Output:")
    print(f"  Precision: {precision:.4f}")
    print(f"  Recall:    {recall:.4f}")
    print(f"  mAP50:     {map50:.4f}")
    print(f"  mAP50-95:  {map50_95:.4f}")

    print("\n=========================================================")
    print("STEP 7: MODEL EXPORT (ONNX & TorchScript)")
    print("=========================================================")
    
    try:
        onnx_file = val_model.export(format="onnx")
        print(f"ONNX Model Exported: {onnx_file}")
    except Exception as e:
        print(f"ONNX Export Warning: {e}")

    try:
        ts_file = val_model.export(format="torchscript")
        print(f"TorchScript Model Exported: {ts_file}")
    except Exception as e:
        print(f"TorchScript Export Warning: {e}")

    print("\n=========================================================")
    print("STEP 8 & 9: APPLICATION REGISTER & INFERENCE VERIFICATION")
    print("=========================================================")
    
    manager = YoloModelManager.get()
    manager.set_active_model(best_pt if best_pt.is_file() else last_pt, persist=True)
    print("Active production model weights updated!")

if __name__ == "__main__":
    run_fast_train()
