"""Authoritative Master Class Registry Generator & Freezing Script."""
import sys
import json
import yaml
from pathlib import Path
from decimal import Decimal

def freeze_registry():
    script_dir = Path(__file__).parent.resolve()
    backend_dir = script_dir.parent.resolve()
    data_yaml_path = script_dir / "data.yaml"

    print("=========================================================")
    print("TASK 2: FREEZE AUTHORITATIVE MASTER CLASS REGISTRY")
    print("=========================================================")

    if not data_yaml_path.is_file():
        print(f"Error: data.yaml not found at '{data_yaml_path}'")
        sys.exit(1)

    with open(data_yaml_path, "r", encoding="utf-8") as f:
        yaml_config = yaml.safe_load(f) or {}

    yaml_names = yaml_config.get("names", {})
    total_classes = len(yaml_names)

    master_registry = {}
    for cls_id_str, class_name in sorted(yaml_names.items(), key=lambda x: int(x[0])):
        cls_id = int(cls_id_str)
        clean_name = class_name.replace("_", " ").strip()
        brand = clean_name.split()[0] if clean_name else "Generic"

        master_registry[cls_id] = {
            "class_id": cls_id,
            "product_name": clean_name,
            "brand": brand,
            "sku": f"SKU-FMCG-{cls_id:04d}",
            "barcode": f"890FMCG{cls_id:04d}",
            "category": "Grocery",
            "yolo_class_name": class_name
        }

    # Write Master JSON Registry
    registry_json_path = script_dir / "class_registry.json"
    with open(registry_json_path, "w", encoding="utf-8") as f:
        json.dump(master_registry, f, indent=2)

    print(f"[OK] Created Authoritative Master Registry: {registry_json_path}")
    print(f"  • Total Frozen Class IDs: {len(master_registry)}")

    # Update Database Catalog Table
    sys.path.insert(0, str(backend_dir))
    import app.main
    from app.core.database import SessionLocal
    from app.data.models.product_model import ProductModel

    db = SessionLocal()
    # Reset existing mappings
    db.query(ProductModel).update({ProductModel.yolo_class_mapping: None})
    db.commit()

    updated_db = 0
    created_db = 0

    for cls_id, item in master_registry.items():
        clean_name = item["product_name"]
        prod = db.query(ProductModel).filter(ProductModel.name.ilike(clean_name)).first()
        if not prod:
            clean_slug = clean_name.lower().replace(" ", "")
            for p in db.query(ProductModel).all():
                if p.name.lower().replace(" ", "") == clean_slug:
                    prod = p
                    break

        if prod:
            prod.name = clean_name
            prod.yolo_class_mapping = cls_id
            updated_db += 1
        else:
            new_prod = ProductModel(
                name=clean_name,
                brand=item["brand"],
                sku=item["sku"],
                barcode=item["barcode"],
                category=item["category"],
                price=Decimal("50.00"),
                cost_price=Decimal("35.00"),
                unit="pack",
                yolo_class_mapping=cls_id,
                status="active"
            )
            db.add(new_prod)
            created_db += 1

    db.commit()
    db.close()

    print(f"[OK] Synchronized SQL Database Catalog:")
    print(f"  • Updated Existing Products : {updated_db}")
    print(f"  • Created New Products      : {created_db}")
    print("=========================================================")

if __name__ == "__main__":
    freeze_registry()
