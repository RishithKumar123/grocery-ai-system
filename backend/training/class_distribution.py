"""Class Instance Frequency Distribution Auditor."""
import sys
import yaml
from pathlib import Path
from typing import Dict

def audit_class_distribution():
    script_dir = Path(__file__).parent.resolve()
    data_yaml = script_dir / "data.yaml"

    with open(data_yaml, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    names = config.get("names", {})
    counts: Dict[int, int] = {int(k): 0 for k in names.keys()}

    dataset_dir = script_dir / "dataset"
    total_instances = 0

    for split in ["train", "val", "test"]:
        lbl_dir = dataset_dir / "labels" / split
        if not lbl_dir.is_dir():
            continue

        for lbl_path in lbl_dir.glob("*.txt"):
            with open(lbl_path, "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.strip().split()
                    if parts:
                        try:
                            cls_id = int(parts[0])
                            counts[cls_id] = counts.get(cls_id, 0) + 1
                            total_instances += 1
                        except ValueError:
                            pass

    print("=========================================================")
    print("FMCG PRODUCT CLASS INSTANCE FREQUENCY DISTRIBUTION")
    print(f"Total Bounding Box Instances: {total_instances}")
    print("=========================================================")

    for cls_id, name in sorted(names.items(), key=lambda x: int(x[0])):
        cnt = counts.get(int(cls_id), 0)
        status = "OK" if cnt >= 50 else ("LOW" if cnt > 0 else "EMPTY")
        print(f"  [{cls_id:03d}] {name:<35}: {cnt:<5} instances [{status}]")

    print("=========================================================")

if __name__ == "__main__":
    audit_class_distribution()
