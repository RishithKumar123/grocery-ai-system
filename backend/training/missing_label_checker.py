"""Missing Label & Orphan Label File Checker."""
import sys
from pathlib import Path

def check_missing_labels():
    script_dir = Path(__file__).parent.resolve()
    dataset_dir = script_dir / "dataset"

    print("=========================================================")
    print("MISSING LABEL & ORPHAN FILE CHECKER")
    print("=========================================================")

    missing_labels = []
    orphan_labels = []

    for split in ["train", "val", "test"]:
        img_dir = dataset_dir / "images" / split
        lbl_dir = dataset_dir / "labels" / split

        imgs = {p.stem: p for p in img_dir.glob("*.*") if p.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]} if img_dir.is_dir() else {}
        lbls = {p.stem: p for p in lbl_dir.glob("*.txt")} if lbl_dir.is_dir() else {}

        for stem, img_path in imgs.items():
            if stem not in lbls:
                missing_labels.append(str(img_path))

        for stem, lbl_path in lbls.items():
            if stem not in imgs:
                orphan_labels.append(str(lbl_path))

    print(f"Missing Labels (Unannotated Images): {len(missing_labels)}")
    for item in missing_labels[:10]:
        print(f"  • {item}")

    print(f"\nOrphan Label Files (Missing Image):   {len(orphan_labels)}")
    for item in orphan_labels[:10]:
        print(f"  • {item}")

    print("=========================================================")

if __name__ == "__main__":
    check_missing_labels()
