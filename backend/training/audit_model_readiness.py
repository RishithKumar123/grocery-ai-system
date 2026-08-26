"""Strict Dataset and Model Readiness Audit Script."""
import sys
import yaml
import json
from pathlib import Path

try:
    from ultralytics import YOLO
    HAS_YOLO = True
except ImportError:
    HAS_YOLO = False

def perform_strict_audit():
    script_dir = Path(__file__).parent.resolve()
    backend_dir = script_dir.parent.resolve()
    data_yaml = script_dir / "data.yaml"
    dataset_dir = script_dir / "dataset"
    if not (dataset_dir / "images").is_dir():
        dataset_dir = backend_dir / "dataset"

    if not data_yaml.is_file():
        print(f"Error: data.yaml not found at '{data_yaml}'")
        sys.exit(1)

    with open(data_yaml, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    names = config.get("names", {})
    num_classes = len(names)

    img_counts = {int(k): 0 for k in names.keys()}
    bbox_counts = {int(k): 0 for k in names.keys()}
    splits = {"train": 0, "val": 0, "test": 0}
    total_imgs = 0

    img_extensions = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

    for s in ["train", "val", "test"]:
        img_d = dataset_dir / "images" / s
        lbl_d = dataset_dir / "labels" / s

        imgs = [p for p in img_d.glob("*.*") if p.suffix.lower() in img_extensions] if img_d.is_dir() else []
        splits[s] = len(imgs)
        total_imgs += len(imgs)

        if lbl_d.is_dir():
            for lbl_f in lbl_d.glob("*.txt"):
                classes_in_file = set()
                with open(lbl_f, "r", encoding="utf-8") as f:
                    for line in f:
                        parts = line.strip().split()
                        if parts:
                            try:
                                cid = int(parts[0])
                                if cid in bbox_counts:
                                    bbox_counts[cid] += 1
                                    classes_in_file.add(cid)
                            except ValueError:
                                pass
                for cid in classes_in_file:
                    if cid in img_counts:
                        img_counts[cid] += 1

    zero_images_classes = [f"[{k}] {names[k]}" for k, v in img_counts.items() if v == 0]
    fewer_than_10_classes = [f"[{k}] {names[k]} ({v} imgs)" for k, v in img_counts.items() if v < 10]
    fewer_than_20_classes = [f"[{k}] {names[k]} ({v} imgs)" for k, v in img_counts.items() if v < 20]

    all_exist = len(zero_images_classes) == 0

    # Model file inspection
    best_pt = backend_dir / "models" / "best.pt"
    prod_best_pt = backend_dir / "models" / "production" / "production_best.pt"
    yolo_base = backend_dir / "yolo11m.pt"

    best_class_count = 0
    prod_class_count = 0
    is_not_coco_copy = False

    metrics_res = None
    if HAS_YOLO and best_pt.is_file():
        m_best = YOLO(str(best_pt))
        best_class_count = len(m_best.names)
        if prod_best_pt.is_file():
            m_prod = YOLO(str(prod_best_pt))
            prod_class_count = len(m_prod.names)
            # Check if sizes/names differ from COCO
            is_not_coco_copy = prod_class_count != 80 and "person" not in m_prod.names.values()

        # Run validation
        try:
            metrics_res = m_best.val(data=str(data_yaml), imgsz=640, split="val")
        except Exception as val_err:
            print(f"Validation warning: {val_err}")

    print("=========================================================")
    print("STRICT DATASET AND MODEL READINESS AUDIT REPORT")
    print("=========================================================")
    print(f"1. Total Number of Images                 : {total_imgs}")
    print(f"2. Images in Splits                       : Train={splits['train']}, Val={splits['val']}, Test={splits['test']}")
    print(f"5. Classes with Zero Images               : {len(zero_images_classes)} of {num_classes}")
    print(f"6. Classes with < 10 Images               : {len(fewer_than_10_classes)} of {num_classes}")
    print(f"7. Classes with < 20 Images               : {len(fewer_than_20_classes)} of {num_classes}")
    print(f"8. All data.yaml classes exist in dataset : {all_exist}")
    print(f"12. best.pt Class Count                   : {best_class_count} custom classes")
    print(f"14. production_best.pt is Custom Model    : {is_not_coco_copy} (Class Count: {prod_class_count})")
    print("=========================================================")

    if metrics_res:
        mp = float(metrics_res.box.mp)
        mr = float(metrics_res.box.mr)
        map50 = float(metrics_res.box.map50)
        map95 = float(metrics_res.box.map)

        print("\n9. ACTUAL VALIDATION METRICS:")
        print(f"   • Precision (P) : {mp * 100:.2f}%")
        print(f"   • Recall (R)    : {mr * 100:.2f}%")
        print(f"   • mAP@50        : {map50 * 100:.2f}%")
        print(f"   • mAP@50-95     : {map95 * 100:.2f}%")

        print("\n10. PER-CLASS PERFORMANCE & LABELED INSTANCES (Sample Classes):")
        print("---------------------------------------------------------")
        print(f"{'Class ID':<8} | {'Class Name':<35} | {'Images':<7} | {'Labels':<7} | {'mAP50'}")
        print("---------------------------------------------------------")
        maps_per_class = metrics_res.box.maps if hasattr(metrics_res.box, "maps") else []
        for cls_id, cls_name in sorted(names.items(), key=lambda x: int(x[0])):
            cid = int(cls_id)
            c_map = maps_per_class[cid] * 100 if cid < len(maps_per_class) else 0.0
            print(f"[{cid:03d}]     | {cls_name:<35} | {img_counts[cid]:<7} | {bbox_counts[cid]:<7} | {c_map:.1f}%")
        print("---------------------------------------------------------")

    print("\nSUMMARY AUDIT CONCLUSION:")
    if total_imgs < 300 or len(zero_images_classes) > 0:
        print("⚠️ STATUS: NOT PRODUCTION-READY YET (DATASET INSUFFICIENT)")
        print(f"Reason: Dataset currently contains only {total_imgs} total images and {len(zero_images_classes)} classes have 0 images.")
        print("Recommendation: Collect 20-50 real shelf images for every zero-image class before deploying to live production.")
    else:
        print("✓ STATUS: PRODUCTION READY")

if __name__ == "__main__":
    perform_strict_audit()
