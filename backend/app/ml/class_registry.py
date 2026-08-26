"""Load YOLO class names from data.yaml and map to product catalog."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Optional, Tuple

import yaml
from sqlalchemy.orm import Session

from app.data.models.product_model import ProductModel
from app.data.models.supplier_model import SupplierModel, ProductSupplierLink
from app.ml.paths import data_yaml_path
from app.core.logging import logger

UNKNOWN_LABEL = "Unknown Product"


def slugify_class_name(name: str) -> str:
    s = name.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "product"


def load_names_from_yaml(path: Optional[Path] = None) -> Dict[int, str]:
    yaml_path = path or data_yaml_path()
    if not yaml_path.is_file():
        return {}
    with yaml_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    names = data.get("names") or {}
    if isinstance(names, list):
        return {i: str(n) for i, n in enumerate(names)}
    return {int(k): str(v) for k, v in names.items()}


def load_names_from_model(model) -> Dict[int, str]:
    if model is None:
        return {}
    names = getattr(model, "names", None)
    if not names:
        return {}
    if isinstance(names, list):
        return {i: str(n) for i, n in enumerate(names)}
    return {int(k): str(v) for k, v in names.items()}


def resolve_class_names(model=None, yaml_path: Optional[Path] = None) -> Dict[int, str]:
    from_yaml = load_names_from_yaml(yaml_path)
    if from_yaml:
        return from_yaml
    from_model = load_names_from_model(model)
    if from_model:
        return from_model
    return {}


def build_data_yaml_from_catalog(db: Session, out_path: Optional[Path] = None) -> Path:
    """Generate data.yaml from products with yolo_class_mapping or sequential assignment."""
    out = out_path or data_yaml_path()
    out.parent.mkdir(parents=True, exist_ok=True)

    products = (
        db.query(ProductModel)
        .filter(ProductModel.status == "active")
        .order_by(ProductModel.id.asc())
        .all()
    )
    if not products:
        raise ValueError("Product catalog is empty; add products before generating data.yaml.")

    names: Dict[int, str] = {}
    used_slugs: set[str] = set()
    next_id = 0

    for prod in products:
        if prod.yolo_class_mapping is not None:
            class_id = int(prod.yolo_class_mapping)
        else:
            while next_id in names:
                next_id += 1
            class_id = next_id
            prod.yolo_class_mapping = class_id
            next_id += 1

        base = slugify_class_name(prod.name)
        slug = base
        suffix = 1
        while slug in used_slugs and names.get(class_id) != slug:
            slug = f"{base}_{suffix}"
            suffix += 1
        used_slugs.add(slug)
        names[class_id] = slug

    db.commit()

    root = out.parent.resolve()
    payload = {
        "path": str(root).replace("\\", "/"),
        "train": "images/train",
        "val": "images/val",
        "test": "images/test",
        "names": names,
        "nc": len(names),
    }
    with out.open("w", encoding="utf-8") as f:
        yaml.safe_dump(payload, f, sort_keys=False, allow_unicode=True)

    logger.info("Generated data.yaml with %s classes at %s", len(names), out)
    return out


def catalog_by_class_id(db: Session) -> Dict[int, ProductModel]:
    products = db.query(ProductModel).filter(ProductModel.yolo_class_mapping.isnot(None)).all()
    return {int(p.yolo_class_mapping): p for p in products}


def catalog_by_slug(db: Session) -> Dict[str, ProductModel]:
    mapping: Dict[str, ProductModel] = {}
    for p in db.query(ProductModel).all():
        mapping[slugify_class_name(p.name)] = p
        if p.yolo_class_mapping is not None:
            mapping[str(p.yolo_class_mapping)] = p
    return mapping


def resolve_product_for_detection(
    db: Session,
    class_id: int,
    class_name: str,
    confidence: float,
    threshold: float = 0.15,
) -> Tuple[str, Optional[ProductModel], bool]:
    """Returns (display_name, product_or_none, is_unknown)."""
    by_id = catalog_by_class_id(db)
    if class_id in by_id:
        prod = by_id[class_id]
        return prod.name, prod, False

    by_slug = catalog_by_slug(db)
    slug = slugify_class_name(class_name)
    if slug in by_slug:
        prod = by_slug[slug]
        return prod.name, prod, False

    # Do not arbitrarily map COCO class IDs to database row numbers
    return UNKNOWN_LABEL, None, True
