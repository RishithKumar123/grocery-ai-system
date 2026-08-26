"""Duplicate Image Detector using MD5 Hashing."""
import sys
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple

def find_duplicates():
    script_dir = Path(__file__).parent.resolve()
    dataset_dir = script_dir / "dataset"

    print("=========================================================")
    print("DUPLICATE IMAGE DETECTOR")
    print("=========================================================")

    hashes: Dict[str, Path] = {}
    duplicates: List[Tuple[Path, Path]] = []

    for split in ["train", "val", "test"]:
        img_dir = dataset_dir / "images" / split
        if not img_dir.is_dir():
            continue

        for img_path in img_dir.glob("*.*"):
            if img_path.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp", ".bmp"]:
                with open(img_path, "rb") as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()

                if file_hash in hashes:
                    duplicates.append((img_path, hashes[file_hash]))
                else:
                    hashes[file_hash] = img_path

    if not duplicates:
        print("✓ Zero duplicate images detected across train, val, and test splits.")
    else:
        print(f"⚠️  Found {len(duplicates)} duplicate image pairs:")
        for dup, orig in duplicates:
            print(f"  • Duplicate: {dup.name} <==> Original: {orig.name}")
    print("=========================================================")

if __name__ == "__main__":
    find_duplicates()
