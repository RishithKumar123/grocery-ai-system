"""Rubik's Cube Multi-Threshold Precision Sticker Detection & Visualization Engine."""
import cv2
import numpy as np
import yaml
import json
from pathlib import Path

CLASS_NAMES = ['white', 'yellow', 'red', 'orange', 'blue', 'green']
CLASS_COLORS_BGR = {
    0: (240, 240, 240), # White (Light Gray in drawing)
    1: (0, 255, 255),   # Yellow
    2: (0, 0, 255),     # Red
    3: (0, 140, 255),   # Orange
    4: (255, 0, 0),     # Blue
    5: (0, 200, 0)      # Green
}

def classify_crop(crop_bgr):
    """Accurately classify a sticker crop into one of 6 classes (0..5)."""
    if crop_bgr is None or crop_bgr.size == 0:
        return 0
        
    hsv = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2HSV)
    h_vals = hsv[:, :, 0].flatten()
    s_vals = hsv[:, :, 1].flatten()
    v_vals = hsv[:, :, 2].flatten()
    
    b_vals = crop_bgr[:, :, 0].flatten()
    g_vals = crop_bgr[:, :, 1].flatten()
    r_vals = crop_bgr[:, :, 2].flatten()
    
    h_med = np.median(h_vals)
    s_med = np.median(s_vals)
    v_med = np.median(v_vals)
    
    b_med = np.median(b_vals)
    g_med = np.median(g_vals)
    r_med = np.median(r_vals)
    
    # White check: Low saturation (< 50) and high brightness (v_med > 140)
    if s_med < 55 and v_med > 130:
        # Extra check: RGB channels should be nearly equal for white
        max_diff = max(abs(r_med - g_med), abs(g_med - b_med), abs(r_med - b_med))
        if max_diff < 35:
            return 0 # white
            
    # Blue check: Hue in range 85..135
    if 85 <= h_med <= 135 and s_med > 45:
        return 4 # blue
        
    # Green check: Hue in range 35..85
    if 35 <= h_med <= 85 and s_med > 40:
        return 5 # green
        
    # Yellow check: Hue in range 14..34, high saturation & brightness
    if 14 <= h_med <= 34 and s_med > 65:
        return 1 # yellow

    # Orange vs Red check:
    # Red hue sits near 0..13 or 165..180
    # Orange hue sits near 7..22 with high Green component
    if h_med < 14 or h_med > 165:
        if g_med > 50 and (r_med - g_med) < 85 and h_med >= 6:
            return 3 # orange
        else:
            return 2 # red
            
    # Channel dominance fallback
    if b_med > r_med and b_med > g_med:
        return 4 # blue
    if g_med > r_med and g_med > b_med:
        return 5 # green
    if r_med > g_med and r_med > b_med:
        if g_med > 150:
            return 1 # yellow
        elif g_med > 65:
            return 3 # orange
        else:
            return 2 # red
            
    return 0

def find_cube_stickers_multiscale(img_bgr):
    """Extract sticker bounding boxes using multi-scale thresholding & color segmentation."""
    h_img, w_img, _ = img_bgr.shape
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    
    candidates = []
    
    # 1. Edge/Adaptive thresholding at multiple block sizes
    for block_size in [9, 13, 19, 25]:
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, block_size, 2)
        contours, _ = cv2.findContours(thresh, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if 100 < area < 12000:
                x, y, bw, bh = cv2.boundingRect(cnt)
                aspect = bw / float(bh)
                if 0.45 < aspect < 2.2:
                    # Ignore entire image bounding box
                    if bw > w_img * 0.7 or bh > h_img * 0.7:
                        continue
                    candidates.append((x, y, bw, bh, area))

    # 2. Color-space HSV mask thresholding for each color family
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
    color_masks = [
        # Blue/Green mask
        cv2.inRange(hsv, np.array([35, 40, 40]), np.array([135, 255, 255])),
        # Yellow/Orange/Red mask
        cv2.inRange(hsv, np.array([0, 60, 60]), np.array([34, 255, 255])),
        # Red upper mask
        cv2.inRange(hsv, np.array([160, 60, 60]), np.array([180, 255, 255]))
    ]
    
    for mask in color_masks:
        contours, _ = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if 100 < area < 12000:
                x, y, bw, bh = cv2.boundingRect(cnt)
                aspect = bw / float(bh)
                if 0.45 < aspect < 2.2:
                    if bw > w_img * 0.7 or bh > h_img * 0.7:
                        continue
                    candidates.append((x, y, bw, bh, area))

    # Sort candidates by area descending and deduplicate with IoU NMS
    candidates.sort(key=lambda item: item[4], reverse=True)
    
    dedup = []
    for c in candidates:
        x1, y1, w1, h1, a1 = c
        overlap = False
        for b in dedup:
            x2, y2, w2, h2, a2 = b
            xx1 = max(x1, x2)
            yy1 = max(y1, y2)
            xx2 = min(x1 + w1, x2 + w2)
            yy2 = min(y1 + h1, y2 + h2)
            inter = max(0, xx2 - xx1) * max(0, yy2 - yy1)
            iou = inter / float(a1 + a2 - inter)
            if iou > 0.30:
                overlap = True
                break
        if not overlap:
            dedup.append(c)

    # Classify each deduplicated box
    final_boxes = []
    for x, y, bw, bh, area in dedup:
        # Sample center region of box (margin inset to avoid borders)
        m_x = int(bw * 0.2)
        m_y = int(bh * 0.2)
        crop = img_bgr[y+m_y:y+bh-m_y, x+m_x:x+bw-m_x]
        
        cls_id = classify_crop(crop)
        final_boxes.append((x, y, bw, bh, cls_id))
        
    return final_boxes

if __name__ == "__main__":
    print("Multi-scale sticker engine ready.")
