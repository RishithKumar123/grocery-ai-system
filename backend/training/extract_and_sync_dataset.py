"""Extract Grocery_Items.v1i.yolov11.zip dataset from Downloads and synchronize catalog."""
import os
import sys
import zipfile
import yaml
import json
import shutil
from pathlib import Path
from decimal import Decimal

def extract_and_sync():
    script_dir = Path(__file__).parent.resolve()
    backend_dir = script_dir.parent.resolve()
    downloads_zip = Path(os.path.expanduser("~/Downloads/Grocery_Items.v1i.yolov11.zip")).resolve()

    print("=========================================================")
    print("EXTRACTING GROCERY DATASET & SYNCHRONIZING SYSTEM CATALOG")
    print("=========================================================")
    print(f"  • Zip Location : {downloads_zip}")

    if not downloads_zip.is_file():
        print(f"Error: Zip file not found at '{downloads_zip}'")
        sys.exit(1)

    target_dataset_dir = script_dir / "dataset"
    print(f"  • Target Dir   : {target_dataset_dir}")

    # Extract zip file
    print("\n[1/3] Extracting 13,395 files from zip... (Please wait)")
    with zipfile.ZipFile(downloads_zip, "r") as zip_ref:
        zip_ref.extractall(target_dataset_dir)

    print("[OK] Dataset extracted successfully!")

    # Read extracted data.yaml
    extracted_yaml = target_dataset_dir / "data.yaml"
    if not extracted_yaml.is_file():
        print(f"Error: data.yaml not found inside extracted folder at {extracted_yaml}")
        sys.exit(1)

    with open(extracted_yaml, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}

    names = cfg.get("names", [])
    num_classes = len(names)

    # Format data.yaml with absolute paths for Ultralytics
    train_path = (target_dataset_dir / "train" / "images").as_posix()
    val_path = (target_dataset_dir / "valid" / "images").as_posix()
    test_path = (target_dataset_dir / "test" / "images").as_posix()

    formatted_config = {
        "path": target_dataset_dir.as_posix(),
        "train": "train/images",
        "val": "valid/images",
        "test": "test/images",
        "nc": num_classes,
        "names": {i: name for i, name in enumerate(names)} if isinstance(names, list) else names
    }

    data_yaml_target = script_dir / "data.yaml"
    with open(data_yaml_target, "w", encoding="utf-8") as f:
        yaml.dump(formatted_config, f, sort_keys=False)

    print(f"\n[2/3] Updated data.yaml with {num_classes} FMCG product classes.")

    # Generate master class_registry.json
    class_map = formatted_config["names"]
    master_registry = {}
    for cls_id, class_name in class_map.items():
        cid = int(cls_id)
        clean_name = str(class_name).replace("_", " ").strip()
        brand = clean_name.split()[0] if clean_name else "Generic"
        master_registry[cid] = {
            "class_id": cid,
            "product_name": clean_name,
            "brand": brand,
            "sku": f"SKU-GROC-{cid:04d}",
            "barcode": f"890GROC{cid:04d}",
            "category": "Grocery",
            "yolo_class_name": class_name
        }

    registry_json_path = script_dir / "class_registry.json"
    with open(registry_json_path, "w", encoding="utf-8") as f:
        json.dump(master_registry, f, indent=2)

    print(f"[3/3] Created Master Class Registry: {registry_json_path}")

    # Synchronize Database
    sys.path.insert(0, str(backend_dir))
    import app.main
    from app.core.database import SessionLocal
    from app.data.models.product_model import ProductModel

    db = SessionLocal()
    db.query(ProductModel).update({ProductModel.yolo_class_mapping: None})
    db.commit()

    updated_db = 0
    created_db = 0

    for cid, item in master_registry.items():
        clean_name = item["product_name"]
        prod = db.query(ProductModel).filter(ProductModel.name.ilike(clean_name)).first()
        if prod:
            prod.name = clean_name
            prod.yolo_class_mapping = cid
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
                yolo_class_mapping=cid,
                status="active"
            )
            db.add(new_prod)
            created_db += 1

    db.commit()
    db.close()

    print("=========================================================")
    print("[OK] EXTRACT & CATALOG SYNCHRONIZATION COMPLETED!")
    print(f"  • Total Classes   : {num_classes}")
    print(f"  • DB Products     : Updated {updated_db}, Created {created_db}")
    print("=========================================================")
    print("💡 READY FOR TRAINING! Run 'python training/train.py' to start training on RTX 3050 GPU.")

if __name__ == "__main__":
    extract_and_sync()
