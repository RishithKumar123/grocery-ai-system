"""YOLOv11 Enterprise Dataset Syntax & Quality Validator."""
import os
import sys
import json
import yaml
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Tuple

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

def validate_dataset_quality():
    script_dir = Path(__file__).parent.resolve()
    data_yaml_path = script_dir / "data.yaml"

    print("=========================================================")
    print("ENTERPRISE YOLOV11 DATASET QUALITY & SYNTAX VALIDATOR")
    print("=========================================================")

    if not data_yaml_path.is_file():
        print(f"CRITICAL ERROR: data.yaml not found at '{data_yaml_path}'")
        sys.exit(1)

    with open(data_yaml_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    names = config.get("names", {})
    num_classes = len(names)
    print(f"[OK] Registered Catalog Classes in data.yaml: {num_classes}")

    dataset_dir = script_dir / "dataset"
    img_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

    report: Dict[str, Any] = {
        "status": "PASS",
        "total_classes": num_classes,
        "total_images": 0,
        "total_labels": 0,
        "total_instances": 0,
        "splits": {},
        "errors": [],
        "warnings": [],
        "class_instance_counts": {int(k): 0 for k in names.keys()}
    }

    hashes: Dict[str, Path] = {}
    duplicates: List[Tuple[str, str]] = []
    corrupt_count = 0
    small_image_count = 0

    for split in ["train", "val", "test"]:
        img_dir = dataset_dir / "images" / split
        lbl_dir = dataset_dir / "labels" / split

        imgs = {p.stem: p for p in img_dir.glob("*.*") if p.suffix.lower() in img_extensions} if img_dir.is_dir() else {}
        lbls = {p.stem: p for p in lbl_dir.glob("*.txt")} if lbl_dir.is_dir() else {}

        report["splits"][split] = {
            "images": len(imgs),
            "labels": len(lbls),
            "missing_labels": 0,
            "orphan_labels": 0
        }

        report["total_images"] += len(imgs)
        report["total_labels"] += len(lbls)

        # Check missing label text files
        for stem, img_path in imgs.items():
            if stem not in lbls:
                report["splits"][split]["missing_labels"] += 1
                report["warnings"].append(f"[{split}] Image missing label file: {img_path.name}")

            # Check image corruption & dimensions
            if HAS_PIL:
                try:
                    with Image.open(img_path) as im:
                        im.verify()
                        w, h = im.size
                        if w < 32 or h < 32:
                            small_image_count += 1
                            report["warnings"].append(f"[{split}] Extremely small image ({w}x{h}): {img_path.name}")
                except Exception:
                    corrupt_count += 1
                    report["errors"].append(f"[{split}] Corrupt / unreadable image: {img_path.name}")

            # Duplicate image hash audit
            try:
                with open(img_path, "rb") as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()
                if file_hash in hashes:
                    duplicates.append((img_path.name, hashes[file_hash].name))
                else:
                    hashes[file_hash] = img_path
            except Exception:
                pass

        # Check orphan label files
        for stem, lbl_path in lbls.items():
            if stem not in imgs:
                report["splits"][split]["orphan_labels"] += 1
                report["warnings"].append(f"[{split}] Orphan label file missing image: {lbl_path.name}")

            # Audit label file contents & coordinates
            with open(lbl_path, "r", encoding="utf-8") as f:
                for idx, line in enumerate(f, 1):
                    parts = line.strip().split()
                    if not parts:
                        continue
                    if len(parts) != 5:
                        report["errors"].append(f"[{split}] {lbl_path.name}:{idx} -> Expected 5 columns, got {len(parts)}")
                        continue
                    try:
                        cls_id = int(parts[0])
                        xc, yc, w, h = [float(v) for v in parts[1:]]

                        if not (0 <= cls_id < num_classes):
                            report["errors"].append(f"[{split}] {lbl_path.name}:{idx} -> Invalid Class ID {cls_id} (valid range: 0..{num_classes-1})")
                        else:
                            report["class_instance_counts"][cls_id] = report["class_instance_counts"].get(cls_id, 0) + 1
                            report["total_instances"] += 1

                        if not all(0.0 <= v <= 1.0 for v in [xc, yc, w, h]):
                            report["errors"].append(f"[{split}] {lbl_path.name}:{idx} -> Coordinates out of normalized [0, 1] bounds")
                    except ValueError:
                        report["errors"].append(f"[{split}] {lbl_path.name}:{idx} -> Non-numeric bounding box values")

    if report["errors"]:
        report["status"] = "FAIL"

    # Save JSON Report
    report_json_path = script_dir / "dataset_report.json"
    with open(report_json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # Print Summary Terminal Report
    print(f"Status                           : [{report['status']}]")
    print(f"Total Dataset Images             : {report['total_images']}")
    print(f"Total Label Files                : {report['total_labels']}")
    print(f"Total Bounding Box Instances     : {report['total_instances']}")
    print(f"Corrupt Image Files              : {corrupt_count}")
    print(f"Duplicate Image Pairs            : {len(duplicates)}")
    print(f"Extremely Small Images (<32x32)  : {small_image_count}")
    print(f"Critical Dataset Errors          : {len(report['errors'])}")
    print(f"Warnings                         : {len(report['warnings'])}")
    print(f"Saved Report JSON                : {report_json_path}")
    print("=========================================================")

    if report["errors"]:
        print("❌ CRITICAL ERRORS ENCOUNTERED: Please resolve errors before training!")
        sys.exit(1)
    else:
        print("[OK] DATASET VALIDATION PASSED CLEANLY! Ready for training.")

if __name__ == "__main__":
    validate_dataset_quality()
