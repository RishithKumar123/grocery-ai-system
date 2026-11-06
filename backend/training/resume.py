"""Resume YOLOv11 GPU Training Engine on D: Drive."""
import os
import sys
from pathlib import Path

def resume_training():
    backend_dir = Path(__file__).parent.parent.resolve()
    
    # Environment variable enforcement for zero C: drive write
    temp_dir = backend_dir / "runs" / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    os.environ["YOLO_CONFIG_DIR"] = str(temp_dir)
    os.environ["TORCH_HOME"] = str(temp_dir)

    import torch
    from ultralytics import YOLO

    last_ckpt = backend_dir / "runs" / "detect" / "grocery_candidate_run" / "weights" / "last.pt"
    if not last_ckpt.is_file():
        print(f"Error: Checkpoint not found at '{last_ckpt}'")
        sys.exit(1)

    print("=========================================================")
    print("RESUMING YOLOV11 GPU TRAINING ON D: DRIVE")
    print("=========================================================")
    print(f"  • Checkpoint Path : {last_ckpt}")
    print(f"  • Hardware        : {torch.cuda.get_device_name(0)}")
    print("=========================================================")

    model = YOLO(str(last_ckpt))
    model.train(resume=True, workers=2)

if __name__ == "__main__":
    resume_training()
