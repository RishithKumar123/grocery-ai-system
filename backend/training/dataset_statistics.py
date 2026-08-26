"""Dataset Statistics Generator."""
import sys
import yaml
from pathlib import Path
from typing import Dict, Any

def generate_statistics():
    script_dir = Path(__file__).parent.resolve()
    data_yaml = script_dir / "data.yaml"

    if not data_yaml.is_file():
        print(f"Error: data.yaml not found at '{data_yaml}'")
        return

    with open(data_yaml, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    names = config.get("names", {})
    num_classes = len(names)

    print("=========================================================")
    print("ENTERPRISE GROCERY DATASET STATISTICS REPORT")
    print(f"Total Registered Classes: {num_classes}")
    print("=========================================================")

    dataset_dir = script_dir / "dataset"
    total_imgs = 0
    total_lbls = 0

    for split in ["train", "val", "test"]:
        img_dir = dataset_dir / "images" / split
        lbl_dir = dataset_dir / "labels" / split

        imgs = list(img_dir.glob("*.*")) if img_dir.is_dir() else []
        lbls = list(lbl_dir.glob("*.txt")) if lbl_dir.is_dir() else []

        total_imgs += len(imgs)
        total_lbls += len(lbls)

        print(f"  • Split [{split:<5}]: {len(imgs):<5} images | {len(lbls):<5} label files")

    print("---------------------------------------------------------")
    print(f"Grand Total Images:     {total_imgs}")
    print(f"Grand Total Label Files: {total_lbls}")
    print("=========================================================")

if __name__ == "__main__":
    generate_statistics()
