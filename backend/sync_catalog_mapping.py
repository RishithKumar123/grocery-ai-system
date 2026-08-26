"""Synchronizes database ProductModel table with training/data.yaml class mappings."""
import sys
import yaml
from decimal import Decimal
from pathlib import Path

import app.main
from app.core.database import SessionLocal
from app.data.models.product_model import ProductModel
from app.core.logging import logger

def sync_catalog():
    script_dir = Path(__file__).parent.resolve()
    data_yaml = script_dir / "training" / "data.yaml"

    if not data_yaml.is_file():
        print(f"Error: data.yaml not found at '{data_yaml}'")
        return False

    with open(data_yaml, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    names = config.get("names", {})
    db = SessionLocal()

    print("=========================================================")
    print("SYNCHRONIZING DATABASE CATALOG WITH DATA.YAML")
    print(f"Total FMCG Classes in YAML: {len(names)}")
    print("=========================================================")

    updated_count = 0
    created_count = 0

    # Reset all yolo_class_mappings to avoid cross-class index collision
    db.query(ProductModel).update({ProductModel.yolo_class_mapping: None})
    db.commit()

    for cls_id_str, class_name in sorted(names.items(), key=lambda x: int(x[0])):
        cls_id = int(cls_id_str)
        clean_name = class_name.replace("_", " ")

        # Look for existing product in database strictly by name or slug
        prod = db.query(ProductModel).filter(ProductModel.name.ilike(clean_name)).first()
        if not prod:
            # Fuzzy match slug
            clean_slug = clean_name.lower().replace(" ", "")
            prods_all = db.query(ProductModel).all()
            for p in prods_all:
                if p.name.lower().replace(" ", "") == clean_slug:
                    prod = p
                    break

        if prod:
            prod.name = clean_name
            prod.yolo_class_mapping = cls_id
            updated_count += 1
        else:
            new_prod = ProductModel(
                name=clean_name,
                sku=f"SKU-FMCG-{cls_id:04d}",
                barcode=f"890FMCG{cls_id:04d}",
                category="Grocery",
                price=Decimal("50.00"),
                cost_price=Decimal("35.00"),
                unit="pack",
                yolo_class_mapping=cls_id,
                status="active"
            )
            db.add(new_prod)
            created_count += 1

    db.commit()
    db.close()

    print(f"✓ Catalog Synchronization Complete:")
    print(f"  • Existing Products Updated: {updated_count}")
    print(f"  • New FMCG Products Created: {created_count}")
    print("=========================================================")
    return True

if __name__ == "__main__":
    success = sync_catalog()
    sys.exit(0 if success else 1)
