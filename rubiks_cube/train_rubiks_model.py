"""High-Resolution Augmented YOLO11n Training Script for Rubik's Cube Stickers."""
import os
import sys
import yaml
from pathlib import Path
import torch
from ultralytics import YOLO

def main():
    project_dir = Path(__file__).parent.resolve()
    dataset_dir = project_dir / "dataset"
    data_yaml = dataset_dir / "data.yaml"

    if not data_yaml.is_file():
        print(f"Error: data.yaml not found at '{data_yaml}'")
        sys.exit(1)

    print("=========================================================")
    print("RUBIK'S CUBE HIGH-RES STICKER YOLO11n TRAINING ENGINE")
    print("=========================================================")
    cuda_available = torch.cuda.is_available()
    device_id = "0" if cuda_available else "cpu"
    gpu_name = torch.cuda.get_device_name(0) if cuda_available else "CPU Fallback"
    print(f"  • Hardware           : {gpu_name}")
    print(f"  • Device             : device={device_id}")
    print(f"  • Model Base         : yolo11n.pt")
    print(f"  • Image Size         : 1024x1024 (Native Resolution)")
    print(f"  • Dataset YAML       : {data_yaml}")
    print("=========================================================")

    model = YOLO("yolo11n.pt")

    runs_dir = project_dir / "runs"
    results = model.train(
        data=str(data_yaml),
        epochs=100,
        imgsz=1024,
        batch=2,
        device=device_id,
        patience=25,
        degrees=15.0,
        scale=0.5,
        perspective=0.0005,
        fliplr=0.5,
        project=str(runs_dir),
        name="rubiks_sticker_run",
        exist_ok=True,
        verbose=True
    )

    best_weights = runs_dir / "rubiks_sticker_run" / "weights" / "best.pt"
    print("\n=========================================================")
    print("HIGH-RES TRAINING COMPLETED SUCCESSFULLY!")
    print(f"  • Best Model Path : {best_weights.resolve()}")
    print("=========================================================")

if __name__ == "__main__":
    main()
