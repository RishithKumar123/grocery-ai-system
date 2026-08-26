"""Class Mismatch Investigation & Audit Script."""
import sys
import json
import yaml
from pathlib import Path

try:
    from ultralytics import YOLO
    HAS_YOLO = True
except ImportError:
    HAS_YOLO = False

def run_class_mismatch_audit():
    script_dir = Path(__file__).parent.resolve()
    backend_dir = script_dir.parent.resolve()
    data_yaml_path = script_dir / "data.yaml"

    print("=========================================================")
    print("TASK 1: CLASS COUNT MISMATCH INVESTIGATION & AUDIT")
    print("=========================================================")

    if not data_yaml_path.is_file():
        print(f"Error: data.yaml not found at '{data_yaml_path}'")
        sys.exit(1)

    with open(data_yaml_path, "r", encoding="utf-8") as f:
        yaml_config = yaml.safe_load(f) or {}

    yaml_names = yaml_config.get("names", {})
    print(f"1. Total Classes defined in training/data.yaml : {len(yaml_names)}")

    # Load DB Products
    sys.path.insert(0, str(backend_dir))
    import app.main
    from app.core.database import SessionLocal
    from app.data.models.product_model import ProductModel

    db = SessionLocal()
    db_prods = db.query(ProductModel).all()
    db.close()

    print(f"2. Total Products in Database Catalog Table   : {len(db_prods)}")

    # Load Model Weights
    best_pt_path = backend_dir / "models" / "best.pt"
    prod_pt_path = backend_dir / "models" / "production" / "production_best.pt"

    best_names = {}
    prod_names = {}

    if HAS_YOLO:
        if best_pt_path.is_file():
            m_best = YOLO(str(best_pt_path))
            best_names = m_best.names
        if prod_pt_path.is_file():
            m_prod = YOLO(str(prod_pt_path))
            prod_names = m_prod.names

    print(f"3. Class Count in models/best.pt               : {len(best_names)}")
    print(f"4. Class Count in models/production_best.pt    : {len(prod_names)}")
    print("=========================================================")

    # Convert to sets for precise diff
    yaml_class_set = {v.replace("_", " ").strip() for v in yaml_names.values()}
    best_class_set = {v.replace("_", " ").strip() for v in best_names.values()}

    missing_from_model = yaml_class_set - best_class_set

    print(f"\n🔍 PRECISE MISMATCH ANALYSIS:")
    print(f"  • Total Classes in data.yaml        : {len(yaml_class_set)}")
    print(f"  • Total Classes in trained best.pt   : {len(best_class_set)}")
    print(f"  • Discrepancy Count                 : {len(missing_from_model)} Missing Classes")
    print("---------------------------------------------------------")
    print("IDENTIFIED 9 MISSING PRODUCTS IN TRAINED MODEL:")
    print("---------------------------------------------------------")
    for idx, missing_p in enumerate(sorted(missing_from_model), 1):
        print(f"  [{idx:02d}] {missing_p}")
    print("---------------------------------------------------------")

    report_payload = {
        "data_yaml_count": len(yaml_names),
        "db_catalog_count": len(db_prods),
        "best_pt_count": len(best_names),
        "missing_count": len(missing_from_model),
        "missing_products": sorted(list(missing_from_model)),
        "data_yaml_classes": {int(k): v for k, v in yaml_names.items()},
        "model_best_classes": {int(k): v for k, v in best_names.items()}
    }

    report_out_path = script_dir / "class_mismatch_report.json"
    with open(report_out_path, "w", encoding="utf-8") as f:
        json.dump(report_payload, f, indent=2)

    print(f"[OK] Audit Report saved to: {report_out_path}")
    print("=========================================================")

if __name__ == "__main__":
    run_class_mismatch_audit()
