import os
import sys
import time
import cv2
import numpy as np

import app.main
from app.core.database import SessionLocal
from app.data.models.product_model import ProductModel
from app.ml.yoloe_engine import YoloEInferenceEngine

def test_yoloe_open_vocabulary_engine():
    print("=========================================================")
    print("YOLOE OPEN-VOCABULARY INFERENCE ENGINE TEST")
    print("=========================================================")
    
    db = SessionLocal()
    
    # 1. Instantiate YOLOE Engine
    yoloe = YoloEInferenceEngine(db=db)
    assert yoloe.model is not None, "YOLOE model failed to load!"
    print(f"[STEP 1] YOLOE Model Loaded Successfully on Device: {yoloe.device}")
    
    # 2. Test Dynamic Prompt Binding
    custom_prompts = ["Patanjali Honey", "Tata Salt", "Maggi Noodles", "Cooking Oil Bottle", "Grocery Item"]
    yoloe.set_prompts(custom_prompts)
    print(f"[STEP 2] Dynamic Text Prompts Bound ({len(yoloe.current_prompts)} classes): {yoloe.current_prompts}")
    assert yoloe.current_prompts == custom_prompts, "Prompt binding failed!"
    
    # 3. Create synthetic test image
    synth_img = np.ones((640, 640, 3), dtype=np.uint8) * 230
    cv2.rectangle(synth_img, (50, 100), (250, 500), (40, 140, 240), -1)
    cv2.putText(synth_img, "Patanjali Honey", (60, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    cv2.rectangle(synth_img, (350, 100), (550, 500), (40, 200, 100), -1)
    cv2.putText(synth_img, "Tata Salt", (360, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    _, encoded = cv2.imencode(".jpg", synth_img)
    img_bytes = encoded.tobytes()
    
    # 4. Perform YOLOE Open-Vocabulary Inference
    print(f"[STEP 3] Running YOLOE Zero-Shot Inference on Test Frame...")
    res = yoloe.predict(source=img_bytes, prompts=custom_prompts, conf=0.15)
    
    detections = res.get("detections", [])
    print(f"  • Total Detections: {len(detections)}")
    print(f"  • Inference Time: {res.get('inference_time_ms')} ms")
    print(f"  • Prompts Used: {res.get('prompts_used')}")
    
    for idx, d in enumerate(detections):
        print(f"    [{idx + 1}] Label: '{d['label']}' | Class ID: {d['class_id']} | Conf: {d['confidence']} | Box: {d['box']}")
        
    db.close()
    print("=========================================================")
    print("✓ YOLOE OPEN-VOCABULARY MIGRATION TEST PASSED SUCCESSFULLY!")
    print("=========================================================")
    return True

if __name__ == "__main__":
    success = test_yoloe_open_vocabulary_engine()
    sys.exit(0 if success else 1)
