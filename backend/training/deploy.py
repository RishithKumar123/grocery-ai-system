"""Automated Model Deployment & Versioning Engine."""
import sys
import time
import shutil
from pathlib import Path

try:
    from ultralytics import YOLO
    HAS_YOLO = True
except ImportError:
    HAS_YOLO = False

def deploy_candidate_model():
    script_dir = Path(__file__).parent.resolve()
    backend_dir = script_dir.parent.resolve()

    models_dir = backend_dir / "models"
    candidates_dir = models_dir / "candidates"
    production_dir = models_dir / "production"
    backups_dir = models_dir / "backups"

    for d in [models_dir, candidates_dir, production_dir, backups_dir]:
        d.mkdir(parents=True, exist_ok=True)

    candidate_path = candidates_dir / "candidate_best.pt"
    if not candidate_path.is_file():
        candidate_path = models_dir / "best.pt"

    print("=========================================================")
    print("YOLOV11 AUTOMATED MODEL DEPLOYMENT & PROMOTION ENGINE")
    print(f"Candidate Target : {candidate_path}")
    print("=========================================================")

    if not candidate_path.is_file():
        print(f"CRITICAL ERROR: Candidate model not found at '{candidate_path}'")
        print("Aborting deployment.")
        sys.exit(1)

    # 1. Verify candidate model names & class count
    if HAS_YOLO:
        try:
            candidate_model = YOLO(str(candidate_path))
            num_classes = len(candidate_model.names)
            print(f"[OK] Verified Candidate Model Class Count: {num_classes}")
            if num_classes < 1:
                print("Error: Candidate model contains 0 class definitions!")
                sys.exit(1)
        except Exception as exc:
            print(f"Error: Failed to load candidate model: {exc}")
            sys.exit(1)

    timestamp = int(time.time())
    prod_target = production_dir / "production_best.pt"
    legacy_prod_target = models_dir / "best.pt"

    # 2. Backup existing production model
    if prod_target.is_file():
        backup_file = backups_dir / f"backup_production_{timestamp}.pt"
        shutil.copy(prod_target, backup_file)
        print(f"[OK] Backed up existing production model to: {backup_file.name}")
    elif legacy_prod_target.is_file():
        backup_file = backups_dir / f"backup_legacy_{timestamp}.pt"
        shutil.copy(legacy_prod_target, backup_file)
        print(f"[OK] Backed up existing legacy model to: {backup_file.name}")

    # 3. Promote candidate to production
    shutil.copy(candidate_path, prod_target)
    shutil.copy(candidate_path, legacy_prod_target)

    print("=========================================================")
    print("[OK] MODEL PROMOTED TO PRODUCTION SUCCESSFULLY!")
    print(f"  • Production Copy : {prod_target}")
    print(f"  • Runtime Target   : {legacy_prod_target}")
    print("=========================================================")
    print("💡 The backend runtime server will now automatically utilize the updated custom model!")

if __name__ == "__main__":
    deploy_candidate_model()
