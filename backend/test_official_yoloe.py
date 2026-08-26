import os
import sys
import time
import cv2
import numpy as np

import app.main
from app.core.database import SessionLocal
from app.data.models.product_model import ProductModel
from app.ml.yoloe_engine import YoloEInferenceEngine, PromptManager

def test_official_yoloe_suite():
    print("=========================================================")
    print("OFFICIAL YOLOE OPEN-VOCABULARY ENGINE VERIFICATION SUITE")
    print("=========================================================")
    
    db = SessionLocal()
    
    # 1. Test PromptManager Lifecycle
    pm = PromptManager(["Patanjali Honey", "Tata Salt"])
    print(f"[TEST 1] Initial Prompts: {pm.get_prompts()}")
    assert len(pm.get_prompts()) == 2, "PromptManager initial prompt count mismatch"
    
    pm.append_prompt("Maggi Noodles")
    print(f"[TEST 2] After Append: {pm.get_prompts()}")
    assert "Maggi Noodles" in pm.get_prompts(), "PromptManager append failed"
    
    pm.remove_prompt("Tata Salt")
    print(f"[TEST 3] After Remove: {pm.get_prompts()}")
    assert "Tata Salt" not in pm.get_prompts(), "PromptManager remove failed"
    
    # 2. Test YOLOE Engine Singleton Loading
    yoloe1 = YoloEInferenceEngine(db=db)
    yoloe2 = YoloEInferenceEngine(db=db)
    assert yoloe1 is yoloe2, "YoloEInferenceEngine Singleton pattern failed!"
    print(f"[TEST 4] YOLOE Singleton Verified. Device: {yoloe1.device}")
    
    # 3. Test YOLOE Open-Vocabulary Frame Prediction
    synth_frame = np.ones((640, 640, 3), dtype=np.uint8) * 220
    cv2.rectangle(synth_frame, (100, 100), (300, 500), (50, 180, 50), -1)
    cv2.putText(synth_frame, "Patanjali Honey", (110, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    _, encoded = cv2.imencode(".jpg", synth_frame)
    frame_bytes = encoded.tobytes()
    
    print("[TEST 5] Executing YOLOE Open-Vocabulary Frame Inference...")
    res = yoloe1.predict(source=frame_bytes, prompts=["Patanjali Honey", "Cooking Oil Bottle"], conf=0.15)
    
    detections = res.get("detections", [])
    print(f"  • Model Type: {res.get('model_type')}")
    print(f"  • Execution Device: {res.get('device')}")
    print(f"  • Detections Count: {len(detections)}")
    print(f"  • Inference Time: {res.get('inference_time_ms')} ms")
    
    for idx, d in enumerate(detections):
        print(f"    [{idx + 1}] Label: '{d['label']}' | Class ID: {d['class_id']} | Conf: {d['confidence']} | Box: {d['box']}")
        
    db.close()
    print("=========================================================")
    print("✓ OFFICIAL YOLOE MIGRATION TEST SUITE PASSED SUCCESSFULLY!")
    print("=========================================================")
    return True

if __name__ == "__main__":
    success = test_official_yoloe_suite()
    sys.exit(0 if success else 1)
