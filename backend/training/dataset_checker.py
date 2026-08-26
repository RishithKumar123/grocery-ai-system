"""Dataset Manager & Health Checker Script for Patanjali Product Dataset."""
import os
import sys
import hashlib
import cv2
import yaml
from pathlib import Path
from typing import Dict, List, Tuple

class DatasetManager:
    """Audits dataset health, label consistency, corrupt images, duplicate detection, and class counts."""

    def __init__(self, dataset_dir: Optional[Path] = None) -> None:
        self.script_dir = Path(__file__).parent.resolve()
        self.dataset_dir = dataset_dir or (self.script_dir / "dataset")
        self.data_yaml = self.script_dir / "data.yaml"
        self.class_names = self._load_class_names()

    def _load_class_names(self) -> Dict[int, str]:
        if not self.data_yaml.is_file():
            return {}
        with open(self.data_yaml, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        names = data.get("names") or {}
        if isinstance(names, list):
            return {i: str(n) for i, n in enumerate(names)}
        return {int(k): str(v) for k, v in names.items()}

    def ensure_dataset_directories(self) -> None:
        """Create dataset directory tree if missing."""
        for split in ["train", "val", "test"]:
            (self.dataset_dir / "images" / split).mkdir(parents=True, exist_ok=True)
            (self.dataset_dir / "labels" / split).mkdir(parents=True, exist_ok=True)
        print(f"✓ Verified dataset directory structure at: {self.dataset_dir}")

    def audit_dataset(self) -> Dict[str, Any]:
        """Perform comprehensive health check on dataset."""
        self.ensure_dataset_directories()
        
        report = {
            "splits": {},
            "total_images": 0,
            "total_labels": 0,
            "corrupt_images": [],
            "missing_labels": [],
            "unmatched_labels": [],
            "duplicate_images": [],
            "class_counts": {idx: 0 for idx in self.class_names.keys()}
        }

        image_hashes: Dict[str, Path] = {}

        for split in ["train", "val", "test"]:
            img_dir = self.dataset_dir / "images" / split
            lbl_dir = self.dataset_dir / "labels" / split

            images = list(img_dir.glob("*.*"))
            labels = list(lbl_dir.glob("*.txt"))

            split_info = {
                "image_count": len(images),
                "label_count": len(labels)
            }
            report["splits"][split] = split_info
            report["total_images"] += len(images)
            report["total_labels"] += len(labels)

            image_stems = {img.stem: img for img in images if img.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp", ".bmp"]}
            label_stems = {lbl.stem: lbl for lbl in labels}

            # Check missing labels
            for stem, img_path in image_stems.items():
                if stem not in label_stems:
                    report["missing_labels"].append(str(img_path))

            # Check unmatched labels
            for stem, lbl_path in label_stems.items():
                if stem not in image_stems:
                    report["unmatched_labels"].append(str(lbl_path))

            # Check corrupt images & duplicate images via MD5
            for stem, img_path in image_stems.items():
                try:
                    img = cv2.imread(str(img_path))
                    if img is None:
                        report["corrupt_images"].append(str(img_path))
                    else:
                        with open(img_path, "rb") as f:
                            file_hash = hashlib.md5(f.read()).hexdigest()
                        if file_hash in image_hashes:
                            report["duplicate_images"].append((str(img_path), str(image_hashes[file_hash])))
                        else:
                            image_hashes[file_hash] = img_path
                except Exception:
                    report["corrupt_images"].append(str(img_path))

            # Count instances per class
            for lbl_path in labels:
                try:
                    with open(lbl_path, "r", encoding="utf-8") as f:
                        for line in f:
                            parts = line.strip().split()
                            if parts:
                                cls_id = int(parts[0])
                                report["class_counts"][cls_id] = report["class_counts"].get(cls_id, 0) + 1
                except Exception:
                    pass

        return report

    def print_summary_report(self) -> None:
        """Print clean formatted dataset health report."""
        report = self.audit_dataset()

        print("=========================================================")
        print("PATANJALI DATASET HEALTH & HEALTH CHECK REPORT")
        print("=========================================================")
        print(f"Dataset Path: {self.dataset_dir}")
        print(f"Total Images: {report['total_images']} | Total Labels: {report['total_labels']}")
        print("---------------------------------------------------------")
        for split, info in report["splits"].items():
            print(f"  • Split '{split}': {info['image_count']} images, {info['label_count']} labels")

        print("---------------------------------------------------------")
        print(f"Corrupt Images:    {len(report['corrupt_images'])}")
        print(f"Missing Labels:    {len(report['missing_labels'])}")
        print(f"Unmatched Labels:  {len(report['unmatched_labels'])}")
        print(f"Duplicate Images:  {len(report['duplicate_images'])}")

        print("---------------------------------------------------------")
        print("INSTANCE COUNTS PER PATANJALI CLASS:")
        for cls_id, name in self.class_names.items():
            count = report["class_counts"].get(cls_id, 0)
            print(f"  [{cls_id:02d}] {name:<25}: {count} instances")

        print("=========================================================")


if __name__ == "__main__":
    checker = DatasetManager()
    checker.print_summary_report()
    sys.exit(0)
