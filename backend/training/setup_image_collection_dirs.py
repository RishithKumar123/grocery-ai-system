"""Product Image Collection Folders Setup Script."""
import os
import sys
import json
from pathlib import Path

def setup_collection_directories():
    script_dir = Path(__file__).parent.resolve()
    registry_json_path = script_dir / "class_registry.json"

    print("=========================================================")
    print("TASK 3 & 4: SETUP PRODUCT IMAGE COLLECTION FOLDERS")
    print("=========================================================")

    if not registry_json_path.is_file():
        print(f"Error: Master registry not found at '{registry_json_path}'")
        sys.exit(1)

    with open(registry_json_path, "r", encoding="utf-8") as f:
        registry = json.load(f)

    base_collection_dir = script_dir / "dataset" / "product_images"
    base_collection_dir.mkdir(parents=True, exist_ok=True)

    created_dirs = 0
    for cls_id_str, item in registry.items():
        cid = int(cls_id_str)
        p_name = item["product_name"].replace(" ", "_")
        dir_name = f"{cid:03d}_{p_name}"
        target_dir = base_collection_dir / dir_name
        target_dir.mkdir(parents=True, exist_ok=True)
        created_dirs += 1

    print(f"[OK] Product Image Collection Base Directory Created:")
    print(f"  • Base Path     : {base_collection_dir}")
    print(f"  • Folders Built : {created_dirs} Product Folders (000_Patanjali_Amla_Murabba .. 104_...)")
    print("=========================================================")

if __name__ == "__main__":
    setup_collection_directories()
