"""Comprehensive Reproducible Dataset & Annotation Audit Script for GroceryAI."""
import os
import sys
import yaml
import csv
import json
import re
from pathlib import Path
from collections import defaultdict, Counter

def run_dataset_audit():
    script_dir = Path(__file__).parent.resolve()
    dataset_dir = script_dir / "dataset"
    data_yaml_path = dataset_dir / "data.yaml"

    if not data_yaml_path.is_file():
        print(f"Error: data.yaml not found at '{data_yaml_path}'")
        sys.exit(1)

    print("=========================================================")
    print("GROCERY AI COMPLETE DATASET & ANNOTATION DIAGNOSTIC AUDIT")
    print("=========================================================")
    print(f"Dataset Root: {dataset_dir.resolve()}")

    with open(data_yaml_path, "r", encoding="utf-8") as f:
        data_cfg = yaml.safe_load(f)

    nc = data_cfg.get("nc", 0)
    names_raw = data_cfg.get("names", {})
    
    if isinstance(names_raw, list):
        class_names = {i: str(n) for i, n in enumerate(names_raw)}
    elif isinstance(names_raw, dict):
        class_names = {int(k): str(v) for k, v in names_raw.items()}
    else:
        class_names = {}

    print(f"Declared Classes in data.yaml (nc) : {nc}")
    print(f"Class Names Parsed                : {len(class_names)}")

    splits = ["train", "valid", "test"]
    split_counts = {}
    
    # Class tracking
    class_train_imgs = defaultdict(set)
    class_valid_imgs = defaultdict(set)
    class_test_imgs = defaultdict(set)
    
    class_train_bboxes = Counter()
    class_valid_bboxes = Counter()
    class_test_bboxes = Counter()

    # Annotation errors
    total_label_files = 0
    empty_label_files = 0
    corrupt_label_lines = 0
    invalid_bbox_coords = 0
    out_of_range_class_ids = set()
    invalid_class_id_instances = 0

    for split in splits:
        labels_dir = dataset_dir / split / "labels"
        images_dir = dataset_dir / split / "images"

        img_files = list(images_dir.glob("*.*")) if images_dir.is_dir() else []
        lbl_files = list(labels_dir.glob("*.txt")) if labels_dir.is_dir() else []

        split_counts[split] = {
            "images": len(img_files),
            "labels": len(lbl_files)
        }

        print(f"\n--- Auditing Split: '{split}' ({len(img_files)} images, {len(lbl_files)} label files) ---")

        for lbl_path in lbl_files:
            total_label_files += 1
            img_name = lbl_path.stem

            try:
                content = lbl_path.read_text(encoding="utf-8", errors="ignore").strip()
            except Exception as e:
                print(f"Error reading {lbl_path}: {e}")
                continue

            if not content:
                empty_label_files += 1
                continue

            lines = content.splitlines()
            for line_idx, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue

                parts = line.split()
                if len(parts) < 5:
                    corrupt_label_lines += 1
                    continue

                try:
                    cls_id = int(parts[0])
                    x_center = float(parts[1])
                    y_center = float(parts[2])
                    w = float(parts[3])
                    h = float(parts[4])
                except ValueError:
                    corrupt_label_lines += 1
                    continue

                # Check class ID range
                if cls_id < 0 or cls_id >= nc:
                    out_of_range_class_ids.add(cls_id)
                    invalid_class_id_instances += 1

                # Check bounding box validity
                if not (0.0 <= x_center <= 1.0 and 0.0 <= y_center <= 1.0 and 0.0 < w <= 1.0 and 0.0 < h <= 1.0):
                    invalid_bbox_coords += 1

                # Record per-split class stats
                if split == "train":
                    class_train_imgs[cls_id].add(img_name)
                    class_train_bboxes[cls_id] += 1
                elif split == "valid":
                    class_valid_imgs[cls_id].add(img_name)
                    class_valid_bboxes[cls_id] += 1
                elif split == "test":
                    class_test_imgs[cls_id].add(img_name)
                    class_test_bboxes[cls_id] += 1

    # Detailed Class Histogram & Low-Shot Analysis
    low_shot_histogram = Counter() # 0, 1, 2, 3, 4, 5 images
    zero_train_classes = []
    
    for cid in range(nc):
        t_count = len(class_train_imgs[cid])
        if t_count <= 5:
            low_shot_histogram[t_count] += 1
        if t_count == 0:
            zero_train_classes.append((cid, class_names.get(cid, f"Class_{cid}")))

    # Duplicate / Near-Duplicate Class Name Detection
    duplicate_groups = []
    normalized_name_map = defaultdict(list)
    
    for cid, name in class_names.items():
        norm = re.sub(r"[^a-z0-9]+", "", name.lower())
        normalized_name_map[norm].append((cid, name))

    for norm_key, group in normalized_name_map.items():
        if len(group) > 1:
            duplicate_groups.append(group)

    # Fuzzy Duplicate Grouping (e.g. Chocolate_DairyMilk_Cadbury vs DairyMilk_Chocolate)
    token_groups = defaultdict(list)
    for cid, name in class_names.items():
        tokens = sorted([t for t in re.findall(r"\w+", name.lower()) if t not in {"cadbury", "amul", "patanjali", "nestle", "britannia", "parle"}])
        token_key = "_".join(tokens)
        if token_key:
            token_groups[token_key].append((cid, name))

    fuzzy_duplicates = [(k, v) for k, v in token_groups.items() if len(v) > 1]

    # Write CSV Report
    report_csv_path = script_dir / "dataset_audit_report.csv"
    with open(report_csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "class_id",
            "product_name",
            "train_image_count",
            "valid_image_count",
            "test_image_count",
            "total_image_count",
            "train_bbox_count",
            "valid_bbox_count",
            "test_bbox_count",
            "total_bbox_count",
            "sufficiency_status"
        ])

        for cid in range(nc):
            pname = class_names.get(cid, f"Class_{cid}")
            tr_img = len(class_train_imgs[cid])
            va_img = len(class_valid_imgs[cid])
            te_img = len(class_test_imgs[cid])
            tot_img = tr_img + va_img + te_img

            tr_bb = class_train_bboxes[cid]
            va_bb = class_valid_bboxes[cid]
            te_bb = class_test_bboxes[cid]
            tot_bb = tr_bb + va_bb + te_bb

            status_str = "Sufficient (>= 15 imgs)" if tr_img >= 15 else ("Extremely Low (1-5 imgs)" if tr_img > 0 else "Zero Training Samples (0 imgs)")

            writer.writerow([
                cid,
                pname,
                tr_img,
                va_img,
                te_img,
                tot_img,
                tr_bb,
                va_bb,
                te_bb,
                tot_bb,
                status_str
            ])

    print("\n=========================================================")
    print("AUDIT RESULTS & STATISTICAL SUMMARY")
    print("=========================================================")
    print(f"Total Declared Product Classes      : {nc}")
    print(f"Total Label Files Audited           : {total_label_files}")
    print(f"Empty Label Files (No Annotations)  : {empty_label_files}")
    print(f"Corrupt Label Lines                 : {corrupt_label_lines}")
    print(f"Invalid Bounding Box Coordinates    : {invalid_bbox_coords}")
    print(f"Out-of-Range Class IDs              : {len(out_of_range_class_ids)} unique IDs ({invalid_class_id_instances} instances)")
    
    print("\n--- Low-Shot Class Distribution (Training Set) ---")
    print(f"  * Classes with 0 training images  : {low_shot_histogram[0]} ({round(low_shot_histogram[0]/nc*100, 1)}%)")
    print(f"  * Classes with 1 training image   : {low_shot_histogram[1]} ({round(low_shot_histogram[1]/nc*100, 1)}%)")
    print(f"  * Classes with 2 training images  : {low_shot_histogram[2]} ({round(low_shot_histogram[2]/nc*100, 1)}%)")
    print(f"  * Classes with 3 training images  : {low_shot_histogram[3]} ({round(low_shot_histogram[3]/nc*100, 1)}%)")
    print(f"  * Classes with 4 training images  : {low_shot_histogram[4]} ({round(low_shot_histogram[4]/nc*100, 1)}%)")
    print(f"  * Classes with 5 training images  : {low_shot_histogram[5]} ({round(low_shot_histogram[5]/nc*100, 1)}%)")
    
    total_low_shot = sum(low_shot_histogram[i] for i in range(6))
    print(f"  TOTAL Classes with <= 5 Training Images: {total_low_shot} out of {nc} ({round(total_low_shot/nc*100, 1)}%)")

    print("\n--- Duplicate / Near-Duplicate Class Names Identified ---")
    print(f"Exact Normalized Duplicates Count : {len(duplicate_groups)}")
    for grp in duplicate_groups[:10]:
        print(f"  * Group: {grp}")

    print(f"\nFuzzy Semantic Duplicate Groups   : {len(fuzzy_duplicates)}")
    for key, grp in fuzzy_duplicates[:10]:
        print(f"  * Match '{key}': {grp}")

    print(f"\nDetailed CSV Report Generated     : {report_csv_path.resolve()}")
    print("=========================================================\n")

if __name__ == "__main__":
    run_dataset_audit()
