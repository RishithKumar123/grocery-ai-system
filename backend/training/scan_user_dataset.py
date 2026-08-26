"""Interactive Step 1 Dataset Inspection & Quality Audit Tool."""
import os
import sys
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

def scan_dataset(target_path: str):
    root_dir = Path(target_path).resolve()
    if not root_dir.exists():
        print(f"Error: Directory '{root_dir}' does not exist.")
        return

    print("=========================================================")
    print("STEP 1: DATASET INSPECTION & AUDIT REPORT")
    print(f"Root Directory: {root_dir}")
    print("=========================================================")

    product_folders = [d for d in root_dir.iterdir() if d.is_dir()]
    if not product_folders:
        print("[!] No subdirectories found. Scanning root directory files...")
        product_folders = [root_dir]

    image_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
    class_counts: Dict[str, int] = {}
    corrupt_images: List[str] = []
    hashes: Dict[str, Path] = {}
    duplicates: List[Tuple[Path, Path]] = []
    total_images = 0

    for folder in sorted(product_folders):
        folder_name = folder.name if folder != root_dir else "Root_Catalog"
        img_files = [f for f in folder.glob("**/*") if f.suffix.lower() in image_extensions]
        class_counts[folder_name] = len(img_files)
        total_images += len(img_files)

        for img_path in img_files:
            # 1. Check corrupt images
            if HAS_PIL:
                try:
                    with Image.open(img_path) as img:
                        img.verify()
                except Exception:
                    corrupt_images.append(str(img_path))
            
            # 2. Check duplicates via MD5 hash
            try:
                with open(img_path, "rb") as f:
                    h = hashlib.md5(f.read()).hexdigest()
                if h in hashes:
                    duplicates.append((img_path, hashes[h]))
                else:
                    hashes[h] = img_path
            except Exception:
                pass

    print(f"Total Detected Product Classes : {len(class_counts)}")
    print(f"Total Detected Product Images  : {total_images}")
    print(f"Corrupt / Unreadable Images    : {len(corrupt_images)}")
    print(f"Duplicate Image Pairs          : {len(duplicates)}")
    print("---------------------------------------------------------")
    print(f"{'Class / Product Name':<35} | {'Image Count':<12} | {'YOLO Status'}")
    print("---------------------------------------------------------")

    for cls_name, count in class_counts.items():
        if count >= 50:
            status = "[OK] Optimal (>=50)"
        elif count >= 15:
            status = "[WARN] Fair (15-49)"
        else:
            status = "[LOW] Insufficient (<15)"
        print(f"{cls_name:<35} | {count:<12} | {status}")

    print("=========================================================")
    if total_images >= 100 and all(c >= 15 for c in class_counts.values()):
        print("[SUCCESS] RECOMMENDATION: Your dataset is READY for YOLOv11 training!")
    else:
        print("[NOTE] RECOMMENDATION: Collect at least 15-30 images per product class before training for high precision.")
    print("=========================================================")

if __name__ == "__main__":
    path_input = sys.argv[1] if len(sys.argv) > 1 else "."
    scan_dataset(path_input)
