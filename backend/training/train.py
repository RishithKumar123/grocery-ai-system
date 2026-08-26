"""NVIDIA RTX 3050 GPU YOLOv11 Training Engine."""
import os
import sys
import yaml
from pathlib import Path

try:
    import torch
    from ultralytics import YOLO
    HAS_YOLO = True
except ImportError:
    HAS_YOLO = False

def run_training(epochs: int = 100, imgsz: int = 640):
    script_dir = Path(__file__).parent.resolve()
    backend_dir = script_dir.parent.resolve()
    
    # Force Ultralytics settings, cache, and PyTorch temp downloads to D:
    temp_dir = backend_dir / "runs" / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    os.environ["YOLO_CONFIG_DIR"] = str(temp_dir)
    os.environ["TORCH_HOME"] = str(temp_dir)
    
    data_yaml = script_dir / "data.yaml"

    if not data_yaml.is_file():
        print(f"Error: data.yaml not found at '{data_yaml}'")
        sys.exit(1)

    cuda_available = torch.cuda.is_available() if HAS_YOLO else False
    device_id = "0" if cuda_available else "cpu"
    gpu_name = torch.cuda.get_device_name(0) if cuda_available else "CPU Fallback"
    cuda_version = torch.version.cuda if cuda_available else "N/A"
    total_vram_gb = round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 2) if cuda_available else 0.0

    print("=========================================================")
    print("NVIDIA RTX 3050 GPU YOLOV11 TRAINING ENGINE")
    print("=========================================================")
    print(f"  • CUDA Available       : {cuda_available}")
    print(f"  • PyTorch CUDA Version : {cuda_version}")
    print(f"  • Hardware             : {gpu_name}")
    print(f"  • Total VRAM           : {total_vram_gb} GB")
    print(f"  • Training Device      : device={device_id}")
    print(f"  • Target Epochs        : {epochs}")
    print(f"  • Image Size           : {imgsz}x{imgsz}")
    print(f"  • Mixed Precision (AMP): True")
    print(f"  • Data YAML            : {data_yaml}")
    print("=========================================================")

    if not HAS_YOLO:
        print("Error: PyTorch or Ultralytics package is missing.")
        sys.exit(1)

    model_name = "yolo11s.pt"
    batch_size = 2  # Optimized for 3674-class loss assignment memory safety

    print(f"Initializing Base Weights: {model_name} (Batch Size={batch_size})...")
    model = YOLO(model_name)

    candidates_dir = backend_dir / "models" / "candidates"
    candidates_dir.mkdir(parents=True, exist_ok=True)
    detect_project_dir = backend_dir / "runs" / "detect"
    run_name = "grocery_candidate_run"

    try:
        results = model.train(
            data=str(data_yaml),
            epochs=epochs,
            imgsz=imgsz,
            batch=batch_size,
            device=device_id,
            amp=True,
            workers=2,
            project=str(detect_project_dir),
            name=run_name,
            exist_ok=True,
            verbose=True
        )
    except Exception as exc:
        print(f"\n⚠️ Memory Warning: {exc}. Retrying with batch=1...")
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        batch_size = 1
        results = model.train(
            data=str(data_yaml),
            epochs=epochs,
            imgsz=imgsz,
            batch=batch_size,
            device=device_id,
            amp=True,
            workers=1,
            project=str(detect_project_dir),
            name=run_name,
            exist_ok=True,
            verbose=True
        )

    best_weights = detect_project_dir / run_name / "weights" / "best.pt"
    if not best_weights.is_file():
        best_weights = detect_project_dir / "runs" / "detect" / run_name / "weights" / "best.pt"

    if best_weights.is_file():
        candidate_target = candidates_dir / "candidate_best.pt"
        import shutil
        shutil.copy(best_weights, candidate_target)
        print("=========================================================")
        print(f"[OK] Candidate Model Trained Successfully!")
        print(f"  • Trained Weights : {best_weights}")
        print(f"  • Candidate Copy  : {candidate_target}")
        print("=========================================================")
        print("💡 Next Step: Run 'python training/validate.py' to evaluate metrics before deployment.")
    else:
        print(f"Error: Trained weights not found at {best_weights}")
        sys.exit(1)

if __name__ == "__main__":
    epochs_input = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    run_training(epochs=epochs_input)
