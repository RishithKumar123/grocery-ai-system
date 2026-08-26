import os
import sys
import time
import json
import shutil
from pathlib import Path
from ultralytics import YOLO

# Add backend directory to sys.path
backend_dir = Path(__file__).parent.resolve()
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.ml.dataset_validator import validate_dataset
from app.ml.model_manager import YoloModelManager
from app.ml.paths import data_yaml_path, runs_root

def run_pipeline():
    print("\n=========================================================")
    print("STEP 1 & 2: DATASET VALIDATION & HEALTH CHECK")
    print("=========================================================")
    
    report = validate_dataset()
    print(f"Dataset Validation OK: {report.ok}")
    print(f"Stats: {report.stats}")
    print(f"Total Issues Found: {len(report.issues)}")
    for issue in report.issues:
        print(f"  [{issue.severity.upper()}] {issue.category}: {issue.message} (split: {issue.split})")

    if not report.ok:
        print("ERROR: Dataset validation failed! Aborting pipeline.")
        return

    print("\n=========================================================")
    print("STEP 3 & 4: YOLOv11m MODEL TRAINING & AUGMENTATION")
    print("=========================================================")
    
    yaml_path = data_yaml_path()
    train_run_name = f"grocery_train_{int(time.time())}"
    detect_project_dir = runs_root() / "detect"
    
    print(f"Loading Base Model: yolo11m.pt")
    model = YOLO("yolo11m.pt")
    
    train_kwargs = {
        "data": str(yaml_path),
        "epochs": 15,
        "imgsz": 640,
        "batch": 4,
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
    
    print(f"Starting Training with parameters:\n{json.dumps({k: str(v) for k, v in train_kwargs.items()}, indent=2)}")
    results = model.train(**train_kwargs)
    
    run_dir = Path(results.save_dir) if hasattr(results, "save_dir") else detect_project_dir / train_run_name
    best_pt = run_dir / "weights" / "best.pt"
    last_pt = run_dir / "weights" / "last.pt"
    
    print(f"\nTraining completed! Run output directory: {run_dir}")
    print(f"Best Weights: {best_pt} (Exists: {best_pt.is_file()})")
    print(f"Last Weights: {last_pt} (Exists: {last_pt.is_file()})")
    
    # Ensure runs/detect/train/weights/best.pt standard output link exists
    standard_train_dir = detect_project_dir / "train" / "weights"
    standard_train_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(best_pt, standard_train_dir / "best.pt")
    shutil.copy(last_pt, standard_train_dir / "last.pt")
    print(f"Copied best weights to standard production path: {standard_train_dir / 'best.pt'}")

    print("\n=========================================================")
    print("STEP 5: MODEL EVALUATION & METRICS GENERATION")
    print("=========================================================")
    
    results_csv = run_dir / "results.csv"
    metrics_csv = run_dir / "metrics.csv"
    if results_csv.is_file():
        shutil.copy(results_csv, metrics_csv)
        print(f"Exported metrics.csv: {metrics_csv}")
        
    val_model = YOLO(str(best_pt))
    metrics = val_model.val(data=str(yaml_path), imgsz=640)
    
    precision = metrics.box.mp
    recall = metrics.box.mr
    map50 = metrics.box.map50
    map50_95 = metrics.box.map
    
    print(f"Model Performance Metrics:")
    print(f"  - Precision:  {precision:.4f} ({precision*100:.2f}%)")
    print(f"  - Recall:     {recall:.4f} ({recall*100:.2f}%)")
    print(f"  - mAP50:      {map50:.4f} ({map50*100:.2f}%)")
    print(f"  - mAP50-95:   {map50_95:.4f} ({map50_95*100:.2f}%)")

    print("\n=========================================================")
    print("STEP 7: MODEL EXPORT (ONNX & TorchScript)")
    print("=========================================================")
    
    try:
        onnx_path = val_model.export(format="onnx")
        print(f"ONNX Model Exported: {onnx_path}")
    except Exception as e:
        print(f"ONNX Export Warning: {e}")
        
    try:
        torchscript_path = val_model.export(format="torchscript")
        print(f"TorchScript Model Exported: {torchscript_path}")
    except Exception as e:
        print(f"TorchScript Export Warning: {e}")

    print("\n=========================================================")
    print("STEP 8 & 9: APPLICATION REGISTER & INFERENCE VERIFICATION")
    print("=========================================================")
    
    manager = YoloModelManager.get()
    manager.set_active_model(best_pt, persist=True)
    print(f"Successfully registered active production model weights!")
    
    # Test inference on test split image
    test_img = dataset_root / "images" / "test" / "sample_0051.jpg"
    if test_img.is_file():
        inf_res = val_model.predict(str(test_img), conf=0.25)
        print(f"Inference Test Output on {test_img.name}: {len(inf_res[0].boxes)} objects detected!")
        for b in inf_res[0].boxes:
            cls_id = int(b.cls[0].item())
            conf_val = float(b.conf[0].item())
            print(f"  -> Object Class #{cls_id} with confidence {conf_val:.2f}")

    print("\n=========================================================")
    print("AI MODEL TRAINING & INTEGRATION COMPLETED SUCCESSFULLY!")
    print("=========================================================")

if __name__ == "__main__":
    run_pipeline()
