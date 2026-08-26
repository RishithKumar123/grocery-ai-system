import os
import sys
import time
import cv2
import numpy as np
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.main
from app.core.database import Base
from app.data.models.product_model import ProductModel
from app.services.decision_service import DecisionEngineService
from app.ai.container_detector import ContainerDetector

def test_enterprise_presence_engine():
    print("=========================================================")
    print("ENTERPRISE PRODUCT PRESENCE VERIFICATION ENGINE TEST")
    print("=========================================================")
    
    # 1. Connect SQLite database
    db_path = "grocery_sqlite.db"
    if not os.path.exists(db_path):
        print(f"FAILED: Database file '{db_path}' not found!")
        return False
        
    engine = create_engine(f"sqlite:///{db_path}")
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    # 2. Load target product
    target_prod = db.query(ProductModel).first()
    if not target_prod:
        print("FAILED: No products found in database!")
        return False
        
    print(f"[STEP 1] Loaded Target Product: ID #{target_prod.id} - '{target_prod.name}' (SKU: {target_prod.sku}, Barcode: {target_prod.barcode})")
    
    # 3. Create dummy test image representing product scan
    test_img = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.putText(test_img, target_prod.name, (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
    _, encoded = cv2.imencode(".jpg", test_img)
    file_bytes = encoded.tobytes()
    
    # 4. YOLO Container Detector test
    detector = ContainerDetector()
    detections = detector.detect_containers(file_bytes)
    print(f"[STEP 2] YOLO Container Detector: Found {len(detections)} candidate bounding box regions.")
    
    # 5. Evaluate Multi-Modal Decision Engine
    decision_engine = DecisionEngineService()
    
    # Test A: Exact Barcode Match
    res_barcode = decision_engine.resolve_decision(
        db=db,
        yolo_label="product",
        ocr_text=None,
        barcode=target_prod.barcode,
        target_product_id=target_prod.id
    )
    print(f"[STEP 3 - TEST A] Barcode Match Evaluation:")
    print(f"  -> Present: {res_barcode['present']} (Expected: True)")
    print(f"  -> Confidence: {res_barcode['confidence']} (Expected: 1.0)")
    print(f"  -> Explanation: '{res_barcode['explanation']}'")
    assert res_barcode['present'] == True, "Barcode match failed to return present=True!"
    
    # Test B: OCR Text Similarity Match
    res_ocr = decision_engine.resolve_decision(
        db=db,
        yolo_label="product",
        ocr_text=target_prod.name,
        barcode=None,
        embedding_similarity=0.88,
        target_product_id=target_prod.id
    )
    print(f"[STEP 3 - TEST B] OCR & SigLIP Embedding Match Evaluation:")
    print(f"  -> Present: {res_ocr['present']} (Expected: True)")
    print(f"  -> Confidence: {res_ocr['confidence']} (Expected >= 0.50)")
    print(f"  -> Explanation: '{res_ocr['explanation']}'")
    assert res_ocr['present'] == True, "OCR + Embedding match failed to return present=True!"
    
    # Test C: Unrelated Product (Negative Control)
    res_negative = decision_engine.resolve_decision(
        db=db,
        yolo_label="unknown",
        ocr_text="Unrelated Industrial Chemical Cleaner",
        barcode="9999999999999",
        embedding_similarity=0.10,
        target_product_id=target_prod.id
    )
    print(f"[STEP 3 - TEST C] Negative Control Evaluation:")
    print(f"  -> Present: {res_negative['present']} (Expected: False)")
    print(f"  -> Confidence: {res_negative['confidence']} (Expected < 0.50)")
    print(f"  -> Explanation: '{res_negative['explanation']}'")
    assert res_negative['present'] == False, "Negative control failed to return present=False!"

    db.close()
    print("=========================================================")
    print("✓ ALL ENTERPRISE PRESENCE VERIFICATION TESTS PASSED!")
    print("=========================================================")
    return True

if __name__ == "__main__":
    success = test_enterprise_presence_engine()
    sys.exit(0 if success else 1)
