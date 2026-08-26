"""YOLOv11 Image Prediction & Crop Extraction Script."""
import sys
import json
import cv2
from pathlib import Path

import app.main
from app.core.database import SessionLocal
from app.ml.yolov11_engine import YoloV11InferenceEngine

def predict_grocery_image(image_path: str):
    path = Path(image_path)
    if not path.is_file():
        print(f"Error: Image file not found at '{image_path}'")
        return False

    db = SessionLocal()
    engine = YoloV11InferenceEngine(db=db)
    
    print(f"=========================================================")
    print(f"YOLOV11 PRODUCT INFERENCE: {path.name}")
    print(f"=========================================================")

    result = engine.predict_image(str(path))
    detections = result.get("detections", [])

    output_json = []
    for d in detections:
        output_json.append({
            "product": d["product"],
            "confidence": d["confidence"],
            "quantity": d["quantity"],
            "bbox": d["bbox"]
        })

    print(json.dumps(output_json, indent=2))
    
    # Save visual bounding box overlay
    img = cv2.imread(str(path))
    for item in output_json:
        x1, y1, x2, y2 = item["bbox"]
        label = f"{item['product']} ({item['confidence']}%)"
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(img, label, (x1, max(20, y1 - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    out_file = f"predicted_{path.name}"
    cv2.imwrite(out_file, img)
    print(f"✓ Visual Bounding Box Overlay saved to: {out_file}")
    
    db.close()
    print("=========================================================")
    return True

if __name__ == "__main__":
    img_arg = sys.argv[1] if len(sys.argv) > 1 else "kirana.jpg"
    predict_grocery_image(img_arg)
