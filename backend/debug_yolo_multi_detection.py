import os
import sys
import cv2
import torch
import numpy as np
from ultralytics import YOLO

from app.core.config import settings
from app.ml.model_manager import YoloModelManager

def run_yolo_pipeline_analysis(image_path: str = None):
    print("=========================================================")
    print("YOLO INFERENCE PIPELINE MULTI-PRODUCT DIAGNOSTIC ANALYSIS")
    print("=========================================================")
    
    # Task 1 & 2: Load model and verify class names
    manager = YoloModelManager.get()
    model = manager.model
    meta = manager.meta
    
    print(f"\n[TASK 1 & 2] Model Weight & Class Verification:")
    print(f"  • Model Path: {meta.path if meta else 'Default loaded'}")
    print(f"  • Model Names attribute: {model.names}")
    print(f"  • Class Names Count: {len(model.names)}")
    for cid, name in model.names.items():
        print(f"    - Class ID {cid}: '{name}'")
        
    # Check test image
    if not image_path or not os.path.exists(image_path):
        # Create a synthetic image containing 3 distinct grocery product boxes
        h, w = 640, 640
        synth_img = np.ones((h, w, 3), dtype=np.uint8) * 240
        # Draw Product 1 (Honey box)
        cv2.rectangle(synth_img, (50, 100), (220, 450), (200, 150, 50), -1)
        cv2.putText(synth_img, "Patanjali Honey", (60, 280), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        # Draw Product 2 (Ghee box)
        cv2.rectangle(synth_img, (260, 100), (430, 450), (50, 180, 220), -1)
        cv2.putText(synth_img, "Cow Ghee", (270, 280), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        # Draw Product 3 (Amla Murabba box)
        cv2.rectangle(synth_img, (460, 100), (610, 450), (80, 200, 80), -1)
        cv2.putText(synth_img, "Amla Murabba", (470, 280), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        image_path = "debug_multi_product.jpg"
        cv2.imwrite(image_path, synth_img)
        print(f"\n[NOTE] Created multi-product synthetic test image at '{image_path}'.")

    img = cv2.imread(image_path)
    
    # Task 3 & 4: Total Detections before vs after NMS
    # Raw forward pass to extract predictions before NMS
    results_raw = model.predict(source=img, conf=0.01, iou=0.99, verbose=False, max_det=1000)
    total_before_nms = len(results_raw[0].boxes) if results_raw else 0
    
    # Task 5, 6, 7: Predict with conf=0.25, iou=0.70, max_det=300
    conf_thresh = 0.25
    iou_thresh = 0.70
    max_det = 300
    
    results = model.predict(source=img, conf=conf_thresh, iou=iou_thresh, max_det=max_det, verbose=False)
    boxes = results[0].boxes
    total_after_nms = len(boxes)
    
    print(f"\n[TASK 3, 4, 5, 6, 7] NMS & Inference Parameters:")
    print(f"  • Conf Threshold: {conf_thresh}")
    print(f"  • IoU Threshold: {iou_thresh}")
    print(f"  • Max Detections (max_det): {max_det}")
    print(f"  • Total Candidates Before NMS (conf >= 0.01): {total_before_nms}")
    print(f"  • Total Detections After NMS (conf >= {conf_thresh}, iou <= {iou_thresh}): {total_after_nms}")
    
    # Task 8, 9, 10, 11, 12: Print and draw bounding boxes
    print(f"\n[TASK 8 & 12] Detailed Detection Outputs ({total_after_nms} items):")
    annotated_img = img.copy()
    
    for idx, box in enumerate(boxes):
        xyxy = box.xyxy[0].tolist()
        conf = float(box.conf[0])
        cls_id = int(box.cls[0])
        cls_name = model.names.get(cls_id, f"class_{cls_id}")
        x1, y1, x2, y2 = [int(v) for v in xyxy]
        
        print(f"  [{idx + 1}] Class ID: {cls_id} | Class Name: '{cls_name}' | Confidence: {conf:.4f} | Bounding Box: [{x1}, {y1}, {x2}, {y2}]")
        
        # Task 11: Draw bounding box on output image
        color = ((cls_id * 50) % 255, (cls_id * 100 + 50) % 255, (cls_id * 150 + 100) % 255)
        cv2.rectangle(annotated_img, (x1, y1), (x2, y2), color, 2)
        label_text = f"{cls_name} {conf:.2f}"
        cv2.putText(annotated_img, label_text, (x1, max(y1 - 10, 20)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
        
    out_vis_path = "debug_detections_vis.jpg"
    cv2.imwrite(out_vis_path, annotated_img)
    print(f"\n[TASK 11] Visualized bounding boxes saved to '{out_vis_path}'.")
    
    # Task 13: Diagnostics if only 1 detection exists
    print(f"\n[TASK 13] Diagnostic Summary & Root Cause Evaluation:")
    if total_after_nms <= 1:
        print("  ⚠️ WARNING: Only 1 or 0 products detected in input image.")
        print("  Root Cause Analysis Checkpoints:")
        print("  1. Dataset Diversity: Ensure dataset generator includes multi-product composite images during training.")
        print("  2. Model Training: Verify model was trained on all classes rather than single-class subset.")
        print("  3. NMS IoU Overlap: High IoU threshold (0.70) prevents suppressing distinct adjacent boxes.")
        print("  4. Fallback Logic: Single-product fallback in API endpoints triggers ONLY when YOLO returns 0 boxes.")
    else:
        print(f"  ✓ SUCCESS: {total_after_nms} distinct products detected and localized properly across image!")

if __name__ == "__main__":
    img_arg = sys.argv[1] if len(sys.argv) > 1 else None
    run_yolo_pipeline_analysis(img_arg)
