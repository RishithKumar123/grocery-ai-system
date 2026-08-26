import os
import sys
import time
import cv2
import numpy as np

import app.main
from app.core.database import SessionLocal
from app.data.models.product_model import ProductModel
from app.ml.yolov11_engine import YoloV11InferenceEngine

def test_yolov11_engine_suite():
    print("=========================================================")
    print("YOLOv11 PRODUCTION ENGINE VERIFICATION SUITE")
    print("=========================================================")
    
    db = SessionLocal()
    
    # 1. Test YoloV11InferenceEngine Singleton Instantiation
    yolo1 = YoloV11InferenceEngine(db=db)
    yolo2 = YoloV11InferenceEngine(db=db)
    assert yolo1 is yolo2, "YoloV11InferenceEngine Singleton pattern failed!"
    print(f"[TEST 1] YOLOv11 Singleton Instance Verified. Device: {yolo1.device}")
    assert yolo1.model is not None, "YOLOv11 model failed to load!"
    
    # 2. Synthetic Test Frame Detection
    synth_frame = np.ones((640, 640, 3), dtype=np.uint8) * 210
    cv2.rectangle(synth_frame, (80, 80), (280, 480), (60, 160, 60), -1)
    cv2.putText(synth_frame, "PATANJALI HONEY", (90, 280), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
    
    _, encoded = cv2.imencode(".jpg", synth_frame)
    frame_bytes = encoded.tobytes()
    
    print("[TEST 2] Executing YOLOv11 Object Detection...")
    res = yolo1.predict(source=frame_bytes, conf=0.15)
    
    detections = res.get("detections", [])
    print(f"  • Model Type: {res.get('model_type')}")
    print(f"  • Execution Device: {res.get('device')}")
    print(f"  • Detections Count: {len(detections)}")
    print(f"  • Inference Time: {res.get('inference_time_ms')} ms")
    
    for idx, d in enumerate(detections):
        print(f"    [{idx + 1}] Label: '{d['label']}' | Class ID: {d['class_id']} | Conf: {d['confidence']} | Box: {d['box']}")
        
    db.close()
    print("=========================================================")
    print("✓ YOLOv11 PRODUCTION ENGINE TEST SUITE PASSED SUCCESSFULLY!")
    print("=========================================================")
    return True

if __name__ == "__main__":
    success = test_yolov11_engine_suite()
    sys.exit(0 if success else 1)
