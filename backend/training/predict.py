"""YOLOv11 Image & Video Inference Testing Script."""
import sys
import json
import time
import cv2
from pathlib import Path

try:
    import torch
    from ultralytics import YOLO
    HAS_YOLO = True
except ImportError:
    HAS_YOLO = False

def run_prediction(source_path: str):
    script_dir = Path(__file__).parent.resolve()
    backend_dir = script_dir.parent.resolve()

    model_path = backend_dir / "models" / "production" / "production_best.pt"
    if not model_path.is_file():
        model_path = backend_dir / "models" / "best.pt"

    print("=========================================================")
    print("YOLOV11 PREDICTION & INFERENCE TEST ENGINE")
    print(f"Target Source  : {source_path}")
    print(f"Loaded Model   : {model_path}")
    print("=========================================================")

    if not HAS_YOLO:
        print("Error: PyTorch or Ultralytics package is missing.")
        sys.exit(1)

    if not model_path.is_file():
        print(f"Error: Model weights not found at '{model_path}'")
        sys.exit(1)

    src_p = Path(source_path).resolve()
    if not src_p.is_file():
        print(f"Error: Target image/video file not found at '{src_p}'")
        sys.exit(1)

    model = YOLO(str(model_path))
    start_t = time.perf_counter()
    results = model.predict(source=str(src_p), conf=0.15, iou=0.70, imgsz=640)
    elapsed_ms = (time.perf_counter() - start_t) * 1000

    out_detections = []
    for r in results:
        names = r.names
        for box in r.boxes:
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            xyxy = [int(v) for v in box.xyxy[0].tolist()]
            p_name = names.get(cls_id, f"Class_{cls_id}")

            out_detections.append({
                "product_name": p_name,
                "class_id": cls_id,
                "confidence": round(conf * 100, 2),
                "bbox": xyxy
            })

    output_dir = backend_dir / "runs" / "predict_results"
    output_dir.mkdir(parents=True, exist_ok=True)
    annotated_save_path = output_dir / f"predict_{src_p.stem}{src_p.suffix}"

    if results and hasattr(results[0], "save"):
        results[0].save(filename=str(annotated_save_path))

    print(f"\n[OK] Inference Completed in {elapsed_ms:.1f} ms!")
    print(f"Total Detections Found: {len(out_detections)}")
    print("---------------------------------------------------------")
    print(json.dumps(out_detections, indent=2))
    print("---------------------------------------------------------")
    print(f"Annotated Image Overlay Saved To: {annotated_save_path}")
    print("=========================================================")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python training/predict.py <path_to_image_or_video>")
        sys.exit(1)
    run_prediction(sys.argv[1])
