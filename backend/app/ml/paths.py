"""Filesystem paths for grocery YOLO dataset and training artifacts."""
from __future__ import annotations

import os
from pathlib import Path
from functools import lru_cache


@lru_cache(maxsize=1)
def project_root() -> Path:
    """Monorepo root (parent of backend/)."""
    return Path(__file__).resolve().parents[3]


def backend_root() -> Path:
    return Path(__file__).resolve().parents[2]


def dataset_root() -> Path:
    env = os.environ.get("ML_DATASET_ROOT")
    if env:
        return Path(env).resolve()
    return project_root() / "dataset"


def runs_root() -> Path:
    env = os.environ.get("ML_RUNS_DIR")
    if env:
        return Path(env).resolve()
    return project_root() / "runs"


def unknown_products_dir() -> Path:
    p = project_root() / "backend" / "local_storage" / "unknown_products"
    p.mkdir(parents=True, exist_ok=True)
    return p


DATASET_SPLITS = ("train", "val", "test")


def split_image_dir(split: str) -> Path:
    return dataset_root() / "images" / split


def split_label_dir(split: str) -> Path:
    return dataset_root() / "labels" / split


def data_yaml_path() -> Path:
    return dataset_root() / "data.yaml"


def ensure_dataset_layout() -> None:
    for split in DATASET_SPLITS:
        split_image_dir(split).mkdir(parents=True, exist_ok=True)
        split_label_dir(split).mkdir(parents=True, exist_ok=True)
    data_yaml_path().touch(exist_ok=True)
