from __future__ import annotations

import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional

from app.core.logging import logger
from app.ml.paths import data_yaml_path, dataset_root, split_image_dir, split_label_dir, DATASET_SPLITS


class DatasetBuilder:
    """Create and verify standard YOLO dataset structure from existing files."""

    def __init__(self, root: Optional[Path] = None):
        self.root = root or dataset_root()
        self.images_dir = self.root / "images"
        self.labels_dir = self.root / "labels"
        self.yaml_path = data_yaml_path()

    def ensure_structure(self) -> None:
        for split in DATASET_SPLITS:
            (self.images_dir / split).mkdir(parents=True, exist_ok=True)
            (self.labels_dir / split).mkdir(parents=True, exist_ok=True)
        self.yaml_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info("Ensured dataset structure at %s", self.root)

    def list_image_files(self, split: str) -> List[Path]:
        return sorted([p for p in (self.images_dir / split).glob("*.*") if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp", ".webp"}])

    def list_label_files(self, split: str) -> List[Path]:
        return sorted((self.labels_dir / split).glob("*.txt"))

    def move_image(self, src: Path, split: str) -> Path:
        dst = self.images_dir / split / src.name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        return dst

    def move_label(self, src: Path, split: str) -> Path:
        dst = self.labels_dir / split / src.name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
        return dst

    def clean_orphan_labels(self) -> int:
        removed = 0
        for split in DATASET_SPLITS:
            for label_path in self.list_label_files(split):
                image_path = self.images_dir / split / f"{label_path.stem}{label_path.suffix}"
                if not any((self.images_dir / split / f"{label_path.stem}{ext}").is_file() for ext in [".jpg", ".jpeg", ".png", ".bmp", ".webp"]):
                    label_path.unlink()
                    removed += 1
        return removed

    def write_data_yaml(self, names: Dict[int, str], train: str = "images/train", val: str = "images/val", test: str = "images/test") -> Path:
        payload = {
            "path": str(self.root).replace("\\", "/"),
            "train": train,
            "val": val,
            "test": test,
            "names": names,
            "nc": len(names),
        }
        import yaml
        with self.yaml_path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(payload, f, sort_keys=False, allow_unicode=True)
        logger.info("Generated data.yaml with %s classes", len(names))
        return self.yaml_path

    def build_labels_from_catalog(self, names: Dict[int, str]) -> Path:
        return self.write_data_yaml(names)

    def verify_structure(self) -> Dict[str, int]:
        counts = {split: len(self.list_image_files(split)) for split in DATASET_SPLITS}
        counts.update({f"{split}_labels": len(self.list_label_files(split)) for split in DATASET_SPLITS})
        return counts
