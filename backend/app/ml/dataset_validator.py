"""YOLO dataset validation utilities."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import cv2
import yaml

from app.ml.paths import (
    DATASET_SPLITS,
    data_yaml_path,
    dataset_root,
    split_image_dir,
    split_label_dir,
)

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


@dataclass
class ValidationIssue:
    severity: str  # error | warning
    category: str
    message: str
    split: Optional[str] = None
    file: Optional[str] = None


@dataclass
class ValidationReport:
    ok: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    stats: Dict[str, object] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "issues": [i.__dict__ for i in self.issues],
            "stats": self.stats,
        }


def _file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _parse_yolo_label_line(line: str, num_classes: int) -> Tuple[bool, str]:
    parts = line.strip().split()
    if len(parts) != 5:
        return False, "label line must have 5 values (class cx cy w h)"
    try:
        cls = int(float(parts[0]))
        coords = [float(x) for x in parts[1:]]
    except ValueError:
        return False, "non-numeric label values"
    if cls < 0 or (num_classes and cls >= num_classes):
        return False, f"class id {cls} out of range [0, {num_classes})"
    for c in coords:
        if c < 0 or c > 1:
            return False, f"normalized coordinate {c} outside [0,1]"
    return True, ""


def validate_dataset(num_classes: Optional[int] = None) -> ValidationReport:
    issues: List[ValidationIssue] = []
    stats: Dict[str, object] = {
        "images": {},
        "labels": {},
        "duplicates": [],
    }

    yaml_path = data_yaml_path()
    names: Dict[int, str] = {}
    if yaml_path.is_file():
        with yaml_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        raw_names = data.get("names") or {}
        if isinstance(raw_names, list):
            names = {i: str(n) for i, n in enumerate(raw_names)}
        else:
            names = {int(k): str(v) for k, v in raw_names.items()}
        if num_classes is None:
            num_classes = data.get("nc") or len(names)
    elif num_classes is None:
        num_classes = 0

    seen_hashes: Dict[str, str] = {}

    for split in DATASET_SPLITS:
        img_dir = split_image_dir(split)
        lbl_dir = split_label_dir(split)
        img_count = 0
        lbl_count = 0

        if not img_dir.exists():
            issues.append(ValidationIssue("warning", "missing_split", f"Missing image split: {split}", split=split))
            continue

        images = [p for p in img_dir.iterdir() if p.suffix.lower() in IMAGE_EXTS]
        img_count = len(images)

        for img in images:
            try:
                img_hash = _file_hash(img)
                if img_hash in seen_hashes:
                    dup = seen_hashes[img_hash]
                    stats["duplicates"].append({"file": str(img), "duplicate_of": dup})
                    issues.append(
                        ValidationIssue(
                            "warning",
                            "duplicate_image",
                            f"Duplicate image hash matches {dup}",
                            split=split,
                            file=img.name,
                        )
                    )
                else:
                    seen_hashes[img_hash] = str(img)
            except OSError as e:
                issues.append(ValidationIssue("error", "corrupted_image", str(e), split=split, file=img.name))
                continue

            mat = cv2.imread(str(img))
            if mat is None:
                issues.append(
                    ValidationIssue("error", "corrupted_image", "OpenCV cannot read image", split=split, file=img.name)
                )
                continue

            h, w = mat.shape[:2]
            lbl = lbl_dir / f"{img.stem}.txt"
            if not lbl.is_file():
                issues.append(
                    ValidationIssue("error", "missing_label", "No matching label file", split=split, file=img.name)
                )
                continue

            lbl_count += 1
            lines = lbl.read_text(encoding="utf-8").strip().splitlines()
            if not lines:
                issues.append(
                    ValidationIssue("warning", "empty_label", "Label file is empty", split=split, file=lbl.name)
                )
            seen_lines: Set[str] = set()
            for i, line in enumerate(lines):
                if line in seen_lines:
                    issues.append(
                        ValidationIssue("warning", "duplicate_label", f"Duplicate box line {i+1}", split=split, file=lbl.name)
                    )
                seen_lines.add(line)
                ok, msg = _parse_yolo_label_line(line, int(num_classes or 0))
                if not ok:
                    issues.append(
                        ValidationIssue("error", "invalid_yolo_label", msg, split=split, file=lbl.name)
                    )

        # orphan labels
        if lbl_dir.exists():
            for lbl in lbl_dir.glob("*.txt"):
                img_candidates = [img_dir / f"{lbl.stem}{ext}" for ext in IMAGE_EXTS]
                if not any(p.is_file() for p in img_candidates):
                    issues.append(
                        ValidationIssue("error", "orphan_label", "Label without image", split=split, file=lbl.name)
                    )

        stats["images"][split] = img_count
        stats["labels"][split] = lbl_count

    stats["class_names"] = names
    stats["dataset_root"] = str(dataset_root())
    errors = [i for i in issues if i.severity == "error"]
    return ValidationReport(ok=len(errors) == 0, issues=issues, stats=stats)
