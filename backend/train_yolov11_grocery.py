"""Automated YOLOv11 Grocery Dataset Training Pipeline Script."""
import os
import sys
import yaml
from pathlib import Path

import app.main
from app.core.database import SessionLocal
from app.data.models.product_model import ProductModel

try:
    import torch
    from ultralytics import YOLO
    HAS_YOLO = True
except ImportError:
    HAS_YOLO = False

def prepare_dataset_structure(base_dir: Path, db) -> Path:
    """Create directory structure and data.yaml from database catalog."""
    base_dir.mkdir(parents=True, exist_ok=True)
    (base_dir / "images" / "train").mkdir(parents=True, exist_ok=True)
    (base_dir / "images" / "val").mkdir(parents=True, exist_ok=True)
    (base_dir / "labels" / "train").mkdir(parents=True, exist_ok=True)
    (base_dir / "labels" / "val").mkdir(parents=True, exist_ok=True)

    products = db.query(ProductModel).filter(ProductModel.status == "active").all()
    class_names = {}
    for idx, p in enumerate(products):
        class_names[idx] = p.name

    if not class_names:
        class_names = {
            0: "Patanjali Honey",
            1: "Patanjali Amla Murabba",
            2: "Patanjali Cow Ghee",
            3: "Patanjali Dant Kanti",
            4: "Patanjali Aloe Vera Gel",
            5: "Patanjali Wheat Atta"
        }

    data_yaml_content = {
        "path": str(base_dir.resolve()).replace("\\", "/"),
        "train": "images/train",
        "val": "images/val",
        "names": class_names
    }

    yaml_path = base_dir / "data.yaml"
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(data_yaml_content, f, default_flow_style=False)

    print(f"✓ Dataset layout & data.yaml configured at: {yaml_path}")
    return yaml_path

def train_yolov11_grocery_model(epochs: int = 50, imgsz: int = 640):
    if not HAS_YOLO:
        print("Error: PyTorch or Ultralytics package is not installed.")
        return False

    db = SessionLocal()
    dataset_dir = Path("dataset").resolve()
    data_yaml = prepare_dataset_structure(dataset_dir, db)
    db.close()

    device = "0" if torch.cuda.is_available() else "cpu"
    print(f"=========================================================")
    print(f"STARTING YOLOV11 GROCERY MODEL TRAINING")
    print(f"  • Data YAML: {data_yaml}")
    print(f"  • Epochs: {epochs} | Image Size: {imgsz}")
    print(f"  • Training Device: {device}")
    print(f"=========================================================")

    model = YOLO("yolo11m.pt")
    
    # Check if training images exist before starting training loop
    train_imgs = list((dataset_dir / "images" / "train").glob("*.*"))
    if not train_imgs:
        print("Note: Dataset images folder is currently empty.")
        print(f"To start training, place images into '{dataset_dir / 'images' / 'train'}' and labels into '{dataset_dir / 'labels' / 'train'}'.")
        return True

    results = model.train(
        data=str(data_yaml),
        epochs=epochs,
        imgsz=imgsz,
        device=device,
        project="runs/detect",
        name="grocery_train_production",
        exist_ok=True
    )
    
    best_weights = Path("runs/detect/grocery_train_production/weights/best.pt")
    if best_weights.is_file():
        os.makedirs("models", exist_ok=True)
        import shutil
        shutil.copy(best_weights, "models/best.pt")
        print(f"✓ Trained best.pt weights copied to 'backend/models/best.pt'!")

    return True

if __name__ == "__main__":
    success = train_yolov11_grocery_model()
    sys.exit(0 if success else 1)
