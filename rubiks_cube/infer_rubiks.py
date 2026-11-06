"""Rubik's Cube Sticker YOLO11n + Hybrid Feature Inference Engine."""
import sys
import cv2
import numpy as np
from pathlib import Path
from ultralytics import YOLO
from find_stickers import detect_cube_stickers, classify_sticker

CLASS_NAMES = ['white', 'yellow', 'red', 'orange', 'blue', 'green']
CLASS_COLORS = {
    0: (240, 240, 240), # White
    1: (0, 255, 255),   # Yellow
    2: (0, 0, 255),     # Red
    3: (0, 140, 255),   # Orange
    4: (255, 0, 0),     # Blue
    5: (0, 200, 0)      # Green
}

def run_inference(image_path: str, model_path: str = None, conf_threshold: float = 0.15):
    project_dir = Path(__file__).parent.resolve()
    
    if model_path is None:
        model_path = project_dir / "runs" / "rubiks_sticker_run" / "weights" / "best.pt"
    else:
        model_path = Path(model_path)

    img_path = Path(image_path)
    if not img_path.is_file():
        print(f"Error: Image not found at '{img_path}'")
        sys.exit(1)

    print("=========================================================")
    print("RUBIK'S CUBE STICKER INFERENCE ENGINE")
    print("=========================================================")
    print(f"  • Test Image : {img_path.resolve()}")
    print(f"  • Model Path : {model_path.resolve()}")
    print("=========================================================")

    img = cv2.imread(str(img_path))
    h_img, w_img, _ = img.shape
    
    detections = []
    
    # 1. Try YOLO Model Prediction
    if model_path.is_file():
        try:
            model = YOLO(str(model_path))
            results = model.predict(source=str(img_path), imgsz=1024, conf=conf_threshold, verbose=False)
            for res in results:
                for box in res.boxes:
                    cls_id = int(box.cls[0].item())
                    conf = float(box.conf[0].item())
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    detections.append((cls_id, conf, x1, y1, x2 - x1, y2 - y1, "YOLO11n"))
        except Exception as e:
            print(f"YOLO predict note: {e}")

    # 2. Hybrid Grid Contour Fallback if YOLO model detections are sparse
    if len(detections) < 3:
        boxes = detect_cube_stickers(img)
        for b in boxes:
            x, y, bw, bh, area, cls_id = b
            detections.append((cls_id, 0.95, x, y, bw, bh, "StickerDetector"))

    # Draw color-coded bounding boxes & text labels
    output_img = img.copy()
    for cls_id, conf, x, y, bw, bh, source in detections:
        cname = CLASS_NAMES[cls_id] if cls_id < len(CLASS_NAMES) else f"class_{cls_id}"
        color = CLASS_COLORS.get(cls_id, (0, 255, 0))
        
        cv2.rectangle(output_img, (x, y), (x + bw, y + bh), color, 2)
        label = f"{cname} ({conf:.2f})"
        cv2.putText(output_img, label, (x, max(15, y - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    output_path = project_dir / "inference_output.jpg"
    cv2.imwrite(str(output_path), output_img)

    print(f"\n[OK] Inference Complete: Detected {len(detections)} stickers.")
    print(f"  • Output Image Saved To : {output_path.resolve()}")
    print("=========================================================")
    return len(detections)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_image = sys.argv[1]
    else:
        target_image = str(Path(__file__).parent / "dataset" / "images" / "val" / "rubik_val_1.jpg")
        
    run_inference(target_image)
